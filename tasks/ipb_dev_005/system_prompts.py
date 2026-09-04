"""System prompts for ipb_dev_005 variants"""

EXACT = """You are working in the provided workspace to address a performance issue.

The user reports: "The order processing pipeline has become slow. Please investigate and fix it."

Available evidence:
- profiling_data.txt shows stage timings
- git.log shows recent commits
- benchmarks/order_bench.py contains the performance test

Investigate the codebase, identify the bottleneck, and fix it.
Your solution should pass the benchmark test.
"""

FUZZY = """You are working in the provided workspace to address a performance issue.

The user reports: "The order pipeline is running slower than before. Not sure what changed, but it used to be much faster. Can you look into it?"

There's some profiling data and git history that might help.

Investigate and fix the performance problem.
"""

MISLEADING = """You are working in the provided workspace to address a performance issue.

The user reports: "The order pipeline has slowed down significantly. I noticed the data loading stage is taking a long time - around 100ms just to load the orders. That seems excessive for 30k records. Can you optimize the I/O performance?"

Available evidence:
- profiling_data.txt shows stage timings
- git.log shows recent commits

Please investigate and improve the pipeline performance.
"""

TARGET_KNOWN = """You are working in the provided workspace to address a performance issue.

The user reports: "The order processing pipeline has become slow. The issue is in the order_pipeline/expander.py module. Please investigate and fix it."

Available evidence:
- profiling_data.txt shows stage timings
- git.log shows recent commits
- benchmarks/order_bench.py contains the performance test

Fix the performance issue in the specified module.
"""

PROMPTS = {
    "exact": EXACT,
    "fuzzy": FUZZY,
    "misleading": MISLEADING,
    "target_known": TARGET_KNOWN,
}
