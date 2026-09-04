"""
IPB Agent Runner — 用 Anthropic API 对单个变体运行一次 agent 评测。

用法：
    source /home/hansirui_3rd/zxiebk/scripts/claw/claw-adapters/train/rl/load_secrets.sh
    python scripts/run_agent.py --task-id ipb_dev_001 --variant fuzzy [--model claude-opus-5]

输出：
    results/ipb_dev_001_fuzzy_run1.json   — 完整轨迹 + 最终 diff + 评测指标
"""

import argparse
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import ipb_measure                                        # noqa: E402
import ipb_workspace                                      # noqa: E402
from ipb_exec import EXEC as _NATIVE_EXEC                 # noqa: E402
from ipb_score import NotCalibrated, score as _score_run  # noqa: E402

# CUDA toolkit 位置：登录节点和计算节点默认 PATH 里都没有 nvcc。
_CUDA_BIN = "/home/hansirui_3rd/cuda-12/bin"


def _gpu_alloc() -> str:
    """Job id of a reserved GPU allocation, or "" if none.

    Deliberately env-only: probing with squeue takes tens of seconds on this
    cluster, and a slow probe silently degrades into a cold start.
    """
    return os.environ.get("IPB_GPU_JOBID", "").strip()


def _gpu_wrap(cmd: str) -> str:
    """Run an agent command inside the reserved allocation.

    Without this the agent's bash tool lives on a host with no usable GPU, so
    it can build but never measure -- turning a "profile, then optimise" task
    into blind optimisation and silently changing what the CUDA arm measures.
    """
    jid = _gpu_alloc()
    if not jid:
        return cmd
    return (f"srun --jobid={jid} --overlap --gres=gpu:1 "
            f"bash -c {shlex.quote(cmd)}")


