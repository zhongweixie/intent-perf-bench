# Exact Variant

优化 `aes128_ctr_encrypt()` 的大数据吞吐，同时保持 NIST SP 800-38A CTR 结果完全一致。请分析 key expansion、AES rounds、CTR block independence、CPU AES-NI 可用性和 portable fallback；不得修改接口、测试向量、harness 或 Makefile。
