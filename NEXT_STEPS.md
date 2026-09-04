# IPB 数据集扩展 - 下一步行动计划

## 当前状态

### 已完成的 Workflow 分析
- **任务总数**: 35 个
- **变体总数**: 约 175 个（每个任务 5 个变体）
- **分析质量**: 每个变体都包含详细的性能缺陷分析、减速估算和欺骗性评分

### 任务分类明细

| 类别 | 数量 | 来源 |
|------|------|------|
| CUDA 基础算法 | 21 | compute-eval |
| CPU 算法 | 4 | flash_attention, bvh_raytracer, hash_join, radix_sort_analysis |
| cuDNN | 2 | compute-eval cuDNN wrappers |
| cuFFT | 1 | compute-eval FFT |
| cuRAND | 1 | compute-eval random |
| cuSOLVER | 1 | compute-eval solver |
| cutile | 3 | compute-eval cutile primitives |
| 大型项目 | 2 | llm.c, xsbench |

## 立即可执行的任务

### Phase 1: 选择高优先级任务构造 IPB (本周)

**选择标准**：
1. 算法代表性强（归约、扫描、矩阵乘等核心模式）
2. 变体欺骗性高（deceptiveness ≥ 8.0）
3. 代码规模适中（500-2000 行）
4. 性能差异显著（减速 ≥ 4×）

**建议的首批 10 个任务**：

#### CUDA 核心算法（6 个）
1. **CUDA/27** - Hierarchical Reduction (两层归约)
   - 优先级: ⭐⭐⭐⭐⭐
   - 理由: warp shuffle + shared memory 的经典模式，变体质量极高

2. **CUDA/189** - 待查看具体算法
   - 优先级: ⭐⭐⭐⭐⭐
   
3. **CUDA/131** - 待查看具体算法
   - 优先级: ⭐⭐⭐⭐⭐

4. **CUDA/56** - 待查看具体算法
   - 优先级: ⭐⭐⭐⭐

5. **CUDA/91** - 待查看具体算法
   - 优先级: ⭐⭐⭐⭐

6. **CUDA/21** - 待查看具体算法
   - 优先级: ⭐⭐⭐⭐

#### CPU 算法（2 个）
7. **flash_attention** - CPU 注意力机制
   - 优先级: ⭐⭐⭐⭐⭐
   - 理由: 热门的深度学习原语，内存访问模式复杂

8. **bvh_raytracer** - BVH 树光线追踪
   - 优先级: ⭐⭐⭐⭐
   - 理由: 树遍历算法，分支预测敏感

#### 库函数优化（2 个）
9. **cudnn/105** - cuDNN 卷积优化
   - 优先级: ⭐⭐⭐⭐⭐
   - 理由: 深度学习核心算子

10. **cutile/37** - Cutile 原语
    - 优先级: ⭐⭐⭐⭐
    - 理由: 现代 CUDA 编程模式

### Phase 2: 构造 IPB 任务结构 (3-5 天)

对于每个选中的任务，需要：

1. **提取源代码**
   ```bash
   # 从 compute-eval 或原始仓库提取
   cp -r /path/to/source tasks/ipb_cuda_XXX/workspace/
   ```

2. **选择最佳变体**（每个任务选 2-3 个）
   - 从 5 个变体中选择欺骗性最高的
   - 确保变体类型多样（同步问题、算法降级、内存误用等）

3. **编写任务描述**
   ```
   tasks/ipb_cuda_XXX/
   ├── README.md          # 任务描述
   ├── prompt_normal.txt  # 正常提示词
   ├── prompt_fuzzy.txt   # 模糊提示词
   ├── prompt_misleading.txt  # 误导性提示词
   └── workspace/
       ├── solve.cu       # 待优化的文件
       ├── baseline.cu    # 已优化的基准
       └── Makefile
   ```

