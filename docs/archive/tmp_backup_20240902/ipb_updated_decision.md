# IPB 任务分析 - 更新决策

**日期**: 2026-09-01  
**状态**: 用户反馈后更新

---

## 用户决策更新

### ✅ **保留区分度最高的 3 个 CPU 任务**

用户要求："先把区分度最高的3个先保留吧，因为毕竟和Kernel有关。"

**理由**: 虽然这些任务是密码学/硬件优化（非 AI），但它们：
1. **区分度极高** - 是 benchmark 中最能区分模型能力的任务
2. **Kernel 优化相关** - 涉及 SIMD、向量化、指令级并行等底层优化技术
3. **可以重新包装** - 作为"通用 Kernel 优化能力"的测试

---

## 最终保留的 CPU 任务（3 个）

### 1. ✅ **ipb_cpu_004_aes128_ctr** - 保留

**区分度**: ⭐⭐⭐⭐⭐ **最高**（sonnet-5 退化 23.5x）

**性能数据**:
- Baseline: 5260ms → Reference: 107ms (48.8x 加速)
- Opus-5 fuzzy: 46.14ms ✅
- Sonnet-5 misleading: 4803.13ms ❌ (被误导退化 23.5x)

**原任务定位**: AES-128 CTR 模式加密优化

**新叙事包装**（AI for AI - Compute 轨道）:

> **"通用 Kernel 优化 - SIMD 向量化与并行化"**
>
> 虽然这是加密算法，但优化技术与 AI kernel 通用：
> - **向量化并行**: 独立 block 的 SIMD 并行（类似 batch inference）
> - **指令级优化**: AES-NI 指令集使用（类似 Tensor Core 优化）
> - **内存访问**: 避免 key schedule 重复（类似 weight caching）
>
> **测试能力**: AI 需要识别真正的并行化机会，而非被表面的"串行瓶颈"误导。
>
> **迁移性**: SIMD 优化、向量化思维可直接用于 AI 算子（如 element-wise ops）

**标签**: `kernel-optimization`, `simd`, `vectorization`, `high-discrimination`

---

### 2. ✅ **ipb_cpu_002_sha256_throughput** - 保留

**区分度**: ⭐⭐⭐⭐⭐ **极高**（GPT 模型退化 5-6x）

**性能数据**:
- Baseline: 2452ms → Reference: 384ms (6.4x 加速)
- Opus-5 fuzzy: 367.25ms ✅
- GPT-Luna fuzzy: 2091.42ms ❌（慢 5.7x）
- GPT-Terra fuzzy: 2118.43ms ❌（慢 5.8x）

**原任务定位**: SHA-256 哈希吞吐优化

**新叙事包装**（AI for AI - Compute 轨道）:

> **"通用 Kernel 优化 - 流水线并行与依赖分析"**
>
> SHA-256 的优化模式与 AI kernel 高度相似：
> - **循环展开**: 64 轮 hash 压缩（类似 Transformer 的多头并行）
> - **依赖链优化**: 消息调度的数据依赖（类似 attention 的 QKV 计算）
> - **块间并行**: 独立块的并行处理（类似 micro-batch 并行）
>
> **测试能力**: 识别循环中的真实依赖 vs 可并行部分
>
> **迁移性**: 依赖分析技术直接用于优化 RNN/LSTM 的循环依赖

**标签**: `kernel-optimization`, `loop-optimization`, `dependency-analysis`, `high-discrimination`

---

### 3. 🟡 **ipb_cpu_003_vliw_scheduler** - 保留（争议）

**区分度**: ⭐⭐⭐⭐ **高**（sonnet-5 卡在最差值 4080ms）

**性能数据**:
- Baseline: 4080ms → Reference: 1200ms (3.4x 加速)
- Opus-5 fuzzy: 1588ms
- Sonnet-5 fuzzy/misleading: 4080ms ❌（完全失败）

**原任务定位**: VLIW 指令调度器优化

**新叙事包装**（AI for AI - Compute 轨道）:

> **"调度优化 - 资源分配与依赖管理"**
>
> VLIW 调度的思维与 AI 系统调度相似：
> - **资源分配**: 3 种 slot（ALU/MUL/MEM）→ 类似 GPU SM 资源分配
> - **依赖管理**: 指令间的 hazard 检测 → 类似 kernel fusion 的依赖分析
> - **延迟隐藏**: MUL/MEM latency → 类似 GPU warp 调度
>
> **测试能力**: 全局优化思维，而非贪心逐条发射
>
> **争议点**: 这个任务与 AI 的连接最弱，如果最终任务数 >15 个，建议淘汰

