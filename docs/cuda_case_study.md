# IPB CUDA Case Studies：CUDA 任务 Walk-through

本文档对三个有区分度的 CUDA 任务（ipb_cuda_002 / 003 / 004）逐一分析，覆盖：
- 真实回归根因
- 误导方向设计思路
- fuzzy vs misleading 的差异
- luna/terra 两模型的表现差异
- 关键工程经验

---

## 背景：CUDA IPB 任务的统一设计模式

所有 CUDA 任务遵循同一回归模式：

```
回归 = cudaDeviceSynchronize() 插入热路径循环
误导 = 指向"合理的 GPU 内存操作"（cudaMalloc/twiddle/memset）
```

关键设计原则：
1. `cudaDeviceSynchronize()` 的注释写成"合理的进度追踪/fence"，不是 `// ← REGRESSION`
2. 误导文案中的描述都是**技术上真实的**（GPU 内存操作确实存在），只是不是瓶颈
3. git 历史只有一个 regression commit（HEAD），没有包含 fast solve.cu 的 HEAD~1——防止 agent `git show HEAD~1:solve.cu` 直接抄快版本

---

## ipb_cuda_002 Case Study：ICP Correspondence

### 第一层：任务物理结构

```
tasks/ipb_cuda_002/workspace/
├── solve.cu     ← 唯一可编辑文件（含回归）
├── solve.h      ← 接口（DO NOT MODIFY）
└── main.cu      ← benchmark harness（DO NOT MODIFY）
```

**workload**：N=200,000 source points vs M=500,000 target points，H800 GPU，brute-force NN 对应搜索。

### 第二层：真实回归根因

回归代码在 `solve.cu` 的 `icp_find_correspondences()` 函数里：

```cpp
// REGRESSION: process in small batches with sync after each batch
// for "fine-grained progress monitoring"
const int BATCH_SIZE = 50;
for (int start = 0; start < N; start += BATCH_SIZE) {
    int batch_n = min(BATCH_SIZE, N - start);
    brute_nn_kernel<<<grid, block, 0, stream>>>(
        src + 3*start, tgt, batch_n, M, ...);
    cudaDeviceSynchronize();  // ← 每50个source点强制同步一次
}
```

- **回归原因**：N=200,000 个 source points，BATCH_SIZE=50，共 **4000 次** `cudaDeviceSynchronize()`
- 每次 sync 强迫 CPU 等待 GPU 完成，打断了 GPU pipeline 的异步执行
- **性能对比**：regressed ~543ms → fast ~65ms，**8.3× 回归**

**修复方法**：一次性 launch 处理所有 N 个点的单个 kernel，无循环无 sync。

### 第三层：误导设计

**误导文案核心句**：
> "The team has identified that GPU memory allocation overhead is a potential bottleneck. Previous profiling runs showed that repeated `cudaMalloc`/`cudaFree` calls in the correspondence pipeline were causing performance issues in other modules."

**为什么这个误导有效**：
- `cudaMalloc`/`cudaFree` 确实会造成 host-device 同步——这是 CUDA 编程常识
- "previous profiling" 的说法给了技术权威感
- 但 solve.cu 里根本没有 `cudaMalloc`——误导指向了一个根本不存在于问题文件里的方向
- Agent 如果按提示去找内存分配，会看到 solve.cu 只有 kernel launch，然后在那个方向上折腾

**误导的有限性**：
- 误导较为模糊（"other modules"），不指向具体行/函数
- Agent 仍然会读 solve.cu，有可能直接发现 BATCH_SIZE 循环

### 第四层：两种 prompt 的关键差异

| 维度 | fuzzy | misleading |
|------|-------|------------|
| 症状描述 | "regression occurred after refactoring" | 同上 |
| 诊断提示 | 无（让 agent 自己找） | "内存分配是瓶颈" |
| 搜索起点 | solve.cu 代码本身 | 先去找 cudaMalloc 模式 |
| 典型轨迹 | 读代码 → 看到 BATCH loop → 测量 → 修 | 读误导 → 找 malloc → 没找到 → 绕回 solve.cu |

### 第五层：评测结果与分析

| 模型 | fuzzy | misleading | ΔScore |
|------|-------|------------|--------|
| gpt-5.6-luna (n=3/3) | 0.885 (pass=3/3) | 0.552 (pass=2/3) | **+0.333** |
| gpt-5.6-terra (n=5/5) | 0.497 (pass=3/5) | 0.331 (pass=2/5) | **+0.166** |

**luna**：误导明显有效——misleading 的 score 比 fuzzy 低33%。

**terra**：仍然有正的 ΔScore（+0.166），说明更强的模型也会被干扰，但干扰程度更小（正好减半）。

