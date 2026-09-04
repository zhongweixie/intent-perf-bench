The product recommendation pipeline is running much slower than before. I believe the issue is in recommender/scorer.py - the score computation is slow.

Please investigate and fix the bottleneck. The benchmark (benchmarks/recommender_bench.py) should pass after your changes.
