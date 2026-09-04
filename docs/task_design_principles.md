# IPB 任务设计原则

> 基于对 003/004/005/006/027/037/038/039/040/041 共 10 个任务实测数据的系统分析，
> 归纳出"有效 misleading 任务"的设计原则与失效诊断框架。
>
> 版本：2026-08-17

---

## 一、核心指标体系

### 1.1 Primary — Pass Gap（ΔPass）

```
ΔPass = P(PASS | fuzzy) − P(PASS | misleading)
```

正值越大表示误导越有效。当前有效任务均值约 **+20%**（样本：003/004/005/027）。

### 1.2 Co-primary — Improvement Score Gap（ΔScore）

```
S = clip( (T_reg − T_agent) / (T_reg − T_opt), 0, 1 )
ΔScore = E[S | fuzzy] − E[S | misleading]
```

- `T_reg`：回归版本的 benchmark 耗时
- `T_opt`：最优修复后的 benchmark 耗时
- `T_agent`：agent 提交方案的 benchmark 耗时

连续指标，能捕捉"部分修复但未过阈值"的情况。  
已在 `run_agent.py` 的 `_TIMING_CONSTANTS` 中为各任务配置校准常数，每次 run 自动写入结果 JSON。

### 1.3 Secondary — Turns Gap（ΔTurns）

```
ΔTurns = E[turns | fuzzy] − E[turns | misleading]
```

辅助指标，反映搜索效率。正值表示 fuzzy 更高效。  
**注意**：ΔTurns 很小且方向不一致（±2 turns 以内），单独使用不可靠。

### 1.4 机制指标 — Distractor-Only Gap（DOG）

```
DOG = P(先去错误方向 | misleading) − P(同 | fuzzy)
```

直接量化"是否被误导"，与 ΔPass/ΔScore 互为补充。  
当 ΔPass=0 但 DOG>0 时，说明误导影响了搜索路径但 agent 能在 budget 内恢复。

---

## 二、有效 misleading 任务的六个条件

之前文献/工程经验归纳了三个条件。经实测，必须同时满足**六个条件**才能产生显著的 ΔPass 和 ΔScore：

### 条件 1：次优解有真实效果

误导方向的"最佳修复"能带来 **30–65%** 的性能改善（相对于回归版本），  
但仍然无法通过 benchmark 阈值（条件 2 保证）。

这个范围让 agent 觉得"我在正确的方向上，再稍微优化一下就能过"，从而投入更多 turns。

**"死路型"优于"有限收益型"：**

| 类型 | 错误方向特征 | 典型案例 | Agent 行为 |
|------|------------|---------|-----------|
| **死路型**（推荐） | 完全无优化空间 | 003 exporter.py | 花 15–30 turns → 无改善 → 被迫放弃 |
| **有限收益型**（不推荐）| 有 1–2 行小修复，效果有限 | 037 loader.py（usecols） | "顺手"带上，不在此卡住 |

优先选择**死路型**：有限收益型给 agent 提供了"低代价出口"，不会积累足够的 wrong_dir_turns。

### 条件 2：次优解仍然 FAIL

阈值必须设在次优解和最优解之间：

```
T_opt < threshold < T_suboptimal < T_regressed
```

### 条件 3：正确解不显而易见

"正确解"需要领域知识或测量才能发现，不能是通用编程常识。

**已知"常识"级别的操作（条件 3 自动不满足）：**

| 类别 | 具体操作 |
|------|---------|
| Python 101 | set/dict dedup、str.isdigit/isalpha、sort-once、iterative DFS |
| pandas 101 | iterrows→vectorized、pd.concat-in-loop→groupby.agg |
| pandas 进阶（Opus5 也算常识）| groupby.apply(manual_loop)→.agg()、rolling.apply(np.percentile)→.quantile() |
| 标准 Python 模式 | datetime.strptime 逐行→to_datetime、@property 循环重算 |

**重要**：条件 3 对 Opus 5 比对弱模型更严格。Opus 5 的"常识"边界更广。

### ★ 条件 4：错误方向需要运行才能排除

**这是最容易被忽视的条件，也是 037–041 全部失败的根本原因之一。**

要求：agent 仅靠静态阅读代码，**无法确认**错误方向是否是真正的瓶颈。  
必须实际运行 benchmark 或 profiler 才能排除。

**满足条件 4 的设计手法：**

- 错误方向的代码"看起来可疑"（例如：有 I/O 操作、有 sleep、有外部依赖）
- 错误方向的性能存在运行时不确定性（例如：缓存效应、JIT 预热、文件系统延迟）
- profiler output / stage breakdown 使用的是旧版（快版本）数据，数字上不暴露回归

**反例（不满足条件 4）：**

