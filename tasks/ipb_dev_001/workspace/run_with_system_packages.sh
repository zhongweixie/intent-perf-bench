#!/usr/bin/env bash
# Run a command using the workspace Python + repo pandas + system site-packages for optional deps
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the system Python 3.10 site-packages if available
SYSTEM_SITE_PACKAGES=""
for python_path in /usr/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages /home/hansirui_3rd/.local/share/uv/python/cpython-3.10-linux-x86_64-gnu/lib/python3.10/site-packages; do
    if [ -d "$python_path" ]; then
        SYSTEM_SITE_PACKAGES="$python_path:$SYSTEM_SITE_PACKAGES"
    fi
done

PYTHONPATH="$SCRIPT_DIR/repo:$SYSTEM_SITE_PACKAGES" \
  /aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/ipb_py310_env/bin/python "$@"
