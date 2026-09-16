"""Log Enricher Module

Enriches log events with category reference metadata (severity, service, routing).
"""
import pandas as pd
import numpy as np


def _build_ref_data() -> pd.DataFrame:
    """Build the category reference table."""
    np.random.seed(0)
    categories = [f"cat_{i:02d}" for i in range(40)]
    return pd.DataFrame({
        'category':        categories,
        'severity':        np.random.choice(['info', 'warn', 'error', 'debug'], 40),
        'service':         np.random.choice(['api', 'auth', 'db', 'cache', 'queue'], 40),
        'routing_group':   np.random.choice(['group_a', 'group_b', 'group_c'], 40),
        'alert_threshold': np.random.randint(100, 500, 40),
    })


REF_DATA = _build_ref_data()


class LogEnricher:
    """Enrich log events with category reference metadata."""

    def __init__(self):
        self.ref_data = REF_DATA

    def enrich_events(self, events: pd.DataFrame) -> pd.DataFrame:
        """Enrich events with severity, service, and routing metadata."""
        return events.merge(
            self.ref_data[['category', 'severity', 'service',
                           'routing_group', 'alert_threshold']],
            on='category',
            how='left',
        ).reset_index(drop=True)
