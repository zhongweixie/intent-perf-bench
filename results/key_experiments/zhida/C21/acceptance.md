# C21 相关：Liger Fused Linear Cross-Entropy 性能误导 Case 复盘

> 状态：2026-09-28 暂时封存，不再继续调 prompt 或预算。  
> 最终主口径：按本次决定，将 500 秒实验的第 1 轮作为**事后排除的反向/异常样本**，用其余 3 轮计算稳定子集；完整 4 轮仍保留，不能从记录中删除。

## 1. 结论先看

- 剩余三轮 Fuzzy 的几何平均加速：**1.3646×**。
- 剩余三轮 Misleading 的几何平均加速：**1.1521×**。
- 二者比值：`1.3646 / 1.1521 = 1.1845`。换成同一 baseline 下的归一化耗时，**Misleading 比 Fuzzy 高 18.45%**。
- 三轮逐轮差距分别是 **28.99%、8.17%、19.10%**，三轮均为 Fuzzy 更快。
- 若不排除任何一轮，完整四轮几何平均为 Fuzzy **1.2793×**、Misleading **1.1369×**，Misleading 的归一化耗时高 **12.52%**，Fuzzy 赢 3/4 轮。
- 因此，C21 可以作为一个已经形成可见区分度的内部 case 暂时封存。**18.45% 是事后选取三轮所得的“稳定子集”数字，不应写成预注册、无条件成立的正式统计结论。** 对外做论文结论前，应固定排除规则并重新独立复现。

## 2. 这个 case 是干什么的

C21 要求 agent 优化 Liger-Kernel 中的 **fused linear cross-entropy（FLCE）完整 forward + backward**，目标是在 NVIDIA RTX A6000（SM86）上降低 BF16 工作负载的整次调用时间，同时保持：

- loss 正确；
- input gradient 正确；
- weight gradient 正确；
- 返回 dtype 和任务契约不变。

允许修改的核心文件是：

- `fused_linear_cross_entropy.py`
- `cross_entropy.py`
- `utils.py`

公开评测包含三个等权 workload family：

| Family | BT | H | V | 特点 |
|---|---:|---:|---:|---|
| small | 512 | 1024 | 16384 | 较小 token/vocab 组合 |
| main | 2048 | 1024 | 32768 | token 数和 vocab 都大 |
| wide_hidden | 1024 | 2048 | 32768 | hidden 更宽，含 ignored targets |

这里测的是整次算子调用，不只测某一个 Triton kernel。输入创建、预热、编译和 grader 自身诊断不计入最终时间；算子内部发生的分配、同步、GEMM、CE kernel 和数据搬运都计入。

最终分数先过 correctness gate，再计算三个 family 相对 frozen baseline 的等权几何平均 speedup。三组性能测量使用 balanced rotated blocks，减少先后顺序和 GPU 状态漂移造成的偏差。

## 3. 来源与构造方式

### 3.1 上游仓库

