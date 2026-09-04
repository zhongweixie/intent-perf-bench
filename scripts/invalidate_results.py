"""Mark historical result files as invalid for performance scoring.

    python scripts/invalidate_results.py --dry-run
    python scripts/invalidate_results.py --apply

Every result produced before the scoring rebuild carries a performance verdict
that cannot be reproduced. The specific defect differs by task, so each file
records only the reasons that actually apply to it rather than one blanket
claim -- attributing the CUDA correctness bug to a pandas task would make the
record wrong in a new way.

The files are not deleted, and trajectory metrics are left untouched: which
file the agent edited, whether it followed the misleading prompt and how many
turns it took were never derived from the timing numbers, and those process
metrics are the bulk of what these runs were collected to measure. This script
quarantines `passed` and `improvement_score` into `invalidated_scores` so
nothing downstream reads them by accident.

results/.archived/ is skipped on purpose: those ipb_cuda_002 runs were already
withdrawn when that task was found to duplicate ipb_cuda_005_icp_correspondence.

Carrying score_detail is not enough to trust a file. Five tasks were scored
through the rebuilt pipeline while shipping no correctness check at all, so
their runs have full scoring provenance standing behind a number that only ever
measured time -- a deleted blur_image body timed 0.000000s and scored
improvement=1.0. The discriminator is score_detail.correctness_checked, added
when the gates were fixed: a run scored without that key has no evidence its
work was checked, however complete its provenance looks.

Reasons are also topped up on files already marked, because the reason list is
the whole value of the archive. The first pass predated the discovery that five
tasks had no correctness check, so it recorded a hard-coded baseline as the only
defect on the very runs where deleting the work scored best.
"""

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent.parent
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "scripts"))

from ipb_exec import EXEC  # noqa: E402

# Trajectory/process metrics are independent of the timing pipeline and survive
# invalidation; only these two keys carry the performance verdict.
SCORE_KEYS = ("passed", "improvement_score")

# Tasks that shipped with no correctness check of any kind, so every score they
# ever produced was a timing measurement with nothing asserting the work was
# done. Historical only: all of them are gated now, and sanity_check.py fails
# any task that is not, so this list must not grow.
# Tasks that shipped the expert implementation as solve_optimized.* inside the
# agent-visible workspace. Historical only: the file has been moved to
# groundtruth/expert/ and purged from workspace history, so this list must not
# grow. A run is only tainted if it actually read the file -- see read_expert().
LEAK_TASKS = {
    "ipb_cpu_001_gaussian_blur",
    "ipb_cpu_002_flash_attention",
    "ipb_cpu_003_bvh_raytracer",
    "ipb_cpu_004_hash_join",
}

UNGATED_TASKS = {
    "ipb_cpu_001_gaussian_blur",
    "ipb_cuda_007_kmeans_clustering",
    "ipb_cuda_008_conv1d_shared",
    "ipb_cuda_009_matrix_transpose",
    "ipb_cuda_010_layernorm",
}

