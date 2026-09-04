"""Score an agent's attempt against a task's calibrated measurements.

The single source of truth is tasks/<id>/groundtruth/measurement.json, written
by scripts/calibrate_task.py. Nothing here hard-codes per-task timings: three
mutually inconsistent copies of those numbers (evaluator constants, bench.sh,
groundtruth) is what let an untouched workspace score 0.48 on ipb_cuda_001 --
a hard-coded baseline of 124.3 ms against a real 66.7 ms meant merely
compiling the regressed code looked like half a fix.

Two figures are reported:

  speedup           baseline / agent, always available.
  improvement       (baseline - agent) / (baseline - reference), clamped to
                    [0,1], and only when the task ships a measured reference
                    fix. 0 means no better than the regressed baseline, 1 means
                    it matched the expert implementation. Tasks without an
                    ipb-reference tag report None rather than a number derived
                    from a guessed optimum.
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent

# Bumped to 3 when calibration began recording the measured reference fix.
# Older files lack reference_median_ms and were written before per-run
# workspace isolation, so their baselines are not trustworthy.
CALIBRATION_SCHEMA = 3


class NotCalibrated(RuntimeError):
    """No usable calibration, so the run must not be assigned a score."""


def load_calibration(task_id: str) -> dict:
    path = ROOT / "tasks" / task_id / "groundtruth" / "measurement.json"
    if not path.exists():
        raise NotCalibrated(f"{task_id}: {path} missing; run scripts/calibrate_task.py")
    data = json.loads(path.read_text())
    if data.get("schema") != CALIBRATION_SCHEMA:
        raise NotCalibrated(
            f"{task_id}: calibration schema {data.get('schema')!r} "
            f"!= {CALIBRATION_SCHEMA}; re-run scripts/calibrate_task.py"
        )
    if not isinstance(data.get("baseline_median_ms"), (int, float)):
        raise NotCalibrated(f"{task_id}: calibration has no baseline_median_ms")
    return data


def score(task_id: str, agent_ms: float, correctness_ok: bool,
          correctness_checked: bool = True) -> dict:
    """Speedup, improvement and pass/fail for one attempt.

    An incorrect result earns nothing, however fast it is. The gate has to
    apply to `improvement` and not only to `passed`: `improvement` is the
    continuous figure that gets averaged across runs, so gating only the
    boolean let a wrong-but-fast submission still contribute 0.99 to the
    reported mean.

    correctness_checked=False means the task ships no correctness check at all,
    so nothing can be concluded from the run and it is recorded with
    passed=None rather than credited for the time it printed -- a deleted
    kernel body is infinitely fast.
    """
    cal = load_calibration(task_id)
    baseline = float(cal["baseline_median_ms"])
    reference = cal.get("reference_median_ms")
    threshold = cal.get("threshold_ms")

    speedup = baseline / agent_ms if agent_ms > 0 else None

    # Raw ratio, kept for diagnostics only; `improvement` below is the figure
    # that may be aggregated.
    raw_improvement = None
    if isinstance(reference, (int, float)):
        span = baseline - float(reference)
        if span > 0:
            raw_improvement = max(0.0, min(1.0, (baseline - agent_ms) / span))

    if not correctness_checked:
        improvement = None
    elif not correctness_ok:
        improvement = 0.0
    else:
        improvement = raw_improvement

    meets_threshold = None if threshold is None else agent_ms <= float(threshold)

    return {
        "speedup": speedup,
        "improvement": improvement,
        "raw_improvement": raw_improvement,
        "correctness_checked": correctness_checked,
        "baseline_median_ms": baseline,
        "reference_median_ms": reference,
        "agent_ms": agent_ms,
        "metric_unit": cal.get("metric_unit", "ms"),
        "threshold_ms": threshold,
        "threshold_basis": cal.get("threshold_basis"),
        "meets_threshold": meets_threshold,
        "correctness_ok": correctness_ok,
        # None when the task has no reviewed performance target, or no
        # correctness check at all: the run is recorded but deliberately not
        # counted as pass or fail.
        "passed": (None if meets_threshold is None or not correctness_checked
                   else bool(meets_threshold and correctness_ok)),
        "calibrated_on": cal.get("measured_on"),
        "baseline_commit": cal.get("baseline_commit"),
    }
