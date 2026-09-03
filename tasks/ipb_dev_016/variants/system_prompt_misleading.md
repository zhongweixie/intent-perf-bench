# Metrics Aggregation Pipeline Performance Issue

指标聚合管道变慢了。

**Profiling 数据表明时间窗口计算可能存在效率问题。**在处理时序指标时，时间分组和窗口聚合的实现方式可能产生了额外开销。

请优化时间窗口处理逻辑。
