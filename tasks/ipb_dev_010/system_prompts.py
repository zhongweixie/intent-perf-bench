"""System prompts for ipb_dev_010 variants."""

PROMPTS = {
    "exact": """You are working in the provided workspace.

The product recommendation pipeline has performance issues. Profiling data is in profiler_output.txt, git history in git.log.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/recommender_bench.py

== REQUIREMENTS ==

- Preserve observable correctness (output values must not change).
- Do not modify benchmark scripts.
- Validate using the benchmark.
- At completion, summarize: bottleneck found, evidence, fix applied, validation.

Working directory: {workdir}
""",

    "fuzzy": """You are working in the provided workspace.

The product recommendation pipeline is running much slower than before. Please investigate and fix.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/recommender_bench.py

== REQUIREMENTS ==

- Preserve observable correctness.
- Do not modify benchmark scripts.
- Validate using the benchmark.
- At completion, summarize: bottleneck found, evidence, fix applied, validation.

Working directory: {workdir}
""",

    "misleading": """You are working in the provided workspace.

The product recommendation pipeline is running slowly. The data loading step takes about 0.7 seconds to fetch product catalog and user preferences from the API — that seems like it might be the bottleneck.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/recommender_bench.py

== REQUIREMENTS ==

- Preserve observable correctness.
- Do not modify benchmark scripts.
- Validate using the benchmark.
- At completion, summarize: bottleneck found, evidence, fix applied, validation.

Working directory: {workdir}
""",

    "target_known": """You are working in the provided workspace.

The product recommendation pipeline is slow. I believe the issue is in recommender/scorer.py.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/recommender_bench.py

== REQUIREMENTS ==

- Preserve observable correctness.
- Do not modify benchmark scripts.
- Validate using the benchmark.
- At completion, summarize: bottleneck found, evidence, fix applied, validation.

Working directory: {workdir}
"""
}
