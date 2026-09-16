"""Report Generator Module

Aggregates anomaly statistics by sensor.
"""
import pandas as pd


class ReportGenerator:
    """Generate anomaly summary report."""

    def generate_report(self, anomalies: pd.DataFrame) -> pd.DataFrame:
        """Aggregate anomaly counts and rates by sensor."""
        report = anomalies.groupby('sensor_id').agg(
            total_readings=('timestamp', 'count'),
            anomaly_count=('is_anomaly', 'sum'),
        ).reset_index()
        report['anomaly_rate'] = report['anomaly_count'] / report['total_readings']
        return report.sort_values('anomaly_rate', ascending=False)
