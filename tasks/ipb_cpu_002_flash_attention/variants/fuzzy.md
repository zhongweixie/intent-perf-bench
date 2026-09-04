# Fuzzy Variant

长序列 attention 推理速度低于预期，数值结果基本正确。检查 `attention()` 的中间存储、softmax 多次遍历和 Q/K/V 的缓存局部性。优化必须保留函数签名及验证输出的数值容限。
