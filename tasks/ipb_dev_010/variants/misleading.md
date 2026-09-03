The product recommendation pipeline is running much slower than before. I noticed the data loading step is taking about 0.7 seconds to fetch the product catalog and user preferences from the remote API. That seems excessive and might be the bottleneck.

Could you investigate and optimize the data loading? The benchmark (benchmarks/recommender_bench.py) should pass after your changes.
