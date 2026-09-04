# ipb_dev_029: JSON Deserialize Per Extraction

## Overview

Performance benchmark task testing agent ability to diagnose and fix unnecessary JSON serialize/deserialize operations inside a value extraction loop.

## Problem Description

The JSON processing pipeline has regressed from ~0.013s to ~0.42s (33x slowdown). The bottleneck is in `json_processor/parser.py` where each extraction call round-trips every object through `json.dumps()` + `json.loads()` unnecessarily.

## Workspace Structure

```
workspace/
├── json_processor/
│   ├── __init__.py
│   └── parser.py          # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── json_bench.py      # Performance test (threshold: 0.080s)
├── generate_data.py       # Test data generation
├── run_pipeline.py        # Interactive pipeline runner
├── test_data.jsonl        # 20k JSON lines
└── profiling_data.txt     # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing json.dumps/loads overhead
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "pipeline has become noticeably slower"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `extract_nested_values()` round-trips each object through JSON

**Root Cause**: The "mutation safety" copy is unnecessary - `dict.get()` traversal never mutates the source object:
```python
# SLOW: 60k JSON roundtrips for 3 calls × 20k objects
for obj in objects:
    safe_obj = json.loads(json.dumps(obj))  # UNNECESSARY copy
    value = safe_obj
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
```

**Solution**: Remove redundant serialization
```python
def extract_nested_values(objects, key_path):
    keys = key_path.split('.')
    results = []
    for obj in objects:
        value = obj
        for key in keys:
            value = value.get(key) if isinstance(value, dict) else None
            if value is None:
                break
        results.append(value)
    return results
```

**Expected Outcome**: ~33x speedup (0.42s → 0.013s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/json_bench.py` exits 0 (best time ≤ 0.080s)
2. **Correctness**: Extraction results unchanged (same values)
3. **Code Quality**: Fix targets root cause (remove unnecessary copy)

## Git History

- Commit 1 (baseline): Direct dict.get() traversal - FAST
- Commit 2 (regression): "refactor: re-serialize objects before extraction for mutation safety" - SLOW
- Commit 3: Add profiling evidence

The regression commit message is misleading (claims "mutation safety" but reading via get() never mutates).

## Running Tests

```bash
cd tasks/ipb_dev_029/workspace

# Interactive pipeline with timing breakdown
python3 run_pipeline.py

# Performance benchmark
python3 benchmarks/json_bench.py
```

## Success Indicators

Agent should:
1. Identify `parser.py:extract_nested_values()` as bottleneck (via profiling or code inspection)
2. Recognize unnecessary json.dumps/loads roundtrip
3. Remove the redundant copy operation
4. Validate with benchmark showing best_time ≤ 0.080s
5. Verify correctness (same extraction results)

## Notes

- Profiling data shows 60k json.dumps + 60k json.loads calls (3 calls × 20k objects)
- The json.loads/dumps pattern appears in both ipb_dev_024 and this task - different context
- This version: per-extraction call (all 3 extractions hit every object with serialize)
- Tests agent's ability to recognize when "defensive copying" is unnecessary overhead
