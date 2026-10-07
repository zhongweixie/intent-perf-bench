"""Run three independent Fuzzy episodes with the existing C8673 runner and grader."""
import datetime
import hashlib
import json
import os
import signal
import sys
from pathlib import Path

from orchestrator import episode, load, progress
from remote_client import ROOT, evaluate
from remote_controller import dump, sources


def worker(batch):
    try:
        protocol = load(ROOT / 'private' / 'protocol.json')
        prompt_path = ROOT / 'private' / 'fuzzy.txt'
        if not os.environ.get('OPENROUTER_API_KEY'):
            raise RuntimeError('API credential absent in launch environment')
        if 'fuzzy' not in protocol['conditions']:
            raise RuntimeError('Fuzzy condition absent from protocol')
        dump(batch / 'protocol.json', protocol)
        dump(batch / 'prompt_snapshot.json', {
            'fuzzy': {'text': prompt_path.read_text(encoding='utf-8'),
                      'sha256': hashlib.sha256(prompt_path.read_bytes()).hexdigest()}})
        base = sources()
        progress(batch, 'base_measurement')
        base_result = evaluate(base, 'smoke-base', timeout=600, final=True)
        dump(batch / 'base_result.json', base_result)
        if not base_result.get('correct'):
            raise RuntimeError('base score failed: ' + str(base_result.get('errors')))

        summary = {'baseline_ms': base_result['latency_ms'], 'repeats': [],
                   'note': 'Three fresh Fuzzy agents; unchanged prompt, protocol, runner and grader.'}
        for number in range(1, 4):
            run_dir = batch / (batch.name + '-r' + str(number))
            run_dir.mkdir()
            progress(batch, 'agent_running', repeat=number, of=3)
            status = episode(run_dir, 'fuzzy', protocol)
            final_files = {p.name: p.read_text(encoding='utf-8')
                           for p in (run_dir / 'fuzzy' / 'public').iterdir()
                           if p.name in base}
            result = evaluate(final_files, run_dir.name + '-fuzzy', timeout=600, final=True)
            dump(run_dir / 'fuzzy' / 'final_evaluation.json', result)
            row = {'repeat': number, 'correct': result.get('correct'),
                   'latency_ms': result.get('latency_ms'),
                   'speedup_vs_base': (base_result['latency_ms'] / result['latency_ms']
                                       if result.get('correct') and result.get('latency_ms') else None),
                   'status': status}
            summary['repeats'].append(row)
            dump(batch / 'summary.json', summary)
            progress(batch, 'repeat_complete', repeat=number,
                     correct=row['correct'], latency_ms=row['latency_ms'])
        dump(batch / 'completed.json', {'at': datetime.datetime.now().isoformat(),
                                        'episodes': len(summary['repeats'])})
        progress(batch, 'complete', episodes=3)
    except Exception as exc:
        dump(batch / 'failed.json', {'error_type': type(exc).__name__, 'error': str(exc)})
        progress(batch, 'failed', error=str(exc))
        raise


def launch():
    if not os.environ.get('OPENROUTER_API_KEY'):
        raise SystemExit('OPENROUTER_API_KEY is not loaded in this remote terminal')
    if not (ROOT / 'public' / 'CONTRACT.md').exists():
        raise SystemExit('Run python3 scripts/prepare.py first')
    batch = ROOT / 'runs' / ('fuzzy-repeats-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    batch.mkdir(parents=True, exist_ok=False)
    pid = os.fork()
    if pid:
        dump(batch / 'launcher.json', {'pid': pid, 'run_dir': str(batch)})
        print('STARTED', pid)
        print('RUN_DIR', batch)
        print('LOG', batch / 'runner.log')
        print('Three Fuzzy episodes run sequentially; closing VS Code will not stop them.')
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
