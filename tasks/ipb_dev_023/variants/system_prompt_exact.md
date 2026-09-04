You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, configuration and tests. You may run profiling,
tests and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with standard library)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/network_bench.py

== CONTEXT ==

The network analysis pipeline crashes with RecursionError when processing
large graph datasets. Error traces and profiling data are available in the
workspace.

Available evidence:
- profiling_data.txt: cProfile output showing recursive call patterns
- benchmarks/network_bench.py: performance benchmark with crash reproduction
- graph_data.json: test graph with 5000 nodes
- git log: recent commit history

== REQUIREMENTS ==

- Preserve observable correctness (component results must not change).
- Do not modify test files, benchmark scripts or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or crash cause;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
