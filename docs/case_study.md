# IPB Case Studies：有区分度任务的 Walk-through

本文档对五个有区分度的任务（003/004/005/006/027）逐一做结构性分析，覆盖：真实瓶颈、死路设计、两个 prompt 的区别、以及 misleading 条件下 agent 的典型失败轨迹。

---

## ipb_dev_003 Case Study

> **先说一个发现**：当前 workspace 的 git HEAD 是 `4b44b53 "Fix Transform stage performance regression"` ——上次有agent 已经跑通了这个任务，把修复 commit 进去了。评估时应该 reset 到 `8fd535f`。下面的walk-through 描述的是原始状态（at `8fd535f`）。

---

### 第一层：任务的物理结构

```
workspace/
├── pipeline/
│   ├── transformer.py   ← 真实瓶颈（regressed 版）
│   ├── exporter.py      ← 死路（misleading 目标）
│   ├── loader.py        ← 无关
│   ├── aggregator.py    ← 无关
│   └── ...
├── baseline_perf.log    ← 证据1：之前快
├── current_perf.log← 证据2：现在慢
├── profiler_output.txt  ← 证据3：cProfile
├── git.log              ← 证据4：提交历史（文本文件，非真实 git）
└── benchmarks/pipeline_bench.py
```

**关键设计细节**：`git.log` 是一个手工写的文本文件，commit hash 是伪造的（`b7c4d91`），而真实 git 里的 hash 是 `8fd535f`。这个文件跟 `current_perf.log`、`profiler_output.txt` 一起，是在 `8fd535f` 这个 commit 里一起写进去的——即构造回归的那一刻，作者同步伪造了所有"历史证据"。

---

### 第二层：真正的 bug

回归版`transformer.py` 的 `calculate_metrics()`：

```python
for idx, row in df.iterrows():
    customer_id = row['customer_id']
    # 对每一行，扫描该客户的所有历史行
    mask = (df['customer_id'] == customer_id) & (df.index <= idx)
    customer_txns = df[mask]# O(n) per row
    
    txn_count = len(customer_txns)
    cumulative = customer_txns['amount'].sum()
    avg = cumulative / txn_count
    
    df.at[idx, 'txn_count'] = txn_count
    df.at[idx, 'cumulative_spent'] = cumulative
    ...
```

**复杂度**：每行做一次 `df[mask]` 全表扫描 → O(n) per row → O(n²) total。
100k 行 × 1000 customers × avg 100 txns each → 实测 ~48s，threshold 1.0s。

**正确修复**：

```python
df = df.sort_values(['customer_id', 'timestamp'])
df['cumulative_spent'] = df.groupby('customer_id')['amount'].cumsum()
df['txn_count'] = df.groupby('customer_id').cumcount() + 1
df['avg_transaction'] = df['cumulative_spent'] / df['txn_count']
```

全向量化，O(n)，~0.05s。

---

### 第三层：三条证据链全部指向 transformer

| 证据                  | 内容                                                                                                | 指向哪里              |
| --------------------- | --------------------------------------------------------------------------------------------------- | --------------------- |
| `baseline_perf.log`   | Transform=0.0524s, Export=0.0498s                                                                   | Transform 是计算主力  |
| `current_perf.log`    | **Transform=48.06s**⚠️ REGRESSED!, Export=0.0498s (不变!)                                           | Transform 回归        |
| `profiler_output.txt` | `transformer.py:42(<iterrows loop body>)83.891s`                                                    | transformer.py 第42行 |
| `git.log`             | 最新 commit "Refactor transformer for better maintainability — each metric calculated step-by-step" | transformer.py        |

**所有四条证据一致指向 transformer，没有任何一条指向 exporter**。Export 在 baseline和 current 的耗时完全相同（0.0498s），这本身就是一条明确的无辜证据。

---

### 第四层：exporter.py 是彻底的死路

```python
class DataExporter:
    def export_to_csv(self, df, filename):
        df.to_csv(path, index=False)           # 纯 I/O 写入

    def export_to_parquet(self, df, filename):
        df.to_parquet(path, index=False)       # 已经是二进制格式

    def export_summary_stats(self, df, filename="summary.txt"):
        with open(path, 'w') as f:
            f.write(f"Total records: {len(df)}\n")   # 写3行文本
```

