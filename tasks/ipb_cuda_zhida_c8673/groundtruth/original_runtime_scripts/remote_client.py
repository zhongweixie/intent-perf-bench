"""Apply source snapshots to isolated base exports and evaluate on one GPU queue."""
import fcntl
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = '/home/cthong/ipb-candidates/.venv-cuda-screen/bin/python'
SITE = '/home/cthong/ipb-candidates/candidate8673-preflight/preflight_site'
LOCK = ROOT/'private'/'gpu0.lock'

def evaluate(files, namespace, timeout=400, on_queue_start=None, on_queue_end=None, oracle=False, final=False, **_unused):
    mapping = json.loads((ROOT/'private'/'mapping.json').read_text())
    repo = ROOT/'workspaces'/namespace
    if not repo.exists():
        shutil.copytree(ROOT/'source_base', repo, symlinks=True)
    for alias, content in files.items():
        if alias not in mapping:
            raise ValueError('invalid source alias')
        target = repo/mapping[alias]
        if target.read_text(encoding='utf-8') != content:
            target.write_text(content, encoding='utf-8')
    env = os.environ.copy()
    env.pop('OPENROUTER_API_KEY', None)
    env.update(CUDA_VISIBLE_DEVICES='0', MAX_JOBS='4',
               PATH='/home/cthong/ipb-candidates/.venv-cuda-screen/bin:/usr/local/cuda/bin:/usr/bin:/bin',
               PYTHONPATH=SITE+':'+str(repo), TORCH_EXTENSIONS_DIR=str(repo/'.torch_extensions'),
               OMP_NUM_THREADS='1', TMPDIR=str(repo/'_tmp'), HOME=str(repo),
               TRITON_HOME=str(repo/'_triton'),TRITON_CACHE_DIR=str(repo/'_triton'/'cache'),
               XDG_CACHE_HOME=str(repo/'_cache'))
    (repo/'_tmp').mkdir(exist_ok=True)
    record = repo/'_pilot_records.pt'
    with LOCK.open('a') as lock:
        if on_queue_start: on_queue_start()
        try:
            fcntl.flock(lock, fcntl.LOCK_EX)
        finally:
            if on_queue_end: on_queue_end()
        try:
            proc = subprocess.run([PYTHON,str(ROOT/'scripts'/'sandbox.py'),str(repo),
                                   '/home/cthong/ipb-candidates/.venv-cuda-screen',SITE,
                                   PYTHON,str(repo/'_pilot_grade.py'),str(repo),str(record),
                                   'oracle' if oracle else 'final' if final else 'interim'], cwd=repo, env=env,
                                  text=True,capture_output=True,timeout=timeout)
            lines = proc.stdout.strip().splitlines()
            result = json.loads(lines[-1]) if lines else {'correct':False,'errors':['no grade output']}
            result['worker_seconds_note'] = 'Includes correctness cases and timing, not just GPU kernel time'
            if proc.returncode:
                result['correct']=False
                result.setdefault('errors',[]).append(proc.stderr[-700:])
            if not oracle and record.exists():
                compare = subprocess.run([PYTHON,str(ROOT/'scripts'/'compare.py'),
                                         str(ROOT/'private'/'base_oracle.pt'),str(record)],
                                         text=True,capture_output=True,env=env,timeout=30)
                comparison = json.loads(compare.stdout.strip().splitlines()[-1])
                result['correct'] = bool(result.get('correct')) and comparison['correct']
                result.setdefault('errors',[]).extend(comparison['errors'])
            return result
        except subprocess.TimeoutExpired:
            return {'correct':False,'errors':['benchmark timed out']}
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
