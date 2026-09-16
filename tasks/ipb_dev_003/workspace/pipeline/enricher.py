"""Data Enricher Module"""

import pandas as pd


class DataEnricher:
    """Enriches transaction data with derived metrics."""

    def calculate_customer_lifetime_value(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate CLV for each customer."""
        return df.groupby('customer_id')['amount'].sum().reset_index(
            name='lifetime_value'
        )

    def add_customer_segments(self, df: pd.DataFrame) -> pd.DataFrame:
        """Segment customers by spending."""
        clv = self.calculate_customer_lifetime_value(df)
        
        # Simple quantile-based segmentation
        clv['segment'] = pd.qcut(clv['lifetime_value'], q=3, 
                                  labels=['low', 'medium', 'high'])
        
        return df.merge(clv[['customer_id', 'segment']], on='customer_id', how='left')
