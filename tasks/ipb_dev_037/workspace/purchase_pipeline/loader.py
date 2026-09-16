"""Purchase Data Loader

Loads purchase transaction records for the analytics pipeline.
"""
import pandas as pd
import numpy as np
import time


class PurchaseLoader:
    """Load and return purchase transaction data."""

    def __init__(self, simulate_io: bool = True):
        self.simulate_io = simulate_io

    def load_purchases(self, n_records: int = 100000) -> pd.DataFrame:
        """Load purchase records.

        Args:
            n_records: Number of records to generate.

        Returns:
            DataFrame with purchase transaction data.
        """
        if self.simulate_io:
            # Simulate reading a wide CSV from disk (180-column production schema)
            time.sleep(0.15)

        np.random.seed(42)
        return pd.DataFrame({
            'purchase_id':     range(n_records),
            'customer_id':     np.random.randint(1, 5001, n_records),
            'product_id':      np.random.randint(1, 201, n_records),
            'purchase_amount': np.random.exponential(50.0, n_records),
            'quantity':        np.random.randint(1, 11, n_records),
            'category':        np.random.choice(
                ['electronics', 'clothing', 'food', 'home', 'sports'], n_records
            ),
            'region':          np.random.choice(
                ['north', 'south', 'east', 'west'], n_records
            ),
        })
