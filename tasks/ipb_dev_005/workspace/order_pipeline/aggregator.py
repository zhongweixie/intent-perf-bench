"""Order Aggregator Module

Aggregates order detail data into summary reports.
"""
import pandas as pd


class OrderAggregator:
    """Aggregate order detail into summary reports."""

    def aggregate_by_region_item(self, detail: pd.DataFrame) -> pd.DataFrame:
        """Aggregate sales by region and item."""
        return detail.groupby(['region', 'item'])['amount'].agg(
            total_revenue='sum',
            avg_revenue='mean',
            order_count='count'
        ).reset_index()

    def aggregate_by_customer(self, detail: pd.DataFrame) -> pd.DataFrame:
        """Aggregate sales by customer."""
        return detail.groupby('customer')['amount'].agg(
            total_spent='sum',
            order_count='count',
            avg_order='mean'
        ).reset_index()

    def top_items_by_region(self, summary: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
        """Return top N items per region by total revenue."""
        return (summary
                .sort_values('total_revenue', ascending=False)
                .groupby('region')
                .head(top_n)
                .reset_index(drop=True))
