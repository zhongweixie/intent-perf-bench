import json
from remote_client import evaluate
from remote_controller import sources
result = evaluate(sources(), 'smoke-base', timeout=240)
print(json.dumps(result))
if not result.get('correct'):
    raise SystemExit(1)
