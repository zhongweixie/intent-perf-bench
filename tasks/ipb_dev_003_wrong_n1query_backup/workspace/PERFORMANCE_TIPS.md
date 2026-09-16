# pandas 性能优化 - 快速参考

## 场景：处理 100k+ 行数据

### ❌ 反面教材

```python
import pandas as pd

# 问题 1：不必要的 DataFrame 转换
df = pd.DataFrame(large_list_of_dicts)

# 问题 2：使用 iterrows() 迭代
for idx, row in df.iterrows():
    process(row['column_a'], row['column_b'])
    
# 问题 3：逐行数据库查询 (N+1)
for idx, row in df.iterrows():
    user = query_user_by_id(row['user_id'])  # 100k 个查询！
    
# 问题 4：重复查询相同数据
for item in items:
    balance = fetch_account_balance(item['account_id'])  # 无缓存
```

**性能**：1.9 秒（100k 行）❌

---

### ✓ 正确做法

```python
# 方案 1：直接迭代原始列表（最快）
results = []
for item in items:
    result = process(item['field_a'], item['field_b'])
    results.append(result)

# 方案 2：使用字典理解
results = [process(item['field_a'], item['field_b']) for item in items]

# 方案 3：避免 N+1 查询 - 批量加载
user_ids = set(item['user_id'] for item in items)
users = batch_query_users(user_ids)  # 一次查询
users_map = {u['id']: u for u in users}

for item in items:
    user = users_map[item['user_id']]  # O(1) 查找

# 方案 4：使用缓存
from functools import lru_cache

@lru_cache(maxsize=1024)
def get_account(account_id):
    return fetch_account_balance(account_id)

for item in items:
    balance = get_account(item['account_id'])  # 自动去重
```

**性能**：0.034 秒（100k 行）✓ **56.5x 加速**

---

## 速度对比表

| 方法 | 时间 (100k 行) | 相对速度 | 场景 |
|------|----------------|---------|------|
| 直接列表迭代 | 0.034s | 1x ✓ | 推荐 |
| 列表理解 | 0.035s | 1.0x ✓ | 推荐 |
| itertuples() | 0.45s | 13x | 快但不如列表 |
| apply() | 0.8s | 24x | 避免 |
| iterrows() | 1.92s | 56x | **完全避免** |

---

## 常见模式修复

### 模式 1：简单转换

```python
# ❌ 慢
df = pd.DataFrame(data)
results = []
for idx, row in df.iterrows():
    results.append(row['value'] * 2)

# ✓ 快
results = [item['value'] * 2 for item in data]
```

### 模式 2：条件过滤

```python
# ❌ 慢
df = pd.DataFrame(data)
results = []
for idx, row in df.iterrows():
    if row['status'] == 'active':
        results.append(row)

# ✓ 快
results = [item for item in data if item['status'] == 'active']
```

### 模式 3：关联查询

```python
# ❌ 慢（N+1 问题）
df = pd.DataFrame(transactions)
results = []
for idx, row in df.iterrows():
    user = query_user(row['user_id'])  # 100k 次查询！
    results.append({**row, 'user': user})

# ✓ 快（批量加载）
user_ids = set(t['user_id'] for t in transactions)
users = {u['id']: u for u in batch_query_users(user_ids)}

results = []
for txn in transactions:
    results.append({**txn, 'user': users[txn['user_id']]})
```

### 模式 4：需要 DataFrame 时的优化

```python
# 如果你必须使用 pandas（例如需要做复杂的矢量化操作）

# ❌ 避免
for idx, row in df.iterrows():
    process(row)

# ✓ 使用矢量化或列操作
df['new_col'] = df['col_a'] * df['col_b']  # 矢量化

# ✓ 或者用 apply（仍不理想但比 iterrows() 好）
df['result'] = df.apply(lambda row: process_func(row), axis=1)
```

---

## 性能检查清单

在提交前审查你的代码：

- [ ] 是否使用了 `df.iterrows()`？→ 改为直接列表迭代
- [ ] 是否有 N+1 查询模式？→ 改为批量加载
- [ ] 是否重复查询相同数据？→ 添加缓存（@lru_cache 或字典）
- [ ] 是否不必要地转换为 DataFrame？→ 在原始结构上操作
- [ ] 是否有同步 I/O 阻塞循环？→ 考虑异步或批处理
- [ ] 是否测试过 100k+ 数据规模？→ 添加基准测试

---

## 基准测试模板

```python
import time

def benchmark(func, data, name, threshold=None):
    times = []
    for _ in range(3):
        start = time.perf_counter()
        result = func(data)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    median = sorted(times)[1]
    print(f"{name}: {median:.4f}s", end="")
    
    if threshold:
        status = "✓ PASS" if median <= threshold else "✗ FAIL"
        print(f" {status}")
    else:
        print()
    
    return median

# 使用
data = [{'id': i, 'value': i*2} for i in range(100000)]

benchmark(slow_version, data, "Slow (iterrows())", threshold=0.8)
benchmark(fast_version, data, "Fast (direct iteration)", threshold=0.8)
```

---

## 关键要点

1. **列表迭代 > DataFrame 迭代**
   - 如果数据开始是列表，就在列表上操作

2. **批量操作 > 逐个操作**
   - 一次加载 1000 用户比加载 1000 次好

3. **缓存 > 重复查询**
   - @lru_cache 或简单的字典都很有效

4. **矢量化 > 任何循环**
   - 如果可能用 NumPy/pandas 矢量化，这是最快的

5. **测试 > 猜测**
   - 添加基准测试到 CI/CD
   - 性能回归会被立即捕获

---

## 相关资源

- [pandas 性能优化指南](https://pandas.pydata.org/docs/user_guide/enhancing.html)
- [Why iterrows() is slow](https://stackoverflow.com/questions/16476924/how-to-iterate-over-rows-in-a-dataframe)
- [N+1 查询问题](https://en.wikipedia.org/wiki/N%2B1_problem)

