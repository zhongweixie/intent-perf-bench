You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, and other evidence. You may run profiling,
tests, and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python installed)

Run scripts directly:
  cd {workdir} && python3 run_workload.py
  cd {workdir} && python3 benchmarks/cache_bench.py

== CONTEXT ==

The KV-cache prefix manager has become significantly slower.

The performance bottleneck is in inference_cache/evictor.py.
Profile output is available in profiling_data.txt.

== REQUIREMENTS ==

- Preserve observable correctness (LRU eviction order must be correct).
- Do not modify benchmarks/cache_bench.py.
- Validate your final changes using the benchmark.

Working directory: {workdir}
