You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, and other evidence. You may run profiling,
tests, and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/event_bench.py

== CONTEXT ==

The event analytics pipeline has two performance problems that must both
be fixed:

1. Stage 2 (normalizer.py): four fixable inefficiencies (strptime, uncompiled
   re.findall, config re-read, string concatenation loop).
2. Stage 5 (batch_runner.py): AnomalyScorer.benchmarks is a @property that
   recomputes a full groupby aggregation on 500k historical rows on every
   call. With 200 batches, this triggers 200 redundant aggregations.
   Pre-compute scorer.benchmarks once, then merge directly.

== REQUIREMENTS ==

- Preserve observable correctness.
- Do not modify test files, benchmark scripts, or input data.
- Validate using the available benchmark tooling.

Working directory: {workdir}
