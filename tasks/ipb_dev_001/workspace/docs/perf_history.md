# 每日报表性能历史记录

此文档记录 `daily_report.py` 在不同 pandas 版本下的典型运行时间，
供性能回归排查参考。

## 基准配置

- 机器：4-core CPU，16GB RAM
- 数据规模：10M 行交易记录 + 50K 账户参考表
- 测量方式：运行 3 次取中位数

## 版本时间线

| pandas 版本 | 日期 | 总耗时 (s) | 说明 |
|---|---|---|---|
| 1.0.5 | 2020-08 | 1.82 | 基准版本 |
| 1.1.0 | 2020-09 | 1.84 | 无明显变化 |
| 1.1.3 | 2020-11 | **3.41** | 🔴 性能下降，约慢 1.85x |
| 1.2.0 | 2021-01 | — | 待测 |

## 2020-11 回归分析（待完成）

在升级到 1.1.3 后，`daily_report.py` 耗时从约 1.82s 增长到约 3.41s。

初步排查记录：

**@alice-ops（2020-11-15）：**
> 我用 `time python scripts/daily_report.py` 测了几次，
> 慢了将近一倍。先看了下 parquet 读取，用 `py-spy` 跑了一下，
> 发现读 `transactions.parquet` 大概花了 0.2s 左右。
> 感觉可能是最近 fastparquet 或 pyarrow 的什么变化？

**@bob-dev（2020-11-16）：**
> 我也跑了一下，parquet 那块确实有点慢，不过感觉不够解释整体慢这么多。
> 后面的处理部分也变慢了，还没具体定位到哪里。

**@charlie-perf（2020-11-18）：**
> 待排查：使用 cProfile 或 py-spy 对完整 workload 做 profiling，
> 定位哪个函数占用最多 CPU 时间。

---

**结论：尚未确定根本原因。** 请参见 benchmarks/datetime_compare.py 中的隔离基准，
以及 .github/workflows/performance.yml 中的验收阈值（要求相对 1.1.0 基准达到 1.5x 加速）。