REASONS = {
    "hardcoded_baseline":
        "Scored against baseline/threshold constants hard-coded in "
        "run_agent.py that disagreed with groundtruth and bench.sh "
        "(ipb_cuda_001 recorded 124.3ms vs 65.4ms measured, so an untouched "
        "workspace scored 0.48).",
    "no_correctness_gate":
        "The task had no correctness check of any kind -- no verify mode, no "
        "output marker, no expected output -- so the score measured time "
        "alone. Deleting the function body is infinitely fast and scored "
        "best: an empty blur_image timed 0.000000s and scored "
        "improvement=1.0. No score from this task can be distinguished from "
        "one earned by doing nothing.",
    "verify_skipped":
        "The CUDA path never ran the correctness check and set passed=True "
        "whenever a time could be parsed, so a fast but incorrect kernel "
        "counted as a pass.",
    "improvement_ungated":
        "Correctness was applied to `passed` only, so an incorrect result "
        "still reported its full `improvement` -- the continuous figure that "
        "gets averaged across runs. A wrong answer measured 0.989.",
    "shared_workspace":
        "All runs built in the shared tasks/<id>/workspace, so concurrent "
        "runs overwrote each other's binaries and each run inherited whatever "
        "the previous one left behind.",
    "no_measurement":
        "The benchmark printed no timing, so improvement_score came from the "
        "`1.0 if passed else 0.0` fallback and has no measurement behind it.",
    "unverified_constants":
        "Scored against _TIMING_CONSTANTS entries of unknown provenance that "
        "were never measured on this cluster.",
    "workspace_leak":
        "The task shipped the expert implementation inside the agent-visible "
        "workspace as solve_optimized.*, sitting next to the file under "
        "optimisation, and this run read it. For ipb_cpu_001_gaussian_blur that "
        "file was byte-identical to ipb-reference:solve.c, so the optimal answer "
        "was one tool call away and any variant could pass by copying it -- "
        "which is why the task looked like a ceiling with no discrimination. A "
        "correct scoring pipeline cannot rescue these runs: what was broken is "
        "the task, not the measurement.",
    "harness_injection":
        "The serving layer in front of the model decorated a tool result with "
        "instructions meant for itself (\"This file was already read in this "
        "conversation...\" / \"Previous Read result:\"), and write_file -- a "
        "whole-file overwrite, the agent's only editing tool -- wrote that "
        "prose into the source as lines 1-2. The build died with 15 nvcc "
        "errors, so the recorded failure belongs to the harness, not the "
        "agent. run_agent.py now strips these notices at the write side and "
        "records every strip in injected_notices_stripped.",
}

# Matched against final_diff. Only an added line counts: the same prose appears
# in the trajectory of runs where the agent read it and never wrote it back, and
# those runs are unaffected.
#
# The prose is not always flush against the '+'. read_file used to prefix every
# line with its number (#108), so a doubly-affected run delivers
# "+1\tThis file was already read..." -- the m1 ipb_cpu_002 workspace shows
# exactly that. Allowing digits and whitespace in between is what makes the two
# defects detectable together instead of one hiding the other.
INJECTION_MARKER_RE = re.compile(
    r"^\+[\s\d]*(?:This file was already read in this conversation"
    r"|Previous Read result:)",
    re.MULTILINE,
)


def original_score(data: dict, key: str):
    """The score as first recorded, from quarantine if already invalidated."""
    if "invalidated_scores" in data:
        return data["invalidated_scores"].get(key)
    return data.get(key)


def is_trusted(data: dict) -> bool:
    """Whether this file's verdict came from the pipeline as it stands now.

    score_detail alone is not the test: the correctness_checked key was added
    when the gates were fixed, so provenance written before it describes a run
    whose output nothing validated.
    """
    detail = data.get("score_detail")
    return isinstance(detail, dict) and "correctness_checked" in detail


def was_injected(data: dict) -> bool:
    """Whether harness-injected prose was written into the delivered source."""
    return bool(INJECTION_MARKER_RE.search(data.get("final_diff") or ""))


def read_expert(data: dict, task_id: str) -> bool:
    """Whether this run reached the leaked expert implementation.

    Checked against the trajectory rather than the diff: copying the file is
    only the most blatant use, and a run that merely read it already had the
    answer in context. Any tool call naming solve_optimized counts, since
    read_file, `cat` and `cp` all deliver the same contents.
    """
    if task_id not in LEAK_TASKS:
        return False
    for step in data.get("trajectory") or []:
        if not isinstance(step, dict):
            continue
        if "solve_optimized" in json.dumps(step.get("input") or ""):
            return True
    return "solve_optimized" in (data.get("final_diff") or "")


def reasons_for(data: dict, task_id: str, shared_ws: bool) -> list[str]:
    """Only the defects that actually applied to this run."""
    out = []
    # An injected run never reached the scoring pipeline -- the build failed --
    # so none of the scoring defects below can be what went wrong with it.
    # Listing them anyway would blame a stale baseline for a broken source
    # file, which is the mislabelling this per-file reason list exists to
    # avoid. The score keys are still quarantined by the caller.
    if was_injected(data):
        return ["harness_injection"]
    # A run scored by the pipeline as it stands now has no scoring defect left
    # to report, so the leak is the whole story for it.
    leaked = read_expert(data, task_id)
    if leaked and is_trusted(data):
        return ["workspace_leak"]
    native = task_id in EXEC
    if native:
        out.append("hardcoded_baseline")
        if task_id.startswith("ipb_cuda_"):
            out.append("verify_skipped")
    else:
        out.append("unverified_constants")
    if task_id in UNGATED_TASKS:
        out.append("no_correctness_gate")
    # A scored run reported `improvement` through the ungated path. Runs with no
    # improvement figure at all have nothing to say about that defect.
    if isinstance(original_score(data, "improvement_score"), (int, float)):
        out.append("improvement_ungated")
    if leaked:
        out.append("workspace_leak")
    if shared_ws:
        out.append("shared_workspace")
    if data.get("elapsed_time") is None and original_score(
            data, "improvement_score") in (0.0, 1.0):
        out.append("no_measurement")
    return out


