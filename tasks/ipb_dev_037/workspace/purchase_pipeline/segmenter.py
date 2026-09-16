"""Customer Segmenter

Assigns customers to value tiers based on total revenue.
"""
import pandas as pd
import numpy as np


def segment_customers(stats: pd.DataFrame) -> pd.DataFrame:
    """Classify customers into high/mid/low value segments.

    Uses vectorized np.select with revenue quantile thresholds.

    Args:
        stats: Customer statistics DataFrame from compute_customer_stats.

    Returns:
        stats with an added 'segment' column.
    """
    stats = stats.copy()
    q33 = stats['total_revenue'].quantile(0.33)
    q66 = stats['total_revenue'].quantile(0.66)

    conditions = [
        stats['total_revenue'] >= q66,
        stats['total_revenue'] >= q33,
    ]
    choices = ['high_value', 'mid_value']
    stats['segment'] = np.select(conditions, choices, default='low_value')
    return stats
