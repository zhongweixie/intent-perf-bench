#!/usr/bin/env python3
"""提取19个任务的最新测试结果并生成汇总"""

import json
import glob
import shutil
from pathlib import Path
from collections import defaultdict

# 19个负区分度任务
TASKS_19 = [
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

def find_latest_result(task, variant):
    """查找任务的最新结果文件"""
    pattern = f"results/{task}_{variant}_*.json"
    files = glob.glob(pattern)

    if not files:
        return None

    # 按修改时间排序，取最新的
    latest = max(files, key=lambda x: Path(x).stat().st_mtime)
    return latest

def extract_best_time_from_benchmark(benchmark_output):
    """从benchmark_output中提取best time"""
    if not benchmark_output:
        return None

    import re
    # 匹配 "Best: 0.0092s" 或 "Best time: 28.7925s"
    match = re.search(r'Best(?:\s+time)?:\s+(\d+\.?\d*)s', benchmark_output)
    if match:
        return float(match.group(1))

    return None

def extract_key_metrics(result_file):
    """从结果文件提取关键指标"""
    with open(result_file) as f:
        data = json.load(f)

    # 优先使用elapsed_time，如果没有则从benchmark_output提取
    elapsed_time = data.get("elapsed_time")
    if elapsed_time is None:
        elapsed_time = extract_best_time_from_benchmark(data.get("benchmark_output", ""))

    return {
        "turns": data.get("turns", 0),
        "elapsed_time": elapsed_time,
        "passed": data.get("passed", False),
        "turns_to_real_target": data.get("turns_to_real_target"),
    }

def calculate_discrimination(fuzzy_time, misleading_time):
    """计算区分度：基于优化后代码的运行时间

    区分度 = (Fuzzy时间 - Misleading时间) / Misleading时间 × 100%

    - 正区分度：Fuzzy更慢，Misleading帮助了优化
    - 负区分度：Misleading更慢，误导了优化方向
    """
    if misleading_time == 0 or fuzzy_time == 0:
        return None

    return (fuzzy_time - misleading_time) / misleading_time * 100

def main():
    print("=" * 80)
    print("提取19个任务的最新测试结果")
    print("=" * 80)
    print()

    # 创建输出目录
    Path("results/key_experiments").mkdir(parents=True, exist_ok=True)

    summary_data = []
    copied_files = []

    for task in TASKS_19:
        print(f"处理 {task}...")

        # 查找最新的fuzzy和misleading结果
        fuzzy_file = find_latest_result(task, "fuzzy")
        misleading_file = find_latest_result(task, "misleading")

        if not fuzzy_file or not misleading_file:
            print(f"  ⚠️  缺少结果文件")
            print(f"     Fuzzy: {'✓' if fuzzy_file else '✗'}")
            print(f"     Misleading: {'✓' if misleading_file else '✗'}")
            continue

        # 提取指标
        fuzzy_metrics = extract_key_metrics(fuzzy_file)
        misleading_metrics = extract_key_metrics(misleading_file)

        # 如果任一时间为None，跳过
        if fuzzy_metrics["elapsed_time"] is None or misleading_metrics["elapsed_time"] is None:
            print(f"  ⚠️  缺少时间数据")
            print(f"     Fuzzy time: {fuzzy_metrics['elapsed_time']}")
            print(f"     Misleading time: {misleading_metrics['elapsed_time']}")
            continue

        # 计算区分度
        disc = calculate_discrimination(
            fuzzy_metrics["elapsed_time"],
            misleading_metrics["elapsed_time"]
        )

        # 汇总数据
        summary_data.append({
            "task": task,
            "fuzzy": fuzzy_metrics,
            "misleading": misleading_metrics,
            "discrimination": disc,
        })

        # 复制文件到key_experiments
        fuzzy_dest = f"results/key_experiments/{Path(fuzzy_file).name}"
        misleading_dest = f"results/key_experiments/{Path(misleading_file).name}"

        shutil.copy2(fuzzy_file, fuzzy_dest)
        shutil.copy2(misleading_file, misleading_dest)

        copied_files.append(fuzzy_dest)
        copied_files.append(misleading_dest)

        print(f"  ✓ 区分度: {disc:+.1f}%" if disc is not None else "  ✓ 无区分度数据")

    # 保存汇总JSON
    summary_json_path = "results/summary/misleading_rewrite_test_summary.json"
    with open(summary_json_path, 'w') as f:
        json.dump({
            "experiment": "misleading_prompt_rewrite",
            "tasks_tested": len(summary_data),
            "results": summary_data
        }, f, indent=2)

    print()
    print("=" * 80)
    print(f"✅ 完成！")
    print(f"   - 汇总数据: {summary_json_path}")
    print(f"   - 复制文件: {len(copied_files)} 个 → results/key_experiments/")
    print("=" * 80)

if __name__ == "__main__":
    main()
