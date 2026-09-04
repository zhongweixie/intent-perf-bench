# Fuzzy Variant

**Information provided:**
- Vague complaint: "pipeline has become slower than before"
- No profiling data, no specific hints
- Benchmark script available

**User description:**
"The time series anomaly detection pipeline has become slower than before. It used to finish in under a second, but now takes much longer."

**Expected behavior:**
Agent must profile or time different pipeline stages independently to discover that feature_builder is the bottleneck, then investigate and optimize.
