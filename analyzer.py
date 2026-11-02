import ast


class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.functions = []
        self.loops = 0
        self.nested_loops = 0
        self.list_membership = 0
        self.repeated_calls = []

        self.loop_depth = 0

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_For(self, node):
        self.loops += 1
        self.loop_depth += 1

        if self.loop_depth > 1:
            self.nested_loops += 1

        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_While(self, node):
        self.loops += 1
        self.loop_depth += 1

        if self.loop_depth > 1:
            self.nested_loops += 1

        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_Compare(self, node):
        for operator in node.ops:
            if isinstance(operator, (ast.In, ast.NotIn)):
                self.list_membership += 1

        self.generic_visit(node)


def analyze_code(source_code):
    try:
        tree = ast.parse(source_code)
    except SyntaxError as error:
        return {
            "success": False,
            "error": str(error)
        }

    analyzer = CodeAnalyzer()
    analyzer.visit(tree)

    return {
        "success": True,
        "functions": analyzer.functions,
        "loops": analyzer.loops,
        "nested_loops": analyzer.nested_loops,
        "membership_checks": analyzer.list_membership,
        "message": "تحلیل ساختاری کد با موفقیت انجام شد."
    }


if __name__ == "__main__":
    sample_code = """
def find_items(items, targets):
    result = []

    for item in items:
        if item in targets:
            result.append(item)

    return result
"""

    result = analyze_code(sample_code)

    for key, value in result.items():
        print(f"{key}: {value}")
