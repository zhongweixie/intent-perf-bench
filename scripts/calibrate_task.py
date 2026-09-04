"""Measure a task's baseline (and reference fix, if it has one) and write
groundtruth/measurement.json.

    python scripts/calibrate_task.py --task-id ipb_cuda_001 [--n-runs 7]
    python scripts/calibrate_task.py --all

Measures isolated clones on the same partition and through the same launcher
the evaluator uses, so the pass bar tracks the machine instead of a number
typed in months ago on unknown hardware.

The pass threshold is derived, never stored independently:
  * task has an ipb-reference tag -> the agent must capture PASS_FRACTION of
    the gain the expert fix achieves (see PASS_FRACTION below);
  * otherwise -> threshold = baseline / threshold_speedup from ipb_exec.py;
  * neither -> the task is recorded but marked unscoreable.

Calibration refuses to write a threshold at or above the measured baseline,
which would pass an agent that changed nothing.
"""

import argparse
import json
import pathlib
import platform
import socket
import statistics
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ipb_measure as measure          # noqa: E402
import ipb_workspace as workspace      # noqa: E402
from ipb_exec import EXEC              # noqa: E402
from ipb_score import CALIBRATION_SCHEMA  # noqa: E402

# Fraction of the expert fix's gain an agent must capture to pass:
#   threshold = baseline - PASS_FRACTION * (baseline - reference)
# so passing is exactly equivalent to improvement >= PASS_FRACTION.
#
# The bar has to be a fraction of the *gain*, not a multiple of the reference
# runtime: a `reference * 1.5` bar silently exceeds the baseline whenever the
# expert fix is less than 1.5x faster. On ipb_cuda_007 (baseline 43.31 ms,
# reference 39.02 ms) it works out to 58.5 ms, which an untouched workspace
# clears outright.
PASS_FRACTION = 0.6

# Below this reference speedup a task cannot separate a real fix from run-to-run
# noise, so its verdict is not trustworthy however it is scored.
MIN_USEFUL_SPEEDUP = 1.5


def parse_args():
    p = argparse.ArgumentParser(description="Calibrate task baselines")
    p.add_argument("--task-id")
    p.add_argument("--all", action="store_true", help="calibrate every task in ipb_exec.EXEC")
    p.add_argument("--n-runs", type=int, default=7, help="timed runs after warmup")
    p.add_argument("--warmup", type=int, default=2, help="discarded warmup runs")
    p.add_argument("--max-cv", type=float, default=0.10,
                   help="warn above this coefficient of variation")
    p.add_argument("--skip-reference", action="store_true",
                   help="measure only the baseline")
    return p.parse_args()


def gpu_node() -> str:
    """Node actually executing the workload, for the provenance record."""
    try:
        out = subprocess.run(
            ["bash", "-c",
             f"source '{ROOT}/scripts/bench_common.sh' && ipb_gpu_run hostname"],
            capture_output=True, text=True, timeout=300,
        )
        lines = [l.strip() for l in out.stdout.strip().splitlines() if l.strip()]
        if lines:
            return lines[-1]
    except subprocess.SubprocessError:
        pass
    return socket.gethostname()


