"""Data Exporter Module"""

import pandas as pd
from pathlib import Path


class DataExporter:
    """Exports processed data to output formats."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export_to_csv(self, df: pd.DataFrame, filename: str) -> None:
        """Export DataFrame to CSV."""
        path = self.output_dir / filename
        df.to_csv(path, index=False)
        print(f"Exported {len(df)} rows to {path}")

    def export_to_parquet(self, df: pd.DataFrame, filename: str) -> None:
        """Export DataFrame to Parquet."""
        path = self.output_dir / filename
        df.to_parquet(path, index=False)
        print(f"Exported {len(df)} rows to {path}")

    def export_summary_stats(self, df: pd.DataFrame, filename: str = "summary.txt") -> None:
        """Export summary statistics."""
        path = self.output_dir / filename
        
        with open(path, 'w') as f:
            f.write("Data Summary Statistics\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total records: {len(df)}\n")
            f.write(f"Columns: {', '.join(df.columns)}\n")
            f.write(f"Memory usage: {df.memory_usage(deep=False).sum() / 1024**2:.2f} MB\n")

        print(f"Exported summary to {path}")
