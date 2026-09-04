# IPB 数据集素材清单

**目标**：搜集可用于构造 IPB 性能回归任务的素材，支持批量并行构造。

---

## 1. AutoLab Benchmarks（已有本地副本）

**路径**：`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/autolab/`

### 1.1 已使用的 CUDA 任务（4个）

| Task ID | 任务名称 | 已构造 IPB | 回归类型 | ΔScore (luna) |
|---------|---------|-----------|---------|---------------|
| huffman_canonical_decode_cuda | Huffman 解码 | ✅ cuda_001 | 算法退化 (LUT→bit-by-bit) | -0.088 (需修复) |
| icp_correspondence_step_cuda | ICP 点云配准 | ✅ cuda_002 | per-batch sync loop | +0.333 |
| ntt_butterfly_cuda | NTT 蝴蝶变换 | ✅ cuda_003 | per-row sync loop | +0.200 |
| msm_pippenger_bls12_381_cuda | MSM Pippenger | ✅ cuda_004 | per-window sync loop | +0.399 |

### 1.2 其他 AutoLab 性能优化任务（32个）

**CPU 密集型任务（可构造 CPU 性能回归）**：

| 任务名称 | 领域 | 优化类型 | 适合构造 IPB |
|---------|------|---------|-------------|
| `flash_attention` | ML inference | SIMD, tiling, cache | ✅ 高优先级 |
| `bvh_raytracer` | 图形学 | BVH 结构, SIMD | ✅ 高优先级 |
| `radix_sort` | 排序算法 | cache, memory bandwidth | ✅ 中优先级 |
| `hash_join` | 数据库 | hash table, SIMD | ✅ 中优先级 |
| `fft_rust` | 信号处理 | Rust, FFT 算法 | ✅ 中优先级 |
| `sha256_throughput` | 密码学 | SIMD, unrolling | ✅ 中优先级 |
| `aes128_ctr` | 密码学 | AES-NI, cache | ✅ 中优先级 |
| `gaussian_blur` | 图像处理 | SIMD, separable filter | 🟡 低优先级 |
| `levenshtein_distance` | 字符串算法 | DP, SIMD | 🟡 低优先级 |
| `fredkin_sort_network` | 排序网络 | 算法设计 | ⚪ 算法题，不适合 |
| `discover_sorting` | 排序 | 算法推理 | ⚪ 不适合 |
| `adversarial_splay` | 数据结构 | splay tree | ⚪ 不适合 |

**其他领域任务（暂不适合 IPB）**：
- `adaptive_compression`, `bm25_search_go`, `concurrent_kv_wal`, `data_select_ifeval`, `grpo_multisource`, `llm_online_serving`, `moving_mnist_world_model`, `multilingual_ocr`, `regex_engine`, `resnet_bit_flip`, `safety_router`, `scaling_law`, `smallest_game_player`, `sstable_compaction_rs`, `stack_machine_golf`, `toy_isa_opt`, `vliw_scheduler`, `z_order_range_scan`, `agent_tool_routing`, `flux2_klein_lora`

---

## 2. Compute-Eval 数据集

**路径**：`/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/compute-eval/data/releases/`

### 2.1 版本清单

- `2025-1-problems.tar.gz` (188KB)
- `2025-2-problems.tar.gz` (468KB)
- `2025-3-problems.tar.gz` (595KB)
- `2026-1-problems.tar.gz` (1.0MB, **最新版本，已解压到 /tmp/problems.jsonl**)

### 2.2 2026-1 版本统计

- **总问题数**：566 个
- **CUDA C++ 问题**：518 个
- **问题类型**：`type == "cuda_cpp"`（全部是正确性题，非性能优化题）

### 2.3 典型问题示例

| Task ID | Group | Prompt 片段 |
|---------|-------|------------|
| CUDA/117 | cuda-kernels | "Write a CUDA kernel to compute the nearest neighbors..." |
| CUDA/136 | cuda-kernels | "Write a CUDA kernel to find the maximum value using parallel reduction..." |

**结论**：Compute-Eval 的 CUDA 问题都是**从零实现**的正确性题目，**不适合**直接用于 IPB（IPB 需要已有 baseline + regression）。但可以作为**参考素材**，了解常见 CUDA kernel 类型。

---

## 3. 可复用数据集优先级排序

### 3.1 高优先级（立即可用，已有完整 baseline + harness）

| 素材来源 | 任务名称 | 预期回归类型 | 构造难度 | 预估 ΔScore |
|---------|---------|-------------|---------|------------|
| AutoLab | `flash_attention` (CPU) | 去掉 tiling/SIMD 优化 | 中 | +0.3 ~ +0.5 |
| AutoLab | `bvh_raytracer` (CPU) | 改成朴素遍历/去掉 SIMD | 中 | +0.3 ~ +0.5 |
| AutoLab | `radix_sort` (CPU) | 改成 std::sort | 低 | +0.2 ~ +0.4 |
| AutoLab | `hash_join` (CPU) | 嵌套循环 join | 低 | +0.2 ~ +0.4 |

