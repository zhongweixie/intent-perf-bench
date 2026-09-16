"""Log Loader Module"""
import time
import pandas as pd
import numpy as np


class LogLoader:
    """Load raw application logs."""

    def __init__(self, simulate_io: bool = True):
        self.simulate_io = simulate_io

    def load_logs(self, n_logs: int = 30000) -> pd.DataFrame:
        """Load raw log entries. Simulates file I/O latency."""
        if self.simulate_io:
            # Simulate realistic log file I/O
            time.sleep(0.08)

        np.random.seed(42)
        timestamps = pd.date_range('2024-01-01', periods=n_logs, freq='1s')
        data = {
            'timestamp': timestamps,
            'level': np.random.choice(['INFO', 'WARN', 'ERROR', 'DEBUG'], n_logs),
            'service': np.random.choice([f'svc-{i}' for i in range(10)], n_logs),
            'duration_ms': np.random.exponential(100, n_logs),
            'status_code': np.random.choice([200, 201, 400, 404, 500], n_logs),
        }
        return pd.DataFrame(data)
