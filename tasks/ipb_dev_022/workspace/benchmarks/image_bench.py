#!/usr/bin/env python3
"""Performance benchmark for image batch processing."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from image_processor import load_image_metadata, process_image_batch

# Performance threshold
THRESHOLD_SECONDS = 0.27
NUM_RUNS = 3


def run_benchmark():
    """Run image processing benchmark."""
    print("=" * 60)
    print("Image Processing Performance Benchmark")
    print("=" * 60)

    # Load test data once
    print("\nLoading test image data...")
    images = load_image_metadata('test_images.json')
    total_pixels = sum(len(img.get('pixels', [])) for img in images)
    print(f"Loaded {len(images)} images ({total_pixels:,} total pixels)")

    # Warm-up run
    print("\nWarm-up run...")
    _ = process_image_batch(images)

    # Timed runs
    print(f"\nRunning {NUM_RUNS} timed iterations...")
    times = []

    for i in range(NUM_RUNS):
        start = time.perf_counter()
        processed = process_image_batch(images)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i + 1}: {elapsed:.4f}s ({len(processed)} images processed)")

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
