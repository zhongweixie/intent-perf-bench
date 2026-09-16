"""Performance Benchmark for Order Processing Pipeline"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from run_pipeline import run_order_pipeline


def benchmark_pipeline(n_runs: int = 3):
    """Run pipeline benchmark."""
    print("=" * 70)
    print("Order Pipeline Performance Benchmark")
    print("=" * 70)
    print(f"\nConfiguration: 30,000 orders, {n_runs} runs\n")

    times = []
    for i in range(n_runs):
        print(f"--- Run {i+1}/{n_runs} ---")
        elapsed = run_order_pipeline()
        times.append(elapsed)
        print(f"Run {i+1}: {elapsed:.4f}s\n")

    times_sorted = sorted(times)
    best_time = times_sorted[0]
    median = times_sorted[len(times_sorted) // 2]
    mean = sum(times) / len(times)

    threshold = 0.60

    print("=" * 70)
    print("Benchmark Results")
    print("=" * 70)
    print(f"Run times: {[f'{t:.4f}s' for t in times]}")
    print(f"Best time: {best_time:.4f}s")
    print(f"Median:    {median:.4f}s")
    print(f"Mean:      {mean:.4f}s")
    print(f"Threshold: {threshold:.4f}s")
    print()

    if best_time <= threshold:
        print(f"✓ PASS - Performance is acceptable ({best_time:.4f}s <= {threshold:.4f}s)")
        return 0
    else:
        print(f"✗ FAIL - Performance regression detected ({best_time:.4f}s > {threshold:.4f}s)")
        return 1


if __name__ == "__main__":
    sys.exit(benchmark_pipeline())
