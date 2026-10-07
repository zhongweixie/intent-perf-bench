"""Same isolated benchmark queue as C8673; C26 source and grading adapter."""
import fcntl,json,os,shutil,signal,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PYTHON='/home/cthong/ipb-candidates/.venv-cuda-screen/bin/python'
LOCK=ROOT/'private'/'gpu0.lock'

def child_run(command,timeout,**kwargs):
    child=subprocess.Popen(command,start_new_session=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,**kwargs)
    try:
        out,err=child.communicate(timeout=timeout)
        return child.returncode,out,err
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL)
        child.communicate()
        raise

def evaluate(files,namespace,timeout=400,on_queue_start=None,on_queue_end=None,oracle=False,final=False,**unused):
    repo=ROOT/'workspaces'/namespace
    if not repo.exists():shutil.copytree(ROOT/'source_base',repo)
    for name,content in files.items():
        if name not in ['pipeline.py','routing.py']:raise ValueError('invalid source alias')
        target=repo/name
        if target.read_text()!=content:target.write_text(content,encoding='utf-8')
    env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ['API_KEY','TOKEN','SECRET','PASSWORD'])}
    env.update(CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',TORCHINDUCTOR_COMPILE_THREADS='1',
               PATH='/home/cthong/ipb-candidates/.venv-cuda-screen/bin:/usr/local/cuda/bin:/usr/bin:/bin',
               PYTHONPATH=str(repo),HOME=str(repo),TMPDIR=str(repo/'_tmp'),
               TRITON_CACHE_DIR=str(repo/'_triton'),TORCHINDUCTOR_CACHE_DIR=str(repo/'_inductor'),
               XDG_CACHE_HOME=str(repo/'_cache'))
    (repo/'_tmp').mkdir(exist_ok=True)
    record=repo/'_pilot_records.pt'
    with LOCK.open('a') as lock:
        if on_queue_start:on_queue_start()
        try:fcntl.flock(lock,fcntl.LOCK_EX)
        finally:
            if on_queue_end:on_queue_end()
        try:
            record.unlink(missing_ok=True)
            command=[PYTHON,str(ROOT/'scripts'/'sandbox.py'),str(repo),
                '/home/cthong/ipb-candidates/.venv-cuda-screen','/usr/local/cuda',PYTHON,
                str(repo/'_pilot_grade.py'),str(repo),str(record),'oracle' if oracle else 'final' if final else 'interim']
            for attempt in range(2):
                code,out,err=child_run(command,timeout=timeout,cwd=repo,env=env)
                lines=out.strip().splitlines()
                result=json.loads(lines[-1]) if lines else {'correct':False,'errors':['no grade output']}
                if attempt==0 and not record.exists() and any('InductorError: SubprocException' in x for x in result.get('errors',[])):
                    continue
                break
            if code:
                result['correct']=False;result.setdefault('errors',[]).append(err[-1000:])
            return result
        except subprocess.TimeoutExpired:return {'correct':False,'errors':['benchmark timed out']}
        finally:fcntl.flock(lock,fcntl.LOCK_UN)
