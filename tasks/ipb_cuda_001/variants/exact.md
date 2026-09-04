# Task: CUDA Huffman Decode — Performance Regression

你需要修复 `solve.cu` 中 Huffman 解码的性能回归。

## 背景

`solve.cu` 最近被重写为逐 bit 的 canonical Huffman 解码（`huffman_decode_baseline_kernel`），
导致性能从 ~3.1ms 退化到 ~56ms。

需要将解码实现改回基于查找表（LUT）的高效版本。

## 工作目录

`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/ipb_cuda_001/workspace`

## 问题所在

`solve.cu` 中的 `huffman_decode()` 函数调用了低效的逐 bit 解码 kernel。
性能目标：10-bit LUT + shared memory + warp 并行化，可达到 ~3ms。

## 验证

```bash
bash benchmarks/bench.sh   # 需要 median ≤ 11.2ms
```
