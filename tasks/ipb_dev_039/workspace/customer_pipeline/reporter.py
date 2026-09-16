"""Report Builder — assembles the final pipeline summary report."""
import pandas as pd


class ReportBuilder:
    def build(self, scores: pd.Series, tiers: pd.Series) -> dict:
        tier_counts = tiers.value_counts().to_dict()
        return {
            'total_records':  int(len(scores)),
            'mean_score':     float(scores.mean()),
            'high_anomalies': int(tier_counts.get('high_anomaly', 0)),
            'medium_anomalies': int(tier_counts.get('medium_anomaly', 0)),
            'normal':         int(tier_counts.get('normal', 0)),
        }