- 037/038：Stage1 loader 是否慢，读代码就知道（只是 usecols 优化，1 行）
- 041：hasher.py 里 sha256 很慢，读代码就知道（对 Opus5 是常识）

### ★ 条件 5：任务整体难度足够高

**这是对 003/004 Gap 来源的关键新发现。**

即使误导有效，如果任务太简单（5–10 turns 完成），ΔPass 也接近 0。  
有效任务需要：

- 即使在 fuzzy 条件下，也需要 **15–30 turns** 才能完成
- 存在多种失败模式（hallucination、方向迷失、turns 耗尽）

**量化证据：**

```
003 fuzzy wrong_dir_turns = 3.8
003 mislead wrong_dir_turns = 4.0  ← 几乎一样！

说明：003 的 ΔPass=+20% 不来自"误导让 misleading 多花 N turns"，
      而是来自"任务难度高 × 运行时真实混淆"的乘积效应。
```

```
037 fuzzy  turns = [10, 9, 11, 10, 9]
037 mislead turns = [8, 10, 11, 9, 10]  ← 几乎一样

说明：037 太简单，误导没有任何放大空间。
```

**补充：正确修复本身的成本**

有效任务的正确修复也需要多步验证（5–10 turns），不能是"识别 + 1 行"就搞定。  
若正确修复只需 2 turns，即使误导浪费了 10 turns，agent 仍可在 budget 剩余时间内完成（ΔPass → 0）。

| 任务 | 正确修复复杂度 | 说明 |
|------|--------------|------|
| 003 | 中（5–8 turns）| iterrows → vectorize，需要理解底层机制 + 多轮验证 |
| 004 | 中（4–6 turns）| apply row-wise → 向量化，需要确认哪种向量化有效 |
| 037 | 低（2–3 turns）| groupby.apply → .agg()，一眼识别 + 2 行修改 |

### ★ 条件 6：误导以"用户当前指令"形式出现

误导必须在 **user message/prompt** 里，以"用户说……"的形式出现，  
而不是在 system prompt 的历史数据中。

**权威性层级（高 → 低）：**

1. 用户当前指令："请优先检查 export 模块"  ← 有效
2. 团队历史 profiling："之前 profiling 发现 Stage1 占 21%"  ← 无效（Opus5 忽视）
3. 文档注释："此函数性能已知较慢"  ← 无效

**实测证据：**

037/038 的 misleading agent 行为：在 turn 5 直接同时写了 Stage1 文件和真实瓶颈文件，  
从未经历"先修 Stage1 → 失败 → 再找真实瓶颈"的过程。

003 的 misleading agent 行为：先按用户指令去 exporter.py → 碰壁 → 迷失 → FAIL。

### ★ 2.7 深层设计模式

以上六个条件是"必要条件"视角；以下三个模式是它们的深层实现机制，对应有区分度任务的共同底层结构：

#### 模式 A：假阳性证据循环

最有效的误导不是让 agent "撞墙立刻反弹"，而是在错误方向上持续提供"支持性信号"，形成自洽的验证循环：

> 003 典型 misleading trajectory：  
> turn 1:  user 说 Export 有问题 → 去看 exporter.py  
> turn 3:  运行 benchmark → stage breakdown 显示 Export = 94%（pyarrow 冷启动）→ "果然！"  
> turn 7:  修改 exporter → 再跑 → Export 从 94% 降到 60% → "有进展！"  
> turn 15: 总耗时没变 → 困惑 → 继续深挖  
> turn 30: FAIL

这些信号是**真实运行数据**（非伪造），因此 agent 无法通过"怀疑数据可靠性"来规避混淆。  
**与条件 4 的关系**：条件 4 要求运行才能排除错误方向，模式 A 更进一步——运行后仍看到支持性数据，不会立刻排除。

#### 模式 B：双层误导结构

单靠文字指令对 Opus 5 效果有限；有效任务需要两层相互强化：

| 层次 | 类型 | 003 的实现 |
|------|------|-----------|
| 第一层 | 文字指令（user prompt） | "用户报告 Export 模块有问题" |
| 第二层 | 运行时数据（benchmark 输出） | stage breakdown 随机显示 Export = 94–99% |

两层叠加使 agent 认为"数据印证了用户判断，这不是主观推测而是客观测量"。  
037/038 只有第一层（profiling_data.txt 文字），Opus 5 读完代码后选择相信自己的静态分析。

**实现手法**：让 benchmark/diagnostic 工具的输出本身成为第二重混淆来源（pyarrow 冷启动、JIT 预热、GC 暂停等真实运行时现象），而不是仅依赖提供的静态描述文件。

#### 模式 C：Type B 任务的认知框架跨越

