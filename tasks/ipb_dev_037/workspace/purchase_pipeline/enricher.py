"""Product Enricher

Enriches purchase records with product catalog metadata via a join.
"""
import pandas as pd
import numpy as np

_PRODUCT_CATALOG: pd.DataFrame | None = None


def _build_catalog() -> pd.DataFrame:
    np.random.seed(0)
    n = 200
    return pd.DataFrame({
        'product_id':   range(1, n + 1),
        'product_tier': np.random.choice(['budget', 'standard', 'premium'], n),
        'margin_rate':  np.random.uniform(0.15, 0.45, n).round(4),
    })


class ProductEnricher:
    """Enrich purchase records with product-level attributes."""

    def __init__(self):
        global _PRODUCT_CATALOG
        if _PRODUCT_CATALOG is None:
            _PRODUCT_CATALOG = _build_catalog()
        self.catalog = _PRODUCT_CATALOG

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        """Left-join product catalog onto purchase records.

        Args:
            df: Purchase DataFrame.

        Returns:
            DataFrame with product_tier and margin_rate columns added.
        """
        return df.merge(
            self.catalog[['product_id', 'product_tier', 'margin_rate']],
            on='product_id',
            how='left',
        )
