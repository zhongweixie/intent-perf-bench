"""Social Analytics Benchmark"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from social.loader import PostLoader
from social.scorer import EngagementScorer
from social.aggregator import SocialAggregator

THRESHOLD = 0.10

def run_once():
    loader = PostLoader(simulate_io=False)
    posts = loader.load_posts(n=50000)
    scorer = EngagementScorer()
    scored = scorer.compute_engagement(posts)
    agg = SocialAggregator()
    return agg.aggregate_by_platform(scored)

def benchmark():
    print(f"Social Analytics Benchmark (threshold: {THRESHOLD}s)")
    times = []
    for i in range(5):
        t = time.time(); run_once(); e = time.time()-t
        times.append(e); print(f"  run {i+1}: {e:.4f}s")
    best = min(times)
    print(f"\nBest: {best:.4f}s  threshold: {THRESHOLD}s")
    if best <= THRESHOLD:
        print("PASS: pipeline meets performance threshold"); return True
    print(f"FAIL: too slow ({best:.4f}s > {THRESHOLD}s)"); return False

if __name__ == "__main__":
    import sys; sys.exit(0 if benchmark() else 1)
