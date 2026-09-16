#!/usr/bin/env python3
"""Run validation pipeline with timing."""

import json
import time
from validator import validate_records, check_constraints


def run_pipeline():
    """Run validation pipeline with timing."""
    print("=" * 60)
    print("Validation Pipeline")
    print("=" * 60)

    # Stage 1: Load data
    print("\n[Stage 1] Loading test data...")
    start = time.perf_counter()
    with open('test_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(data)} records")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Validate records
    print("\n[Stage 2] Validating records...")
    start = time.perf_counter()
    valid = validate_records(data)
    stage2_time = time.perf_counter() - start
    print(f"  Valid records: {len(valid)}")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Check constraints
    print("\n[Stage 3] Checking constraints...")
    start = time.perf_counter()
    pass_count, fail_count = check_constraints(valid)
    stage3_time = time.perf_counter() - start
    print(f"  Passed: {pass_count}, Failed: {fail_count}")
    print(f"  Time: {stage3_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Stage 1 (Load):       {stage1_time:.4f}s")
    print(f"  Stage 2 (Validate):   {stage2_time:.4f}s")
    print(f"  Stage 3 (Constraints): {stage3_time:.4f}s")
    print(f"  Total:                {total_time:.4f}s")
    print("=" * 60)


if __name__ == '__main__':
    run_pipeline()
