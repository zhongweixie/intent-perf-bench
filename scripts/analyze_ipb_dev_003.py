#!/usr/bin/env python3
"""分析 ipb_dev_003 测试结果。"""

import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "results"

def load_results():
    """加载所有 ipb_dev_003 结果。"""
    results = []
    for f in RESULTS_DIR.glob("ipb_dev_003_*.json"):
        try:
            data = json.loads(f.read_text())
            results.append(data)
        except Exception as e:
            print(f"⚠ 跳过 {f.name}: {e}")
    return results

def analyze():
    results = load_results()
    if not results:
        print("未找到结果文件")
        return

    print(f"\n共加载 {len(results)} 个结果\n")
    print("=" * 80)

    # 按 model + variant 分组
    by_config = defaultdict(list)
    for r in results:
        model_short = r["model"].split("-")[-1] if "haiku" in r["model"].lower() else r["model"].split("-")[-1].capitalize()
        if "haiku" in r["model"].lower() and "4-5" in r["model"]:
            model_short = "Haiku-4.5"
        elif "sonnet" in r["model"].lower():
            model_short = "Sonnet-5"
        key = (model_short, r["variant"])
        by_config[key].append(r)

    # 打印结果表格
    print(f"{'Model':<12} {'Variant':<15} {'通过':<6} {'轮数':<6} {'接触目标':<10} {'修改正确文件':<12}")
    print("-" * 80)

    for (model, variant), runs in sorted(by_config.items()):
        for r in runs:
            passed = "✓" if r["modified_causal_file"] else "✗"
            turns = r["turns"]
            contact = r.get("turns_to_real_target", "N/A")
            modified = "✓" if r["modified_causal_file"] else "✗"

            print(f"{model:<12} {variant:<15} {passed:<6} {turns:<6} {str(contact):<10} {modified:<12}")

    print("\n" + "=" * 80)

    # 统计成功率
    print("\n## 成功率统计\n")
    success_by_variant = defaultdict(lambda: {"total": 0, "passed": 0})
    for r in results:
        variant = r["variant"]
        success_by_variant[variant]["total"] += 1
        if r["modified_causal_file"]:
            success_by_variant[variant]["passed"] += 1

    for variant in ["exact", "target_known", "fuzzy", "misleading"]:
        if variant in success_by_variant:
            stats = success_by_variant[variant]
            rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"{variant:>15}: {stats['passed']}/{stats['total']} = {rate:.1f}%")

if __name__ == "__main__":
    analyze()