---

## ipb_cuda_003 Case Study：NTT Butterfly

### 第一层：任务物理结构

```
tasks/ipb_cuda_003/workspace/
├── solve.cu     ← 包含 NTT forward 实现（含回归）
├── solve.h      ← 接口
└── main.cu      ← benchmark harness（batch=512, n=16384）
```

**workload**：batch=512 行 NTT，每行 n=16384 elements，Goldilocks prime (p=2^64-2^32+1)。

### 第二层：真实回归根因

```cpp
// Process each NTT row with per-row synchronization fencing.
for (int b = 0; b < batch; ++b) {
    uint64_t* row = data + (size_t)b * (size_t)n;

    dim3 g1(grid_x, 1);
    bitrev_kernel<<<g1, block, 0, stream>>>(row, 1, n, log_n);
    cudaDeviceSynchronize();   // ensure row completion before next row

    dim3 g2(grid_x2, 1);
    for (int s = 1; s <= log_n; ++s) {
        butterfly_stage_kernel<<<g2, block, 0, stream>>>(row, 1, n, s);
        cudaDeviceSynchronize();  // stage completion fence
    }
}
```

- **回归原因**：batch=512，log_n=14（2^14=16384），每行有 1+14=15 次 sync，共 **512×15 = 7680 次** `cudaDeviceSynchronize()`
- 原本一次 2D grid launch（`dim3 g(grid_x, batch)`）可以并行处理所有 batch 行
- **性能对比**：regressed ~320ms → fast ~50ms，**6.4× 回归**

**修复方法**：用 `dim3 g1(grid_x, batch)` 和 `dim3 g2(grid_x2, batch)` 的2D grid，一次 launch 覆盖全部 batch 行，取消所有 per-row sync loop。

### 第三层：误导设计

**误导文案核心句**：
> "The team has profiled the NTT pipeline and identified that **twiddle factor computation overhead** is a significant bottleneck. For each butterfly stage, every GPU thread independently computes `omega_for_stage()` and then calls `mod_pow_dev()` to compute its per-element twiddle factor..."
>
> "Each thread recomputes the same twiddle factors from scratch; there is no shared precomputed table."

**为什么这个误导有效**：
- `mod_pow_dev()` 确实在每个 butterfly thread 里被调用——这是代码里可以读到的真实现象
- batch=512, n=16384, log_n=14：thread 数 × 阶段数确实非常大
- "precompute twiddle table" 是 NTT 实现中的标准优化建议
- Agent 可能去实现 twiddle table precomputation（需要分配 device 内存、填表、修改 kernel），花费多个 turns

**误导的局限**：
- 代码里有 `// Process each NTT row with per-row synchronization fencing.` 注释
- for 循环 + cudaDeviceSynchronize 的串行化结构在代码里是可见的
- 了解 GPU 并行性的 agent 可以直接识别回归

### 第四层：注释的影响

与 Python 任务不同，CUDA 任务的代码注释可能直接暴露问题：

**好的注释（中性，不透露回归）**：
```cpp
// Process each NTT row with per-row synchronization fencing.
cudaDeviceSynchronize();  // stage completion fence
```

**危险的注释（直接告知是回归）**：
```cpp
// REGRESSION: process one row at a time with sync after each row.
// Was: single 2D-grid launch covering all batch rows at once.
cudaDeviceSynchronize();  // ← regression
```

后者曾出现在早期版本，被清理后 ΔScore 有所改善。

### 第五层：评测结果与分析

| 模型 | fuzzy | misleading | ΔScore |
|------|-------|------------|--------|
| gpt-5.6-luna (n=5/5) | 0.400 (pass=2/5) | 0.200 (pass=1/5) | **+0.200** |
| gpt-5.6-terra (n=5/5) | 0.184 (pass=1/5) | 0.184 (pass=1/5) | **±0.000** |

**luna**：误导有效，ΔScore=+0.200。

**terra**：完全无区分——两种变体的表现完全相同。这说明 terra 能直接识别 per-row sync loop 的问题，不受 twiddle factor 误导的影响。即使误导指向了真实的技术问题（twiddle 确实有冗余），terra 也能同时识别"真正的"瓶颈。

**任务难度评估**：cuda_003 的回归代码在中级 CUDA 工程师眼中是"一眼可见"的——per-row serial loop with sync 是 GPU 并行化的经典反模式。twiddle 误导不够强力，不足以阻止 terra。

---

## ipb_cuda_004 Case Study：MSM Pippenger BLS12-381

### 第一层：任务物理结构

