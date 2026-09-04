# Exact Variant

优化 `sha256()` 的吞吐，但必须保持 FIPS 180-4 digest 完全一致。请自行通过 profiling 判断消息调度、压缩轮次、CPU 指令路径和块间处理中的主要瓶颈。允许在 `solve.c` 中增加运行时 CPU feature dispatch、SIMD/硬件指令和 scalar fallback；不得修改接口、harness 或 Makefile。