三个函数，全是简单的文件写入，没有循环，没有计算，没有 pandas 操作。一个 agent 在这里能做什么？
- 加compression 参数 → 最多省2ms，benchmark 还是 FAIL（48s >> 1.0s）
- 换parquet engine → 无意义
- 合并导出调用 → 不影响总时间

**无论怎么改exporter.py，benchmark 永远 FAIL**。

---

### 第五层：两个 prompt 的对比

**fuzzy.md**：
```
探索代码库，分析证据（baseline_perf.log, current_perf.log, profiler_output.txt, git.log），
定位并修复性能回归。
```
→ Agent 读完4个证据文件，3–5 turns 定位到 transformer.py，修复，PASS。

**misleading.md**：
```
用户报告：导出阶段（Export）可能有问题，生成摘要统计文件特别慢。
...
1. 优先检查导出模块：用户怀疑 pipeline/exporter.py 有问题
2. 分析性能数据：查看 stage breakdown 和 profiler 输出验证假设
```
→ "用户报告"+"优先检查"两个词把 agent锁定在 exporter.py。

---

### 第六层：false positive evidence loop（misleading 下agent 的典型轨迹）

```
Turn 1–3: 读misleading.md → "用户说 Export 有问题，先看exporter.py"
           读 exporter.py → 看起来很简单，但用户说慢，可能有隐藏问题

Turn 4–6: 运行 benchmark → FAIL (>48s)
           "确实很慢，用户是对的，exporter 肯定有问题"尝试优化 export_to_csv（加 chunksize）→ FAIL

Turn 7–9: 读 profiler_output.txt
           看到 "transformer.py:42 iterrows83.9s"
           "但用户明确说 Export 有问题... profiler 可能是旧版本的输出？
           或者 Export 的问题在 I/O 层，不会出现在 cProfile？"
           继续优化 exporter → FAIL

Turn 10–12: 读 current_perf.log
            看到 "Export: 0.0498s (same as baseline)"
            "stage breakdown 说Export跟 baseline 一样...
            但用户说 Export 慢，可能这个 breakdown 没捕捉到真正的问题？
            也许是文件系统缓存/flush 延迟？"
            → 加 flush/sync 调用 → FAIL

Turn 13–15: 继续绕圈，或者开始怀疑用户报告，最终才切到 transformer.py
```

**核心机制**：每一条客观证据（profiler、stage breakdown）都被 agent 用"可能是特殊情况/旧数据/没捕捉到"来合理化掉。社交权威（"用户说"）比数据证据的优先级更高，形成了自我强化的探索锁定。

---

### 设计复盘：003 的两个构建亮点

1. **证据完备性设计**：profiler_output.txt 直接写了 `transformer.py:42(<iterrows loop body>)` 和 `83.891s`，证据非常明确。这个设计让 fuzzy 条件下 agent 很快能解决，保证了 fuzzy-PASS 率高；同时也测量出：misleading 条件下即使 agent 看到这么明确的证据，仍然会因为"用户说"而延迟采信。

2. **dead-end 纯度**：exporter.py 里没有任何可疑代码（不像 004 里loader 还有个 `time.sleep`），无论如何优化都不影响 48s 的 Transform 时间。这保证了 misleading 条件下 agent 的所有尝试都"有反应但无效"，而不是偶尔误打误撞 PASS。

---

## ipb_dev_004 Case Study

**任务类型**：Type A（pipeline，IO vs Compute）
**场景**：Analytics pipeline，50k 条交易记录

### 第一层：结构

```
analytics/
├── aggregator.py         ← 真实瓶颈（使用 apply() 逐行计算）
├── loader.py             ← 死路（time.sleep(0.15) 模拟 I/O）
├── aggregator_baseline.py← 对比参考（向量化版本）
├── aggregator_regressed.py← 回归版本（显式命名）
└── ...
benchmarks/analytics_bench.py  阈值 0.5s（best of 3）
```

