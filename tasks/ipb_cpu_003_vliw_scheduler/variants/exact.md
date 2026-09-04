# Exact Variant

优化 `vliw_schedule()` 的总 cycle 数，同时保持每条指令恰好发射一次、slot 类型正确、RAW hazard 安全、寄存器模拟结果完全一致。请分析依赖图、操作延迟、三个 issue slot 的利用率和输入顺序；不得修改 harness、接口或 Makefile。
