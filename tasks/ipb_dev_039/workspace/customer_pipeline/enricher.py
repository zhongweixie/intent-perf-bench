"""Catalog Enricher — joins product catalog attributes onto transaction data."""
import pandas as pd
import numpy as np


_CATALOG: pd.DataFrame | None = None


def _build_catalog() -> pd.DataFrame:
    np.random.seed(0)
    n = 200
    return pd.DataFrame({
        'product_id':   range(1, n + 1),
        'product_tier': np.random.choice(['budget', 'standard', 'premium'], n),
        'margin_rate':  np.random.uniform(0.15, 0.45, n).round(4),
    })


class CatalogEnricher:
    def __init__(self):
        global _CATALOG
        if _CATALOG is None:
            _CATALOG = _build_catalog()
        self._catalog = _CATALOG

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.merge(
            self._catalog[['product_id', 'product_tier', 'margin_rate']],
            on='product_id',
            how='left',
        )
