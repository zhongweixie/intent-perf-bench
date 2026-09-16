"""Data Loader Module

Loads raw customer transaction data.
"""
import time
import numpy as np
import pandas as pd


class DataLoader:
    """Load raw transaction data."""

    def __init__(self, simulate_io: bool = True):
        self.simulate_io = simulate_io

    def load_transactions(self, n_rows: int = 50000) -> pd.DataFrame:
        """Load raw transaction records. Simulates database query latency."""
        if self.simulate_io:
            # Simulate realistic database query latency
            time.sleep(0.15)

        np.random.seed(42)
        data = {
            'customer_id': np.random.randint(1000, 5000, n_rows),
            'amount': np.random.uniform(10, 1000, n_rows),
            'quantity': np.random.randint(1, 20, n_rows),
            'discount': np.random.uniform(0, 0.3, n_rows),
            'category': np.random.choice(['A', 'B', 'C', 'D'], n_rows),
            'is_premium': np.random.choice([0, 1], n_rows),
        }
        return pd.DataFrame(data)
