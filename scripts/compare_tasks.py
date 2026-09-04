#!/usr/bin/env python3
"""比较 ipb_dev_001/002/003 的区分度"""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "results"

def load_results(task_id):
    """加载指定任务的所有结果"""
    results = []
    for path in RESULTS_DIR.glob(f"{task_id}_*.json"):
        try:
            data = json.loads(path.read_text())
            results.append(data)
        except:
            pass
    return results

def analyze_task(task_id):
    """分析单个任务的成功率和轮数"""
    results = load_results(task_id)
    if not results:
        return None

    by_variant = defaultdict(list)
    for r in results:
        variant = r.get("variant", "unknown")
        passed = r.get("passed", False)
        turns = r.get("turns", 0)
        model = r.get("model", "unknown")

        by_variant[variant].append({
            "model": model,
            "passed": passed,
            "turns": turns,
            "turns_to_target": r.get("turns_to_real_target")
        })

    # 计算每个变体的成功率
    stats = {}
    for variant, runs in by_variant.items():
        total = len(runs)
        passed = sum(1 for r in runs if r["passed"])
        success_rate = passed / total if total > 0 else 0

        avg_turns = sum(r["turns"] for r in runs if r["passed"]) / passed if passed > 0 else 0

        stats[variant] = {
            "success_rate": success_rate,
            "passed": passed,
            "total": total,
            "avg_turns": avg_turns
        }

    return stats

def main():
    tasks = ["ipb_dev_001", "ipb_dev_002", "ipb_dev_003"]

    print("\n" + "=" * 80)
    print("IPB Tasks 区分度对比")
    print("=" * 80)

    all_stats = {}
    for task_id in tasks:
        stats = analyze_task(task_id)
        if stats:
            all_stats[task_id] = stats

            print(f"\n## {task_id}")
            print("-" * 80)
            for variant in ["exact", "target_known", "fuzzy", "misleading"]:
                if variant in stats:
                    s = stats[variant]
                    rate = s["success_rate"] * 100
                    print(f"{variant:15s}: {s['passed']:2d}/{s['total']:2d} = {rate:5.1f}%  "
                          f"(avg {s['avg_turns']:.1f} turns)")

    # 计算区分度指标
    print("\n" + "=" * 80)
    print("区分度指标")
    print("=" * 80)

    for task_id, stats in all_stats.items():
        if "exact" in stats and "fuzzy" in stats and "misleading" in stats:
            exact_rate = stats["exact"]["success_rate"]
            fuzzy_rate = stats["fuzzy"]["success_rate"]
            misleading_rate = stats["misleading"]["success_rate"]

            fuzzy_gap = exact_rate - fuzzy_rate
            misleading_gap = fuzzy_rate - misleading_rate

            print(f"\n{task_id}:")
            print(f"  FuzzyGap      = {fuzzy_gap:+.2f}  (Exact - Fuzzy)")
            print(f"  MisleadingGap = {misleading_gap:+.2f}  (Fuzzy - Misleading)")
            print(f"  Total Gap     = {exact_rate - misleading_rate:+.2f}")

if __name__ == "__main__":
    main()
