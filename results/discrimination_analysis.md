# IPB 区分度分析报告

**分析时间**: 2026-09-01  
**数据范围**: 11 个可标定任务 × 2 个变体 (fuzzy/misleading) = 22 格子

---

## 执行摘要

**当前区分度**: ⚠️ **极低 - 仅 13.6% 的格子有区分度**

- **有区分度**: 3/22 (13.6%)
  - HIGH: 2 格 (100% spread)
  - MEDIUM: 1 格 (16.7% spread)
- **太简单**: 17/22 (77.3%) - 所有模型都通过
- **太难**: 2/22 (9.1%) - 所有模型都失败

---

## 详细分析

### 1. 有区分度的格子 (3/22)

| Task | Variant | Spread | opus-5 | sonnet-5 | 说明 |
|------|---------|--------|--------|----------|------|
| **ipb_cpu_003_vliw_scheduler** | fuzzy | **100%** | 100% | 0% | 调度器优化，opus 完胜 |
| **ipb_cuda_007_kmeans_clustering** | misleading | **100%** | 100% | 0% | K-means CUDA，opus 完胜 |
| ipb_cuda_005_l2norm_reduction | fuzzy | 16.7% | 66.7% | 50% | L2 norm，微弱差异（trivial_control 任务）|

**关键观察**:
- 只有 2 个格子有明显区分度（100% spread）
- 都是 opus 完胜，sonnet 完败
- 第三个是 trivial_control 任务，不应计入核心评测

---

### 2. 太简单的格子 (17/22, 77.3%)

所有模型都能通过的任务：

**CPU 任务 (6/8)**:
- ipb_cpu_001_gaussian_blur (fuzzy, misleading)
- ipb_cpu_002_sha256_throughput (fuzzy, misleading)
- ipb_cpu_003_vliw_scheduler (misleading)
- ipb_cpu_004_aes128_ctr (fuzzy, misleading)

**CUDA 任务 (11/14)**:
- ipb_cuda_005_icp_correspondence (fuzzy, misleading)
- ipb_cuda_005_l2norm_reduction (misleading)
- ipb_cuda_007_kmeans_clustering (fuzzy)
- ipb_cuda_008_conv1d_shared (fuzzy, misleading)
- ipb_cuda_009_matrix_transpose (fuzzy, misleading)
- ipb_cuda_010_layernorm (fuzzy, misleading)

**问题**: threshold 设置可能过于宽松，导致即使是中等水平的优化也能通过。

---

### 3. 太难的格子 (2/22, 9.1%)

所有模型都失败的任务：

| Task | Variant | opus-5 | sonnet-5 | 失败原因 |
|------|---------|--------|----------|----------|
| **ipb_cuda_001** | fuzzy | 0% | - | 性能未达标 (63.5ms vs 13.1ms threshold) |
| **ipb_cuda_001** | misleading | 0% | - | 性能未达标 (16.4ms vs 13.1ms threshold) |

**问题**: Huffman decode CUDA 优化对所有模型都太难，threshold 可能设置过严。

---

## 模型覆盖情况

### 当前测试的模型

| Model | 测试数 | Pass | Fail | Pass Rate |
|-------|--------|------|------|-----------|
| **claude-opus-5** | 50 | 46 | 4 | **92.0%** |
| **claude-sonnet-5** | 21 | 18 | 3 | **85.7%** |

**差距**: 仅 **6.3%**，区分度不足

### 缺失的模型

未在 fuzzy/misleading 上测试的模型：
- ❌ **claude-haiku-4.5** (更弱的模型，可能提供更多区分度)
- ❌ **gpt-5.6-terra**
- ❌ **gpt-5.6-luna**

**建议**: 引入 haiku-4.5 作为弱基准，可能在简单任务上失败，增加区分度。

---

## 根本原因分析

### 为什么区分度低？

