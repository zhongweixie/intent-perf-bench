"""Output Formatter Module

Formats aggregated results for reporting.
"""
import pandas as pd
from typing import Dict, Any


class ReportFormatter:
    """Format aggregated results into report structures."""

    def format_region_summary(self, summary: pd.DataFrame) -> Dict[str, Any]:
        """Format region-item summary into report dict."""
        return {
            'total_regions': summary['region'].nunique(),
            'total_items': summary['item'].nunique(),
            'total_revenue': summary['total_revenue'].sum(),
            'avg_revenue_per_combination': summary['total_revenue'].mean(),
            'top_region': summary.groupby('region')['total_revenue'].sum().idxmax(),
        }

    def format_customer_summary(self, customer_agg: pd.DataFrame) -> Dict[str, Any]:
        """Format customer summary into report dict."""
        return {
            'total_customers': len(customer_agg),
            'total_revenue': customer_agg['total_spent'].sum(),
            'avg_spend_per_customer': customer_agg['total_spent'].mean(),
            'top_customer': customer_agg.nlargest(1, 'total_spent')['customer'].iloc[0],
        }

    def print_report(self, region_report: Dict, customer_report: Dict) -> None:
        """Print formatted summary."""
        print("\n--- Region/Item Summary ---")
        for k, v in region_report.items():
            print(f"  {k}: {v}")
        print("\n--- Customer Summary ---")
        for k, v in customer_report.items():
            print(f"  {k}: {v}")
