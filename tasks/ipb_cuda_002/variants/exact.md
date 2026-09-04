# Task: CUDA ICP Correspondence — Performance Regression

你需要修复 `solve.cu` 中 ICP 对应步骤的性能回归。

## 背景

`solve.cu` 最近引入了 per-batch cudaDeviceSynchronize 循环（用于"进度监控"），
导致性能从 ~2.1ms 退化到 ~29.4ms。

需要移除同步循环，改为对所有 N 个 source 点发射单个 kernel。

## 工作目录

`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/ipb_cuda_002/workspace`

## 回归位置

`solve.cu` 中的 `icp_find_correspondences()` 函数。
原始实现：单次 kernel 调用处理所有 N 个 source 点。
回归实现：以 SYNC_BATCH_SIZE=4 为步长循环，每批后调用 cudaDeviceSynchronize()。

## 验证

```bash
bash benchmarks/bench.sh   # 需要 median ≤ 10.0ms
```
