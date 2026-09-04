You are working in the provided workspace to investigate and resolve a performance regression.

The customer analytics pipeline has become significantly slower. Available evidence:

1. **profiling_data.txt** — cProfile output showing function-level timing
2. **benchmarks/analytics_bench.py** — performance test (currently FAILING)
3. **git.log** — recent commit history

Address the performance issue by:
- Analyzing the profiling data to identify the bottleneck
- Investigating the relevant code modules
- Implementing an optimization that passes the benchmark
- Validating correctness and performance

Working directory: tasks/ipb_dev_014/workspace/
