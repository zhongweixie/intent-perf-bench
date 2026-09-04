"""Verify that the scoring pipeline reports what it should at every endpoint.

    python scripts/sanity_check.py --task-id ipb_cuda_001
    python scripts/sanity_check.py --all
    python scripts/sanity_check.py --all --static-only   # no builds, no GPU

For each task this re-measures known states through the *scoring* path and
asserts the result:

    baseline  (the regressed code the agent starts from)  -> improvement ~= 0
    reference (the expert fix, when the task ships one)   -> improvement ~= 1
    cheats    (deliberately wrong but fast submissions)   -> improvement == 0

Both honest endpoints matter. A rig that scores an untouched workspace above
zero is silently crediting agents for doing nothing -- ipb_cuda_001 gave 0.48 to
a workspace with no edits because the evaluator compared a real 66.7 ms run
against a hard-coded 124.3 ms baseline. A rig that cannot score the expert fix
near 1.0 has a threshold no agent can reach.

The cheat endpoint matters for a different reason. Baseline and reference are
both *correct* implementations, so no arrangement of them can reveal a missing
correctness gate. That blind spot is why five tasks shipped with no correctness
check at all, and why replacing blur_image's body with `return;` measured
0.000000 s and scored improvement=1.0. Scoring on time alone makes deleting the
work the optimal strategy, so the rig has to be shown rejecting it.

This is deliberately independent of calibrate_task.py's own bookkeeping: it goes
through ipb_score.score(), the same function run_agent.py calls, so a bug in the
scoring path cannot hide behind correct calibration numbers.
"""

import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ipb_measure as measure          # noqa: E402
import ipb_workspace as workspace      # noqa: E402
from ipb_exec import EXEC              # noqa: E402
from ipb_score import NotCalibrated, load_calibration, score  # noqa: E402

# Tolerances. The baseline bound is tight because re-measuring the same commit
# should land on the calibrated median; the reference bound is looser because
# an expert fix is often fast enough that timer granularity dominates.
BASELINE_MAX_IMPROVEMENT = 0.15
REFERENCE_MIN_IMPROVEMENT = 0.80

# Source mutations that produce a fast but wrong submission: a `return` is
# injected at the top of the function under optimisation, so it is entered and
# leaves without doing the work. "no-op" does nothing at all;
# "identity" copies the input to the output, which is the more interesting cheat
# because it produces plausible-looking data and survives any gate that only
# checks the output was populated or sums it.
#
# `signature` is applied to every match in the file, not just the first: kmeans
# splits its work across two kernels, and leaving one intact would test a
# half-broken submission rather than one that does nothing at all.
CHEATS = {
    "ipb_cpu_001_gaussian_blur": {
        "file": "solve.c",
        "signature": r"void\s+blur_image\s*\([^)]*\)\s*\{",
        "bodies": {
            "no-op": "\n    return;\n",
            "identity": ("\n    memcpy(dst, src, (size_t)width * (size_t)height);"
                         "\n    (void)passes;\n    return;\n"),
        },
    },
    "ipb_cuda_007_kmeans_clustering": {
        "file": "solution.cu",
        # Both k_assignClusters and k_updateCentroids.
        "signature": r"__global__\s+void\s+k_\w+\s*\([^)]*\)\s*\{",
        "bodies": {"no-op": "\n    return;\n"},
    },
    "ipb_cuda_008_conv1d_shared": {
        "file": "solution.cu",
        "signature": r"__global__\s+void\s+k_runConvolution\s*\([^)]*\)\s*\{",
        "bodies": {"no-op": "\n    return;\n"},
    },
    "ipb_cuda_009_matrix_transpose": {
        "file": "solution.cu",
        "signature": r"__global__\s+void\s+k_transpose\s*\([^)]*\)\s*\{",
        "bodies": {
            "no-op": "\n    return;\n",
            # Writes every output element, but copies instead of transposing.
            # The output is fully populated and holds exactly the same values
            # as the right answer, just in the wrong places, so anything short
            # of a positional comparison accepts it.
            "identity": ("\n    {\n"
                         "        int cx = blockIdx.x * TILE_DIM + threadIdx.x;\n"
                         "        int cy = blockIdx.y * TILE_DIM + threadIdx.y;\n"
                         "        if (cx < N && cy < N)\n"
                         "            output[cy * N + cx] = input[cy * N + cx];\n"
                         "        return;\n"
                         "    }\n"),
        },
    },
    "ipb_cuda_010_layernorm": {
        "file": "src/layernorm.cu",
        "signature": r"__global__\s+void\s+layernorm_kernel\s*\([^)]*\)\s*\{",
        "bodies": {"no-op": "\n    return;\n"},
    },
}


