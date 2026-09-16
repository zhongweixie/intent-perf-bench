"""Log Loader Module

Loads raw log events from data source with simulated I/O latency.
"""
import pandas as pd
import numpy as np
import time


class LogLoader:
    """Load raw log events from data source."""

    def __init__(self, simulate_io: bool = True):
        self.simulate_io = simulate_io

    def load_events(self, n_events: int = 80000) -> pd.DataFrame:
        """Load raw log events. Simulates network/disk I/O latency."""
        if self.simulate_io:
            # Simulate realistic I/O latency from log aggregation service
            time.sleep(0.093)

        np.random.seed(42)
        categories = [f"cat_{i:02d}" for i in range(40)]
        data = {
            'event_id': range(n_events),
            'timestamp': pd.date_range('2024-01-01', periods=n_events, freq='1s'),
            'category': np.random.choice(categories, n_events),
            'host': np.random.choice([f'host_{i}' for i in range(200)], n_events),
            'message': np.random.choice(
                ['Connection timeout', 'Request processed', 'Cache miss',
                 'DB query ok', 'Auth success', 'Rate limit hit'],
                n_events
            ),
            'duration_ms': np.random.exponential(50, n_events),
        }
        return pd.DataFrame(data)
