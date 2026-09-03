# Task: Training Data Preprocessing Pipeline Performance Regression

你需要诊断并修复一个训练数据预处理管道的性能回归问题。

## 背景

我们的训练数据预处理管道处理大规模样本数据（100k 条训练样本），最近性能大幅下降。基准测试现在失败了。

**初步分析表明聚合和导出阶段存在重复的内存拷贝。**在处理 100k 条样本时，聚合模块（aggregate）和导出模块（export）似乎对 DataFrame 进行了不必要的 `.copy()` 操作，导致内存占用飙升和额外的拷贝开销。某些中间结果可能被重复复制了多次。

## 工作目录

`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/ipb_dev_003/workspace`

## 可用证据

1. **性能日志**：
   - `baseline_perf.log` - 之前的良好性能（~0.15s）
   - `current_perf.log` - 当前的糟糕性能（~48s）

2. **Profiler 输出**：
   - `profiler_output.txt` - 显示某些操作很慢

3. **Git 历史**：
   - `git.log` - 最近的提交记录

4. **基准测试**：
   - `benchmarks/pipeline_bench.py` - 性能测试脚本
   - 阈值：1.0s

## 你的任务

1. **分析聚合和导出模块**：检查 aggregate 和 export 模块是否有不必要的 `.copy()` 调用
2. **查看证据文件**：使用性能日志和 profiler 输出定位问题
3. **优化内存使用**：减少重复的 DataFrame 拷贝操作
4. **验证修复**：运行 `python3 benchmarks/pipeline_bench.py` 确保通过（中位数 ≤ 1.0s）

## 管道说明

这是一个机器学习训练数据预处理管道，包含多个阶段：

- **Load**: 加载原始训练样本
- **Validate**: 验证数据质量
- **Transform**: 特征工程
- **Aggregate**: 聚合统计
- **Enrich**: 特征增强
- **Export**: 输出处理后的数据

## 提示

- 聚合和导出阶段处理 100k 条样本，频繁的 DataFrame.copy() 会严重影响性能
- 检查这两个模块是否有防御性的拷贝操作
- Profiler 输出可能显示内存分配相关的耗时

## 成功标准

运行 `python3 benchmarks/pipeline_bench.py` 显示：
```
✓ PASS: median 0.XXXX ≤ 1.0000s
```
