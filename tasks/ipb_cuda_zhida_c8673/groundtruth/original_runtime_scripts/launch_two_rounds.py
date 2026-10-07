"""Launch two sequential, isolated rounds using the unchanged C8673 orchestrator."""
import datetime
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def worker(batch):
    try:
        for number in (1, 2):
            round_dir = batch / ('round' + str(number))
            round_dir.mkdir()
            save(batch / 'run_status.json', {'phase': 'running', 'round': number})
            subprocess.run([sys.executable, '-u', str(ROOT / 'scripts' / 'orchestrator.py'),
                            str(round_dir)], cwd=ROOT, check=True)
        save(batch / 'completed.json', {'at': datetime.datetime.now().isoformat(), 'rounds': 2})
        save(batch / 'run_status.json', {'phase': 'complete', 'rounds': 2})
    except Exception as exc:
        save(batch / 'failed.json', {'error_type': type(exc).__name__, 'error': str(exc)})
        save(batch / 'run_status.json', {'phase': 'failed', 'error': str(exc)})
        raise


def launch():
    if not os.environ.get('OPENROUTER_API_KEY'):
        raise SystemExit('OPENROUTER_API_KEY is not loaded in this remote terminal')
    if not (ROOT / 'public' / 'CONTRACT.md').exists():
        raise SystemExit('Public task files are missing')
    batch = ROOT / 'runs' / ('two-rounds-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    batch.mkdir(parents=True, exist_ok=False)
    pid = os.fork()
    if pid:
        save(batch / 'launcher.json', {'pid': pid, 'run_dir': str(batch)})
        print('STARTED', pid)
        print('RUN_DIR', batch)
        print('LOG', batch / 'runner.log')
        print('The two rounds run sequentially; closing VS Code will not stop the server job.')
        return
    os.setsid()
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    devnull = os.open('/dev/null', os.O_RDONLY)
    os.dup2(devnull, 0)
    os.close(devnull)
    logfile = os.open(str(batch / 'runner.log'), os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
    os.dup2(logfile, 1)
    os.dup2(logfile, 2)
    os.close(logfile)
    os.execv(sys.executable, [sys.executable, '-u', str(Path(__file__).resolve()),
                           '--worker', str(batch)])


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        worker(Path(sys.argv[2]).resolve())
    else:
        launch()
