# ipb_dev_026: Set vs List Membership Test

## Overview

Performance benchmark task testing agent ability to diagnose and fix inefficient data structure choice for membership testing.

## Problem Description

The validation pipeline has regressed from ~0.015s to ~0.04s (2.7x slowdown). The bottleneck is in `validator/rules.py` where `check_constraints()` uses list iteration instead of set membership testing.

## Workspace Structure

```
workspace/
├── validator/
│   ├── __init__.py
│   └── rules.py           # PERFORMANCE BOTTLENECK HERE
├── benchmarks/
│   └── validation_bench.py # Performance test (threshold: 0.025s)
├── run_pipeline.py        # Interactive pipeline runner
├── generate_data.py       # Test data generation
├── test_data.json         # 200k records
└── profiling_data.txt     # cProfile evidence (variant: exact_evidence)
```

## Test Variants

### 1. exact_evidence
- Provides profiling data showing list iteration overhead
- System prompt explicitly mentions available evidence files
- Tests agent's ability to interpret profiling data and apply fix

### 2. fuzzy_context
- Minimal context: "validation pipeline taking longer than expected"
- No profiling data provided upfront
- Tests agent's investigation and diagnosis capabilities

## Ground Truth

**Bottleneck**: `check_constraints()` uses list iteration for membership testing

**Root Cause**: The refactored code replaced O(1) set membership (`if category in valid_categories`) with O(n) list iteration:
```python
# SLOW: O(n) for each check
valid_categories = ['alpha', 'beta', ...]  # list
for valid_cat in valid_categories:
    if category == valid_cat:
        category_valid = True
        break
```

With 200k records × 10 categories (worst case), this performs ~2M comparisons instead of 200k constant-time lookups.

**Solution**: Use set instead of list
```python
def check_constraints(records):
    """Check records satisfy business constraints.

    Args:
        records: List of record dictionaries

    Returns:
        Tuple of (pass_count, fail_count)
    """
    # Define valid categories as set for O(1) lookup
    valid_categories = {'alpha', 'beta', 'gamma', 'delta', 'epsilon',
                       'zeta', 'eta', 'theta', 'iota', 'kappa'}

    pass_count = 0
    fail_count = 0

    for record in records:
        # O(1) membership test
        if record['category'] in valid_categories:
            if 100 <= record['value'] <= 900:
                pass_count += 1
            else:
                fail_count += 1
        else:
            fail_count += 1

    return pass_count, fail_count
```

**Expected Outcome**: ~2.7x speedup (0.04s → 0.015s), benchmark passes

## Evaluation Criteria

1. **Performance**: `python3 benchmarks/validation_bench.py` exits 0 (best time ≤ 0.025s)
2. **Correctness**: Validation counts unchanged (same pass/fail results)
3. **Code Quality**: Fix targets root cause (data structure choice)

## Git History

- Commit 1 (baseline): Set-based membership test - FAST
- Commit 2 (regression): "refactor: improve constraint validation with detailed checking" - SLOW
- Commit 3: Add profiling evidence

The regression commit message is misleading (claims "improve" and "detailed" but degrades performance).

## Running Tests

```bash
cd tasks/ipb_dev_026/workspace

# Interactive pipeline with timing breakdown
python3 run_pipeline.py

# Performance benchmark
python3 benchmarks/validation_bench.py
```

## Success Indicators

Agent should:
1. Identify `rules.py:check_constraints()` as bottleneck (via profiling or code inspection)
2. Recognize O(n) list iteration replaced O(1) set membership
3. Convert `valid_categories` list back to set
4. Validate with benchmark showing best_time ≤ 0.025s
5. Verify correctness (same pass/fail counts)

## Notes

- Classic data structure anti-pattern: using list where set is appropriate
- Profiling data shows high time in `check_constraints()` function
- Git log provides narrative clue: regression introduced in "detailed checking" commit
- This tests fundamental understanding of Python data structure performance characteristics
- The misleading commit message tests whether agent measures actual behavior vs trusts claims

## ⚠ Misleading Variant Status

The misleading variant for this task is **ineffective**.
The anti-pattern is too obvious: experienced agents immediately find
the correct fix without following the misleading suggestion.
MisleadingGap = 0% in experiments (3/3 misleading runs all passed).

Superseded by ipb_dev_034 which uses the same regex-vs-builtin structure
as ipb_dev_027 (the only confirmed effective misleading task).
