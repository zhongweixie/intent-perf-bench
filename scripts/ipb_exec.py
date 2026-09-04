"""Single registry of how to build, verify and benchmark each native task.

Both the calibration script and the agent evaluator import this module, so a
task can never be calibrated with one command and scored with another -- the
failure mode that let an unmodified workspace score 0.48 on ipb_cuda_001.

Timing values deliberately live in each task's groundtruth/measurement.json
(written by scripts/calibrate_task.py), never here: hard-coding them in the
evaluator is what allowed three mutually inconsistent copies to drift apart.

Per-task keys:
  gpu           run the binary through srun (CUDA) or locally (CPU)
  binary        executable produced by `make`, run from the workspace root
  bench_args    argv for the timed run
  verify_args   argv tail for correctness mode. [] means the harness validates
                when run with no arguments; None means it has no separate mode
                (correctness then comes from ok_marker or output_check)
  verify_marker substring the correctness run must print. Required wherever the
                harness prints one, because exit status alone is unreliable:
                the transpose harness prints FAIL and still exits 0
  output_check  compare a written output file against a stored expected file
                within a tolerance; for tasks whose harness self-check is
                unusable. See tools/make_blur_oracle.py
  ok_marker     substring the benchmark must print for the result to count;
                used by tasks whose correctness check is folded into the run
  metric_regex  capture group 1 is the raw metric
  metric_scale  multiplier converting the raw metric to metric_unit
  reference_ref git ref holding a working expert fix, or None if the task has
                none -- ipb_cuda_001/003/004 are the three such tasks, their
                task.toml reference_commit values are all dangling refs
  threshold_speedup
                explicit pass bar as a multiple of the measured baseline. Only
                needed when reference_ref is None; otherwise calibration
                derives the bar from the measured reference.

Every entry must satisfy ipb_measure.has_correctness_check(): a task that only
reports a time cannot be scored, because deleting the work is infinitely fast.
scripts/sanity_check.py asserts this and rejects no-op submissions.

CPU tasks intentionally bypass benchmarks/bench.sh: those scripts hard-code
`cd "$(dirname "$0")/../workspace"`, the shared task directory, so under
per-run workspace isolation they would measure the pristine baseline instead
of the agent's edits and every agent would score exactly baseline.
"""

import pathlib as _pathlib

_BLUR_GT = _pathlib.Path(__file__).parent.parent / "tasks" / "ipb_cpu_001_gaussian_blur" / "groundtruth"
_BLUR_INPUT = _BLUR_GT / "blur_input_256.raw"
_BLUR_EXPECTED = _BLUR_GT / "blur_expected_256.raw"

_CUDA = {"gpu": True, "metric_regex": None, "metric_scale": 1.0,
         "metric_unit": "ms", "ok_marker": None, "verify_marker": None,
         "output_check": None}