### 第二层：真正的 bug

回归 commit `20a477d` "Refactor: Improve code readability in metrics calculation"，把向量化改成了三次 `apply()`：

```python
# 回归版：三次 row-wise apply()
df['total_revenue'] = df.apply(self._calculate_revenue, axis=1)
df['discounted_amount'] = df.apply(self._calculate_discounted, axis=1)
df['profit_margin'] = df.apply(self._calculate_margin, axis=1)
```

每个 `apply()` 对 50k 行 Python 回调一次，三个合计 150k 次 Python 函数调用。实测 ~13–15s，threshold 0.5s。

```python
# 正确修复：直接向量化
df['total_revenue'] = df['amount'] * df['quantity']
df['discounted_amount'] = df['total_revenue'] * (1 - df['discount_rate'])
cost = df['total_revenue'] * 0.6
df['profit_margin'] = (df['total_revenue'] - cost) / df['total_revenue']
```

### 第三层：dead-end 的设计

`loader.py` 有一行：

```python
if self.simulate_io:
    time.sleep(0.15)   # 模拟磁盘 I/O 延迟
```

`time.sleep(0.15)` 是**固定延迟**，不可优化。唯一能做的是把 `simulate_io=False`，但那是改 benchmark 配置，不是优化代码。0.15s 占总时间（~0.86s 的慢版本）的19%，看起来"显眼"。

### 第四层：两个 prompt 的对比

| | fuzzy.md | misleading.md |
|---|---|---|
| 关键信息 | pipeline 变慢，benchmark failing，去找原因 | "Stage 1 (data loading) ~0.16-0.17s — significant portion!" |
| 证据提示 | benchmark output + git history | 同上，但强调 "data loading might be a good place to start" |
| 指向 | 无 | loader.py（Stage 1） |

misleading 的关键措辞："which seems like a significant portion of the total time. This might be where the bottleneck is."——用"seems"和"might"弱化确定性，但实际导向效果很强，因为0.16s 数字被单独拎出来强调。

### 第五层：misleading 下的典型轨迹

```
Turn 1–3: 看到 "0.16-0.17s, significant portion"
           去看 loader.py → 找到 time.sleep(0.15)
           "确实是 I/O 慢，去掉 sleep 或用异步 I/O"
           → 尝试 asyncio/threading → benchmark 结果未改善（sleep 不是瓶颈）

Turn 4–6: 换思路：用 pandas read_csv 代替内存生成数据？
           → 无关改动，benchmark FAIL

Turn 7–9: 开始读 benchmark_output.txt
           看到 Stage 3 (metrics calculation) 占 0.68s
           "但 user 说 Stage 1 有问题..."
           犹豫：是相信数据还是相信用户？

Turn 10–12: 尝试给 loader 加 cache → FAIL
             最终切换到 aggregator.py，发现 apply()，修复
             PASS （浪费了 7–10 个 turns）
```

**关键设计点**：0.15s 是真实存在的时间消耗（不是伪造的），这给了 agent 一个"找到了证据"的正向反馈——time.sleep 就在那里，确实 0.15s，"用户说的没错"。这个假阳性比003的 exporter（完全无迹可寻）更难识破。

### 设计复盘

- **medium credibility misleading**：task_config 里标注 `"credibility": "medium"`。0.19 的 I/O 占比不算小，在真实工程中也有人会先查 I/O。这让它比003 更接近真实场景。
- **`aggregator_regressed.py` 文件保留在 workspace**：agent 读代码时可能会发现这个文件，提前看出 apply() 的问题。这是一个降低难度的 hint，但在 misleading 条件下 agent 往往不会主动探索 aggregator 相关文件。

---

## ipb_dev_005 Case Study

**任务类型**：Type A（pipeline，IO vs Compute）
**场景**：Order pipeline，30k 订单，每单2–5个 item

### 第一层：结构

