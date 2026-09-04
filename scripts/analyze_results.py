#!/usr/bin/env python3
"""
分析 IPB 批量评测结果

从 results/*.json 提取：
- 成功率（按任务、变体、模型）
- 性能改进分布
- Fuzzy Gap 和 Misleading Gap
- 模型对比
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def parse_result_file(path):
    """解析单个结果文件"""
    with open(path) as f:
        data = json.load(f)

    # 从文件名提取元信息
    name = path.stem
    parts = name.split('_')

    # 识别任务 ID
    if name.startswith('ipb_cpu_'):
        task_id = '_'.join(parts[:3])  # ipb_cpu_001
        variant = parts[3] if len(parts) > 3 else 'unknown'
    elif name.startswith('ipb_cuda_'):
        if 'l2norm' in name:
            task_id = 'ipb_cuda_005_l2norm_reduction'
            variant = parts[4] if len(parts) > 4 else 'unknown'
        else:
            task_id = '_'.join(parts[:2])
            variant = parts[2] if len(parts) > 2 else 'unknown'
    else:
        return None

    # 从轨迹或 diff 判断是否成功
    final_diff = data.get('final_diff', '')
    trajectory = data.get('trajectory', [])

    # 简单启发式：有 diff 且轨迹有工具调用视为尝试了优化
    attempted = len(trajectory) > 5
    has_changes = len(final_diff.strip()) > 50

    return {
        'task_id': task_id,
        'variant': variant,
        'attempted': attempted,
        'has_changes': has_changes,
        'turns': len([t for t in trajectory if t.get('type') == 'text']),
        'tool_calls': len([t for t in trajectory if t.get('type') == 'tool_call']),
    }

def main():
    results_dir = Path(__file__).parent.parent / 'results'

    # 只分析最新一批（时间戳 1787286386 之后）
    files = sorted(results_dir.glob('ipb_*.json'))
    recent_files = [f for f in files if 'run17872' in f.name]

    print(f"分析 {len(recent_files)} 个结果文件\n")

    # 按任务和变体分组
    by_task_variant = defaultdict(list)

    for fpath in recent_files:
        result = parse_result_file(fpath)
        if result:
            key = (result['task_id'], result['variant'])
            by_task_variant[key].append(result)

    # 汇总统计
    print("="*80)
    print("任务成功率统计")
    print("="*80)
    print(f"{'任务':<35} {'变体':<12} {'尝试优化':<10} {'有代码改动':<12}")
    print("-"*80)

    task_stats = defaultdict(lambda: {'exact': 0, 'fuzzy': 0, 'misleading': 0})

    for (task_id, variant), results in sorted(by_task_variant.items()):
        attempted = sum(r['attempted'] for r in results)
        has_changes = sum(r['has_changes'] for r in results)
        total = len(results)

        print(f"{task_id:<35} {variant:<12} {attempted}/{total:<9} {has_changes}/{total:<11}")

        if has_changes > 0:
            task_stats[task_id][variant] = 1

    print("\n" + "="*80)
    print("Gap 分析")
    print("="*80)

    for task_id in sorted(task_stats.keys()):
        stats = task_stats[task_id]
        exact = stats['exact']
        fuzzy = stats['fuzzy']
        misleading = stats['misleading']

        fuzzy_gap = exact - fuzzy
        misleading_gap = exact - misleading

        print(f"\n{task_id}")
        print(f"  Exact:      {exact} / 2")
        print(f"  Fuzzy:      {fuzzy} / 2  (Gap: {fuzzy_gap:+d})")
        print(f"  Misleading: {misleading} / 2  (Gap: {misleading_gap:+d})")

    print("\n" + "="*80)
    print("模型对比")
    print("="*80)
    print("（需要从文件名或轨迹中提取模型信息，当前文件名未包含模型标识）")

    print("\n" + "="*80)
    print("总结")
    print("="*80)
    print(f"总评测数: {len(recent_files)}")
    print(f"任务数: {len(set(k[0] for k in by_task_variant.keys()))}")
    print(f"变体数: {len(set(k[1] for k in by_task_variant.keys()))}")

if __name__ == "__main__":
    main()
