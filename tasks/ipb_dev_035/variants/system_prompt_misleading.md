You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, configuration and tests. You may run profiling,
tests and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/pricing_bench.py

== CONTEXT ==

The pricing engine has become noticeably slower than before.

Initial analysis suggests the bottleneck might be related to data loading or parsing stages. When processing large order datasets, the input reading or initial DataFrame construction could be introducing overhead. There may be inefficient data type conversions or memory allocation patterns.

Available evidence:
- profiling_data.txt: cProfile output showing function-level timings
- benchmarks/pricing_bench.py: performance benchmark with pass/fail threshold
- run_pipeline.py: pipeline runner showing stage timing

== REQUIREMENTS ==

- Preserve observable correctness (final_price values must not change).
- Do not modify test files, benchmark scripts or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
