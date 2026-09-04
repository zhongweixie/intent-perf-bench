"""
Step 5 (可选): 污染探针 —— 检测模型是否可能记住了历史任务答案

方法：
  1. 无仓库记忆探针：只给模糊描述，不给代码，测试模型是否能猜中历史函数
  2. Patch 相似度分析：比较 agent patch 与专家 patch 的非必要细节重合度

用法：
    python scripts/05_contamination_probe.py \
        --task-id ipb_dev_001 \
        --agent-patch results/ipb_dev_001_fuzzy_agent.diff \
        --model claude-opus-5
"""

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
TASKS_DIR = ROOT / "tasks"


def parse_args():
    p = argparse.ArgumentParser(description="污染风险探测")
    p.add_argument("--task-id",      required=True)
    p.add_argument("--agent-patch",  default=None, help="agent 提交的 patch（用于相似度分析）")
    p.add_argument("--model",        default="claude-opus-5")
    p.add_argument("--no-probe",     action="store_true", help="跳过 LLM 记忆探针，只做 patch 相似度")
    return p.parse_args()


def run_memory_probe(intent: dict, model: str) -> dict:
    """
    无仓库探针：只给模糊描述，测试模型能否直接说出历史函数名和文件路径。
    高风险信号：说出了 primary_targets 中的 symbol 或 file。
    """
    import anthropic
    client = anthropic.Anthropic()

    # 只提供非常高层的描述，不给仓库名和具体代码
    probe_prompt = (
        f"A Python repository has a performance issue. "
        f"The workload involves: {intent['primary_workload']}. "
        f"Without seeing the code, what files or functions are most likely responsible? "
        f"List your top 3 guesses with specific file paths and function names."
    )

    response = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": probe_prompt}],
    ).content[0].text

    # 检查 primary_targets 的符号是否出现在响应中
    target_symbols = [
        sym
        for t in intent.get("primary_targets", [])
        for sym in t.get("symbols", [])
    ]
    target_files = [t.get("file", "") for t in intent.get("primary_targets", [])]

    hits = {
        "symbols_mentioned": [s for s in target_symbols if s in response],
        "files_mentioned":   [f for f in target_files   if f.split("/")[-1] in response],
    }
    risk = "HIGH" if hits["symbols_mentioned"] else (
           "MEDIUM" if hits["files_mentioned"] else "LOW")

    return {
        "probe_response":    response[:500],
        "hits":              hits,
        "contamination_risk": risk,
    }


def patch_similarity(expert_patch: str, agent_patch: str) -> dict:
    """
    简单的行级相似度分析。
    非必要细节（变量名、注释、空行以外的差异）高度一致时为高风险。
    """
    expert_lines = set(l.strip() for l in expert_patch.splitlines() if l.startswith("+") and not l.startswith("+++"))
    agent_lines  = set(l.strip() for l in agent_patch.splitlines()  if l.startswith("+") and not l.startswith("+++"))

    if not expert_lines:
        return {"similarity": 0.0, "note": "expert patch 为空"}

    overlap = len(expert_lines & agent_lines)
    similarity = overlap / len(expert_lines)

    risk = "HIGH" if similarity > 0.80 else ("MEDIUM" if similarity > 0.50 else "LOW")
    return {
        "expert_added_lines":  len(expert_lines),
        "agent_added_lines":   len(agent_lines),
        "overlapping_lines":   overlap,
        "similarity":          round(similarity, 3),
        "risk":                risk,
        "note": (
            "相似度高并不直接证明记忆，强模型通过静态分析也可能得到相同修改" if risk == "HIGH"
            else "相似度正常范围"
        ),
    }


def main():
    args = parse_args()
    task_dir = TASKS_DIR / args.task_id
    intent   = json.loads((task_dir / "groundtruth" / "intent.json").read_text())

    report = {"task_id": args.task_id, "memory_probe": None, "patch_similarity": None}

    # 1. 记忆探针
    if not args.no_probe:
        print("运行无仓库记忆探针...")
        report["memory_probe"] = run_memory_probe(intent, args.model)
        risk = report["memory_probe"]["contamination_risk"]
        print(f"  污染风险: {risk}")
        if risk == "HIGH":
            print("  ⚠️  模型在无代码情况下直接说出了目标函数，应将此任务标为高污染风险")

    # 2. Patch 相似度
    if args.agent_patch:
        expert_diff = (task_dir / "groundtruth" / "expert_patch.diff").read_text()
        agent_diff  = pathlib.Path(args.agent_patch).read_text()
        print("分析 patch 相似度...")
        report["patch_similarity"] = patch_similarity(expert_diff, agent_diff)
        print(f"  相似度: {report['patch_similarity']['similarity']:.1%}  风险: {report['patch_similarity']['risk']}")

    # 写报告
    out = task_dir / "groundtruth" / "contamination_probe.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"\n报告已写入 {out}")


if __name__ == "__main__":
    main()