# Load .env file if it exists (override environment variables)
_ENV_FILE = ROOT / ".env"
if _ENV_FILE.exists():
    with open(_ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip()

# ── Agent 系统提示（按任务类型选择，不暴露"这是 benchmark"）──
#
# ipb_dev_001: pandas 内部源码修改任务，有 repo/ 子目录
# ipb_dev_002+: 用户级脚本优化任务，无 repo/ 子目录
#
_SYSTEM_PROMPT_REPO = """You are working in the provided repository and workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, configuration and tests. You may run profiling,
tests and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter (use this for ALL python commands):
  /aifs4su/hansirui_3rd/zxiebk/scripts/codeben/intent-perf-bench/ipb_py310_env/bin/python

The workspace/repo/ directory contains the pandas source with pre-built extensions.
Use the run.sh helper to run scripts with the correct PYTHONPATH automatically:
  cd {workdir} && ./run.sh scripts/daily_report.py
  cd {workdir} && ./run.sh -c "import pandas; print(pandas.__version__)"

To modify pandas source and see the effect, edit files under repo/pandas/ then
run scripts again — no recompilation needed for .py files.

To check your changes:
  cd {workdir} && git -C repo diff

== REQUIREMENTS ==

- Preserve observable correctness and public behavior.
- Do not modify tests, benchmark workloads, evaluation scripts or input data.
- Validate your final changes using the repository's available tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
"""

_SYSTEM_PROMPT_SCRIPT = """You are working in the provided workspace.

Address the user's request by investigating the available code, scripts,
documentation, benchmarks, configuration and tests. You may run profiling,
tests and benchmarks as needed.

== ENVIRONMENT ==

Python interpreter:
  python3   (system python with pandas, numpy installed)

Run scripts directly:
  cd {workdir} && python3 scripts/daily_report.py
  cd {workdir} && python3 benchmarks/report_bench.py

== REQUIREMENTS ==

- Preserve observable correctness (output values must not change).
- Do not modify test files, benchmark scripts or input data.
- Validate your final changes using the available benchmark tooling.
- At completion, briefly summarize:
  1. the measured bottleneck or performance problem;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. correctness and performance validation performed.

Working directory: {workdir}
"""


# CUDA 任务的环境说明。变体 prompt（exact/fuzzy/misleading）只描述"要优化什么"，
# 不描述"怎么编译和跑"；这段对三个变体完全相同，因此不影响变体间的对照。
# 关键点：本机 GPU 不能直接访问（直接运行二进制会报 "system not yet initialized"），
# 必须通过 srun 提交。
_GPU_LAUNCH_DIRECT = """Every bash command you run already executes inside a GPU allocation, so GPU
binaries run directly:
  ./<binary>
  ./<binary> --benchmark"""

# Fallback wording for when no allocation is reserved. Agents do not reliably
# obey it: given this text, opus-5 ran ./transpose_test directly three times,
# hit "system not yet initialized" each time, concluded the fabric manager was
# down and shipped a kernel it had never executed -- which is why the harness
# now wraps the command instead of asking.
_GPU_LAUNCH_SRUN = """GPU binaries CANNOT be run directly on this host -- doing so fails with
"system not yet initialized". Always launch them through srun:
  srun -p debug --qos=llm_debug --gres=gpu:1 -t 5 ./<binary>
  srun -p debug --qos=llm_debug --gres=gpu:1 -t 5 ./<binary> --benchmark

This applies to every command below that shows a binary being invoked
directly: prefix it with the srun line above."""

_CUDA_ENV_PREAMBLE = """== ENVIRONMENT ==

Working directory: {workdir}

GPU: NVIDIA H800 (sm_90, Hopper architecture)
CUDA Toolkit: 12.x (nvcc already on PATH)

Build locally:
  make clean && make

{gpu_launch}

You are expected to actually build and measure your change, not just reason
about it.

== TASK ==

"""

_CPU_ENV_PREAMBLE = """== ENVIRONMENT ==

Working directory: {workdir}

CPU: Intel Xeon Platinum 8480C (Sapphire Rapids, x86-64),
     56 cores / 112 threads per socket
Compiler: gcc/g++. The workspace Makefile builds with -O2 -march=native, so
          the host CPU's full instruction set is available. Run lscpu if
          you need the exact feature list.

Build locally:
  make clean && make

Run directly:
  ./<binary>

You are expected to actually build and measure your change, not just reason
about it.

== TASK ==

"""


def _get_system_prompt(task_id: str, variant: str = "exact") -> str:
    """Return the appropriate system prompt for the given task and variant."""
    if task_id == "ipb_dev_001":
        return _SYSTEM_PROMPT_REPO

    from pathlib import Path
    task_dir = Path(__file__).parent.parent / "tasks" / task_id

    # CUDA tasks: use variant-specific .md files
    if task_id.startswith("ipb_cuda_"):
        prompt_file = task_dir / "variants" / f"{variant}.md"
        if prompt_file.exists():
            launch = _GPU_LAUNCH_DIRECT if _gpu_alloc() else _GPU_LAUNCH_SRUN
            return (_CUDA_ENV_PREAMBLE.replace("{gpu_launch}", launch)
                    + prompt_file.read_text())
        # Fallback to generic CUDA prompt if variant file missing
        return """You are working in a CUDA workspace.

Address the user's request by investigating the code, profiling, and benchmarks.

== ENVIRONMENT ==

CUDA compiler: nvcc (available in PATH or via module load cuda/12.2)
GPU: H800 (sm_90)

Build and run:
  cd {workdir} && make clean && make
  srun -p debug --qos=llm_debug --gres=gpu:1 -t 10 ./<binary> --verify
  srun -p debug --qos=llm_debug --gres=gpu:1 -t 10 ./<binary> --benchmark

== REQUIREMENTS ==

- Preserve correctness (all tests must pass).
- Do not modify test harness or interface files.
- Validate performance and correctness before completing.
- At completion, summarize:
  1. the measured bottleneck;
  2. the evidence supporting your diagnosis;
  3. the implementation change;
  4. validation performed.

Working directory: {workdir}
"""

    # Native CPU tasks use the same task-specific variant files as CUDA tasks.
    if task_id.startswith("ipb_cpu_"):
        prompt_file = task_dir / "variants" / f"{variant}.md"
        if prompt_file.exists():
            return _CPU_ENV_PREAMBLE + prompt_file.read_text()
        return """You are working in a native CPU performance workspace.

Investigate the implementation, preserve the public interface and observable
correctness, and use the available Makefile and benchmark script to validate
both correctness and performance.

Working directory: {workdir}
"""

    # ipb_dev_015+: variants/ 目录下有 system_prompt_{variant}.md
    # 新任务用 exact_evidence / fuzzy_context 命名
    # 旧任务用 exact / fuzzy / misleading 命名
    for candidate in [variant, f"system_prompt_{variant}"]:
        prompt_file = task_dir / "variants" / f"system_prompt_{variant}.md"
        if prompt_file.exists():
            return prompt_file.read_text()

    # Try system_prompts.py (ipb_dev_003 style)
    sys.path.insert(0, str(task_dir))
    try:
        from system_prompts import PROMPTS
        return PROMPTS.get(variant, PROMPTS.get("exact", _SYSTEM_PROMPT_SCRIPT))
    except ImportError:
        pass
    finally:
        if str(task_dir) in sys.path:
            sys.path.remove(str(task_dir))

    # Legacy: system_prompt_{variant}.md at task root
    prompt_file = task_dir / f"system_prompt_{variant}.md"
    if prompt_file.exists():
        return prompt_file.read_text()

    return _SYSTEM_PROMPT_SCRIPT


# ── 工具定义 ──
TOOLS = [
    {
        "name": "bash",
        "description": "Run a shell command. CWD is the workspace root.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a file's contents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "start_line": {"type": "integer"},
                "end_line":   {"type": "integer"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write or overwrite a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_dir",
        "description": "List directory contents.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        }
    }
]


def _load_dotenv():
    """从项目根目录 .env 加载凭证（优先级最高）。"""
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def _load_sops_secrets():
    """从 sops 加载 secrets 到内存（仅限当前进程，不写文件）。"""
    import subprocess, pathlib
    sops_bin  = pathlib.Path.home() / ".local/bin/sops"
    sops_file = pathlib.Path.home() / ".config/claw/secrets.env.sops"
    age_key   = pathlib.Path.home() / ".config/sops/age/keys.txt"
    if not sops_file.exists() or not sops_bin.exists():
        return
    try:
        env = dict(os.environ)
        env["SOPS_AGE_KEY_FILE"] = str(age_key)
        r = subprocess.run(
            [str(sops_bin), "decrypt",
             "--input-type", "yaml", "--output-type", "dotenv",
             str(sops_file)],
            capture_output=True, text=True, env=env, timeout=15
        )
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass   # 已有环境变量则继续



_BUDGET_WARNING = (
    "SYSTEM NOTICE: your turn budget is almost exhausted "
    "({left} turn(s) left of {total}). Stop exploring now. Leave the "
    "workspace in the best working state you have achieved: it must compile, "
    "pass correctness checks, and be your fastest correct version. If you are "
    "mid-edit or have reverted to a slower version, restore your best version "
    "immediately."
)

# Metric lines emitted by the native harnesses, e.g.
#   "result=ok N=200000 ... time_ms=65.448608"   (CUDA)
#   "n_ops=3000 cycles=1418 result=ok"           (CPU)
_METRIC_RE = re.compile(r"\b(time_ms|cycles)\s*=\s*([0-9]+(?:\.[0-9]+)?)")


def _scan_best_measurement(trajectory):
    """Best (lowest) correct measurement observed during the run.

    Diagnostic only, never feeds the score. Distinguishes a run that never
    reached the target from one that reached it and then lost it.
    """
    best = None
    for entry in trajectory:
        if entry.get("type") != "tool_result":
            continue
        text = str(entry.get("result", ""))
        # Only trust measurements the harness itself labelled correct.
        if ("result=ok" not in text
                and "__VERIFIER_CORRECTNESS__=PASS" not in text):
            continue
        for unit, raw in _METRIC_RE.findall(text):
            value = float(raw)
            if best is None or value < best["value"]:
                best = {"value": value, "unit": unit, "turn": entry.get("turn")}
    return best


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--task-id",  default="ipb_dev_001")
    p.add_argument("--variant",  required=True,
                   choices=["exact","target_known","fuzzy","misleading",
                            "exact_evidence","fuzzy_context"])
    p.add_argument("--model",    default="claude-opus-5")
    p.add_argument("--max-turns", type=int, default=30)
    p.add_argument("--budget-warning-turns", type=int, default=5,
                   help="warn the agent its turn budget is running out this "
                        "many turns before max-turns, so it can leave the "
                        "workspace in its best state; 0 disables")
    p.add_argument("--run-id",   default=None)
    p.add_argument("--bench-runs", type=int, default=3,
                   help="timed runs for native tasks; median is scored")
    p.add_argument("--keep-workspace", action="store_true",
                   help="keep the isolated workspace clone for debugging")
    p.add_argument("--provider", default="anthropic",
                   choices=["anthropic", "openai"],
                   help="API provider: anthropic (default) or openai (for GPT models)")
    return p.parse_args()


def get_client():
    _load_dotenv()        # 优先加载 .env
    _load_sops_secrets()  # 再加载 sops（如果有）
    import anthropic
    api_key  = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    assert api_key, (
        "未找到 Anthropic 凭证，请先执行：\n"
        "  source /home/hansirui_3rd/zxiebk/scripts/claw/claw-adapters/train/rl/load_secrets.sh"
    )
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return anthropic.Anthropic(**kwargs)


def get_openai_client():
    _load_dotenv()
    _load_sops_secrets()
    from openai import OpenAI
    api_key  = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    assert api_key, "未找到 OPENAI_API_KEY，请检查 .env 或环境变量"
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


# read_file result cap. The previous 8000 silently truncated files this size
# (ipb_cpu_004 solve.c is 9119 bytes), so the agent could edit a file it had
# only partly seen without ever being told.
_READ_LIMIT = 60000

# Notices that can ride along on a tool result and end up in a source file.
# Two sources: the serving layer in front of the model decorates tool results
# with instructions meant for itself (nothing in this repo emits that text),
# and read_file adds its own truncation marker. Either way write_file is the
# agent's only editing tool and overwrites whole files, so a read_file result
# handed straight back writes the notice into the code.
#
# That is how ipb_cuda_001/misleading (g5c, opus-5) delivered a solve.cu whose
# first two lines were "This file was already read in this conversation..." and
# "Previous Read result:": 15 nvcc errors, build failed, and the run was
# recorded as an agent failure it had not caused. Same failure mode as the
# line-number prefixes (#108), but this text originates outside the harness, so
# the write side is the only place it can be stopped.
_INJECTED_NOTICE_RE = re.compile(
    r"^(?:"
    r"This file was already read in this conversation\..*"
    r"|Previous Read result:[ \t]*"
    r"|\[truncated: \d+ of \d+ chars\..*"
    r")\n?",
    re.MULTILINE,
)

# Recorded into the result JSON. Stripping silently would trade an obvious
# build failure for an invisible edit, and a reviewer has to be able to see
# that the delivered workspace was touched by the harness.
_INJECTION_STRIPS: list[dict] = []


def _strip_injected_notices(path: str, content: str) -> tuple[str, list[str]]:
    """Drop tool-result notices from content the agent is about to write.

    The patterns are English prose anchored at column 0, which no line of C,
    CUDA or Python source is. A comment or docstring could in principle open
    with one and dropping it would be wrong, but the alternative is writing
    source that cannot compile, so the strip wins.
    """
    found = _INJECTED_NOTICE_RE.findall(content)
    if not found:
        return content, []
    cleaned = _INJECTED_NOTICE_RE.sub("", content)
    stripped = [s.strip() for s in found]
    _INJECTION_STRIPS.append({"path": path, "lines": stripped})
    return cleaned, stripped


def execute_tool(name: str, inp: dict, workdir: pathlib.Path) -> str:
    """执行工具调用，返回结果字符串。"""
    try:
        if name == "bash":
            cmd     = inp["command"]
            timeout = inp.get("timeout", 60)
            # nvcc 不在本进程的 PATH 里。不注入的话 CUDA 任务的 agent 无法编译，
            # 也就无法实测自己的改动，只能盲写 kernel。
            if "ipb_cuda_" in str(workdir):
                cmd = f"export PATH={_CUDA_BIN}:$PATH\n{cmd}"
                cmd = _gpu_wrap(cmd)
            r = subprocess.run(
                cmd, shell=True, cwd=str(workdir),
                capture_output=True, text=True, timeout=timeout
            )
            out = r.stdout[-4000:] if len(r.stdout) > 4000 else r.stdout
            err = r.stderr[-1000:] if len(r.stderr) > 1000 else r.stderr
            result = out
            if err.strip():
                result += f"\n[stderr]\n{err}"
            if r.returncode != 0:
                result += f"\n[exit code {r.returncode}]"
            return result or "(no output)"

        elif name == "read_file":
            path = workdir / inp["path"]
            if not path.exists():
                return f"File not found: {inp['path']}"
            lines = path.read_text(errors="replace").splitlines()
            s = inp.get("start_line", 1) - 1
            e = inp.get("end_line",   len(lines))
            # Returned verbatim, without line-number prefixes. write_file
            # (whole-file overwrite) is the agent's only editing tool, so what
            # this returns can come straight back as file content; prefixing
            # each line with its number and a tab produced source files whose
            # every line was "30<tab>255<tab>code" and could not compile.
            snippet = "\n".join(lines[s:e])
            if len(snippet) > _READ_LIMIT:
                shown = snippet[:_READ_LIMIT]
                return (shown + f"\n\n[truncated: {len(shown)} of "
                        f"{len(snippet)} chars. Re-read with start_line/"
                        f"end_line to see the rest.]")
            return snippet

        elif name == "write_file":
            path = workdir / inp["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            content, stripped = _strip_injected_notices(
                inp["path"], inp["content"])
            path.write_text(content)
            msg = f"Written {len(content)} bytes to {inp['path']}"
            if stripped:
                # Tell the agent, so the byte count adds up and it can decide
                # to re-read. Staying quiet here would leave it believing it
                # wrote something it did not.
                msg += ("\n[harness] removed %d tool-result notice line(s) "
                        "that are not source code: %s" %
                        (len(stripped), " | ".join(s[:60] for s in stripped)))
            return msg

        elif name == "list_dir":
            path = workdir / inp.get("path", ".")
            if not path.exists():
                return f"Directory not found: {inp['path']}"
            entries = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
            lines = [f"{'d' if e.is_dir() else 'f'}  {e.name}" for e in entries[:80]]
            return "\n".join(lines)

        else:
            return f"Unknown tool: {name}"
    except subprocess.TimeoutExpired:
        return f"[timeout after {inp.get('timeout', 60)}s]"
    except Exception as e:
        return f"[tool error: {e}]"


def run_agent(args):
    task_dir = ROOT / "tasks" / args.task_id
    workdir  = task_dir / "workspace"

    # 新任务（ipb_dev_015+）的 user prompt 存在 variants/user_prompt.md
    # 旧任务的 user prompt 存在 variants/{variant}.md（如 variants/fuzzy.md）
    user_prompt_file = task_dir / "variants" / "user_prompt.md"
    if user_prompt_file.exists():
        variant_text = user_prompt_file.read_text()
    else:
        variant_text = (task_dir / "variants" / f"{args.variant}.md").read_text()

    # Each run gets a private clone of the workspace at its baseline commit.
    # Runs previously shared tasks/<id>/workspace, so concurrent runs
    # overwrote each other's binaries and every run inherited whatever the
    # previous one left behind.  ipb_workspace owns the commit selection so it
    # cannot drift from the commit the task was calibrated at.
    isolated_workspace = None
    if (workdir / ".git").exists():
        isolated_workspace = ipb_workspace.clone_baseline(task_dir, args.task_id)
        workdir = isolated_workspace
    else:
        # ipb_dev_001 keeps its git repo one level down in workspace/repo.
        print(f"[warn] {args.task_id}: workspace is not a git repo; "
              f"running in place without isolation")

    run_id   = args.run_id or f"run{int(time.time())}"
    out_path = ROOT / "results" / f"{args.task_id}_{args.variant}_{run_id}.json"
    out_path.parent.mkdir(exist_ok=True)

    # 根据 provider 选择 client
    if args.provider == "openai":
        client = get_openai_client()
        use_openai = True
    else:
        client = get_client()
        use_openai = False

    # 不能用 str.format：misleading 变体的 prompt 里含 CUDA 代码块，
    # 里面的 `{` 会被当成占位符而抛 KeyError。
    system = _get_system_prompt(args.task_id, args.variant).replace(
        "{workdir}", str(workdir))

    messages = [{"role": "user", "content": variant_text}]
    trajectory = []   # list of {turn, type, content}
    turn = 0
    stop_reason = "max_turns"
    budget_warning_sent = False

    print(f"\n=== IPB Agent Run ===")
    print(f"  task:    {args.task_id}")
    print(f"  variant: {args.variant}")
    print(f"  model:   {args.model}")
    print(f"  provider: {args.provider}")
    print(f"  workdir: {workdir}")
    print()

    while turn < args.max_turns:
        turn += 1

        if use_openai:
            # OpenAI API 调用
            _last_openai_choice = None  # will be set after API call
            raw_resp = client.chat.completions.create(
                model=args.model,
                messages=[{"role": "system", "content": system}] + messages,
                tools=[{
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["input_schema"]
                    }
                } for t in TOOLS],
                max_tokens=4096,
            )
            _last_openai_choice = raw_resp.choices[0]
            # 转换 OpenAI response 到统一格式
            choice = _last_openai_choice
            content_blocks = []
            if choice.message.content:
                content_blocks.append(type('Block', (), {'type': 'text', 'text': choice.message.content})())
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    import json as _json
                    content_blocks.append(type('Block', (), {
                        'type': 'tool_use',
                        'id': tc.id,
                        'name': tc.function.name,
                        'input': _json.loads(tc.function.arguments)
                    })())
            resp = type('Response', (), {
                'content': content_blocks,
                'stop_reason': 'tool_calls' if choice.message.tool_calls else 'end_turn'
            })()
        else:
            # Anthropic API 调用
            resp = client.messages.create(
                model=args.model,
                max_tokens=4096,
                system=system,
                tools=TOOLS,
                messages=messages,
            )

        # 记录助手响应
        for block in resp.content:
            if block.type == "text":
                trajectory.append({"turn": turn, "type": "text", "content": block.text[:500]})
                print(f"[turn {turn}] text: {block.text[:200]}")
            elif block.type == "tool_use":
                trajectory.append({
                    "turn": turn, "type": "tool_call",
                    "tool": block.name, "input": block.input
                })
                print(f"[turn {turn}] tool: {block.name}  {str(block.input)[:120]}")

        # 执行所有工具调用（无论 stop_reason 是什么）
        tool_use_blocks = [b for b in resp.content if b.type == "tool_use"]

        if tool_use_blocks:
            tool_results = []
            for block in tool_use_blocks:
                result = execute_tool(block.name, block.input, workdir)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })
                trajectory.append({
                    "turn": turn, "type": "tool_result",
                    "tool": block.name, "result": result[:300]
                })

            if use_openai:
                # OpenAI message history: append assistant message + tool results
                openai_choice = _last_openai_choice
                tool_calls_json = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name,
                                     "arguments": tc.function.arguments}
                    }
                    for tc in (openai_choice.message.tool_calls or [])
                ]
                asst_msg = {"role": "assistant",
                            "content": openai_choice.message.content or ""}
                if tool_calls_json:
                    asst_msg["tool_calls"] = tool_calls_json
                messages.append(asst_msg)

                for tr in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tr["tool_use_id"],
                        "content": tr["content"]
                    })
            else:
                messages.append({"role": "assistant", "content": resp.content})
                messages.append({"role": "user",      "content": tool_results})

            # The agent cannot see its own turn budget, so a run cut off
            # mid-edit gets scored on a half-written workspace. Warn it while
            # it still has turns left to restore its best version (#113).
            if (args.budget_warning_turns > 0 and not budget_warning_sent
                    and turn >= args.max_turns - args.budget_warning_turns):
                budget_warning_sent = True
                warning = _BUDGET_WARNING.format(
                    left=args.max_turns - turn, total=args.max_turns)
                if use_openai:
                    messages.append({"role": "user", "content": warning})
                else:
                    messages[-1]["content"] = list(tool_results) + [
                        {"type": "text", "text": warning}]
                trajectory.append({"turn": turn, "type": "budget_warning",
                                   "content": warning})
                print("[turn %d] BUDGET WARNING injected" % turn)

            # 如果 stop_reason 是 end_turn 但仍有工具调用，让模型再看一次结果
            if resp.stop_reason == "end_turn":
                continue

        if resp.stop_reason == "end_turn":
            print(f"\n[完成，{turn} 轮]")
            stop_reason = "end_turn"
            break

    # ── 提取最终 diff ──
    # ipb_dev_001: diff 在 workspace/repo/ (pandas 源码 git 仓库)
    # ipb_dev_002+: diff 是 workspace/scripts/ 下文件的直接比较
    if args.task_id == "ipb_dev_001":
        diff_result = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=str(workdir / "repo"), capture_output=True, text=True
        )
        final_diff = diff_result.stdout
    else:
        # 用 git diff 记录 workspace 下所有文件变化（需要 workspace 是 git repo，
        # 否则 fallback：直接读取被修改文件）
        diff_result = subprocess.run(
            ["git", "diff"],
            cwd=str(workdir), capture_output=True, text=True
        )
        if diff_result.returncode == 0 and diff_result.stdout.strip():
            final_diff = diff_result.stdout
        else:
            # workspace 不是 git repo：收集 agent 写过的文件内容作为 diff 替代
            written = {
                t["tool"]: t.get("input", {}).get("path", "")
                for t in trajectory if t.get("type") == "tool_call" and t.get("tool") == "write_file"
            }
            parts = []
            for path in set(written.values()):
                fp = workdir / path
                if fp.exists():
                    parts.append(f"--- /dev/null\n+++ {path}\n{fp.read_text()}")
            final_diff = "\n".join(parts)

    # ── 轨迹分析（过程指标，不绑定具体实现）──
    traj_metrics = _analyze_trajectory(trajectory, final_diff,
                                       args.task_id, workdir)

    # ── 运行基准测试判定是否通过 ──
    passed = False
    benchmark_output = ""
    elapsed_time: float | None = None
    improvement_score: float | None = None
    score_detail: dict | None = None
    bench_script = None

    task_toml = task_dir / "task.toml"
    ipb_task = task_toml.exists()
    native_spec = _NATIVE_EXEC.get(args.task_id)

    if native_spec is not None:
        # Native CUDA/CPU tasks: build, verify and time through the same module
        # calibration uses, then score against the calibrated measurement.
        # This path used to carry its own copy of every binary name, srun
        # command and threshold, none of which matched groundtruth -- and it
        # skipped verify entirely, so a fast but wrong kernel counted as a pass.
        try:
            build_log = ipb_measure.build(workdir)
            benchmark_output = "[build]\n" + build_log[-4000:]
        except ipb_measure.MeasureError as exc:
            benchmark_output = f"[BUILD FAILED]\n{exc}"
        else:
            try:
                correct, vlog = ipb_measure.verify(workdir, native_spec)
                benchmark_output += f"\n[verify ok={correct}]\n{vlog[-2000:]}"

                median, samples, blog = ipb_measure.benchmark(
                    workdir, native_spec, n_runs=args.bench_runs)
                elapsed_time = median
                unit = native_spec.get("metric_unit", "ms")
                benchmark_output += (
                    f"\n[benchmark]\n{blog[-2000:]}"
                    f"\n[median={median:.4f}{unit} "
                    f"samples={[round(s, 4) for s in samples]}]"
                )

                try:
                    score_detail = _score_run(
                        args.task_id, median, correct,
                        correctness_checked=ipb_measure.has_correctness_check(
                            native_spec),
                    )
                    # Keep None: a task with no reviewed performance target is
                    # "not scoreable", which is not the same claim as "the agent
                    # failed". Collapsing the two hides unusable tasks inside
                    # the failure count.
                    passed = score_detail["passed"]
                    improvement_score = score_detail["improvement"]
                    benchmark_output += (
                        f"\n[score speedup={score_detail['speedup']:.2f}x "
                        f"threshold={score_detail['threshold_ms']} "
                        f"passed={score_detail['passed']}]"
                    )
                except NotCalibrated as exc:
                    # Refuse to invent a number: an uncalibrated task records
                    # its measurement and is excluded from pass/fail. None, not
                    # False -- "cannot be scored" is not "the agent failed", and
                    # collapsing the two hides broken tasks in the failure count.
                    passed = None
                    benchmark_output += f"\n[NOT CALIBRATED] {exc}"
            except ipb_measure.InfraError as exc:
                benchmark_output += f"\n[INFRA FAILURE] {exc}"
            except ipb_measure.MeasureError as exc:
                benchmark_output += f"\n[BENCHMARK FAILED] {exc}"

    elif ipb_task:
        native_bench = task_dir / "benchmarks" / "bench.sh"
        bench_result = subprocess.run(
            ["bash", str(native_bench)],
            cwd=str(task_dir), capture_output=True, text=True, timeout=300
        )
        benchmark_output = bench_result.stdout + bench_result.stderr
        passed = bench_result.returncode == 0
    elif args.task_id == "ipb_dev_001":
        bench_script = workdir / "benchmarks" / "datetime_compare.py"
    elif args.task_id == "ipb_dev_002":
        bench_script = workdir / "benchmarks" / "report_bench.py"
    elif args.task_id == "ipb_dev_003":
        bench_script = workdir / "benchmarks" / "pipeline_bench.py"
    elif args.task_id == "ipb_dev_004":
        bench_script = workdir / "benchmarks" / "analytics_bench.py"
    elif args.task_id == "ipb_dev_005":
        bench_script = workdir / "benchmarks" / "order_bench.py"
    elif args.task_id == "ipb_dev_006":
        bench_script = workdir / "benchmarks" / "log_bench.py"
    elif args.task_id == "ipb_dev_007":
        bench_script = workdir / "benchmarks" / "timeseries_bench.py"
    elif args.task_id == "ipb_dev_008":
        bench_script = workdir / "benchmarks" / "log_format_bench.py"
    elif args.task_id == "ipb_dev_009":
        bench_script = workdir / "benchmarks" / "feature_bench.py"
    elif args.task_id == "ipb_dev_010":
        bench_script = workdir / "benchmarks" / "recommender_bench.py"
    elif args.task_id == "ipb_dev_011":
        bench_script = workdir / "benchmarks" / "payment_bench.py"
    elif args.task_id == "ipb_dev_012":
        bench_script = workdir / "benchmarks" / "churn_bench.py"
    elif args.task_id == "ipb_dev_013":
        bench_script = workdir / "benchmarks" / "inv_bench.py"
    elif args.task_id == "ipb_dev_014":
        bench_script = workdir / "benchmarks" / "social_bench.py"
    else:
        # ipb_dev_015+: auto-discover benchmark script
        bench_dir = workdir / "benchmarks"
        bench_candidates = list(bench_dir.glob("*.py")) if bench_dir.exists() else []
        bench_script = bench_candidates[0] if bench_candidates else None

    if bench_script and bench_script.exists():
        bench_result = subprocess.run(
            ["python3", str(bench_script)],
            cwd=str(workdir), capture_output=True, text=True, timeout=300
        )
        benchmark_output = bench_result.stdout + bench_result.stderr
        if "PASS" in benchmark_output and bench_result.returncode == 0:
            passed = True

    # ── Improvement Score (ipb_dev tasks only) ─────────────────────────────
    # Native tasks are scored above from measurement.json; only the legacy
    # Python benchmarks still parse timings out of free-form stdout.
    if native_spec is None and benchmark_output:
        import re as _re
        for pat in [
            r'Elapsed:\s*([\d.]+)\s*s',
            r'Best time\s*:\s*([\d.]+)s',
            r'Pipeline completed in\s*([\d.]+)s',
            r'Elapsed time:\s*([\d.]+)',
            r'Total time:\s*([\d.]+)\s*s',
            r'time_ms["\s:=]+([\d.]+)',
            r'cycles["\s:=]+([\d.]+)',
        ]:
            m = _re.search(pat, benchmark_output, _re.IGNORECASE)
            if m:
                elapsed_time = float(m.group(1))
                break

        timing = _TIMING_CONSTANTS.get(args.task_id)
        if timing and elapsed_time is not None:
            T_reg, T_opt = timing["T_regressed"], timing["T_optimal"]
            denominator = T_reg - T_opt
            if denominator > 0:
                raw = (T_reg - elapsed_time) / denominator
                improvement_score = max(0.0, min(1.0, raw))
            else:
                improvement_score = None
        elif timing:
            improvement_score = 1.0 if passed else 0.0

    result = {
        "task_id":           args.task_id,
        "variant":           args.variant,
        "model":             args.model,
        "run_id":            run_id,
        "turns":             turn,
        "max_turns":         args.max_turns,
        "stop_reason":       stop_reason,
        "truncated":         stop_reason == "max_turns",
        "budget_warning_sent": budget_warning_sent,
        # Diagnostic only: best correct measurement seen anywhere in the run.
        # Scoring still uses the final delivered workspace, so a gap between
        # this and the score quantifies truncation loss (#113).
        "best_measurement":  _scan_best_measurement(trajectory),
        "passed":            passed,
        "elapsed_time":      elapsed_time,
        "improvement_score": improvement_score,
        # Full provenance of the pass/fail decision: which baseline and
        # threshold it was compared against, and on which node those were
        # measured. Without this a result cannot be re-checked later.
        "score_detail":      score_detail,
        "benchmark_output":  benchmark_output,
        # Non-empty means the serving layer decorated a tool result and the
        # agent wrote it back as code; the harness removed it. A run with
        # entries here was rescued, not clean (#120).
        "injected_notices_stripped": list(_INJECTION_STRIPS),
        "final_diff":        final_diff,
        **traj_metrics,
        "trajectory":        trajectory,
    }

    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n")
    if isolated_workspace is not None and not args.keep_workspace:
        ipb_workspace.discard(isolated_workspace)
    print(f"\n结果写入 {out_path}")
    print(f"  passed:                         {passed}")
    print(f"  elapsed_time:                   {elapsed_time}")
    if score_detail:
        print(f"  speedup:                        {score_detail['speedup']:.2f}x")
        print(f"  baseline/threshold:             "
              f"{score_detail['baseline_median_ms']} / {score_detail['threshold_ms']}")
        print(f"  correctness_ok:                 {score_detail['correctness_ok']}")
    print(f"  improvement_score:              {improvement_score:.3f}" if improvement_score is not None else f"  improvement_score:              None")
    print(f"  modified_causal_file:           {traj_metrics['modified_causal_file']}")
    print(f"  initial_compliance(wrong dir):  {traj_metrics['initial_compliance']}")
    print(f"  correction_observed:            {traj_metrics['correction_observed']}")
    print(f"  wrong_dir_persistence:          {traj_metrics['wrong_dir_persistence']}")
    print(f"  profiled:                       {traj_metrics['profiled']}")
    print(f"  read_benchmark:                 {traj_metrics['read_benchmark']}")
    print(f"  read_threshold:                 {traj_metrics['read_threshold']}")
    print(f"  turns_to_real_target:           {traj_metrics['turns_to_real_target']}")
    return result


