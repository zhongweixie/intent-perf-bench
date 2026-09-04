#!/usr/bin/env python3
"""
对比 misleading 变体改进前后的效果

对比：
- 旧版 misleading（时间戳 17872）
- 新版 misleading（时间戳 17873+）
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_batch(files, label):
    """分析一批结果文件"""
    results = []
    for fpath in files:
        with open(fpath) as f:
            data = json.load(f)
            if data['variant'] == 'misleading':
                results.append(data)

    # 按任务和模型分组
    by_task = defaultdict(lambda: {'luna': [], 'terra': []})
    for r in results:
        task = r['task_id']
        model = 'luna' if 'luna' in r['model'] else 'terra'
        has_diff = len(r.get('final_diff', '')) > 100
        by_task[task][model].append(has_diff)

    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")
    print(f"{'任务':<40} {'Luna':<15} {'Terra':<15} {'总计':<15}")
    print('-'*80)

    total_success = 0
    total_count = 0

    for task in sorted(by_task.keys()):
        luna_success = sum(by_task[task]['luna'])
        luna_total = len(by_task[task]['luna'])
        terra_success = sum(by_task[task]['terra'])
        terra_total = len(by_task[task]['terra'])

        task_success = luna_success + terra_success
        task_total = luna_total + terra_total

        total_success += task_success
        total_count += task_total

        luna_rate = f"{luna_success}/{luna_total}" if luna_total > 0 else "N/A"
        terra_rate = f"{terra_success}/{terra_total}" if terra_total > 0 else "N/A"
        task_rate = f"{task_success}/{task_total}"

        print(f"{task:<40} {luna_rate:<15} {terra_rate:<15} {task_rate:<15}")

    print('-'*80)
    print(f"{'总计':<40} {'':<15} {'':<15} {total_success}/{total_count} ({total_success/total_count*100:.1f}%)")

    return by_task, total_success, total_count

def main():
    results_dir = Path(__file__).parent.parent / 'results'

    # 分离旧版和新版结果
    all_files = sorted(results_dir.glob('ipb_*_misleading_*.json'))

    old_files = [f for f in all_files if 'run17872' in f.name]
    new_files = [f for f in all_files if 'run17873' in f.name or 'run17874' in f.name]

    print(f"旧版 misleading 结果: {len(old_files)} 个文件")
    print(f"新版 misleading 结果: {len(new_files)} 个文件")

    # 分析旧版
    old_by_task, old_success, old_total = analyze_batch(old_files, "旧版 Misleading (直接给答案)")

    # 分析新版
    new_by_task, new_success, new_total = analyze_batch(new_files, "新版 Misleading (误导到错误方向)")

    # 对比分析
    print(f"\n{'='*80}")
    print("改进效果对比")
    print(f"{'='*80}")
    print(f"{'任务':<40} {'旧版成功率':<20} {'新版成功率':<20} {'变化':<15}")
    print('-'*80)

    for task in sorted(set(old_by_task.keys()) | set(new_by_task.keys())):
        old_success_count = sum(old_by_task[task]['luna']) + sum(old_by_task[task]['terra']) if task in old_by_task else 0
        old_count = len(old_by_task[task]['luna']) + len(old_by_task[task]['terra']) if task in old_by_task else 0

        new_success_count = sum(new_by_task[task]['luna']) + sum(new_by_task[task]['terra']) if task in new_by_task else 0
        new_count = len(new_by_task[task]['luna']) + len(new_by_task[task]['terra']) if task in new_by_task else 0

        old_rate = old_success_count / old_count * 100 if old_count > 0 else 0
        new_rate = new_success_count / new_count * 100 if new_count > 0 else 0
        delta = new_rate - old_rate

        delta_str = f"{delta:+.1f}%" if new_count > 0 else "N/A"

        print(f"{task:<40} {old_success_count}/{old_count} ({old_rate:.1f}%){'':<8} {new_success_count}/{new_count} ({new_rate:.1f}%){'':<8} {delta_str:<15}")

    print('-'*80)
    old_overall = old_success / old_total * 100 if old_total > 0 else 0
    new_overall = new_success / new_total * 100 if new_total > 0 else 0
    overall_delta = new_overall - old_overall

    print(f"{'总体':<40} {old_success}/{old_total} ({old_overall:.1f}%){'':<8} {new_success}/{new_total} ({new_overall:.1f}%){'':<8} {overall_delta:+.1f}%")

    print(f"\n{'='*80}")
    print("结论")
    print(f"{'='*80}")
    if overall_delta < -10:
        print(f"✅ 改进有效！misleading 成功率下降 {abs(overall_delta):.1f}%，区分度显著提升")
    elif overall_delta < -5:
        print(f"⚠️  改进有一定效果，misleading 成功率下降 {abs(overall_delta):.1f}%")
    else:
        print(f"❌ 改进效果不明显，成功率变化 {overall_delta:+.1f}%")

if __name__ == "__main__":
    main()
