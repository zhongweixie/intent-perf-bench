"""Data Aggregator Module"""

import pandas as pd


class DataAggregator:
    """Aggregates transaction data at different levels."""

    def aggregate_by_customer(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate metrics by customer."""
        return df.groupby('customer_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'transaction_id': 'count'
        }).reset_index()

    def aggregate_by_time_period(self, df: pd.DataFrame, freq: str = 'D') -> pd.DataFrame:
        """Aggregate by time period."""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        return df.resample(freq).agg({
            'amount': ['sum', 'count'],
            'customer_id': 'nunique'
        }).reset_index()
