# ipb_dev_031: Log Level Regex Validation Anti-pattern

## Overview

Performance benchmark task testing agent ability to diagnose and fix unnecessary regex validation inside a counting loop.

## Problem Description

The log analysis pipeline has regressed from ~0.015s to ~0.042s (2.8x slowdown). The bottleneck is in `log_analyzer/analyzer.py` where `count_error_types()` runs a compiled regex match on every one of the 200k log entries to "validate" the level field before counting.

## Workspace Structure

```
workspace/
├── log_analyzer/
│   ├── __init__.py
│   └── analyzer.py         # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── log_bench.py        # Performance test (threshold: 0.025s)
├── run_pipeline.py         # Interactive pipeline runner
├── generate_data.py        # Test data generation
├── test_logs.txt           # 200k log lines
└── profiling_data.txt      # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### exact_evidence
Provides profiling data showing 200k `.match()` calls. Agent must recognize
regex validation is unnecessary for a fixed set of known strings.

### fuzzy_context
Minimal context only. Agent must investigate and diagnose independently.

**No misleading variant**: the frozenset replacement is immediately obvious
to any Python developer once they see the regex only tests membership in
5-6 fixed string literals. The correct fix is Python 101 knowledge — no
measurement required. See ipb_dev_027 for a successful Type B misleading task.

## Ground Truth

**Bottleneck**: `count_error_types()` uses `re.match()` per entry

**Root Cause**: The "robustness" validation compiles a regex and calls `.match()` on every entry. Since the log levels were already parsed from known values, this validation is redundant.

**Solution**: Remove regex, use direct dict counting
```python
counts = {}
for entry in log_entries:
    level = entry['level']
    counts[level] = counts.get(level, 0) + 1
return counts
```

## Git History

- Commit 1 (baseline): Direct dict accumulation - FAST
- Commit 2 (regression): "refactor: add regex validation for log level robustness" - SLOW
- Commit 3: Add profiling evidence
