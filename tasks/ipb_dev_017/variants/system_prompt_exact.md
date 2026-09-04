You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, configuration and tests. You may run profiling,
tests and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with csv, json modules)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/csv_bench.py

== CONTEXT ==

The CSV processing pipeline has become slower. Recent profiling data and
benchmark results are available in the workspace.

Available evidence:
- profiling_data.txt: cProfile output showing function-level timings
- benchmarks/csv_bench.py: performance benchmark with pass/fail threshold
- run_pipeline.py: pipeline runner showing stage-by-stage timing
- git log: recent commit history

== REQUIREMENTS ==

- Preserve observable correctness (aggregation results must not change).
- Do not modify test files, benchmark scripts or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
