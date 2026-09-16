#!/usr/bin/env python3
"""Performance benchmark for report generation."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from report_generator import generate_sample_data, generate_report

# Performance threshold
THRESHOLD_SECONDS = 0.20
NUM_RUNS = 3

def run_benchmark():
    """Run report generation benchmark."""
    print("=" * 60)
    print("Report Generation Performance Benchmark")
    print("=" * 60)

    # Generate test data once
    print("\nGenerating test data...")
    data = generate_sample_data(num_records=500000)
    print(f"Generated {len(data)} records")

    # Warm-up run
    print("\nWarm-up run...")
    _ = generate_report(data)

    # Timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []

    for i in range(NUM_RUNS):
        start = time.perf_counter()
        report = generate_report(data)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.4f}s")

    # Results
    best_time = min(times)
    avg_time = sum(times) / len(times)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Best time:    {best_time:.4f}s")
    print(f"Average time: {avg_time:.4f}s")
    print(f"Threshold:    {THRESHOLD_SECONDS:.4f}s")
    print()

    if best_time <= THRESHOLD_SECONDS:
        print("✓ PASS: Performance within threshold")
        return 0
    else:
        print(f"✗ FAIL: Performance exceeds threshold by {best_time - THRESHOLD_SECONDS:.4f}s")
        return 1

if __name__ == '__main__':
    exit(run_benchmark())
