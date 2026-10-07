import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--task-id',required=True);a,rest=p.parse_known_args()
root=Path(__file__).resolve().parents[1]
ids={'ipb_cuda_zhida_c19','ipb_cuda_zhida_c21','ipb_cuda_zhida_c29','ipb_cuda_zhida_c8673'}
if a.task_id not in ids:p.error('Not a Zhida task ID')
sys.exit(subprocess.call([sys.executable,str(root/'tasks'/a.task_id/'evaluation/evaluate.py'),*rest]))
