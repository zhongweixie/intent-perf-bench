# Opus5 Fuzzy/Misleading 评测最终报告

**目标**: 用 opus5 跑所有可标定任务的 fuzzy/misleading 变体

**执行时间**: 2026-08-31 ~ 2026-09-01

**状态**: ✅ **已完成** - 22/22 格子全部成功测量

---

## 执行摘要

- **成功率**: 22/22 (100%)
- **通过率**: 18/22 (81.8%)
- **失败率**: 4/22 (18.2%)
- **Improvement 均值**: 0.875 (n=20，有效值平均 0.969)

---

## 完整结果表

| Task                              | Variant    | Passed | Median (ms) | Improvement | Reason if Failed |
|-----------------------------------|------------|--------|-------------|-------------|------------------|
| ipb_cpu_001_gaussian_blur         | fuzzy      | ❌ False | 5.93      | -           | 正确性失败 |
| ipb_cpu_001_gaussian_blur         | misleading | ❌ False | 3.04      | -           | 正确性失败 |
| ipb_cpu_002_sha256_throughput     | fuzzy      | ✅ True | 367.25    | 1.000       | |
| ipb_cpu_002_sha256_throughput     | misleading | ✅ True | 331.94    | 1.000       | |
| ipb_cpu_003_vliw_scheduler        | fuzzy      | ✅ True | 1588.00   | 0.865       | |
| ipb_cpu_003_vliw_scheduler        | misleading | ✅ True | 1378.00   | 0.938       | |
| ipb_cpu_004_aes128_ctr            | fuzzy      | ✅ True | 46.14     | 1.000       | |
| ipb_cpu_004_aes128_ctr            | misleading | ✅ True | 46.63     | 1.000       | |
| ipb_cuda_001                      | fuzzy      | ❌ False | 63.50     | -           | 未达阈值 13.1ms |
| ipb_cuda_001                      | misleading | ❌ False | 16.44     | -           | 未达阈值 13.1ms |
| ipb_cuda_005_icp_correspondence   | fuzzy      | ✅ True | 4.31      | 0.938       | |
| ipb_cuda_005_icp_correspondence   | misleading | ✅ True | 4.32      | 0.938       | |
| ipb_cuda_005_l2norm_reduction     | fuzzy      | ✅ True | 0.01      | 1.000       | |
| ipb_cuda_005_l2norm_reduction     | misleading | ✅ True | 0.01      | 1.000       | |
| ipb_cuda_007_kmeans_clustering    | fuzzy      | ✅ True | 39.06     | 0.984       | |
| ipb_cuda_007_kmeans_clustering    | misleading | ✅ True | 37.88     | 1.000       | |
| ipb_cuda_008_conv1d_shared        | fuzzy      | ✅ True | 8.39      | 1.000       | |
| ipb_cuda_008_conv1d_shared        | misleading | ✅ True | 8.90      | 1.000       | |
| ipb_cuda_009_matrix_transpose     | fuzzy      | ✅ True | 0.08      | 1.000       | |
| ipb_cuda_009_matrix_transpose     | misleading | ✅ True | 0.08      | 1.000       | |
| ipb_cuda_010_layernorm            | fuzzy      | ✅ True | 0.03      | 0.945       | |
| ipb_cuda_010_layernorm            | misleading | ✅ True | 0.04      | 0.882       | |

---

## 失败分析

### 1. ipb_cpu_001_gaussian_blur (fuzzy & misleading)
- **原因**: 正确性检查失败 (`correctness_ok=False`)
- **性能**: 5.9ms (fuzzy) 和 3.0ms (misleading)，远快于 threshold 45.6ms
- **结论**: Agent 优化破坏了正确性。任务有 `output_check`，要求输出文件与预期的二进制文件匹配。

### 2. ipb_cuda_001 (fuzzy & misleading)
- **原因**: 正确性通过，但性能未达阈值
- **Fuzzy**: 63.5ms vs threshold 13.1ms (baseline 65.4ms)
- **Misleading**: 16.4ms vs threshold 13.1ms (比 fuzzy 好 3.9x)
- **结论**: Agent 在这个任务上做了部分优化但不够。Misleading 提示更有效。

---

## 按任务类型统计

### CPU 任务 (4 tasks, 8 cells)
- 成功: 8/8
- Passed: 6/8 (75.0%)
- Failed: 2/8 (ipb_cpu_001 两变体，正确性失败)
- 平均 improvement (passed): 0.967

### CUDA 任务 (7 tasks, 14 cells)
- 成功: 14/14
- Passed: 12/14 (85.7%)
- Failed: 2/14 (ipb_cuda_001 两变体，性能未达标)
- 平均 improvement (passed): 0.971

