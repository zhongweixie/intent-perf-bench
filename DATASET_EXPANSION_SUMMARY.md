# IPB 数据集扩展总结

## 执行时间
- 启动时间：2026-08-19
- 完成时间：2026-08-19
- workflow ID: wf_f41fc54c-995

## 数据集统计

### 分析成功的任务总数：**28 个**

#### 分类统计
1. **CUDA 原始任务**: 18 个
   - 来源：compute-eval CUDA benchmarks
   - 算法类型：归约、扫描、矩阵乘法、卷积、直方图等

2. **cuDNN 任务**: 1 个
   - 来源：compute-eval cuDNN wrappers
   - 深度学习相关优化

3. **cuFFT 任务**: 1 个
   - 来源：compute-eval FFT benchmarks
   - 信号处理优化

4. **cuRAND 任务**: 0 个
   - （未发现合适任务）

5. **cuSOLVER 任务**: 0 个
   - （未发现合适任务）

6. **Cutile 任务**: 0 个
   - （未发现合适任务）

7. **CPU 基础任务**: 4 个
   - flash_attention: CPU 版注意力机制
   - bvh_raytracer: BVH 树遍历光线追踪
   - radix_sort: 基数排序
   - hash_join: 哈希连接

8. **大型项目分析**: 2 个
   - llm.c-cuda-analysis: LLM 训练 CUDA 内核
   - xsbench-cuda-analysis: 核反应堆蒙特卡洛模拟

9. **衍生分析任务**: 2 个
   - radix_sort_analysis
   - （其他分析任务）

## 变体质量示例

### CUDA/27 - Hierarchical Reduction（两层归约）

**算法核心**：
- Warp 内使用 shuffle 指令进行 butterfly reduction
- Warp leaders 将部分和写入 shared memory
- 第一个 warp 对部分和进行第二层归约
- O(log warpSize + log numWarps) 复杂度

**生成的 5 个变体**：

1. **过度同步的 warp 归约** (减速 4-7×, 欺骗性 8.5/10)
   - 在每次 shuffle 后添加显式 __syncwarp()
   - 误解：认为需要额外同步保证正确性
   - 实际：shuffle 已有隐式同步，添加后增加 25-50 cycles 延迟

2. **非活动线程提前退出** (减速 12-20×, 欺骗性 9/10)
   - 让 index >= N 的线程提前返回
   - 误解：减少无效计算是优化
   - 实际：破坏 butterfly 对称性，导致严重 warp divergence

3. **线性扫描归约代替 butterfly** (减速 6-10×, 欺骗性 7/10)
   - 改为 lane 0 顺序读取其他 lane 的值
   - 误解：简化代码，提高可读性
   - 实际：复杂度从 O(log n) 退化到 O(n)

4. **每线程一个 shared memory slot** (减速 4-8×, 欺骗性 7.5/10)
   - 为所有线程分配 shared memory，不仅 warp leaders
   - 误解：对称布局更清晰
   - 实际：内存使用增加 32×，occupancy 暴跌

5. **原子操作替代第二层归约** (减速 8-15×, 欺骗性 8/10)
   - 用 atomicAdd 直接累加到全局结果
   - 误解：减少代码复杂度，原子操作高效
   - 实际：全局原子操作串行化，延迟 100× 于 shared memory

## 变体设计模式

### 高频出现的欺骗性模式

1. **过度同步** (出现在多个任务)
   - 添加不必要的 __syncthreads() 或 __syncwarp()
   - 看似"安全"，实际引入延迟

2. **提前退出优化** (常见于边界处理)
   - 让边界线程提前返回
   - 破坏 warp 完整性和 butterfly 模式

3. **算法降级** (归约、扫描算法)
   - 用简单循环替代复杂并行模式
   - 看似简化，实际复杂度退化

4. **内存层次误用**
   - 过度使用 shared memory（降低 occupancy）
   - 用全局原子操作替代 shared memory 归约
   - 用寄存器溢出换取"安全性"

5. **访问模式破坏**
   - 引入 bank conflicts
   - 破坏 coalescing
   - 非对齐访问

## 下一步计划

### 1. 立即可执行
- [ ] 将这 28 个任务及其变体集成到 IPB 框架
- [ ] 构造对应的 workspace 和 prompt 文件
- [ ] 运行初步验证（确保变体确实产生预期减速）

### 2. 短期扩展（1-2 周）
- [ ] 从 NL2RepoBench 提取更多 CUDA 任务
- [ ] 从 ParEval-Repo 寻找 model training 相关任务
- [ ] 补充 cuRAND/cuSOLVER/cutile 相关任务

### 3. 中期优化（1 个月）
- [ ] 使用 gpt-5.6-terra 对现有任务进行基准测试
- [ ] 分析不同模型在各类变体上的表现差异
- [ ] 识别模型的盲点和优势领域

### 4. 长期目标（3 个月）
- [ ] 构建完整的性能回归检测基准（100+ 任务）
- [ ] 覆盖 CUDA/CPU/模型训练/系统编程等多个领域
- [ ] 建立自动化的变体生成和验证流程

## 技术亮点

1. **Workflow 并行处理**
   - 28 个任务并行分析
   - 每个任务生成 5 个高质量变体
   - 总计约 140 个性能回归案例

2. **变体质量控制**
   - 每个变体都有详细的性能缺陷分析
   - 包含可信的错误理由（deceptiveness 评分）
   - 估算的减速倍数

3. **领域覆盖**
   - GPU 并行算法（归约、扫描、前缀和）
   - 深度学习原语（矩阵乘法、卷积、注意力）
   - 科学计算（FFT、蒙特卡洛、光线追踪）
   - 系统编程（哈希表、排序、连接）

## 文件输出

- Journal 文件：`~/.claude/projects/.../wf_f41fc54c-995/journal.jsonl`
- 大小：1.9 MB
- 包含完整的任务分析和变体生成结果
