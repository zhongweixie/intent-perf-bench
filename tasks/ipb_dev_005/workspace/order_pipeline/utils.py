"""Utility Functions for Order Pipeline"""
import pandas as pd
import numpy as np


def safe_divide(a, b, default=0.0):
    """Safe division, return default when b is zero."""
    if b == 0:
        return default
    return a / b


def normalize_region(region: str) -> str:
    """Normalize region name to title case."""
    return region.strip().title()


def deduplicate_orders(orders: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate order_ids, keeping first occurrence."""
    return orders.drop_duplicates(subset='order_id', keep='first')


def get_date_range_label(dates: pd.Series) -> str:
    """Return human-readable date range label."""
    if dates.empty:
        return "N/A"
    return f"{dates.min()} to {dates.max()}"
