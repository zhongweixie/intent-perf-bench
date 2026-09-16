# Performance History — daily_report.py

## Recent observations

The daily report generation has been slower than expected over the past few weeks.
Operations noticed the dashboard refresh is taking longer in staging, and the CI
performance gate has started failing intermittently.

Historical performance was stable for several months. Recent changes include:
- Migration from CSV to Parquet for data storage
- Addition of return_rate KPI to the summary metrics
- Code refactoring for maintainability

## SLO

Operations dashboard must refresh within 5 s end-to-end.
`compute_regional_summary` should complete in a reasonable time for
the data volumes we typically process (~5 million transactions, ~1 000 stores).

The team suspects the performance issue may be related to how we're loading
the transaction data, since we recently migrated to Parquet format.
