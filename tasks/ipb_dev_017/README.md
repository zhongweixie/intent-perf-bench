# ipb_dev_017: CSV Processing Repeated Filtering Performance

## Overview

Performance benchmark task testing agent ability to diagnose and fix repeated list comprehension filtering in CSV data aggregation.

## Problem Description

The CSV processing pipeline has regressed from ~0.20s to ~0.23s. The bottleneck is in `csv_processor/analyzer.py` where repeated list comprehension filtering over 100k records for each category/status creates unnecessary O(n×m) overhead instead of single-pass O(n) aggregation.

## Workspace Structure

```
workspace/
├── csv_processor/
│   ├── __init__.py
│   ├── parser.py          # CSV file parsing
│   ├── analyzer.py        # PERFORMANCE BOTTLENECK HERE
│   └── exporter.py        # JSON export
├── benchmarks/
│   └── csv_bench.py       # Performance test (threshold: 0.21s)
├── generate_data.py       # Test data generation (100k records)
├── run_pipeline.py        # Interactive pipeline runner
└── profiling_data.txt     # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing repeated filtering bottleneck
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "pipeline has become noticeably slower"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `analyze_data()` uses repeated list comprehension filtering

**Root Cause**: For each category/status value, the function filters the entire 100k record list:
```python
for cat in all_categories:
    category_counts[cat] = len([r for r in records if r.get('category') == cat])
```
This creates O(n×m) behavior where n=100k records, m=number of categories/statuses (~9 total).

**Solution**: Single-pass aggregation
```python
category_counts = {}
for record in records:
    cat = record.get('category', 'unknown')
    category_counts[cat] = category_counts.get(cat, 0) + 1
```

**Expected Outcome**: ~2x speedup in Stage 2 (0.075s → 0.034s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/csv_bench.py` exits 0 (best time ≤ 0.21s)
2. **Correctness**: Aggregation results unchanged (same counts, same avg_value)
3. **Code Quality**: Fix targets root cause, not symptoms

## Git History

- Commit 1 (baseline): Single-pass dict accumulation - FAST
- Commit 2 (regression): "refactor: use explicit filtering for each aggregation category" - SLOW
- Commit 3: Add profiling evidence

The regression commit message is intentionally misleading (claims "explicit filtering" improves clarity).

## Running Tests

```bash
cd tasks/ipb_dev_017/workspace

# Generate test data (if needed)
python3 generate_data.py

# Interactive pipeline with timing breakdown
python3 run_pipeline.py

# Performance benchmark
PYTHONPATH=. python3 benchmarks/csv_bench.py
```

## Success Indicators

Agent should:
1. Identify `analyzer.py` as bottleneck (via profiling, timing, or code inspection)
2. Recognize repeated list comprehension anti-pattern
3. Refactor to single-pass dictionary accumulation
4. Validate with benchmark showing best_time ≤ 0.21s
5. Verify correctness (aggregation results unchanged)

## Notes

- Profiling data shows 1.4M function calls (9 passes × ~155k calls per pass)
- Stage 2 timing jumps from 0.034s (baseline) to 0.075s (regressed) - 2.2x slower
- The "explicit filtering" approach looks cleaner but has hidden O(n×m) cost
- Tests agent's ability to recognize when "clearer" code is actually slower
