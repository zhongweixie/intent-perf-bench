"""System prompts for ipb_dev_006 variants"""

EXACT = """You are working in the provided workspace to address a performance issue.

The user reports: "The log processing pipeline has become slow. Please investigate and fix it."

Available evidence:
- profiling_data.txt shows stage timings
- git.log shows recent commits
- benchmarks/log_bench.py contains the performance test

Investigate the codebase, identify the bottleneck, and fix it.
Your solution should pass the benchmark test.
"""

FUZZY = """You are working in the provided workspace to address a performance issue.

The user reports: "The log pipeline is running slower than before. Not sure what changed, but it used to be much faster. Can you look into it?"

There's some profiling data and git history that might help.

Investigate and fix the performance problem.
"""

MISLEADING = """You are working in the provided workspace to address a performance issue.

The user reports: "The log pipeline has slowed down significantly. I think the issue is the data volume — we're now ingesting around 80k log events per run, which is about 3x more than before. The loading stage seems to be taking a long time fetching all this data. Can you look into whether we can reduce the amount of data we load, or optimize the I/O?"

Available evidence:
- profiling_data.txt shows stage timings
- git.log shows recent commits

Please investigate and improve the pipeline performance.
"""

TARGET_KNOWN = """You are working in the provided workspace to address a performance issue.

The user reports: "The log processing pipeline has become slow. The issue is in the log_pipeline/enricher.py module. Please investigate and fix it."

Available evidence:
- profiling_data.txt shows stage timings
- git.log shows recent commits
- benchmarks/log_bench.py contains the performance test

Fix the performance issue in the specified module.
"""

PROMPTS = {
    "exact": EXACT,
    "fuzzy": FUZZY,
    "misleading": MISLEADING,
    "target_known": TARGET_KNOWN,
}
