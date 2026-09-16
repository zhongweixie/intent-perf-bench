"""Feature Builder Module - REGRESSED VERSION

Computes rolling window statistics for time series forecasting.

REGRESSION: Uses iterrows + row-wise concat (O(n^2) copies)
"""
import pandas as pd


class FeatureBuilder:
    """Build rolling window features from sensor data."""

    def build_features(self, data: pd.DataFrame, window_size: int = 10) -> pd.DataFrame:
        """
        Compute rolling mean/std for each sensor.

        SLOW: iterates over rows and concatenates one by one.
        """
        features = pd.DataFrame()

        for idx, row in data.iterrows():
            sensor_id = row['sensor_id']
            sensor_data = data[data['sensor_id'] == sensor_id].iloc[:idx+1].tail(window_size)

            row_features = row.to_frame().T.copy()
            for col in ['temperature', 'humidity', 'pressure']:
                row_features[f'{col}_rolling_mean'] = sensor_data[col].mean()
                row_features[f'{col}_rolling_std'] = sensor_data[col].std()

            features = pd.concat([features, row_features], ignore_index=True)

        return features
