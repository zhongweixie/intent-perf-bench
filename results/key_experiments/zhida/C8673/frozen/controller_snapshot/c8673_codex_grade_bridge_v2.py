"""Reconnectable evaluator jobs. Caller-only; never included in the solver environment."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/home/cthong/ipb-candidates/candidate8673-clearer-v4')
CACHE = ROOT / 'runs' / 'codex-grade-bridge-v2'


def dump(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value), encoding='utf8')
    os.replace(temp, path)


def worker(job):
    request = json.loads((job / 'request.json').read_text())
    sys.path.insert(0, str(ROOT / 'scripts'))
    import remote_client
    remote_client.LOCK = Path('/tmp/cthong/songcpu4-gpu0.lock')
    remote_client.LOCK.parent.mkdir(exist_ok=True)
    def phase(name):
        dump(job / 'status.json', {'phase': name, 'at': time.time()})
    try:
        workspace = request.get('workspace_namespace', request['namespace'])
        if not workspace.startswith('codex61m_') or not workspace.replace('_', '').isalnum():
            raise ValueError('invalid workspace namespace')
        # Each solver retains its own build cache, as in the old grader. Snapshot
        # jobs remain separately cached; this lock prevents an abandoned interim
        # evaluation and final evaluation from changing the same workspace together.
        with (CACHE / (workspace + '.workspace.lock')).open('a') as lock:
            phase('queued')
            fcntl.flock(lock, fcntl.LOCK_EX)
            phase('preparing')
            result = remote_client.evaluate(
                request['files'], workspace, timeout=request['timeout'],
                final=request.get('final', False),
                on_queue_start=lambda: phase('queued'),
                on_queue_end=lambda: phase('running'))
        dump(job / 'result.json', result)
        phase('complete')
    except Exception as exc:
        dump(job / 'infrastructure_error.json', {'error': str(exc)})
        phase('failed')


def attach(request):
    namespace = request['namespace']
    if not namespace.startswith('codex61m_') or not namespace.replace('_', '').isalnum():
        raise ValueError('invalid namespace')
    CACHE.mkdir(parents=True, exist_ok=True)
    job = CACHE / namespace
    job.mkdir(mode=0o700, exist_ok=True)
    digest = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
    with (job / 'start.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (job / 'request.sha256').exists():
            if (job / 'request.sha256').read_text() != digest:
                raise ValueError('namespace reused with a different submission')
        else:
            dump(job / 'request.json', request)
            (job / 'request.sha256').write_text(digest)
            phase = {'phase': 'preparing', 'at': time.time()}
            dump(job / 'status.json', phase)
            with (job / 'worker.log').open('a') as log:
                child = subprocess.Popen([sys.executable, __file__, '--worker', str(job)],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                    start_new_session=True, close_fds=True)
            (job / 'pid').write_text(str(child.pid))
    started = time.monotonic()
    last_phase = None
    while time.monotonic() - started < request['timeout'] + 1900:
        if (job / 'result.json').exists():
            print(json.dumps({'kind': 'result', 'result': json.loads((job / 'result.json').read_text())}), flush=True)
            return
        if (job / 'infrastructure_error.json').exists():
            raise RuntimeError((job / 'infrastructure_error.json').read_text())
        status = json.loads((job / 'status.json').read_text())
        phase = status['phase']
        if phase != last_phase:
            print(json.dumps({'kind': 'queue_start' if phase == 'queued' else 'queue_end'}), flush=True)
            last_phase = phase
        try:
            os.kill(int((job / 'pid').read_text()), 0)
        except ProcessLookupError:
            raise RuntimeError('detached evaluator exited without a result')
        time.sleep(0.25)
    raise TimeoutError('evaluator queue/worker watchdog exceeded')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        worker(Path(sys.argv[2]))
    else:
        try:
            attach(json.load(sys.stdin))
        except BrokenPipeError:
            # The detached worker keeps running; reconnect retrieves its exact result.
            pass
