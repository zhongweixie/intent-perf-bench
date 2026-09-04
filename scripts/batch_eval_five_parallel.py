#!/usr/bin/env python3
import argparse
import concurrent.futures
import subprocess
from pathlib import Path

DEFAULT_TASKS = [
    "ipb_cpu_001_gaussian_blur",
    "ipb_cpu_002_sha256_throughput",
    "ipb_cpu_003_vliw_scheduler",
    "ipb_cpu_004_aes128_ctr",
    "ipb_cuda_005_icp_correspondence",
]
PYTHON_EXE = "/aifs4su/hansirui_3rd/gaoyisen/miniconda3/bin/python3"

def run_single_eval(task, variant, model, root, max_turns, run_id=None):
    cmd = [PYTHON_EXE, str(root / "scripts/run_agent.py"), "--task-id", task,
           "--variant", variant, "--provider", "openai", "--model", model,
           "--max-turns", str(max_turns)]
    if run_id:
        # Keep one result file per (task, variant, model) within a batch.
        cmd += ["--run-id", f"{run_id}_{model}"]
    try:
        subprocess.run(cmd, check=True, cwd=str(root), capture_output=True)
        return task, variant, model, True, None
    except subprocess.CalledProcessError as exc:
        return task, variant, model, False, str(exc)

def run_task_group(task, variants, models, root, max_turns, run_id=None):
    # A workspace is reset by each run; serialize runs within one task.
    return [run_single_eval(task, variant, model, root, max_turns, run_id)
            for variant in variants for model in models]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", default=DEFAULT_TASKS)
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--variants", nargs="+", default=["exact", "fuzzy", "misleading"])
    parser.add_argument("--max-turns", type=int, default=15)
    parser.add_argument("--parallel", type=int, default=5)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).parent.parent
    groups = [(task, args.variants, args.models) for task in args.tasks]
    total = len(args.tasks) * len(args.variants) * len(args.models)
    print(f"将执行 {total} 次评测（任务并行度：{args.parallel}）：")
    print(f"  任务：{args.tasks}")
    print(f"  变体：{args.variants}")
    print(f"  模型：{args.models}")
    if args.dry_run:
        return
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = [pool.submit(run_task_group, task, variants, models, root, args.max_turns, args.run_id)
                   for task, variants, models in groups]
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())
            completed = len(results)
            for task, variant, model, success, error in results[-len(args.variants) * len(args.models):]:
                mark = "✓" if success else "✗"
                print(f"[{completed}/{total}] {mark} {task} / {variant} / {model}")
    failed = [r for r in results if not r[3]]
    print("=" * 60)
    print(f"完成 {len(results) - len(failed)}/{total} 次评测")
    if failed:
        print("失败：")
        for task, variant, model, _, error in failed:
            print(f"  - {task} / {variant} / {model}: {error}")

if __name__ == "__main__":
    main()
