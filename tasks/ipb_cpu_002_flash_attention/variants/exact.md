# Exact Variant

`attention()` 当前会物化 double 类型的 n×n score 和 probability 矩阵，并对 softmax 与输出执行多次全量遍历。请实现 tiled/online-softmax 方向的优化，减少中间内存和流量，同时保持 scaled dot-product attention 的数学语义和验证精度。
