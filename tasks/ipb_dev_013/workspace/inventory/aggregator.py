"""Inventory Aggregator"""
import pandas as pd

class InventoryAggregator:
    def aggregate_by_warehouse(self, df: pd.DataFrame) -> pd.DataFrame:
        return (df.groupby('warehouse')
                .agg(total_skus=('sku','count'),
                     total_value=('inventory_value','sum'),
                     reorder_needed=('below_reorder','sum'),
                     avg_urgency=('urgency_score','mean'))
                .reset_index())
