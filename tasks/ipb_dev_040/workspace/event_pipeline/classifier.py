"""Event Classifier — assigns anomaly tier based on z-score."""
import pandas as pd
import numpy as np


def classify_events(scores: pd.Series) -> pd.Series:
    conditions = [scores >= 3.0, scores >= 2.0, scores >= 1.0]
    choices    = ['critical', 'high', 'medium']
    return pd.Series(
        np.select(conditions, choices, default='normal'),
        index=scores.index,
    )
