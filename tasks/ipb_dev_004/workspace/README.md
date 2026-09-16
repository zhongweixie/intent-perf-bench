# Data Analytics Library - Performance Regression

这是一个数据分析库，用于加载、聚合和报告业务指标。

## 项目结构

```
analytics/
├── loader.py       - 数据加载模块
├── aggregator.py   - 数据聚合模块 (CAUSAL FILE)
├── reporter.py     - 报告生成模块
├── validator.py    - 数据验证模块
├── filters.py      - 数据过滤模块
└── utils.py        - 工具函数
```

## 已知问题

最近的代码重构后，数据分析流程变慢了。需要诊断并修复性能回归。

## 运行基准测试

```bash
python3 benchmarks/analytics_bench.py
```

基准测试应该在 1 秒内完成。
