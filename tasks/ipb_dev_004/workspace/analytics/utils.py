"""Utility Functions

Common utilities for data analytics.
"""

import pandas as pd
import numpy as np
from typing import Any, List


def round_to_decimals(value: float, decimals: int = 2) -> float:
    """
    Round value to specified decimal places.

    Args:
        value: Value to round
        decimals: Number of decimal places

    Returns:
        Rounded value
    """
    return round(value, decimals)


def safe_divide(numerator: Any, denominator: Any, default: float = 0.0) -> float:
    """
    Safely divide two values, returning default if denominator is zero.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value to return if division by zero

    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame column names to lowercase with underscores.

    Args:
        df: DataFrame to normalize

    Returns:
        DataFrame with normalized column names
    """
    df = df.copy()
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    return df


def convert_to_numeric(series: pd.Series, errors: str = 'coerce') -> pd.Series:
    """
    Convert series to numeric type.

    Args:
        series: Series to convert
        errors: How to handle errors ('raise', 'coerce', 'ignore')

    Returns:
        Numeric series
    """
    return pd.to_numeric(series, errors=errors)


def get_summary_stats(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Get summary statistics for specified columns.

    Args:
        df: DataFrame to analyze
        columns: List of columns to summarize

    Returns:
        DataFrame with summary statistics
    """
    valid_columns = [col for col in columns if col in df.columns]
    if not valid_columns:
        return pd.DataFrame()

    return df[valid_columns].describe()
