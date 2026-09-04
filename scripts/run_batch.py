#!/usr/bin/env python3
"""Run many agent evaluations, keeping each workspace for a clean re-measure.

Agent runs are API-bound and can be run concurrently, but the timing they
produce cannot be trusted when they are: several agents compile and run
benchmarks on one login node and perturb each other, and the CUDA tasks all
funnel into a single GPU. So this driver only collects the agents' *edits*;
scripts/remeasure.py then times the kept workspaces one at a time and produces
the authoritative score.

Each run gets its own IPB_SCRATCH so the kept workspace can be mapped back to
the (task, variant, model) it came from -- run_agent.py does not record where
its workspace was.
"""

import argparse
import concurrent.futures
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent


def combo_slug(task: str, variant: str, model: str) -> str:
    return f"{task}__{variant}__{model}"


def run_one(task: str, variant: str, model: str, args, scratch_root: pathlib.Path,
            log_dir: pathlib.Path) -> dict:
    slug = combo_slug(task, variant, model)
    scratch = scratch_root / slug
    scratch.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["IPB_SCRATCH"] = str(scratch)

    cmd = [
        sys.executable, str(ROOT / "scripts" / "run_agent.py"),
        "--task-id", task,
        "--variant", variant,
        "--model", model,
        "--provider", args.provider,
        "--max-turns", str(args.max_turns),
        "--bench-runs", str(args.bench_runs),
        # run_agent writes results/<task>_<variant>_<run_id>.json, with no model
        # in the name: without this suffix two models in one batch overwrite
        # each other's result and only the one finishing last survives.
        "--run-id", f"{args.run_id}_{model}",
        "--keep-workspace",
    ]

    log_path = log_dir / f"{slug}.log"
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True,
                              text=True, timeout=args.timeout)
        log_path.write_text(proc.stdout + "\n[stderr]\n" + proc.stderr)
        ok, err = proc.returncode == 0, (None if proc.returncode == 0
                                         else f"exit {proc.returncode}")
    except subprocess.TimeoutExpired as exc:
        log_path.write_text((exc.stdout or "") + "\n[stderr]\n" + (exc.stderr or ""))
        ok, err = False, f"timeout after {args.timeout}s"

    return {"task": task, "variant": variant, "model": model, "ok": ok,
            "error": err, "seconds": round(time.time() - started, 1),
            "scratch": str(scratch)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tasks", nargs="+", required=True)
    p.add_argument("--variants", nargs="+", default=["exact", "fuzzy", "misleading"])
    p.add_argument("--models", nargs="+", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--parallel", type=int, default=6)
    p.add_argument("--max-turns", type=int, default=30)
    p.add_argument("--bench-runs", type=int, default=3)
    p.add_argument("--provider", default="anthropic")
    p.add_argument("--timeout", type=int, default=3600)
    p.add_argument("--skip-missing-variant", action="store_true",
                   help="skip combos whose variants/<variant>.md does not exist, "
                        "instead of letting run_agent.py fall back to a generic "
                        "prompt that would silently break the variant contrast")
    args = p.parse_args()

    scratch_root = ROOT / ".scratch" / f"batch_{args.run_id}"
    log_dir = ROOT / "results" / "batch_logs" / args.run_id
    log_dir.mkdir(parents=True, exist_ok=True)

    combos = []
    skipped = []
    for task in args.tasks:
        for variant in args.variants:
            for model in args.models:
                vf = ROOT / "tasks" / task / "variants" / f"{variant}.md"
                if args.skip_missing_variant and not vf.exists():
                    skipped.append((task, variant))
                    continue
                combos.append((task, variant, model))

    for task, variant in sorted(set(skipped)):
        print(f"[skip] {task}: no variants/{variant}.md")

    print(f"batch {args.run_id}: {len(combos)} runs, parallel={args.parallel}")
    print(f"  scratch: {scratch_root}")
    print(f"  logs:    {log_dir}")
    sys.stdout.flush()

    done = 0
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = {pool.submit(run_one, t, v, m, args, scratch_root, log_dir): (t, v, m)
                   for t, v, m in combos}
        for fut in concurrent.futures.as_completed(futures):
            r = fut.result()
            results.append(r)
            done += 1
            mark = "ok " if r["ok"] else "ERR"
            print(f"[{done}/{len(combos)}] {mark} {r['task']} / {r['variant']} / "
                  f"{r['model']}  ({r['seconds']}s)"
                  + (f"  {r['error']}" if r["error"] else ""))
            sys.stdout.flush()

    failed = [r for r in results if not r["ok"]]
    print("=" * 70)
    print(f"batch {args.run_id}: {len(results) - len(failed)}/{len(results)} ok")
    for r in failed:
        print(f"  FAILED {r['task']} / {r['variant']} / {r['model']}: {r['error']}")


if __name__ == "__main__":
    main()
