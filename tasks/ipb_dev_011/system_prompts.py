"""System prompts for ipb_dev_011 variants."""

PROMPTS = {
    "exact": """You are working in the provided workspace.

The payment risk analysis pipeline has a performance regression. Profiling data is in profiler_output.txt and git history in git.log.

== ENVIRONMENT ==
Python interpreter: python3

Run scripts:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/payment_bench.py

== REQUIREMENTS ==
- Preserve correctness.
- Do not modify benchmark scripts.
- Validate with the benchmark.
- Summarize: bottleneck, evidence, fix, validation.

Working directory: {workdir}
""",
    "fuzzy": """You are working in the provided workspace.

The payment risk analysis pipeline has become slower than before. Please investigate and fix.

== ENVIRONMENT ==
Python interpreter: python3

Run scripts:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/payment_bench.py

== REQUIREMENTS ==
- Preserve correctness.
- Do not modify benchmark scripts.
- Validate with the benchmark.
- Summarize: bottleneck, evidence, fix, validation.

Working directory: {workdir}
""",
    "misleading": """You are working in the provided workspace.

The payment risk analysis pipeline is slow. I noticed the payment processor API call takes about 0.09 seconds, which might be excessive for our throughput requirements.

== ENVIRONMENT ==
Python interpreter: python3

Run scripts:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/payment_bench.py

== REQUIREMENTS ==
- Preserve correctness.
- Do not modify benchmark scripts.
- Validate with the benchmark.
- Summarize: bottleneck, evidence, fix, validation.

Working directory: {workdir}
""",
    "target_known": """You are working in the provided workspace.

The payment risk analysis pipeline is slow. The issue is in payment/risk_scorer.py.

== ENVIRONMENT ==
Python interpreter: python3

Run scripts:
  cd {workdir} && python3 run_pipeline.py
  cd {workdir} && python3 benchmarks/payment_bench.py

== REQUIREMENTS ==
- Preserve correctness.
- Do not modify benchmark scripts.
- Validate with the benchmark.
- Summarize: bottleneck, evidence, fix, validation.

Working directory: {workdir}
"""
}
