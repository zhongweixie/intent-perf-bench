# ipb_dev_018: JSON Deduplication Nested Loop Performance

## Overview

Performance benchmark task testing agent ability to diagnose and fix O(n²) nested loop deduplication in JSON record processing.

## Problem Description

The JSON processing pipeline has regressed from ~0.07s to ~8.4s (120x slowdown). The bottleneck is in `json_processor/merger.py` where nested loop deduplication scans the growing unique list for each of 20k records, creating O(n²) behavior instead of O(n) dict-based deduplication.

## Workspace Structure

```
workspace/
├── json_processor/
│   ├── __init__.py
│   ├── loader.py          # JSON file loading
│   ├── merger.py          # PERFORMANCE BOTTLENECK HERE
│   └── validator.py       # Schema validation
├── benchmarks/
│   └── json_bench.py      # Performance test (threshold: 0.40s)
├── json_data/             # 200 JSON files, 100 records each
├── generate_data.py       # Test data generation
├── run_pipeline.py        # Interactive pipeline runner
└── profiling_data.txt     # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing 200M+ function calls in nested loop
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "pipeline has become noticeably slower"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `merge_records()` uses nested loop to check for duplicate IDs

**Root Cause**: For each of 20k records, scans the growing unique list:
```python
for record in records:
    for existing in unique:
        if existing.get('id') == record_id:
            ...
```
This creates O(n²) behavior: first record scans 0 items, second scans 1, ..., 20000th scans 19999.
Total comparisons: ~200 million.

**Solution**: Dict-based O(n) deduplication
```python
unique = {}
for record in records:
    record_id = record.get('id')
    if record_id is not None:
        unique[record_id] = record
return list(unique.values())
```

**Expected Outcome**: ~4600x speedup in Stage 3 (8.4s → 0.002s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/json_bench.py` exits 0 (best time ≤ 0.40s)
2. **Correctness**: Deduplication results unchanged (same unique record count)
3. **Code Quality**: Fix targets root cause, not symptoms

## Git History

- Commit 1 (baseline): Dict-based O(n) deduplication - FAST
- Commit 2 (regression): "refactor: use explicit list comparison for deduplication clarity" - SLOW
- Commit 3: Add profiling evidence

The regression commit message is intentionally misleading (claims "clarity" improvement).

## Running Tests

```bash
cd tasks/ipb_dev_018/workspace

# Generate test data (already done)
python3 generate_data.py

# Interactive pipeline with timing breakdown
python3 run_pipeline.py

# Performance benchmark
PYTHONPATH=. python3 benchmarks/json_bench.py
```

## Success Indicators

Agent should:
1. Identify `merger.py` as bottleneck (via profiling, timing, or code inspection)
2. Recognize nested loop O(n²) anti-pattern
3. Refactor to dict-based O(n) deduplication
4. Validate with benchmark showing best_time ≤ 0.40s
5. Verify correctness (same unique count)

## Notes

- Profiling shows 200M+ function calls (20k records × ~10k average comparisons)
- Stage 3 timing jumps from 0.002s (baseline) to 8.4s (regressed) - 4200x slower
- The "explicit comparison" looks clearer but has catastrophic O(n²) cost
- Classic example where "readable" code hides algorithmic complexity
- Tests agent's ability to recognize when loop nesting creates quadratic behavior
