# IPB Task Structure

## Selected Tasks for Initial Release

1. **ipb_cuda_001** - Huffman Decode CUDA Performance Regression
   - Regression: 21.8x slower (124.3ms vs 5.7ms)
   - Difficulty: Medium
   - Issue: Inefficient memory access patterns

2. **ipb_cuda_002** - ICP Correspondence CUDA Performance Regression
   - Regression: 42.5x slower (340ms vs 8ms)
   - Difficulty: Medium
   - Issue: Suboptimal kernel configuration

3. **ipb_cuda_003** - NTT Butterfly CUDA Performance Regression
   - Regression: 6.4x slower (320ms vs 50ms)
   - Difficulty: Medium
   - Issue: Bank conflicts and synchronization

4. **ipb_cuda_004** - BLS12-381 G1 MSM CUDA Performance Regression
   - Regression: 10.6x slower (624ms vs 59ms)
   - Difficulty: Hard
   - Issue: Complex cryptographic computation optimization

5. **ipb_cuda_005** - L2 Norm Hierarchical Reduction
   - Regression: 5.6x slower (4.5ms vs 0.8ms)
   - Difficulty: Medium
   - Issue: Excessive synchronization

## Required Components per Task

### 1. Task Metadata (`task.toml`)
```toml
[task]
id = "ipb_cuda_xxx"
title = "Task Title"
category = "cuda"
difficulty = "easy|medium|hard"

[timing]
regressed_ms = X.X
optimal_ms = Y.Y
threshold_ms = Z.Z

[evaluation]
benchmark_script = "benchmarks/bench.sh"
regression_commit = "HEAD"
reference_commit = "HASH"

[variants]
fuzzy = "variants/fuzzy.md"
misleading = "variants/misleading.md"
```

### 2. Workspace Structure
```
workspace/
├── .git/               # Git repository with regression and optimal commits
├── Makefile           # Build configuration
├── main.cu            # Test harness
├── solve.cu           # Current implementation (regression version)
├── solve_baseline.cu  # Baseline implementation
├── solve_regression.cu # Explicit regression version
└── include/           # Header files
```

### 3. Benchmark Script (`benchmarks/bench.sh`)
```bash
#!/bin/bash
# Runs performance benchmark and outputs timing in ms
# Used by evaluation system to measure performance
```

### 4. Git History
- **Baseline commit**: Efficient implementation with good performance
- **Regression commit**: Introduces performance degradation
- Commits should have clear messages explaining the changes

### 5. Variant Specifications
- `variants/fuzzy.md`: Fuzzy description of the issue (less specific)
- `variants/misleading.md`: Misleading description that points in wrong direction

## Task Validation Checklist

For each task, verify:
- [ ] task.toml exists with complete metadata
- [ ] workspace/ directory exists
- [ ] workspace/.git exists with proper history
- [ ] Makefile compiles successfully
- [ ] solve.cu (regression) and solve_baseline.cu exist
- [ ] main.cu runs verification tests
- [ ] benchmarks/bench.sh exists and runs
- [ ] Performance regression is measurable (>2x slowdown)
- [ ] Optimal version passes all correctness tests
- [ ] Regression version passes correctness but is slower

## Next Steps

1. Run completeness check on all 5 tasks
2. Fill in missing components
3. Validate each task individually
4. Create evaluation framework
5. Test end-to-end workflow
