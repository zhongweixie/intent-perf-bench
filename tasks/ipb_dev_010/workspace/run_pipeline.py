"""Product Recommendation Pipeline Runner"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from recommender.loader import DataLoader
from recommender.scorer import ProductScorer
from recommender.aggregator import RecommendationAggregator


def run_recommendation_pipeline():
    """Execute the product recommendation pipeline."""
    t_total = time.time()

    loader = DataLoader(simulate_network=True)
    products, users = loader.load_data(n_users=500, n_products=200)

    scorer = ProductScorer()
    scores = scorer.compute_scores(products, users)

    agg = RecommendationAggregator()
    recommendations = agg.get_top_n(scores, n=5)

    elapsed = time.time() - t_total
    print(f"Pipeline completed in {elapsed:.4f}s")
    print(f"  Products: {len(products)}, Users: {len(users)}")
    print(f"  Recommendations: {len(recommendations)} (top 5 per user)")
    return elapsed


if __name__ == "__main__":
    run_recommendation_pipeline()
