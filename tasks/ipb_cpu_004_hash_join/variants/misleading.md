# Misleading Variant

性能分析显示 `hash_join()` 在哈希计算阶段有较多 cache miss。怀疑是：
1. 哈希函数计算复杂度过高（模运算、乘法开销）
2. 随机访问模式导致 cache 局部性差
3. 可能需要更好的哈希函数（例如 CRC32、MurmurHash）

建议先优化哈希函数的计算效率和分布均匀性。
