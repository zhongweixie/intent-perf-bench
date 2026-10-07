"""Independent adapter to the frozen per-case correctness/performance worker."""
import argparse, fcntl, getpass, hashlib, importlib.util, json, math, os
from pathlib import Path
import shutil, socket, subprocess, sys, tempfile, time, uuid

TASK = Path(__file__).resolve().parents[1]
RUNTIME = TASK / 'evaluation/runtime'

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def evaluate(candidate, final=True, seed=271828, timeout=600):
    cfg=load(TASK/'task.json')
    files={name:(Path(candidate)/name).read_text(encoding='utf8') for name in cfg['editable_files']}
    # Reject changes to initial visible support files, while permitting added scratch files.
    for p in (TASK/'workspace/repo').rglob('*'):
        if p.is_file() and str(p.relative_to(TASK/'workspace/repo')).replace('\\','/') not in cfg['editable_files']:
            q=Path(candidate)/p.relative_to(TASK/'workspace/repo')
            if not q.is_file() or q.read_bytes()!=p.read_bytes():
                return {'correct':False,'latency_ms':None,'errors':['Protected support file changed: '+str(p.name)]}
    spec=importlib.util.spec_from_file_location('ipb_case_remote_client', RUNTIME/'scripts/remote_client.py')
    module=importlib.util.module_from_spec(spec)
    sys.path.insert(0,str(RUNTIME/'scripts')); spec.loader.exec_module(module)
    result=module.evaluate(files, 'upload_'+uuid.uuid4().hex, final=final, seed=seed, timeout=timeout)
    # Source failures and infrastructure errors are separate endpoints. An incorrect
    # result never receives a valid speedup, even if its worker emitted a timer.
    ok=bool(result.get('correct')) and not result.get('infrastructure_error')
    latency=result.get('latency_ms')
    if latency is None and 'latency_us' in result:latency=result['latency_us']/1000
    if latency is None and result.get('cases'):
        values=[c['median_us']/1000 for c in result['cases']]
        latency=math.exp(sum(map(math.log,values))/len(values))
    return {'correct':ok,'latency_ms':latency if ok else None,'raw_worker_result':result,
            'seed':seed,'final':final,'task_id':cfg['task_id']}

def main():
    p=argparse.ArgumentParser()
    choices=p.add_mutually_exclusive_group(required=True)
    choices.add_argument('--candidate',type=Path)
    choices.add_argument('--patch',type=Path)
    choices.add_argument('--reference',action='store_true')
    choices.add_argument('--baseline',action='store_true')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seed',type=int,default=271828)
    p.add_argument('--timeout',type=int,default=600)
    p.add_argument('--interim',action='store_true')
    a=p.parse_args()
    cfg=load(TASK/'task.json')
    try:
        if a.patch:
            with tempfile.TemporaryDirectory(prefix='ipb-patch-') as td:
                shutil.copytree(TASK/'workspace/repo',td,dirs_exist_ok=True)
                subprocess.run(['git','apply','--check',str(a.patch.resolve())],cwd=td,check=True,capture_output=True)
                subprocess.run(['git','apply',str(a.patch.resolve())],cwd=td,check=True,capture_output=True)
                result=evaluate(td,not a.interim,a.seed,a.timeout)
        else:
            candidate=TASK/'groundtruth/reference_sources' if a.reference else TASK/'workspace/repo' if a.baseline else a.candidate
            result=evaluate(candidate,not a.interim,a.seed,a.timeout)
        if result['correct'] and cfg.get('historical_baseline_ms'):
            result['speedup_vs_historical_baseline']=cfg['historical_baseline_ms']/result['latency_ms']
            result['comparison_note']='Historical timing is context only; recalibrate a baseline in the same job for a new performance claim.'
    except Exception as exc:
        result={'task_id':cfg['task_id'],'correct':False,'latency_ms':None,
                'infrastructure_or_adapter_error':type(exc).__name__+': '+str(exc)}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result.get('correct') else 2

if __name__=='__main__':sys.exit(main())
