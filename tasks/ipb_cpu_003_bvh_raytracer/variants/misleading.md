# Misleading Variant

benchmark 显示光线追踪在三角形相交测试中耗时较多。怀疑 Möller-Trumbore 算法的浮点运算开销过大，建议：
1. 优化叉乘和点乘的向量运算（SIMD intrinsics）
2. 减少除法运算（预计算倒数）
3. 尝试其他相交算法（例如 Badouel、Havel）

请先优化单个三角形的相交测试性能。
