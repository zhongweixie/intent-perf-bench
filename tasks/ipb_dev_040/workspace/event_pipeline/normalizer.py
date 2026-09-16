"""Event Normalizer — stage 2 with four performance fixes applied."""
import re
import json
import pathlib
import pandas as pd


_CONFIG_PATH = str(pathlib.Path(__file__).parent.parent / 'event_config.json')

# Fix 3: Load config once at import time instead of on every normalize() call.
with open(_CONFIG_PATH) as _f:
    _CONFIG = json.load(_f)

# Fix 2: Pre-compile the tag regex once at module level.
_TAG_PAT = re.compile(r'tag_(\d+)')


class EventNormalizer:
    """Normalize raw event records: parse dates, extract tags, filter, label."""

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Fix 1: pd.to_datetime() vectorized — replaces 100k strptime() calls.
        event_dates = pd.to_datetime(df['event_date'], format="%Y-%m-%d")
        df['event_date']  = event_dates
        df['event_month'] = event_dates.dt.month
        df['event_dow']   = event_dates.dt.weekday   # Monday=0, same as .weekday()

        # Fix 2: .str.extract() with the pre-compiled pattern — replaces two
        #         re.findall() calls per row in a Python loop.
        df['tag_id'] = (
            df['raw_tag']
            .str.extract(_TAG_PAT, expand=False)
            .fillna(-1)
            .astype(int)
        )

        # Fix 3: use module-level config (loaded once above).
        valid_sources = set(_CONFIG.get('valid_sources', []))
        df = df[df['source'].isin(valid_sources)]

        # Fix 4: vectorized Series string concatenation — replaces per-row loop.
        df['event_label'] = (
            'type=' + df['event_type']
            + ' src=' + df['source']
            + ' tag=' + df['tag_id'].astype(str)
        )

        return df.reset_index(drop=True)
