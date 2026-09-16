"""Time Series Anomaly Detection Pipeline

Main entry point for the sensor anomaly detection workflow.
"""
import time
from timeseries.loader import TimeSeriesLoader
from timeseries.feature_builder import FeatureBuilder
from timeseries.anomaly_detector import AnomalyDetector
from timeseries.report_generator import ReportGenerator


def run_anomaly_pipeline():
    """Execute the complete anomaly detection pipeline."""
    print("=" * 70)
    print("Time Series Anomaly Detection Pipeline")
    print("=" * 70)

    # Stage 1: Load sensor data
    print("\n[1/4] Loading sensor data...")
    t = time.time()
    loader = TimeSeriesLoader(simulate_io=True)
    data = loader.load_sensor_data(n_points=10000)
    stage1_time = time.time() - t
    print(f"      Loaded {len(data)} points in {stage1_time:.4f}s")

    # Stage 2: Build features
    print("\n[2/4] Building rolling window features...")
    t = time.time()
    builder = FeatureBuilder()
    features = builder.build_features(data, window_size=10)
    stage2_time = time.time() - t
    print(f"      Built features in {stage2_time:.4f}s")

    # Stage 3: Detect anomalies
    print("\n[3/4] Detecting anomalies...")
    t = time.time()
    detector = AnomalyDetector()
    anomalies = detector.detect_anomalies(features)
    stage3_time = time.time() - t
    print(f"      Detected in {stage3_time:.4f}s")

    # Stage 4: Generate report
    print("\n[4/4] Generating report...")
    t = time.time()
    reporter = ReportGenerator()
    report = reporter.generate_report(anomalies)
    stage4_time = time.time() - t
    print(f"      Generated report in {stage4_time:.4f}s")

    total_time = stage1_time + stage2_time + stage3_time + stage4_time
    print(f"\n{'Total time:':20} {total_time:.4f}s")
    print(f"{'  - Load':20} {stage1_time:.4f}s ({stage1_time/total_time*100:.1f}%)")
    print(f"{'  - Features':20} {stage2_time:.4f}s ({stage2_time/total_time*100:.1f}%)")
    print(f"{'  - Detection':20} {stage3_time:.4f}s ({stage3_time/total_time*100:.1f}%)")
    print(f"{'  - Report':20} {stage4_time:.4f}s ({stage4_time/total_time*100:.1f}%)")

    print(f"\nTop anomalous sensors:")
    print(report.head(5).to_string(index=False))

    return total_time


if __name__ == "__main__":
    run_anomaly_pipeline()
