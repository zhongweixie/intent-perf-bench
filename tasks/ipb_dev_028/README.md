# ipb_dev_028: List Membership Check Performance Regression

## Overview

Performance benchmark task testing agent ability to diagnose and fix O(n²) deduplication caused by linear search through a list instead of using a set for membership testing.

## Problem Description

The data merging pipeline hangs or takes extremely long (>10000s) due to nested loop in deduplication. The bottleneck is in `data_merger/merger.py` where `deduplicate_records()` iterates through `unique_records` list for each record to check for duplicates, creating O(n²) complexity.

## Workspace Structure

```
workspace/
├── data_merger/
│   ├── __init__.py
│   └── merger.py           # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── merge_bench.py      # Performance test (threshold: 0.25s)
├── generate_data.py        # Test data generation
├── run_pipeline.py         # Interactive pipeline runner
├── test_datasets.json      # 150k records with duplicates
└── profiling_data.txt      # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing O(n²) nested loop behavior
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "pipeline is extremely slow"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities with hung/timeout behavior

## Ground Truth

**Bottleneck**: `deduplicate_records()` uses nested loop with linear search

**Root Cause**: 
```python
for record in records:  # 150k iterations
    for existing in unique_records:  # grows to ~77k
        if existing['id'] == record_id:  # O(1) comparison
```
Total: ~11.25 billion comparisons

**Solution**: Set-based membership test
```python
seen_ids = set()
for record in records:
    if record['id'] not in seen_ids:  # O(1) lookup
        seen_ids.add(record['id'])
        unique_records.append(record)
```

**Expected Outcome**: >2000x speedup (from >10000s to ~0.02s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/merge_bench.py` exits 0 (best time ≤ 0.25s)
2. **Correctness**: Deduplicated count unchanged (77656 unique records)
3. **Code Quality**: Fix targets root cause, not symptoms

## Git History

- Commit 1 (904a79b): baseline implementation with set-based dedup - FAST
- Commit 2 (e78d9c2): **performance regression** - "use thorough duplicate detection for better accuracy" - EXTREMELY SLOW
- Commit 3 (f93eb9a): add profiling evidence

The regression commit message is intentionally misleading (claims "thorough" and "better accuracy").

## Running Tests

```bash
cd tasks/ipb_dev_028/workspace

# Interactive pipeline with timing breakdown (will hang on regressed version)
python3 run_pipeline.py

# Performance benchmark
python3 benchmarks/merge_bench.py
```

## Success Indicators

Agent should:
1. Identify `merger.py:deduplicate_records()` as bottleneck (via profiling, timeout behavior, or code inspection)
2. Recognize nested loop / list membership anti-pattern
3. Refactor to set-based membership test
4. Validate with benchmark showing best_time ≤ 0.25s
5. Verify correctness (unique count unchanged at 77656)

## Notes

- Profiling data intentionally shows massive function call count (500M+ calls) in nested loop
- The "thorough" duplicate detection is actually just inefficient - same correctness as set approach
- Tests agent's ability to recognize classic list vs set membership performance trap
- Extreme slowdown makes this highly observable even without profiling tools