**标签**: `scheduling`, `resource-allocation`, `controversial`

**建议**: 如果 dev 任务筛选后有 >5 个 AI 相关任务，则淘汰这个任务。

---

### 🟡 **ipb_cpu_001_gaussian_blur** - 状态待定

**之前建议**: 边缘保留（图像预处理）

**用户决策**: 未明确，等待 dev 任务分析后决定

**建议**: 
- 如果保留上述 3 个 CPU 任务，Gaussian Blur 可作为第 4 个（更直接与 AI 相关）
- 或者淘汰 VLIW，保留 Gaussian Blur

---

## 更新后的任务集结构

### 核心层（必须保留）

**CUDA 任务（6 个）**:
1. ✅ ipb_cuda_010_layernorm - Transformer 核心
2. ✅ ipb_cuda_007_kmeans_clustering - ML 聚类（区分度 18x）
3. ✅ ipb_cuda_008_conv1d_shared - CNN 核心
4. ✅ ipb_cuda_005_icp_correspondence - 3D AI
5. ✅ ipb_cuda_001 (Huffman) - 数据压缩
6. 🟡 ipb_cuda_009_matrix_transpose - 基础操作（可选）

**CPU 任务（3-4 个）**:
1. ✅ ipb_cpu_004_aes128_ctr - SIMD 向量化（区分度 23.5x）
2. ✅ ipb_cpu_002_sha256_throughput - 循环优化（区分度 5-6x）
3. 🟡 ipb_cpu_003_vliw_scheduler - 调度优化（争议）
4. 🟡 ipb_cpu_001_gaussian_blur - 图像预处理（可选）

### 扩展层（待 dev 任务分析）

**Dev 任务（3-8 个）**: 等待 workflow 分析结果

---

## 新的 AI for AI 叙事

### 标题
**AI for AI Benchmark - Compute 轨道**

### 副标题
衡量 AI 模型优化计算效率的能力 - 从 AI 算子到通用 Kernel

### 核心能力测试

#### 1. **AI 核心算子优化**（CUDA 任务）
- Transformer/CNN 的关键 kernel（LayerNorm, Conv1D）
- ML 算法优化（K-Means, ICP）
- 数据压缩场景（Huffman）

#### 2. **通用 Kernel 优化能力**（CPU 任务）
- **向量化并行**: SIMD、指令集优化（AES）
- **循环优化**: 依赖分析、展开策略（SHA-256）
- **调度优化**: 资源分配、延迟隐藏（VLIW）

**关键洞察**: 优化 AI 系统不仅需要了解 ML 算法，还需要**底层 kernel 优化能力**。AES/SHA-256 虽然不是 AI 算法，但其优化技术（SIMD、循环优化、依赖分析）**直接迁移到 AI kernel 优化**。

#### 3. **ML Pipeline 优化**（Dev 任务 - 待分析）
- 特征工程加速
- 数据预处理 pipeline
- 推理 serving 优化

### Misleading Prompt 的作用

在 **AI Safety** 语境下：
- **识别虚假瓶颈**: 不被表面的 profiler 数据误导
- **依赖分析能力**: 区分真实依赖 vs 可并行部分
- **全局优化思维**: 而非局部贪心优化

---

## 预期最终任务数

**保守估计**: 12-15 个
- CPU: 3-4 个
- CUDA: 6-7 个
- Dev: 3-5 个

**乐观估计**: 15-19 个
- CPU: 4 个
- CUDA: 7-8 个
- Dev: 5-8 个

---

## 待 Workflow 完成后的决策

1. **如果 dev 任务中有 5+ 个 AI 相关任务**:
   - 保留 3 个 CPU 任务（AES/SHA/VLIW）
   - 保留 6-7 个 CUDA 任务
   - 保留 5-8 个 Dev 任务
   - **总计**: 14-18 个任务

2. **如果 dev 任务中只有 2-3 个 AI 相关任务**:
   - 保留 3 个 CPU 任务（AES/SHA/Gaussian Blur）
   - 淘汰 VLIW（最不相关）
   - 保留 6-7 个 CUDA 任务
   - 保留 2-3 个 Dev 任务
   - **总计**: 11-13 个任务

3. **如果 dev 任务中没有强 AI 相关任务**:
   - 保留 4 个 CPU 任务（AES/SHA/VLIW/Gaussian）
   - 保留 6-7 个 CUDA 任务
   - 整体淘汰 Dev 任务
   - **总计**: 10-11 个任务

---

## 下一步

等待 workflow `w433ebvt4` 完成，获取 dev 任务的详细分析，然后做出最终决策。

**预计完成时间**: 5-10 分钟（26 个并行 agent）
