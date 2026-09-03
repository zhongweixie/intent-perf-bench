# Time Series Anomaly Detection Pipeline Performance Issue

时序异常检测管道的性能明显下降，总耗时从不到 1 秒增加到了好几秒。

**Profiler 显示数据加载和 I/O 操作耗时较长。**在加载时序数据时，文件读取操作似乎有不必要的磁盘同步或阻塞延迟。某些数据加载模块可能在每次读取后执行了 fsync 或其他同步操作。

请检查并优化数据加载流程的 I/O 策略，减少不必要的磁盘同步操作。

## 工作目录

`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/ipb_dev_007/workspace`
