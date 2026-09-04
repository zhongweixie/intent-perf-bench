"""System prompts for ipb_dev_009 variants."""

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
  cd {workdir} && python3 benchmarks/feature_bench.py

== AVAILABLE DIAGNOSTIC DATA ==

Performance profiler output is available in profiler_output.txt
Git commit history is available in git.log

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

The user reports that the feature engineering pipeline has become slower
than it used to be. Investigate and fix the performance issue.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/feature_bench.py

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

The user reports that the feature engineering pipeline has become slower.
They mention that the data loading stage seems to take around 0.5 seconds,
which feels excessive for loading 100k rows from the database. The load
stage accounts for about 13% of total runtime. This might be the bottleneck.

Investigate and fix the performance issue.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/feature_bench.py

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

The user reports that the feature engineering pipeline has become slower.
They suspect the issue is in feature_eng/builder.py in the feature building
logic.

Investigate and fix the performance issue.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/feature_bench.py

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
