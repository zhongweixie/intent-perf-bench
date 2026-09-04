"""
主评测入口：给定任务 ID、变体名称和 agent 提交的 patch，返回结构化评测结果。

用法：
    python evaluation/evaluate.py \
        --task-id ipb_dev_001 \
        --variant fuzzy \
        --patch /path/to/agent.diff \
        --output results/ipb_dev_001_fuzzy.json
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from evaluation.correctness import run_correctness_tests
from evaluation.performance  import compute_speedup, measure_script, meets_threshold
from evaluation.anti_hack    import check_integrity, check_git_modified_files

TASKS_DIR = ROOT / "tasks"


def parse_args():
    p = argparse.ArgumentParser(description="IPB 任务评测")
    p.add_argument("--task-id",  required=True)
    p.add_argument("--variant",  required=True,
                   choices=["exact", "target_known", "fuzzy", "misleading"])
    p.add_argument("--patch",    required=True, help="agent 提交的 unified diff 路径")
    p.add_argument("--output",   default=None,  help="结果 JSON 输出路径")
    p.add_argument("--n-runs",   type=int, default=9)
    p.add_argument("--warmup",   type=int, default=3)
    p.add_argument("--max-cv",   type=float, default=0.05)
    return p.parse_args()


def load_task(task_id: str) -> tuple[dict, dict]:
    task_dir = TASKS_DIR / task_id
    intent      = json.loads((task_dir / "groundtruth" / "intent.json").read_text())
    measurement = json.loads((task_dir / "groundtruth" / "measurement.json").read_text())
    return intent, measurement, task_dir


def apply_patch(repo_dir: Path, patch_path: str) -> bool:
    r = subprocess.run(
        ["git", "apply", "--check", patch_path],
        cwd=str(repo_dir), capture_output=True
    )
    if r.returncode != 0:
        return False
    subprocess.run(["git", "apply", patch_path], cwd=str(repo_dir), check=True)
    return True


def reverse_patch(repo_dir: Path, patch_path: str):
    subprocess.run(
        ["git", "apply", "--reverse", patch_path],
        cwd=str(repo_dir), check=True
    )


def evaluate(args) -> dict:
    intent, measurement, task_dir = load_task(args.task_id)
    repo_dir  = task_dir / "workspace" / "repo"
    workload  = task_dir / "workspace" / "scripts" / "reproduce.py"
    test_files = [t["file"] for t in intent.get("visible_evidence", [])
                  if t["role"] == "correctness-contract"]

    result = {
        "task_id":         args.task_id,
        "variant":         args.variant,
        "patch":           args.patch,
        "timestamp":       time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "anti_hack":       None,
        "correctness":     None,
        "performance":     None,
        "success":         False,
        "speedup":         None,
        "threshold":       intent["threshold"],
        "errors":          [],
    }

    # 1. Anti-hack 检查（先于 patch 应用）
    integrity = check_integrity(task_dir)
    result["anti_hack"] = integrity
    if not integrity["clean"]:
        result["errors"].append("anti_hack_violation")
        return result

    # 2. 应用 patch
    if not apply_patch(repo_dir, args.patch):
        result["errors"].append("patch_apply_failed")
        return result

    try:
        # 3. 正确性测试
        correctness = run_correctness_tests(repo_dir, test_files)
        result["correctness"] = correctness
        if not correctness["passed"]:
            result["errors"].append("correctness_failed")
            return result

        # 4. 性能测量
        patched_meas = measure_script(
            script=str(workload),
            cwd=str(repo_dir),
            n_runs=args.n_runs,
            warmup=args.warmup,
            max_cv=args.max_cv,
        )
        baseline_s = measurement["baseline_median_s"]
        patched_s  = patched_meas["median_s"]
        speedup    = compute_speedup(baseline_s, patched_s)
        passed_perf = meets_threshold(baseline_s, patched_s, intent["threshold"])

        result["performance"] = {
            "baseline_median_s": baseline_s,
            "patched_median_s":  patched_s,
            "speedup":           round(speedup, 4),
            "threshold":         intent["threshold"],
            "passed":            passed_perf,
            "cv":                round(patched_meas["cv"], 4),
        }
        result["speedup"] = round(speedup, 4)
        result["success"] = passed_perf

    finally:
        reverse_patch(repo_dir, args.patch)

    return result


def main():
    args = parse_args()
    result = evaluate(args)

    status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
    print(f"\n{status}  task={args.task_id}  variant={args.variant}  "
          f"speedup={result['speedup']}x  threshold={result['threshold']}x")

    if result["errors"]:
        print(f"  错误: {result['errors']}")

    out_path = args.output or f"results/{args.task_id}_{args.variant}.json"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(result, indent=2) + "\n")
    print(f"  结果已写入 {out_path}")


if __name__ == "__main__":
    main()
