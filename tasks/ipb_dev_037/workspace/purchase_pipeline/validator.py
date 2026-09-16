"""Data Validator

Validates and cleans purchase records before downstream processing.
"""
import pandas as pd


class PurchaseValidator:
    """Validate and clean purchase transaction data."""

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop null rows and filter out invalid amounts/quantities.

        Args:
            df: Raw purchase DataFrame.

        Returns:
            Cleaned DataFrame with valid records only.
        """
        df = df.dropna()
        df = df[df['purchase_amount'] > 0]
        df = df[df['quantity'] > 0]
        return df.reset_index(drop=True)
