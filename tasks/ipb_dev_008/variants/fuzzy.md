Our AI training log monitoring pipeline has been running slower than before. We collect logs from distributed training jobs (30,000 log entries per job from multiple nodes) and format them for real-time monitoring dashboards.

Something changed recently and now the log formatting stage takes much longer to process the same amount of data. This is blocking our ability to monitor training runs in real-time.

Could you look into what's causing the slowdown and fix it? The benchmark (benchmarks/log_format_bench.py) should pass after your changes.

Context: The pipeline formats structured log entries into human-readable text for monitoring dashboards that track training metrics, errors, and system health across distributed training nodes.