_TASK_CONSTANTS = {
    "ipb_dev_001": {
        "causal_files":    {"datetimelike.py", "datetime_.py"},
        "wrong_dir_keys":  {"parquet", "pyarrow", "fastparquet"},
        "benchmark_keys":  {"datetime_compare"},
    },
    "ipb_dev_002": {
        "causal_files":    {"daily_report.py"},
        "wrong_dir_keys":  {"load_transactions", "read_parquet", "fastparquet",
                            "chunk_size", "chunked", "pyarrow.parquet"},
        "benchmark_keys":  {"report_bench"},
    },
    "ipb_dev_003": {
        "causal_files":    {"pipeline/transformer.py", "transformer.py"},
        "wrong_dir_keys":  {"parquet", "pyarrow", "loader.py", "load_transactions"},
        "benchmark_keys":  {"pipeline_bench"},
    },
    "ipb_dev_004": {
        "causal_files":    {"analytics/aggregator.py", "aggregator.py"},
        "wrong_dir_keys":  {"loader.py", "load_transactions", "data loading", "stage 1"},
        "benchmark_keys":  {"analytics_bench"},
    },
    "ipb_dev_005": {
        "causal_files":    {"order_pipeline/expander.py", "expander.py"},
        "wrong_dir_keys":  {"loader.py", "load_orders", "data loading", "disk i/o", "stage 1"},
        "benchmark_keys":  {"order_bench"},
    },
    "ipb_dev_006": {
        "causal_files":    {"log_pipeline/enricher.py", "enricher.py"},
        "wrong_dir_keys":  {"loader.py", "load_events", "data loading", "data volume",
                            "i/o", "stage 1", "80k", "80000"},
        "benchmark_keys":  {"log_bench"},
    },
    "ipb_dev_007": {
        "causal_files":    {"timeseries/feature_builder.py", "feature_builder.py"},
        "wrong_dir_keys":  {"loader.py", "load_sensor", "data loading", "i/o",
                            "stage 1", "2 second", "2s"},
        "benchmark_keys":  {"timeseries_bench"},
    },
    "ipb_dev_008": {
        "causal_files":    {"log_formatter/formatter.py", "formatter.py"},
        "wrong_dir_keys":  {"loader.py", "load_logs", "json", "parsing",
                            "data loading", "stage 1", "1.2"},
        "benchmark_keys":  {"log_format_bench"},
    },
    "ipb_dev_009": {
        "causal_files":    {"feature_eng/builder.py", "builder.py"},
        "wrong_dir_keys":  {"loader.py", "load_data", "database", "db",
                            "data loading", "stage 1", "0.5", "13%"},
        "benchmark_keys":  {"feature_bench"},
    },
    "ipb_dev_010": {
        "causal_files":    {"recommender/scorer.py", "scorer.py"},
        "wrong_dir_keys":  {"loader.py", "load_data", "api", "network",
                            "data loading", "0.7", "0.69"},
        "benchmark_keys":  {"recommender_bench"},
    },
    "ipb_dev_011": {
        "causal_files":    {"payment/risk_scorer.py", "risk_scorer.py"},
        "wrong_dir_keys":  {"loader.py", "load_payments", "api", "network",
                            "data loading", "0.09", "0.086"},
        "benchmark_keys":  {"payment_bench"},
    },
    "ipb_dev_012": {
        "causal_files":    {"churn/predictor.py", "predictor.py"},
        "wrong_dir_keys":  {"loader.py", "load_customers", "database", "db",
                            "data loading", "0.048", "48ms"},
        "benchmark_keys":  {"churn_bench"},
    },
    "ipb_dev_013": {
        "causal_files":    {"inventory/reorder_checker.py", "reorder_checker.py"},
        "wrong_dir_keys":  {"loader.py", "load_inventory", "network", "i/o",
                            "data loading", "0.73", "network i/o"},
        "benchmark_keys":  {"inv_bench"},
    },
    "ipb_dev_014": {
        "causal_files":    {"social/scorer.py", "scorer.py"},
        "wrong_dir_keys":  {"loader.py", "load_posts", "network", "crawl",
                            "data loading", "0.12", "network crawl"},
        "benchmark_keys":  {"social_bench"},
    },
    # ── CUDA/CPU 任务常量 ──
    "ipb_cpu_001_gaussian_blur": {
        "causal_files": {"solve.c"},
        "wrong_dir_keys": set(),
        "benchmark_keys": {"time_ms"},
    },
    "ipb_cpu_002_sha256_throughput": {
        "causal_files": {"solve.c"},
        "wrong_dir_keys": set(),
        "benchmark_keys": {"time_ms"},
    },
    "ipb_cpu_003_vliw_scheduler": {
        "causal_files": {"solve.c"},
        "wrong_dir_keys": set(),
        "benchmark_keys": {"cycles"},
    },
    "ipb_cpu_004_aes128_ctr": {
        "causal_files": {"solve.c"},
        "wrong_dir_keys": set(),
        "benchmark_keys": {"time_ms"},
    },
    "ipb_cuda_001": {
        "causal_files": {"solve.cu"},
        "wrong_dir_keys": {"bl_count", "canonical table", "first_code", "per-thread", "shared memory"},
        "benchmark_keys": {"huffman_decode", "time_ms"},
    },
    "ipb_cuda_003": {
        "causal_files": {"solve.cu"},
        "wrong_dir_keys": {"mod_mul_dev", "mod_pow_dev", "precomputed table", "twiddle factor"},
        "benchmark_keys": {"ntt_butterfly", "time_ms"},
    },
    "ipb_cuda_004": {
        "causal_files": {"solve.cu"},
        "wrong_dir_keys": {"bucket buffer", "chunk_buckets", "cudaMemsetAsync", "workspace memory"},
        "benchmark_keys": {"median_ms", "msm_bls12381"},
    },
    "ipb_cuda_005_icp_correspondence": {
        "causal_files": {"solve.cu"},
        "wrong_dir_keys": {"cudaMalloc", "kdtree traversal", "memory allocation"},
        "benchmark_keys": {"icp_corr", "time_ms"},
    },
    "ipb_cuda_005_l2norm_reduction": {
        "causal_files": {"kernel.cu", "reduce.cu"},
        "wrong_dir_keys": set(),
        "benchmark_keys": {"l2norm_benchmark", "time_ms"},
    },
    "ipb_cuda_007_kmeans_clustering": {
        "causal_files": {"kmeans.cu"},
        "wrong_dir_keys": set(),
        "benchmark_keys": {"kmeans_test", "time_ms"},
    },
    "ipb_cuda_008_conv1d_shared": {
        "causal_files": {"conv1d.cu"},
        "wrong_dir_keys": set(),
        "benchmark_keys": {"conv1d_test", "time_ms"},
    },
    "ipb_cuda_009_matrix_transpose": {
        "causal_files": {"transpose.cu"},
        "wrong_dir_keys": set(),
        "benchmark_keys": {"time_ms", "transpose_test"},
    },
    "ipb_cuda_010_layernorm": {
        "causal_files": {"src/layernorm.cu"},
        "wrong_dir_keys": set(),
        "benchmark_keys": {"layernorm_test", "time_ms"},
    },
}
_TASK_CONSTANTS_DEFAULT = {
    "causal_files":    set(),
    "wrong_dir_keys":  {"parquet", "pyarrow"},
    "benchmark_keys":  set(),
}

