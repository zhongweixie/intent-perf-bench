"""Event Ingester — loads raw event records."""
import time
import numpy as np
import pandas as pd


class EventIngester:
    def __init__(self, simulate_io: bool = True):
        self.simulate_io = simulate_io

    def ingest(self, n_records: int = 100000) -> pd.DataFrame:
        if self.simulate_io:
            time.sleep(0.15)
        np.random.seed(42)
        return pd.DataFrame({
            'event_id':   range(n_records),
            'segment':    np.random.choice([f's{i}' for i in range(20)], n_records),
            'value':      np.random.exponential(50.0, n_records),
            'event_date': [f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}" for i in range(n_records)],
            'event_type': np.random.choice(['click', 'view', 'purchase', 'cart'], n_records),
            'source':     np.random.choice(['web', 'mobile', 'api'], n_records),
            'raw_tag':    [f"tag_{i % 50}:val_{i % 20}" for i in range(n_records)],
        })
