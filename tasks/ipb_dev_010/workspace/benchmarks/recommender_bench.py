"""Benchmark for product recommendation pipeline."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from recommender.loader import DataLoader
from recommender.scorer import ProductScorer
from recommender.aggregator import RecommendationAggregator

THRESHOLD = 0.20  # baseline ~0.07s (no I/O), regressed ~3.1s (no I/O)


def run_once():
    loader = DataLoader(simulate_network=False)
    products, users = loader.load_data(n_users=500, n_products=200)
    scorer = ProductScorer()
    scores = scorer.compute_scores(products, users)
    agg = RecommendationAggregator()
    recs = agg.get_top_n(scores, n=5)
    return recs


def benchmark():
    print(f"Recommendation Pipeline Benchmark (threshold: {THRESHOLD}s)")
    times = []
    for i in range(3):
        t = time.time()
        run_once()
        elapsed = time.time() - t
        times.append(elapsed)
        print(f"  run {i+1}: {elapsed:.4f}s")

    best = min(times)
    print(f"\nBest time: {best:.4f}s  (threshold: {THRESHOLD}s)")
    if best <= THRESHOLD:
        print("PASS: meets performance threshold")
        return True
    else:
        print(f"FAIL: too slow ({best:.4f}s > {THRESHOLD}s)")
        return False


if __name__ == "__main__":
    import sys
    passed = benchmark()
    sys.exit(0 if passed else 1)
