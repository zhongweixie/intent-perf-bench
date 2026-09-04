#!/usr/bin/env python3
"""分析新任务（ipb_dev_015~033）的 fuzzy_context vs misleading 结果."""

import json
import os
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "results"
NEW_TASKS = ["ipb_dev_015", "ipb_dev_016", "ipb_dev_026", "ipb_dev_027", "ipb_dev_033"]
VARIANTS = ["fuzzy_context", "misleading"]


def load_results():
    """加载所有新任务的结果文件."""
    data = defaultdict(lambda: defaultdict(list))

    for task in NEW_TASKS:
        for variant in VARIANTS:
            pattern = f"{task}_{variant}_"
            for f in RESULTS_DIR.glob(f"{pattern}*.json"):
                try:
                    with open(f, encoding='utf-8') as fp:
                        result = json.load(fp)
                        data[task][variant].append({
                            "file": f.name,
                            "passed": result.get("passed", False),
                            "turns": result.get("turns", 0),
                            "model": result.get("model", ""),
                        })
                except Exception as e:
                    print(f"警告：无法读取 {f.name}: {e}")

    return data


def print_summary(data):
    """打印汇总统计."""
    print("=" * 80)
    print(" 新任务评测汇总：fuzzy_context vs misleading")
    print("=" * 80)
    print()

    for task in NEW_TASKS:
        variants_data = data[task]
        if not any(variants_data.values()):
            print(f"⚠ {task}: 无结果")
            continue

        print(f"📋 {task}")
        print("-" * 80)

        for variant in VARIANTS:
            runs = variants_data[variant]
            if not runs:
                print(f"  {variant:20s}: 无结果")
                continue

            total = len(runs)
            passed = sum(1 for r in runs if r["passed"])
            pass_rate = passed / total * 100 if total > 0 else 0
            avg_turns = sum(r["turns"] for r in runs) / total if total > 0 else 0

            status = "✓" if pass_rate >= 50 else "✗"
            print(f"  {variant:20s}: {status} {passed}/{total} 通过 ({pass_rate:.0f}%)  |  平均 {avg_turns:.1f} 轮")

        print()

    # 总体统计
    print("=" * 80)
    print(" 总体对比")
    print("=" * 80)

    for variant in VARIANTS:
        all_runs = [r for task_data in data.values() for r in task_data[variant]]
        if not all_runs:
            continue

        total = len(all_runs)
        passed = sum(1 for r in all_runs if r["passed"])
        pass_rate = passed / total * 100 if total > 0 else 0
        avg_turns = sum(r["turns"] for r in all_runs) / total if total > 0 else 0

        print(f"{variant:20s}: {passed}/{total} 通过 ({pass_rate:.1f}%)  |  平均 {avg_turns:.1f} 轮")

    print()


def main():
    data = load_results()
    print_summary(data)


if __name__ == "__main__":
    main()
