"""Exploratory C21 correctness and full-call latency worker; runs only on songcpu4."""
import ast
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "vendor/liger_kernel"
EDITABLE = ("fused_linear_cross_entropy.py", "cross_entropy.py", "utils.py")
CASE_SPECS = (
    ("small", 512, 1024, 16384),
    ("main", 2048, 1024, 32768),
    ("wide_hidden", 1024, 2048, 32768),
)


def validate_source(files):
    if set(files) != set(EDITABLE):
        raise ValueError("Candidate must contain exactly the three editable operator files")
    permitted = {"torch", "triton", "packaging", "liger_kernel", "typing", "operator",
                 "functools", "importlib", "contextlib", "math"}
    forbidden_names = {"open", "exec", "eval", "compile", "__import__"}
    for name, code in files.items():
        if not isinstance(code, str) or len(code) > 100000:
            raise ValueError("Invalid source size")
        tree = ast.parse(code, filename=name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(item.name.split(".")[0] not in permitted for item in node.names):
                    raise ValueError(f"Disallowed import in {name}")
            elif isinstance(node, ast.ImportFrom):
                if not node.module or node.module.split(".")[0] not in permitted:
                    raise ValueError(f"Disallowed import in {name}")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_names:
                raise ValueError(f"Disallowed call in {name}")


def make_inputs(torch, bt, h, v, seed, ignored=False):
    torch.manual_seed(seed)
    x = (torch.randn(bt, h, dtype=torch.bfloat16, device="cuda") / 20).detach()
    w = (torch.randn(v, h, dtype=torch.bfloat16, device="cuda") / 20).detach()
    target = torch.randint(v, (bt,), device="cuda")
    if ignored:
        target[::17] = -100
    return x, w, target


def run_candidate(torch, fn, x0, w0, target):
    x = x0.detach().requires_grad_(True)
    w = w0.detach().requires_grad_(True)
    loss = fn.apply(x, w, target)[0]
    loss.backward()
    torch.cuda.synchronize()
    return loss.detach(), x.grad.detach(), w.grad.detach()


def run_reference(torch, x0, w0, target):
    x = x0.detach().requires_grad_(True)
    w = w0.detach().requires_grad_(True)
    logits = x @ w.t()
    loss = torch.nn.functional.cross_entropy(logits.float(), target, ignore_index=-100)
    loss.backward()
    torch.cuda.synchronize()
    return loss.detach(), x.grad.detach(), w.grad.detach()


def compare(torch, actual, expected, name):
    if actual.shape != expected.shape or not bool(torch.isfinite(actual).all()):
        raise AssertionError(f"{name}: shape or finiteness failure")
    a = actual.float()
    e = expected.float()
    diff = float(torch.linalg.vector_norm(a - e).item())
    scale = max(float(torch.linalg.vector_norm(e).item()), 1e-8)
    relative = diff / scale
    if relative > (0.008 if name == "loss" else 0.035):
        raise AssertionError(f"{name}: relative error {relative:.5f}")
    return relative


def evaluate(torch, fn, case, seed, repeats, ignored=False):
    name, bt, h, v = case
    x0, w0, target = make_inputs(torch, bt, h, v, seed, ignored)
    expected = run_reference(torch, x0, w0, target)
    actual = run_candidate(torch, fn, x0, w0, target)
    errors = {label: compare(torch, got, want, label)
              for label, got, want in zip(("loss", "input_grad", "weight_grad"), actual, expected)}
    del actual, expected
    for _ in range(2):
        run_candidate(torch, fn, x0, w0, target)
    samples = []
    for _ in range(repeats):
        torch.cuda.synchronize()
        started = time.perf_counter_ns()
        result = run_candidate(torch, fn, x0, w0, target)
        samples.append((time.perf_counter_ns() - started) / 1000.0)
        del result
    return {"name": name, "bt": bt, "h": h, "v": v, "median_us": statistics.median(samples),
            "samples_us": samples, "relative_errors": errors, "ignored_targets": ignored}


def main():
    request = json.load(sys.stdin)
    files = request["files"]
    validate_source(files)
    if not BASE.is_dir():
        raise RuntimeError("Frozen Liger dependency tree missing")
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    with tempfile.TemporaryDirectory(prefix="c21-flce-") as temp:
        package = Path(temp) / "liger_kernel"
        shutil.copytree(BASE, package, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in EDITABLE:
            (package / "ops" / name).write_text(files[name], encoding="utf-8")
        sys.path.insert(0, temp)
        from liger_kernel.ops.fused_linear_cross_entropy import LigerFusedLinearCrossEntropyFunction
        final = bool(request.get("final"))
        seed = int(request.get("seed", 21000))
        repeats = 7 if final else 4
        cases = []
        for i, case in enumerate(CASE_SPECS):
            cases.append(evaluate(torch, LigerFusedLinearCrossEntropyFunction, case,
                                  seed + i, repeats, ignored=(i == 2)))
        if final:
            # Correctness-only edge: larger ignore-index fraction and a fresh value set.
            evaluate(torch, LigerFusedLinearCrossEntropyFunction,
                     ("edge_ignored", 384, 1024, 8192), seed + 91, 1, ignored=True)
        print(json.dumps({"correct": True, "cases": cases, "device": torch.cuda.get_device_name(0)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"correct": False, "cases": [],
                          "error": f"{type(exc).__name__}: {str(exc)[:500]}"}))
