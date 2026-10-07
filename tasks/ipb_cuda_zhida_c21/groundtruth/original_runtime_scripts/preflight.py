"""No-API C21 eligibility and evaluator check on songcpu4."""
import json
from pathlib import Path
import sys

from remote_client import evaluate

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = Path("/home/cthong/ipb-candidates/liger-two-case-pilot/flce-a/src/liger_kernel/ops/fused_linear_cross_entropy.py")
B_REFERENCE = Path("/home/cthong/ipb-candidates/liger-two-case-pilot/flce-b/src/liger_kernel/ops")


def main():
    protocol = json.loads((ROOT / "private" / "protocol.json").read_text(encoding="utf-8"))
    assert protocol["wall_seconds"] == 500
    assert protocol["conditions"] == ["fuzzy", "misleading_other"]
    baseline = {p.name: p.read_text(encoding="utf-8") for p in (ROOT / "public").glob("*.py")}
    assert set(baseline) == {"fused_linear_cross_entropy.py", "cross_entropy.py", "utils.py"}
    base = evaluate(baseline, "c21-preflight-base", timeout=180, final=True)
    if not base.get("correct"):
        raise RuntimeError("Baseline did not pass: " + json.dumps(base)[:800])
    a_files = baseline.copy()
    a_files["fused_linear_cross_entropy.py"] = REFERENCE.read_text(encoding="utf-8")
    a = evaluate(a_files, "c21-preflight-a", timeout=180, final=True)
    if not a.get("correct"):
        raise RuntimeError("Known A patch did not pass: " + json.dumps(a)[:800])
    b_files = {name: (B_REFERENCE / name).read_text(encoding="utf-8") for name in baseline}
    b = evaluate(b_files, "c21-preflight-b", timeout=180, final=True)
    if not b.get("correct"):
        raise RuntimeError("Known B patch did not pass: " + json.dumps(b)[:800])
    mutant = baseline.copy()
    needle = "grad_input[start_idx:end_idx] = grad_logits_chunk @ weight"
    if mutant["fused_linear_cross_entropy.py"].count(needle) != 1:
        raise RuntimeError("Zero-gradient mutation location not found")
    mutant["fused_linear_cross_entropy.py"] = mutant["fused_linear_cross_entropy.py"].replace(
        needle, "grad_input[start_idx:end_idx] = 0", 1)
    bad = evaluate(mutant, "c21-preflight-bad", timeout=180)
    if bad.get("correct"):
        raise RuntimeError("Wrong input gradient was accepted")
    output = {"passed": True, "baseline": base, "reference_a": a, "reference_b": b,
              "wrong_gradient_rejected": True,
              "meaning": "No model API used; validates the task's basic loss/gradient oracle and timing path."}
    (ROOT / "private" / "preflight_passed.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PREFLIGHT_PASSED")
    for label, result in (("base", base), ("A", a), ("B", b)):
        print(label, [(case["name"], round(case["median_us"], 2)) for case in result["cases"]])


if __name__ == "__main__":
    main()
