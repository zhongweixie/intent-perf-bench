# Exact Variant

当前 `hash_join()` 对 S 的每条记录完整扫描 R，复杂度为 O(R×S)。请将 build side 建立为适合重复 key 的哈希结构，使 probe 接近 O(R+S)，并精确保持 match_count 与 uint64 checksum 语义。
