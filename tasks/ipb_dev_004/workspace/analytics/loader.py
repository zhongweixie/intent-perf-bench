"""Data Loader Module

Handles loading and parsing of CSV data files.
"""

import pandas as pd
import numpy as np
from typing import Optional
import time


class DataLoader:
    """Load and parse business transaction data."""

    def __init__(self, simulate_io: bool = True):
        """
        Initialize data loader.

        Args:
            simulate_io: If True, add small delay to simulate disk I/O
        """
        self.simulate_io = simulate_io

    def load_transactions(self, n_records: int = 50000) -> pd.DataFrame:
        """
        Load transaction data.

        Args:
            n_records: Number of records to generate

        Returns:
            DataFrame with transaction data
        """
        if self.simulate_io:
            # Simulate disk I/O latency (20-30% of total time)
            time.sleep(0.15)

        np.random.seed(42)

        # Generate synthetic transaction data
        data = {
            'transaction_id': range(n_records),
            'customer_id': np.random.randint(1, 1000, n_records),
            'product_id': np.random.randint(1, 500, n_records),
            'amount': np.random.uniform(10, 1000, n_records),
            'quantity': np.random.randint(1, 20, n_records),
            'discount_rate': np.random.uniform(0, 0.3, n_records),
            'category': np.random.choice(['A', 'B', 'C', 'D'], n_records),
            'region': np.random.choice(['North', 'South', 'East', 'West'], n_records)
        }

        return pd.DataFrame(data)

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """
        Validate that DataFrame has expected columns.

        Args:
            df: DataFrame to validate

        Returns:
            True if schema is valid
        """
        required_columns = [
            'transaction_id', 'customer_id', 'product_id',
            'amount', 'quantity', 'discount_rate', 'category', 'region'
        ]
        return all(col in df.columns for col in required_columns)
