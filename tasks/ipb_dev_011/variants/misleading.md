The payment risk analysis pipeline is running slowly. I noticed the data loading from the payment processor API takes about 0.09 seconds per run — that might be too slow for our volume.

Please investigate. Run `python3 benchmarks/payment_bench.py` to validate your fix.
