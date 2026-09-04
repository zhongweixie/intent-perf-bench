# ipb_dev_021: Batch Deduplication Performance Regression

## Overview

Performance benchmark task testing agent ability to diagnose and fix O(n²) deduplication in batch processing.

## Problem Description

The batch processing pipeline has regressed from ~0.01s to ~4.8s (480x slowdown) when processing 5000 records. The bottleneck is in `data_processor/batch_ops.py` where deduplication checks each record against all previously deduplicated records.

## Workspace Structure

```
workspace/
├── data_processor/
│   ├── __init__.py
│   └── batch_ops.py        # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── batch_bench.py      # Performance test (threshold: 0.08s)
├── generate_data.py        # Test data generation
├── run_pipeline.py         # Interactive pipeline runner
└── profiling_data.txt      # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing O(n²) behavior
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "batch processing has become slow"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `process_batch()` uses nested loop for deduplication

**Root Cause**: For each record, iterates through all previously deduplicated records calling `compute_hash()`, causing O(n²) behavior with ~10M function calls for 5000 records

**Solution**: Set-based membership test
```python
# Use set to track seen hashes
seen = set()
deduplicated = []

for record in normalized:
    record_hash = compute_hash(record)
    if record_hash not in seen:  # O(1) lookup instead of O(n)
        seen.add(record_hash)
        deduplicated.append(record)
```

**Expected Outcome**: ~60x speedup (4.8s → 0.01s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/batch_bench.py` exits 0 (best time ≤ 0.08s)
2. **Correctness**: Deduplication results unchanged (same 4250 unique records)
3. **Code Quality**: Fix targets root cause, not symptoms

## Git History

- Commit 1 (baseline): Set-based deduplication - FAST
- Commit 2 (regression): "refactor: improve deduplication clarity" - SLOW
- Commit 3: Add profiling evidence

The regression commit message is misleading (claims "clarity" improvement).

## Running Tests

```bash
cd tasks/ipb_dev_021/workspace

# Interactive pipeline with timing breakdown
python3 run_pipeline.py

# Performance benchmark
python3 benchmarks/batch_bench.py
```

## Success Indicators

Agent should:
1. Identify `batch_ops.py:process_batch()` as bottleneck
2. Recognize O(n²) nested loop anti-pattern
3. Refactor to set-based deduplication for O(n) lookup
4. Validate with benchmark showing best_time ≤ 0.08s
5. Verify correctness (same deduplication results)

## Notes

- Profiling shows 10M+ calls to `compute_hash()` for 5000 records
- Git log provides clue: regression in recent "refactor" commit
- Classic algorithmic complexity issue: O(n²) vs O(n) with proper data structure
