"""Reporter Module

Generates summary reports from aggregated data.
"""

import pandas as pd
from typing import Dict, Any


class ReportGenerator:
    """Generate business reports from aggregated metrics."""

    def __init__(self):
        """Initialize reporter."""
        pass

    def format_currency(self, value: float) -> str:
        """Format value as currency."""
        return f"${value:,.2f}"

    def format_percentage(self, value: float) -> str:
        """Format value as percentage."""
        return f"{value * 100:.2f}%"

    def generate_customer_report(self, customer_agg: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate customer-level summary report.

        Args:
            customer_agg: Customer aggregation DataFrame

        Returns:
            Dictionary with report metrics
        """
        report = {
            'total_customers': len(customer_agg),
            'total_revenue': customer_agg['total_revenue'].sum(),
            'avg_revenue_per_customer': customer_agg['total_revenue'].mean(),
            'total_discounted_amount': customer_agg['discounted_amount'].sum(),
            'avg_profit_margin': customer_agg['profit_margin'].mean(),
            'total_transactions': customer_agg['transaction_count'].sum(),
            'avg_transactions_per_customer': customer_agg['transaction_count'].mean()
        }
        return report

    def generate_region_report(self, region_agg: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate region-level summary report.

        Args:
            region_agg: Region aggregation DataFrame

        Returns:
            Dictionary with report metrics
        """
        report = {
            'total_regions': len(region_agg),
            'total_revenue': region_agg['total_revenue'].sum(),
            'avg_revenue_per_region': region_agg['total_revenue'].mean(),
            'total_discounted_amount': region_agg['discounted_amount'].sum(),
            'avg_profit_margin': region_agg['profit_margin'].mean(),
            'top_region': region_agg.nlargest(1, 'total_revenue')['region'].iloc[0]
        }
        return report

    def print_report(self, report: Dict[str, Any], title: str = "Report"):
        """
        Print formatted report to console.

        Args:
            report: Report dictionary
            title: Report title
        """
        print(f"\n{'=' * 60}")
        print(f"{title:^60}")
        print(f"{'=' * 60}\n")

        for key, value in report.items():
            if isinstance(value, float):
                if 'revenue' in key.lower() or 'amount' in key.lower():
                    formatted_value = self.format_currency(value)
                elif 'margin' in key.lower() or 'rate' in key.lower():
                    formatted_value = self.format_percentage(value)
                else:
                    formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)

            print(f"{key.replace('_', ' ').title():<40} {formatted_value:>19}")

        print()
