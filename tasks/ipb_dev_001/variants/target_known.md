# Target-known — ipb_dev_001

`daily_report.py` 中的 timestamp 比较步骤（`tx_time > deadline`）
在最近 pandas 升级后明显变慢了。请优化对应的 DatetimeArray 比较实现。

要求：
- 报告输出结果不能变化
- 不要修改测试文件和 workload 脚本
- 完成标准请按仓库中现有的性能要求执行（见 `workspace/.github/workflows/performance.yml`）

workspace 中有独立 benchmark 可帮助你定位和验证效果。
