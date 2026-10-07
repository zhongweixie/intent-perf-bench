"""Validate the task/reference, then detach one independent two-arm round."""
import datetime
import fcntl
import getpass
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    host = socket.gethostname().split('.')[0]
    if host != 'songcpu4':
        raise SystemExit('This experiment is restricted to songcpu4; nothing started')
    if not os.environ.get('DEEPINFRA_API_KEY', '').strip():
        if not sys.stdin.isatty():
            raise SystemExit('DEEPINFRA_API_KEY missing; run this launcher in the VS Code terminal')
        key = getpass.getpass('DeepInfra API key (hidden): ').strip()
        if not key:
            raise SystemExit('Empty API key; nothing started')
        os.environ['DEEPINFRA_API_KEY'] = key
    protocol = json.loads((ROOT / 'private/protocol.json').read_text())
    arms = len(protocol['conditions'])
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    batch = ROOT / 'runs' / host / stamp
    batch.mkdir(parents=True, exist_ok=False)
    for number in (1,):
        (batch / f'round{number}').mkdir()
    log = batch / 'runner.log'
    pid = os.fork()
    if pid:
        (batch / 'launcher.json').write_text(json.dumps({'pid': pid, 'hostname': host, 'batch_dir': str(batch)}, indent=2))
        print('STARTED', pid)
        print('BATCH_DIR', batch)
        print('LOG', log)
        print('First phase is baseline/reference validation; agents start only after it passes.')
        print(f'One round, {arms} concurrent agents per round. GPU evaluations serialize.')
        print('MODEL', protocol['model'], 'REASONING_EFFORT', protocol['reasoning_effort'])
        print('CONDITIONS', ', '.join(protocol['conditions']))
        print('The job is detached; closing VS Code will not stop it.')
        return
    os.setsid()
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    devnull = os.open('/dev/null', os.O_RDONLY)
    os.dup2(devnull, 0)
    os.close(devnull)
    logfile = os.open(str(log), os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
    os.dup2(logfile, 1)
    os.dup2(logfile, 2)
    os.close(logfile)
    # Prevent accidentally starting two batches from this same package/host.
    with (ROOT / 'private' / (host + '.batch.lock')).open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            (batch / 'failed.json').write_text(json.dumps({'error': 'Another C29 batch is already running on this host'}))
            print('A C29 batch is already running; this duplicate exited without agent calls.', flush=True)
            return
        # Reuse the completed package validation while task/grader bytes match.
        validation = ROOT / 'runs' / host / 'package-check' / 'preflight.json'
        stamp = ROOT / 'private' / 'validated_sources.json'
        cached = False
        if validation.exists() and stamp.exists():
            import hashlib
            validated = json.loads(validation.read_text())
            hashes = json.loads(stamp.read_text())
            cached = (validated.get('correct')
                      and all((ROOT / name).is_file() and hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                              for name, digest in hashes.items()))
        if cached:
            (batch / 'preflight').mkdir()
            (batch / 'preflight' / 'reused_validation.json').write_text(json.dumps({'source': str(validation), 'result': validated}, indent=2))
            print('REUSED_PASSING_PACKAGE_VALIDATION', flush=True)
            code = 0
        else:
            code = subprocess.call([sys.executable, '-u', str(ROOT / 'scripts/preflight.py'), str(batch / 'preflight')], cwd=ROOT)
        if code:
            (batch / 'failed.json').write_text(json.dumps({'phase': 'preflight', 'exit_code': code}))
            print('PREFLIGHT_FAILED; no agents started', flush=True)
            return
        results = []
        for number in (1,):
            code = subprocess.call([sys.executable, '-u', str(ROOT / 'scripts/orchestrator.py'), str(batch / f'round{number}')], cwd=ROOT)
            results.append({'round': number, 'exit_code': code})
            (batch / 'batch_status.json').write_text(json.dumps({'results': results, 'hostname': host}, indent=2))
            if code:
                break
        if len(results) == 1 and all(x['exit_code'] == 0 for x in results):
            (batch / 'completed.json').write_text(json.dumps({'completed': True, 'rounds': 1, 'arms_per_round': arms}))
            print('BATCH_COMPLETE', batch, flush=True)


if __name__ == '__main__':
    main()
