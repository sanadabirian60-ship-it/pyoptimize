import ast
import sys
from pathlib import Path
from collections import Counter


class PyOptimizeAnalyzer(ast.NodeVisitor):
    """Static analyzer for Python source code."""

    def __init__(self, source):
        self.source = source
        self.tree = None
        self.issues = []
        self.functions = []
        self.loop_count = 0
        self.max_loop_depth = 0
        self.loop_depth = 0
        self.container_count = 0
        self.recursive_functions = set()
        self.current_function = None
        self.function_calls = {}
        self.line_count = len(source.splitlines())

    def add_issue(
        self, line, severity, category, message, suggestion
    ):
        self.issues.append({
            "line": line,
            "severity": severity,
            "category": category,
            "message": message,
            "suggestion": suggestion,
        })

    def visit_FunctionDef(self, node):
        previous_function = self.current_function
        self.current_function = node.name

        self.functions.append(node.name)
        self.function_calls.setdefault(node.name, set())

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    self.function_calls[node.name].add(
                        child.func.id
                    )

        self.generic_visit(node)
        self.current_function = previous_function

    visit_AsyncFunctionDef = visit_FunctionDef

    def _visit_loop(self, node):
        self.loop_count += 1
        self.loop_depth += 1

        self.max_loop_depth = max(
            self.max_loop_depth, self.loop_depth
        )

        if self.loop_depth == 2:
            self.add_issue(
                node.lineno,
                "Medium",
                "Performance",
                "Nested loop detected.",
                "Check whether repeated work can be reduced "
                "with a more suitable algorithm or data structure."
            )

        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_For(self, node):
        self._visit_loop(node)

    def visit_AsyncFor(self, node):
        self._visit_loop(node)

    def visit_While(self, node):
        self._visit_loop(node)

    def visit_List(self, node):
        self.container_count += 1
        self.generic_visit(node)

    def visit_Dict(self, node):
        self.container_count += 1
        self.generic_visit(node)

    def visit_Set(self, node):
        self.container_count += 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.container_count += 1

        if len(node.generators) > 1:
            self.add_issue(
                node.lineno,
                "Low",
                "Performance",
                "List comprehension has multiple generators.",
                "Check whether all generated combinations are needed."
            )

        self.generic_visit(node)

    def visit_Compare(self, node):
        has_membership = any(
            isinstance(op, (ast.In, ast.NotIn))
            for op in node.ops
        )

        if has_membership and self.loop_depth > 0:
            self.add_issue(
                node.lineno,
                "Low",
                "Performance",
                "Membership check found inside a loop.",
                "If the searched collection is a list and many "
                "lookups occur, consider a set or dictionary. "
                "Check that changing the structure preserves behavior."
            )

        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            name = node.func.id

            if name in {"eval", "exec"}:
                self.add_issue(
                    node.lineno,
                    "High",
                    "Security",
                    f"Use of {name}() detected.",
                    "Avoid evaluating untrusted strings. "
                    "Prefer explicit parsing or safer alternatives."
                )

            if name == "deepcopy":
                self.add_issue(
                    node.lineno,
                    "Low",
                    "Memory",
                    "Deep-copy operation detected.",
                    "Check whether all nested objects need to be copied."
                )

        self.generic_visit(node)

    def analyze(self):
        try:
            self.tree = ast.parse(self.source)
        except SyntaxError as error:
            self.add_issue(
                error.lineno or 0,
                "High",
                "Syntax",
                error.msg,
                "Fix the syntax error before analyzing performance."
            )
            return self

        self.visit(self.tree)

        # Check direct recursion in each function.
        for function_name, calls in self.function_calls.items():
            if function_name in calls:
                self.recursive_functions.add(function_name)

                self.add_issue(
                    None,
                    "Medium",
                    "Algorithm",
                    f"Possible direct recursion in '{function_name}'.",
                    "Check the base case and recursion depth. "
                    "Recursion is not necessarily a problem."
                )

        # Remove exact duplicate findings.
        unique = []
        seen = set()

        for issue in self.issues:
            key = (
                issue["line"],
                issue["category"],
                issue["message"],
            )

            if key not in seen:
                seen.add(key)
                unique.append(issue)

        self.issues = unique
        return self

    def estimate_complexity(self):
        if self.max_loop_depth >= 2:
            time_estimate = (
                "Possible O(n^2) or higher; inspect loop bounds."
            )
        elif self.loop_count > 0:
            time_estimate = (
                "Possible O(n) for a single input-dependent loop; "
                "inspect all loops and called functions."
            )
        else:
            time_estimate = (
                "Cannot determine from loop structure alone."
            )

        if self.container_count > 0:
            space_estimate = (
                "Additional containers detected. "
                "Space complexity depends on their sizes."
            )
        else:
            space_estimate = (
                "No explicit list/dict/set literals detected. "
                "Total space complexity is unknown."
            )

        return time_estimate, space_estimate

    def report(self):
        print("\n" + "=" * 48)
        print("           PYOPTIMIZE REPORT")
        print("=" * 48)

        syntax_errors = [
            issue for issue in self.issues
            if issue["category"] == "Syntax"
        ]

        if syntax_errors:
            print("Syntax analysis: FAILED")
        else:
            print("Syntax analysis: PASSED")

        print("Lines of code:", self.line_count)
        print("Functions detected:", len(set(self.functions)))
        print("Loops detected:", self.loop_count)
        print("Maximum loop nesting:", self.max_loop_depth)
        print("Container literals detected:", self.container_count)

        time_estimate, space_estimate = self.estimate_complexity()

        print("\n--- Complexity estimates ---")
        print("Time:", time_estimate)
        print("Space:", space_estimate)

        print("\n--- Findings ---")

        if not self.issues:
            print("No supported warning patterns detected.")
        else:
            for number, issue in enumerate(self.issues, 1):
                line = issue["line"]
                location = (
                    f"line {line}" if line else "location unknown"
                )

                print(
                    f"\n{number}. [{issue['severity']}] "
                    f"{issue['category']} - {location}"
                )
                print("Finding:", issue["message"])
                print("Suggestion:", issue["suggestion"])

        print("\n--- Important limitations ---")
        print(
            "This is a heuristic static analyzer. It does not execute "
            "the analyzed program, prove exact complexity, measure "
            "runtime or memory, or automatically rewrite the source."
        )
        print("=" * 48 + "\n")


def analyze_file(filename):
    path = Path(filename)

    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"Error reading file: {error}")
        return 1

    analyzer = PyOptimizeAnalyzer(source)
    analyzer.analyze()
    analyzer.report()

    if any(
        issue["category"] == "Syntax"
        for issue in analyzer.issues
    ):
        return 1

    return 0


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyzer.py <python_file.py>")
        return 2

    return analyze_file(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())

                    
