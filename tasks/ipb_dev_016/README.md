# ipb_dev_016: Report String Concatenation Performance Regression

## Overview

Performance benchmark task testing agent ability to diagnose and fix a string concatenation bottleneck in a report formatting pipeline.

## Problem Description

The report generation pipeline has regressed from ~0.02s to ~0.24s (12x slowdown) in the formatting stage. The bottleneck is in `report_generator/formatter.py` where iterative string concatenation (`result += line`) creates quadratic copying overhead.

## Workspace Structure

```
workspace/
├── report_generator/
│   ├── __init__.py
│   ├── data_source.py      # Sample data generation
│   ├── formatter.py        # PERFORMANCE BOTTLENECK HERE
│   └── writer.py           # File output
├── benchmarks/
│   └── report_bench.py     # Performance test (threshold: 0.20s)
├── run_generator.py        # Interactive pipeline runner
└── profiling_data.txt      # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing the bottleneck
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "pipeline has become noticeably slower"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `generate_report()` uses iterative `result += line` string concatenation

**Root Cause**: Each concatenation creates a full copy of the accumulated string, causing O(n²) behavior with 500k records

**Solution**: List accumulation approach
```python
# Collect all lines in list
lines = []
lines.append("=" * 80 + "\n")
lines.append("PERFORMANCE REPORT\n")
# ... more headers

for record in data:
    lines.append(format_line(record) + "\n")

# Single join at end
return ''.join(lines)
```

**Expected Outcome**: ~10x speedup (0.24s → 0.02s for formatting stage), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/report_bench.py` exits 0 (best time ≤ 0.20s)
2. **Correctness**: Report output unchanged (same content and format)
3. **Code Quality**: Fix targets root cause, not symptoms

## Git History

- Commit 1 (baseline): List accumulation + join approach - FAST
- Commit 2 (regression): "refactor: use incremental string building for clarity" - SLOW

The regression commit message is intentionally misleading (claims "clarity" improvement).

## Running Tests

```bash
cd tasks/ipb_dev_016/workspace

# Interactive pipeline with timing breakdown
python3 run_generator.py

# Performance benchmark
PYTHONPATH=. python3 benchmarks/report_bench.py
```

## Success Indicators

Agent should:
1. Identify `formatter.py` as bottleneck (via profiling, git history, or code inspection)
2. Recognize iterative string concatenation anti-pattern
3. Refactor to list accumulation + single join
4. Validate with benchmark showing best_time ≤ 0.20s
5. Verify correctness (report output unchanged)

## Notes

- Profiling data intentionally shows high time in `generate_report()`
- Git log provides narrative clue: regression introduced in recent "refactor" commit
- The misleading commit message tests whether agent validates claims vs measures actual behavior
- String concatenation is a well-known Python performance anti-pattern