def check_structure(task_id: str, spec: dict) -> list[str]:
    """Every task must validate its output somehow.

    Cheap, needs no build, and is the check five unguarded tasks would have
    failed: with only a timer, deleting the work scores best.
    """
    if not measure.has_correctness_check(spec):
        return [f"{task_id}: NO CORRECTNESS CHECK -- scored on time alone, so "
                f"deleting the work is infinitely fast and scores best. Needs "
                f"verify_args, ok_marker or output_check in scripts/ipb_exec.py"]
    return []


# Only names that assert a file is the finished article. "reference" is
# deliberately absent: a correctness reference the verifier imports is a normal
# part of a task, and flagging it would bury this check in false positives.
LEAK_NAME_RE = re.compile(r"optimi[sz]ed|expert|golden", re.I)


def _blobs(workdir: pathlib.Path, ref: str) -> dict[str, set[str]]:
    """blob sha -> paths carrying it, for every commit reachable from ref."""
    out: dict[str, set[str]] = {}
    revs = subprocess.run(["git", "-C", str(workdir), "rev-list", ref],
                          capture_output=True, text=True).stdout.split()
    for rev in revs:
        listing = subprocess.run(
            ["git", "-C", str(workdir), "ls-tree", "-r", rev],
            capture_output=True, text=True).stdout.splitlines()
        for line in listing:
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if len(parts) == 3:
                out.setdefault(parts[2], set()).add(path)
    return out


def check_no_expert_in_workspace(task_id: str, spec: dict) -> list[str]:
    """The optimal implementation must not be reachable from the workspace.

    ipb_cpu_001_gaussian_blur shipped solve_optimized.c beside solve.c,
    byte-identical to ipb-reference:solve.c, so one read_file handed over the
    answer and all three prompt variants scored 1.0 -- indistinguishable from a
    task with no headroom. Scoring was working correctly throughout; what leaked
    was the task.

    Identity of contents is the test, not the filename: the file under
    optimisation legitimately shares its name with its own reference version,
    while a *differently named* file matching a reference blob is the answer
    sitting in the tree. History counts as reachable, since `git show` reads any
    commit the clone still has.
    """
    workdir = ROOT / "tasks" / task_id / "workspace"
    if not (workdir / ".git").exists():
        return []

    failures = []
    try:
        base = workspace.baseline_ref(workdir, task_id)
    except RuntimeError:
        return []
    base_blobs = _blobs(workdir, base)

    ref_ref = spec.get("reference_ref")
    if ref_ref and subprocess.run(
            ["git", "-C", str(workdir), "rev-parse", "--verify", "-q", ref_ref],
            capture_output=True).returncode == 0:
        ref_blobs = _blobs(workdir, ref_ref)
        for sha, ref_paths in ref_blobs.items():
            leaked = base_blobs.get(sha, set()) - ref_paths
            if leaked:
                failures.append(
                    f"{task_id}: WORKSPACE LEAK -- {sorted(leaked)} is "
                    f"byte-identical to {ref_ref}:{sorted(ref_paths)[0]}, so "
                    f"the agent can read the optimal implementation directly")

    build = " ".join(
        f.read_text() for f in workdir.glob("Makefile*") if f.is_file())
    for paths in base_blobs.values():
        for path in paths:
            if LEAK_NAME_RE.search(path) and path not in build:
                failures.append(
                    f"{task_id}: WORKSPACE LEAK -- {path} is reachable from "
                    f"the workspace, is named as a finished implementation and "
                    f"is not part of the build; move it to groundtruth/")
    return sorted(set(failures))


