"""Data Validator Module"""

import pandas as pd


class DataValidator:
    """Validates and cleans transaction data."""

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Basic validation checks."""
        # Remove rows with null customer_id or amount
        df = df.dropna(subset=['customer_id', 'amount'])
        
        # Remove negative amounts
        df = df[df['amount'] > 0]
        
        return df

    def check_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate transactions."""
        return df.drop_duplicates(subset=['transaction_id'])
