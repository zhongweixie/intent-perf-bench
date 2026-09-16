"""Payment Aggregator - groups risk scores."""


class PaymentAggregator:
    def aggregate_by_category(self, scored):
        import pandas as pd
        
        return (scored.groupby('merchant_category')
                .agg(count=('payment_id','count'),
                     avg_risk=('risk_score','mean'),
                     high_risk_count=('risk_score', lambda x: (x > 0.7).sum()))
                .reset_index())
