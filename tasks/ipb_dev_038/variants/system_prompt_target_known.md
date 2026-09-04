You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, and other evidence. You may run profiling,
tests, and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/sensor_bench.py

== CONTEXT ==

The IoT sensor anomaly detection pipeline has become significantly slower.

The bottleneck is in sensor_pipeline/feature_extractor.py.
The function extract_rolling_features uses rolling().apply() with a
numpy percentile callback for each window. Replace the two
rolling().apply(lambda x: np.percentile(x, N)) calls with
rolling().quantile(N/100) for each sensor channel — this uses the
C-implemented quantile routine instead of a Python callback.

== REQUIREMENTS ==

- Preserve observable correctness (anomaly counts must not change).
- Do not modify test files, benchmark scripts, or input data.
- Validate your final changes using the available benchmark tooling.

Working directory: {workdir}
