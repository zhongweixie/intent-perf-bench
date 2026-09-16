"""Customer Analyzer

Computes aggregate purchase statistics per customer for downstream segmentation.
"""
import pandas as pd
import numpy as np


def compute_customer_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-customer purchase statistics.

    Uses vectorized Pandas aggregation for optimal performance.

    Args:
        df: Enriched purchase DataFrame.

    Returns:
        DataFrame with one row per customer and aggregate statistics.
    """
    return (
        df.groupby('customer_id')['purchase_amount']
        .agg([
            ('purchase_count', 'count'),
            ('total_revenue', 'sum'),
            ('mean_purchase', 'mean'),
            ('std_purchase', 'std'),
            ('max_purchase', 'max'),
        ])
        .fillna(0.0)
        .reset_index()
    )
