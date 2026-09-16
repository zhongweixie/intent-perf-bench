"""Data Aggregator Module - BASELINE (Fast, Vectorized)

Aggregates business metrics from transaction data using vectorized operations.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


class MetricsAggregator:
    """Aggregate business metrics from transaction data."""

    def __init__(self):
        """Initialize the aggregator."""
        pass

    def calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate derived metrics for each transaction using vectorized operations.

        FAST: Using numpy/pandas vectorized operations instead of apply().

        Args:
            df: Transaction DataFrame

        Returns:
            DataFrame with additional metric columns
        """
        df = df.copy()

        # Vectorized calculations - much faster than apply()
        df['total_revenue'] = df['amount'] * df['quantity']
        df['discounted_amount'] = df['total_revenue'] * (1 - df['discount_rate'])

        # Profit margin calculation
        cost_estimate = df['total_revenue'] * 0.6  # 60% cost ratio
        df['profit_margin'] = np.where(
            df['total_revenue'] > 0,
            (df['total_revenue'] - cost_estimate) / df['total_revenue'],
            0.0
        )

        return df

    def aggregate_by_customer(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate metrics by customer.

        Args:
            df: Transaction DataFrame with derived metrics

        Returns:
            DataFrame with customer-level aggregates
        """
        agg_dict = {
            'total_revenue': 'sum',
            'discounted_amount': 'sum',
            'profit_margin': 'mean',
            'transaction_id': 'count'
        }

        result = df.groupby('customer_id').agg(agg_dict).reset_index()
        result.rename(columns={'transaction_id': 'transaction_count'}, inplace=True)

        return result

    def aggregate_by_region(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate metrics by region.

        Args:
            df: Transaction DataFrame with derived metrics

        Returns:
            DataFrame with region-level aggregates
        """
        agg_dict = {
            'total_revenue': 'sum',
            'discounted_amount': 'sum',
            'profit_margin': 'mean',
            'transaction_id': 'count'
        }

        result = df.groupby('region').agg(agg_dict).reset_index()
        result.rename(columns={'transaction_id': 'transaction_count'}, inplace=True)

        return result