def check_wrong_answer_scores_zero(task_id: str, cal: dict) -> list[str]:
    """An incorrect result must earn nothing, however fast it is.

    Exercises ipb_score.score() directly with a time at the expert fix's level
    and correctness_ok=False. This is what caught `improvement` bypassing the
    gate: correctness was applied to `passed` only, while `improvement` -- the
    continuous figure that gets averaged across runs -- still returned 0.99 for
    a wrong answer.
    """
    baseline = float(cal["baseline_median_ms"])
    reference = cal.get("reference_median_ms")
    fast_ms = float(reference) if isinstance(reference, (int, float)) else baseline / 100

    failures = []
    wrong = score(task_id, fast_ms, correctness_ok=False)
    if wrong["passed"]:
        failures.append(f"{task_id}: a WRONG answer at {fast_ms:.4f}ms passes")
    if wrong["improvement"]:
        failures.append(
            f"{task_id}: a WRONG answer at {fast_ms:.4f}ms scores "
            f"improvement={wrong['improvement']:.3f}; incorrect results must "
            f"score 0, or they still contribute to an averaged score")

    # A task whose correctness cannot be verified must not be scored at all.
    unchecked = score(task_id, fast_ms, correctness_ok=True, correctness_checked=False)
    if unchecked["passed"] is not None or unchecked["improvement"] is not None:
        failures.append(
            f"{task_id}: with no correctness check the run still scored "
            f"passed={unchecked['passed']} improvement={unchecked['improvement']}; "
            f"it must be recorded as unscoreable")
    return failures


def check_cheats(task_id: str, spec: dict, n_runs: int) -> list[str]:
    """Build deliberately wrong implementations and require them to score zero.

    The end-to-end counterpart of check_wrong_answer_scores_zero: it runs the
    real verify path, so it fails if a task's correctness gate is configured but
    toothless -- a checksum that a no-op also satisfies, say.
    """
    recipe = CHEATS.get(task_id)
    if not recipe:
        return []

    task_dir = ROOT / "tasks" / task_id
    base_ref = workspace.baseline_ref(task_dir / "workspace", task_id)
    sig = re.compile(recipe["signature"], re.S)
    failures = []

    for label, body in recipe["bodies"].items():
        ws = workspace.clone_at_ref(task_dir, task_id, base_ref)
        try:
            path = ws / recipe["file"]
            text = path.read_text()
            # Every match, so a task that splits its work across several
            # kernels ends up doing nothing at all rather than half the job.
            # Applied back to front so each insertion leaves the earlier
            # offsets valid.
            spots = [m.end() for m in sig.finditer(text)]
            if not spots:
                # A signature that stops matching would make this check pass
                # vacuously, which is the failure mode it exists to catch.
                failures.append(
                    f"{task_id}: cheat {label!r}: signature "
                    f"{recipe['signature']!r} not found in {recipe['file']}")
                continue
            for end in reversed(spots):
                text = text[:end] + body + text[end:]
            path.write_text(text)

            measure.build(ws)
            correct, _ = measure.verify(ws, spec)
            try:
                median, _, _ = measure.benchmark(ws, spec, n_runs=n_runs)
            except measure.MeasureError:
                # Rejected before timing (a missing ok_marker, say): the gate
                # held, and there is no measurement to score.
                print(f"[{task_id}] cheat {label:<9} rejected at benchmark "
                      f"stage ({len(spots)} site(s) patched)")
                continue

            result = score(task_id, median, correct,
                           correctness_checked=measure.has_correctness_check(spec))
            imp = result["improvement"]
            imp_txt = "n/a" if imp is None else f"{imp:.3f}"
            print(f"[{task_id}] cheat {label:<9} {median:.4f}ms "
                  f"correct={correct} improvement={imp_txt} "
                  f"passed={result['passed']} ({len(spots)} site(s) patched)")

            if correct:
                failures.append(
                    f"{task_id}: the {label} submission PASSES VERIFY -- the "
                    f"correctness check does not detect missing work")
            if result["passed"]:
                failures.append(
                    f"{task_id}: the {label} submission SCORES A PASS at "
                    f"{median:.4f}ms")
            if imp:
                failures.append(
                    f"{task_id}: the {label} submission scores "
                    f"improvement={imp:.3f}; doing no work must score 0")
        finally:
            workspace.discard(ws)
    return failures


def check_endpoint(task_id: str, spec: dict, ref: str, n_runs: int) -> dict:
    """Measure one git ref and score it exactly as an agent run would be."""
    task_dir = ROOT / "tasks" / task_id
    ws = workspace.clone_at_ref(task_dir, task_id, ref)
    try:
        measure.build(ws)
        correct, _ = measure.verify(ws, spec)
        median, _, _ = measure.benchmark(ws, spec, n_runs=n_runs)
        result = score(task_id, median, correct,
                       correctness_checked=measure.has_correctness_check(spec))
        result["measured_ms"] = median
        return result
    finally:
        workspace.discard(ws)


