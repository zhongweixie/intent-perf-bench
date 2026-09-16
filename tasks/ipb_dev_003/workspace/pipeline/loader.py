"""Data Loader Module"""

import pandas as pd
from pathlib import Path


class DataLoader:
    """Loads transaction data from various sources."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    def load_transactions(self) -> pd.DataFrame:
        """Load transactions from Parquet file."""
        path = self.data_dir / "transactions.parquet"
        return pd.read_parquet(path)
