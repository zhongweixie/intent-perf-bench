"""
Step 3: 用 LLM 根据 intent.json 生成四个 prompt 变体

前提：groundtruth/intent.json 的 TODO 字段已填写完毕，measurement.json 已有数据。

用法：
    python scripts/03_generate_variants.py --task-id ipb_dev_001 [--model claude-opus-5]
"""

import argparse
import json
import pathlib

TASKS_DIR = pathlib.Path("tasks")

# Meta-prompt 核心（来自 IPB 设计文档）
META_PROMPT_TEMPLATE = """You are a benchmark task designer constructing one instance for
Intent-Perf-Bench.

Intent-Perf-Bench evaluates whether a coding agent can recover the real
performance-engineering intent from repository evidence when the user
instruction is incomplete, vague, or contains a plausible but incorrect
diagnosis.

You are NOT being asked to invent a performance task from scratch.
You must transform the supplied verified seed task into paired instruction
variants while preserving exactly the same repository, workload, correctness
contract, and performance oracle.

====================
INPUTS
====================

Repository: {repo}
Base commit: {base_commit}
Primary workload: {primary_workload}
Known bottleneck: {primary_targets}
Required speedup threshold: {threshold}x
Threshold source file: {threshold_source}
Correctness contract: {correctness_contract}
Available repository evidence: {visible_evidence}
Candidate misdiagnosis: {misdiagnosed_targets}
Measured time share of misdiagnosis: {component_share}
Maximum speedup if misdiagnosis optimized to zero: {max_speedup_wrong}x

====================
CORE DESIGN RULES
====================

1. The instruction may be underspecified, but the environment must not be.
2. Do not turn the task into a riddle.
3. Visible evidence must never contradict hidden evaluation.
4. Distractors must be naturally present in the workload.
5. The fuzzy instruction must NOT contain: exact target function, exact source
   file, benchmark test name, numerical speedup threshold, or expert technique.
6. Retain natural constraints: do not change results, do not modify tests.
7. For a misleading variant, the wrong diagnosis must be provably insufficient:
   maximum_possible_speedup_wrong_direction < required_speedup.

====================
OUTPUT REQUIRED
====================

## C. Exact instruction
(concise, states target workload + component + performance requirement + constraints)

## D. Target-known instruction
(states what to optimize, omits numerical threshold)

## E. Fuzzy instruction
(2-5 sentences, natural user complaint, no exact bottleneck, no threshold)

## F. Misleading instruction
(confident but wrong diagnosis, some real evidence supports it, retains end goal)
If evidence does not justify a valid misleading variant, output: NO_VALID_MISLEADING_VARIANT

## G. Human audit checklist
(10 yes/no questions per the IPB protocol)

## H. Ground-truth intent JSON
(fill in the schema, do NOT invent measurements)
"""


def parse_args():
    p = argparse.ArgumentParser(description="生成四个 prompt 变体")
    p.add_argument("--task-id", required=True)
    p.add_argument("--model", default="claude-opus-5")
    return p.parse_args()


def load_task_context(task_id: str) -> dict:
    task_dir = TASKS_DIR / task_id
    intent = json.loads((task_dir / "groundtruth" / "intent.json").read_text())
    measurement = json.loads((task_dir / "groundtruth" / "measurement.json").read_text())
    return {"intent": intent, "measurement": measurement, "task_dir": task_dir}


def build_prompt(ctx: dict) -> str:
    intent = ctx["intent"]
    meas   = ctx["measurement"]
    mc     = intent.get("misdiagnosis_counterfactual", {})
    return META_PROMPT_TEMPLATE.format(
        repo                  = intent["source"]["instance_id"],
        base_commit           = "see groundtruth/expert_patch.diff",
        primary_workload      = intent["primary_workload"],
        primary_targets       = json.dumps(intent["primary_targets"], ensure_ascii=False),
        threshold             = intent["threshold"],
        threshold_source      = intent["threshold_source"],
        correctness_contract  = "see evaluation/correctness/",
        visible_evidence      = json.dumps(intent["visible_evidence"], ensure_ascii=False),
        misdiagnosed_targets  = json.dumps(intent["misdiagnosed_targets"], ensure_ascii=False),
        component_share       = mc.get("component_share", "N/A"),
        max_speedup_wrong     = mc.get("maximum_possible_speedup", "N/A"),
    )


def call_llm(prompt: str, model: str) -> str:
    """
    调用 Anthropic API 生成变体。

    支持两种凭证方式（通过 load_secrets.sh 加载）：
      - ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL  （claw 代理端点）
      - ANTHROPIC_API_KEY                          （直连，兜底）
    """
    import os
    import anthropic

    api_key  = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")   # None 时 SDK 用默认值

    assert api_key, (
        "未找到 Anthropic 凭证，请先执行：\n"
        "  source /home/hansirui_3rd/zxiebk/scripts/claw/claw-adapters/train/rl/load_secrets.sh"
    )

    kwargs = dict(api_key=api_key)
    if base_url:
        kwargs["base_url"] = base_url

    client = anthropic.Anthropic(**kwargs)
    msg = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def write_variants(response: str, task_dir: pathlib.Path):
    """将 LLM 输出按章节分割写入 variants/ 目录。"""
    sections = {
        "## C.": "exact.md",
        "## D.": "target_known.md",
        "## E.": "fuzzy.md",
        "## F.": "misleading.md",
    }
    lines = response.splitlines()
    current_key = None
    buffers: dict[str, list[str]] = {v: [] for v in sections.values()}

    for line in lines:
        for marker, fname in sections.items():
            if line.startswith(marker):
                current_key = fname
                break
        if current_key:
            buffers[current_key].append(line)

    variants_dir = task_dir / "variants"
    for fname, buf in buffers.items():
        if buf:
            (variants_dir / fname).write_text("\n".join(buf) + "\n")
            print(f"  写入 {variants_dir / fname}")

    # 完整响应存档
    (task_dir / "variants" / "_raw_llm_response.md").write_text(response)


def main():
    args = parse_args()
    ctx = load_task_context(args.task_id)
    prompt = build_prompt(ctx)
    print(f"正在调用 {args.model} 生成 prompt 变体...")
    response = call_llm(prompt, args.model)
    write_variants(response, ctx["task_dir"])
    print(f"完成。查看 tasks/{args.task_id}/variants/")


if __name__ == "__main__":
    main()
