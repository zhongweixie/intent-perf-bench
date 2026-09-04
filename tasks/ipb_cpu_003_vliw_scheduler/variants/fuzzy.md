# Fuzzy Variant

VLIW 计划器在 adversarial instruction stream 上 cycle 数明显偏高。不要只按输入顺序逐条发射；从操作依赖、三种 slot 的可用性、MUL/MEM latency 和 ready 时机整体分析。正确性包括 hazard、每个 id 一次以及最终寄存器状态。
