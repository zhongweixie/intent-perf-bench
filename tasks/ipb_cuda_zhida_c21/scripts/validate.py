"""No-API validation: positive baseline/reference plus a wrong-answer mutant."""
import argparse, hashlib, importlib.util, json, shutil, sys, tempfile
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('adapter',TASK/'evaluation/evaluate.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    cfg=adapter.load(TASK/'task.json')
    rows={}
    for label,folder in [('baseline','workspace/repo'),('reference','groundtruth/reference_sources')]:
        print('VALIDATING',cfg['case'],label,flush=True)
        rows[label]=adapter.evaluate(TASK/folder,final=True,timeout=900)
        if not rows[label].get('correct'):break
    if all(rows.get(k,{}).get('correct') for k in ('baseline','reference')):
        with tempfile.TemporaryDirectory() as td:
            shutil.copytree(TASK/'workspace/repo',td,dirs_exist_ok=True)
            path=Path(td)/cfg['editable_files'][0]
            original=path.read_text(encoding='utf8')
            if cfg['case']=='C19':
                mutant=original+'\n_original_call = Pipeline.__call__\ndef _wrong_call(self):\n    value = _original_call(self)\n    self.out.zero_()\n    return value\nPipeline.__call__ = _wrong_call\n'
            elif cfg['case']=='C21':
                needle='grad_input[start_idx:end_idx] = grad_logits_chunk @ weight'
                assert original.count(needle)==1
                mutant=original.replace(needle,'grad_input[start_idx:end_idx] = 0')
            elif cfg['case']=='C29':
                mutant=original+'\ndef combine_from_routed(expert_output, top_scores, token_indices_sorted, top_k, score_apply, combine_impl, shape):\n    return expert_output.new_zeros(shape)\n'
            else:
                mutant=original+'\n_original_step = FP16_Optimizer.step\ndef _wrong_step(self, *args, **kwargs):\n    value = _original_step(self, *args, **kwargs)\n    self.fp32_groups_flat[0].data.zero_()\n    return value\nFP16_Optimizer.step = _wrong_step\n'
            path.write_text(mutant,encoding='utf8')
            rows['wrong_answer']=adapter.evaluate(td,final=False,timeout=240)
    negative=rows.get('wrong_answer',{})
    raw=negative.get('raw_worker_result',{})
    messages=' '.join(raw.get('errors',[]))+' '+raw.get('error','')
    numeric_rejection=not negative.get('correct',True) and any(x in messages for x in (
        'correctness failed','relative error','Tensor-likes are not close','Mismatched elements'))
    report={'task_id':cfg['task_id'],'positive_controls':rows,
            'negative_control_rejected_numerically':numeric_rejection,
            'passed':all(rows.get(k,{}).get('correct') for k in ('baseline','reference')) and numeric_rejection,
            'note':'Packaging check only; negative control changes numeric output/gradient/state. This does not add independent agent trials or replace archived performance.'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'task_id':cfg['task_id'],'passed':report['passed']}),flush=True)
    return 0 if report['passed'] else 2

if __name__=='__main__':sys.exit(main())
