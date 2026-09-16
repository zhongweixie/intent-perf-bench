"""Report Builder

Assembles a summary report from customer statistics and segments.
"""
import pandas as pd


def build_report(stats: pd.DataFrame, segments: pd.DataFrame) -> dict:
    """Build a summary report dict.

    Args:
        stats:    Customer statistics DataFrame.
        segments: Segmented customer DataFrame.

    Returns:
        Report dictionary with key business metrics.
    """
    segment_counts = segments['segment'].value_counts().to_dict()
    return {
        'total_customers':       int(len(stats)),
        'total_revenue':         float(stats['total_revenue'].sum()),
        'mean_customer_revenue': float(stats['total_revenue'].mean()),
        'median_purchase':       float(stats['mean_purchase'].median()),
        'segments':              segment_counts,
    }
