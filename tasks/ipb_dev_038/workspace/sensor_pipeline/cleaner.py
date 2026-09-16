"""Sensor Signal Cleaner

Cleans and interpolates missing values in sensor readings.
"""
import pandas as pd


class SensorCleaner:
    """Clean sensor time-series data."""

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Forward-fill then backward-fill missing sensor values.

        Args:
            df: Raw sensor DataFrame.

        Returns:
            Cleaned DataFrame with no NaN values.
        """
        sensor_cols = [c for c in df.columns if c.startswith('sensor_')]
        df = df.copy()
        df[sensor_cols] = df[sensor_cols].ffill().bfill()
        return df.dropna().reset_index(drop=True)