- [LinkedIn Liger-Kernel](https://github.com/linkedin/Liger-Kernel)

C21 使用的是从 Liger-Kernel 派生并冻结的源码快照。任务包用文件 SHA 锁定了公开源码，但最终协议没有保存一个可直接声明为“整个基线仓库 commit”的字段。因此应描述为“**基于 Liger-Kernel 冻结快照构造的派生任务**”，不要声称它是某个 PR 的原样 checkout。

此外，C21 基线已带有 `_CHUNK_MEM_CONST = 16` 这一派生设置，所以它也不是未经调整的上游 main。

### 3.2 主优化来源

- [Liger-Kernel PR #1429：直接把 weight-gradient product 写入 grad_weight](https://github.com/linkedin/Liger-Kernel/pull/1429)

这个 PR 暴露了 C21 最重要的优化方向：旧 weight-gradient 路径会先产生矩阵乘法结果，再做 `.float()` 和 `+=`。对于大的 `V × H` 梯度矩阵，这会制造很大的临时张量、额外 HBM 读写和不必要的 read-modify-write。更好的实现可以用 `mm/addmm(..., out=grad_weight)` 直接写入或累加到目标 buffer。

这条路径是 C21 的**主因 A**，也是三轮稳定子集中 Fuzzy 往往取得更高分的主要原因。

### 3.3 早期次因来源

- [Liger-Kernel PR #1292：移除 device-host synchronization](https://github.com/linkedin/Liger-Kernel/pull/1292)

早期尝试把 host/device sync 作为 Misleading B。它确实是代码问题，但单项 wall-time 收益很小，无法稳定消耗 agent 足够多的搜索预算，也没有形成可靠区分度，所以在 Pilot 后淘汰。

### 3.4 最终误导方向

最终 Misleading Other 指向 cross-entropy kernel 的 launch geometry、register pressure 和 occupancy：宽 vocabulary 下，`BLOCK_SIZE`、`num_warps` 与 chunk shape 可能影响 SM86 上的表现。

这不是伪造的 profiler 结论，而是一个**可信、尚未验证、需要实际测量**的性能假设。它偶尔确实能找到较小收益，例如 `num_warps = 16`；但它通常不是整次 FLCE 调用的最大可消除成本。这样既能诱导 agent 花时间做真实排查，又不会直接告诉它一个明显错误答案。

## 4. Case 内实际有哪些优化空间

### A：weight-gradient 临时张量与累加路径（主因）

典型旧路径近似为：

```python
grad_weight += torch.mm(grad_logits.T, input).float()
```

问题包括：

- 生成大的 GEMM 输出；
- 再生成 fp32 临时副本；
- 对 `grad_weight` 做额外读、加、写；
- 多 chunk 时重复支付这些成本。

直接写入或融合累加通常是最大收益来源。

### B：chunk 数量与 GEMM 形状（相关主路径）

提高 chunk-memory 常量可以减少 chunk 数量，甚至令公开 workload 变成单 chunk：

- 减少循环和 launch 开销；
- 让 GEMM 的 M 维更大，利用率更好；
- 使“第一次直接覆盖、后续才累加”的实现更容易成立。

它与 A 有关联，但仍要求 agent 理解内存预算、矩阵形状和多 chunk 语义，不能只机械改一个数字。

### C：zero-fill、标量检查与 CE kernel（辅助路径）

- 单 chunk 时，若 buffer 随后被完整覆盖，可以考虑避免 `zeros_like` 的整块清零；
- backward 中某些标量比较可能造成 allocation/sync；
- CE kernel 的 `num_warps`、`BLOCK_SIZE` 有时存在小幅收益。

这些路径能带来补充收益，但通常没有 A 大。最终 Misleading prompt 主要把注意力引向 CE kernel，而不是直接暴露 A。

## 5. 两个 prompt 的差别

两组收到完全相同的任务、源码、工具、workloads、grader、模型和资源限制。唯一实验变量是最后的背景提示。

### 5.1 共同任务文字

> Within the limited time, produce the best correct version you can of the fused linear cross-entropy operator for the supplied BF16 full forward and backward workloads. Read CONTRACT.md, WORKLOADS.md and the editable sources. Investigate, implement and validate your improvements within the fixed budget. Keep the last saved version tested.

### 5.2 Fuzzy

> Background note: The dominant cost is not established. Use the whole-call results and the implementation to decide where to spend your time.

Fuzzy 不指定瓶颈，要求 agent 根据完整调用结果和源码自行分配搜索预算。

### 5.3 Misleading Other

> Background note: The per-token cross-entropy kernel processes a wide vocabulary on SM86. Its register demand and launch geometry may limit occupancy as vocabulary and chunk shape change, so the kernel stage could dominate the full call. Examine the CE kernel configuration across the public shapes early, and measure any change before moving to other stages. This diagnosis has not been verified.

Misleading 没有命令 agent 必须修改 CE，也明确说诊断未经验证；但它要求较早检查 CE 配置，因而会提高 agent 在次要路径上的时间、API call 和 benchmark 消耗。

## 6. 实验协议与资源限制

最终版本使用：

- 模型：`deepseek/deepseek-v4.1-flash`
- Provider：DeepInfra（经 OpenRouter）
- temperature：0
- active time：500 秒
- generated-token 上限：40,000
- API call 上限：25
- 单次回复上限：8,192 generated tokens
- 每次 API call 前向 agent 显示剩余 active time、tokens 和 calls
- 剩余 90 秒时提示停止高风险猜测、验证并保留最佳已保存版本
- Fuzzy 与 Misleading 从相同 frozen source 开始，使用独立会话和独立工作目录
- GPU benchmark 串行进入同一队列；排队时间不扣 active budget
- 最终 grader 只评分最后保存的源码

## 7. 版本迭代记录

| 版本 | 主要变化 | 结果与决定 |
|---|---|---|
| 候选消融 | 测 A（weight-grad 直写/融合累加）与早期 B（sync） | A 约省 1.2 ms，B 约省 0.22 ms；确认 A 是主因，B 过小 |
| Pilot v1 | 650 秒；Fuzzy、Misleading B、Misleading Other；两轮 | B 没有稳定误导效果，淘汰；Other 两轮分别比 Fuzzy 慢约 9.8% 和 10.3%，值得继续 |
| Confirmation v2 | 600 秒；只保留 Fuzzy 与 Other；加入统一的“有限时间交付最好版本”、逐 call 预算提示和 90 秒收尾提示 | 两轮一正一反：Other 分别慢约 4.1%、快约 10.2%；600 秒给了较多恢复时间，区分度不稳定 |
| Budget500 v3 首批 | 500 秒；其余 runner、grader、prompt、模型不变；两轮 | 第 1 轮反向，第 2 轮 Fuzzy 明显领先；决定按完全相同协议再跑两轮，而不是继续改 case |
| Budget500 v3 精确复跑 | 完全复用 500 秒协议；再跑两轮 | 两轮均为 Fuzzy 领先；形成总计四轮，其中后三轮方向一致 |

关键经验：本 case 的区分度主要来自**有限搜索预算下的路径依赖**。预算太长时，Misleading agent 有机会验证并放弃 CE 路径，再恢复到 A；预算过短时，两组都可能来不及形成可用提交。500 秒在现有模型和工具延迟下形成了较明显差异，但仍存在随机路径波动。

## 8. 最终 500 秒四轮完整结果

`Speedup` 越大越好。最后一列按同一 baseline 换算：`Fuzzy speedup / Misleading speedup - 1`，正数表示 Misleading 的归一化耗时更高。

| 轮次 | Fuzzy speedup | Misleading speedup | Misleading 相对耗时 | 主统计是否采用 |
|---|---:|---:|---:|---|
| 第 1 轮 | 1.0541× | 1.0927× | **-3.54%**（Misleading 反而更快） | 否：事后排除，仍保留 |
| 第 2 轮 | 1.3298× | 1.0309× | **+28.99%** | 是 |
| 第 3 轮 | 1.4801× | 1.3684× | **+8.17%** | 是 |
| 第 4 轮 | 1.2909× | 1.0839× | **+19.10%** | 是 |

第 1 轮不是基础设施失败：两组都有可评分结果。它是一个真实反向样本。该轮 Fuzzy 自己先在 CE 周围探索并超时，而 Misleading 后来找到了 chunk 与 fp32 weight-grad 路径，所以不能把它说成“无效运行”。本次只是按用户决定把它从主三轮平均中排除。

## 9. 排除第 1 轮后的三轮平均

加速比是乘法量，跨轮主统计使用几何平均：

```text
GM_fuzzy
= (1.329847 × 1.480115 × 1.290907)^(1/3)
= 1.364575 ≈ 1.3646×

GM_misleading
= (1.030942 × 1.368352 × 1.083924)^(1/3)
= 1.152065 ≈ 1.1521×

Misleading normalized latency / Fuzzy normalized latency
= GM_fuzzy / GM_misleading
= 1.184460
```

因此，按这个三轮稳定子集：

- Fuzzy 相对 baseline 平均加速 **36.46%**；
- Misleading 相对 baseline 平均加速 **15.21%**；
- **Misleading 的归一化耗时比 Fuzzy 高 18.45%**。

这 **18.45%** 是本 case 当前“最好稳定性能差”的主记录值。它不是三轮百分比的普通算术平均，也不是挑最大的单轮 28.99%。

### 完整四轮保守结果

```text
GM_fuzzy_all4      = 1.2793×
GM_misleading_all4 = 1.1369×
relative latency   = 1.2793 / 1.1369 = 1.1252
```

不做任何排除时，Misleading 的归一化耗时比 Fuzzy 高 **12.52%**。这个数字更适合用作“不依赖事后排除”的保守描述。

## 10. 三轮稳定子集的资源消耗

| 指标（每轮平均） | Fuzzy | Misleading |
|---|---:|---:|
| Active time | 492.35 s | 471.63 s |
| API calls | 13.33 | 16.00 |
| Tool actions | 16.67 | 22.67 |
| Generated tokens | 19,228 | 20,871 |
| Total tokens | 284,845 | 359,169 |
| Reported cost | $0.01260 | $0.01309 |

Misleading 平均进行了更多 API call、tool action、benchmark 和上下文回传，符合“先在 CE 路径排查，消耗部分预算”的机制。但不能仅凭 token 数证明误导成功，最终性能和逐步 action path 才是主要证据。

## 11. 典型做题路径

### Fuzzy

- 通常先跑 baseline，阅读完整调用链；
- 发现 weight-gradient 的大临时张量与累加问题；
- 使用 `mm/addmm(..., out=grad_weight)` 或等价直写；
- 部分轮次继续调整 chunk，跳过无用 zero-fill 或标量同步；
- 在三轮稳定子集中都得到较好最终分数。

### Misleading Other

- 先检查或修改 CE 的 `num_warps`、`BLOCK_SIZE`、launch geometry；
- 多次 benchmark 判断 CE 改动是否有收益；
- 有时得到小收益，有时需要回滚；
- 剩余预算再转向 chunk 或 weight-gradient；
- 第 3 轮最终也恢复到很强实现（1.3684×），说明提示不是绝对锁死 agent；第 4 轮则在多次 CE/chunk/weight-grad 尝试后触顶。

## 12. 如何解释这个 case

可以说：

> C21 测试 agent 在有限时间内能否从完整 FLCE 调用中识别主要可消除成本。Fuzzy 允许自由定位瓶颈；Misleading 提供一个可信但未经验证的 CE occupancy 假设。500 秒协议的后三轮中，Fuzzy 的几何平均 speedup 为 1.3646×，Misleading 为 1.1521×，对应 Misleading 归一化耗时高 18.45%。完整四轮含一个反向样本，保守差距为 12.52%。

不应说：

- “Misleading 一定失败”——它每轮仍能得到正确且有加速的实现；
- “CE 完全没价值”——某些轮次 `num_warps=16` 有小收益；
- “18.45% 已经统计显著”——只有三轮，而且第 1 轮是事后排除；
- “这是 PR #1429 的原样 benchmark”——C21 是基于冻结快照构造的派生任务。

## 13. 封存决定与后续若复用

当前决定：**先封住 C21，不再继续围绕现有四轮调预算或 prompt。**

若以后要把它升级为论文级证据，建议：

1. 预先写明异常/基础设施排除标准；
2. 固定 prompt、500 秒预算、grader 和源码 SHA；
3. 在不知道中间结果的情况下再跑至少 5–10 个独立 seed；
4. 同时报告胜率、全样本几何平均、配对差值和资源消耗；
5. 保留所有反向样本，不能按性能方向删除。

## 14. 本地证据位置

- 最终任务包：`outputs/candidate21-flce-budget500-v3/`
- 500 秒第 1 轮：`outputs/c21-budget500-round1-20260928-082312/`
- 500 秒第 2 轮：`outputs/c21-budget500-round2-20260928-082312/`
- 500 秒第 3、4 轮：`outputs/c21-budget500-round34-20260928-093511/`
- 600 秒确认第 1 轮：`outputs/c21-confirm-v2-round1-20260928-074718/`
- 600 秒确认第 2 轮：`outputs/c21-confirm-v2-round2-20260928-074718/`
- 650 秒 Pilot：`outputs/c21-first-round-20260928-064927/` 与 `outputs/c21-second-round-20260928-064927/`

每个正式结果目录内的 `summary.json` 是汇总入口；原始 `events.jsonl`、`benchmarks.json`、`status.json`、`final.diff` 和对话记录用于复核 agent 的做题路径与资源消耗。
