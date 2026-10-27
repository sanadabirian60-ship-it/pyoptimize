import ast
from collections import Counter


class PythonCodeAnalyzer(ast.NodeVisitor):
    """
    Static analyzer for Python source code.
    Detects selected code patterns and estimates complexity.
    """

    def __init__(self):
        self.loops = 0
        self.nested_loops = 0
        self.max_loop_depth = 0
        self.loop_depth = 0
        self.function_count = 0
        self.recursive_functions = set()
        self.function_calls = Counter()
        self.issues = []
        self.complexity_notes = []
        self.current_function = None
        self.function_calls_map = {}
        self.list_membership_in_loop = 0

    def visit_FunctionDef(self, node):
        previous_function = self.current_function
        self.current_function = node.name
        self.function_count += 1
        self.function_calls_map.setdefault(node.name, [])

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    called = child.func.id
                    self.function_calls[called] += 1
                    self.function_calls_map[node.name].append(called)

        self.generic_visit(node)
        self.current_function = previous_function

    def visit_For(self, node):
        self._inspect_loop(node)
        self.generic_visit(node)

    def visit_While(self, node):
        self._inspect_loop(node)
        self.generic_visit(node)

    def _inspect_loop(self, node):
        self.loops += 1
        self.loop_depth += 1
        self.max_loop_depth = max(
            self.max_loop_depth, self.loop_depth
        )

        if self.loop_depth > 1:
            self.nested_loops += 1
            self.issues.append({
                "line": node.lineno,
                "severity": "Medium",
                "message": (
                    "Nested loop detected. "
                    "Check whether both loops must scan all elements."
                ),
                "recommendation": (
                    "Consider dictionaries, sets, sorting, "
                    "or a more efficient algorithm where appropriate."
                ),
            })

        for child in ast.walk(node):
            if isinstance(child, ast.Compare):
                for operator in child.ops:
                    if isinstance(operator, (ast.In, ast.NotIn)):
                        self.list_membership_in_loop += 1
                        self.issues.append({
                            "line": getattr(child, "lineno", node.lineno),
                            "severity": "Low",
                            "message": (
                                "Membership test inside a loop detected. "
                                "The container type is not inferred."
                            ),
                            "recommendation": (
                                "If the container is a list and many "
                                "lookups are needed, consider a set "
                                "or dictionary, after checking semantics."
                            ),
                        })
                        break

        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            name = node.func.id

            if name in {"eval", "exec"}:
                self.issues.append({
                    "line": node.lineno,
                    "severity": "High",
                    "message": f"Use of {name}() detected.",
                    "recommendation": (
                        "Avoid evaluating dynamic strings when possible; "
                        "use safer, explicit alternatives."
                    ),
                })

        self.generic_visit(node)

    def analyze_recursion(self):
        for function_name, calls in self.function_calls_map.items():
            if function_name in calls:
                self.recursive_functions.add(function_name)

        for name in sorted(self.recursive_functions):
            self.issues.append({
                "line": None,
                "severity": "Medium",
                "message": (
                    f"Possible direct recursion in function '{name}'."
                ),
                "recommendation": (
                    "Check the base case and recursion depth. "
                    "Recursion does not necessarily indicate a defect."
                ),
            })

    def report(self):
        self.analyze_recursion()

        print("\n========== PYOPTIMIZE REPORT ==========")
        print(f"Functions detected: {self.function_count}")
        print(f"Loops detected: {self.loops}")
        print(f"Nested-loop detections: {self.nested_loops}")
        print(f"Maximum loop nesting depth: {self.max_loop_depth}")

        print("\n--- Complexity assessment ---")

        if self.max_loop_depth >= 2:
            print(
                "Potential O(n^2) or higher behavior: nested loops exist. "
                "Actual complexity depends on loop bounds and operations."
            )
        elif self.loops == 1:
            print(
                "Potential O(n) behavior: one loop detected. "
                "Verify the number of iterations."
            )
        elif self.loops == 0:
            print(
                "No for/while loops detected. "
                "Function calls and library operations may still be costly."
            )
        else:
            print(
                "Multiple loops detected. "
                "They may be sequential rather than nested."
            )

        if self.recursive_functions:
            print(
                "Recursive functions detected: "
                + ", ".join(sorted(self.recursive_functions))
            )

        print("\n--- Issues and recommendations ---")

        if not self.issues:
            print("No supported warning patterns were detected.")
        else:
            for index, issue in enumerate(self.issues, start=1):
                line = issue["line"]
                location = f"Line {line}" if line else "Location unknown"

                print(f"\n{index}. [{issue['severity']}] {location}")
                print("   Finding:", issue["message"])
                print("   Suggestion:", issue["recommendation"])

        print("\n--- Important limitations ---")
        print(
            "This is a heuristic static analyzer, not a formal "
            "complexity proof. It does not infer all variable types, "
            "loop bounds, memory allocations, or library costs."
        )
        print("=======================================\n")


def analyze_source(source_code):
    try:
        syntax_tree = ast.parse(source_code)
    except SyntaxError as error:
        print("Syntax error detected:")
        print(f"Line: {error.lineno}")
        print(f"Message: {error.msg}")
        return

    analyzer = PythonCodeAnalyzer()
    analyzer.visit(syntax_tree)
    analyzer.report()


if __name__ == "__main__":
    sample_code = '''
def find_duplicates(items):
    duplicates = []

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])

    return duplicates


def search_items(items, targets):
    result = []

    for target in targets:
        if target in items:
            result.append(target)

    return result
'''

    analyze_source(sample_code)
