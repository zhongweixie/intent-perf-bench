"""Data Validator Module

Validates data quality and business rules.
"""

import pandas as pd
import numpy as np


class DataValidator:
    """Validate business data quality."""

    def __init__(self):
        """Initialize validator."""
        pass

    def check_missing_values(self, df: pd.DataFrame) -> dict:
        """
        Check for missing values in DataFrame.

        Args:
            df: DataFrame to validate

        Returns:
            Dictionary with missing value counts per column
        """
        return df.isnull().sum().to_dict()

    def check_value_ranges(self, df: pd.DataFrame) -> dict:
        """
        Check if values are within expected ranges.

        Args:
            df: DataFrame to validate

        Returns:
            Dictionary with validation results
        """
        results = {}

        if 'amount' in df.columns:
            results['amount_negative'] = (df['amount'] < 0).sum()
            results['amount_zero'] = (df['amount'] == 0).sum()

        if 'quantity' in df.columns:
            results['quantity_negative'] = (df['quantity'] < 0).sum()
            results['quantity_zero'] = (df['quantity'] == 0).sum()

        if 'discount_rate' in df.columns:
            results['discount_out_of_range'] = (
                (df['discount_rate'] < 0) | (df['discount_rate'] > 1)
            ).sum()

        return results

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Run full validation suite.

        Args:
            df: DataFrame to validate

        Returns:
            True if all validations pass
        """
        missing = self.check_missing_values(df)
        ranges = self.check_value_ranges(df)

        # Check if any validation failed
        has_missing = any(count > 0 for count in missing.values())
        has_range_issues = any(count > 0 for count in ranges.values())

        return not (has_missing or has_range_issues)
