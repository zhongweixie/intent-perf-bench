# LLM Prefix KV-Cache Manager

A high-performance prefix-aware KV-cache manager for LLM inference, inspired by
the block management layer in [vLLM](https://github.com/vllm-project/vllm).

## Overview

The cache manager shares KV-cache blocks across requests that share a common
token prefix, reducing GPU memory usage and improving throughput.

## Running

```bash
python run_workload.py          # end-to-end simulation
python benchmarks/cache_bench.py  # correctness + performance benchmark
```

## Architecture

| Module | Role |
|---|---|
| `evictor.py` | LRU eviction policy (tracks free block pool) |
| `hasher.py` | Content-addressable hash for token blocks |
| `block_allocator.py` | Physical block pool with eviction integration |
| `prefix_cache.py` | Prefix-sharing logic across concurrent requests |
