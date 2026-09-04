"""Clean, isolated baseline workspaces.

Calibration and agent evaluation share this module so both always start from
the same commit. Runs used to execute directly in tasks/<id>/workspace, a
single shared directory: two concurrent runs overwrote each other's binaries
and every run inherited whatever the previous one left behind.

REGRESSED_COMMITS lives here rather than inside the evaluator so the commit a
task is calibrated at cannot drift from the commit it is scored at.
"""

import os
import pathlib
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).parent.parent

# Isolated workspaces must live on shared storage: /tmp is node-local, so a
# clone made on the login node is invisible to whichever GPU node srun picks,
# which surfaces as "couldn't chdir" / "execve(): No such file or directory".
SCRATCH_ROOT = pathlib.Path(os.environ.get("IPB_SCRATCH", str(ROOT / ".scratch")))

# The commit holding each task's regressed (pre-fix) state. Tasks carrying an
# immutable ipb-baseline tag ignore this map -- see baseline_ref().
REGRESSED_COMMITS: dict[str, str] = {
    "ipb_dev_001": "HEAD~0",
    "ipb_dev_002": "a3f2c89",
    "ipb_dev_003": "8fd535f",
    "ipb_dev_004": "d8e9a72",
    "ipb_dev_005": "3b24939",
    "ipb_dev_006": "65e822b",
    "ipb_dev_007": "676cbdf",
    "ipb_dev_008": "82415dc",
    "ipb_dev_009": "5d8e3b1",
    "ipb_dev_010": "2c99539",
    "ipb_dev_011": "affb9d7",
    "ipb_dev_012": "014f17a",
    "ipb_dev_013": "efcad98",
    "ipb_dev_014": "ce09978",
    # ipb_dev_015+: HEAD is the regressed state (docs commit on top).
    **{f"ipb_dev_{n:03d}": "HEAD" for n in range(15, 42)},
    "ipb_cuda_001": "HEAD",
    "ipb_cuda_003": "HEAD",
    "ipb_cuda_004": "HEAD",
    "ipb_cuda_005_icp_correspondence": "HEAD",
    "ipb_cuda_005_l2norm_reduction": "HEAD",
    "ipb_cuda_007_kmeans_clustering": "HEAD",
    "ipb_cuda_008_conv1d_shared": "HEAD",
    "ipb_cuda_009_matrix_transpose": "HEAD",
    "ipb_cuda_010_layernorm": "HEAD~1",
    "ipb_cpu_001_gaussian_blur": "HEAD~1",
    "ipb_cpu_002_sha256_throughput": "HEAD~1",
    "ipb_cpu_003_vliw_scheduler": "HEAD~1",
    "ipb_cpu_004_aes128_ctr": "HEAD~1",
}


def baseline_ref(workdir: pathlib.Path, task_id: str) -> str:
    """Resolve the ref holding the regressed state.

    Prefers the immutable ipb-baseline tag. A relative ref such as HEAD~1 is
    self-consuming under `git reset --hard`: it moves the branch pointer, so
    after one run HEAD *is* the baseline and HEAD~1 refers somewhere else.
    """
    has_tag = subprocess.run(
        ["git", "-C", str(workdir), "rev-parse", "--verify", "ipb-baseline"],
        capture_output=True,
    ).returncode == 0
    if has_tag:
        return "ipb-baseline"
    ref = REGRESSED_COMMITS.get(task_id)
    if ref is None:
        raise RuntimeError(
            f"{task_id}: no ipb-baseline tag and no REGRESSED_COMMITS entry; "
            "refusing to guess which commit is the regressed state"
        )
    return ref


def _strip_expert_refs(dst: pathlib.Path, task_id: str) -> None:
    """Remove every path from the clone back to the expert solution.

    `git clone --local` copies refs/tags, so the clone handed to an agent
    carried ipb-reference: a single `git show ipb-reference:solve.c` printed the
    expert implementation. Deleting solve_optimized.* from the tree does not
    close this, so the fix has to happen at the ref level.

    Three separate doors, all of which have to shut:
      - tags, which name the expert commit directly;
      - the origin remote, which would let `git fetch` pull it back in;
      - unreachable objects, since the commit survives in the object database
        after its ref is gone and stays reachable through the reflog.

    Callers reset to their ref before this runs, so the working tree is already
    correct and only history is pruned. final_diff uses `git diff HEAD`, which
    does not consult tags.
    """
    def git(*args):
        return subprocess.run(["git", "-C", str(dst), *args],
                              capture_output=True, text=True)

    for tag in git("tag").stdout.split():
        git("tag", "-d", tag)
    for remote in git("remote").stdout.split():
        git("remote", "remove", remote)
    current = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    for branch in git("for-each-ref", "--format=%(refname:short)",
                      "refs/heads").stdout.split():
        if branch != current:
            git("branch", "-D", branch)
    git("reflog", "expire", "--expire=now", "--all")
    git("gc", "--prune=now", "--quiet")

    leaked = git("tag").stdout.split() + git("remote").stdout.split()
    if leaked:
        raise RuntimeError(f"{task_id}: refs still reach expert state: {leaked}")


def clone_at_ref(task_dir: pathlib.Path, task_id: str, ref: str) -> pathlib.Path:
    """Clone the task workspace into a private scratch dir at an explicit ref.

    Caller owns the returned directory and should pass it to discard().
    """
    src = task_dir / "workspace"
    if not (src / ".git").exists():
        raise RuntimeError(f"{task_id}: workspace is not a git repo, cannot isolate")

    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    holder = pathlib.Path(tempfile.mkdtemp(prefix=f"{task_id}_", dir=str(SCRATCH_ROOT)))
    dst = holder / "workspace"
    subprocess.run(
        ["git", "clone", "--local", "--no-hardlinks", "--quiet", str(src), str(dst)],
        capture_output=True, check=True,
    )
    # Tags are not fetched as branches by a local clone of a detached ref, but
    # `git clone` copies refs/tags, so ipb-baseline / ipb-reference resolve here.
    proc = subprocess.run(["git", "-C", str(dst), "reset", "--hard", "--quiet", ref],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        shutil.rmtree(holder, ignore_errors=True)
        raise RuntimeError(f"{task_id}: cannot check out {ref!r}: {proc.stderr.strip()}")
    subprocess.run(["git", "-C", str(dst), "clean", "-fdq"],
                   capture_output=True, check=True)
    _strip_expert_refs(dst, task_id)
    return dst


def clone_baseline(task_dir: pathlib.Path, task_id: str) -> pathlib.Path:
    """Clone the task workspace at its regressed baseline commit."""
    return clone_at_ref(task_dir, task_id, baseline_ref(task_dir / "workspace", task_id))


def discard(workspace: pathlib.Path) -> None:
    """Remove a workspace created by clone_baseline (its scratch parent included)."""
    shutil.rmtree(workspace.parent, ignore_errors=True)
