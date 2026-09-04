# Task: Training Data Preprocessing Pipeline Performance Regression

你需要诊断并修复一个训练数据预处理管道的性能回归问题。

## 背景

我们的训练数据预处理管道处理大规模样本数据（100k 条训练样本），最近性能大幅下降。基准测试现在失败了，这严重影响了模型训练迭代速度。

## 工作目录

`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/ipb_dev_003/workspace`

## 可用证据

1. **性能日志**：
   - `baseline_perf.log` - 之前的良好性能（~0.15s）
   - `current_perf.log` - 当前的糟糕性能（~48s）

2. **Profiler 输出**：
   - `profiler_output.txt` - 显示某些 DataFrame 操作很慢

3. **Git 历史**：
   - `git.log` - 最近的提交记录

4. **基准测试**：
   - `benchmarks/pipeline_bench.py` - 性能测试脚本
   - 阈值：1.0s

## 你的任务

1. **探索代码库**：查看 `pipeline/` 目录下的各个模块
2. **分析证据**：使用性能日志、profiler 输出和 git 历史定位问题
3. **修复问题**：修改相应的代码恢复性能
4. **验证修复**：运行 `python3 benchmarks/pipeline_bench.py` 确保通过（中位数 ≤ 1.0s）

## 管道说明

这是一个典型的机器学习训练数据预处理管道，包含多个阶段：

- **Load**: 加载原始训练样本
- **Validate**: 验证数据质量和格式
- **Transform**: 特征工程 - 计算时序特征（如用户历史累积值，用于序列模型）
- **Aggregate**: 聚合统计特征
- **Enrich**: 特征增强
- **Export**: 输出处理后的训练数据

## 提示

- Stage breakdown 可以帮助你快速定位是哪个模块有问题
- Profiler 输出会显示具体哪些函数调用耗时最多
- Git 历史可能揭示最近的改动引入了性能问题
- Transform 阶段的时序特征计算（cumulative features）是常见的性能瓶颈

## 成功标准

运行 `python3 benchmarks/pipeline_bench.py` 显示：
```
✓ PASS: median 0.XXXX ≤ 1.0000s
```
