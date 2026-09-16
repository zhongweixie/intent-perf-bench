"""Churn Aggregator"""
import pandas as pd


class ChurnAggregator:
    def aggregate_by_contract(self, scored: pd.DataFrame) -> pd.DataFrame:
        return (scored.groupby('contract_type')
                .agg(count=('customer_id','count'),
                     avg_churn_prob=('churn_probability','mean'),
                     churn_count=('predicted_churn','sum'))
                .reset_index())