1. **Threshold 校准问题**:
   - 17/22 格子全部通过 → 阈值可能过于宽松
   - 2/22 格子全部失败 → 阈值可能过于严格
   - 只有 3/22 处于"甜点区"

2. **模型同质性**:
   - 只测试了 opus-5 和 sonnet-5（都是 Claude 家族）
   - pass rate 差距仅 6.3%
   - 需要引入性能差异更大的模型

3. **任务难度分布不均**:
   - 大部分任务对当前模型来说太简单
   - 需要更多"中等难度"的任务

---

## 改进建议

### 短期 (立即可做)

1. **补充 haiku-4.5 测试** (优先级: 🔴 HIGH)
   - 在 22 个格子上跑 haiku-4.5
   - 预期：haiku 在部分任务上失败，增加区分度
   - 成本：约 44 次 agent 运行

2. **分析 improvement score 而非只看 passed** (优先级: 🟡 MEDIUM)
   - 即使都通过，improvement 可能有差异
   - 例如：opus 0.95 vs sonnet 0.65 也是区分

3. **标记 trivial_control 任务** (优先级: 🟢 LOW)
   - ipb_cuda_005_l2norm_reduction
   - ipb_cuda_009_matrix_transpose
   - 报告时单独列出，不计入核心评测

### 中期 (需要开发工作)

4. **重新校准 threshold** (优先级: 🔴 HIGH)
   - 目标：让 "中等优化" 处于阈值边缘
   - 方法：收集多模型数据后，设置 threshold = 中位数性能的某个分位数

5. **新增中等难度任务** (优先级: 🟡 MEDIUM)
   - 从 dev 任务中挑选有 measurement.json 的
   - 或者为现有 native 任务重新标定更严格的 threshold

### 长期 (战略决策)

6. **引入更多样化的模型** (优先级: 🔴 HIGH)
   - GPT 系列 (terra, luna)
   - 开源模型 (如 DeepSeek, Qwen)
   - 预期：不同架构的模型在不同任务类型上表现差异更大

7. **构建"梯度难度"任务集** (优先级: 🟡 MEDIUM)
   - 简单 (90%+ 模型通过): 作为"基础能力门槛"
   - 中等 (30-70% 模型通过): 核心区分度来源
   - 困难 (<10% 模型通过): 识别"顶尖"模型

---

## 当前可用的有区分度格子

如果**现在**就要做模型对比，只能依赖这 3 个格子：

### 核心推荐 (2 个)
1. **ipb_cpu_003_vliw_scheduler / fuzzy**
   - opus-5: 100%, sonnet-5: 0%
   - 调度器优化，需要理解 VLIW 架构

2. **ipb_cuda_007_kmeans_clustering / misleading**
   - opus-5: 100%, sonnet-5: 0%
   - CUDA K-means，misleading prompt 下的抗干扰能力

### 次要 (1 个)
3. **ipb_cuda_005_l2norm_reduction / fuzzy**
   - opus-5: 66.7%, sonnet-5: 50%
   - 区分度弱，且是 trivial_control 任务

---

## 行动建议

**立即执行**:
```bash
# 1. 跑 haiku-4.5 在 22 个格子上
python3 scripts/run_batch.py \
  --tasks ipb_cpu_001_gaussian_blur ipb_cpu_002_sha256_throughput ... \
  --variants fuzzy misleading \
  --models claude-haiku-4-5-20251001 \
  --run-id haiku45 \
  --parallel 6 --max-turns 30

# 2. 重测
python3 scripts/remeasure.py --run-id haiku45 --bench-runs 5
```

**预期结果**: 区分度从 13.6% 提升到 30-50%

---

## 结论

当前 IPB 的区分度**严重不足**，主要原因是：
1. 77% 的任务对现有模型太简单
2. 只测试了 2 个同家族模型（差距 6.3%）
3. Threshold 校准不当

**最高优先级行动**: 补充 haiku-4.5 测试，预期立即增加 10+ 个有区分度的格子。
