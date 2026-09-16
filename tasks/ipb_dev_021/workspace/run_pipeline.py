#!/usr/bin/env python3
"""Batch processing pipeline runner."""

import time
from data_processor import load_records, process_batch, save_results


def run_pipeline(input_file='test_data.json', output_file='processed_data.json'):
    """Run batch processing pipeline with timing."""
    print("=" * 60)
    print("Batch Processing Pipeline")
    print("=" * 60)

    # Stage 1: Load data
    print("\n[Stage 1] Loading data...")
    start = time.perf_counter()
    records = load_records(input_file)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(records)} records")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Process batch (normalize + deduplicate)
    print("\n[Stage 2] Processing batch...")
    start = time.perf_counter()
    processed = process_batch(records)
    stage2_time = time.perf_counter() - start
    print(f"  Processed {len(records)} records")
    print(f"  Deduplicated to {len(processed)} unique records")
    print(f"  Removed {len(records) - len(processed)} duplicates")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Save results
    print("\n[Stage 3] Saving results...")
    start = time.perf_counter()
    save_results(processed, output_file)
    stage3_time = time.perf_counter() - start
    print(f"  Saved {len(processed)} records to {output_file}")
    print(f"  Time: {stage3_time:.4f}s")

    # Summary
    total_time = stage1_time + stage2_time + stage3_time
    print("\n" + "=" * 60)
    print("TIMING SUMMARY")
    print("=" * 60)
    print(f"Stage 1 (Load):        {stage1_time:.4f}s ({100*stage1_time/total_time:5.1f}%)")
    print(f"Stage 2 (Process):     {stage2_time:.4f}s ({100*stage2_time/total_time:5.1f}%)")
    print(f"Stage 3 (Save):        {stage3_time:.4f}s ({100*stage3_time/total_time:5.1f}%)")
    print("─" * 60)
    print(f"Total:                 {total_time:.4f}s")


if __name__ == '__main__':
    run_pipeline()
