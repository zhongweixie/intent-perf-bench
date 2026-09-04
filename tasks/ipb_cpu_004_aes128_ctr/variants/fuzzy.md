# Fuzzy Variant

大块 CTR 加密的结果正确但吞吐不足。请从完整实现定位瓶颈：包括 key schedule 是否重复、每个 block 的 round 工作、counter 生成、独立 block 的并行度、内存访问以及运行时指令集选择。保持所有 NIST 向量和任意长度输入正确。
