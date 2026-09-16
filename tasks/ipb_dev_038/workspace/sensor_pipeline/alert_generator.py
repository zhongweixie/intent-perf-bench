"""Alert Generator

Generates alert messages for sensors exceeding anomaly count thresholds.
"""
from typing import List


def generate_alerts(anomalies, threshold: int = 50) -> List[str]:
    """Generate alert strings for sensors with high anomaly counts.

    Args:
        anomalies: DataFrame with 'sensor' and 'anomaly_count' columns.
        threshold: Minimum anomaly count to trigger an alert.

    Returns:
        List of alert message strings.
    """
    alerts = []
    for _, row in anomalies.iterrows():
        if row['anomaly_count'] > threshold:
            alerts.append(
                f"ALERT: {row['sensor']} — {row['anomaly_count']} anomalies detected"
            )
    return alerts
