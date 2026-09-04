"""
Step 4: 测量 baseline 和 expert patch 的性能，填写 groundtruth/measurement.json

用法：
    python scripts/04_measure_baseline.py --task-id ipb_dev_001
"""

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

TASKS_DIR = pathlib.Path("tasks")


def parse_args():
    p = argparse.ArgumentParser(description="测量 baseline 和 expert patch 性能")
    p.add_argument("--task-id",   required=True)
    p.add_argument("--n-runs",    type=int, default=9,   help="正式测量轮数")
    p.add_argument("--warmup",    type=int, default=3,   help="warmup 轮数（不计入统计）")
    p.add_argument("--max-cv",    type=float, default=0.05, help="最大允许变异系数（5%）")
    return p.parse_args()


def main():
    args = parse_args()
    task_dir = TASKS_DIR / args.task_id
    assert task_dir.exists(), f"任务目录不存在: {task_dir}"

    # 将 evaluation/performance.py 的功能作为模块使用
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    from evaluation.performance import measure_script, compute_speedup

    workload = task_dir / "workspace" / "scripts" / "reproduce.py"
    assert workload.exists(), f"workload 脚本不存在: {workload}"

    patch_file = task_dir / "groundtruth" / "expert_patch.diff"
    repo_dir   = task_dir / "workspace" / "repo"

    # --- 测量 baseline ---
    print(f"测量 baseline（repo 无 patch）...")
    baseline = measure_script(
        script=str(workload),
        cwd=str(repo_dir),
        n_runs=args.n_runs,
        warmup=args.warmup,
        max_cv=args.max_cv,
    )
    print(f"  中位数: {baseline['median_s']:.4f}s  CV: {baseline['cv']:.3f}")

    # --- 应用 expert patch ---
    print("应用 expert patch...")
    subprocess.run(
        ["git", "apply", str(patch_file.resolve())],
        cwd=str(repo_dir), check=True
    )

    # --- 测量 patched ---
    print("测量 patched 性能...")
    patched = measure_script(
        script=str(workload),
        cwd=str(repo_dir),
        n_runs=args.n_runs,
        warmup=args.warmup,
        max_cv=args.max_cv,
    )
    speedup = compute_speedup(baseline["median_s"], patched["median_s"])
    print(f"  中位数: {patched['median_s']:.4f}s  CV: {patched['cv']:.3f}")
    print(f"  Speedup: {speedup:.3f}x")

    # --- 回滚 patch ---
    subprocess.run(
        ["git", "apply", "--reverse", str(patch_file.resolve())],
        cwd=str(repo_dir), check=True
    )
    print("patch 已回滚")

    # --- 写入 measurement.json ---
    import platform
    measurement = {
        "baseline_median_s": round(baseline["median_s"], 6),
        "patched_median_s":  round(patched["median_s"],  6),
        "expert_speedup":    round(speedup, 4),
        "baseline_cv":       round(baseline["cv"], 4),
        "patched_cv":        round(patched["cv"], 4),
        "baseline_samples":  baseline["samples"],
        "patched_samples":   patched["samples"],
        "n_runs":            args.n_runs,
        "warmup_runs":       args.warmup,
        "measured_on":       platform.node(),
        "notes":             "",
    }
    out = task_dir / "groundtruth" / "measurement.json"
    out.write_text(json.dumps(measurement, indent=2) + "\n")
    print(f"\n已写入 {out}")

    if speedup < 1.20:
        print(f"警告: speedup={speedup:.3f}x < 1.20x，此任务可能信号过弱，建议替换")


if __name__ == "__main__":
    main()
