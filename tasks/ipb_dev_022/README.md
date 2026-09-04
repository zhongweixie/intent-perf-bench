# ipb_dev_022: Image Transform Double-Pass Performance Regression

## Overview

Performance benchmark task testing agent ability to diagnose and fix unnecessary double-pass iteration in image transformation pipeline.

## Problem Description

The image processing pipeline has regressed from ~0.25s to ~0.30s (20% slowdown). The bottleneck is in `image_processor/transforms.py` where brightness and contrast transformations are applied in two separate `map()` passes, creating an unnecessary intermediate list and doubling the iteration overhead.

## Workspace Structure

```
workspace/
├── image_processor/
│   ├── __init__.py
│   └── transforms.py        # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── image_bench.py       # Performance test (threshold: 0.28s)
├── generate_data.py         # Test data generation
├── run_pipeline.py          # Interactive pipeline runner
└── profiling_data.txt       # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing double iteration with lambda overhead
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "image processing has become slower"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `process_image_batch()` uses two separate `map()` calls

**Root Cause**: Brightness applied in first pass creating intermediate list, then contrast applied in second pass iterating again. Each transformation requires 500k function calls + lambda overhead + intermediate list allocation.

**Solution**: Single-pass list comprehension
```python
# Combine transformations in single pass
adjusted_pixels = [
    apply_contrast_adjustment(
        apply_brightness_adjustment(p, brightness_factor),
        contrast_factor
    )
    for p in pixels
]
```

**Expected Outcome**: ~15% speedup (0.30s → 0.25s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/image_bench.py` exits 0 (best time ≤ 0.28s)
2. **Correctness**: Transformation results unchanged (same adjusted pixels, histograms)
3. **Code Quality**: Fix targets root cause, not symptoms

## Git History

- Commit 1 (baseline): Single-pass list comprehension - FAST
- Commit 2: Adjust test data size
- Commit 3 (regression): "refactor: separate brightness and contrast passes" - SLOW
- Commit 4: Add profiling evidence

The regression commit message claims "better modularity" but sacrifices performance.

## Running Tests

```bash
cd tasks/ipb_dev_022/workspace

# Interactive pipeline with timing breakdown
python3 run_pipeline.py

# Performance benchmark
python3 benchmarks/image_bench.py
```

## Success Indicators

Agent should:
1. Identify `transforms.py:process_image_batch()` as bottleneck
2. Recognize double-pass iteration anti-pattern
3. Refactor to single-pass list comprehension
4. Validate with benchmark showing best_time ≤ 0.28s
5. Verify correctness (same transformation results)

## Notes

- Profiling shows 500k calls each to brightness and contrast lambdas
- Each `map()` creates intermediate list iterator overhead
- Classic optimization: eliminate unnecessary passes through large datasets
- Git log provides clue: regression in "modularity" refactor
