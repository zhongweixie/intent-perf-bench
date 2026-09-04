# Fuzzy Variant

图像模糊处理在大尺寸输入和多次 pass 下明显变慢，但输出像素仍然正确。请定位 `solve.c` 中每个像素的热点，关注重复的邻域工作、边界判断以及缓存访问模式。

## Correctness Requirements

- 保持边界 clamp 规则和输出误差容限不变
- **Must use `double` precision for all intermediate computations** - do not change data types to float or other precisions
- The baseline uses `double` throughout; your optimization must maintain bit-exact numerical results
