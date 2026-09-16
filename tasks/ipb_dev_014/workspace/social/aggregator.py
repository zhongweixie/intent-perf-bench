"""Social Aggregator"""
import pandas as pd

class SocialAggregator:
    def aggregate_by_platform(self, df: pd.DataFrame) -> pd.DataFrame:
        return (df.groupby('platform')
                .agg(post_count=('post_id','count'),
                     avg_engagement=('engagement_score','mean'),
                     total_likes=('likes','sum'))
                .reset_index())
