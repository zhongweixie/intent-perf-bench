"""Social Media Analytics Pipeline"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from social.loader import PostLoader
from social.scorer import EngagementScorer
from social.aggregator import SocialAggregator

def run_social_pipeline():
    print("=" * 60)
    print("Social Media Analytics Pipeline")
    print("=" * 60)
    t = time.time()
    loader = PostLoader(simulate_io=True)
    posts = loader.load_posts(n=50000)
    print(f"\n[1/3] Load:      {time.time()-t:.4f}s  ({len(posts)} posts)")
    t = time.time()
    scorer = EngagementScorer()
    scored = scorer.compute_engagement(posts)
    print(f"[2/3] Score:     {time.time()-t:.4f}s")
    t = time.time()
    agg = SocialAggregator()
    summary = agg.aggregate_by_platform(scored)
    print(f"[3/3] Aggregate: {time.time()-t:.4f}s")
    return summary

if __name__ == "__main__":
    run_social_pipeline()
