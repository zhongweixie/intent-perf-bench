"""Event Enricher — stage 3, joins catalog metadata onto events."""
import pandas as pd
import numpy as np

_CATALOG: pd.DataFrame | None = None


def _build_catalog() -> pd.DataFrame:
    np.random.seed(1)
    n = 50
    return pd.DataFrame({
        'event_type': ['click', 'view', 'purchase', 'cart'] * (n // 4) + ['click'] * (n % 4),
        'priority':   np.random.choice(['high', 'medium', 'low'], n),
        'weight':     np.random.uniform(0.5, 2.0, n).round(3),
    }).drop_duplicates('event_type')


class EventEnricher:
    def __init__(self):
        global _CATALOG
        if _CATALOG is None:
            _CATALOG = _build_catalog()
        self._catalog = _CATALOG

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.merge(
            self._catalog[['event_type', 'priority', 'weight']],
            on='event_type', how='left',
        )
