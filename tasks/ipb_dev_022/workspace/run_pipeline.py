#!/usr/bin/env python3
"""Image batch processing pipeline runner."""

import time
from image_processor import load_image_metadata, process_image_batch, save_processed_images


def run_pipeline(input_file='test_images.json', output_file='processed_images.json'):
    """Run image processing pipeline with timing."""
    print("=" * 60)
    print("Image Processing Pipeline")
    print("=" * 60)

    # Stage 1: Load image metadata
    print("\n[Stage 1] Loading image metadata...")
    start = time.perf_counter()
    images = load_image_metadata(input_file)
    stage1_time = time.perf_counter() - start
    print(f"  Loaded {len(images)} images")
    total_pixels = sum(len(img.get('pixels', [])) for img in images)
    print(f"  Total pixels: {total_pixels:,}")
    print(f"  Time: {stage1_time:.4f}s")

    # Stage 2: Process batch (brightness + contrast + histogram)
    print("\n[Stage 2] Processing image batch...")
    start = time.perf_counter()
    processed = process_image_batch(images)
    stage2_time = time.perf_counter() - start
    print(f"  Processed {len(processed)} images")
    print(f"  Applied transformations and computed histograms")
    print(f"  Time: {stage2_time:.4f}s")

    # Stage 3: Save results
    print("\n[Stage 3] Saving processed images...")
    start = time.perf_counter()
    save_processed_images(processed, output_file)
    stage3_time = time.perf_counter() - start
    print(f"  Saved {len(processed)} images to {output_file}")
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
