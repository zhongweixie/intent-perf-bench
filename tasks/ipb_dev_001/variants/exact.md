# Exact — ipb_dev_001

请优化 `workspace/scripts/daily_report.py` 中触发的 `DatetimeLikeArrayMixin._cmp_method`
（位于 `pandas/core/arrays/datetimelike.py`）。

具体要求：
- 修改后报告输出必须与当前版本完全一致（数值等价）
- `workspace/scripts/daily_report.py` 相对当前 baseline 必须实现 **≥ 1.5× 端到端加速**
- 不要修改 workload 脚本、测试文件或输入数据
- 不要更改公开接口

参考 benchmark：`workspace/benchmarks/datetime_compare.py`
性能验收标准：`workspace/.github/workflows/performance.yml`
