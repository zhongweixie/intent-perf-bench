"""Performance Benchmark for Time Series Pipeline"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from timeseries.loader import TimeSeriesLoader
from timeseries.feature_builder import FeatureBuilder
from timeseries.anomaly_detector import AnomalyDetector
from timeseries.report_generator import ReportGenerator

THRESHOLD = 0.40  # baseline ~0.02s (no I/O), regressed ~7.8s (no I/O)


def run_once():
    loader = TimeSeriesLoader(simulate_io=False)
    data = loader.load_sensor_data(n_points=10000)
    builder = FeatureBuilder()
    features = builder.build_features(data, window_size=10)
    detector = AnomalyDetector()
    anomalies = detector.detect_anomalies(features)
    reporter = ReportGenerator()
    report = reporter.generate_report(anomalies)
    return report


def benchmark_pipeline(n_runs: int = 3):
    """Run pipeline benchmark."""
    print("=" * 70)
    print("Time Series Pipeline Performance Benchmark")
    print("=" * 70)
    print(f"\nConfiguration: 10,000 points, {n_runs} runs\n")

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

    threshold = THRESHOLD

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