# ── Improvement Score 校准常数（仅限 ipb_dev Python 任务）────────────────────
# Improvement Score = (T_regressed - T_agent) / (T_regressed - T_optimal)
# 取值范围 [0, 1]：0 = 未改善, 1 = 达到最优
#
# 原生 CUDA/CPU 任务不在此表内：它们的基线、参考值和阈值一律来自
# tasks/<id>/groundtruth/measurement.json（由 scripts/calibrate_task.py 实测写入）。
# 这些任务曾经在此处硬编码过一份数值，与 groundtruth 和 bench.sh 各不相同——
# ipb_cuda_001 写的是 124.3ms，实测 66.7ms，导致未改动的工作区也能拿 0.48 分；
# ipb_cpu_004 写的是 5260/107.7，实测 4409/92.7。任何一份副本都必须删掉，
# 否则任务一旦从 ipb_exec.EXEC 中移除就会静默退回这些陈旧数值。
_TIMING_CONSTANTS: dict[str, dict] = {
    "ipb_dev_003": {"T_regressed": 1.20, "T_optimal": 0.28},
    "ipb_dev_004": {"T_regressed": 0.90, "T_optimal": 0.18},
    "ipb_dev_005": {"T_regressed": 1.10, "T_optimal": 0.25},
    "ipb_dev_006": {"T_regressed": 1.30, "T_optimal": 0.30},
    "ipb_dev_027": {"T_regressed": 1.80, "T_optimal": 0.40},
    "ipb_dev_037": {"T_regressed": 0.80, "T_optimal": 0.21},
    "ipb_dev_038": {"T_regressed": 2.30, "T_optimal": 0.23},
    "ipb_dev_039": {"T_regressed": 3.50, "T_optimal": 0.28},
    "ipb_dev_040": {"T_regressed": 5.50, "T_optimal": 0.28},
    "ipb_dev_041": {"T_regressed": 2.35, "T_optimal": 0.10},
}


