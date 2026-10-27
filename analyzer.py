import random
import timeit
from typing import List, TypeVar

T = TypeVar("T")


# ==========================================
# 1. نسخه اولیه (Original Version)
# ==========================================

def find_common_elements(list_a: List[T],
                         list_b: List[T]) -> List[T]:
    """
    پیدا کردن عناصر مشترک دو لیست بدون تکرار.
    ترتیب اولین ظاهر شدن عناصر مطابق list_a است.
    """
    result = []

    for item in list_a:
        if item in list_b:
            if item not in result:
                result.append(item)

    return result


# ==========================================
# 2. نسخه بهینه‌شده (Optimized Version)
# ==========================================

def find_common_elements_optimized(
    list_a: List[T],
    list_b: List[T]
) -> List[T]:
    """
    نسخه بهینه‌شده با استفاده از set.
    ترتیب خروجی مطابق اولین ظاهر شدن عناصر در list_a است.

    نکته: عناصر باید قابل هش شدن (hashable) باشند.
    """
    set_b = set(list_b)
    seen = set()
    result = []

    for item in list_a:
        if item in set_b and item not in seen:
            result.append(item)
            seen.add(item)

    return result


# ==========================================
# 3. تست صحت (Correctness Tests)
# ==========================================

def run_tests():
    test_cases = [
        ([1, 2, 3], [2, 3, 4], [2, 3]),
        ([1, 1, 2, 2, 3], [1, 2], [1, 2]),
        ([], [1, 2, 3], []),
        ([1, 2, 3], [], []),
        ([5, 4, 3, 2], [2, 3, 5], [5, 3, 2]),
        (["a", "b", "a"], ["a", "c"], ["a"]),
    ]

    for index, (list_a, list_b, expected) in enumerate(
        test_cases, start=1
    ):
        original = find_common_elements(list_a, list_b)
        optimized = find_common_elements_optimized(
            list_a, list_b
        )

        assert original == expected, (
            f"Original failed on test {index}: {original}"
        )
        assert optimized == expected, (
            f"Optimized failed on test {index}: {optimized}"
        )

    print("All correctness tests passed!")


# ==========================================
# 4. بررسی پیچیدگی الگوریتم
# ==========================================

def print_complexity_analysis():
    print("\n" + "=" * 55)
    print("COMPLEXITY ANALYSIS")
    print("=" * 55)

    print("""
Original Version:
-----------------
Let n = len(list_a), m = len(list_b).

- Searching in list_b: O(m) per item.
- Searching in result: up to O(n) per item.
- Total time: O(n*m + n^2).
- If n and m are similar: O(n^2).
- Extra space: O(n).

Optimized Version:
------------------
- Building set_b: expected O(m).
- Membership checks: expected O(1) per item.
- Total expected time: O(n + m).
- Extra space: O(n + m).

Important:
These are expected bounds for typical hash-table behavior.
Worst-case hash-table operations can be slower.
The optimized version requires hashable elements.
""")


# ==========================================
# 5. بنچمارک (Benchmark)
# ==========================================

def run_benchmark():
    random.seed(42)

    size = 3000

    list_a = [
        random.randint(0, size)
        for _ in range(size)
    ]

    list_b = [
        random.randint(0, size)
        for _ in range(size)
    ]

    # ابتدا مطمئن می‌شویم خروجی دو نسخه برابر است.
    original_result = find_common_elements(
        list_a, list_b
    )

    optimized_result = find_common_elements_optimized(
        list_a, list_b
    )

    assert original_result == optimized_result, (
        "The two implementations returned different results!"
    )

    print("\n" + "=" * 55)
    print("BENCHMARK")
    print("=" * 55)

    print(f"Input size A: {len(list_a)}")
    print(f"Input size B: {len(list_b)}")

    repetitions = 3

    original_timer = timeit.Timer(
        lambda: find_common_elements(list_a, list_b)
    )

    optimized_timer = timeit.Timer(
        lambda: find_common_elements_optimized(
            list_a, list_b
        )
    )

    original_times = original_timer.repeat(
        repeat=repetitions, number=1
    )

    optimized_times = optimized_timer.repeat(
        repeat=repetitions, number=1
    )

    original_best = min(original_times)
    optimized_best = min(optimized_times)

    print(
        f"\nOriginal best time: "
        f"{original_best:.6f} seconds"
    )

    print(
        f"Optimized best time: "
        f"{optimized_best:.6f} seconds"
    )

    if optimized_best > 0:
        speedup = original_best / optimized_best

        print(f"Speedup: {speedup:.2f}x")

    print(
        "\nNote: Results depend on your computer, "
        "Python version, and input data."
    )


# ==========================================
# 6. اجرای برنامه
# ==========================================

def main():
    print("=" * 55)
    print("PYOPTIMIZE: CODE ANALYSIS AND OPTIMIZATION")
    print("=" * 55)

    run_tests()
    print_complexity_analysis()
    run_benchmark()

    print("\nAnalysis completed successfully.")


if __name__ == "__main__":
    main()
