"""Log Aggregator Module

Computes summary statistics from enriched log events.
"""
import pandas as pd


class LogAggregator:
    """Aggregate enriched log events into summary reports."""

    def aggregate_by_service(self, enriched: pd.DataFrame) -> pd.DataFrame:
        """Count events and compute avg duration by service."""
        return (
            enriched.groupby('service')
            .agg(
                event_count=('event_id', 'count'),
                avg_duration=('duration_ms', 'mean'),
                error_count=('severity', lambda x: (x == 'error').sum()),
            )
            .reset_index()
        )

    def aggregate_by_host(self, enriched: pd.DataFrame) -> pd.DataFrame:
        """Count events per host and latency bucket."""
        return (
            enriched.groupby(['host', 'latency_bucket'], observed=False)
            .size()
            .reset_index(name='count')
        )
