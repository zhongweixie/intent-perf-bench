"""Performance Benchmark for Feature Engineering Pipeline"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from feature_eng.loader import DataLoader
from feature_eng.builder import FeatureBuilder
from feature_eng.validator import FeatureValidator
from feature_eng.exporter import FeatureExporter

THRESHOLD = 0.40  # baseline ~0.02s (no I/O), regressed ~3.0s (no I/O) — will tune


def run_once():
    loader = DataLoader(simulate_io=False)
    data = loader.load_transactions(n_rows=100000)
    builder = FeatureBuilder()
    features = builder.build_features(data)
    validator = FeatureValidator()
    checks = validator.validate_features(features)
    exporter = FeatureExporter()
    summary = exporter.export_features(features)
    return features


def benchmark_pipeline(n_runs: int = 3):
    """Run pipeline benchmark."""
    print("=" * 70)
    print("Feature Engineering Pipeline Performance Benchmark")
    print("=" * 70)
    print(f"\nConfiguration: 100,000 transactions, {n_runs} runs\n")

    times = []
    for i in range(n_runs):
        print(f"--- Run {i+1}/{n_runs} ---")
        t_start = time.time()
        run_once()
        elapsed = time.time() - t_start
        times.append(elapsed)
        print(f"Run {i+1}: {elapsed:.4f}s\n")

    times_sorted = sorted(times)
    best_time = times_sorted[0]
    median = times_sorted[len(times_sorted) // 2]
    mean = sum(times) / len(times)

    print("=" * 70)
    print("Benchmark Results")
    print("=" * 70)
    print(f"Run times: {[f'{t:.4f}s' for t in times]}")
    print(f"Best time: {best_time:.4f}s")
    print(f"Median:    {median:.4f}s")
    print(f"Mean:      {mean:.4f}s")
    print(f"Threshold: {THRESHOLD:.4f}s")
    print()

    if best_time <= THRESHOLD:
        print(f"✓ PASS - Performance is acceptable ({best_time:.4f}s <= {THRESHOLD:.4f}s)")
        return 0
    else:
        print(f"✗ FAIL - Performance regression detected ({best_time:.4f}s > {THRESHOLD:.4f}s)")
        return 1


if __name__ == "__main__":
    sys.exit(benchmark_pipeline())
