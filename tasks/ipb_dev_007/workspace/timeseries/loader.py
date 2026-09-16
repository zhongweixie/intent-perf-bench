"""Time Series Data Loader Module

Loads raw sensor data from data source.
"""
import time
import numpy as np
import pandas as pd


class TimeSeriesLoader:
    """Load raw time series sensor data."""

    def __init__(self, simulate_io: bool = True):
        self.simulate_io = simulate_io

    def load_sensor_data(self, n_points: int = 10000) -> pd.DataFrame:
        """Load raw sensor readings. Simulates network/storage I/O latency."""
        if self.simulate_io:
            # Simulate realistic data ingestion latency
            time.sleep(2.00)

        np.random.seed(42)
        timestamps = pd.date_range('2024-01-01', periods=n_points, freq='1min')
        data = {
            'timestamp': timestamps,
            'sensor_id': np.random.choice([f'sensor_{i:02d}' for i in range(20)], n_points),
            'temperature': np.random.normal(25, 5, n_points),
            'humidity': np.random.normal(60, 10, n_points),
            'pressure': np.random.normal(1013, 5, n_points),
        }
        return pd.DataFrame(data)