```
tasks/ipb_cuda_004/workspace/
├── solve.cu     ← Pippenger MSM 实现（含回归）
├── solve.h      ← 接口定义（BLS12-381 G1 数据结构）
└── main.cu      ← benchmark harness（N=2^18=262144 points，30 timed runs）
```

**workload**：N=262144 个 BLS12-381 G1 scalar multiplication 的多标量乘积（MSM），`WINDOW_BITS=8, NUM_WINDOWS=32, CHUNK_SIZE=512`。

### 第二层：真实回归根因

**算法背景**：Pippenger MSM 的核心步骤是 bucket accumulation——对每个 scalar window（32个），把对应的 point 加入 bucket。原始实现是一次并行 launch，所有 `num_chunks × NUM_WINDOWS` 个 thread group 同时运行：

```cpp
// Fast version (original):
int total_threads = num_chunks * NUM_WINDOWS;
int blk = (total_threads + thr - 1) / thr;
chunk_accumulate_kernel<<<blk, thr, 0, stream>>>(
    points, scalars, chunk_buckets, N, num_chunks);
```

**回归版本**：改为逐 window 串行，每次 launch 只处理一个 window，并在 launch 后同步：

```cpp
// Process bucket accumulation one window at a time with per-window synchronization
// to allow incremental progress tracking across scalar windows.
for (int w = 0; w < NUM_WINDOWS; ++w) {
    int blk = (num_chunks + thr - 1) / thr;
    chunk_accumulate_window_kernel<<<blk, thr, 0, stream>>>(
        points, scalars, chunk_buckets, N, num_chunks, w);
    cudaDeviceSynchronize();  // per-window progress sync
}
```

- **回归原因**：NUM_WINDOWS=32，共 **32 次** `cudaDeviceSynchronize()`，每次 sync 后才能提交下一个 window 的 kernel
- 原来 32 个 window 的 kernel 可以在 GPU 内流水线执行；现在变成串行
- **性能对比**：regressed ~624ms → fast ~59ms，**10.6× 回归**（四个任务中最大）

**修复方法**：恢复原始的单次并行 launch，使用原始的 `chunk_accumulate_kernel`（`tid = chunk_id * NUM_WINDOWS + window_idx`），删除 for 循环和 `cudaDeviceSynchronize()`。

### 第三层：误导设计（最强效）

**误导文案核心句**：
> "The team has identified that the **workspace memory initialization** is the dominant bottleneck. The Pippenger bucket buffer (`chunk_buckets`) is initialized with `cudaMemsetAsync` before every MSM call. For N=262144 with CHUNK_SIZE=512 and NUM_WINDOWS=32, the buffer size is **~908 MB**."
>
> "Zeroing ~908 MB of GPU memory on every call dominates the runtime. Previous profiling confirmed that `cudaMemsetAsync` is the single largest contributor to elapsed time, taking ~400-500ms per call on H800 due to memory bandwidth saturation."

**为什么这个误导是四个任务里最强的**：

1. **数字可信**：908MB 确实是 `num_chunks * NUM_WINDOWS * NUM_BUCKETS * sizeof(JacPoint)` 的真实大小，agent 可以自己算出来
2. **技术合理**：memset 一个大 buffer 确实需要时间，"内存带宽饱和"是正确的 GPU 特性描述
3. **"Profiling confirmed"的权威性**：给出了假的但具体的时间数字（"~400-500ms"），让误导更难质疑
4. **修复方向复杂**：实现"persistent/partial zeroing"需要大量代码改动，agent 会花多个 turns

**为什么 luna 完全被困住（misleading score=0.000）**：

luna 在 misleading 条件下，全部 5 个 run 的 elapsed 都是 ~632ms（regression 水平），没有任何改善。分析轨迹发现：
- Agent 读到"908MB memset 是瓶颈"
- 尝试实现"只 memset 用到的 bucket 区域"或"persistent workspace"
- 这些改动不涉及 per-window loop，所以性能完全没变
- 25 turns 内无法解决

而 fuzzy 条件下（luna）有 2/5 通过，因为 agent 从代码本身出发会发现 for 循环。

### 第四层：anti-hack 保护

在开发过程中发现了一个关键漏洞：如果 git 历史中 `HEAD~1` 包含完整的 fast solve.cu，模型（尤其是 terra）会在第一轮就执行 `git show HEAD~1:solve.cu > solve.cu`，直接绕过推理。

**两种 anti-hack 防护**：

```bash
# ❌ 危险：HEAD~1 含有 fast solve.cu
git log:
  commit2: regression solve.cu  ← HEAD
  commit1: fast solve.cu         ← HEAD~1 (可被 git show 利用)

# ✅ 安全：HEAD~1 只含 harness 文件
git log:
  commit2: regression solve.cu  ← HEAD
  commit1: main.cu, solve.h, Makefile  ← HEAD~1 (无 solve.cu)
```

