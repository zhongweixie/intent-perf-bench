"""Feature Validator Module

Validates feature engineering output.
"""
import pandas as pd


class FeatureValidator:
    """Validate computed features."""

    def validate_features(self, features: pd.DataFrame) -> dict:
        """Run validation checks on feature output."""
        checks = {
            'null_count': features.isnull().sum().sum(),
            'total_rows': len(features),
            'feature_count': len(features.columns),
            'has_negatives': (features.select_dtypes(include=['number']) < 0).any().any(),
        }
        return checks
