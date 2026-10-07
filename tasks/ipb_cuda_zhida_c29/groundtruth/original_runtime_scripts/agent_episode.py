"""One isolated model episode, invoked by the remote OS-level watchdog."""
import json, os, sys
from pathlib import Path
from remote_controller import ROOT, run, secret

if __name__=='__main__':
    condition, output, namespace = sys.argv[1:4]
    protocol = json.loads((ROOT/'private'/'protocol.json').read_text(encoding='utf-8'))
    if condition not in protocol['conditions'] or not os.environ.get('DEEPINFRA_API_KEY'):
        raise RuntimeError('Invalid condition or missing remote API credential')
    run(condition,Path(output),secret(),protocol,namespace)