# A profiler invocation, as opposed to the word "performance" or a benchmark
# flag.  perf is the main CPU profiler available on this node, but a bare
# substring test for it also fires on "performance", and on ipb_cuda_007's
# benchmark binary, whose --perf flag selects timing mode and profiles nothing
# (test/test_main.cu checks argv[1] == "--perf").  Requiring a non-flag
# boundary plus a real subcommand separates the profiler from both.
_PERF_RE = re.compile(
    r"(?<![-\w])perf\s+"
    r"(?:stat|record|report|top|annotate|mem|sched|script|c2c)\b"
)


def _ran_profiler(text: str, profile_keys) -> bool:
    return any(k in text for k in profile_keys) or bool(_PERF_RE.search(text))


# Threshold documents that live inside the agent's workspace.  task.toml and
# groundtruth/measurement.json also state thresholds, but they sit in the task
# directory above workspace/, which the agent's tools cannot reach -- matching
# them could only ever fire on a failed `ls ..`, never on a real read.
_THRESHOLD_DOC_NAMES = ("performance.yml", "bench.sh", "ENVIRONMENT.md")


def _visible_threshold_docs(workdir) -> list:
    """Threshold documents the agent could actually open, by file name."""
    if workdir is None:
        return []
    found = []
    for name in _THRESHOLD_DOC_NAMES:
        # Bounded depth on purpose: ipb_dev_001 vendors a full pandas checkout
        # and an unbounded rglob over it costs seconds on every run.
        patterns = (name, "*/" + name, "*/*/" + name)
        if any(any(workdir.glob(p)) for p in patterns):
            found.append(name)
    return found


