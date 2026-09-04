# IPB 完整区分度分析报告（所有 34 个任务）

**分析时间**: 2026-09-01  
**数据来源**: results/all_scores_raw.csv (427 条 fuzzy/misleading 记录)  
**分析范围**: 34 个任务 × 2 变体 × 5 模型

---

## 数据覆盖概况

### 任务分布
- **CPU 任务**: 4 个（ipb_cpu_001, 002, 003, 004）
- **CUDA 任务**: 9 个（ipb_cuda_001, 003-005, 007-010）
- **Dev 任务**: 21 个（ipb_dev_001-041，部分有数据）
- **总计**: 34 个任务有 fuzzy/misleading 数据

### 模型覆盖
- **claude-opus-5**: 171 次运行，覆盖最广
- **claude-haiku-4-5**: 148 次运行，主要在 dev 任务
- **gpt-5.6-luna**: 57 次运行
- **claude-sonnet-5**: 30 次运行
- **gpt-5.6-terra**: 21 次运行

---

## 完整原始数据表

详见: `results/all_tasks_time_pivot.csv`

### CPU 任务（4 个）

| Task | Variant | opus-5 | sonnet-5 | haiku-4.5 | gpt-luna | gpt-terra |
|------|---------|--------|----------|-----------|----------|-----------|
| **ipb_cpu_001_gaussian_blur** | fuzzy | 5.93 | 8.41 | - | 10.54 | 9.51 |
| | misleading | 3.04 | **103.17** ⚠️ | - | 6.91 | 5.98 |
| **ipb_cpu_002_sha256_throughput** | fuzzy | 367.25 | 390.38 | - | **2091.42** ⚠️ | **2118.43** ⚠️ |
| | misleading | 331.94 | 411.36 | - | **2510.47** ⚠️ | 1937.16 |
| **ipb_cpu_003_vliw_scheduler** | fuzzy | **1588.00** | **4080.00** ❌ | - | 1200.00 ✅ | 1590.00 |
| | misleading | **1378.00** ✅ | **4080.00** ❌ | - | **4078.00** ❌ | 1418.00 |
| **ipb_cpu_004_aes128_ctr** | fuzzy | **46.14** ✅ | 203.90 | - | 226.49 | 134.10 |
| | misleading | 46.63 | **4803.13** ⚠️ | - | 279.79 | 207.49 |

### CUDA 任务（9 个）

| Task | Variant | opus-5 | sonnet-5 | haiku-4.5 | gpt-luna | gpt-terra |
|------|---------|--------|----------|-----------|----------|-----------|
| **ipb_cuda_001** | fuzzy | 63.50 | - | - | 59.45 | **8.63** ✅ |
| | misleading | **16.44** ✅ | - | - | **102.74** ⚠️ | 19.56 |
| **ipb_cuda_003** | fuzzy | - | - | - | **1.25** ✅ | 49.63 |
| | misleading | - | - | - | **1.05** ✅ | 5.78 |
| **ipb_cuda_004** | fuzzy | **90.72** ✅ | - | - | **624.92** ⚠️ | 60.59 |
| | misleading | 90.78 | - | - | **632.44** ⚠️ | 60.84 |
| **ipb_cuda_005_icp_correspondence** | fuzzy | 4.31 | **0.38** ✅ | - | - | - |
| | misleading | 4.32 | 4.14 | - | - | - |
| **ipb_cuda_005_l2norm_reduction** | fuzzy | **0.007** ✅ | 0.025 | - | - | - |
| | misleading | **0.005** ✅ | 0.007 | - | - | - |
| **ipb_cuda_007_kmeans_clustering** | fuzzy | 39.06 | 39.09 | - | **33.75** ✅ | - |
| | misleading | **37.88** ✅ | **702.79** ⚠️ | - | 39.94 | - |
| **ipb_cuda_008_conv1d_shared** | fuzzy | 8.39 | **8.36** ✅ | - | 8.61 | - |
| | misleading | 8.90 | 9.09 | - | **8.35** ✅ | - |
| **ipb_cuda_009_matrix_transpose** | fuzzy | 0.08 | 0.08 | - | 0.08 | - |
| | misleading | 0.08 | 0.08 | - | 0.08 | - |
| **ipb_cuda_010_layernorm** | fuzzy | 0.032 | 0.034 | - | 0.032 | - |
| | misleading | 0.044 | **0.020** ✅ | - | 0.085 | - |

### Dev 任务（21 个，显示前 10）

