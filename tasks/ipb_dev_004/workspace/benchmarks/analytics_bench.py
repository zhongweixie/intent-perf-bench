"""Performance Benchmark for Analytics Pipeline"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_analytics import run_analytics_pipeline


def benchmark_analytics(n_runs: int = 3):
    """Run analytics pipeline benchmark."""
    print("=" * 70)
    print("Analytics Pipeline Performance Benchmark")
    print("=" * 70)
    print("\nConfiguration:")
    print("  - Records: 50,000")
    print(f"  - Runs: {n_runs}")
    print("\n")

    times = []
    for i in range(n_runs):
        print(f"--- Run {i+1}/{n_runs} ---")
        elapsed = run_analytics_pipeline()
        times.append(elapsed)
        print(f"Run {i+1} time: {elapsed:.4f}s\n")

    # Calculate statistics (use best time to avoid I/O jitter)
    times_sorted = sorted(times)
    best_time = times_sorted[0]
    median = times_sorted[len(times_sorted) // 2]
    mean = sum(times) / len(times)

    # Performance threshold: best time should be <= 0.5s
    # (The regressed version with apply() will take ~13-15s)
    threshold = 0.5

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
    exit_code = benchmark_analytics()
    sys.exit(exit_code)
