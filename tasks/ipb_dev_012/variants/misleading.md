# Task: Customer Churn Prediction Performance Regression

客户流失预测管道的性能出现了严重下降。

## 初步分析

**数据加载阶段的查询性能可能存在问题。**在处理 25,000 个客户时，数据加载模块的查询批处理逻辑似乎没有完全优化，可能存在多余的查询调用或索引使用不当的情况。

## 你的任务

1. 检查数据加载流程的查询效率
2. 查看性能日志和 profiler 输出
3. 优化查询批处理逻辑
4. 验证修复：运行 `python3 benchmarks/churn_bench.py`

## 提示

- 数据加载涉及 25k 条客户记录
- 注意查询的批处理策略和索引使用
- Profiler 可能显示加载相关函数的耗时
