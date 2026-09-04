# IPB 数据集扩展候选清单

## 已完成任务（4 个 CUDA）

| Task ID | 源任务 | 回归类型 | 性能差距 | 状态 |
|---------|--------|---------|---------|------|
| ipb_cuda_001 | huffman_canonical_decode_cuda | 算法退化（LUT→bit-by-bit） | 21× | ✓ 已构造 |
| ipb_cuda_002 | icp_correspondence_step_cuda | per-batch sync | 8× | ✓ 已构造 |
| ipb_cuda_003 | ntt_butterfly_cuda | per-row sync | 6× | ✓ 已构造 |
| ipb_cuda_004 | msm_pippenger_bls12_381_cuda | bucket 并行度退化 | ~10× | ✓ 已构造 |

## 待构造任务（4 个 CPU）

### 1. flash_attention
**源路径**: `autolab/tasks/flash_attention/`
**语言**: C
**性能基线**:
- Baseline: ~0.75s (naive O(n²) 空间, double 精度, 标量代码)
- Optimized: ~0.03s (~25× 加速)

**优化技术**:
1. Flash Attention tiling（Dao et al.）: O(n²)→O(n·d) 空间，L1 cache 友好 (~3×)
2. Online softmax: 增量更新 max/denom，避免二次遍历 (~2×)
3. float32: 内存带宽减半 (~2×)
4. AVX2 SIMD: Q·K^T 向量化 (~4×)

**回归候选方案**:
- **方案 A**: 去掉 tiling，物化完整 n×n score 矩阵（回退到 O(n²) 空间）
- **方案 B**: 保留 tiling，但去掉 online softmax（改成 two-pass）
- **方案 C**: 保留算法，但禁用 AVX2（标量 fallback）

**Misleading 诱饵方向**:
- 暗示"内存分配开销"是瓶颈（实际是算法复杂度）
- 或暗示"缓存行对齐"问题（实际是工作集大小）

---

### 2. radix_sort
**源路径**: `autolab/tasks/radix_sort/`
**语言**: C
**性能基线**:
- Baseline: ~4.5s (stdlib qsort，O(n log n)，函数指针间接调用)
- Optimized: ~0.1s (~45× 加速)

**优化技术**:
1. Naive 8-pass LSD radix sort: O(n log n)→O(n) (~10×)
2. 2-pass 16-bit radix: 8 passes→2 passes，减半内存访问 (~1.3×)
3. Multi-threaded: OpenMP 并行 (~3×)

**回归候选方案**:
- **方案 A**: 回退到 qsort（完全算法退化）
- **方案 B**: 用 radix sort 但单 pass 4-byte digit（需要 2^32 buckets，内存爆炸）
- **方案 C**: 用 8-pass radix 但串行（去掉 OpenMP）

**Misleading 诱饵方向**:
- 暗示"分支预测失败"导致慢（实际是算法复杂度）
- 或"NUMA 远端内存访问"（实际是并行度不足）

---

### 3. hash_join
**源路径**: `autolab/tasks/hash_join/`
**语言**: C
**性能基线**:
- Baseline: ~20s (nested-loop，O(R×S) = ~100 billion 比较)
- Optimized: ~0.1s (~200× 加速)

**优化技术**:
1. Hash join (build + probe): O(R×S)→O(R+S) (~500×)
2. Open-addressing + Knuth multiplicative hash: 避免 chaining malloc (~2×)

**回归候选方案**:
- **方案 A**: 完全回退到 nested-loop
- **方案 B**: 用 hash join 但用 chained hash table（malloc-per-node 缓存抖动）
- **方案 C**: 用 hash join 但哈希函数差（模质数而非位运算）

**Misleading 诱饵方向**:
- 暗示"哈希冲突太多"需要换哈希函数（实际是算法复杂度）
- 或"输入数据未排序"（实际是缺少索引结构）

---

### 4. bvh_raytracer
**源路径**: `autolab/tasks/bvh_raytracer/`
**语言**: C++
**性能基线**:
- Baseline: ~3.8s (brute-force，每条光线测试全部 4096 三角形)
- Optimized: ~0.1s (~38× 加速)

**优化技术**:
1. BVH midpoint split: O(N)→O(log N) 测试 (~37×)
2. SAH binned split: 优化 BVH 质量，减少节点访问 (~1.5×)

**回归候选方案**:
- **方案 A**: 完全去掉 BVH，回退到 brute-force
- **方案 B**: 构建 BVH 但遍历时串行（去掉 SIMD/多线程）
- **方案 C**: 用劣质 BVH（随机 split 而非 SAH）

**Misleading 诱饵方向**:
- 暗示"三角形排序不优化"导致缓存不友好（实际是缺少空间结构）
- 或"光线方向不规则"导致 SIMD 无效（实际是算法复杂度）

---

## 不适合的数据集

### Python ML 训练任务 (AutoLab)
- **flux2_klein_lora, grpo_multisource, moving_mnist_world_model, scaling_law**
- 问题: 训练时间过长（小时级），无独立性能测量，属于超参数调优而非性能回归

### resnet_bit_flip (AutoLab)
- 问题: 对抗攻击算法优化，不是性能回归

### ComputeEval (566 任务)
- 问题: 全是 correctness 评测，无 baseline/optimized 性能对比

### ParEval-Repo (6 任务)
- 问题: HPC 代码翻译 benchmark，关注语言翻译质量而非性能回归

### NL2RepoBench (105 任务)
- 问题: Python repo 生成，无 CUDA/training 内容

---

## 推荐构造优先级

**第一批（高价值）**:
1. **flash_attention** — 学术热点，有明确论文出处，优化技术层次丰富
2. **radix_sort** — 经典算法，O(n log n)→O(n) 对比强烈
3. **hash_join** — 数据库核心操作，500× 加速空间大

**第二批（备选）**:
4. **bvh_raytracer** — 图形学经典，但 C++ 代码可能更复杂

---

## 下一步行动计划

### Phase 1: 批量读取源代码（并行）
- 4 个 CPU 任务的 environment/ 和 solution/ 完整代码
- 提取关键函数、数据结构、编译选项

### Phase 2: 设计回归方案（并行）
- 为每个任务设计 2-3 种回归候选
- 用 ultracode workflow 并行验证每种回归的性能差距

### Phase 3: 构造 fuzzy/misleading 变体（并行）
- fuzzy: 模糊描述（"运行很慢，需要优化"）
- misleading: 具体但错误的方向（如"缓存对齐问题"实际是算法复杂度）

### Phase 4: 构建 workspace + git 历史（并行）
- 每个任务独立 git repo（baseline → regression）
- 确保 anti-hack：git 历史不能包含完整 optimized 版本

### Phase 5: 编写 benchmarks/ 脚本（并行）
- 性能测量脚本（time, perf stat）
- 验证脚本（正确性检查）

### Phase 6: 集成到 run_agent.py
- 添加 CPU 任务的 compile + benchmark 逻辑
- threshold 设置（基于实测性能）
