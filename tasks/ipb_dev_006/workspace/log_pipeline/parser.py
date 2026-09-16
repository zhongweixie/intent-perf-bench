"""Log Parser Module

Parses and normalizes raw log events before enrichment.
"""
import pandas as pd


class LogParser:
    """Parse and normalize raw log events."""

    def parse_events(self, events: pd.DataFrame) -> pd.DataFrame:
        """Normalize and tag log fields."""
        parsed = events.copy()
        # Normalize host names to lowercase
        parsed['host'] = parsed['host'].str.lower()
        # Classify duration into latency buckets
        parsed['latency_bucket'] = pd.cut(
            parsed['duration_ms'],
            bins=[0, 10, 50, 200, float('inf')],
            labels=['fast', 'normal', 'slow', 'critical']
        )
        return parsed