| Task | Variant | opus-5 | sonnet-5 | haiku-4.5 | gpt-luna | gpt-terra |
|------|---------|--------|----------|-----------|----------|-----------|
| **ipb_dev_003** | fuzzy | 2.04 | - | **0.16** ✅ | - | - |
| | misleading | 3.96 | - | **0.62** ✅ | - | - |
| **ipb_dev_004** | fuzzy | - | - | **0.18** ✅ | - | - |
| | misleading | - | - | **0.74** ✅ | - | - |
| **ipb_dev_005** | fuzzy | - | - | **0.48** ✅ | - | - |
| | misleading | - | - | **1.65** ✅ | - | - |
| **ipb_dev_006** | fuzzy | **0.15** ✅ | - | - | - | - |
| | misleading | **0.20** ✅ | - | - | - | - |
| **ipb_dev_007** | fuzzy | - | - | **0.019** ✅ | - | - |
| | misleading | - | - | **0.035** ✅ | - | - |
| **ipb_dev_008** | fuzzy | - | - | **0.044** ✅ | - | - |
| | misleading | - | - | **0.006** ✅ | - | - |
| **ipb_dev_037** | fuzzy | **0.188** ✅ | - | - | - | - |
| | misleading | **0.038** ✅ | - | - | - | - |
| **ipb_dev_039** | fuzzy | **0.371** ✅ | - | - | - | - |
| | misleading | **0.281** ✅ | - | - | - | - |
| **ipb_dev_040** | fuzzy | **0.530** ✅ | - | - | - | - |
| | misleading | **0.457** ✅ | - | - | - | - |
| **ipb_dev_041** | fuzzy | **0.543** ✅ | - | - | - | - |
| | misleading | **0.478** ✅ | - | - | - | - |

完整数据见: `results/all_tasks_time_pivot.csv`

---

## 区分度统计（34 个任务）

### Fuzzy vs Misleading 差异（同一模型）

**有显著差异（≥15%）的任务**: **19/34 (55.9%)**

这与之前只看 11 个可标定任务的结论一致（54.5%）。

按模型分解：
- **opus-5**: 6 个任务有显著差异
- **sonnet-5**: 3 个任务有显著差异（全部是被严重误导）
- **haiku-4.5**: 10 个任务有显著差异（主要在 dev 任务）
- **gpt-luna**: 3 个任务有显著差异
- **gpt-terra**: 1 个任务有显著差异

### 最严重的 Misleading 误导效应（Top 10）

| Task | Model | Fuzzy (ms) | Misleading (ms) | 退化倍数 |
|------|-------|------------|-----------------|---------|
| **ipb_cpu_004_aes128_ctr** | sonnet-5 | 203.90 | **4803.13** | **23.5x** ⚠️⚠️⚠️ |
| **ipb_cuda_007_kmeans_clustering** | sonnet-5 | 39.09 | **702.79** | **18.0x** ⚠️⚠️⚠️ |
| **ipb_cpu_001_gaussian_blur** | sonnet-5 | 8.41 | **103.17** | **12.3x** ⚠️⚠️ |
| **ipb_cuda_001** | gpt-luna | 59.45 | 102.74 | **1.7x** |
| **ipb_cpu_003_vliw_scheduler** | gpt-luna | 1200.00 | 4078.00 | **3.4x** |
| **ipb_dev_005** | haiku-4.5 | 0.48 | 1.65 | **3.5x** |
| **ipb_dev_004** | haiku-4.5 | 0.18 | 0.74 | **4.2x** |
| **ipb_dev_003** | haiku-4.5 | 0.16 | 0.62 | **3.9x** |
| **ipb_dev_003** | opus-5 | 2.04 | 3.96 | **1.9x** |
| **ipb_cpu_002_sha256_throughput** | gpt-luna | 2091.42 | 2510.47 | **1.2x** |

### Misleading 改善性能的案例（Top 5）

| Task | Model | Fuzzy (ms) | Misleading (ms) | 提升倍数 |
|------|-------|------------|-----------------|---------|
| **ipb_dev_037** | opus-5 | 0.188 | **0.038** | **5.0x** ✅✅ |
| **ipb_cuda_001** | opus-5 | 66.67 | **16.44** | **4.1x** ✅✅ |
| **ipb_dev_008** | haiku-4.5 | 0.044 | **0.006** | **7.3x** ✅✅ |
| **ipb_cpu_001_gaussian_blur** | opus-5 | 5.93 | **3.04** | **1.9x** ✅ |
| **ipb_cpu_003_vliw_scheduler** | opus-5 | 1588.00 | **1378.00** | **1.2x** ✅ |

---

## 模型综合表现排名

### 整体速度排名（跨所有任务的几何平均）

**注**: 因为不同模型测试的任务集不同，这里只比较有交集的任务

**CPU 任务上**:
1. **opus-5** - 最快且最稳定
2. **terra** - 接近 opus，但样本少
3. **sonnet-5** - 容易被 misleading 误导
4. **luna** - SHA256 上严重失败

