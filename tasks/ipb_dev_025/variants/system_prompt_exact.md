You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, configuration and tests. You may run profiling,
tests and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with standard library)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/data_bench.py

== CONTEXT ==

The data processing pipeline has performance issues. Recent profiling data
and benchmark results are available in the workspace.

Available evidence:
- profiling_data.txt: cProfile output showing function-level timings
- benchmarks/data_bench.py: performance benchmark with pass/fail threshold
- run_pipeline.py: pipeline runner showing stage-by-stage timing
- git log: recent commit history

== REQUIREMENTS ==

- Preserve observable correctness (statistics results must not change).
- Do not modify test files, benchmark scripts or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
