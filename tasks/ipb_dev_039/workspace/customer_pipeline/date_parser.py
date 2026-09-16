"""Date Parser — parses purchase_date strings into datetime objects.

Uses pd.to_datetime for vectorised C-level parsing, eliminating the
per-call format re-parsing overhead of datetime.strptime.
"""
import pandas as pd


class DateParser:
    def parse(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # Vectorised parsing: pd.to_datetime avoids re-parsing the format
        # string on every row (unlike datetime.strptime in a list comprehension)
        parsed = pd.to_datetime(df['purchase_date'], format='%Y-%m-%d')
        df['purchase_date'] = parsed
        df['purchase_month'] = parsed.dt.month
        df['purchase_quarter'] = (parsed.dt.month - 1) // 3 + 1
        return df
