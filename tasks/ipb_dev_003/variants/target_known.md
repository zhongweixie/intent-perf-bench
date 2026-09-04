# Task: ETL Pipeline Performance Regression

你需要诊断并修复一个 ETL 数据处理管道的性能回归问题。

## 背景

我们的 ETL 管道处理交易数据（100k 条记录），最近性能大幅下降。基准测试现在失败了。

## 工作目录

`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/ipb_dev_003/workspace`

## 已知信息

**性能瓶颈在 `pipeline/transformer.py` 的 `calculate_metrics()` 函数。** 该函数使用了低效的实现方式。

## 可用证据

1. **性能日志**：
   - `baseline_perf.log` - 之前的良好性能（~0.15s）
   - `current_perf.log` - 当前的糟糕性能（~48s）
   - Stage breakdown 显示 Transform 阶段回归

2. **Profiler 输出**：
   - `profiler_output.txt` - 详细的性能分析

3. **Git 历史**：
   - `git.log` - 最近的提交记录

4. **基准测试**：
   - `benchmarks/pipeline_bench.py` - 性能测试脚本
   - 阈值：1.0s

## 你的任务

1. **检查目标文件**：查看 `pipeline/transformer.py` 的 `calculate_metrics()` 函数
2. **识别反模式**：找出低效的实现方式（提示：查找行级迭代）
3. **修复问题**：用向量化操作替换低效实现
4. **验证修复**：运行 `python3 benchmarks/pipeline_bench.py` 确保通过（中位数 ≤ 1.0s）

## 提示

- `calculate_metrics()` 应该使用 pandas 的向量化操作（如 groupby, cumsum）
- 避免使用 iterrows() 或逐行处理
- 原始实现可能使用了 `groupby('customer_id').cumsum()` 的方式

## 成功标准

运行 `python3 benchmarks/pipeline_bench.py` 显示：
```
✓ PASS: median 0.XXXX ≤ 1.0000s
```
