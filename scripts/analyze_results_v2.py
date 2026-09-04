#!/usr/bin/env python3
"""
分析 IPB 批量评测结果 - 完整版

提取：
- 成功率（按任务、变体、模型）
- 性能改进
- Fuzzy Gap 和 Misleading Gap
- 模型对比
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def main():
    results_dir = Path(__file__).parent.parent / 'results'

    # 只分析最新批次（时间戳 1787286386 及之后）
    files = sorted(results_dir.glob('ipb_*.json'))
    recent = [f for f in files if 'run17872' in f.name]

    print(f"分析 {len(recent)} 个结果文件\n")

    # 解析所有结果
    results = []
    for fpath in recent:
        with open(fpath) as f:
            data = json.load(f)
            results.append(data)

    # 按任务和变体分组
    by_task = defaultdict(lambda: defaultdict(list))
    for r in results:
        task = r['task_id']
        variant = r['variant']
        model = r['model']
        by_task[task][variant].append(r)

    print("="*80)
    print("详细成功率统计")
    print("="*80)
    print(f"{'任务':<40} {'变体':<12} {'模型':<18} {'改动':<8} {'轮数':<8}")
    print("-"*80)

    # 收集汇总数据
    task_summary = defaultdict(lambda: {'exact': [], 'fuzzy': [], 'misleading': []})

    for task in sorted(by_task.keys()):
        for variant in ['exact', 'fuzzy', 'misleading']:
            runs = by_task[task].get(variant, [])
            for r in runs:
                model = r['model']
                has_diff = len(r.get('final_diff', '')) > 100
                turns = r.get('turns', 0)

                print(f"{task:<40} {variant:<12} {model:<18} {'✓' if has_diff else '✗':<8} {turns:<8}")

                task_summary[task][variant].append({
                    'model': model,
                    'success': has_diff,
                    'turns': turns
                })

    print("\n" + "="*80)
    print("任务级汇总")
    print("="*80)

    for task in sorted(task_summary.keys()):
        print(f"\n{task}")

        for variant in ['exact', 'fuzzy', 'misleading']:
            runs = task_summary[task][variant]
            success_count = sum(1 for r in runs if r['success'])
            total = len(runs)

            luna_success = sum(1 for r in runs if 'luna' in r['model'] and r['success'])
            terra_success = sum(1 for r in runs if 'terra' in r['model'] and r['success'])

            print(f"  {variant:<12}  成功: {success_count}/{total}  (luna: {luna_success}, terra: {terra_success})")

    print("\n" + "="*80)
    print("Gap 分析")
    print("="*80)

    for task in sorted(task_summary.keys()):
        exact_success = sum(1 for r in task_summary[task]['exact'] if r['success'])
        fuzzy_success = sum(1 for r in task_summary[task]['fuzzy'] if r['success'])
        misleading_success = sum(1 for r in task_summary[task]['misleading'] if r['success'])

        exact_rate = exact_success / 2.0
        fuzzy_rate = fuzzy_success / 2.0
        misleading_rate = misleading_success / 2.0

        fuzzy_gap = exact_rate - fuzzy_rate
        misleading_gap = exact_rate - misleading_rate

        print(f"\n{task}")
        print(f"  Exact:      {exact_success}/2  ({exact_rate*100:.0f}%)")
        print(f"  Fuzzy:      {fuzzy_success}/2  ({fuzzy_rate*100:.0f}%)  Gap: {fuzzy_gap*100:+.0f}%")
        print(f"  Misleading: {misleading_success}/2  ({misleading_rate*100:.0f}%)  Gap: {misleading_gap*100:+.0f}%")

    print("\n" + "="*80)
    print("模型对比")
    print("="*80)

    luna_total = sum(1 for r in results if 'luna' in r['model'] and len(r.get('final_diff', '')) > 100)
    terra_total = sum(1 for r in results if 'terra' in r['model'] and len(r.get('final_diff', '')) > 100)

    print(f"\ngpt-5.6-luna:  {luna_total}/15  ({luna_total/15*100:.1f}%)")
    print(f"gpt-5.6-terra: {terra_total}/15  ({terra_total/15*100:.1f}%)")

    print("\n" + "="*80)
    print("总结")
    print("="*80)
    total_success = sum(1 for r in results if len(r.get('final_diff', '')) > 100)
    print(f"总成功率: {total_success}/{len(results)}  ({total_success/len(results)*100:.1f}%)")
    print(f"任务数: {len(task_summary)}")
    print(f"变体数: 3 (exact, fuzzy, misleading)")
    print(f"模型数: 2 (luna, terra)")

if __name__ == "__main__":
    main()
