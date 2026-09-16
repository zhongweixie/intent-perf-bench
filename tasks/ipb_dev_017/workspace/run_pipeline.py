#!/usr/bin/env python3
"""Interactive CSV processing pipeline with timing."""

import time
from csv_processor import parse_csv_file, analyze_data, export_results


def run_pipeline():
    """Run CSV processing pipeline with timing breakdown."""
    print("=" * 60)
    print("CSV Processing Pipeline")
    print("=" * 60)

    # Stage 1: Parse CSV
    print("\n[Stage 1] Parsing CSV file...")
    start = time.perf_counter()
    records = parse_csv_file('sample_data.csv')
    stage1_time = time.perf_counter() - start
    print(f"  Parsed {len(records)} records")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Analyze data
    print("\n[Stage 2] Analyzing data...")
    start = time.perf_counter()
    analysis = analyze_data(records)
    stage2_time = time.perf_counter() - start
    print(f"  Total records: {analysis['total']}")
    print(f"  Categories: {len(analysis['by_category'])}")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Export results
    print("\n[Stage 3] Exporting results...")
    start = time.perf_counter()
    export_results(analysis, 'analysis_results.json')
    stage3_time = time.perf_counter() - start
    print(f"  Written to: analysis_results.json")
    print(f"  Time: {stage3_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("TIMING SUMMARY")
    print("=" * 60)
    print(f"Stage 1 (Parse):       {stage1_time:.4f}s ({stage1_time/total_time*100:5.1f}%)")
    print(f"Stage 2 (Analyze):     {stage2_time:.4f}s ({stage2_time/total_time*100:5.1f}%)")
    print(f"Stage 3 (Export):      {stage3_time:.4f}s ({stage3_time/total_time*100:5.1f}%)")
    print("─" * 60)
    print(f"Total:                 {total_time:.4f}s")


if __name__ == '__main__':
    run_pipeline()
