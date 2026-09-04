# Task: CUDA Huffman Decode — Performance Regression

你需要诊断并修复一个 CUDA Huffman 解码管道的性能回归问题。

## 背景

该系统对大量压缩比特流进行并行 Huffman 解码（2048 路独立码流，每路 64KB 解码输出）。
最近性能大幅下降，基准测试失败。

## 工作目录

`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/ipb_cuda_001/workspace`

## 关键信息

回归点在 `solve.cu` 的 kernel 实现。git 历史显示最近一次提交将 LUT-based 解码
替换成了逐 bit 解码。

## 可用证据

1. `baseline_perf.log` / `current_perf.log` — 性能对比
2. `git.log` — 最近的提交记录
3. `profiler_output.txt` — 运行时 profile

## 验证

```bash
bash benchmarks/bench.sh   # 需要 median ≤ 11.2ms
```
