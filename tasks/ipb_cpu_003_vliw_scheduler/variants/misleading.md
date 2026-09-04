# Misleading Variant

profile 中相交测试的叉乘、点乘和除法耗时明显。可以先尝试手工展开向量运算、预计算倒数，或用 SIMD 改写单三角形测试。保持最近邻、阈值和统计量语义不变；不要仅根据局部 kernel 指标判断整体 correspondence pipeline 的瓶颈。
