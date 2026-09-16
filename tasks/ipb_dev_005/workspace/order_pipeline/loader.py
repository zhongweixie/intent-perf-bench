"""Order Loader Module

Loads order data from data source with simulated I/O latency.
"""
import pandas as pd
import numpy as np
import time


class OrderLoader:
    """Load order data from data source."""

    def __init__(self, simulate_io: bool = True):
        self.simulate_io = simulate_io

    def load_orders(self, n_orders: int = 30000) -> pd.DataFrame:
        """Load order data. Simulates disk/network I/O latency."""
        if self.simulate_io:
            # Simulate realistic I/O latency (tuned for baseline ~0.5s total)
            time.sleep(0.10)

        np.random.seed(42)
        data = {
            'order_id': range(n_orders),
            'items': [
                list(np.random.choice(
                    ['ItemA', 'ItemB', 'ItemC', 'ItemD', 'ItemE', 'ItemF'],
                    np.random.randint(2, 6), replace=False
                )) for _ in range(n_orders)
            ],
            'amount': np.random.uniform(10, 1000, n_orders),
            'customer': np.random.choice([f'cust_{i}' for i in range(1000)], n_orders),
            'region': np.random.choice(['North', 'South', 'East', 'West'], n_orders),
        }
        return pd.DataFrame(data)
