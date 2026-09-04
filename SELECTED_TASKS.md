# 选定的 5 个 IPB CUDA 任务

生成时间：2024-08-20

## 任务列表

我们从现有的 CUDA 任务中选择了以下 5 个任务进行完整构造：

### 1. ipb_cuda_001 - Huffman Decode CUDA 性能回归
- **减速倍数**: 21.8x (124.3ms → 5.7ms)
- **难度**: 中等
- **性能问题**: 内存访问模式低效
- **状态**: 已有 workspace 和 git 历史，需要补充 benchmark 脚本

### 2. ipb_cuda_002 - ICP Correspondence CUDA 性能回归
- **减速倍数**: 42.5x (340ms → 8ms)
- **难度**: 中等
- **性能问题**: Kernel 配置次优
- **状态**: 已有 workspace 和 git 历史，需要补充 benchmark 脚本

### 3. ipb_cuda_003 - NTT Butterfly CUDA 性能回归
- **减速倍数**: 6.4x (320ms → 50ms)
- **难度**: 中等
- **性能问题**: Bank conflicts 和同步问题
- **状态**: 已有 workspace 和 git 历史，需要补充 benchmark 脚本

### 4. ipb_cuda_004 - BLS12-381 G1 MSM CUDA 性能回归
- **减速倍数**: 10.6x (624ms → 59ms)
- **难度**: 困难
- **性能问题**: 复杂的密码学计算优化
- **状态**: 已有 workspace 和 git 历史，需要补充 benchmark 脚本

### 5. ipb_cuda_005 - L2 Norm 分层归约性能回归
- **减速倍数**: 5.6x (4.5ms → 0.8ms)
- **难度**: 中等
- **性能问题**: 过度同步
- **状态**: **接近完成**，有完整实现和测试

## 当前工作总结

### 已完成

1. ✅ **选定 5 个任务**
   - 覆盖不同的性能问题类型
   - 覆盖不同的减速倍数 (5.6x - 42.5x)
   - 覆盖不同的难度等级

2. ✅ **构造了 ipb_cuda_005 (L2 Norm Reduction)**
   - 完整的 workspace 结构
   - solve.cu 的 baseline 和 regression 版本
   - Git 历史记录
   - main.cu 测试框架
   - 验证和性能测试都通过

3. ✅ **创建了基础设施**
   - `validate_tasks.py` - 任务验证脚本
   - `setup_tasks.sh` - 批量设置脚本
   - `templates/bench.sh` - 通用 benchmark 脚本模板
   - `TASK_STRUCTURE.md` - 任务结构文档
   - `TASK_STATUS.md` - 任务状态追踪

### 待完成

1. **补全所有任务的 benchmarks/**
   - 为每个任务复制并调整 bench.sh
   - 验证 benchmark 脚本能正确提取时间

2. **补全所有任务的 variants/**
   - fuzzy.md - 模糊描述
   - misleading.md - 误导性描述
   - 基于每个任务的具体特征编写

3. **验证所有任务**
   - 运行 validate_tasks.py
   - 测试每个任务的编译
   - 测试每个任务的正确性
   - 测试每个任务的性能回归

4. **运行批量评测**
   - 使用 gpt-5.6-luna
   - 使用 gpt-5.6-terra
   - 对比两个模型的表现
   - 统计 fuzzy vs misleading 的 ΔScore

## 下一步操作

### 立即执行（优先级高）

```bash
# 1. 运行设置脚本
cd /aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench
chmod +x setup_tasks.sh
./setup_tasks.sh

# 2. 验证任务状态
python3 validate_tasks.py

# 3. 测试 ipb_cuda_005 的完整流程
cd tasks/ipb_cuda_005_l2norm_reduction
make clean && make
srun -p llm-debug --qos=llm_debug --gres=gpu:1 ./reduce_benchmark --verify
./benchmarks/bench.sh
```

### 批量验证（优先级高）

对每个任务执行：
1. 检查 workspace/Makefile 能否编译
2. 检查测试能否通过
3. 检查性能回归是否可测量
4. 记录实际的 baseline 和 regression 时间

### 补全缺失组件（优先级中）

1. 为每个任务编写特定的 variants/fuzzy.md
2. 为每个任务编写特定的 variants/misleading.md
3. 确保每个 bench.sh 能正确提取时间

### 批量评测（优先级中）

```bash
# 使用现有的评测框架
export OPENAI_API_KEY=sk-TRZO8TfMYIiLnDh7ERofq7sxF3iDRrU4r4aY0OStcZ8yucN1
export OPENAI_BASE_URL=https://chatapi.zjt66.top/v1

# 对每个任务运行 luna 和 terra
for task in ipb_cuda_001 ipb_cuda_002 ipb_cuda_003 ipb_cuda_004 ipb_cuda_005_l2norm_reduction; do
    ./ipb_py310_env/bin/python scripts/run_agent.py \
        --task-id $task \
        --variant normal \
        --provider openai \
        --model gpt-5.6-luna \
        --max-turns 15

    ./ipb_py310_env/bin/python scripts/run_agent.py \
        --task-id $task \
        --variant normal \
        --provider openai \
        --model gpt-5.6-terra \
        --max-turns 15
done
```

## 预期时间投入

- **补全基础设施**: 2-3 小时
- **验证所有任务**: 3-4 小时
- **运行批量评测**: 每个模型 5-8 小时（可并行）
- **分析结果**: 2-3 小时

**总计**: 约 15-20 小时工作量

## 成功标准

一个任务被认为"准备好"当：

1. ✅ task.toml 完整且准确
2. ✅ workspace/ 可以编译
3. ✅ 测试通过（正确性）
4. ✅ 性能回归可测量且显著（>2x）
5. ✅ Git 历史清晰
6. ✅ benchmarks/bench.sh 能运行并输出 JSON
7. ✅ variants/ 文件存在且有意义

## API 配置

评测使用的 API：
```bash
OPENAI_API_KEY=sk-TRZO8TfMYIiLnDh7ERofq7sxF3iDRrU4r4aY0OStcZ8yucN1
OPENAI_BASE_URL=https://chatapi.zjt66.top/v1
```

模型：
- gpt-5.6-luna
- gpt-5.6-terra

## 文件清单

已创建的基础设施文件：
- ✅ `/aifs4su/.../intent-perf-bench/TASK_STRUCTURE.md`
- ✅ `/aifs4su/.../intent-perf-bench/TASK_STATUS.md`
- ✅ `/aifs4su/.../intent-perf-bench/SELECTED_TASKS.md` (本文件)
- ✅ `/aifs4su/.../intent-perf-bench/validate_tasks.py`
- ✅ `/aifs4su/.../intent-perf-bench/setup_tasks.sh`
- ✅ `/aifs4su/.../intent-perf-bench/templates/bench.sh`

待创建的任务组件：
- ⏳ 每个任务的 benchmarks/bench.sh
- ⏳ 每个任务的 variants/fuzzy.md
- ⏳ 每个任务的 variants/misleading.md