def main():
    p = argparse.ArgumentParser(description="Quarantine pre-rebuild scores")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="report only")
    g.add_argument("--apply", action="store_true", help="rewrite the files")
    p.add_argument("--results-dir", default=str(RESULTS))
    p.add_argument("--no-relabel", action="store_true",
                   help="leave already-marked files alone even if new reasons "
                        "now apply to them")
    args = p.parse_args()

    files = sorted(pathlib.Path(args.results_dir).glob("*.json"))
    if not files:
        print(f"no result files under {args.results_dir}")
        return 0

    # Whether the task's workspace is a git repo decides if runs shared it.
    shared_cache: dict[str, bool] = {}
    per_task = collections.Counter()
    per_reason = collections.Counter()
    added_reason = collections.Counter()
    unchanged = kept = changed = relabelled = skipped_shape = 0

    for path in files:
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            print(f"  SKIP (unparsable): {path.name}")
            continue

        # results/ also holds hand-written aggregate reports (a JSON list, e.g.
        # remeasure_m1.json) that are not runs and carry no score keys. They
        # have no per-run verdict to quarantine, and treating one as a run dict
        # crashed this script.
        if not isinstance(data, dict) or "task_id" not in data:
            skipped_shape += 1
            continue

        task_id = data.get("task_id", "?")
        # is_trusted only certifies the scoring pipeline. A leaked task defeats
        # scoring that is working perfectly, so it has to be checked too.
        if is_trusted(data) and not read_expert(data, task_id):
            kept += 1
            continue

        if task_id not in shared_cache:
            shared_cache[task_id] = (ROOT / "tasks" / task_id / "workspace" / ".git").exists()

        why = reasons_for(data, task_id, shared_cache[task_id])
        marked = "invalidated_scores" in data

        if marked:
            if args.no_relabel:
                unchanged += 1
                continue
            new = [r for r in why if r not in (data.get("invalidated_reasons") or [])]
            if not new:
                unchanged += 1
                continue
            added_reason.update(new)
            relabelled += 1
            if args.apply:
                # Never re-quarantine: the scores are already in
                # invalidated_scores and the live keys are None, so popping
                # again would overwrite the originals with None.
                data["invalidated_reasons"] = why
                data["invalidated_detail"] = [REASONS[r] for r in why]
                path.write_text(json.dumps(data, indent=2, default=str) + "\n")
            continue

        per_task[task_id] += 1
        per_reason.update(why)
        if args.apply:
            data["invalidated_scores"] = {k: data.pop(k, None) for k in SCORE_KEYS}
            data["invalidated_reasons"] = why
            data["invalidated_detail"] = [REASONS[r] for r in why]
            for k in SCORE_KEYS:
                data[k] = None
            path.write_text(json.dumps(data, indent=2, default=str) + "\n")
        changed += 1

    verb = "would invalidate" if args.dry_run else "invalidated"
    verb2 = "would add reasons to" if args.dry_run else "added reasons to"
    print(f"{verb} {changed} file(s); {verb2} {relabelled} already-marked "
          f"file(s); {unchanged} already complete; {kept} kept (scored with a "
          f"correctness gate); {skipped_shape} skipped (not a run file)\n")
    if per_task:
        print("newly invalidated:")
        for task, n in sorted(per_task.items()):
            print(f"  {n:4d}  {task}")
        print("\nreasons applied:")
        for r, n in per_reason.most_common():
            print(f"  {n:4d}  {r}")
    if added_reason:
        print("\nreasons added to already-marked files:")
        for r, n in added_reason.most_common():
            print(f"  {n:4d}  {r}")
    if args.dry_run:
        print("\ndry run; re-run with --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
