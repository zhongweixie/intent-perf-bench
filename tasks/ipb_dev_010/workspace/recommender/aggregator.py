"""Recommendation Aggregator Module

Extracts top-N recommendations for each user.
"""
import pandas as pd


class RecommendationAggregator:
    """Aggregate scores into top-N recommendations per user."""

    def get_top_n(self, scores: pd.DataFrame, n: int = 5) -> pd.DataFrame:
        """Get top N product recommendations per user."""
        return (
            scores.sort_values(['user_id', 'recommendation_score'], ascending=[True, False])
            .groupby('user_id')
            .head(n)
            .reset_index(drop=True)
        )
