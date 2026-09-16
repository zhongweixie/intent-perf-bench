"""Sensor Feature Extractor

Computes rolling statistical features used for IQR-based anomaly detection.
"""
import pandas as pd


def extract_rolling_features(df: pd.DataFrame, window: int = 100) -> pd.DataFrame:
    """Extract rolling IQR features for each sensor channel.

    Computes rolling 75th percentile, 25th percentile, and inter-quartile
    range (IQR) per channel using pandas' built-in quantile implementation.

    Args:
        df:     Cleaned sensor DataFrame.
        window: Rolling window size in samples.

    Returns:
        DataFrame with rolling P75, P25, and IQR columns per sensor.
    """
    sensor_cols = [c for c in df.columns if c.startswith('sensor_')]
    result = df[['timestamp']].copy()

    for col in sensor_cols:
        series = df[col]
        # Use pandas built-in rolling quantile (Cython-optimised) instead of
        # rolling().apply(np.percentile) to avoid per-window Python call overhead.
        p75 = series.rolling(window=window).quantile(0.75)
        p25 = series.rolling(window=window).quantile(0.25)
        iqr = p75 - p25
        result[f'{col}_p75'] = p75
        result[f'{col}_p25'] = p25
        result[f'{col}_iqr'] = iqr

    return result.dropna().reset_index(drop=True)
