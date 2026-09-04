# Target Known Variant

**Information provided:**
- Complaint: "pipeline has become much slower"
- **Direct hint**: "I suspect there's a performance issue in timeseries/feature_builder.py"
- Request: "can you investigate and optimize it?"

**User description:**
"The time series anomaly detection pipeline has become much slower. I suspect there's a performance issue in timeseries/feature_builder.py — can you investigate and optimize it?"

**Expected behavior:**
Agent is pointed directly to the correct module but must still:
1. Confirm the bottleneck with evidence (profiling/timing)
2. Identify the specific anti-pattern (iterrows + concat-in-loop)
3. Replace it with the correct vectorized approach

This tests the agent's ability to execute when given the right direction.