### 3.2 中优先级（需要适配，但可行）

| 素材来源 | 任务名称 | 预期回归类型 | 构造难度 | 备注 |
|---------|---------|-------------|---------|-----|
| AutoLab | `fft_rust` | 朴素 DFT | 中 | Rust 环境 |
| AutoLab | `sha256_throughput` | scalar 实现 | 低 | 简单 |
| AutoLab | `aes128_ctr` | 去掉 AES-NI | 中 | 需要 CPU feature |

### 3.3 低优先级或不适合

- **Compute-Eval CUDA 问题**：全是从零实现，没有可回归的 baseline
- **AutoLab 算法题**（如 `fredkin_sort_network`, `discover_sorting`）：重点是算法正确性，不适合性能回归
- **AutoLab ML/系统题**（如 `llm_online_serving`, `sstable_compaction_rs`）：复杂度高，构造成本大

---

## 4. 批量构造计划

### 4.1 立即可并行构造（4个 CPU 任务）

使用 AutoLab 高优先级任务，复用 IPB 构造流程（参考 `docs/cuda_case_study.md` 中的方法论）：

1. **ipb_cpu_001: flash_attention**
   - Baseline: AutoLab solution（已有 tiling + SIMD）
   - Regression: 去掉 tiling，每次 softmax 都完整遍历 n×n
   - Misleading: "Q/K/V 矩阵布局导致 cache miss"
   - Fuzzy: "这个实现太慢了，优化一下"

2. **ipb_cpu_002: bvh_raytracer**
   - Baseline: AutoLab solution（已有 BVH + SIMD）
   - Regression: 改成朴素 O(N) 遍历所有三角形
   - Misleading: "ray-triangle intersection 函数调用开销大"
   - Fuzzy: "光线追踪很慢，优化渲染性能"

3. **ipb_cpu_003: radix_sort**
   - Baseline: AutoLab radix sort
   - Regression: 改成 `std::sort`（O(N log N) vs O(N×k)）
   - Misleading: "内存分配开销"
   - Fuzzy: "排序太慢，优化性能"

4. **ipb_cpu_004: hash_join**
   - Baseline: AutoLab hash join
   - Regression: 嵌套循环 O(N×M)
   - Misleading: "hash 函数计算开销"
   - Fuzzy: "join 操作很慢，优化"

### 4.2 构造方法（工程化流程）

参考 `docs/cuda_case_study.md` 中总结的经验：

1. **复制 AutoLab 环境** → `tasks/ipb_cpu_00X/workspace/`
2. **编写 regression solve.c**（手动注入性能问题）
3. **构建 git 历史**：只保留 2 个 commit（baseline → regression），**不能有 fast 版本在历史中**
4. **编写 variants/fuzzy.md 和 misleading.md**
5. **编写 groundtruth/intent.json** 和 `measurement.json`
6. **实测 baseline/regression 性能**，确定 threshold
7. **验证 benchmark 命令输出格式**（需要解析 `time_ms=` 或类似输出）

### 4.3 并行执行策略

使用 **Workflow** 工具并行构造 4 个任务：

```javascript
export const meta = {
  name: 'construct-cpu-ipb-tasks',
  description: 'Parallel construction of 4 CPU IPB tasks from AutoLab',
  phases: [
    {title: 'Copy', detail: 'Copy AutoLab environments'},
    {title: 'Inject', detail: 'Inject regressions'},
    {title: 'Git', detail: 'Build git history'},
    {title: 'Variants', detail: 'Write fuzzy/misleading'},
    {title: 'Benchmark', detail: 'Measure performance'},
  ],
}

const TASKS = [
  {id: 'ipb_cpu_001', autolab: 'flash_attention', regression: 'remove_tiling'},
  {id: 'ipb_cpu_002', autolab: 'bvh_raytracer', regression: 'naive_traversal'},
  {id: 'ipb_cpu_003', autolab: 'radix_sort', regression: 'use_std_sort'},
  {id: 'ipb_cpu_004', autolab: 'hash_join', regression: 'nested_loop'},
]

phase('Copy')
await parallel(TASKS.map(t => () => agent(`Copy ${t.autolab} to ${t.id}`, {phase: 'Copy'})))

phase('Inject')
await parallel(TASKS.map(t => () => agent(`Inject ${t.regression} into ${t.id}`, {phase: 'Inject'})))

// ... 后续 phases
```

---

## 5. 下一步行动

1. ✅ **搜集素材**（本文档）
2. ⏭️ **并行构造** 4 个 CPU 任务（使用 workflow）
3. ⏭️ **评测** CPU 任务（gpt-5.6-luna/terra）
4. ⏭️ **修复** cuda_001 的 misleading 方向
5. ⏭️ **扩展** CUDA 数据集（从 Compute-Eval 手动挑选有潜力的 kernel 类型，自己写 baseline + regression）

