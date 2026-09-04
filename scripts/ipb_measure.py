"""Build, verify and time a native task workspace.

Imported by both scripts/calibrate_task.py and scripts/run_agent.py so a
baseline, a reference implementation and an agent's attempt are always measured
by identical code. When these lived separately, calibration recorded 56 ms for
ipb_cuda_001 while the evaluator scored against a hard-coded 124.3 ms.

CUDA tasks run through srun (spec["gpu"] is True); CPU tasks run locally.
"""

import json
import pathlib
import re
import statistics
import subprocess

ROOT = pathlib.Path(__file__).parent.parent
_COMMON_SH = ROOT / "scripts" / "bench_common.sh"

# Fallback metric keys, used when a task defines no explicit metric_regex.
# Binaries emit either JSON ({"time_ms": 1.5}) or key=value (time_ms=1.5).
_METRIC_KEYS = ("time_ms", "median_ms", "cycles")


class MeasureError(RuntimeError):
    """Build failed, or the workload produced no usable measurement."""


class InfraError(MeasureError):
    """The job never ran the workload (scheduler, filesystem or launch fault).

    Kept distinct from a correctness failure: a node-local scratch dir once made
    the binary invisible to the GPU node, and reporting that as "the baseline
    fails its own correctness check" aims debugging at the task, not the rig.
    """


# Faults that mean the workload never actually started.
_INFRA_PATTERNS = (
    r"couldn't chdir",
    r"execve\(\)",
    r"going to /tmp instead",
    r"Unable to allocate resources",
    r"invalid partition",
    r"system not yet initialized",
    r"CUDA driver version is insufficient",
    r"no CUDA-capable device",
)


def _raise_if_infra(log: str, what: str) -> None:
    for pat in _INFRA_PATTERNS:
        if re.search(pat, log, re.IGNORECASE):
            raise InfraError(f"{what}: job did not run the workload:\n{log}")


def _run(workdir: pathlib.Path, spec: dict, argv: list[str],
         timeout: int) -> subprocess.CompletedProcess:
    """Run ./<binary> <args> from the workspace root, on a GPU if the task needs one."""
    quoted = " ".join(f"'{a}'" for a in argv)
    launcher = "ipb_gpu_run " if spec.get("gpu") else ""

    # bench_env: environment variables for --benchmark-verify hidden seeds
    # Use export so they survive through srun (direct prefix only works locally)
    env_setup = ""
    if spec.get("bench_env"):
        exports = " && ".join(f"export {k}={v}" for k, v in spec["bench_env"].items())
        env_setup = exports + " && "

    return subprocess.run(
        ["bash", "-c",
         f"source '{_COMMON_SH}' && cd '{workdir}' && {env_setup}{launcher}{quoted}"],
        capture_output=True, text=True, timeout=timeout,
    )


def build(workdir: pathlib.Path, timeout: int = 300) -> str:
    """make clean && make. Raises MeasureError on failure."""
    proc = subprocess.run(
        ["bash", "-c",
         f"source '{_COMMON_SH}' && export PATH=\"$IPB_CUDA_BIN:$PATH\" && "
         f"cd '{workdir}' && make clean && make"],
        capture_output=True, text=True, timeout=timeout,
    )
    log = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise MeasureError(f"build failed:\n{log}")
    return log


