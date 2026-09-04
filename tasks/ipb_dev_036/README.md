# ipb_dev_036: Order Analytics concat-in-loop Anti-pattern (Type A)

## Overview

Type A misleading task. The pipeline has two stages; the misleading prompt
points to Stage 1 (data loading) as the bottleneck, while the real regression
is in Stage 2 (per-user report building with pd.concat in a loop).

## Problem Description

The order analytics pipeline has regressed from ~0.01s to ~7.8s in Stage 2.
The bottleneck is in `order_analytics/reporter.py` where `build_user_report()`
iterates over 1000 users, filters 200k rows per user with a boolean scan, and
accumulates results with `pd.concat` inside the loop — producing both O(n²)
copy overhead and O(n×k) scan overhead.

## Workspace Structure

```
workspace/
├── order_analytics/
│   ├── __init__.py
│   ├── loader.py          # JSON loading (Stage 1, ~0.15s)
│   └── reporter.py        # PERFORMANCE BOTTLENECK HERE (Stage 2)
├── benchmarks/
│   └── analytics_bench.py # Performance test (threshold: 0.25s)
├── generate_data.py        # Test data generation (200k orders, 1000 users)
├── run_pipeline.py         # Pipeline runner showing stage timing
├── orders.json             # 200k order records
├── profiling_data.txt      # cProfile evidence
└── variants/               # System prompts per variant
```

## Test Variants

### fuzzy_context
Minimal context only.

### exact_evidence
Points to profiling data showing per-user boolean scan (1000 × 200k rows).

### misleading ← key variant
Tells the agent that **Stage 1 (data loading) is slow** — the JSON file has
grown and loading time "appears to be a significant fraction" of total runtime.
This is plausible: Stage 1 takes ~0.15s (real, not fabricated).

Agent trajectory under misleading:
1. Looks at loader.py → json.load is already optimal → can't improve much
2. Checks Stage 2 → sees concat-in-loop
3. Common first fix: replace pd.concat with list + pd.DataFrame → ~47% improvement, still **FAILS** (threshold 0.25s)
4. Must keep searching → finds groupby.agg → **PASS**

Fuzzy agent skips Step 1, finds Stage 2 faster → higher pass rate.

## Performance Profile

| State | Stage 2 | Pipeline Total | Result |
|-------|---------|----------------|--------|
| Regression (concat-in-loop) | ~7.8s | ~8.0s | FAIL |
| Misleading fix (list+DataFrame) | ~0.40s | ~0.55s | FAIL (threshold: 0.25s) |
| Correct fix (groupby+agg) | ~0.009s | ~0.16s | PASS |

## Why This Works as a Misleading Task

**Type A mechanism**: The agent is sent to look at the wrong module (Stage 1
loader) first. Stage 1 is genuinely ~0.15s — not fabricated — so the suspicion
is plausible. But json.load is already near-optimal for 200k records; there is
nothing meaningful to optimize there.

After wasting turns on Stage 1, the agent finds Stage 2's concat-in-loop.
The natural first fix ("avoid pd.concat by collecting into a list") improves
Stage 2 by ~47% — convincing — but the pipeline still fails at 0.55s vs 0.25s
threshold. Only `groupby().agg()` gets the pipeline below threshold.

MisleadingGap target: fuzzy ~100%, misleading ~33% → Gap ~**+67%**

## Git History

- Commit 1 (HEAD = regression): initial implementation with concat-in-loop
