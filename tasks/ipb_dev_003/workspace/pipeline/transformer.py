"""Data Transformer Module - Optimized (Vectorized)"""

import pandas as pd
import numpy as np


class DataTransformer:
    """Transforms transaction data with rolling metrics."""

    def __init__(self, window_hours: int = 24):
        self.window_hours = window_hours

    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features."""
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6])
        return df

    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate per-transaction metrics (VECTORIZED - FAST!)."""
        df = df.sort_values(['customer_id', 'timestamp'])
        
        # Use efficient vectorized groupby operations instead of iterrows
        df['txn_count'] = df.groupby('customer_id').cumcount() + 1
        df['cumulative_spent'] = df.groupby('customer_id')['amount'].cumsum()
        df['avg_transaction'] = df['cumulative_spent'] / df['txn_count']
        
        # Add simple derived metrics
        df['amount_vs_avg'] = df['amount'] / df['avg_transaction']
        df['is_large_txn'] = df['amount'] > df['avg_transaction'] * 1.5
        
        return df
