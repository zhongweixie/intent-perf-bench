"""Data Filters Module

Provides filtering capabilities for transaction data.
"""

import pandas as pd
from typing import List, Optional


class DataFilter:
    """Filter transaction data based on various criteria."""

    def __init__(self):
        """Initialize filter."""
        pass

    def filter_by_categories(self, df: pd.DataFrame, categories: List[str]) -> pd.DataFrame:
        """
        Filter transactions by product categories.

        Args:
            df: Transaction DataFrame
            categories: List of categories to include

        Returns:
            Filtered DataFrame
        """
        if 'category' not in df.columns:
            return df
        return df[df['category'].isin(categories)].copy()

    def filter_by_regions(self, df: pd.DataFrame, regions: List[str]) -> pd.DataFrame:
        """
        Filter transactions by regions.

        Args:
            df: Transaction DataFrame
            regions: List of regions to include

        Returns:
            Filtered DataFrame
        """
        if 'region' not in df.columns:
            return df
        return df[df['region'].isin(regions)].copy()

    def filter_by_amount_range(
        self, df: pd.DataFrame, min_amount: float = 0, max_amount: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Filter transactions by amount range.

        Args:
            df: Transaction DataFrame
            min_amount: Minimum transaction amount
            max_amount: Maximum transaction amount (None for no limit)

        Returns:
            Filtered DataFrame
        """
        if 'amount' not in df.columns:
            return df

        result = df[df['amount'] >= min_amount]
        if max_amount is not None:
            result = result[result['amount'] <= max_amount]

        return result.copy()

    def filter_high_value_transactions(self, df: pd.DataFrame, threshold: float = 500) -> pd.DataFrame:
        """
        Filter for high-value transactions.

        Args:
            df: Transaction DataFrame
            threshold: Minimum amount threshold

        Returns:
            Filtered DataFrame with high-value transactions
        """
        return self.filter_by_amount_range(df, min_amount=threshold)
