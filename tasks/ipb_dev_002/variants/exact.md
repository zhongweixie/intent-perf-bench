# Exact — ipb_dev_002

`scripts/daily_report.py` 中的 `compute_regional_summary` 函数在
commit a3f2c89（2026-07-18）被重构为使用 `groupby.apply(_store_kpis)`，
引入了性能回归：每次调用都会对 1 000 个 store 各构造一个 `pd.Series` 对象，
累计产生大量 Python 对象开销。

具体要求：
- 将 `compute_regional_summary` 改为 `df.groupby("store_id").agg(named_aggregations)`
- 修改后 `compute_regional_summary` 的 median 运行时间须 **≤ 0.1428 s**（即比当前快 ≥ 1.5×）
- 返回结果的数值必须与修改前一致（dtypes 的细微差异可接受）
- 不要修改 workload 脚本的其他部分、测试文件或输入数据

参考：
- Benchmark : `benchmarks/report_bench.py`
- 阈值定义  : `.github/workflows/performance.yml`
- Profiler  : `profiler_output.txt`
