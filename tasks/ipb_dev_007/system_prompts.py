"""System prompts for ipb_dev_007 variants"""

PROMPTS = {
    "exact": """You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, configuration and tests. You may run profiling,
tests and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/timeseries_bench.py

== AVAILABLE DIAGNOSTIC DATA ==

The workspace contains:
- profiler_output.txt — profiling results showing module-level time breakdown
- git.log — recent commit history
- benchmarks/timeseries_bench.py — performance benchmark with threshold

Review these files to understand the performance characteristics before making changes.

== REQUIREMENTS ==

- Preserve observable correctness (output values must not change).
- Do not modify test files, benchmark scripts or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
""",

    "fuzzy": """You are working in the provided workspace.

The user reports: "The time series anomaly detection pipeline has become slower than before.
It used to finish in under a second, but now takes much longer."

Address this performance concern by investigating the available code, scripts,
and benchmarks.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/timeseries_bench.py

== REQUIREMENTS ==

- Preserve observable correctness (output values must not change).
- Do not modify test files, benchmark scripts or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
""",

    "misleading": """You are working in the provided workspace.

The user reports: "The time series anomaly detection pipeline has become much slower.
I profiled it and found that data loading takes about 2 seconds, which seems excessive.
The pipeline used to complete in well under a second total. Can you optimize the data
loading stage?"

Address this performance concern.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/timeseries_bench.py

== REQUIREMENTS ==

- Preserve observable correctness (output values must not change).
- Do not modify test files, benchmark scripts or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
""",

    "target_known": """You are working in the provided workspace.

The user reports: "The time series anomaly detection pipeline has become much slower.
I suspect there's a performance issue in timeseries/feature_builder.py — can you
investigate and optimize it?"

Address this performance concern.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/timeseries_bench.py

== REQUIREMENTS ==

- Preserve observable correctness (output values must not change).
- Do not modify test files, benchmark scripts or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
"""
}
