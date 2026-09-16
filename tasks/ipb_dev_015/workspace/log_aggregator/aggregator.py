"""Log Aggregator Module - OPTIMIZED VERSION

Aggregates logs by time windows using vectorized groupby operations.
"""
import pandas as pd


class LogAggregator:
    """Aggregate logs by time windows."""

    def aggregate_by_window(self, logs: pd.DataFrame, window: str = '1min') -> pd.DataFrame:
        """
        Aggregate logs into time windows.

        Vectorized approach: uses groupby().agg() for all statistics in one pass.
        """
        logs['window'] = logs['timestamp'].dt.floor(window)

        # Vectorized aggregation: compute all statistics in a single pass
        result = logs.groupby('window').agg({
            'level': lambda x: (x == 'ERROR').sum(),  # error_count
            'duration_ms': ['mean', lambda x: x.quantile(0.95)],  # avg_duration, p95_duration
            'status_code': lambda x: (x == 200).sum(),  # status_200_count
        }).reset_index()

        # Flatten column names and rename
        result.columns = ['window', 'error_count', 'avg_duration', 'p95_duration', 'status_200_count']
        
        # Add total_count by using size()
        counts = logs.groupby('window').size().reset_index(name='total_count')
        result = result.merge(counts, on='window')
        
        # Reorder columns to match original output
        result = result[['window', 'total_count', 'error_count', 'avg_duration', 'p95_duration', 'status_200_count']]

        return result
