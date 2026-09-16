# Environment

## GPU

NVIDIA H800 (sm_90, 80 GB HBM3)

## Build

```bash
make          # nvcc -O3 -std=c++17 -arch=sm_90 -o huffman_decode main.cu solve.cu
make clean
```

## Run modes

```bash
./huffman_decode --verify              # 公开正确性校验 (小 workload)
./huffman_decode --benchmark           # 无评分计时 (公开 seed)
./huffman_decode --benchmark-verify    # 评分 run（需要环境变量 HUFFMAN_DECODE_SEED）
```

## Benchmark

```bash
bash benchmarks/bench.sh   # 编译 + 运行 + 判断是否通过阈值
```

通过条件：`./huffman_decode --benchmark` 报告的 `time_ms` ≤ **11.2 ms**
（即相对当前回归版本的 5× 加速）

## Files

| File | Description |
|------|-------------|
| `solve.h`   | 接口头文件（**禁止修改**） |
| `main.cu`   | 测试 harness（**禁止修改**） |
| `solve.cu`  | ← **你的工作区**，当前为回归版本 |
| `Makefile`  | 构建规则 |
