# ipb_dev_024: JSON Redundant Serialization

## Overview

Performance benchmark task testing agent ability to diagnose and fix unnecessary JSON serialize/deserialize operations in a field extraction loop.

## Problem Description

The JSON processing pipeline has regressed from ~0.02s to ~0.29s (12x slowdown). The bottleneck is in `json_processor/parser.py` where each record is unnecessarily serialized to JSON and deserialized back just to extract a few fields.

## Workspace Structure

```
workspace/
├── json_processor/
│   ├── __init__.py
│   └── parser.py          # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── json_bench.py      # Performance test (threshold: 0.050s)
├── run_pipeline.py        # Interactive pipeline runner
├── generate_data.py       # Test data generation
├── test_data.json         # 50k records, ~11 MB
└── profiling_data.txt     # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing json.dumps/loads overhead
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "pipeline has become slower"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `extract_fields()` uses `json.dumps()` + `json.loads()` per record

**Root Cause**: Unnecessary serialization roundtrip for 50k records. Each record is converted to JSON string and parsed back just to extract fields, adding ~100k extra JSON operations.

**Solution**: Direct dictionary access
```python
def extract_fields(records, field_names):
    """Extract specified fields from records efficiently.

    Uses list comprehension for O(n) performance.

    Args:
        records: List of record dictionaries
        field_names: List of field names to extract

    Returns:
        List of dictionaries with only specified fields
    """
    return [
        {field: record.get(field) for field in field_names}
        for record in records
    ]
```

**Expected Outcome**: ~12x speedup (0.29s → 0.02s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/json_bench.py` exits 0 (best time ≤ 0.050s)
2. **Correctness**: Extraction results unchanged (same field values)
3. **Code Quality**: Fix targets root cause, not symptoms

## Git History

- Commit 1 (baseline): List comprehension with direct dict access - FAST
- Commit 2: Add path setup to benchmark script
- Commit 3 (regression): "refactor: use json serialize/deserialize for cleaner field isolation" - SLOW
- Commit 4: Add profiling evidence

The regression commit message is misleading (claims "cleaner isolation" but adds unnecessary work).

## Running Tests

```bash
cd tasks/ipb_dev_024/workspace

# Interactive pipeline with timing breakdown
python3 run_pipeline.py

# Performance benchmark
python3 benchmarks/json_bench.py
```

## Success Indicators

Agent should:
1. Identify `parser.py:extract_fields()` as bottleneck (via profiling or code inspection)
2. Recognize unnecessary json.dumps/loads operations
3. Refactor to direct dictionary field access
4. Validate with benchmark showing best_time ≤ 0.050s
5. Verify correctness (same extraction results)

## Notes

- Profiling data shows high `json.dumps` and `json.loads` cumulative time (50k calls each)
- Git log provides narrative clue: regression introduced in recent "refactor" commit
- The misleading commit message tests whether agent validates claims vs measures actual behavior
- This is a "doing unnecessary work" anti-pattern, not algorithmic complexity issue