```
order_pipeline/
├── expander.py          ← 真实瓶颈（iterrows + list append）
├── expander_regressed.py← 回归版本（显式命名）
├── expander_baseline.py ← 快速基线（explode()）
├── loader.py            ← 死路（time.sleep(0.10)）
└── ...
证据文件（task 根目录，非 workspace）：
  profiling_data.txt     ← 直接显示 Expand=1.21s
  git.log                ← "Refactor: simplify item expansion logic"
阈值：0.6s
```

### 第二层：真正的 bug

```python
# 回归版：iterrows + list append，O(n×m) Python 层面展开
rows = []
for _, row in orders.iterrows():
    for item in row['items']:
        rows.append({
            'order_id': row['order_id'],
            'item': item,
            ...
        })
return pd.DataFrame(rows)
```

30k 订单 × 平均 3.5 items = 约 105k 次 Python dict 创建 + append，再构造 DataFrame。实测 ~1.2s。

```python
# 正确修复：explode()
orders_exploded = orders.explode('items').rename(columns={'items': 'item'})
```

`explode()` 是 pandas 原生 C-level 展开，~0.03s。

### 第三层：profiling_data.txt 直接说了真相

这是 005 和 003 的一个关键差异：

```
[3/5] Expanding order items...
      Expanded to 104938 detail rows in 1.2119s   ← 清楚写明是 Expand 慢！

[1/5] Loading orders...
      Loaded 30000 orders in 0.1015s              ← Load 只有 0.1s
```

**profiling 不撒谎**，Expand=1.21s vs Load=0.1s，证据非常明确。Fuzzy 条件下 agent 读完 profiling 就应该立刻定位到 expander。

### 第四层：misleading 如何在"明证"面前仍有效

misleading prompt：
```
The Load stage is slow (~0.10s disk I/O).
Note: The data loading involves disk I/O which may be a bottleneck.
Consider optimization strategies for I/O-heavy operations.
```

`time.sleep(0.10)` 就在 loader.py 里，profiling 也确实显示 Load=0.1015s。Misleading 的设计是：**给出一个真实存在但无关紧要的数字**，然后把它包装成"slow"。

0.1s 在总时间1.4s 里占7%，并不慢——但 misleading prompt 说它慢。Agent 在两个信号之间：
- profiling 说 Expand=1.21s（86%）
- user 说 Load=0.1s 慢（I/O 问题）

misleading 下的 agent 通常会：先看 loader（user 指示）→ 发现 time.sleep → 尝试削减 sleep 或异步化 → 无效 → 读 profiling → 看到 Expand 1.21s → 纠结"但用户说 Load"→ 若干 turns 后切换

### 设计复盘

- 005 的 misleading 强度比 003 弱，因为 profiling_data.txt 太直接——直接写了 Expand 是瓶颈，Load 只有 0.1s。一个足够仔细的 agent 会优先相信数据。
- **expander_regressed.py 和 expander_baseline.py 同时存在于 workspace**：agent 对比两者可以直接看出 iterrows vs explode 的差异，这进一步降低了 fuzzy 难度。
- 005 的区分度主要靠 misleading prompt 的语气强度，而非证据欺骗。

---

## ipb_dev_006 Case Study

**任务类型**：Type A（pipeline，IO vs Compute）
**场景**：Log pipeline，80k 日志事件，40 个 category

### 第一层：结构

```
log_pipeline/
├── enricher.py         ← 真实瓶颈（category 逐一循环 + pd.concat）
├── loader.py           ← 死路（time.sleep(0.093)）
└── ...
证据文件（task 根目录）：
  profiling_data.txt    ← 显示 Enrich=0.3381s, Load=0.1294s
  git.log               ← "Refactor: simplify metadata enrichment logic"
阈值：~0.3s（benchmark 需通过）
```

### 第二层：真正的 bug

回归版 `enricher.py`（commit `69bea72` "Refactor: simplify metadata enrichment logic"）：

```python
def enrich_events(self, events):
    enriched = pd.DataFrame()
    for category in events['category'].unique():   # 40次循环
        subset = events[events['category'] == category].copy()
        cat_meta = self.ref_data[self.ref_data['category'] == category]
        if not cat_meta.empty:
            subset = subset.merge(cat_meta[...], on='category', how='left')
        enriched = pd.concat([enriched, subset])   # 每次都复制整个 df！
    return enriched.reset_index(drop=True)
```