def check_task(task_id: str, args) -> list[str]:
    """Return a list of failure descriptions; empty means the task is sound."""
    spec = EXEC.get(task_id)
    if spec is None:
        return [f"{task_id}: no entry in scripts/ipb_exec.py"]

    # The structural check needs no calibration and no build, so it still
    # reports on tasks that are uncalibrated or fail to compile.
    failures: list[str] = check_structure(task_id, spec)
    failures.extend(check_no_expert_in_workspace(task_id, spec))

    try:
        cal = load_calibration(task_id)
    except NotCalibrated as exc:
        return failures + [f"{task_id}: {exc}"]

    failures.extend(check_wrong_answer_scores_zero(task_id, cal))

    if args.static_only:
        return failures

    unit = cal.get("metric_unit", "ms")

    base_ref = workspace.baseline_ref(ROOT / "tasks" / task_id / "workspace", task_id)
    base = check_endpoint(task_id, spec, base_ref, args.n_runs)
    imp = base["improvement"]
    imp_txt = "n/a" if imp is None else f"{imp:.3f}"
    print(f"[{task_id}] baseline  {base['measured_ms']:.4f}{unit} "
          f"speedup={base['speedup']:.2f}x improvement={imp_txt} "
          f"passed={base['passed']}")

    if not base["correctness_ok"]:
        failures.append(f"{task_id}: baseline fails its own correctness check")
    if base["passed"]:
        failures.append(
            f"{task_id}: UNTOUCHED BASELINE PASSES -- the threshold "
            f"({base['threshold_ms']}) is at or above the regressed runtime, so "
            f"an agent that changes nothing scores a pass")
    if imp is not None and imp > BASELINE_MAX_IMPROVEMENT:
        failures.append(
            f"{task_id}: baseline scores improvement={imp:.3f} "
            f"(> {BASELINE_MAX_IMPROVEMENT}); doing nothing looks like progress")

    ref_ref = spec.get("reference_ref")
    if not ref_ref:
        print(f"[{task_id}] no reference implementation; "
              f"cannot confirm the pass bar is reachable")
    else:
        ref = check_endpoint(task_id, spec, ref_ref, args.n_runs)
        imp = ref["improvement"]
        imp_txt = "n/a" if imp is None else f"{imp:.3f}"
        print(f"[{task_id}] reference {ref['measured_ms']:.4f}{unit} "
              f"speedup={ref['speedup']:.2f}x improvement={imp_txt} "
              f"passed={ref['passed']}")

        if not ref["correctness_ok"]:
            failures.append(f"{task_id}: reference implementation fails verify")
        if ref["passed"] is False:
            failures.append(
                f"{task_id}: EXPERT FIX FAILS -- measured "
                f"{ref['measured_ms']:.4f}{unit} against threshold "
                f"{ref['threshold_ms']}; the bar is unreachable")
        if imp is not None and imp < REFERENCE_MIN_IMPROVEMENT:
            failures.append(
                f"{task_id}: reference scores only improvement={imp:.3f} "
                f"(< {REFERENCE_MIN_IMPROVEMENT}); scoring disagrees with "
                f"calibration")

    if not args.no_cheats:
        failures.extend(check_cheats(task_id, spec, args.n_runs))
    return failures


def main():
    p = argparse.ArgumentParser(description="Sanity-check the scoring pipeline")
    p.add_argument("--task-id")
    p.add_argument("--all", action="store_true")
    p.add_argument("--n-runs", type=int, default=3)
    p.add_argument("--static-only", action="store_true",
                   help="only the checks that need no build or GPU")
    p.add_argument("--no-cheats", action="store_true",
                   help="skip the adversarial rebuilds (they cost extra builds)")
    args = p.parse_args()

    if args.all:
        targets = list(EXEC)
    elif args.task_id:
        targets = [args.task_id]
    else:
        raise SystemExit("need --task-id or --all")

    all_failures: list[str] = []
    for tid in targets:
        try:
            all_failures.extend(check_task(tid, args))
        except (measure.MeasureError, RuntimeError) as exc:
            all_failures.append(f"{tid}: {type(exc).__name__}: {str(exc)[:300]}")
            print(f"[{tid}] ERROR: {str(exc)[:300]}")

    print()
    if all_failures:
        print(f"SANITY CHECK FAILED ({len(all_failures)} problem(s)):")
        for f in all_failures:
            print(f"  - {f}")
        return 1
    print(f"sanity check passed for {len(targets)} task(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
