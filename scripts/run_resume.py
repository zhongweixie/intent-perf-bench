#!/usr/bin/env python3
"""Resume a batch, skipping combos that cannot or need not be run.

Three guards, each earned from a wasted batch:
  * skip is scoped to the batch's own run-id, so a resume does not treat an
    older batch's result (different harness, different variant text) as if the
    rerun had already happened;
  * tasks whose task.toml marks them unscorable (regression inside measurement
    noise) or deprecated are refused up front -- running them burns GPU on
    numbers that cannot separate models;
  * a short streak of quota/auth failures aborts the batch instead of marching
    through dozens of runs that cannot succeed.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent.parent
PYTHON = "/aifs4su/hansirui_3rd/gaoyisen/miniconda3/bin/python3"
RUN_AGENT = ROOT / "scripts/run_agent.py"
RESULTS = ROOT / "results"
TASKS = ROOT / "tasks"

QUOTA_MARKERS = (
    "token quota is not enough",
    "PermissionDeniedError",
    "AuthenticationError",
    "RateLimitError",
    "insufficient_quota",
)
ABORT_AFTER_CONSECUTIVE_QUOTA = 3

UNSCORABLE_CLASSES = ("trivial_control", "blocked")


def refuse_reason(task):
    """Why this task must not be run, or None if it is fair game."""
    tdir = TASKS / task
    if not tdir.is_dir():
        return "no such task directory"
    if (tdir / "DEPRECATED.md").exists():
        return "deprecated (see DEPRECATED.md)"

    tpath = tdir / "task.toml"
    if not tpath.exists():
        return "no task.toml"
    try:
        doc = tomllib.load(open(tpath, "rb"))
    except Exception as exc:
        return f"unreadable task.toml: {exc}"

    flat = {}
    for section in doc.values():
        if isinstance(section, dict):
            flat.update(section)

    if flat.get("scorable") is False:
        speed = flat.get("measured_speedup", "?")
        return f"scorable=false (measured {speed})"
    cls = str(flat.get("classification", "") or "")
    if cls in UNSCORABLE_CLASSES:
        return f"classification={cls}"
    return None


def already_done(batch_name, task, variant, model):
    tag = model.replace("claude-", "")
    hits = sorted(RESULTS.glob(f"{task}_{variant}_{batch_name}_*{tag}*.json"))
    return hits[0].name if hits else None


def log_has_quota_error(path):
    try:
        tail = path.read_text(errors="replace")[-4000:]
    except OSError:
        return False
    return any(m in tail for m in QUOTA_MARKERS)


def run_batch(batch_name, batch_file, max_turns, timeout):
    lines = [ln.strip() for ln in open(batch_file) if ln.strip()]
    logdir = ROOT / "results/batch_logs" / batch_name
    logdir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== batch {batch_name}: {len(lines)} combos ===", flush=True)
    ok = skipped = refused = failed = 0
    consecutive_quota = 0
    refused_tasks = {}

    for i, ln in enumerate(lines, 1):
        task, variant, model = [x.strip() for x in ln.split("/")]
        prefix = f"[{i}/{len(lines)}] {task} / {variant} / {model}"

        reason = refuse_reason(task)
        if reason:
            refused += 1
            refused_tasks[task] = reason
            print(f"{prefix} ... REFUSE ({reason})", flush=True)
            continue

        existing = already_done(batch_name, task, variant, model)
        if existing:
            skipped += 1
            print(f"{prefix} ... SKIP (have {existing})", flush=True)
            continue

        run_id = f"{batch_name}_{model.replace('claude-', '')}"
        log = logdir / f"{task}__{variant}__{model.replace('claude-', '')}.log"
        cmd = [PYTHON, str(RUN_AGENT), "--task-id", task, "--variant", variant,
               "--model", model, "--max-turns", str(max_turns),
               "--budget-warning-turns", "5", "--run-id", run_id]

        print(f"{prefix} ... ", end="", flush=True)
        t0 = time.time()
        try:
            with open(log, "w") as fh:
                subprocess.run(cmd, cwd=str(ROOT), stdout=fh,
                               stderr=subprocess.STDOUT, check=True,
                               timeout=timeout)
            ok += 1
            consecutive_quota = 0
            print(f"ok ({time.time() - t0:.0f}s)", flush=True)
        except subprocess.TimeoutExpired:
            failed += 1
            consecutive_quota = 0
            print("TIMEOUT", flush=True)
        except subprocess.CalledProcessError as exc:
            failed += 1
            if log_has_quota_error(log):
                consecutive_quota += 1
                print(f"QUOTA-FAIL (streak {consecutive_quota})", flush=True)
                if consecutive_quota >= ABORT_AFTER_CONSECUTIVE_QUOTA:
                    print(f"\nABORT: {consecutive_quota} consecutive quota "
                          f"failures; not burning the rest of the batch.",
                          flush=True)
                    break
            else:
                consecutive_quota = 0
                print(f"FAILED exit {exc.returncode} -> {log}", flush=True)

    print("-" * 70, flush=True)
    print(f"batch {batch_name}: ok={ok} skipped={skipped} refused={refused} "
          f"failed={failed} of {len(lines)}", flush=True)
    for task, reason in sorted(refused_tasks.items()):
        print(f"  refused {task}: {reason}", flush=True)
    print(f"{batch_name} ended at {time.strftime('%c')}", flush=True)
    return failed == 0, consecutive_quota >= ABORT_AFTER_CONSECUTIVE_QUOTA


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", nargs="+", default=["g5", "g6"])
    ap.add_argument("--max-turns", type=int, default=30)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--gpu-jobid", default=os.environ.get("IPB_GPU_JOBID", ""))
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would run, without spending anything")
    args = ap.parse_args()

    if args.gpu_jobid:
        os.environ["IPB_GPU_JOBID"] = args.gpu_jobid

    if args.dry_run:
        for name in args.batches:
            bf = ROOT / f".scratch/batch_{name}.txt"
            if not bf.exists():
                print(f"missing batch file {bf}")
                continue
            print(f"\n=== dry run {name} ===")
            for ln in [x.strip() for x in open(bf) if x.strip()]:
                task, variant, model = [x.strip() for x in ln.split("/")]
                reason = refuse_reason(task)
                have = already_done(name, task, variant, model)
                verdict = (f"REFUSE ({reason})" if reason
                           else f"SKIP (have {have})" if have else "WOULD RUN")
                print(f"  {task} / {variant} / {model}: {verdict}")
        return 0

    all_clean = True
    for name in args.batches:
        bf = ROOT / f".scratch/batch_{name}.txt"
        if not bf.exists():
            print(f"missing batch file {bf}", flush=True)
            all_clean = False
            continue
        clean, aborted = run_batch(name, bf, args.max_turns, args.timeout)
        all_clean = all_clean and clean
        if aborted:
            print("stopping remaining batches due to quota abort", flush=True)
            break
    return 0 if all_clean else 1


if __name__ == "__main__":
    sys.exit(main())