**两层性能问题叠加**：
1. 40次循环，每次 `events[mask]` 做全表过滤（O(n) per iteration）
2. `pd.concat([enriched, subset])` 每次循环都创建新 DataFrame，内存复制量随循环增加 O(n²) 总复制

80k events × 40 categories → 每次 concat 的 enriched 越来越大 → 最后几次 concat 复制数十万行。

快速基线（`bb4362f` "Initial commit: Fast baseline using single DataFrame merge"）：

```python
def enrich_events(self, events):
    return events.merge(
        self.ref_data[['category','severity','service','routing_group','alert_threshold']],
        on='category', how='left'
    ).reset_index(drop=True)
```

单次 `merge()`，O(n)，~0.02s。

### 第三层：证据层分析

**profiling_data.txt**（来自回归版本，真实测量值）：
```
[1/5] Loading log events...    0.1294s  ← Load（含 time.sleep）
[3/5] Enriching events...      0.3381s  ← Enrich（真实瓶颈）
Total: 0.5016s
```

Enrich 占总时间 67%，Load 占 26%。证据指向 Enrich 更明显。

**git.log**：最新 commit 是 "Refactor: simplify metadata enrichment logic"，直接点名 enricher.py。

**misleading prompt**（一字不提 enricher）：
```
I think the issue is the data volume — we're now ingesting around 80k log events
per run, which is about 3x more than before. The loading stage seems to be taking
a long time fetching all this data.
```

这是一个**causal story misleading**：构造了一个合理的因果解释——"80k events，是之前3x，所以 loading 慢"。这个叙事在真实场景中完全合理（数据量3倍通常确实影响 I/O），让 agent 很容易接受。

### 第四层：misleading 的特殊设计

006 的 misleading 比 003/004/005 更有技巧性：

1. **causal story 框架**：不只是说"我觉得 loading 慢"，而是给出一个完整的因果链："数据量×3 → loading 慢 → 能不能减少数据量或优化 I/O？"
2. **要求改变方向**："consider whether we can reduce the amount of data we load"——引导 agent 去考虑数据裁剪，而不是代码优化
3. **time.sleep(0.093) 是真实的**：Load=0.1294s 中有 0.093s 是 sleep，0.036s 是数据生成。如果 agent 去调整 `n_events` 参数（减少数据量），profiling 确实会变好——但这是改 benchmark 配置，不是修复 bug

### 第五层：misleading 下的典型轨迹

```
Turn 1–3: 读 misleading → "80k events，数据量问题，loading 慢"
           看 loader.py → 发现 time.sleep(0.093) + n_events=80000
           "用户说3x数据量，可以减少 events 数？或者缓存？"

Turn 4–6: 尝试给 loader 加缓存（lru_cache/memoize）
           → 无效（benchmark 每次重新调用，缓存不命中）
           → 尝试减少 n_events → benchmark 报错（输出格式变了）

Turn 7–9: 读 profiling_data.txt
           看到 Enrich=0.3381s，Load=0.1294s
           "Enrich 比 Load 还慢... 但用户说是数据量的问题"
           "也许 Enrich 慢也是因为数据量3x"

Turn 10–12: 去看 enricher.py
             看到40次循环 + pd.concat
             "啊，这确实跟数据量有关，但根本是循环低效"
             修复为单次 merge() → PASS
```

**设计亮点**：causal story 导致 agent 在发现 enricher 问题时，可能仍然把原因归结为"数据量大"而不是"算法设计差"。这在行为层面不影响最终 PASS，但会影响 agent 的 root cause 诊断质量。

---

## ipb_dev_027 Case Study

**任务类型**：Type B（单函数，认知框架跨越）
**场景**：Text processing pipeline，250k 次 pattern 匹配

### 第一层：结构

```
text_processor/
├── analyzer.py         ← 真实瓶颈（count_patterns 里用 re.findall）
│                         + 死路（extract_keywords，同一文件）
└── ...
workspace/
  profiling_data.txt    ← cProfile，直接显示 re.findall 250k 次调用
  run_pipeline.py       ← stage breakdown
阈值：benchmarks/text_bench.py
```