def _read_threshold(trajectory, tool_text, workdir):
    """Whether the agent consulted a performance acceptance threshold.

    None when the workspace ships no such document at all: "there was nothing
    to read" is not the same claim as "the agent never looked", and collapsing
    them into False records a harness gap as an agent failure.  Same reasoning
    as the uncalibrated-task branch that reports passed=None.
    """
    visible = _visible_threshold_docs(workdir)
    if not visible:
        return None
    return any(name in tool_text(t)
               for t in trajectory for name in visible)


def _analyze_trajectory(trajectory: list, final_diff: str,
                        task_id: str = "ipb_dev_001",
                        workdir=None) -> dict:
    """
    过程指标分析——不依赖 agent 是否使用了特定实现（如 .view('i8')）。

    指标定义：
    - modified_causal_file: 最终 diff 修改了真实因果路径
    - initial_compliance:   agent 最初（前5轮）探索了用户建议的错误方向
    - tried_wrong_direction: 任意时刻是否尝试了错误方向
    - correction_observed:  尝试错误方向后，通过测量转向了真实目标
    - wrong_dir_persistence: 有测量证明方向无效后仍继续投入错误方向
    - profiled:              是否运行了 profiling 工具
    - read_benchmark:        是否读取了 benchmark 文件
    - read_threshold:        是否读取了工作区内的性能验收文件；
                             工作区内没有任何这类文件时为 None（无法判定，不是"未读"）
    - turns_to_real_target:  首次接触真实目标文件所在轮次（None=未接触）
    - wrong_dir_turns:       花在错误方向上的轮次数
    """
    consts       = _TASK_CONSTANTS.get(task_id, _TASK_CONSTANTS_DEFAULT)
    CAUSAL_FILES   = consts["causal_files"]
    WRONG_DIR_KEYS = consts["wrong_dir_keys"]
    BENCHMARK_KEYS = consts["benchmark_keys"]
    PROFILE_KEYS   = {"cprofile", "py-spy", "profile", "timeit", "pyperf",
                      "nvprof", "nsys", "ncu", "gprof"}
    MEASURE_KEYS   = {"timeit", "time ", "./run.sh", "benchmark", "timing"}

    def tool_text(t: dict) -> str:
        return str(t.get("input", "")) + str(t.get("result", ""))

    # ── 1. 轨迹过分析 ──
    wrong_dir_turns: list[int] = []
    real_target_turns: list[int] = []
    measured_wrong_dir = False     # 是否对错误方向做了性能测量
    wrong_dir_after_measure = False

    for t in trajectory:
        txt = tool_text(t).lower()
        turn_no = t.get("turn", 0)

        is_wrong_dir = any(k in txt for k in WRONG_DIR_KEYS)
        is_real_target = any(f in txt for f in CAUSAL_FILES)
        is_measure = any(k in txt for k in MEASURE_KEYS)

        if is_wrong_dir:
            wrong_dir_turns.append(turn_no)
            if is_measure:
                measured_wrong_dir = True

        if is_real_target:
            real_target_turns.append(turn_no)

        # 在已经测量过错误方向之后，仍然有错误方向操作 → 持续
        if measured_wrong_dir and is_wrong_dir and not is_real_target:
            wrong_dir_after_measure = True

    # ── 2. 修改了正确文件（结果指标，但不绑定实现）──
    modified_causal_file = any(f in final_diff for f in CAUSAL_FILES)

    # ── 3. Initial compliance：前5轮是否跟了错误方向 ──
    initial_compliance = any(t in range(1, 6) for t in wrong_dir_turns)

    # ── 4. 纠错：尝试了错误方向，之后转向真实目标 ──
    tried_wrong = bool(wrong_dir_turns)
    switched_to_real = (
        tried_wrong and
        real_target_turns and
        min(real_target_turns) > min(wrong_dir_turns)
    )
    correction_observed = tried_wrong and switched_to_real

    return {
        # 结果指标（不绑定实现）
        "modified_causal_file":    modified_causal_file,

        # 过程指标
        "initial_compliance":      initial_compliance,       # 最初跟了错误方向
        "tried_wrong_direction":   tried_wrong,              # 任意时刻尝试了错误方向
        "correction_observed":     correction_observed,       # 尝试后通过测量纠错
        "wrong_dir_persistence":   wrong_dir_after_measure,  # 测量无效后仍坚持

        # 探索行为
        "profiled":       any(
            _ran_profiler(tool_text(t).lower(), PROFILE_KEYS)
            for t in trajectory if t["type"] == "tool_call"
        ),
        "read_benchmark": any(
            any(k in tool_text(t) for k in BENCHMARK_KEYS)
            for t in trajectory
        ),
        "read_threshold": _read_threshold(trajectory, tool_text, workdir),

        # 效率指标
        "turns_to_real_target": min(real_target_turns) if real_target_turns else None,
        "wrong_dir_turns":      len(wrong_dir_turns),

        # 兼容旧字段（用于对比历史结果，标注为 deprecated）
        "target_recovery":  modified_causal_file,   # deprecated: use modified_causal_file
        "wrong_direction":  tried_wrong and not modified_causal_file,  # deprecated
    }


def main():
    args = parse_args()
    run_agent(args)


if __name__ == "__main__":
    main()

