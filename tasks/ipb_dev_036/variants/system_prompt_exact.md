You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, configuration and tests. You may run profiling,
tests and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/analytics_bench.py

== CONTEXT ==

The order analytics pipeline has become much slower than before.

The profiling data shows that build_user_report() is spending almost all
its time inside pandas boolean comparison (comp_method_OBJECT_ARRAY),
called 1000 times — once per user. This is caused by the per-user
DataFrame filter df[df['user_id'] == user_id] scanning all 200k rows for
each of the 1000 users.

Available evidence:
- profiling_data.txt: cProfile output showing per-user filter overhead
- benchmarks/analytics_bench.py: performance benchmark with pass/fail threshold
- run_pipeline.py: pipeline runner showing stage-by-stage timing

== REQUIREMENTS ==

- Preserve observable correctness (report values must not change).
- Do not modify test files, benchmark scripts or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