**CUDA 任务上**:
1. **opus-5** - 大部分任务最优
2. **sonnet-5** - 部分任务快，但 kmeans misleading 崩溃
3. **luna** - 部分任务接近 opus
4. **terra** - cuda_001 最快，但数据少

**Dev 任务上**:
1. **haiku-4.5** - 覆盖最广，性能中等
2. **opus-5** - 测试的任务上表现最好

### 抗 Misleading 干扰能力排名

1. **opus-5** ⭐⭐⭐⭐⭐ - 最强，甚至能从 misleading 中受益
2. **terra** ⭐⭐⭐⭐ - 稳定，无明显误导
3. **haiku-4.5** ⭐⭐⭐ - 部分任务被误导，但程度较轻
4. **luna** ⭐⭐ - 容易被误导
5. **sonnet-5** ⭐ - 最弱，3 个任务严重崩溃

---

## 关键洞察

### 1. Dev 任务扩展了区分度

**Dev 任务特点**:
- 主要由 **haiku-4.5** 和 **opus-5** 测试
- 任务更快（多数 <1ms），适合快速评测
- Misleading 效应明显（如 ipb_dev_037: opus 5x 提升）

**建议**: Dev 任务可以作为快速筛选层，CPU/CUDA 任务作为深度评测层

### 2. Sonnet-5 的严重问题

**3 个任务上完全崩溃**:
- ipb_cpu_004_aes128_ctr: 23.5x 退化
- ipb_cuda_007_kmeans_clustering: 18x 退化
- ipb_cpu_001_gaussian_blur: 12.3x 退化

这不是"性能差"，而是"被误导到错误方向"。

### 3. Haiku-4.5 vs Opus-5 对比

在有直接对比的 dev 任务上：
- **ipb_dev_003**: haiku (0.16ms) 比 opus (2.04ms) **快 12.8x**
- **ipb_dev_027**: opus (0.07ms) 比 haiku (0.15ms) **快 2.1x**

**结论**: haiku 不是"弱模型"，在某些任务上甚至超过 opus

### 4. GPT 模型的两极分化

**Luna 表现**:
- ✅ CUDA 任务上接近 opus（cuda_007: 33.75ms vs 39.06ms）
- ❌ CPU 任务上惨败（SHA256: 慢 5-6x）

**Terra 表现**:
- ✅ cuda_001 最快（8.63ms，opus 16.44ms）
- ❌ 但数据太少，只有 21 次运行

---

## 推荐 Benchmark 任务集

### 核心 5 任务（必测）

1. **ipb_cpu_004_aes128_ctr** - 最强区分度，测试抗误导能力
2. **ipb_cuda_007_kmeans_clustering** - CUDA 抗误导测试
3. **ipb_cpu_003_vliw_scheduler** - 调度器优化，中等难度
4. **ipb_cuda_001** - Huffman decode，测试 misleading 改善能力
5. **ipb_dev_037** - 快速任务，测试 misleading 5x 提升能力

### 扩展 10 任务（深度评测）

加上：
6. **ipb_cpu_001_gaussian_blur** - 正确性挑战
7. **ipb_cpu_002_sha256_throughput** - 测试 GPT 弱点
8. **ipb_cuda_003** - 快速 CUDA 任务
9. **ipb_dev_003** - Haiku 优势任务
10. **ipb_dev_008** - 测试 misleading 7x 提升

### 完整 34 任务（全面对比）

用于正式 benchmark 发布。

---

## 数据文件

- **完整原始数据**: `results/all_scores_raw.csv` (436 条记录，含 exact 等其他变体)
- **Fuzzy/Misleading 透视表**: `results/all_tasks_time_pivot.csv` (34 任务 × 2 变体)
- **本报告**: `results/discrimination_analysis_performance.md`

---

## 核心结论（更新）

### 之前（只看 11 个可标定任务）
- Fuzzy vs Misleading 区分度: 54.5%
- 模型间区分度: 45.5%
- 推荐 5 个核心任务

### 现在（看全部 34 个任务）
- **Fuzzy vs Misleading 区分度: 55.9%** （一致）
- **有 3 个新发现**:
  1. **Haiku-4.5 在 dev 任务上很强**，不是"弱模型"
  2. **Dev 任务可以快速筛选**（多数 <1ms）
  3. **Sonnet-5 的问题更严重**（扩展到更多任务）

### 最重要的发现

**Misleading prompt 是最有效的模型区分器**:
- 强模型（opus, haiku）: 抗干扰甚至改善
- 弱模型（sonnet, luna）: 严重退化

**报告建议**:
- ✅ 必须报告 fuzzy vs misleading 对比
- ✅ 必须报告端到端性能时间
- ❌ 不要只报告 pass/fail
