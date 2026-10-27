
# استفاده: python index.py your_code.py
import ast
import sys
from pathlib import Path

COMPLEXITY = {0: "O(1) یا بدون حلقه", 1: "O(n)", 2: "O(n²)", 3: "O(n³)"}


class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.issues = []           # (line, message)
        self.loop_depth = 0
        self.func_stack = []
        self.max_depth = {}        # تابع -> بیشترین عمق حلقه
        self.func_calls = {}       # تابع -> نام توابعی که صدا زده

    @property
    def current_func(self):
        return self.func_stack[-1] if self.func_stack else "<module>"

    def add(self, node, msg):
        self.issues.append((node.lineno, msg))

    def visit_FunctionDef(self, node):
        self.func_stack.append(node.name)
        self.max_depth.setdefault(node.name, 0)
        self.func_calls[node.name] = set()
        saved, self.loop_depth = self.loop_depth, 0

        self.generic_visit(node)

        self.loop_depth = saved
        self.func_stack.pop()

        # بررسی بازگشتی بودن بدون کش
        if node.name in self.func_calls[node.name]:
            decorators = [ast.unparse(d) for d in node.decorator_list]
            if not any("cache" in d for d in decorators):
                self.add(node, f"تابع «{node.name}» بازگشتی است. اگر زیرمسئله‌ها تکرار می‌شوند، از @lru_cache استفاده کن.")

    def _visit_loop(self, node):
        self.loop_depth += 1
        fn = self.current_func
        self.max_depth[fn] = max(self.max_depth.get(fn, 0), self.loop_depth)
        if self.loop_depth >= 3:
            self.add(node, f"حلقه‌های تودرتو با عمق {self.loop_depth} در «{fn}» (پیچیدگی تقریبی O(n^{self.loop_depth})).")
        self.generic_visit(node)
        self.loop_depth -= 1

    visit_For = _visit_loop
    visit_While = _visit_loop

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if self.func_stack:
                self.func_calls[self.current_func].add(node.func.id)
            if node.func.id == "sorted" and self.loop_depth > 0:
                self.add(node, "sorted() داخل حلقه هر بار O(n log n) است. مرتب‌سازی را بیرون از حلقه انجام بده.")
        elif isinstance(node.func, ast.Attribute) and self.loop_depth > 0:
            if node.func.attr == "pop" and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == 0:
                self.add(node, "pop(0) روی لیست O(n) است. برای صف از collections.deque استفاده کن.")
            if node.func.attr == "insert" and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == 0:
                self.add(node, "insert(0, ...) روی لیست O(n) است. برای صف از collections.deque استفاده کن.")
        self.generic_visit(node)

    def visit_Compare(self, node):
        if self.loop_depth > 0 and any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops):
            comp = node.comparators[0]
            if isinstance(comp, (ast.List, ast.Tuple)):
                self.add(node, "جست‌وجوی `in` روی لیست داخل حلقه O(n) است. از set استفاده کن (O(1)).")
            elif isinstance(comp, ast.Name):
                self.add(node, f"جست‌وجوی `in` داخل حلقه. اگر «{comp.id}» لیست است، آن را به set تبدیل کن (احتمال کندی).")
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        is_str = (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)) \
                 or isinstance(node.value, ast.JoinedStr)
        if self.loop_depth > 0 and isinstance(node.op, ast.Add) and is_str:
            self.add(node, "الحاق رشته با += داخل حلقه هر بار کل رشته را کپی می‌کند. از list و ''.join(...) استفاده کن.")
        self.generic_visit(node)


def main():
    if len(sys.argv) < 2:
        print("استفاده: python index.py your_code.py")
        sys.exit(1)

    path = Path(sys.argv[1])
    tree = ast.parse(path.read_text(encoding="utf-8"))
    analyzer = CodeAnalyzer()
    analyzer.visit(tree)

    print(f"\n=== تحلیل {path.name} ===\n")
    print("تخمین پیچیدگی زمانی بر اساس عمق حلقه‌ها:")
    for fn, depth in analyzer.max_depth.items():
        print(f"  {fn:<25} {COMPLEXITY.get(depth, f'O(n^{depth})')}")

    print("\nمشکلات احتمالی:")
    if not analyzer.issues:
        print("  موردی پیدا نشد.")
    for line, msg in sorted(analyzer.issues):
        print(f"  خط {line}: {msg}")

    print("\nنکته: این تحلیل تخمینی و ایستاست. برای پیدا کردن گلوگاه واقعی از cProfile استفاده کن.")


if __name__ == "__main__":
    main()
