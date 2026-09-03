You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, configuration and tests. You may run profiling,
tests and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with standard library)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/text_bench.py

== CONTEXT ==

The text processing pipeline has become noticeably slower than before.

Initial investigation suggests the performance issue might be related to I/O operations. When processing large text datasets, the file reading or data parsing stages could be introducing latency. There might be inefficient buffering or unnecessary file operations.

Available evidence:
- profiling_data.txt: cProfile output showing function-level timings
- run_pipeline.py: pipeline runner showing stage-by-stage timing breakdown

== REQUIREMENTS ==

- Preserve observable correctness (pattern counts and keywords must not change).
- Do not modify test files, benchmark scripts or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
