#!/usr/bin/env python3
"""对比旧任务和新任务的 fuzzy vs misleading 区分度."""

import json
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path(__file__).parent.parent / "results"

OLD_TASKS = [f"ipb_dev_{i:03d}" for i in range(3, 15)]  # 003~014
NEW_TASKS = ["ipb_dev_015", "ipb_dev_016", "ipb_dev_026", "ipb_dev_027", "ipb_dev_033"]


def analyze_task(task, variants):
    """分析一个任务的通过率."""
    results = defaultdict(lambda: {"passed": 0, "total": 0})

    for variant in variants:
        pattern = f"{task}_{variant}_*.json"
        for f in RESULTS_DIR.glob(pattern):
            try:
                with open(f, encoding='utf-8') as fp:
                    data = json.load(fp)
                    results[variant]["total"] += 1
                    if data.get("passed"):
                        results[variant]["passed"] += 1
            except Exception:
                pass

    return results


def print_comparison():
    """打印旧任务 vs 新任务的对比."""
    print("=" * 90)
    print(" 旧任务（ipb_dev_003~014）vs 新任务（015,016,026,027,033）区分度对比")
    print("=" * 90)
    print()

    # 旧任务
    print("【旧任务】每个任务 10 次 × 4 个变体（exact/fuzzy/misleading/target_known）")
    print("-" * 90)

    old_fuzzy_total = 0
    old_fuzzy_passed = 0
    old_mis_total = 0
    old_mis_passed = 0

    for task in OLD_TASKS:
        results = analyze_task(task, ["fuzzy", "misleading"])
        fuzzy = results["fuzzy"]
        mis = results["misleading"]

        if fuzzy["total"] == 0:
            continue

        fuzzy_rate = fuzzy["passed"] / fuzzy["total"] * 100 if fuzzy["total"] else 0
        mis_rate = mis["passed"] / mis["total"] * 100 if mis["total"] else 0
        gap = fuzzy_rate - mis_rate

        old_fuzzy_total += fuzzy["total"]
        old_fuzzy_passed += fuzzy["passed"]
        old_mis_total += mis["total"]
        old_mis_passed += mis["passed"]

        status = "✓" if abs(gap) >= 20 else " "
        print(f"{status} {task}: fuzzy {fuzzy['passed']}/{fuzzy['total']} ({fuzzy_rate:3.0f}%)  "
              f"mis {mis['passed']}/{mis['total']} ({mis_rate:3.0f}%)  gap={gap:+4.0f}%")

    old_fuzzy_rate = old_fuzzy_passed / old_fuzzy_total * 100 if old_fuzzy_total else 0
    old_mis_rate = old_mis_passed / old_mis_total * 100 if old_mis_total else 0
    old_gap = old_fuzzy_rate - old_mis_rate

    print()
    print(f"旧任务总计: fuzzy {old_fuzzy_passed}/{old_fuzzy_total} ({old_fuzzy_rate:.1f}%)  "
          f"mis {old_mis_passed}/{old_mis_total} ({old_mis_rate:.1f}%)  "
          f"MisleadingGap={old_gap:+.1f}%")

    # 新任务
    print()
    print("【新任务】每个任务 3 次 × 2 个变体（fuzzy_context/misleading）")
    print("-" * 90)

    new_fuzzy_total = 0
    new_fuzzy_passed = 0
    new_mis_total = 0
    new_mis_passed = 0

    for task in NEW_TASKS:
        results = analyze_task(task, ["fuzzy_context", "misleading"])
        fuzzy = results["fuzzy_context"]
        mis = results["misleading"]

        if fuzzy["total"] == 0 and mis["total"] == 0:
            continue

        fuzzy_rate = fuzzy["passed"] / fuzzy["total"] * 100 if fuzzy["total"] else 0
        mis_rate = mis["passed"] / mis["total"] * 100 if mis["total"] else 0
        gap = fuzzy_rate - mis_rate

        new_fuzzy_total += fuzzy["total"]
        new_fuzzy_passed += fuzzy["passed"]
        new_mis_total += mis["total"]
        new_mis_passed += mis["passed"]

        status = "✓" if abs(gap) >= 20 else " "
        print(f"{status} {task}: fuzzy {fuzzy['passed']}/{fuzzy['total']} ({fuzzy_rate:3.0f}%)  "
              f"mis {mis['passed']}/{mis['total']} ({mis_rate:3.0f}%)  gap={gap:+4.0f}%")

    new_fuzzy_rate = new_fuzzy_passed / new_fuzzy_total * 100 if new_fuzzy_total else 0
    new_mis_rate = new_mis_passed / new_mis_total * 100 if new_mis_total else 0
    new_gap = new_fuzzy_rate - new_mis_rate

    print()
    print(f"新任务总计: fuzzy {new_fuzzy_passed}/{new_fuzzy_total} ({new_fuzzy_rate:.1f}%)  "
          f"mis {new_mis_passed}/{new_mis_total} ({new_mis_rate:.1f}%)  "
          f"MisleadingGap={new_gap:+.1f}%")

    # 总结
    print()
    print("=" * 90)
    print(" 结论")
    print("=" * 90)
    print(f"旧任务 MisleadingGap: {old_gap:+.1f}%")
    print(f"新任务 MisleadingGap: {new_gap:+.1f}%")
    print()
    if abs(new_gap) < 10:
        print("⚠ 新任务的 misleading 区分度较弱，可能需要：")
        print("  1. 调整 misleading 提示（更有迷惑性）")
        print("  2. 检查任务难度（太简单 agent 会忽略提示，太难两边都过不了）")
        print("  3. 增加实验次数（目前只有 3 次，统计噪声较大）")
    else:
        print("✓ 新任务显示了有效的 misleading 效果")


if __name__ == "__main__":
    print_comparison()