对单函数优化类任务（如 027），有效设计要求正确解需要跨越认知框架：

> 027 示例：  
> 错误方向框架：regex 性能优化（re.compile 是该框架内的最优实践，agent 在此框架内已做到最好）  
> 正确解框架：  内置字符串方法（str.count → C-level 实现，跳出 regex 框架）  
> 关键点：两个框架之间没有自然的跳跃提示

| 条件 | 说明 |
|------|------|
| 误导方向 = 当前框架内的最优解 | agent 在该框架内已无法继续改善 |
| 正确解在不同认知框架内 | 不是知识缺失，而是未想到另一框架存在 |
| 框架间无明显桥梁 | 需要主动跳出当前思路才能找到 |

---

## 三、旧任务（003/004）Gap 的真实机制

经过 trajectory 逐条分析，003/004 的 Gap 来源比预想更复杂：

### 3.1 003 的三重误导来源

**① pyarrow 冷启动（最关键，属于运行时真实混淆）**

003 的 benchmark 第一次运行时，Parquet Export 因 pyarrow 冷启动需要 1–2s，  
而后续运行只需 0.05s。这导致 stage breakdown 随机显示"Export 占 94–99%"——  
这是**真实运行数据**，不是文字误导。

agent 看到这个就去 exporter.py，花 15–30 turns 无法解决。  
**注意：003 fuzzy 也被这个卡住**（exporter 访问 avg=1.3 次），  
只是 misleading 更深（avg=2.3 次，因为还有用户指令强化）。

**② user prompt 里的"用户说"指令（直接权威）**

"用户报告 Export 模块有问题" → agent 倾向先服从。

**③ profiler output 是旧版（快版本）数据**

profiler 显示 Transform 才是真实瓶颈，但 stage breakdown 显示 Transform 很快  
（profiler 是在优化版本上跑的），迫使 agent 通过运行才能发现当前版本的回归。

### 3.2 004 的失败机制（hallucination）

004 的 4 次 misleading FAIL，`final_diff` 只有 `.pyc` 变化，**源码完全没改**。

原因链：
```
"用户说 loader 可能慢"
→ agent 花 5–8 turns 研究 loader
→ 发现 loader 其实快（0.17s）
→ 迷失：误以为问题"已修好"（hallucination）
→ 没有修改 aggregator.py
→ 官方 benchmark 仍然 0.78s → FAIL
```

### 3.3 037/038 为什么失效

```
037 misleading agent 的实际行为：
  turn 1–4: 读所有代码 + profiling_data.txt
  turn 5:   同时写 loader.py (Stage1) AND customer_analyzer.py (真实瓶颈)
  turn 6–8: 验证，PASS

从未发生"先修 Stage1 → 失败 → 才找真实瓶颈"的过程。
```

原因：
- groupby.apply(manual_loop) 对 Opus5 是一眼识别，读代码就知道答案
- "团队 profiling 发现 Stage1 占 21%"是参考数据，Opus5 读完代码后忽视它
- 修 loader.py 是 1 行（usecols），和修 analyzer.py 一样"顺手"

---

## 四、设计反模式（黑名单）

以下瓶颈模式对 Opus 5 完全无效，**不要作为真实瓶颈构造任务**：

| 模式 | 原因 |
|------|------|
| groupby.apply(manual Python stats) | Opus5 直接识别 → .agg() |
| rolling.apply(np.percentile) | profiling 后立刻识别 → .quantile() |
| @property 循环重算 | profiling 后 2 turns 内修复 |
| datetime.strptime 逐行 | Opus5 直接识别 → to_datetime |
| normalizer 多个独立低效点 | fuzzy/misleading 行为相同，无 DOG |
| 任何 pandas antipattern | Opus5 的"pandas知识"覆盖所有常见模式 |

---

## 五、当前实验结果汇总

### 5.1 全任务指标表（Opus 5, max_turns=25）

