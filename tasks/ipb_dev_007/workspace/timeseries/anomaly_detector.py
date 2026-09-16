"""Anomaly Detector Module

Detects outliers based on rolling statistics.
"""
import pandas as pd


class AnomalyDetector:
    """Flag anomalous sensor readings."""

    def detect_anomalies(self, features: pd.DataFrame) -> pd.DataFrame:
        """Flag readings > 2 std away from rolling mean."""
        anomalies = features.copy()
        anomalies['is_anomaly'] = False

        for col in ['temperature', 'humidity', 'pressure']:
            mean_col = f'{col}_rolling_mean'
            std_col = f'{col}_rolling_std'
            if mean_col in features.columns and std_col in features.columns:
                deviation = abs(features[col] - features[mean_col])
                threshold = 2 * features[std_col]
                anomalies['is_anomaly'] |= (deviation > threshold)

        return anomalies
