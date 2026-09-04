# seed/ 目录说明

此目录存放从公开 benchmark 筛选出的候选任务元数据（JSONL 格式），以及克隆的参考仓库。

## 目录结构

```
seed/
├── README.md                        # 本文件
├── .gitignore                       # 排除大型仓库和数据集缓存
├── swefficiency_candidates.jsonl    # 01_select_candidates.py 输出，已筛选的候选
├── gso_candidates.jsonl             # GSO 对应候选（可选）
└── reference_repos/                 # SETUP.sh 克隆的参考仓库（不提交）
    ├── swefficiency/                # SWE-fficiency harness
    ├── gso/                         # GSO benchmark
    └── SWE-bench/                   # SWE-bench Docker harness 参考
```

## 数据分类

| 来源 | Provenance 标签 | 是否进主榜 | 用途 |
|---|---|---|---|
| SWE-fficiency 历史任务 | `legacy` | 否 | 开发 evaluator、验证设计 |
| GSO 历史任务 | `legacy` | 否 | 多语言开发集 |
| 注入式回归（人工构造）| `injected` | 是 | 可扩展主评测 |
| 最新未公开真实任务 | `fresh` | 是 | 高质量验证 |
| 企业/维护者私有任务 | `private` | 是（最可信）| 高置信主评测 |

**关键原则**：论文主结论必须来自 `injected`/`fresh`/`private`，`legacy` 只用于说明 benchmark 设计可行性。

## 生成候选列表

```bash
# 从 SWE-fficiency HuggingFace 数据集筛选（需要网络）
python scripts/01_select_candidates.py \
    --output seed/swefficiency_candidates.jsonl \
    --min-speedup 1.20 \
    --repos pandas-dev/pandas numpy/numpy scipy/scipy scikit-learn/scikit-learn
```