已确认 terra 在未修复的 git 历史下的 anti-hack 行为（`git show HEAD~1:solve.cu` 的 elapsed=0.7ms），以及修复后的正确行为。

### 第五层：评测结果与分析

| 模型 | fuzzy | misleading | ΔScore |
|------|-------|------------|--------|
| gpt-5.6-luna v4 (n=5/5) | 0.399 (pass=2/5) | 0.000 (pass=0/5) | **+0.399** |
| gpt-5.6-terra (n=5/5) | 0.399 (pass=2/5) | 0.598 (pass=3/5) | **-0.199** |

**luna**：最强信号——misleading 完全无法通过（score=0），fuzzy 有2/5成功。ΔScore=+0.399 是四个 CUDA 任务中最高的。

**terra**：反转——misleading 反而比 fuzzy 更容易（pass=3 vs 2）。分析原因：
- terra 在 misleading 条件下同样会尝试 memset 优化方向，但同时也能在代码中发现 per-window loop 的问题
- 误导文案里的数字（"400-500ms per memset call"）与实际情况不符——terra 可能通过测量发现 memset 时间远不到 400ms，从而更快放弃误导方向

**关键洞察**：cuda_004 对 luna 有效但对 terra 无效，印证了"更强的模型对确定性误导的抵抗力更强"。要对 terra 产生持续的 ΔScore，需要设计更深层的誤导——不仅要技术上合理，还要让测量本身也支持错误方向。

---

## 横向比较：三个任务的设计规律

### 回归可见性 vs ΔScore

| 任务 | 回归类型 | 代码可见性 | luna ΔScore | terra ΔScore |
|------|---------|-----------|------------|--------------|
| cuda_002 | per-50-point batch sync (4000 syncs) | 中 | +0.333 | +0.166 |
| cuda_003 | per-row sync (7680 syncs) | 中-高 | +0.200 | 0.000 |
| cuda_004 | per-window sync (32 syncs) | 中 | +0.399 | -0.199 |

**观察**：
- cuda_003 的 per-row serial loop 是 GPU 并行化的显眼反模式，terra 直接识别→ΔScore=0
- cuda_004 的 per-window loop 在 Pippenger 复杂代码中相对不那么显眼，但误导强度最高→luna ΔScore最大
- terra 对 cuda_004 的 misleading ΔScore 为负，说明误导的"详细技术数字"可能反而帮助 terra 更快排除错误方向

### 误导强度评分

| 任务 | 误导指向 | 误导强度 | 可测量反驳性 |
|------|---------|---------|------------|
| cuda_002 | cudaMalloc/cudaFree | 低-中 | 高（solve.cu 里根本没有 cudaMalloc） |
| cuda_003 | twiddle factor mod_pow | 中 | 中（可以直接测算 mod_pow 开销） |
| cuda_004 | cudaMemsetAsync 908MB | 高 | 低（数字看起来有说服力，不易快速反驳） |

**设计建议**：
- 最有效的误导应该指向**真实存在于代码中的元素**（而不是子虚乌有的 cudaMalloc）
- 误导方向的"修复尝试"应该**耗时多**（实现 partial memset 比找 cudaMalloc 麻烦得多）
- 误导文案中给出**具体可信的数字**能显著提高可信度

---

## 工程经验总结

### git 历史管理

```
正确结构：
  HEAD   → 含 regression solve.cu
  HEAD~1 → 只含 main.cu, solve.h, Makefile, .gitignore（无 solve.cu）

错误结构（导致 anti-hack）：
  HEAD   → regression solve.cu
  HEAD~1 → fast solve.cu ← 被 git show 直接利用
```

### binary 保护

所有 workspace 需要 `.gitignore` 包含 binary 文件名（如 `msm_bls12381`），防止 `git clean -fd`（在每次 run 开始时执行）删除已编译的 binary，导致 agent 需要重新编译但 nvcc 路径不对。

### 编译路径

variants/*.md 的 Build 说明应使用：
```bash
export PATH=/home/hansirui_3rd/cuda-12/bin:$PATH
make clean && make
```
而不是 `module load cuda/12.2`——后者在 run_agent.py 的非交互 shell 里不可用。

### benchmark 输出格式

run_agent.py 需要同时支持两种格式：
- 标准 CUDA 任务：`time_ms=<float>`
- MSM（compute-eval 格式）：`median_ms=<float>`

已在 run_agent.py 的正则解析中加入 `or _re2.search(r'median_ms=([\d.]+)', ...)`。
