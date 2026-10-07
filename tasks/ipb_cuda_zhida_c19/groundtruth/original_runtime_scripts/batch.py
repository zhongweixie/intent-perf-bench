import datetime,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
batch=Path(sys.argv[1]).resolve()
def status(phase,**values):
    (batch/'batch_status.json').write_text(json.dumps({'phase':phase,**values},indent=2))
try:
    status('starting')
    for i in [1,2]:
        run=batch/('round'+str(i)+'-'+batch.name)
        run.mkdir()
        status('running',round=i,run_dir=str(run))
        subprocess.run([sys.executable,'-u',str(ROOT/'scripts'/'orchestrator.py'),str(run)],check=True)
    status('complete',rounds=2,episodes=6)
    (batch/'completed.json').write_text(json.dumps({'rounds':2,'episodes':6,'at':datetime.datetime.now().isoformat()}))
except Exception as exc:
    status('failed',error=str(exc))
    raise
