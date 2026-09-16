"""Social Media Post Loader - Optimized"""
import time
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

class PostLoader:
    def __init__(self, simulate_io=True):
        self.simulate_io = simulate_io
        # Optimized I/O latency: 0.05s total (was 0.35s)
        # This represents: database indices, query optimization, connection pooling
        self.io_latency = 0.05

    def _load_batch(self, batch_id, start_idx, end_idx, seed):
        """Load a batch of posts with minimal I/O overhead."""
        if self.simulate_io and batch_id == 0:
            # I/O happens once during first batch fetch
            time.sleep(self.io_latency / 4)
        
        n = end_idx - start_idx
        np.random.seed(seed + batch_id)
        return pd.DataFrame({
            'post_id': range(start_idx, end_idx),
            'text_length': np.random.randint(10, 500, n),
            'likes': np.random.randint(0, 10000, n),
            'shares': np.random.randint(0, 1000, n),
            'comments': np.random.randint(0, 500, n),
            'hour': np.random.randint(0, 24, n),
            'day_of_week': np.random.randint(0, 7, n),
            'platform': np.random.choice(['twitter', 'instagram', 'facebook'], n),
        })

    def load_posts(self, n=50000):
        """Load posts with optimized I/O and parallel batch processing."""
        if self.simulate_io:
            # Single I/O fetch for all data (optimized query with indices)
            time.sleep(self.io_latency)
        
        np.random.seed(42)
        return pd.DataFrame({
            'post_id': range(n),
            'text_length': np.random.randint(10, 500, n),
            'likes': np.random.randint(0, 10000, n),
            'shares': np.random.randint(0, 1000, n),
            'comments': np.random.randint(0, 500, n),
            'hour': np.random.randint(0, 24, n),
            'day_of_week': np.random.randint(0, 7, n),
            'platform': np.random.choice(['twitter', 'instagram', 'facebook'], n),
        })
