"""One round with fresh contexts; reuse the established episode/watchdog logic."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from remote_client import ROOT, evaluate
from remote_controller import catalog, dump, secret, sources


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def progress(run_dir, phase, **details):
    dump(run_dir / 'run_status.json', {'phase': phase, 'at': datetime.datetime.now().isoformat(), **details})
    print('STATUS', phase, json.dumps(details), flush=True)


def episode(run_dir, condition, protocol):
    output = run_dir / condition
    output.mkdir()
    host = socket.gethostname().split('.')[0]
    namespace = host + '-' + run_dir.parent.name + '-' + run_dir.name + '-' + condition
    started = time.monotonic()
    with (output / 'agent.log').open('w', encoding='utf-8') as log:
        child = subprocess.Popen([sys.executable, '-u', str(ROOT / 'scripts/agent_episode.py'),
                                  condition, str(output), namespace], cwd=ROOT,
                                 stdout=log, stderr=subprocess.STDOUT,
                                 env=os.environ.copy(), start_new_session=True)
        while child.poll() is None:
            real = time.monotonic() - started
            clock_file = output / 'clock.json'
            clock = load(clock_file) if clock_file.exists() else None
            queued = 0.0 if clock is None else clock['paused_seconds'] + (
                time.monotonic() - clock['queue_since_monotonic']
                if clock['queue_since_monotonic'] is not None else 0)
            if real - queued > protocol['wall_seconds'] + 5 or queued > protocol['max_queue_wait_seconds'] + 5:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                raise RuntimeError('watchdog stopped ' + condition)
            time.sleep(1)
    if child.returncode:
        raise RuntimeError(condition + ' agent failed; see agent.log')
    return load(output / 'status.json')


def main():
    run_dir = Path(sys.argv[1]).resolve()
    protocol = load(ROOT / 'private/protocol.json')
    dump(run_dir / 'protocol.json', protocol)
    dump(run_dir / 'prompt_snapshot.json', {
        'common': (ROOT / 'private/common.txt').read_text(encoding='utf-8'),
        'conditions': {arm: {'text': (ROOT / 'private' / (arm + '.txt')).read_text(encoding='utf-8'),
                            'sha256': hashlib.sha256((ROOT / 'private' / (arm + '.txt')).read_bytes()).hexdigest()}
                       for arm in protocol['conditions']}})
    dump(run_dir / 'model_catalog.json', catalog(secret(), protocol['model']))
    base = sources()
    progress(run_dir, 'base_measurement')
    base_result = evaluate(base, run_dir.parent.name + '-' + run_dir.name + '-base', timeout=360, final=True)
    dump(run_dir / 'base_result.json', base_result)
    if not base_result.get('correct'):
        raise RuntimeError('baseline failed: ' + str(base_result))
    progress(run_dir, 'agents_running', conditions=protocol['conditions'], baseline_ms=base_result['latency_ms'])
    statuses = {}
    with ThreadPoolExecutor(max_workers=len(protocol['conditions'])) as pool:
        futures = {pool.submit(episode, run_dir, arm, protocol): arm for arm in protocol['conditions']}
        for future in as_completed(futures):
            arm = futures[future]
            statuses[arm] = future.result()
            print('AGENT_END', arm, statuses[arm]['stop_reason'], flush=True)
    progress(run_dir, 'final_comparison')
    final_sources = {arm: {p.name: p.read_text(encoding='utf-8')
                          for p in (run_dir / arm / 'public').iterdir() if p.name in base}
                     for arm in protocol['conditions']}
    reference = load(ROOT / 'private/reference.json')
    results = {}
    base_blocks, ref_blocks = [], []
    arm_blocks = {arm: [] for arm in protocol['conditions']}
    for block in (1, 2):
        order = protocol['conditions'] if block == 1 else list(reversed(protocol['conditions']))
        for name in ['base'] + order + ['reference']:
            submitted = base if name == 'base' else reference if name == 'reference' else final_sources[name]
            ns = run_dir.parent.name + '-' + run_dir.name + '-final-' + name
            result = evaluate(submitted, ns, timeout=360, final=True, seed=271828 + block)
            dump(run_dir / 'final_comparison' / (f'block{block}-' + name + '.json'), result)
            if name == 'base':
                base_blocks.append(result)
            elif name == 'reference':
                ref_blocks.append(result)
            else:
                arm_blocks[name].append(result)
                results[name] = result
                dump(run_dir / name / 'final_evaluation.json', result)
    if not all(x.get('correct') for x in base_blocks + ref_blocks):
        raise RuntimeError('baseline/reference failed during final comparison')
    def average(data):
        return sum(x['latency_ms'] for x in data) / len(data)
    baseline_ms, reference_ms = average(base_blocks), average(ref_blocks)
    summary = {'baseline_ms': baseline_ms, 'reference_ms': reference_ms,
               'reference_speedup': baseline_ms / reference_ms, 'comparison_blocks': 2,
               'arms': {}, 'warning': 'Exploratory repeats; inspect path/time/resource use before causal claims.'}
    for arm in protocol['conditions']:
        valid = all(x.get('correct') for x in arm_blocks[arm])
        latency = average(arm_blocks[arm]) if valid else None
        summary['arms'][arm] = {'correct': valid, 'latency_ms': latency,
                               'speedup_vs_base': baseline_ms / latency if valid else None,
                               'latency_ratio_to_reference': latency / reference_ms if valid else None,
                               'cases': results[arm].get('cases'), 'status': statuses[arm],
                               'remaining_seconds': max(0, protocol['wall_seconds'] - statuses[arm]['agent_seconds']),
                               'remaining_generated_tokens': max(0, protocol['max_generated_tokens'] - statuses[arm]['generated_tokens']),
                               'remaining_api_attempts': max(0, protocol['max_api_attempts'] - statuses[arm]['api_calls'])}
    dump(run_dir / 'summary.json', summary)
    dump(run_dir / 'completed.json', {'at': datetime.datetime.now().isoformat(), 'episodes': len(statuses)})
    progress(run_dir, 'complete', scores={k: v['speedup_vs_base'] for k, v in summary['arms'].items()})


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        run_dir = Path(sys.argv[1]).resolve()
        dump(run_dir / 'failed.json', {'error_type': type(exc).__name__, 'error': str(exc)})
        progress(run_dir, 'failed', error=str(exc))
        raise
