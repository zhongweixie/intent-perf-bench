"""Five-arm C8673 screening pilot. The only cross-arm shared resource is a GPU queue."""
import datetime
import hashlib
import json
import os
import shutil
import signal
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from remote_client import evaluate, ROOT
from remote_controller import catalog, dump, secret, sources

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def progress(run_dir, phase, **details):
    dump(run_dir/'run_status.json',{'phase':phase,'at':datetime.datetime.now().isoformat(),**details})
    print('STATUS',phase,json.dumps(details),flush=True)

def episode(run_dir, condition, protocol):
    output = run_dir/condition
    output.mkdir()
    namespace = run_dir.name+'-'+condition
    started = time.monotonic()
    with (output/'agent.log').open('w',encoding='utf-8') as log:
        child = subprocess.Popen([sys.executable,'-u',str(ROOT/'scripts'/'agent_episode.py'),
                                  condition,str(output),namespace],cwd=ROOT,
                                  stdout=log,stderr=subprocess.STDOUT,
                                  env=os.environ.copy(),start_new_session=True)
        while child.poll() is None:
            real = time.monotonic()-started
            clock_file = output/'clock.json'
            clock = load(clock_file) if clock_file.exists() else None
            queued = 0.0 if clock is None else clock['paused_seconds']+(
                time.monotonic()-clock['queue_since_monotonic'] if clock['queue_since_monotonic'] is not None else 0)
            if real-queued > protocol['wall_seconds']+5 or queued > protocol['max_queue_wait_seconds']+5:
                os.killpg(child.pid,signal.SIGTERM)
                try: child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL)
                    child.wait()
                raise RuntimeError('watchdog stopped '+condition)
            time.sleep(1)
    if child.returncode:
        raise RuntimeError(condition+' agent failed; see agent.log')
    return load(output/'status.json')

def main():
    run_dir=Path(sys.argv[1]).resolve()
    protocol=load(ROOT/'private'/'protocol.json')
    if not os.environ.get('OPENROUTER_API_KEY'):
        raise RuntimeError('API credential absent in launch environment')
    dump(run_dir/'protocol.json',protocol)
    dump(run_dir/'prompt_snapshot.json',{
        arm:{'text':(ROOT/'private'/(arm+'.txt')).read_text(encoding='utf-8'),
             'sha256':hashlib.sha256((ROOT/'private'/(arm+'.txt')).read_bytes()).hexdigest()}
        for arm in protocol['conditions']})
    dump(run_dir/'model_catalog.json',catalog(secret(),protocol['model']))
    base=sources()
    progress(run_dir,'base_measurement')
    base_result=evaluate(base,'smoke-base',timeout=600,final=True)
    dump(run_dir/'base_result.json',base_result)
    if not base_result.get('correct'):
        raise RuntimeError('base score failed: '+str(base_result.get('errors')))
    progress(run_dir,'prewarm_isolated_workspaces')
    for arm in protocol['conditions']:
        warm=evaluate(base,run_dir.name+'-'+arm,timeout=300)
        if not warm.get('correct'):raise RuntimeError('workspace prewarm failed: '+str(warm))
    progress(run_dir,'agents_running',conditions=protocol['conditions'],baseline_us=base_result.get('latency_us'))
    statuses={}
    with ThreadPoolExecutor(max_workers=len(protocol['conditions'])) as pool:
        futures={pool.submit(episode,run_dir,arm,protocol):arm for arm in protocol['conditions']}
        for future in as_completed(futures):
            arm=futures[future]
            statuses[arm]=future.result()
            print('AGENT_END',arm,statuses[arm]['stop_reason'],flush=True)
    progress(run_dir,'final_scoring')
    results={}
    for arm in protocol['conditions']:
        final_files={p.name:p.read_text(encoding='utf-8') for p in (run_dir/arm/'public').iterdir() if p.name in base}
        namespace=run_dir.name+'-'+arm
        result=evaluate(final_files,namespace,timeout=600,final=True)
        dump(run_dir/arm/'final_evaluation.json',result)
        results[arm]=result
    summary={'baseline_us':base_result['latency_us'],
             'arms':{arm:{'correct':result.get('correct'),
                          'latency_us':result.get('latency_us'),
                          'speedup_vs_base':base_result['latency_us']/result['latency_us'] if result.get('correct') and result.get('latency_us') else None,
                          'status':statuses[arm]}
                     for arm,result in results.items()},
             'warning':'Exploratory one-run pilot; inspect agent paths and repeat promising arms before claims.'}
    dump(run_dir/'summary.json',summary)
    dump(run_dir/'completed.json',{'at':datetime.datetime.now().isoformat(),'episodes':len(statuses)})
    progress(run_dir,'complete',scores={k:v['speedup_vs_base'] for k,v in summary['arms'].items()})

if __name__=='__main__':
    try: main()
    except Exception as exc:
        run_dir=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT
        dump(run_dir/'failed.json',{'error_type':type(exc).__name__,'error':str(exc)})
        progress(run_dir,'failed',error=str(exc))
        raise
