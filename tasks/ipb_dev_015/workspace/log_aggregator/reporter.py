"""Log Reporter Module"""
import pandas as pd


class LogReporter:
    """Generate aggregation reports."""

    def generate_report(self, aggregated: pd.DataFrame) -> dict:
        """Generate summary report from aggregated data."""
        return {
            'total_windows': len(aggregated),
            'total_logs': aggregated['total_count'].sum(),
            'total_errors': aggregated['error_count'].sum(),
            'avg_duration_overall': aggregated['avg_duration'].mean(),
            'max_p95': aggregated['p95_duration'].max(),
        }
