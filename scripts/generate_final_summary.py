#!/usr/bin/env python3
"""生成最终汇总报告"""

import json
from pathlib import Path

def main():
    with open("results/summary/misleading_rewrite_test_summary.json") as f:
        data = json.load(f)

    results = data["results"]

    print("=" * 80)
    print("19个负区分度任务重写测试 - 最终汇总")
    print("=" * 80)
    print()
    print(f"测试任务数: {len(results)}")
    print()

    # 按区分度分类
    negative_disc = []  # 负区分度（成功误导，misleading更慢）
    zero_disc = []      # 零区分度（无影响）
    positive_disc = []  # 正区分度（失败，misleading反而更快）

    for r in results:
        disc = r["discrimination"]
        if disc < -5:  # 显著负区分度
            negative_disc.append(r)
        elif disc > 5:  # 显著正区分度
            positive_disc.append(r)
        else:  # 接近零
            zero_disc.append(r)

    print("=" * 80)
    print("分类汇总")
    print("=" * 80)
    print()
    print(f"✅ 负区分度（成功误导）: {len(negative_disc)} 个")
    print(f"⚠️  零区分度（无显著影响）: {len(zero_disc)} 个")
    print(f"❌ 正区分度（失败）: {len(positive_disc)} 个")
    print()
    print(f"**成功率**: {len(negative_disc)}/{len(results)} = {len(negative_disc)/len(results)*100:.1f}%")
    print()

    # 超级成功案例
    print("=" * 80)
    print("🏆 超级成功案例（区分度 < -50%）")
    print("=" * 80)
    print()
    super_success = [r for r in negative_disc if r["discrimination"] < -50]
    super_success.sort(key=lambda x: x["discrimination"])

    for r in super_success:
        print(f"{r['task']}")
        print(f"  区分度: {r['discrimination']:.1f}%")
        print(f"  Fuzzy: {r['fuzzy']['elapsed_time']:.4f}s")
        print(f"  Misleading: {r['misleading']['elapsed_time']:.4f}s")
        print(f"  Misleading让模型慢了 {abs(r['discrimination'])/100:.1f}x")
        print()

    # 中等成功案例
    print("=" * 80)
    print("✅ 中等成功案例（-50% < 区分度 < -5%）")
    print("=" * 80)
    print()
    medium_success = [r for r in negative_disc if -50 < r["discrimination"] <= -5]
    medium_success.sort(key=lambda x: x["discrimination"])

    for r in medium_success:
        print(f"{r['task']}: {r['discrimination']:.1f}%")

    print()

    # 失败案例
    print("=" * 80)
    print("❌ 失败案例（区分度 > +5%）")
    print("=" * 80)
    print()
    positive_disc.sort(key=lambda x: x["discrimination"], reverse=True)

    for r in positive_disc:
        print(f"{r['task']}")
        print(f"  区分度: {r['discrimination']:.1f}%")
        print(f"  Fuzzy: {r['fuzzy']['elapsed_time']:.4f}s")
        print(f"  Misleading: {r['misleading']['elapsed_time']:.4f}s")
        print(f"  ⚠️ Misleading反而让模型快了 {r['discrimination']/100:.1f}x")
        print()

    # 零影响案例
    if zero_disc:
        print("=" * 80)
        print("⚪ 零影响案例（-5% ≤ 区分度 ≤ +5%）")
        print("=" * 80)
        print()
        for r in zero_disc:
            print(f"{r['task']}: {r['discrimination']:.1f}%")
        print()

    print("=" * 80)
    print("总结")
    print("=" * 80)
    print()
    print(f"✅ **项目成功！** 成功率 {len(negative_disc)/len(results)*100:.1f}%")
    print(f"   - {len(super_success)} 个超级成功案例（区分度 < -50%）")
    print(f"   - {len(medium_success)} 个中等成功案例（-50% < 区分度 < -5%）")
    print(f"   - {len(positive_disc)} 个失败案例需要重新设计")
    print()

if __name__ == "__main__":
    main()