def parse_metric(text: str, spec: dict | None = None) -> float | None:
    """Extract the timing metric, scaled to the task's metric_unit."""
    if spec and spec.get("metric_regex"):
        m = re.search(spec["metric_regex"], text)
        if not m:
            return None
        return float(m.group(1)) * float(spec.get("metric_scale", 1.0))

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            for key in _METRIC_KEYS:
                if key in data:
                    return float(data[key])
    for key in _METRIC_KEYS:
        m = re.search(rf'{key}["\s:=]+([\d.]+)', text, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None


def has_correctness_check(spec: dict) -> bool:
    """Whether anything at all validates this task's output.

    A task with no check cannot be scored: deleting the kernel body is
    infinitely fast, so timing alone rewards doing no work.
    """
    return (spec.get("verify_args") is not None
            or bool(spec.get("ok_marker"))
            or bool(spec.get("output_check")))


def _check_output_image(workdir: pathlib.Path, spec: dict,
                        timeout: int) -> tuple[bool, str]:
    """Run the binary so it writes an output file, and compare it to a stored
    expected file allowing `tolerance` per byte.

    Used where the harness has no usable self-check. ipb_cpu_001's checksum is
    the example: it is 0 for every implementation on an all-zero input, so a
    deleted blur_image body passed while timing 0.000000s.
    """
    oc = spec["output_check"]
    expected_path = pathlib.Path(oc["expected"])
    if not expected_path.is_absolute():
        expected_path = ROOT / expected_path
    if not expected_path.exists():
        raise MeasureError(
            f"output_check expected file missing: {expected_path}; "
            f"run tools/make_blur_oracle.py")

    out = workdir / "__ipb_verify_out.bin"
    out.unlink(missing_ok=True)
    argv = [f"./{spec['binary']}", *[str(out) if a == "{out}" else a
                                     for a in oc["args"]]]
    proc = _run(workdir, spec, argv, timeout)
    log = proc.stdout + proc.stderr
    _raise_if_infra(log, "output_check")
    if proc.returncode != 0:
        return False, log + f"\n[output_check: exited {proc.returncode}]"
    if not out.exists():
        return False, log + "\n[output_check: produced no output file]"

    got = out.read_bytes()
    want = expected_path.read_bytes()
    out.unlink(missing_ok=True)
    if len(got) != len(want):
        return False, log + (f"\n[output_check: got {len(got)} bytes, "
                             f"expected {len(want)}]")
    tol = int(oc.get("tolerance", 0))
    worst = 0
    nbad = 0
    for x, y in zip(got, want):
        d = x - y if x > y else y - x
        if d > worst:
            worst = d
        if d > tol:
            nbad += 1
    ok = nbad == 0
    return ok, log + (f"\n[output_check: max|d|={worst} tolerance={tol} "
                      f"out_of_tolerance={nbad} -> {'ok' if ok else 'FAILED'}]")


def verify(workdir: pathlib.Path, spec: dict, timeout: int = 600) -> tuple[bool, str]:
    """Run the task's correctness check.

    verify_args is the argv tail for correctness mode; [] means the harness
    validates when run with no arguments (the CUDA test binaries here select
    performance mode via --perf/--benchmark, so bare invocation is the check).
    None means the task has no separate mode -- correctness is then either
    folded into the benchmark run via ok_marker, or absent entirely, which
    has_correctness_check() reports.

    A positive verify_marker is required where the harness has one: exit codes
    and failure-word matching are both too weak on their own. The transpose
    harness prints "FAIL" and still exits 0, and an optimisation that silently
    produces no output would otherwise read as success.
    """
    if spec.get("output_check"):
        return _check_output_image(workdir, spec, timeout)

    args = spec.get("verify_args")
    if args is None:
        return True, "[no separate verify mode]"
    proc = _run(workdir, spec, [f"./{spec['binary']}", *args], timeout)
    log = proc.stdout + proc.stderr
    _raise_if_infra(log, "verify")
    ok = proc.returncode == 0 and not re.search(
        r"correctness_fail|MISMATCH|FAILED|FAIL\b|verification failed", log, re.IGNORECASE
    )
    marker = spec.get("verify_marker")
    if ok and marker and marker not in log:
        ok = False
        log += f"\n[verify: required marker {marker!r} absent from output]"
    return ok, log


def benchmark(workdir: pathlib.Path, spec: dict, n_runs: int = 1,
              timeout: int = 600) -> tuple[float, list[float], str]:
    """Time the workload n_runs times; return (median, samples, log)."""
    samples: list[float] = []
    logs: list[str] = []
    marker = spec.get("ok_marker")
    for i in range(n_runs):
        proc = _run(workdir, spec, [f"./{spec['binary']}", *spec["bench_args"]], timeout)
        log = proc.stdout + proc.stderr
        logs.append(log)
        _raise_if_infra(log, f"benchmark run {i + 1}")
        if proc.returncode != 0:
            raise MeasureError(f"benchmark run {i + 1} exited {proc.returncode}:\n{log}")
        # Tasks without a --verify mode signal correctness here; a fast but
        # wrong result must not be timed as if it were valid.
        if marker and marker not in log:
            raise MeasureError(
                f"benchmark run {i + 1} did not report '{marker}':\n{log}")
        value = parse_metric(log, spec)
        if value is None:
            raise MeasureError(f"benchmark run {i + 1} produced no parsable metric:\n{log}")
        samples.append(value)
    return statistics.median(samples), samples, "\n".join(logs)


def cv(samples: list[float]) -> float | None:
    """Coefficient of variation, for judging measurement stability."""
    if len(samples) < 2:
        return None
    mean = statistics.mean(samples)
    if mean == 0:
        return None
    return statistics.stdev(samples) / mean
