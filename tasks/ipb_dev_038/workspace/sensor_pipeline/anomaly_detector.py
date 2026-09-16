"""Anomaly Detector

Flags sensor readings that fall outside rolling IQR-based bounds.
"""
import pandas as pd
import numpy as np


class AnomalyDetector:
    """Detect anomalies using rolling IQR thresholding."""

    def __init__(self, iqr_multiplier: float = 1.5):
        self.iqr_multiplier = iqr_multiplier

    def detect(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """Flag readings outside [P25 - k*IQR, P75 + k*IQR] bounds.

        Args:
            df:       Full sensor DataFrame.
            features: Rolling feature DataFrame from extract_rolling_features.

        Returns:
            DataFrame with anomaly counts per sensor channel.
        """
        sensor_cols = [c for c in df.columns if c.startswith('sensor_')]
        results = []
        n = len(features)

        for col in sensor_cols:
            if f'{col}_p75' not in features.columns:
                continue
            vals = df[col].iloc[-n:].values
            p75  = features[f'{col}_p75'].values
            p25  = features[f'{col}_p25'].values
            iqr  = features[f'{col}_iqr'].values

            upper  = p75 + self.iqr_multiplier * iqr
            lower  = p25 - self.iqr_multiplier * iqr
            flagged = int(((vals > upper) | (vals < lower)).sum())
            results.append({'sensor': col, 'anomaly_count': flagged})

        return pd.DataFrame(results)
