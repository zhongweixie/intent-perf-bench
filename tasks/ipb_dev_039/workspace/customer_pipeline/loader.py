"""Customer Data Loader — loads raw customer transaction records."""
import time
import numpy as np
import pandas as pd


class CustomerLoader:
    def __init__(self, simulate_io: bool = True):
        self.simulate_io = simulate_io

    def load(self, n_records: int = 100000) -> pd.DataFrame:
        if self.simulate_io:
            time.sleep(0.15)
        np.random.seed(42)
        return pd.DataFrame({
            'customer_id': np.random.randint(1, 5001, n_records),
            'segment':     np.random.choice(
                [f's{i}' for i in range(10)], n_records
            ),
            'value':       np.random.exponential(50.0, n_records),
            'purchase_date': [
                f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
                for i in range(n_records)
            ],
            'product_id':  np.random.randint(1, 201, n_records),
            'quantity':    np.random.randint(1, 11, n_records),
        })
