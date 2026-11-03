import ast
import argparse
from pathlib import Path


def analyze_code(source_code):
    """
    تحلیل ساختاری کد پایتون بدون اجرای آن.
    """

    try:
        tree = ast.parse(source_code)
    except SyntaxError as error:
        return {
            "success": False,
            "error": (
                f"خطای نحوی در خط {error.lineno}: "
                f"{error.msg}"
            )
        }

    functions = []
    classes = []
    loops = []
    conditions = []
    imports = []

    for node in ast.walk(tree):

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)

        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            loops.append(node)

        elif isinstance(node, (ast.If, ast.IfExp)):
            conditions.append(node)

        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node)

    # بررسی تقریبی وجود حلقه‌های تو در تو
    nested_loops = 0

    for loop in loops:
        for child in ast.walk(loop):
            if child is not loop and isinstance(
                child, (ast.For, ast.AsyncFor, ast.While)
            ):
                nested_loops += 1
                break

    # بررسی استفاده از ساختارهای داده
    uses_list = any(
        isinstance(node, (ast.List, ast.ListComp))
        for node in ast.walk(tree)
    )

    uses_set = any(
        isinstance(node, (ast.Set, ast.SetComp))
        for node in ast.walk(tree)
    )

    uses_dict = any(
        isinstance(node, (ast.Dict, ast.DictComp))
        for node in ast.walk(tree)
    )

    # بررسی عملیات بررسی عضویت
    membership_checks = sum(
        isinstance(node, ast.Compare)
        and any(
            isinstance(op, (ast.In, ast.NotIn))
            for op in node.ops
        )
        for node in ast.walk(tree)
    )

    return {
        "success": True,
        "functions": functions,
        "classes": classes,
        "loops": len(loops),
        "nested_loops": nested_loops,
        "conditions": len(conditions),
        "imports": len(imports),
        "membership_checks": membership_checks,
        "uses_list": uses_list,
        "uses_set": uses_set,
        "uses_dict": uses_dict
    }


def print_report(result):

    if not result["success"]:
        print("\nخطا در تحلیل کد:")
        print(result["error"])
        return

    print("\n========== PyOptimize Report ==========\n")

    print("تعداد تابع‌ها:", len(result["functions"]))
    print("تعداد کلاس‌ها:", len(result["classes"]))
    print("تعداد حلقه‌ها:", result["loops"])
    print("تعداد شرط‌ها:", result["conditions"])
    print("تعداد دستورهای import:", result["imports"])
    print("بررسی‌های عضویت:", result["membership_checks"])

    print("\nنام تابع‌ها:")
    if result["functions"]:
        for name in result["functions"]:
            print("-", name)
    else:
        print("تابعی پیدا نشد.")

    print("\nنام کلاس‌ها:")
    if result["classes"]:
        for name in result["classes"]:
            print("-", name)
    else:
        print("کلاسی پیدا نشد.")

    print("\nساختارهای داده:")
    print("List:", "استفاده شده" if result["uses_list"] else "پیدا نشد")
    print("Set:", "استفاده شده" if result["uses_set"] else "پیدا نشد")
    print("Dictionary:", "استفاده شده" if result["uses_dict"] else "پیدا نشد")

    print("\nبررسی حلقه‌ها:")
    if result["nested_loops"]:
        print("حلقه‌های تو در تو شناسایی شدند.")
        print("پیچیدگی ممکن است در برخی مسیرها بیشتر باشد.")
    else:
        print("حلقه تو در تو شناسایی نشد.")

    print("\nتوجه:")
    print(
        "این گزارش فقط ساختار کد را بررسی می‌کند. "
        "پیچیدگی دقیق الگوریتم از این اطلاعات به‌تنهایی مشخص نمی‌شود."
    )

    print("\n=======================================\n")


def main():

    parser = argparse.ArgumentParser(
        description="PyOptimize - Python Code Analyzer"
    )

    parser.add_argument(
        "file",
        help="مسیر فایل پایتون برای تحلیل"
    )

    args = parser.parse_args()

    file_path = Path(args.file)

    if not file_path.is_file():
        print("فایل موردنظر پیدا نشد.")
        return

    if file_path.suffix != ".py":
        print("لطفاً یک فایل با پسوند py انتخاب کنید.")
        return

    try:
        source_code = file_path.read_text(encoding="utf-8")
    except OSError as error:
        print("خطا در خواندن فایل:", error)
        return

    result = analyze_code(source_code)
    print_report(result)


if __name__ == "__main__":
    main()
