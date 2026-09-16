#!/usr/bin/env python3
"""Interactive report generator with timing breakdown."""

import time
from report_generator import generate_sample_data, generate_report, write_report

def main():
    """Run report generation pipeline with timing."""
    print("=" * 60)
    print("Report Generation Pipeline")
    print("=" * 60)

    # Stage 1: Data generation
    print("\n[Stage 1] Generating sample data...")
    start = time.perf_counter()
    data = generate_sample_data(num_records=500000)
    stage1_time = time.perf_counter() - start
    print(f"  Generated {len(data)} records")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Report formatting
    print("\n[Stage 2] Formatting report...")
    start = time.perf_counter()
    report = generate_report(data)
    stage2_time = time.perf_counter() - start
    print(f"  Report length: {len(report)} characters")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Write output
    print("\n[Stage 3] Writing to file...")
    start = time.perf_counter()
    output_path = write_report(report, 'sample_report.txt')
    stage3_time = time.perf_counter() - start
    print(f"  Written to: {output_path}")
    print(f"  Time: {stage3_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("TIMING SUMMARY")
    print("=" * 60)
    print(f"Stage 1 (Data):       {stage1_time:7.4f}s ({stage1_time/total_time*100:5.1f}%)")
    print(f"Stage 2 (Format):     {stage2_time:7.4f}s ({stage2_time/total_time*100:5.1f}%)")
    print(f"Stage 3 (Write):      {stage3_time:7.4f}s ({stage3_time/total_time*100:5.1f}%)")
    print(f"{'─' * 60}")
    print(f"Total:                {total_time:7.4f}s")
    print()

if __name__ == '__main__':
    main()
