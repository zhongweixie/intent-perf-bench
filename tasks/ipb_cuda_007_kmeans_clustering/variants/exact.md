# Task: CUDA K-Means Clustering — Performance Regression

你需要修复 `solution.cu` 中 K-Means 聚类的性能回归。

## 背景

K-Means 实现最近被重构，移除了共享内存优化，导致性能从 ~35ms 退化到 ~42ms。
虽然正确性测试仍然通过，但性能已无法满足生产需求。

需要恢复基于共享内存 tiling 的优化版本。

## 工作目录

`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/ipb_cuda_007_kmeans_clustering/workspace`

## 问题所在

`solution.cu` 中的 `k_assignClusters` kernel 直接从全局内存读取质心坐标，
没有利用共享内存缓存，导致内存访问效率低下。

性能目标：使用共享内存 tiling 缓存质心数据，减少全局内存访问，可达到 ~36ms 以下。

## 验证

编译并运行性能测试：
```bash
make clean && make
./kmeans_test          # 正确性检查（必须通过）
./kmeans_test --perf   # 性能测试（需要达到阈值）
```

性能要求：中位数运行时间需显著低于 baseline（~42ms）。
