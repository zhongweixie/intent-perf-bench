"""Anomaly Scorer — computes per-segment z-score benchmarks."""
import pandas as pd
import numpy as np


class AnomalyScorer:
    """Score events against historical segment norms."""

    def __init__(self, historical_data: pd.DataFrame):
        self._historical = historical_data
        # Compute benchmarks once at construction; avoids a full 500k-row
        # groupby on every score_batch() call (was 200 repeated groupbys).
        bench = (
            historical_data
            .groupby('segment')
            .agg(mean=('value', 'mean'), std=('value', 'std'))
            .reset_index()
        )
        self._benchmarks: pd.DataFrame = bench
        # Dict-based lookup is faster than merge for the 200 small batches:
        # two O(n) map() calls replace one pandas merge per batch.
        self._mean_map: dict = bench.set_index('segment')['mean'].to_dict()
        self._std_map: dict  = bench.set_index('segment')['std'].to_dict()

    @property
    def benchmarks(self) -> pd.DataFrame:
        """Return the cached per-segment mean and std."""
        return self._benchmarks

    def score_batch(self, batch: pd.DataFrame) -> pd.Series:
        """Compute z-score for each record in a batch."""
        means = batch['segment'].map(self._mean_map)
        stds  = batch['segment'].map(self._std_map)
        return (batch['value'] - means).abs() / (stds + 1e-9)
