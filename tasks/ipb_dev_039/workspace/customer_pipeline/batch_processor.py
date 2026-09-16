"""Batch Processor — runs CustomerScorer over current data."""
import pandas as pd


class BatchProcessor:
    BATCH_SIZE = 500

    def __init__(self, scorer):
        self._scorer = scorer

    def process(self, df: pd.DataFrame) -> pd.Series:
        """Score all records in a single vectorised pass.

        Iterating in BATCH_SIZE chunks previously called score_batch() 200
        times — each call triggering a separate merge + Series allocation.
        Since scoring is row-independent (each row only needs its segment's
        pre-computed mean/std), a single merge over the full DataFrame is
        mathematically equivalent and eliminates 199 rounds of merge setup
        and the final pd.concat overhead.
        """
        return self._scorer.score_batch(df).reset_index(drop=True)
