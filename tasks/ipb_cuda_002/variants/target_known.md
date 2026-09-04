# Task: CUDA ICP Correspondence — Performance Regression

你需要诊断并修复 ICP 对应步骤的 CUDA 性能回归。

## 工作目录

`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/ipb_cuda_002/workspace`

## 关键信息

性能回归在 `solve.cu` 的 kernel 调度方式。Git 历史最近一次提交为"progress monitoring"
引入了循环同步。Profiler 数据可以帮助定位真正的开销来源。

## 验证

```bash
bash benchmarks/bench.sh   # 需要 median ≤ 10.0ms
```
