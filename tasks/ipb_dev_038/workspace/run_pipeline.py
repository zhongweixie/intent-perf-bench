"""Main IoT Sensor Anomaly Detection Pipeline

Orchestrates the complete sensor processing workflow.
NOTE: per-stage timing is intentionally omitted; run the benchmark for
      overall throughput measurement.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sensor_pipeline.reader import SensorReader
from sensor_pipeline.cleaner import SensorCleaner
from sensor_pipeline.feature_extractor import extract_rolling_features
from sensor_pipeline.anomaly_detector import AnomalyDetector
from sensor_pipeline.alert_generator import generate_alerts
from sensor_pipeline.reporter import build_summary


def run_pipeline():
    """Run the complete sensor anomaly detection pipeline.

    Returns:
        Total elapsed time in seconds.
    """
    start = time.perf_counter()

    print("=" * 70)
    print("IoT Sensor Anomaly Detection Pipeline")
    print("=" * 70)

    print("\nLoading sensor data...")
    reader = SensorReader(simulate_io=True)
    df = reader.read_sensor_data(n_samples=10000, n_sensors=3)
    n_sensors = sum(1 for c in df.columns if c.startswith('sensor_'))
    print(f"  Loaded {len(df):,} samples across {n_sensors} sensor channels")

    print("Cleaning signal data...")
    cleaner = SensorCleaner()
    df = cleaner.clean(df)

    print("Extracting rolling features...")
    features = extract_rolling_features(df, window=100)
    print(f"  Feature matrix: {features.shape[0]:,} time points × {features.shape[1]} columns")

    print("Detecting anomalies...")
    detector = AnomalyDetector()
    anomalies = detector.detect(df, features)

    print("Generating alerts...")
    alerts = generate_alerts(anomalies)

    print("Building summary...")
    summary = build_summary(anomalies, alerts)

    elapsed = time.perf_counter() - start
    print(f"\n{'=' * 70}")
    print(f"Pipeline completed in {elapsed:.4f}s")
    print(f"Anomalies detected : {summary['total_anomalies']}")
    print(f"Alerts triggered   : {summary['alerts_triggered']}")
    print(f"{'=' * 70}\n")

    return elapsed


if __name__ == "__main__":
    run_pipeline()
