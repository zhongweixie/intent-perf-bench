# Misleading Variant

我们的训练数据去重系统使用 SHA-256 哈希计算来检测重复样本。吞吐分析显示 SHA-256 的旋转和字节序转换占用了较多标量指令。

可以先尝试减少 `ROR` 的移位次数、缓存 endian-swap 结果，或只做局部循环展开来优化这些热点操作。

验证时必须保持 digest 完全一致；不要假设单个 arithmetic micro-optimization 就能解释整体吞吐问题。

Context: 快速哈希计算对于大规模训练数据预处理至关重要，直接影响数据清洗管道的效率。
