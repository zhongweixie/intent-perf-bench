"""Customer Scorer — computes z-score deviation from segment benchmarks."""
import pandas as pd
import numpy as np


class CustomerScorer:
    """Score customers by comparing their value to historical segment norms."""

    def __init__(self, historical_data: pd.DataFrame):
        self._historical = historical_data
        # Pre-compute benchmarks once in __init__ rather than recomputing on
        # every score_batch() call.  Previously this was a @property that ran
        # a groupby over 200 k rows on each of the 200 batch iterations
        # (200 × groupby = the dominant pipeline cost).
        self._benchmarks = (
            historical_data
            .groupby('segment')
            .agg(mean=('value', 'mean'), std=('value', 'std'))
            .reset_index()
        )

    @property
    def benchmarks(self) -> pd.DataFrame:
        """Return the pre-computed per-segment mean and std from historical data."""
        return self._benchmarks

    def score_batch(self, batch: pd.DataFrame) -> pd.Series:
        """Compute z-score for each record in a batch."""
        b = self.benchmarks
        scored = batch.merge(b, on='segment', how='left')
        return (scored['value'] - scored['mean']).abs() / (scored['std'] + 1e-9)