4. **验证性能差异**
   ```bash
   # 运行 baseline
   cd workspace && make && ./benchmark
   # 记录性能: baseline_time
   
   # 运行 slow variant
   cp slow_variant.cu solve.cu && make && ./benchmark
   # 记录性能: variant_time
   
   # 计算减速: variant_time / baseline_time
   ```

### Phase 3: 批量验证 (2-3 天)

使用现有的评测框架验证所有任务：

```bash
# 对每个新任务运行快速验证
for task in ipb_cuda_005 ipb_cuda_006 ...; do
  python run_single.py \
    --task $task \
    --variant normal \
    --model gpt-5.6-luna \
    --max-turns 10
done
```

**验证指标**：
- ✅ 模型能否在 10 轮内找到优化点
- ✅ 优化后的代码是否通过测试
- ✅ 性能提升是否达到预期（≥ 2×）
- ✅ fuzzy/misleading 变体是否增加难度

## 中期计划 (2-4 周)

### 1. 扩展到所有 35 个任务

优先级排序：
1. CUDA 核心算法 (21 个) - 第一批
2. CPU 算法 (4 个) - 第二批
3. cuDNN/cuFFT (3 个) - 第三批
4. cutile (3 个) - 第四批
5. 大型项目 (2 个) - 最后
6. cuRAND/cuSOLVER (2 个) - 按需

### 2. 模型对比实验

使用 gpt-5.6-terra 重新评测现有任务：
```bash
python run_batch.py \
  --tasks cuda_001,cuda_002,cuda_003,cuda_004 \
  --variants normal,fuzzy,misleading \
  --models gpt-5.6-terra,gpt-5.6-luna \
  --runs 3
```

分析维度：
- 模型在不同算法类型上的优势
- fuzzy vs misleading 的难度差异
- 模型对不同欺骗性模式的敏感度

### 3. 从其他数据集补充

**NL2RepoBench**:
- 搜索 CUDA kernel 相关的任务
- 提取涉及性能优化的场景

**ParEval-Repo**:
- 重点关注 model training 相关的任务
- 提取分布式训练、混合精度等场景

**compute-eval 深度挖掘**:
- 重新审视被跳过的任务
- 寻找更多 cuRAND/cuSOLVER 案例

## 长期目标 (1-3 个月)

### 1. 建立完整基准套件

目标：**100+ 高质量任务**

领域覆盖：
- [ ] GPU 并行算法 (40%)
- [ ] 深度学习原语 (25%)
- [ ] 科学计算 (15%)
- [ ] 系统编程 (10%)
- [ ] 模型训练优化 (10%)

### 2. 自动化变体生成

开发工具链：
```
analyze_task.py --> generate_variants.py --> validate_variants.py
```

每个阶段自动化：
- 静态分析识别热点
- LLM 生成候选变体
- 性能测试验证减速
- 代码正确性测试

### 3. 建立模型能力图谱

跟踪不同模型在各类任务上的表现：
- 算法类型 × 模型 的热力图
- 识别每个模型的强项和弱项
- 指导未来模型改进方向

## 技术债务

1. **当前 journal.jsonl 数据的持久化**
   - 将 35 个任务的分析结果导出为结构化格式
   - 建立索引便于后续查询

2. **变体代码生成**
   - 当前只有文本描述，需要生成实际代码
   - 可以用 LLM 辅助生成并人工审核

3. **性能基准数据**
   - 需要实际运行并记录每个变体的性能
   - 建立性能数据库

## 即时行动检查清单

本周内完成：
- [ ] 从 journal.jsonl 提取 10 个高优先级任务的完整分析
- [ ] 查看这些任务在 compute-eval 中的源代码位置
- [ ] 为每个任务选择 2-3 个最佳变体
- [ ] 构造第一个新任务（如 CUDA/27）的完整 IPB 结构
- [ ] 运行验证确保变体产生预期的性能差异
- [ ] 使用 gpt-5.6-luna 测试新任务

下周继续：
- [ ] 批量构造剩余 9 个任务
- [ ] 并行化任务构造流程（可以用 workflow）
- [ ] 开始模型对比实验
