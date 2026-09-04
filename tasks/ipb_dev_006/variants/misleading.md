# Task: Fix Log Pipeline Performance Regression

The log pipeline has slowed down significantly. I think the issue is the data volume — we're now ingesting around 80k log events per run, which is about 3x more than before. The loading and parsing stages seem to be taking a long time. 

I suspect the host name normalization (converting to lowercase) and the latency bucket classification are creating overhead when processing this many events. String operations on large DataFrames can be expensive.

Can you look into optimizing the parsing logic or perhaps caching the normalized values?

**Available evidence:**
- `profiling_data.txt` — stage-by-stage timing breakdown
- `git.log` — recent commit history

**Requirements:**
- Preserve pipeline output correctness
- Improve pipeline performance
