# ipb_dev_019: Query Filter Index Unused Performance

## Overview

Performance benchmark task testing agent ability to diagnose and fix unused index optimization in query filtering.

## Problem Description

The query engine has a subtle performance regression from ~0.058s to ~0.072s (24% slowdown). The code builds indexes by category and status for O(1) lookup, but the refactored `apply_filters()` ignores them and scans all 50k records linearly for each query.

## Workspace Structure

```
workspace/
├── query_engine/
│   ├── __init__.py
│   ├── indexer.py         # Index building (correct)
│   ├── filters.py         # PERFORMANCE BOTTLENECK HERE
│   └── search.py          # Text search
├── benchmarks/
│   └── query_bench.py     # Performance test (threshold: 0.070s)
├── records.json           # 50k test records
├── generate_data.py       # Test data generation
├── run_pipeline.py        # Interactive pipeline runner
└── profiling_data.txt     # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing list comprehension scanning 1.6M records
- System prompt explicitly mentions available evidence files
- Tests agent's ability to recognize unused optimization

### 2. fuzzy_context
- Minimal context: "query engine has become noticeably slower"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `apply_filters()` extracts all records from index then filters linearly

**Root Cause**: The "simplified" refactor removes index-aware logic:
```python
# Before (FAST): use index lookup
if 'category' in filters:
    result = index['by_category'].get(filters['category'], [])

# After (SLOW): extract everything, then scan
if isinstance(records, dict) and 'by_id' in records:
    records = list(records['by_id'].values())  # All 50k records!
result = records
for key, value in filters.items():
    result = [r for r in result if r.get(key) == value]  # Linear scan
```

**Solution**: Restore index-aware filtering
```python
if isinstance(records, dict) and 'by_id' in records:
    index = records
    # Use index for first filter
    if 'category' in filters:
        result = index['by_category'].get(filters['category'], [])
    elif 'status' in filters:
        result = index['by_status'].get(filters['status'], [])
    else:
        result = list(index['by_id'].values())
    
    # Apply remaining filters to subset
    for key, value in filters.items():
        if key not in ['category', 'status']:
            result = [r for r in result if r.get(key) == value]
    return result
```

**Expected Outcome**: ~20% speedup (0.072s → 0.058s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/query_bench.py` exits 0 (best time ≤ 0.070s)
2. **Correctness**: Query results unchanged (same result counts)
3. **Code Quality**: Fix leverages existing index structure

## Git History

- Commit 1 (baseline): Index-aware filtering using by_category/by_status - FAST
- Commit 2 (regression): "refactor: simplify filter logic using direct list iteration for clarity" - SLOW
- Commit 3: Add profiling evidence

The regression commit message emphasizes "clarity" but removes the optimization.

## Running Tests

```bash
cd tasks/ipb_dev_019/workspace

# Interactive pipeline with timing breakdown
python3 run_pipeline.py

# Performance benchmark
PYTHONPATH=. python3 benchmarks/query_bench.py
```

## Success Indicators

Agent should:
1. Identify `filters.py` as bottleneck (via profiling, git diff, or code inspection)
2. Recognize that index is built but not used
3. Restore index-aware filtering logic
4. Validate with benchmark showing best_time ≤ 0.070s
5. Verify correctness (same query result counts)

## Notes

- Profiling shows 1.6M dict.get() calls scanning full 50k records repeatedly
- The index is correctly built in Stage 2 but ignored in Stage 3
- Classic "simplification" that removes important optimization
- Tests agent's ability to recognize when premature abstraction hurts performance
- Subtle regression: code still works correctly, just slower
- Requires understanding the purpose of the index structure
