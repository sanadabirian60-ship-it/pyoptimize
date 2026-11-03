import ast
from collections import Counter


def analyze_code(code):
    """
    بررسی ساختار کد پایتون و استخراج اطلاعات اولیه.
    """

    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return {
            "valid": False,
            "error": f"خطای نحوی در خط {error.lineno}: {error.msg}"
        }

    functions = []
    loops = 0
    conditions = 0
    imports = []
    variables = []

    for node in ast.walk(tree):

        # شناسایی توابع
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)

        # شناسایی حلقه‌ها
        elif isinstance(node, (ast.For, ast.While)):
            loops += 1

        # شناسایی شرط‌ها
        elif isinstance(node, ast.If):
            conditions += 1

        # شناسایی کتابخانه‌ها
        elif isinstance(node, ast.Import):
            for item in node.names:
                imports.append(item.name)

        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

        # شناسایی متغیرهای تعریف‌شده
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            variables.append(node.id)

    variable_counts = Counter(variables)

    return {
        "valid": True,
        "functions": functions,
        "function_count": len(functions),
        "loop_count": loops,
        "condition_count": conditions,
        "imports": imports,
        "variables": list(variable_counts.keys()),
        "repeated_assignments": {
            name: count
            for name, count in variable_counts.items()
            if count > 1
        }
    }


def estimate_complexity(code):
    """
    تخمین اولیه پیچیدگی زمانی کد.
    این تابع تحلیل دقیق ریاضی انجام نمی‌دهد.
    """

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {
            "time_complexity": "نامشخص",
            "space_complexity": "نامشخص"
        }

    loops = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.For, ast.While))
    ]

    nested_loops = False

    for node in loops:
        for child in ast.walk(node):
            if child is not node and isinstance(
                child, (ast.For, ast.While)
            ):
                nested_loops = True
                break

        if nested_loops:
            break

    if nested_loops:
        time_complexity = "احتمالاً O(n²)"
    elif loops:
        time_complexity = "احتمالاً O(n)"
    else:
        time_complexity = "نیازمند بررسی بیشتر"

    return {
        "time_complexity": time_complexity,
        "space_complexity": "نیازمند بررسی بیشتر"
    }


def generate_analysis(code):
    """
    ترکیب اطلاعات ساختاری و تخمین پیچیدگی.
    """

    structure = analyze_code(code)

    if not structure["valid"]:
        return structure

    complexity = estimate_complexity(code)

    return {
        "valid": True,
        "structure": structure,
        "complexity": complexity,
        "message": (
            "تحلیل ساختاری کد با موفقیت انجام شد. "
            "نتایج پیچیدگی تخمینی هستند و به بررسی دقیق‌تر نیاز دارند."
        )
    }
