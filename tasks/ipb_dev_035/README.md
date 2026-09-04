# ipb_dev_035: Pricing Engine iterrows Anti-pattern

## Overview

Performance benchmark task testing agent ability to diagnose and fix
`DataFrame.iterrows()` anti-pattern in a pricing calculation pipeline.

## Problem Description

The pricing engine has regressed from ~0.0005s to ~1.28s (2500x slowdown).
The bottleneck is in `pricing_engine/calculator.py` where `calculate_order_totals()`
was refactored to use `df.iterrows()` for "clearer business logic", creating a
full pandas `Series` object for every one of the 50k order rows.

## Workspace Structure

```
workspace/
├── pricing_engine/
│   ├── __init__.py
│   ├── loader.py          # JSON order loading
│   └── calculator.py      # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── pricing_bench.py   # Performance test (threshold: 0.20s)
├── generate_data.py        # Test data generation (50k orders)
├── run_pipeline.py         # Interactive pipeline runner
├── orders.json             # 50k order records
├── profiling_data.txt      # cProfile evidence
└── variants/               # System prompts per variant
```

## Test Variants

### fuzzy_context
Minimal context only. Agent must investigate and diagnose independently.

### exact_evidence
Points to profiling data showing 50k `iterrows()` calls dominating runtime.

### misleading ← key variant
Explicitly suggests `DataFrame.apply()` as the standard fix for `iterrows()`.
- `apply()` is the textbook recommendation for replacing iterrows
- Improvement: ~70%, from ~1.28s to ~0.38s — convincing
- But still **FAILS** threshold (0.20s) — apply is still row-by-row Python
- Real fix: vectorized column arithmetic, requires knowing pandas broadcasting

## Ground Truth

**Bottleneck**: `calculate_order_totals()` uses `df.iterrows()`

**Root Cause**: `iterrows()` creates a full `Series` per row — 50k Series
allocations with associated Python overhead. 9.4M function calls total.

**Misleading fix** (insufficient): Replace with `df.apply(row_fn, axis=1)`
→ ~0.38s, still FAILS 0.20s threshold

**Correct fix**: Vectorized pandas column operations
```python
subtotal       = df['base_price'] * df['quantity']
after_discount = subtotal * (1 - df['discount_rate'])
with_tax       = after_discount * (1 + df['tax_rate'])
final          = with_tax + df['handling_fee']
return final.tolist()
```

## Performance Profile

| State | Time | Result |
|-------|------|--------|
| Regression (iterrows) | ~1.28s | FAIL |
| Misleading fix (apply) | ~0.38s | FAIL (threshold: 0.20s, ~70% improvement) |
| Correct fix (vectorized) | ~0.0005s | PASS |

## Why This Works as a Misleading Task

`df.apply()` is the **universally recommended** replacement for `iterrows()` in
Python documentation, blog posts, and StackOverflow. Any developer who knows
"iterrows is slow" will immediately reach for `apply()`. The vectorized approach
requires knowing that even `apply(axis=1)` is still row-by-row Python execution,
and that true speedup requires eliminating the Python loop entirely via NumPy/pandas
column operations — this is non-obvious without measuring.

MisleadingGap target: fuzzy ~100%, misleading ~33% → Gap ~**+67%**

## Git History

- Commit 1 (HEAD = regression): "refactor: use row-by-row calculation for clarity"
