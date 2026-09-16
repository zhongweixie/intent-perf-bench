"""Data Aggregator Module - REGRESSED VERSION

Aggregates business metrics from transaction data.

PERFORMANCE ISSUE: This version uses DataFrame.apply() which is much slower
than vectorized operations for computing derived metrics.
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
        Calculate derived metrics for each transaction.

        This is the PERFORMANCE BOTTLENECK - using apply() instead of vectorized ops.

        Args:
            df: Transaction DataFrame

        Returns:
            DataFrame with additional metric columns
        """
        # SLOW: Using apply() to calculate row-by-row
        df = df.copy()
        df['total_revenue'] = df.apply(self._calculate_revenue, axis=1)
        df['discounted_amount'] = df.apply(self._calculate_discounted, axis=1)
        df['profit_margin'] = df.apply(self._calculate_margin, axis=1)
        return df

    def _calculate_revenue(self, row) -> float:
        """Calculate total revenue for a transaction."""
        return row['amount'] * row['quantity']

    def _calculate_discounted(self, row) -> float:
        """Calculate discounted amount."""
        base = row['amount'] * row['quantity']
        return base * (1 - row['discount_rate'])

    def _calculate_margin(self, row) -> float:
        """Calculate profit margin estimate."""
        revenue = row['amount'] * row['quantity']
        cost_estimate = revenue * 0.6  # 60% cost ratio
        return (revenue - cost_estimate) / revenue if revenue > 0 else 0.0

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
