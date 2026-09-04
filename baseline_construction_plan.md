# 自建性能基线方案

## 核心发现

### ComputeEval 潜力
- **143 个 CUDA 任务**（114 cuda-kernels + 29 cuda-runtime）
- **79 个任务提到 shared memory**
- **45 个 reduction 任务**
- **40 个 warp-level 优化任务**
- **13 个 tiling/coalesced 任务**

**关键优势**：
- 任务都给出了**期望的优化技术**（如"use shared memory", "tree-based reduction"）
- 我们可以实现两个版本：
  1. **Baseline**：朴素实现（全局内存、串行、无优化）
  2. **Reference**：按要求使用优化技术（shared memory、warp primitives、tiling）
- 测量性能差距，筛选出 5×+ 加速的任务

## 三种自建基线策略

### 策略 1：从 ComputeEval 逆向构造基线（推荐）

**工作流程**：
1. 从 ComputeEval 挑选明确要求优化技术的任务（如 CUDA/10 reduction, CUDA/114 shared memory tiling）
2. 实现两个版本：
   - **Naive baseline**：朴素实现（global memory only, 串行 reduction, 无 tiling）
   - **Optimized reference**：按 prompt 要求实现（shared memory, tree reduction, tiling）
3. 在 H800 上测量性能差距
4. 筛选出 5×+ 加速的任务转化为 IPB 任务

**优势**：
- 任务定义清晰（ComputeEval prompt 本身就是规格）
- 优化方向明确（prompt 直接说明使用什么技术）
- 可批量处理（143 个候选）

**候选任务清单**：
```
高优先级（经典优化场景）：
1. CUDA/10  - Recursive reduction (shared memory + tree reduction)
2. CUDA/114 - Bilinear interpolation (shared memory tiling)
3. CUDA/105 - 矩阵相关（shared memory）
4. CUDA/11  - Reduction 变体
5. CUDA/112 - Shared memory 相关

中优先级（warp-level 优化）：
- 40 个 warp-related 任务（warp shuffle, ballot, etc.）

低优先级（coalesced access）：
- 13 个 coalescing 相关任务
```

---

### 策略 2：复用 CUDA 回归模式到新场景

**已验证的回归模式**：
1. **Per-item sync**：在热路径加 cudaDeviceSynchronize（ipb_cuda_002/003 成功）
2. **算法退化**：复杂算法 → 朴素算法（ipb_cuda_001 LUT→bit-by-bit）
3. **并行度退化**：chunked parallel → sequential（ipb_cuda_004）

**可应用的新场景**：
- **矩阵乘法**：tiled shared memory → naive triple loop
- **Reduction**：tree reduction → sequential accumulation
- **Scan**：Blelloch scan → sequential prefix sum
- **Histogram**：atomic in shared memory → atomic in global memory
- **Transpose**：coalesced tiled → strided naive

**工作流程**：
1. 从 AutoLab 或手写实现一个优化版本
2. 系统性"去优化"（去 shared memory、去 tiling、去并行）
3. 测量性能差距
4. 构造 misleading 变体

---

### 策略 3：手工构造"教科书级"任务

**经典优化对比**：
1. **矩阵乘法**
   - Baseline: naive O(n³) triple loop
   - Regression: 带 shared memory 但 tile size=1（无复用）
   - Optimized: tile size=16/32 shared memory

2. **Reduction**
   - Baseline: CPU 串行
   - Regression: GPU 但串行（blockDim=1）
   - Optimized: warp shuffle + tree reduction

3. **Transpose**
   - Baseline: naive row-major read → column-major write（非 coalesced）
   - Regression: coalesced read 但带 bank conflict
   - Optimized: coalesced + padding 消除 bank conflict

4. **Convolution**
   - Baseline: 每个输出像素独立读 kernel（无复用）
   - Regression: shared memory 但 tile overlap 不正确
   - Optimized: shared memory + halo tile

**优势**：
- 教学价值高（每个任务对应一个核心概念）
- 可控性强（自己设计回归点）
- 优化幅度可预测

**劣势**：
- 需要手工实现（工作量大）
- 缺少多样性（只有 4-5 个经典模式）

---

## 推荐执行方案

### Phase 1：快速验证（1-2 天）
从 ComputeEval 选 3 个任务快速实现 baseline + optimized：
1. **CUDA/10** (reduction) — 最经典
2. **CUDA/114** (shared memory tiling) — 最实用
3. 一个 warp-level 任务（从 40 个中选）

测量性能差距，验证可行性。

### Phase 2：批量构造（3-5 天）
如果 Phase 1 成功（至少 2/3 任务有 5×+ 加速）：
- 用 workflow 并行处理 10-15 个 ComputeEval 任务
- 每个任务：实现 baseline → 实现 optimized → 测量 → 构造 variants

### Phase 3：整合（1 天）
- 构建 git workspace
- 编写 benchmark 脚本
- 集成到 run_agent.py
- 补充 misleading variants

---

## 与 AutoLab 数据的对比

| 维度 | AutoLab CPU | ComputeEval CUDA | 手工构造 |
|------|-------------|------------------|----------|
| 数据量 | 4 个可用 | 143 个候选 | 无限制 |
| 优化幅度 | 25-200× | 未知（需测量）| 可控 |
| 实现成本 | 已有代码 | 需实现两版 | 全手工 |
| 多样性 | 高 | 很高 | 低 |
| CUDA 相关 | 无 | 全是 | 可选 |
| 控制性 | 低 | 中 | 高 |

**建议优先级**：
1. **ComputeEval CUDA**（高价值 + 大规模）
2. AutoLab CPU（已有代码，快速扩充）
3. 手工构造（补充特定教学场景）

---

## 下一步行动

### 立即执行（ultracode workflow）
1. 实现 CUDA/10 (reduction) 的 baseline + optimized
2. 实现 CUDA/114 (tiling) 的 baseline + optimized
3. 在 H800 上测量性能差距
4. 如果成功（>5× 加速），批量扩展到 10+ 任务

### 需要确认
- 是否优先 ComputeEval CUDA（143 个候选）还是 AutoLab CPU（4 个现成）？
- 目标任务数量（8 个？16 个？32 个？）
- 性能差距阈值（5×？10×？）
