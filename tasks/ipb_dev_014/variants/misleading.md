You are working in the provided workspace to investigate and resolve a performance issue.

The customer analytics pipeline has become slower. Initial investigation suggests the data loading stage may be the bottleneck — loading 40,000 customer records takes around 0.12-0.15s from the database.

**Note**: The loading involves a database query that fetches customer records with multiple joins (customers, orders, transactions). This might be causing I/O overhead. Consider optimizing the query or adding database indices.

Available tools:
- **benchmarks/analytics_bench.py** — performance test  
- **run_pipeline.py** — full pipeline runner
- Code files in customer_analytics/

Investigate and fix the performance issue.

Working directory: tasks/ipb_dev_014/workspace/
