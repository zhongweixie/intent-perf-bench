#!/usr/bin/env python3
"""Run CSV validation pipeline with timing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from csv_validator import load_csv_fields, validate_fields


def run_pipeline():
    print("=" * 60)
    print("CSV Validation Pipeline")
    print("=" * 60)

    print("\n[Stage 1] Loading field data...")
    start = time.perf_counter()
    fields = load_csv_fields('test_fields.json')
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(fields):,} fields")
    print(f"  Time: {stage1_time:.4f}s")

    print("\n[Stage 2] Validating fields...")
    start = time.perf_counter()
    results = validate_fields(fields)
    stage2_time = time.perf_counter() - start
    numeric = sum(results)
    print(f"  Numeric fields: {numeric:,} ({numeric/len(results)*100:.1f}%)")
    print(f"  Time: {stage2_time:.4f}s")

    total_time = stage1_time + stage2_time
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Stage 1 (Load):     {stage1_time:.4f}s")
    print(f"  Stage 2 (Validate): {stage2_time:.4f}s")
    print(f"  Total:              {total_time:.4f}s")


if __name__ == '__main__':
    run_pipeline()
