# Workspace Environment

## Python interpreter

Use this Python for all scripts in this workspace:

    /aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/ipb_py310_env/bin/python

It is Python 3.10.20 with numpy 1.26.4 installed.

## Using the repo pandas

The `repo/` directory contains the pandas source with pre-built extensions.
Set PYTHONPATH so this pandas is imported instead of any system pandas:

    PYTHONPATH=/aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/tasks/ipb_dev_001/workspace/repo \
      /aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/ipb_py310_env/bin/python <script>

Shorthand — a helper script is provided:

    ./run.sh scripts/daily_report.py
    ./run.sh benchmarks/datetime_compare.py

## Verify current pandas version

    ./run.sh -c "import pandas; print(pandas.__version__, pandas.__file__)"
    # Expected: 1.2.0.dev0+... .../workspace/repo/pandas/__init__.py
