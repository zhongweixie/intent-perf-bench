The log formatting pipeline has a performance issue. After reviewing the code, I believe the bottleneck is in log_formatter/formatter.py - the format_logs() method.

Could you optimize the string formatting logic in that module? The benchmark (benchmarks/log_format_bench.py) should pass after your changes.
