#!/usr/bin/env python3
"""Re-time the workspaces kept by scripts/run_batch.py, one at a time.

The number an agent run reports is measured while its siblings are still
running: up to `--parallel` other agents are compiling, and every CUDA task
shares one GPU. That is fine for collecting edits and useless for timing.

This script re-times each kept workspace serially, through the same
ipb_measure/ipb_score calls run_agent.py and calibrate_task.py use, so the
result is comparable to the calibrated baseline by construction.

It also gives a second independent measurement of the *same* code, so the two
numbers together show which tasks are too noisy to rank agents on: a task whose
median moves more than its baseline-to-reference span cannot support a score.
"""

import argparse
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import ipb_measure
import ipb_score
from ipb_exec import EXEC

ROOT = pathlib.Path(__file__).parent.parent


def find_workspaces(scratch_root: pathlib.Path) -> list[tuple[str, str, str, pathlib.Path]]:
    """Recover (task, variant, model, workspace) from run_batch's scratch layout."""
    out = []
    for slug_dir in sorted(scratch_root.iterdir()):
        if not slug_dir.is_dir():
            continue
        parts = slug_dir.name.split("__")
        if len(parts) != 3:
            continue
        task, variant, model = parts
        # run_batch gives each combo its own IPB_SCRATCH; clone_at_ref then
        # makes one mkdtemp holder inside it containing `workspace`.
        holders = [p for p in slug_dir.glob("*/workspace") if p.is_dir()]
        if not holders:
            continue
        out.append((task, variant, model, sorted(holders)[-1]))
    return out


def remeasure_one(task: str, workspace: pathlib.Path, bench_runs: int) -> dict:
    spec = EXEC.get(task)
    if spec is None:
        return {"error": f"{task}: not in ipb_exec.EXEC"}

    rec: dict = {"workspace": str(workspace)}
    try:
        ipb_measure.build(workspace)
    except ipb_measure.MeasureError as exc:
        rec["error"] = f"build failed: {str(exc)[:400]}"
        return rec

    try:
        correct, vlog = ipb_measure.verify(workspace, spec)
        rec["correctness_ok"] = correct
        rec["verify_tail"] = vlog[-300:]

        median, samples, _ = ipb_measure.benchmark(workspace, spec, n_runs=bench_runs)
        rec["median"] = median
        rec["samples"] = samples
        rec["cv"] = ipb_measure.cv(samples)
    except ipb_measure.InfraError as exc:
        rec["error"] = f"infra: {str(exc)[:400]}"
        return rec
    except ipb_measure.MeasureError as exc:
        rec["error"] = f"measure failed: {str(exc)[:400]}"
        return rec

    try:
        rec["score"] = ipb_score.score(
            task, median, correct,
            correctness_checked=ipb_measure.has_correctness_check(spec))
    except ipb_score.NotCalibrated as exc:
        rec["error"] = f"not calibrated: {exc}"
    return rec


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--bench-runs", type=int, default=5)
    p.add_argument("--only", nargs="*", default=None,
                   help="restrict to these task ids")
    args = p.parse_args()

    scratch_root = ROOT / ".scratch" / f"batch_{args.run_id}"
    if not scratch_root.exists():
        sys.exit(f"no such batch scratch: {scratch_root}")

    combos = find_workspaces(scratch_root)
    if args.only:
        combos = [c for c in combos if c[0] in args.only]
    print(f"re-measuring {len(combos)} workspaces serially "
          f"(bench_runs={args.bench_runs})\n")

    out = []
    for i, (task, variant, model, ws) in enumerate(combos, 1):
        print(f"[{i}/{len(combos)}] {task} / {variant} / {model}")
        sys.stdout.flush()
        rec = remeasure_one(task, ws, args.bench_runs)
        rec.update({"task": task, "variant": variant, "model": model})

        # The figure the agent run reported, measured under load. run_batch
        # suffixes the run id with the model, since run_agent's result filename
        # has no model field and two models would otherwise overwrite each other.
        orig_path = (ROOT / "results" /
                     f"{task}_{variant}_{args.run_id}_{model}.json")
        if not orig_path.exists():
            orig_path = ROOT / "results" / f"{task}_{variant}_{args.run_id}.json"
        if orig_path.exists():
            orig = json.loads(orig_path.read_text())
            rec["orig_elapsed"] = orig.get("elapsed_time")
            rec["orig_passed"] = orig.get("passed")
            rec["orig_improvement"] = orig.get("improvement_score")

        if "error" in rec:
            print(f"    ERROR {rec['error'][:160]}")
        else:
            s = rec.get("score") or {}
            cvs = f"{rec['cv']:.3f}" if rec.get("cv") is not None else "n/a"
            imp = s.get("improvement")
            print(f"    median={rec['median']:.4f} cv={cvs} "
                  f"correct={rec.get('correctness_ok')} "
                  f"passed={s.get('passed')} "
                  f"improvement={imp if imp is None else round(imp, 3)}"
                  + (f"  (agent-run reported {rec['orig_elapsed']:.4f})"
                     if isinstance(rec.get("orig_elapsed"), (int, float)) else ""))
        sys.stdout.flush()
        out.append(rec)

    dest = ROOT / "results" / f"remeasure_{args.run_id}.json"
    dest.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(f"\nwrote {dest}")

    ok = [r for r in out if "error" not in r]
    print(f"{len(ok)}/{len(out)} re-measured cleanly")
    drift = [r for r in ok
             if isinstance(r.get("orig_elapsed"), (int, float)) and r.get("median")
             and r["orig_elapsed"] > 0
             and abs(r["median"] - r["orig_elapsed"]) / r["orig_elapsed"] > 0.25]
    if drift:
        print(f"\n{len(drift)} run(s) moved >25% between the loaded and serial "
              f"measurement -- the loaded numbers were not usable:")
        for r in drift:
            print(f"  {r['task']}/{r['variant']}/{r['model']}: "
                  f"{r['orig_elapsed']:.4f} -> {r['median']:.4f}")


if __name__ == "__main__":
    main()