### Trivial Control 任务
这两个任务标记为 `trivial_control`，应与主任务分开统计：
- ipb_cuda_005_l2norm_reduction: fuzzy 1.000, misleading 1.000
- ipb_cuda_009_matrix_transpose: fuzzy 1.000, misleading 1.000

---

## 关键发现

### 1. Fuzzy vs Misleading 对比

| Task                          | Fuzzy Passed | Misleading Passed | Winner     |
|-------------------------------|--------------|-------------------|------------|
| ipb_cpu_001_gaussian_blur     | ❌           | ❌                | Tie (both failed) |
| ipb_cpu_002_sha256_throughput | ✅           | ✅                | Tie        |
| ipb_cpu_003_vliw_scheduler    | ✅           | ✅                | **Misleading** (1378ms vs 1588ms) |
| ipb_cpu_004_aes128_ctr        | ✅           | ✅                | Tie        |
| ipb_cuda_001                  | ❌           | ❌                | **Misleading** (16.4ms vs 63.5ms) |
| ipb_cuda_005_icp_correspondence | ✅         | ✅                | Tie        |
| ipb_cuda_005_l2norm_reduction | ✅           | ✅                | Tie        |
| ipb_cuda_007_kmeans_clustering | ✅          | ✅                | **Misleading** (37.9ms vs 39.1ms) |
| ipb_cuda_008_conv1d_shared    | ✅           | ✅                | Tie        |
| ipb_cuda_009_matrix_transpose | ✅           | ✅                | Tie        |
| ipb_cuda_010_layernorm        | ✅           | ✅                | **Fuzzy** (0.03ms vs 0.04ms) |

**结论**: Misleading 在 3 个任务上更好，Fuzzy 在 1 个任务上更好，其余平局。

### 2. Bug 修复记录

**Bug #1: ipb_measure.py srun 环境变量传递错误**
- **症状**: `execve(): HUFFMAN_DECODE_SEED=0xc0ffee42: No such file or directory`
- **根本原因**: `bench_env` 的 `KEY=VALUE` 直接拼接到命令字符串，被 srun 当成可执行文件名
- **修复**: 改用 `export KEY=VALUE &&` 在 bash 中设置环境变量
- **位置**: `scripts/ipb_measure.py:63-67`
- **影响**: ipb_cuda_001 等所有使用 `bench_env` 的 CUDA 任务

**Bug #2: remeasure.py workspace 选择错误**
- **症状**: ipb_cpu_004_aes128_ctr fuzzy 测出 4805ms，与 agent 报告的 48ms 相差 100 倍
- **根本原因**: 使用 `sorted(holders)[-1]` 按字典序取 workspace，而非按时间戳取最新的（retry 后的）
- **修复**: 改用 `max(holders, key=lambda p: os.path.getmtime(p))`
- **影响**: 所有 retry 批次的任务

---

## 技术细节

### 执行流程
1. **并发 agent 运行** (`run_batch.py --parallel 6`):
   - 第一批次: 22 格，18 成功，4 失败（API 502）
   - Retry 批次: 6 格，全部成功
   - Agent 结果文件: `results/*_o5*_claude-opus-5.json`

2. **串行重测** (`remeasure.py --bench-runs 5`):
   - 从保留的 workspace 重新 build/verify/benchmark
   - 排除并发测量时的相互干扰
   - 权威分数来源

3. **Bug 修复与重建**:
   - 修复 srun 环境变量传递
   - 修复 workspace 选择逻辑
   - 完整重测 22 格

### 数据文件
- **agent 原始结果**: `results/ipb_*_*_o5*_claude-opus-5.json` (22 个)
- **重测结果**: `results/remeasure_o5_final.json`
- **保留 workspace**: `.scratch/batch_o5/*/workspace`
- **本报告**: `results/opus5_fuzzy_misleading_FINAL.md`

### 测量参数
- `--max-turns 30`
- `--bench-runs 3` (agent 内), `5` (remeasure)
- `--timeout 3600`
- Model: `claude-opus-5`

---

## 结论

✅ **目标完成**: 22/22 格子全部成功测量，18/22 passed (81.8%)

**Opus5 表现总结**:
- 在 SHA256、AES、调度器、CUDA kernel 等任务上表现优异
- 18/22 通过，improvement 均值 0.875（有效值 0.969）
- Misleading prompt 在部分任务上略优于 fuzzy
- 两个失败点：正确性破坏（gaussian_blur）和优化不足（cuda_001）

**后续工作**（非本次目标）:
- 分析 ipb_cpu_001_gaussian_blur 为何破坏正确性
- 改进 ipb_cuda_001 的 prompt 或给 agent 更多轮次
- 对比其他模型（haiku, sonnet, gpt）在相同任务上的表现
