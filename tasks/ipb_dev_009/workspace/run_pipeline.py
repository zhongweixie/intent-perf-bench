"""Feature Engineering Pipeline Runner

Orchestrates the full feature engineering workflow.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from feature_eng.loader import DataLoader
from feature_eng.builder import FeatureBuilder
from feature_eng.validator import FeatureValidator
from feature_eng.exporter import FeatureExporter


def run_feature_pipeline():
    """Run the complete feature engineering pipeline."""
    print("=" * 70)
    print("Feature Engineering Pipeline")
    print("=" * 70)

    # Stage 1: Load raw data
    print("\n[1/4] Loading transaction data...")
    t = time.time()
    loader = DataLoader(simulate_io=True)
    data = loader.load_transactions(n_rows=100000)
    stage1_time = time.time() - t
    print(f"      Loaded {len(data)} transactions in {stage1_time:.4f}s")

    # Stage 2: Build features
    print("\n[2/4] Building features...")
    t = time.time()
    builder = FeatureBuilder()
    features = builder.build_features(data)
    stage2_time = time.time() - t
    print(f"      Built {len(features.columns)} features in {stage2_time:.4f}s")

    # Stage 3: Validate
    print("\n[3/4] Validating features...")
    t = time.time()
    validator = FeatureValidator()
    checks = validator.validate_features(features)
    stage3_time = time.time() - t
    print(f"      Validation complete in {stage3_time:.4f}s")
    print(f"      Checks: {checks}")

    # Stage 4: Export
    print("\n[4/4] Exporting features...")
    t = time.time()
    exporter = FeatureExporter()
    summary = exporter.export_features(features)
    stage4_time = time.time() - t
    print(f"      {summary} in {stage4_time:.4f}s")

    total_time = stage1_time + stage2_time + stage3_time + stage4_time
    print("\n" + "=" * 70)
    print(f"Pipeline completed in {total_time:.4f}s")
    print("=" * 70)
    return total_time


if __name__ == "__main__":
    run_feature_pipeline()
