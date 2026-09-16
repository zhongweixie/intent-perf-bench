"""Inventory Data Loader"""
import time, numpy as np, pandas as pd

class InventoryLoader:
    def __init__(self, simulate_io=True):
        self.simulate_io = simulate_io

    def load_inventory(self, n=30000):
        if self.simulate_io:
            time.sleep(0.10)
        np.random.seed(42)
        return pd.DataFrame({
            'sku': [f'SKU-{i:05d}' for i in range(n)],
            'warehouse': np.random.choice(['A','B','C','D'], n),
            'quantity': np.random.randint(0, 500, n),
            'unit_cost': np.random.uniform(1, 200, n),
            'reorder_point': np.random.randint(10, 100, n),
            'lead_days': np.random.randint(1, 30, n),
            'days_since_order': np.random.randint(0, 60, n),
        })
