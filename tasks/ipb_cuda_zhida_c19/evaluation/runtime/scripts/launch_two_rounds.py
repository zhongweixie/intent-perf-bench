"""Launch one detached songcpu4 experiment, inheriting the current shell key."""
import datetime, json, os, signal, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    if not os.environ.get('OPENROUTER_API_KEY'):
        raise SystemExit('OPENROUTER_API_KEY is not loaded in this remote terminal')
    if not (ROOT/'public'/'CONTRACT.md').exists():
        raise SystemExit('Run python3 scripts/prepare.py first')
    run_dir = ROOT/'runs'/('two-rounds-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    run_dir.mkdir(parents=True,exist_ok=False)
    pid = os.fork()
    if pid:
        (run_dir/'launcher.json').write_text(json.dumps({'pid':pid,'run_dir':str(run_dir)},indent=2))
        print('STARTED',pid)
        print('RUN_DIR',run_dir)
        print('LOG',run_dir/'runner.log')
        print('The process is detached; closing VS Code will not stop the server job.')
        return
    os.setsid()
    signal.signal(signal.SIGHUP,signal.SIG_IGN)
    devnull = os.open('/dev/null',os.O_RDONLY)
    os.dup2(devnull,0)
    os.close(devnull)
    logfile = os.open(str(run_dir/'runner.log'),os.O_CREAT|os.O_WRONLY|os.O_APPEND,0o600)
    os.dup2(logfile,1)
    os.dup2(logfile,2)
    os.close(logfile)
    os.execv(sys.executable,[sys.executable,'-u',str(ROOT/'scripts'/'batch.py'),str(run_dir)])

if __name__=='__main__':
    main()
