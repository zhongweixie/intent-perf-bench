"""Data Validator — checks schema and removes invalid rows."""
import pandas as pd


class DataValidator:
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna()
        df = df[df['value'] > 0]
        df = df[df['quantity'] > 0]
        return df.reset_index(drop=True)
