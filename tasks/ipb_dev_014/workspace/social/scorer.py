"""Engagement Scorer - VECTORIZED"""
import pandas as pd, numpy as np

class EngagementScorer:
    def compute_engagement(self, posts: pd.DataFrame) -> pd.DataFrame:
        """FAST: vectorized scoring without apply()."""
        result = posts.copy()
        
        # Vectorized calculations
        engagement_rate = (result['likes'] + result['shares'] * 3 + result['comments'] * 2) / 10000.0
        virality_score = np.minimum(10, result['shares'] / np.maximum(1, result['likes']))
        peak_hour = (result['hour'] >= 9) & (result['hour'] <= 17)
        long_form = result['text_length'] > 200
        
        # Combine scores
        result['engagement_score'] = (
            0.4 * np.minimum(1, engagement_rate) + 
            0.3 * virality_score / 10.0 +
            0.2 * peak_hour.astype(int) + 
            0.1 * long_form.astype(int)
        )
        
        return result
