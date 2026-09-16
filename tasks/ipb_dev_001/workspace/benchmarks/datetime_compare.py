"""
benchmarks/datetime_compare.py — DatetimeArray 比较操作性能基准

这个 benchmark 对应 pandas ASV 套件中的：
    pandas/benchmarks/arithmetic.py::Timeseries.time_series_timestamp_compare

运行方式：
    python workspace/benchmarks/datetime_compare.py

预期输出（baseline，未打 patch 时）：
    平均耗时约 0.8–1.2s / 10次重复（N=10_000_000）
    打 patch 后预期降至 0.4–0.6s（约 2x 加速）

注意：此 benchmark 反映的是 DatetimeArray.__lt__ 的 CPU 耗时，
与 parquet 文件 I/O 无关。
"""

import pandas as pd
import numpy as np
import timeit
import statistics

N = 10_000_000

def setup():
    global arr1, arr2
    base = pd.date_range("2000-01-01", periods=N, freq="s")
    arr1 = base._data                                                   # DatetimeArray
    arr2 = pd.date_range("2000-01-01 00:00:01", periods=N, freq="s")._data

def workload():
    global arr1, arr2
    arr1 < arr2                                                         # DatetimeArray comparison

setup()
runtimes = timeit.repeat(workload, number=10, repeat=25)

print(f"N = {N:,}")
print(f"Mean:   {statistics.mean(runtimes):.4f}s (×10 repeats)")
print(f"Median: {statistics.median(runtimes):.4f}s")
print(f"StdDev: {statistics.stdev(runtimes):.4f}s")
print(f"CV:     {statistics.stdev(runtimes)/statistics.mean(runtimes):.3f}")
