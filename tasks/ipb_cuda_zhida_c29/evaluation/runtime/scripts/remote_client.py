import sys, tempfile, getpass, socket
"""Apply source snapshots to host-isolated exports; reuse the GPU queue protocol."""
import fcntl
import getpass
import json
import os
from pathlib import Path
import shutil
import socket
import signal
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
VENV = Path(os.environ.get('IPB_PYTHON',sys.executable)).absolute().parent.parent
PYTHON = os.environ.get('IPB_PYTHON',sys.executable)
HOST = socket.gethostname().split('.')[0]
LOCAL = Path(tempfile.gettempdir()) / getpass.getuser() / ('c29-' + HOST)
LOCAL.mkdir(parents=True, exist_ok=True)
GPU = os.environ.get('IPB_GPU',os.environ.get('C29_GPU','0'))
# Same physical GPU is serialized across all C27 batches on this host.
LOCK = Path(tempfile.gettempdir()) / getpass.getuser() / (HOST + '-gpu' + GPU + '.lock')
LOCK.parent.mkdir(parents=True, exist_ok=True)


def evaluate(files, namespace, timeout=400, on_queue_start=None, on_queue_end=None,
             oracle=False, final=False, seed=271828, **_unused):
    mapping = json.loads((ROOT / 'private/mapping.json').read_text())
    if any(alias not in mapping for alias in files):
        raise ValueError('invalid source alias')
    if '/' in namespace or '\\' in namespace or namespace in ('', '.', '..'):
        raise ValueError('invalid namespace')
    repo = ROOT / 'workspaces' / HOST / namespace
    if not repo.exists():
        repo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / 'source_base', repo)
    for alias, content in files.items():
        target = repo / mapping[alias]
        target.write_text(content, encoding='utf-8')
    # The independent evaluator is copied from a frozen private source each time.
    shutil.copy2(ROOT / 'scripts/grade_task.py', repo / '_pilot_grade.py')
    cache = LOCAL / namespace
    cache.mkdir(parents=True, exist_ok=True)
    for name in ('tmp', 'triton', 'torch', 'cache', 'home'):
        (cache / name).mkdir(exist_ok=True)
    env = {k:v for k,v in os.environ.items() if not any(w in k.upper() for w in ('API_KEY','TOKEN','SECRET','PASSWORD'))}
    env.pop('DEEPINFRA_API_KEY', None)
    env.pop('OPENROUTER_API_KEY', None)
    env.update(CUDA_VISIBLE_DEVICES=GPU, MAX_JOBS='4', PYTHONPATH=str(repo),
               OMP_NUM_THREADS='1', TMPDIR=str(cache / 'tmp'), HOME=str(cache / 'home'),
               TRITON_HOME=str(cache / 'triton'), TRITON_CACHE_DIR=str(cache / 'triton/cache'),
               TORCH_EXTENSIONS_DIR=str(cache / 'torch'), XDG_CACHE_HOME=str(cache / 'cache'))
    with LOCK.open('a') as lock:
        if on_queue_start:
            on_queue_start()
        started = time.monotonic()
        try:
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() - started > 1800:
                        return {'infrastructure_error': 'GPU queue wait exceeded 1800 seconds'}
                    time.sleep(0.1)
        finally:
            if on_queue_end:
                on_queue_end()
        try:
            worker_started = time.monotonic()
            proc = subprocess.Popen(
                [PYTHON, str(ROOT / 'scripts/sandbox.py'), str(repo), str(VENV), str(cache),
                 PYTHON, str(repo / '_pilot_grade.py'), str(repo),
                 'final' if final or oracle else 'interim', str(seed)],
                cwd=repo, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True)
            try:
                stdout, stderr = proc.communicate(timeout=max(0.1, timeout))
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
                raise
            lines = stdout.strip().splitlines()
            if not lines:
                return {'infrastructure_error': 'Evaluator produced no JSON: ' + stderr[-1500:]}
            try:
                result = json.loads(lines[-1])
            except json.JSONDecodeError:
                return {'infrastructure_error': 'Invalid evaluator JSON: ' + lines[-1][-1000:]}
            result['worker_seconds'] = time.monotonic() - worker_started
            if proc.returncode and result.get('correct'):
                return {'infrastructure_error': 'Evaluator exit contradicts correctness result'}
            if proc.returncode:
                result.setdefault('errors', []).append(stderr[-1500:])
            return result
        except subprocess.TimeoutExpired:
            return {'correct': False, 'errors': ['benchmark timed out before trial deadline']}
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
