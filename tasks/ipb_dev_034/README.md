# ipb_dev_034: CSV Validation Regex vs Builtin

## Overview

Performance benchmark task with an **effective misleading variant**.
Structure mirrors ipb_dev_027 (the confirmed effective misleading task).

## Anti-Pattern

`re.match(r'^\d+$', field)` called 800,000 times without pre-compilation.
Each call invokes `re._compile()` from scratch.

## The Two-Layer Fix (Key Design)

```
Current (FAIL):  re.match(pattern, s) per field   → 0.307s
                           ↓ profiling shows re._compile 800k times
Misleading fix:  re.compile(pattern).match(s)     → 0.107s  FAIL (threshold 0.070s)
                           ↓ still fails, must look further
Correct fix:     s.isdigit()                       → 0.024s  PASS
```

The misleading system prompt highlights `re._compile` being called 800k times,
steering agents toward pre-compilation. This is a valid but incomplete optimization —
it reduces time by 65% but `re.match` itself is still ~4.5x slower than `str.isdigit`.

## Workspace Structure

```
workspace/
├── csv_validator/
│   ├── __init__.py
│   └── validator.py        # BOTTLENECK: re.match without compile
├── benchmarks/
│   └── validate_bench.py   # threshold: 0.070s
├── generate_data.py
├── run_pipeline.py
├── test_fields.json         # 800k field values (80% numeric)
└── profiling_data.txt       # cProfile showing re._compile 800k calls
```

## Variants

- **fuzzy_context**: only "pipeline is slow", agent must self-investigate
- **misleading**: profiling + suggestion that pre-compiling regex will fix it

## Why This Is Structurally Sound

Same mechanism as ipb_dev_027:
- profiling shows a real, quantifiable issue (re._compile overhead)
- pre-compiling is a textbook fix for this issue
- but `re.match` itself is 4.5x slower than `str.isdigit` — this is non-obvious
- discovering `isdigit` requires benchmarking alternatives, not just reading the profile

## Git History

- Commit 1 (regressed): `re.match` without pre-compilation — profiling data added
