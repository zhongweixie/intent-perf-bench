"""Validate the real baseline/reference contract before any agent API spending."""
import json
import socket
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path
from remote_client import ROOT, evaluate
from remote_controller import dump, sources


def check(output=None):
    host = socket.gethostname().split('.')[0]
    stamp = time.strftime('%Y%m%d-%H%M%S')
    output = Path(output) if output else ROOT / 'runs' / host / ('preflight-' + stamp)
    output.mkdir(parents=True, exist_ok=True)
    gpu = os.environ.get('C29_GPU', '0')
    samples = []
    for _ in range(3):
        raw = subprocess.check_output([
            'nvidia-smi', '-i', gpu,
            '--query-gpu=index,name,utilization.gpu,memory.used,memory.free',
            '--format=csv,noheader,nounits'], text=True).strip()
        parts = [x.strip() for x in raw.split(',')]
        samples.append({'index': parts[0], 'name': parts[1],
                        'utilization_percent': int(parts[2]),
                        'memory_used_mib': int(parts[3]), 'memory_free_mib': int(parts[4])})
        time.sleep(0.5)
    dump(output / 'gpu_before.json', {'hostname': host, 'samples': samples})
    print('GPU_BEFORE', json.dumps(samples[-1]), flush=True)
    if statistics.median(x['utilization_percent'] for x in samples) >= 30:
        raise RuntimeError('Selected GPU is busy with other work; no agents started. Pick another idle C29_GPU or wait.')
    if min(x['memory_free_mib'] for x in samples) < 1024:
        raise RuntimeError('Selected GPU has less than 1 GiB free; no agents started.')
    base = evaluate(sources(), host + '-' + stamp + '-base', timeout=360, final=True)
    dump(output / 'base_result.json', base)
    if not base.get('correct'):
        raise RuntimeError('Baseline failed; no agents started: ' + str(base.get('errors') or base))
    ref_sources = json.loads((ROOT / 'private/reference.json').read_text())
    reference = evaluate(ref_sources, host + '-' + stamp + '-reference', timeout=360, final=True)
    dump(output / 'reference_result.json', reference)
    if not reference.get('correct'):
        raise RuntimeError('Full reference failed; no agents started: ' + str(reference.get('errors') or reference))
    ratio = base['latency_ms'] / reference['latency_ms']
    result = {'correct': True, 'baseline_ms': base['latency_ms'],
              'reference_ms': reference['latency_ms'], 'reference_speedup': ratio,
              'cases': [dict(name=b['name'], baseline_ms=b['latency_ms'], reference_ms=r['latency_ms'],
                             speedup=b['latency_ms'] / r['latency_ms'])
                        for b, r in zip(base['cases'], reference['cases'])],
              'note': 'Complete local token-movement export; no actual communication, GEMM or full training step.'}
    dump(output / 'preflight.json', result)
    print('FULL_CALL_PREFLIGHT', json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    check(sys.argv[1] if len(sys.argv) > 1 else None)
