# Flash Attention Performance Issue

Attention 计算的性能出现了下降。

**Profiling 显示 softmax 归一化阶段可能存在计算效率问题。**在处理大规模 attention 矩阵时，数值稳定性处理和归一化计算似乎产生了额外的开销。

请检查 softmax 实现，优化归一化计算逻辑。
