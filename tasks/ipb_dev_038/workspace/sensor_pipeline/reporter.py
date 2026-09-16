"""Summary Reporter

Assembles the final pipeline summary.
"""
from typing import List


def build_summary(anomalies, alerts: List[str]) -> dict:
    """Build a summary dict from anomaly counts and alerts.

    Args:
        anomalies: DataFrame with sensor anomaly counts.
        alerts:    List of alert message strings.

    Returns:
        Summary dict with key metrics.
    """
    return {
        'sensors_monitored': int(len(anomalies)),
        'total_anomalies':   int(anomalies['anomaly_count'].sum()),
        'alerts_triggered':  len(alerts),
    }
