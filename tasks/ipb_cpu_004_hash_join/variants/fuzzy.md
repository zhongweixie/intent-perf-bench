# Fuzzy Variant

连接结果正确但大表查询很慢。检查 `hash_join()` 的复杂度、key 查找的缓存行为和 probe 阶段的重复工作。必须保持 match_count 与 checksum 的 64 位精确语义。
