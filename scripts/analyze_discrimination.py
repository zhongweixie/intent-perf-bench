#!/usr/bin/env python3
"""分析全量19个任务的测试结果"""

import json
import glob
from pathlib import Path
from collections import defaultdict

# 全部19个任务
ALL_TASKS = [
    "ipb_cuda_009_matrix_transpose",
    "ipb_dev_003",
    "ipb_dev_012",
    "ipb_cuda_001",
    "ipb_dev_008",
    "ipb_dev_032",
    "ipb_dev_027",
    "ipb_dev_007",
    "ipb_dev_004",
    "ipb_cpu_001_gaussian_blur",
    "ipb_dev_037",
    "ipb_dev_036",
    "ipb_dev_041",
    "ipb_dev_010",
    "ipb_dev_038",
    "ipb_dev_009",
    "ipb_dev_016",
    "ipb_dev_040",
    "ipb_cuda_004",
]

def load_latest_result(task, variant):
    """加载任务的最新结果"""
    pattern = f"results/{task}_{variant}_*.json"
    files = sorted(glob.glob(pattern), key=lambda x: Path(x).stat().st_mtime, reverse=True)

    if not files:
        return None

    with open(files[0]) as f:
        return json.load(f)

def extract_performance_metric(result):
    """提取性能指标（优先用speedup，否则用elapsed_time）"""
    if result.get('speedup'):
        return ('speedup', result['speedup'])
    elif result.get('elapsed_time') is not None:
        return ('time', result['elapsed_time'])
    return (None, None)

def calculate_discrimination(fuzzy_result, misleading_result):
    """
    计算区分度
    - 基于speedup: (misleading_speedup - fuzzy_speedup) / fuzzy_speedup × 100%
    - 基于time: (fuzzy_time - misleading_time) / fuzzy_time × 100%

    正区分度 = Misleading反而帮助了模型（失败）
    负区分度 = Misleading成功误导了模型（成功）
    """
    f_type, f_val = extract_performance_metric(fuzzy_result)
    m_type, m_val = extract_performance_metric(misleading_result)

    if f_type != m_type or f_type is None:
        return None, f_type, f_val, m_val

    if f_type == 'speedup':
        # speedup越大越好，misleading应该让speedup变小
        disc = (m_val - f_val) / f_val * 100
    else:  # time
        # time越小越好，misleading应该让time变大
        disc = (f_val - m_val) / f_val * 100

    return disc, f_type, f_val, m_val

def main():
    print("=" * 100)
    print("全量19任务 Misleading Prompt 测试结果分析")
    print("=" * 100)
    print()

    results = []

    for task in ALL_TASKS:
        fuzzy = load_latest_result(task, "fuzzy")
        misleading = load_latest_result(task, "misleading")

        if not fuzzy:
            print(f"⚠️  {task}: 缺少 fuzzy 结果")
            continue

        if not misleading:
            print(f"⚠️  {task}: 缺少 misleading 结果")
            continue

        disc, metric_type, f_val, m_val = calculate_discrimination(fuzzy, misleading)

        if disc is None:
            print(f"⚠️  {task}: 无法计算区分度")
            continue

        results.append({
            'task': task,
            'discrimination': disc,
            'metric_type': metric_type,
            'fuzzy_value': f_val,
            'misleading_value': m_val,
            'fuzzy_turns': fuzzy.get('turns', 0),
            'misleading_turns': misleading.get('turns', 0),
            'fuzzy_passed': fuzzy.get('passed', False),
            'misleading_passed': misleading.get('passed', False),
        })

    # 按区分度排序（从低到高，负数在前）
    results.sort(key=lambda x: x['discrimination'])

    print(f"{'任务':<45} {'指标':<8} {'Fuzzy':<12} {'Misleading':<12} {'区分度':<12} {'状态'}")
    print("-" * 100)

    negative_count = 0
    positive_count = 0
    zero_count = 0

    for r in results:
        disc_str = f"{r['discrimination']:+.1f}%"

        if r['discrimination'] < -5:
            status = "✅ 成功"
            negative_count += 1
        elif r['discrimination'] < 0:
            status = "✅ 轻微成功"
            negative_count += 1
        elif r['discrimination'] == 0:
            status = "⚠️  无影响"
            zero_count += 1
        else:
            status = "❌ 失败"
            positive_count += 1

        metric_label = "speedup" if r['metric_type'] == 'speedup' else "time(s)"
        f_str = f"{r['fuzzy_value']:.4f}" if r['metric_type'] == 'time' else f"{r['fuzzy_value']:.2f}x"
        m_str = f"{r['misleading_value']:.4f}" if r['metric_type'] == 'time' else f"{r['misleading_value']:.2f}x"

        print(f"{r['task']:<45} {metric_label:<8} {f_str:<12} {m_str:<12} {disc_str:<12} {status}")

    print("-" * 100)
    print()
    print(f"✅ 负区分度（Misleading成功误导）: {negative_count} 个")
    print(f"⚠️  零区分度（无影响）: {zero_count} 个")
    print(f"❌ 正区分度（Misleading反而帮助）: {positive_count} 个")
    print()
    print(f"📊 误导成功率: {negative_count}/{len(results)} = {negative_count/len(results)*100:.1f}%")
    print()

    # 统计分布
    print("=" * 100)
    print("区分度分布")
    print("=" * 100)
    print()

    ranges = [
        ("超级成功", lambda d: d <= -100),
        ("很成功", lambda d: -100 < d <= -50),
        ("成功", lambda d: -50 < d <= -10),
        ("轻微成功", lambda d: -10 < d < 0),
        ("无影响", lambda d: d == 0),
        ("轻微失败", lambda d: 0 < d <= 10),
        ("失败", lambda d: 10 < d <= 50),
        ("严重失败", lambda d: d > 50),
    ]

    for label, pred in ranges:
        count = sum(1 for r in results if pred(r['discrimination']))
        if count > 0:
            print(f"{label:>12}: {count:2d} 个")

    print()

    # 列出失败案例
    failed = [r for r in results if r['discrimination'] > 0]
    if failed:
        print("=" * 100)
        print("需要改进的任务（Misleading反而帮助了模型）")
        print("=" * 100)
        print()
        for r in failed:
            print(f"  • {r['task']}")
            print(f"    区分度: {r['discrimination']:+.1f}%")
            print(f"    Fuzzy轮数: {r['fuzzy_turns']}, Misleading轮数: {r['misleading_turns']}")
            print()

if __name__ == "__main__":
    main()
