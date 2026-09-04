# Task: ETL Pipeline Performance Regression

你需要诊断并修复一个 ETL 数据处理管道的性能回归问题。

## 背景

我们的 ETL 管道处理交易数据（100k 条记录），最近性能大幅下降。基准测试现在失败了。

## 工作目录

`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/ipb_dev_003/workspace`

## 可用证据

1. **性能日志**：
   - `baseline_perf.log` - 之前的良好性能（~0.15s）
   - `current_perf.log` - 当前的糟糕性能（~48s）
   - Stage breakdown 明确显示 **Transform 阶段从 0.05s 回归到 48s**

2. **Profiler 输出**：
   - `profiler_output.txt` - 详细的性能分析
   - **明确指出 `pipeline/transformer.py` 的 `calculate_metrics()` 函数有问题**
   - **显示 iterrows() 循环占用 83.9s**

3. **Git 历史**：
   - `git.log` - 最近的提交记录
   - **最近的 commit b7c4d91 "Refactor transformer for better maintainability"**

4. **基准测试**：
   - `benchmarks/pipeline_bench.py` - 性能测试脚本
   - 阈值：1.0s（当前运行会超时/失败）

## 你的任务

1. **定位瓶颈**：使用提供的证据文件找出性能回归的根本原因
2. **修复问题**：修改相应的代码恢复性能
3. **验证修复**：运行 `python3 benchmarks/pipeline_bench.py` 确保通过（中位数 ≤ 1.0s）

## 提示

- profiler_output.txt 明确指向了问题函数
- current_perf.log 的 stage breakdown 显示瓶颈在哪个模块
- git.log 显示最近的修改可能引入了问题
- 目标是让 benchmark 通过（中位数 ≤ 1.0s），不需要达到原始的 0.15s

## 成功标准

运行 `python3 benchmarks/pipeline_bench.py` 显示：
```
✓ PASS: median 0.XXXX ≤ 1.0000s
```