def measure_ref(task_dir: pathlib.Path, task_id: str, ref: str, spec: dict,
                args) -> dict:
    """Build, verify and time one git ref in its own isolated clone."""
    ws = workspace.clone_at_ref(task_dir, task_id, ref)
    try:
        head = subprocess.run(["git", "-C", str(ws), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        measure.build(ws)
        ok, vlog = measure.verify(ws, spec)
        if not ok:
            raise SystemExit(f"{task_id}: {ref} fails its own correctness check:\n{vlog}")

        _, samples, _ = measure.benchmark(ws, spec, n_runs=args.warmup + args.n_runs)
        timed = samples[args.warmup:]
        return {
            "commit": head,
            "median": statistics.median(timed),
            "samples": timed,
            "cv": measure.cv(timed),
        }
    finally:
        workspace.discard(ws)


def calibrate(task_id: str, args) -> dict:
    spec = EXEC.get(task_id)
    if spec is None:
        raise SystemExit(f"{task_id}: no entry in scripts/ipb_exec.py")

    task_dir = ROOT / "tasks" / task_id
    unit = spec.get("metric_unit", "ms")

    base_ref = workspace.baseline_ref(task_dir / "workspace", task_id)
    print(f"[{task_id}] baseline ref={base_ref}")
    base = measure_ref(task_dir, task_id, base_ref, spec, args)
    cv_txt = f"{base['cv']:.3f}" if base["cv"] is not None else "n/a"
    print(f"[{task_id}] baseline  median={base['median']:.4f}{unit} cv={cv_txt}")
    if base["cv"] is not None and base["cv"] > args.max_cv:
        print(f"[{task_id}] WARNING: baseline cv {base['cv']:.3f} > {args.max_cv}")

    ref_ref = None if args.skip_reference else spec.get("reference_ref")
    reference = None
    if ref_ref:
        print(f"[{task_id}] reference ref={ref_ref}")
        reference = measure_ref(task_dir, task_id, ref_ref, spec, args)
        cv_txt = f"{reference['cv']:.3f}" if reference["cv"] is not None else "n/a"
        print(f"[{task_id}] reference median={reference['median']:.4f}{unit} cv={cv_txt}")

    # Derive the pass bar. Prefer the measured reference over a declared target.
    ts = spec.get("threshold_speedup")
    if reference is not None:
        gain = base["median"] - reference["median"]
        threshold = base["median"] - PASS_FRACTION * gain
        basis = f"baseline - {PASS_FRACTION} * (baseline - reference)"
    elif ts:
        threshold = base["median"] / ts
        basis = f"baseline / {ts}"
    else:
        threshold, basis = None, None

    # A threshold at or above the baseline would pass an agent that changed
    # nothing, which is the single worst failure this rig can have.
    if threshold is not None and threshold >= base["median"]:
        raise SystemExit(
            f"{task_id}: computed threshold {threshold:.4f} >= baseline "
            f"{base['median']:.4f}; an untouched workspace would pass"
        )

    speedup = (base["median"] / reference["median"]
               if reference and reference["median"] > 0 else None)
    low_headroom = speedup is not None and speedup < MIN_USEFUL_SPEEDUP
    if speedup is not None:
        print(f"[{task_id}] reference speedup = {speedup:.1f}x  "
              f"threshold = {threshold:.4f}{unit}")
        if low_headroom:
            print(f"[{task_id}] WARNING: reference only {speedup:.2f}x faster than "
                  f"baseline (< {MIN_USEFUL_SPEEDUP}x); results on this task "
                  f"cannot be distinguished from measurement noise")

    record = {
        "schema": CALIBRATION_SCHEMA,
        "task_id": task_id,
        "metric_unit": unit,
        "baseline_median_ms": round(base["median"], 4),
        "baseline_samples_ms": [round(s, 4) for s in base["samples"]],
        "baseline_cv": round(base["cv"], 4) if base["cv"] is not None else None,
        "baseline_ref": base_ref,
        "baseline_commit": base["commit"],
        "reference_ref": ref_ref,
        "reference_commit": reference["commit"] if reference else None,
        "reference_median_ms": round(reference["median"], 4) if reference else None,
        "reference_samples_ms": [round(s, 4) for s in reference["samples"]] if reference else None,
        "reference_speedup": round(speedup, 3) if speedup else None,
        "threshold_ms": round(threshold, 4) if threshold else None,
        "threshold_basis": basis,
        "threshold_speedup": ts,
        "pass_fraction": PASS_FRACTION if reference is not None else None,
        # Set when the expert fix barely beats the baseline: the task is still
        # recorded, but its pass/fail verdict should not be reported alongside
        # tasks that have real headroom.
        "low_headroom": low_headroom,
        "n_runs": args.n_runs,
        "warmup": args.warmup,
        "measured_on": gpu_node() if spec.get("gpu") else platform.node(),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "host": platform.node(),
        "notes": "baseline = regressed state; measured via scripts/ipb_measure.py",
    }
    out = task_dir / "groundtruth" / "measurement.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"[{task_id}] wrote {out}")
    if threshold is None:
        print(f"[{task_id}] NOTE: no ipb-reference tag and no threshold_speedup "
              f"-> not scoreable until a design target is reviewed")
    return record


def main():
    args = parse_args()
    if args.all:
        targets = list(EXEC)
    elif args.task_id:
        targets = [args.task_id]
    else:
        raise SystemExit("need --task-id or --all")

    ok, failed = [], []
    for tid in targets:
        try:
            calibrate(tid, args)
            ok.append(tid)
        except (SystemExit, measure.MeasureError, subprocess.SubprocessError,
                RuntimeError) as exc:
            print(f"[{tid}] FAILED: {exc}")
            failed.append((tid, str(exc)[:300]))
    print(f"\ncalibrated {len(ok)}/{len(targets)}")
    for tid, why in failed:
        print(f"  FAILED {tid}: {why}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
