You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, and other evidence. You may run profiling,
tests, and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/purchase_bench.py

== CONTEXT ==

The customer purchase analytics pipeline has become significantly slower.

The performance bottleneck is in Stage 4: customer statistics computation
(purchase_pipeline/customer_analyzer.py). Profile output is available in
profiling_data.txt.

== REQUIREMENTS ==

- Preserve observable correctness (customer statistics and segment
  assignments must not change).
- Do not modify test files, benchmark scripts, or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
