# Exact Variant

`blur_image()` 的当前实现是正确的，但 17x17 卷积在每个像素、每个 pass 上重复执行完整二维 kernel，并在内层循环做边界 clamp。请优化 `solve.c`，保持函数签名、5 次 pass、clamp 边界规则及像素误差容限不变。使用 `../benchmarks/bench.sh` 验证性能。
