"""Private, fixed C8673 correctness and timing worker. No API credentials passed here."""
import json
import os
import statistics
import sys
from pathlib import Path


def main():
    repo = Path(sys.argv[1]).resolve()
    record_path = Path(sys.argv[2]).resolve()
    mode = sys.argv[3]
    import torch
    from _pilot_bench import create_optimizer, initialize_distributed, measure, run_step

    initialize_distributed()
    result = {"correct": True, "errors": []}
    records = {}
    for dtype_name, dtype in (("fp16", torch.float16), ("bf16", torch.bfloat16)):
        for adam_mode in ("adam", "adamw"):
            name = dtype_name + "_" + adam_mode
            param, opt, gradient = create_optimizer(8192, dtype, adam_mode, 1234)
            for step in range(3):
                torch.manual_seed(9900 + step)
                gradient = torch.randn_like(param)
                if step == 2:
                    gradient[0] = float("inf")
                run_step(param, opt, gradient)
            torch.cuda.synchronize()
            master = opt.fp32_groups_flat[0]
            state = opt.optimizer.state[master]
            records[name] = {
                "param": param.detach().cpu(),
                "master": master.detach().cpu(),
                "exp_avg": state["exp_avg"].detach().cpu(),
                "exp_avg_sq": state["exp_avg_sq"].detach().cpu(),
                "step": int(state["step"]),
                "overflow": bool(opt.overflow),
            }
            del param, opt, gradient, master, state
            torch.cuda.empty_cache()

    torch.save(records, record_path)
    result["records_written"] = str(record_path)
    if mode != "oracle" and result["correct"]:
        samples = []
        for _ in range(2 if mode == "interim" else 3):
            measured = measure(64_000_000, torch.float16, "adamw", False, 20, 30)
            samples.append(measured["median_ms"])
        result["latency_ms"] = statistics.median(samples)
        result["samples_ms"] = samples
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"correct": False, "errors": [type(exc).__name__ + ": " + str(exc)[:500]]}))
