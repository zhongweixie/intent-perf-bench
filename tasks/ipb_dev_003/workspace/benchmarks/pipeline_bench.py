"""Performance Benchmark for ETL Pipeline"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_pipeline import run_pipeline


def benchmark_pipeline(n_runs: int = 3):
    """Run pipeline benchmark."""
    print("=" * 70)
    print("ETL Pipeline Performance Benchmark")
    print("=" * 70)
    print("\nConfiguration:")
    print("  - Transactions: 100,000")
    print("  - Customers: 1,000")
    print("  - Runs: {n_runs}")
    print("\n")

    times = []
    for i in range(n_runs):
        print(f"--- Run {i+1}/{n_runs} ---")
        elapsed = run_pipeline()
        times.append(elapsed)
        print(f"Run {i+1} time: {elapsed:.4f}s\n")

    # Calculate statistics (use all runs)
    times_sorted = sorted(times)
    median = times_sorted[len(times_sorted) // 2]
    mean = sum(times) / len(times)
    
    # Performance threshold: median should be <= 1.0s
    # (This accounts for export disk I/O variability)
    threshold = 1.0
    
    print("=" * 70)
    print("Benchmark Results")
    print("=" * 70)
    print(f"Run times: {[f'{t:.4f}s' for t in times]}")
    print(f"Median: {median:.4f}s")
    print(f"Mean:   {mean:.4f}s")
    print(f"Threshold: {threshold:.4f}s")
    print()
    
    if median <= threshold:
        print(f"✓ PASS - Performance is acceptable ({median:.4f}s <= {threshold:.4f}s)")
        return 0
    else:
        print(f"✗ FAIL - Performance regression detected ({median:.4f}s > {threshold:.4f}s)")
        return 1


if __name__ == "__main__":
    exit_code = benchmark_pipeline()
    sys.exit(exit_code)
