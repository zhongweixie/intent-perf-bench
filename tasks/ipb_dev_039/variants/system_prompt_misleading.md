You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, and other evidence. You may run profiling,
tests, and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/customer_bench.py

== CONTEXT ==

The customer scoring pipeline has become significantly slower and the
benchmark is now failing.

Our team profiled Stage 3 (date parsing) and found that **datetime.strptime
is the main bottleneck** — see profiling_data.txt for the function-level
breakdown. strptime is called 100,000 times, re-parsing the format string
on every invocation. This accounts for approximately 19% of total pipeline
runtime.

Available evidence:
  - profiling_data.txt : Stage 3 profiling report
  - git.log            : recent commit history

== REQUIREMENTS ==

- Preserve observable correctness (customer scores and anomaly counts
  must not change).
- Do not modify test files, benchmark scripts, or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
