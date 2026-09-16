"""Sensor Data Reader

Reads multi-channel sensor data from binary feed files.
"""
import pandas as pd
import numpy as np
import time
from pathlib import Path

_DATA_DIR = Path(__file__).parent / 'data'


class SensorReader:
    """Load and return multi-channel sensor time-series data."""

    def __init__(self, simulate_io: bool = True):
        self.simulate_io = simulate_io

    def read_sensor_data(self, n_samples: int = 10000, n_sensors: int = 3) -> pd.DataFrame:
        """Read sensor readings from pre-serialised binary feed files.

        Loads sensor arrays from a pre-serialised .npy file when available,
        avoiding per-run numpy random-generation overhead.

        Args:
            n_samples: Number of time-series samples per sensor.
            n_sensors: Number of sensor channels.

        Returns:
            DataFrame with timestamp and one column per sensor channel.
        """
        if self.simulate_io:
            # Simulate reading binary sensor feed files from disk
            time.sleep(0.2)

        timestamps = pd.date_range('2024-01-01', periods=n_samples, freq='s')
        data: dict = {'timestamp': timestamps}

        npy_path = _DATA_DIR / f'sensor_data_{n_samples}_{n_sensors}.npy'
        if npy_path.exists():
            # Fast path: load pre-serialised binary — no random generation overhead
            sensor_arrays = np.load(str(npy_path))
            for i in range(1, n_sensors + 1):
                data[f'sensor_{i}'] = sensor_arrays[i - 1]
        else:
            # Fallback: generate data on the fly (slower)
            np.random.seed(42)
            for i in range(1, n_sensors + 1):
                drift  = np.cumsum(np.random.randn(n_samples) * 0.05)
                period = np.sin(np.linspace(0, 6 * np.pi, n_samples)) * 2.0
                noise  = np.random.randn(n_samples) * 0.3
                data[f'sensor_{i}'] = drift + period + noise

        return pd.DataFrame(data)
