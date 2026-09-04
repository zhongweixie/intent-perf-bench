# ipb_dev_027: Regex Overkill Anti-pattern

## Overview

Performance benchmark task testing agent ability to diagnose and fix unnecessary regex usage for simple string matching operations.

## Problem Description

The text processing pipeline has regressed from ~0.07s to ~0.23s (3x slowdown). The bottleneck is in `text_processor/analyzer.py` where `count_patterns()` uses `re.findall()` for literal string matching when simple `str.count()` would suffice.

## Workspace Structure

```
workspace/
├── text_processor/
│   ├── __init__.py
│   └── analyzer.py        # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── text_bench.py      # Performance test (threshold: 0.080s)
├── run_pipeline.py        # Interactive pipeline runner
├── generate_data.py       # Test data generation
├── text_data.json         # 50k text entries
└── profiling_data.txt     # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing regex compilation overhead
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "text processing pipeline taking much longer than before"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `count_patterns()` uses regex for literal string matching

**Root Cause**: The refactored code uses `re.findall()` to match literal patterns, which involves:
- Regex compilation (or cache lookup) for each pattern × text combination
- Complex regex matching engine for simple literal string search

```python
# SLOW: regex overkill for literal strings
import re
for text in texts:
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        counts[pattern] += len(matches)
```

With 50k texts × 5 patterns = 250k regex operations, this adds significant overhead compared to simple string scanning.

**Solution**: Use str.count() for literal matching
```python
def count_patterns(texts, patterns):
    """Count occurrences of patterns in texts efficiently.

    Args:
        texts: List of text strings
        patterns: List of pattern strings to search for

    Returns:
        Dictionary mapping pattern to count
    """
    counts = {pattern: 0 for pattern in patterns}

    for text in texts:
        text_lower = text.lower()
        for pattern in patterns:
            counts[pattern] += text_lower.count(pattern.lower())

    return counts
```

**Expected Outcome**: ~3x speedup (0.23s → 0.07s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/text_bench.py` exits 0 (best time ≤ 0.080s)
2. **Correctness**: Pattern counts unchanged (same match results)
3. **Code Quality**: Fix targets root cause (appropriate tool selection)

## Git History

- Commit 1 (baseline): str.count() for literal matching - FAST
- Commit 2 (regression): "refactor: use regex for more flexible pattern matching" - SLOW
- Commit 3: Add profiling evidence

The regression commit message is misleading (claims "flexible" but patterns are literals, adding unnecessary complexity).

## Running Tests

```bash
cd tasks/ipb_dev_027/workspace

# Interactive pipeline with timing breakdown
python3 run_pipeline.py

# Performance benchmark
python3 benchmarks/text_bench.py
```

## Success Indicators

Agent should:
1. Identify `analyzer.py:count_patterns()` as bottleneck (via profiling or code inspection)
2. Recognize regex is overkill for literal string matching
3. Replace re.findall() with str.count()
4. Validate with benchmark showing best_time ≤ 0.080s
5. Verify correctness (same pattern counts)

## Notes

- Classic anti-pattern: using regex when simpler string operations suffice
- Profiling data shows high cumulative time in re.findall() and re._compile()
- Git log provides narrative clue: regression introduced in "flexible pattern matching" commit
- The misleading commit message tests whether agent validates claims vs measures actual behavior
- Tests understanding of when regex overhead is justified vs when it's wasteful