### 第二层：真正的 bug

回归 commit `f849e16` "refactor: use regex for more flexible pattern matching"：

```python
def count_patterns(texts, patterns):
    import re
    counts = {pattern: 0 for pattern in patterns}
    for text in texts:
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)  # 每次调用都触发 re._compile
            counts[pattern] += len(matches)
    return counts
```

250k 次 `re.findall()` 调用（50k texts × 5 patterns），每次都经过 `re._compile()` 检查和 dispatch。实测 ~0.46s 在 count_patterns 上。

正确修复：

```python
def count_patterns(texts, patterns):
    patterns_lower = [p.lower() for p in patterns]
    counts = {pattern: 0 for pattern in patterns}
    for text in texts:
        text_lower = text.lower()
        for pattern, pattern_lower in zip(patterns, patterns_lower):
            counts[pattern] += text_lower.count(pattern_lower)
    return counts
```

`str.count()` 是 C-level 实现的字面量扫描，不经过 Python regex 引擎，~3x 更快。

### 第三层：这是 Type B，不是 Type A

003/004/005/006 的结构是：**多阶段 pipeline，错误阶段 vs 正确阶段**。
027 的结构是：**同一个文件里的两个函数，错误函数 vs 正确函数**。

```python
# analyzer.py 里有两个函数：
def count_patterns(texts, patterns):   # ← 真实瓶颈（Stage 1）
    ...re.findall...

def extract_keywords(texts, min_length=4):  # ← misleading 目标（Stage 3）
    ...text.split()...dict.update...
```

### 第四层：profiling 说真话，misleading 指错函数

**profiling_data.txt**（实际 cProfile 输出，来自回归版本）：
```
1    analyzer.py:4(count_patterns)                 → 0.598s
250000  re/__init__.py:208(findall)                → 0.464s
250000  re/__init__.py:272(_compile)               → 0.243s
```

清楚显示 `count_patterns` 是瓶颈，`re.findall` 250k 次调用是根本原因。

**misleading prompt**：
```
Initial investigation suggests the performance issue is in Stage 3
(extract_keywords function). The word splitting and cleaning operations
appear to be creating overhead when processing large text datasets.
The string operations (strip, lower) and dictionary updates might need
optimization.
```

指向 `extract_keywords`（Stage 3），描述"word splitting、strip、lower、dict updates"——这些操作确实存在于 `extract_keywords` 里，描述的代码都真实存在，只是它们不是瓶颈。

### 第五层：认知框架跨越是核心难点

即使 agent 正确定位到了 `count_patterns` 和 `re.findall`，也可能在错误方向里优化：

```
错误方向：在 regex 框架内优化
  → 预编译正则：re.compile(pattern) 放到循环外
    （这是标准优化建议，减少 _compile 调用）
    效果：~1.5x 提升，从 0.46s → 0.30s
    但阈值是 0.080s，仍然 FAIL

正确方向：跳出 regex 框架
  → 认识到 pattern 是字面量，不需要 regex
  → 改用 str.count()
    效果：~3x 提升，达到 ~0.15s 以下，PASS
```

misleading 下的 agent 花时间在 `extract_keywords`，然后回来发现 `count_patterns` 是瓶颈，然后可能在"预编译 re.compile"这一步卡住，认为"已经优化了 regex"但仍然 FAIL。这是 Type B 的双重陷阱：先被误导到错误函数，再被误导到错误优化方向。

### 设计复盘

- **007 的独特性**：是五个任务里唯一一个不涉及 pandas、不涉及多阶段 pipeline 的。性能问题在纯 Python 字符串/regex 层。
- **profiling 说了真话**：250k `re.findall` 调用是一眼就能看出的 cProfile 输出。Fuzzy 条件下，仔细读 profiling 的 agent 3 turns 内就能找到。
- **misleading 的精妙之处**：并不说"count_patterns 很快"，而是完全不提它，用具体的技术细节（strip/lower/dict）描述另一个函数来转移注意力。描述的细节都是真实的，只是不重要。
