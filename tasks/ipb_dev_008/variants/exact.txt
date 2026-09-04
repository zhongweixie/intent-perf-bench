The log formatting pipeline has become significantly slower after recent changes.

I've run the benchmark and noticed the performance has degraded:
- Current performance: ~8 seconds for 30,000 log entries
- Expected performance: should complete in well under 1 second

I've included profiler output (profiler_output.txt) and recent git history (git.log) in the workspace for your reference.

Please investigate what's causing this slowdown and fix it. The benchmark should pass (< 0.30s threshold).
