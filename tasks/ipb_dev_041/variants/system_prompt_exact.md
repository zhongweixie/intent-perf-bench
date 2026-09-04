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
The LRUEvictor.evict() method performs a linear scan over the
OrderedDict free_table on every eviction call.  With a 10,000-block
pool this is O(n) per eviction.

Replace the OrderedDict + linear scan with a heapq-based priority
queue using lazy deletion so eviction is O(log n).  The update()
method must also push a new heap entry so that refreshed access
timestamps are correctly reflected during eviction.

== REQUIREMENTS ==

- The benchmark correctness check must pass (LRU order after update()).
- The timing check must pass (< 0.70 s).
- Do not modify benchmarks/cache_bench.py.

Working directory: {workdir}