EXEC: dict[str, dict] = {
    # ── CUDA tasks ────────────────────────────────────────────────────────
    "ipb_cuda_001": {
        **_CUDA,
        "binary": "huffman_decode",
        "verify_args": ["--verify"],
        "bench_args": ["--benchmark-verify"],
        "bench_env": {"HUFFMAN_DECODE_SEED": "0xc0ffee42"},
        "reference_ref": None,
        # groundtruth/measurement.json and benchmarks/bench.sh both documented 5x.
        "threshold_speedup": 5.0,
    },
    "ipb_cuda_003": {
        **_CUDA,
        "binary": "ntt_butterfly",
        "verify_args": ["--verify"],
        "bench_args": ["--benchmark-verify"],
        "bench_env": {"NTT_BENCH_SEED": "0xdeadbeef"},
        "reference_ref": None,
        "threshold_speedup": None,
    },
    "ipb_cuda_004": {
        **_CUDA,
        "binary": "msm_bls12381",
        "verify_args": ["--verify"],
        "bench_args": ["--benchmark-verify"],
        "bench_env": {"MSM_BENCH_SEED": "0x1337cafe"},
        "reference_ref": None,
        "threshold_speedup": None,
    },
    "ipb_cuda_005_icp_correspondence": {
        **_CUDA,
        "binary": "icp_corr",
        "verify_args": ["--verify"],
        "bench_args": ["--benchmark-verify"],
        "reference_ref": "ipb-reference",
        "threshold_speedup": None,
    },
    "ipb_cuda_005_l2norm_reduction": {
        **_CUDA,
        "binary": "l2norm_benchmark",
        "verify_args": ["--verify"],
        "bench_args": ["--benchmark"],
        # This one reports "Average time: 0.0078 ms" instead of the time_ms /
        # median_ms the other CUDA tasks emit.
        "metric_regex": r"Average time:\s*([0-9.eE+-]+)\s*ms",
        "reference_ref": "ipb-reference",
        # Retained as a trivial control: no regression to fix.
        "threshold_speedup": None,
    },
    "ipb_cuda_007_kmeans_clustering": {
        **_CUDA,
        "binary": "kmeans_test",
        # test_main.cu picks benchmark mode with --perf, so a bare run is the
        # correctness path: it asserts against expected centroid sums and
        # prints PASS. The evaluator previously never invoked it.
        "verify_args": [],
        "verify_marker": "PASS",
        "bench_args": ["--perf"],
        "reference_ref": "ipb-reference",
        "threshold_speedup": None,
    },
    "ipb_cuda_008_conv1d_shared": {
        **_CUDA,
        "binary": "conv1d_test",
        # This harness asserts (aborting on mismatch) but prints no success
        # line, so the gate is exit status only -- weaker than the others.
        "verify_args": [],
        "verify_marker": None,
        "bench_args": ["--perf"],
        "reference_ref": "ipb-reference",
        "threshold_speedup": None,
    },
    "ipb_cuda_009_matrix_transpose": {
        **_CUDA,
        "binary": "transpose_test",
        # Prints FAIL and still exits 0 on mismatch, so the positive marker is
        # what actually gates this task.
        "verify_args": [],
        "verify_marker": "PASS",
        "bench_args": ["--perf"],
        "reference_ref": "ipb-reference",
        "threshold_speedup": None,
    },
    "ipb_cuda_010_layernorm": {
        **_CUDA,
        "binary": "layernorm_test",
        "verify_args": [],
        "verify_marker": "PASSED",
        "bench_args": ["--benchmark"],
        "reference_ref": "ipb-reference",
        "threshold_speedup": None,
    },

    # ── Native CPU tasks ──────────────────────────────────────────────────
    # These print `time=<seconds>` or `cycles=<n>` plus a `result=ok` marker.
    "ipb_cpu_001_gaussian_blur": {
        "gpu": False,
        "binary": "blur",
        "verify_args": None,
        "verify_marker": None,
        # Timed on the same fixed image the oracle uses, not /dev/zero.
        "bench_args": [str(_BLUR_INPUT), "-", "256", "256"],
        "metric_regex": r"time=([0-9.]+)",
        "metric_scale": 1000.0,
        "metric_unit": "ms",
        # The harness checksum is not a usable oracle: it is 0 for every
        # implementation on an all-zero input (a deleted blur_image body timed
        # 0.000000s and scored improvement=1.0), and on a real image the
        # baseline and the expert fix disagree by 4, so an exact match would
        # reject the fix. Compare pixels with a tolerance instead: the fix is
        # within 1 everywhere, identity and no-op are off by ~148.
        "ok_marker": None,
        "output_check": {
            "args": [str(_BLUR_INPUT), "{out}", "256", "256"],
            "expected": str(_BLUR_EXPECTED),
            "tolerance": 1,
        },
        "reference_ref": "ipb-reference",
        "threshold_speedup": None,
    },
    "ipb_cpu_002_sha256_throughput": {
        "gpu": False,
        "binary": "solve",
        "verify_args": None,
        "bench_args": [],
        "metric_regex": r"time=([0-9.]+)",
        "metric_scale": 1000.0,
        "metric_unit": "ms",
        "ok_marker": "result=ok",
        "reference_ref": "ipb-reference",
        "threshold_speedup": None,
    },
    "ipb_cpu_003_vliw_scheduler": {
        "gpu": False,
        "binary": "solve",
        "verify_args": None,
        "bench_args": [],
        "metric_regex": r"cycles=([0-9]+)",
        "metric_scale": 1.0,
        "metric_unit": "cycles",
        "ok_marker": "result=ok",
        "reference_ref": "ipb-reference",
        "threshold_speedup": None,
    },
    "ipb_cpu_004_aes128_ctr": {
        "gpu": False,
        "binary": "solve",
        "verify_args": None,
        "bench_args": [],
        "metric_regex": r"time=([0-9.]+)",
        "metric_scale": 1000.0,
        "metric_unit": "ms",
        "ok_marker": "result=ok",
        "reference_ref": "ipb-reference",
        "threshold_speedup": None,
    },
}

# ipb_cuda_002 is intentionally absent: it is the same task as
# ipb_cuda_005_icp_correspondence with mismatched constants (task #87).