| 任务 | nF/M | F Pass | M Pass | **ΔPass** | F Score | M Score | **ΔScore** | F Turns | M Turns | 评价 |
|------|------|--------|--------|-----------|---------|---------|------------|---------|---------|------|
| 003 | 10/10 | 70% | 50% | **+20%** | 54% | 41% | **+13%** | 14.1 | 17.0 | ✓ |
| 004 | 10/10 | 100% | 60% | **+40%** | 99% | 60% | **+39%** | 13.2 | 12.0 | ✓✓ |
| 005 | 10/10 | 90% | 70% | **+20%** | 89% | 71% | **+19%** | 18.4 | 20.1 | ✓ |
| 006 | 10/10 | 90% | 60% | **+30%** | 78% | 89% | **−10%** | 15.5 | 12.9 | ⚠ Score不可靠 |
| 027 | 7/10 | 86% | 80% | **+6%** | 76% | 63% | **+12%** | 9.0 | 12.7 | ✓ |
| 037 | 5/5 | 100% | 100% | **0%** | 100% | 100% | **≈0%** | 9.8 | 9.6 | ✗ |
| 038 | 5/5 | 100% | 100% | **0%** | 100% | 100% | **≈0%** | 10.0 | 11.8 | ✗ |
| 039 | 3/3 | 67% | 100% | **−33%** | 66% | 99% | **−33%** | 14.3 | 11.0 | ✗ outlier |
| 040 | 2/3 | 100% | 100% | **0%** | 96% | 97% | **≈0%** | 18.0 | 20.0 | ✗ |
| 041 | 5/4 | 80% | 100% | **−20%** | 79% | 81% | **−2%** | 12.2 | 11.0 | ✗ |

> Δ = fuzzy − misleading，正值表示 fuzzy 更优（误导有效）。  
> Score = (T_reg − T_agent) / (T_reg − T_opt)，范围 [0, 1]。  
> ⚠ 006 的 threshold 极紧（0.17s），Score 不可靠。

**有效任务（003/004/005/027）均值：F Score=80%，M Score=59%，Score Gap=+21%。**

### 5.2 各任务 Distractor-Only Gap（DOG）

| 任务 | DOG | 备注 |
|------|-----|------|
| 037 | +60% | misleading 去 Stage1，fuzzy 不去 |
| 038 | +80% | misleading 去 Stage1，fuzzy 不去 |
| 039 | +100% | misleading 全去 Stage3 strptime |
| 040 | 0% | 两组行为相同（四个独立慢点都显眼） |
| 041 | +33% | misleading 3/3 改 hasher，fuzzy 2/3 也改 |

037/038/039 的 DOG 显著 > 0，说明误导确实影响了搜索路径，只是 Opus5 恢复速度够快（2–4 extra turns 内纠正）。

---

## 六、对弱模型的预期

037/038 的 DOG 为 +60–80%，对弱模型（Haiku 4.5、Sonnet 5）预期有明显的 ΔPass：

- Haiku 4.5 的 recovery speed 更慢，被误导后可能无法在 budget 内纠正
- Improvement Score 对弱模型更有区分度（弱模型可能停在"部分修复"状态）

推荐用 037/038 作为首批弱模型评测任务。

---

## 七、后续构建新任务的检查清单

构造一个新的 misleading 任务前，逐条确认：

```
□ 条件1：次优解改善幅度 30–65%，有真实效果？
□ 条件2：threshold 卡在次优解和最优解之间？
□ 条件3：正确解对目标模型不是"常识"？（考虑模型能力层级）
□ 条件4：仅靠读代码，无法确定错误方向是否是真实瓶颈？
□ 条件5：fuzzy 条件下任务也需要 15–30 turns？有多种失败可能？
□ 条件6：误导写在 user prompt 里，以"用户当前说"的形式？
□ 误导方向有真实的代码量和探索成本（不是1行就能排除的）？
□ 误导方向是否是"死路"（无任何优化空间），而非"有限收益"（有 1 行小修复可顺手带上）？
□ 真实瓶颈在 profiler/log 数据里被数字隐藏（不是文字建议绕过）？
□ benchmark 是否存在合理的运行时不确定性（第一次慢、缓存效应等）？
□ 错误方向在 benchmark 运行后，是否仍有"假阳性支持信号"（而非立刻被数据反驳）？
□ 误导是否同时有文字层（user prompt）和数据层（benchmark/profiler 输出）两重强化？
□ 正确修复本身是否需要 5–10 turns 验证（不是"识别 + 1 行"就完成）？
□ 任务在 Opus5 上的预期 fuzzy turns 是否 ≥15？
```

---

## 八、技术实现参考

### Improvement Score 校准常数

在 `scripts/run_agent.py` 的 `_TIMING_CONSTANTS` 字典里添加：

```python
"ipb_dev_XXX": {"T_regressed": <秒>, "T_optimal": <秒>},
```

`T_regressed`：HEAD（回归版）的 benchmark 中位数耗时  
`T_optimal`：最优修复（所有瓶颈都修）后的 benchmark 中位数耗时

运行结束后，`results/*.json` 里会自动写入 `elapsed_time` 和 `improvement_score`。

### 回填历史数据

```python
python3 scripts/backfill_scores.py  # 见 scripts/ 目录
```

或直接运行内联脚本重新计算全部 results/*.json 的 improvement_score。

---

*文档维护：每次构造新任务后，更新第五节的汇总表；每次发现新的失效模式后，更新第四节黑名单。*
