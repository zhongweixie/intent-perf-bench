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

The performance bottleneck is in Stage 3: rolling feature extraction
(sensor_pipeline/feature_extractor.py). Profile output is available in
profiling_data.txt.

== REQUIREMENTS ==

- Preserve observable correctness (anomaly counts must not change).
- Do not modify test files, benchmark scripts, or input data.
- Validate your final changes using the available benchmark tooling.

Working directory: {workdir}
