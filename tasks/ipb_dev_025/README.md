# ipb_dev_025: Redundant Set Membership Check

## Overview

Performance benchmark task testing agent ability to diagnose and fix redundant set membership checks in a grouping operation.

## Problem Description

The data processing pipeline has regressed from ~0.03s to ~0.06s (2x slowdown). The bottleneck is in `data_processor/transformer.py` where `compute_statistics()` performs redundant category membership checks inside the nested loop.

## Workspace Structure

```
workspace/
├── data_processor/
│   ├── __init__.py
│   └── transformer.py     # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── data_bench.py      # Performance test (threshold: 0.040s)
├── run_pipeline.py        # Interactive pipeline runner
├── generate_data.py       # Test data generation
├── test_data.json         # 100k records
└── profiling_data.txt     # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing nested loop overhead
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "pipeline not meeting performance targets"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `compute_statistics()` has redundant set membership check

**Root Cause**: Inside the nested loop, code checks `if record['category'] in categories and record['category'] == category`. The `in categories` check is redundant because:
1. All categories in the set come from the data itself
2. The equality check `record['category'] == category` is sufficient
3. This adds 50k × 10 = 500k unnecessary set lookups

**Solution**: Remove redundant check
```python
def compute_statistics(data):
    """Compute summary statistics efficiently using set operations.

    Args:
        data: List of dictionaries with 'category' and 'value' fields

    Returns:
        Dictionary with category statistics
    """
    # Efficient set-based approach
    categories = {record['category'] for record in data}

    stats = {}
    for category in categories:
        category_records = [r for r in data if r['category'] == category]
        values = [r['value'] for r in category_records]

        stats[category] = {
            'count': len(category_records),
            'sum': sum(values),
            'avg': sum(values) / len(values) if values else 0,
            'min': min(values) if values else 0,
            'max': max(values) if values else 0
        }

    return stats
```

**Expected Outcome**: ~2x speedup (0.06s → 0.03s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/data_bench.py` exits 0 (best time ≤ 0.040s)
2. **Correctness**: Statistics results unchanged (same counts, sums, averages)
3. **Code Quality**: Fix targets root cause, not symptoms

## Git History

- Commit 1 (baseline): Simple set-based grouping - FAST
- Commit 2 (regression): "refactor: add explicit category validation for robustness" - SLOW
- Commit 3: Add profiling evidence

The regression commit message is misleading (claims "robustness" but adds unnecessary work).

## Running Tests

```bash
cd tasks/ipb_dev_025/workspace

# Interactive pipeline with timing breakdown
python3 run_pipeline.py

# Performance benchmark
python3 benchmarks/data_bench.py
```

## Success Indicators

Agent should:
1. Identify `transformer.py:compute_statistics()` as bottleneck (via profiling or code inspection)
2. Recognize redundant `in categories` check before equality comparison
3. Remove unnecessary membership test
4. Validate with benchmark showing best_time ≤ 0.040s
5. Verify correctness (same statistics results)

## Notes

- Profiling data shows high cumulative time in `compute_statistics()` function
- The redundant check pattern: `if x in set and x == value` where the equality is sufficient
- Git log provides narrative clue: regression introduced in "validation" commit
- This tests whether agent can identify micro-optimizations in set operations
- The misleading commit message tests whether agent validates "robustness" claims
