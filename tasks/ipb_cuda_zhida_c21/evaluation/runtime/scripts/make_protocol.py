"""Freeze hashes and settings before any model call."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
conditions = ["fuzzy", "misleading_other"]
public_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (root / "public").iterdir() if p.is_file()}
prompt_hashes = {name: hashlib.sha256((root / "private" / f"{name}.txt").read_bytes()).hexdigest()
                 for name in conditions}
protocol = {
    "case": "C21 Liger fused linear cross-entropy",
    "experiment": "One 500-second budget-sensitivity round, two independent conditions",
    "model": "deepseek/deepseek-v4.1-flash",
    "provider": "DeepInfra",
    "temperature": 0,
    "wall_seconds": 500,
    "max_queue_wait_seconds": 900,
    "max_generated_tokens": 40000,
    "max_api_attempts": 25,
    "total_tokens_response_threshold": 1000000,
    "per_response_max_tokens": 8192,
    "transport_retries": 2,
    "rounds": 1,
    "conditions": conditions,
    "gpu": "1",
    "workload": "Three BF16 full forward/backward input families; optional ignored targets",
    "final_artifact": "last saved public source files",
    "agent_feedback": "loss and gradient validity plus whole-call per-family timing",
    "measurement": "three balanced rotated process blocks per round; equal-weight geometric mean",
    "isolation": "fresh source tree, messages, and CUDA worker per condition and round",
    "hypotheses": {
        "misleading_other": "wide-vocabulary CE kernel occupancy/launch geometry may dominate",
    },
    "public_hashes": public_hashes,
    "prompt_hashes": prompt_hashes,
    "budget_notice": "remaining active time, generated tokens, API attempts shown before each model call",
}
(root / "private" / "protocol.json").write_text(json.dumps(protocol, ensure_ascii=False, indent=2), encoding="utf-8")
print(root / "private" / "protocol.json")
