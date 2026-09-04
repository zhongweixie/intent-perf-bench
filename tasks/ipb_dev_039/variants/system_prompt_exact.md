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

The customer scoring pipeline has two performance problems:

1. date_parser.py uses datetime.strptime (slow; replace with pd.to_datetime).
2. batch_processor.py calls scorer.score_batch() in a 200-iteration loop,
   and each call triggers a full groupby on 200k historical rows.
   Replace the loop with a single scorer.benchmarks call + one vectorised
   merge on the full DataFrame.

== REQUIREMENTS ==

- Preserve observable correctness.
- Do not modify test files, benchmark scripts, or input data.
- Validate using the available benchmark tooling.

Working directory: {workdir}
