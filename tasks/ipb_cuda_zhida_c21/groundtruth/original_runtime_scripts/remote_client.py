"""Call the isolated C21 worker with one package-wide GPU queue."""
import fcntl
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "private" / "flce_worker.py"
PYTHON = Path("/home/cthong/ipb-candidates/.venv-cuda-screen/bin/python")
QUEUE_LOCK = ROOT / "private" / "gpu-queue.lock"


def evaluate(files, namespace, timeout=240, on_queue_start=None, on_queue_end=None, **options):
    request = dict(files=files, namespace=namespace, **options)
    with QUEUE_LOCK.open("a") as lock:
        if on_queue_start is not None:
            on_queue_start()
        try:
            fcntl.flock(lock, fcntl.LOCK_EX)
        finally:
            if on_queue_end is not None:
                on_queue_end()
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = "1"
        try:
            result = subprocess.run([str(PYTHON), str(WORKER)], input=json.dumps(request),
                                    capture_output=True, text=True, encoding="utf-8",
                                    timeout=max(1.0, timeout), env=env)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
    if result.returncode:
        return {"infrastructure_error": f"worker exit {result.returncode}: {result.stderr[-700:]}"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"infrastructure_error": f"worker output was not JSON: {result.stdout[-700:]} {result.stderr[-300:]}"}
