# IoT Sensor Anomaly Detection Pipeline

## Overview

Six-stage pipeline that reads multi-channel IoT sensor data, computes
rolling IQR-based statistical features, and flags anomalous readings.

## Stages

1. **Read**    — load sensor feed data (`reader.py`)
2. **Clean**   — interpolate missing values (`cleaner.py`)
3. **Extract** — rolling P75/P25/IQR features (`feature_extractor.py`)
4. **Detect**  — IQR-based anomaly detection (`anomaly_detector.py`)
5. **Alert**   — threshold-based alert generation (`alert_generator.py`)
6. **Report**  — summary report (`reporter.py`)

## Running

```bash
# Full pipeline
python3 run_pipeline.py

# Performance benchmark
python3 benchmarks/sensor_bench.py
```

## Benchmark Threshold

The benchmark passes when `best_time <= 0.6s`.
