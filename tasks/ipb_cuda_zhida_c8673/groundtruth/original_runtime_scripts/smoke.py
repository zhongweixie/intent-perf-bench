"""One-time no-API check of the exact frozen base evaluator."""
import json
import shutil
from remote_client import ROOT, evaluate
from remote_controller import sources

base = sources()
oracle = evaluate(base, 'smoke-base', timeout=600, oracle=True)
print('ORACLE', json.dumps(oracle), flush=True)
if not oracle.get('correct'):
    raise SystemExit(1)
shutil.copy2(ROOT/'workspaces'/'smoke-base'/'_pilot_records.pt',ROOT/'private'/'base_oracle.pt')
result = evaluate(base,'smoke-base',timeout=600,final=True)
print('BASE',json.dumps(result),flush=True)
if not result.get('correct'):
    raise SystemExit(1)
