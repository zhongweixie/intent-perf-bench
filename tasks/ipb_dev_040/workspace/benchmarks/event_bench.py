"""Performance benchmark for the Event Analytics Pipeline."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from run_pipeline import run_pipeline


def run_benchmark(n_runs: int = 3):
    print("=" * 70)
    print("Event Analytics Pipeline Benchmark")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Events   : 100,000")
    print(f"  Batches  : 200 × 500")
    print(f"  Runs     : {n_runs}")
    print()

    times = []
    for i in range(n_runs):
        print(f"--- Run {i + 1}/{n_runs} ---")
        t = run_pipeline()
        times.append(t)
        print(f"Run {i + 1} time: {t:.4f}s\n")

    times_sorted = sorted(times)
    best   = times_sorted[0]
    median = times_sorted[len(times_sorted) // 2]
    THRESHOLD = 0.55

    print("=" * 70)
    print("Benchmark Results")
    print("=" * 70)
    print(f"Run times : {[f'{t:.4f}s' for t in times]}")
    print(f"Best time : {best:.4f}s")
    print(f"Median    : {median:.4f}s")
    print(f"Threshold : {THRESHOLD:.4f}s")
    print()

    if best <= THRESHOLD:
        print(f"✓ PASS: Best time {best:.4f}s <= {THRESHOLD:.4f}s")
        return 0
    else:
        print(f"✗ FAIL: Best time {best:.4f}s > {THRESHOLD:.4f}s")
        return 1


if __name__ == "__main__":
    sys.exit(run_benchmark())
