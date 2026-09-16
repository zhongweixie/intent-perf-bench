"""Customer Segmenter — assigns value tier labels based on z-scores."""
import pandas as pd
import numpy as np


def segment_by_score(scores: pd.Series) -> pd.Series:
    """Classify each score into high/medium/low anomaly tier."""
    conditions = [scores >= 2.0, scores >= 1.0]
    choices = ['high_anomaly', 'medium_anomaly']
    return pd.Series(
        np.select(conditions, choices, default='normal'),
        index=scores.index,
    )
