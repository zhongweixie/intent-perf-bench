"""C21 two-arm confirmation. Credentials remain in the launching server shell."""
import sys,os,json,time,re,hashlib,datetime,shutil,difflib,urllib.request,urllib.error,argparse,subprocess
from pathlib import Path
from remote_client import evaluate
ROOT=Path(__file__).resolve().parents[1]
def sources():return {p.name:p.read_text(encoding='utf-8') for p in (ROOT/'public').glob('*.py')}

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def secret():
    value=os.environ.get('OPENROUTER_API_KEY')
    if not value:raise RuntimeError('Remote API key not in current environment')
    return value.strip()

def catalog(key,model):
    req=urllib.request.Request('https://openrouter.ai/api/v1/models',headers={'Authorization':'Bearer '+key})
    with urllib.request.urlopen(req,timeout=30) as r:data=json.load(r)
    found=[x for x in data['data'] if x['id']==model]
    if not found:raise RuntimeError('Configured model unavailable; no fallback')
    return {k:found[0].get(k) for k in ['id','name','context_length','pricing','supported_parameters']}
def tool(name,desc,props,required=()):
    return {'type':'function','function':{'name':name,'description':desc,'parameters':{'type':'object','properties':props,'required':list(required),'additionalProperties':False}}}
S={'type':'string'};I={'type':'integer'}
TOOLS = [
    tool('list_files', 'List public task files.', {}),
    tool('read_file', 'Read public UTF-8 file lines inclusive.',
         {'path': S, 'start_line': I, 'end_line': I}, ['path']),
    tool('search_text', 'Literal search over public task files.',
         {'query': S, 'path': S, 'max_results': I}, ['query']),
    tool('write_file', 'Save complete editable Python source file.',
         {'path': S, 'content': S}, ['path', 'content']),
    tool('replace_text', 'Replace one exact block in a public Python file. Old block must occur exactly once.',
         {'path': S, 'old': S, 'new': S}, ['path', 'old', 'new']),
    tool('run_benchmark', 'Check fused CE loss and gradients against a PyTorch reference, then time full forward plus backward on the public workloads.', {}),
]
SYSTEM='''You are an autonomous coding agent working on a controlled performance optimization task. Use only the provided tools and public files. Follow CONTRACT.md. Background notes are fallible hypotheses. No shell, external solutions, private evaluator, previous trials or researcher results are available. Do not bypass evaluation or alter framework state. Save and test your implementation; the last saved source is your final submission. A budget notice is supplied before each model call. Return a brief final report when ready.'''

def run(condition,out,key,p,namespace):
    work=out/'public';shutil.copytree(ROOT/'public',work);events=[];benchmarks=[]
    start=time.monotonic();paused_total=0.;pause_started=None
    generated=inputs=attempts=actions=unknown=0;cost=0.;stop='unknown';final='';warnings=[]
    def elapsed():
        now=time.monotonic()
        return now-start-paused_total-(now-pause_started if pause_started is not None else 0.)
    def clock():
        target=out/'clock.json';temp=out/'clock.json.tmp'
        dump(temp,dict(start_monotonic=start,paused_seconds=paused_total,
                       queue_since_monotonic=pause_started,updated_monotonic=time.monotonic()))
        os.replace(temp,target)
    def event(kind,**kw):
        record=dict(kind=kind,elapsed_seconds=elapsed(),real_elapsed_seconds=time.monotonic()-start,**kw);events.append(record)
        with (out/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    def queue_start():
        nonlocal pause_started
        if pause_started is not None:raise RuntimeError('Nested GPU queue wait')
        pause_started=time.monotonic();clock();event('gpu_queue_start')
    def queue_end():
        nonlocal pause_started,paused_total
        if pause_started is None:raise RuntimeError('GPU queue exit without entry')
        waited=time.monotonic()-pause_started;paused_total+=waited;pause_started=None
        clock();event('gpu_queue_end',wait_seconds=waited)
    def files():return {x.name:x.read_text(encoding='utf-8') for x in work.glob('*.py')}
    def checkpoint(label):
        data=files();sha=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest();dump(out/'snapshots'/(sha+'.json'),data)
        event('checkpoint',label=label,source_sha256=sha,generated_tokens=generated,prompt_tokens=inputs,api_calls=attempts)
        return sha
    def path(name,write=False):
        base=work.resolve();target=(base/name).resolve()
        if base not in target.parents:raise ValueError('outside public directory')
        if write and (target.parent!=base or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*\.py',target.name)):raise ValueError('only root-level Python sources may be edited')
        return target
    def execute(name,args):
        nonlocal actions
        actions+=1
        if name=='list_files':return '\n'.join(sorted(x.name for x in work.iterdir() if x.is_file()))
        if name=='read_file':
            lines=path(args['path']).read_text(encoding='utf-8').splitlines();a=max(1,int(args.get('start_line',1)));b=min(a+499,int(args.get('end_line',a+299)))
            return '\n'.join(f'{i+1}: {line}' for i,line in enumerate(lines) if a<=i+1<=b)
        if name=='search_text':
            target=work if args.get('path','') in ['', '.'] else path(args['path']);results=[]
            entries=[target] if target.is_file() else sorted(target.glob('*'))
            for f in entries:
                if not f.is_file():continue
                for i,line in enumerate(f.read_text(encoding='utf-8').splitlines()):
                    if args['query'] in line:
                        results.append(f'{f.name}:{i+1}: {line}')
                        if len(results)>=min(100,int(args.get('max_results',40))):return '\n'.join(results)
            return '\n'.join(results) or 'No matches'
        if name in ['write_file','replace_text']:
            f=path(args['path'],True)
            if name=='replace_text':
                before=f.read_text(encoding='utf-8')
                if not args['old'] or before.count(args['old'])!=1:raise ValueError('old text must occur exactly once')
                after=before.replace(args['old'],args['new'],1)
            else:after=args['content']
            if len(after)+sum(len(v) for k,v in files().items() if k!=f.name)>200000:raise ValueError('total source too large')
            if elapsed()>=p['wall_seconds']:raise ValueError('deadline reached; source not saved')
            f.write_text(after,encoding='utf-8');return 'Saved '+checkpoint(name)
        if name=='run_benchmark':
            checkpoint('before_benchmark');remaining=p['wall_seconds']-elapsed()
            if remaining<8:return 'Insufficient wall time to start evaluation. Saved code will be graded.'
            r=evaluate(files(),namespace,timeout=remaining,final=False,
                       on_queue_start=queue_start,on_queue_end=queue_end)
            if r.get('infrastructure_error'):raise RuntimeError(r['infrastructure_error'])
            benchmarks.append(r);dump(out/'benchmarks.json',benchmarks)
            return json.dumps(r,ensure_ascii=False)
        raise ValueError('unknown tool')
    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':(ROOT/'private'/f'{condition}.txt').read_text(encoding='utf-8')}]
    clock();checkpoint('initial')
    try:
        while elapsed()<p['wall_seconds'] and generated<p['max_generated_tokens'] and inputs+generated<p['total_tokens_response_threshold'] and attempts<p['max_api_attempts']:
            remaining_s=max(0,int(p['wall_seconds']-elapsed()))
            notice=f"Budget remaining: {remaining_s} seconds; {max(0,p['max_generated_tokens']-generated)} generated tokens; {p['max_api_attempts']-attempts} API attempts; {max(0,p['total_tokens_response_threshold']-inputs-generated)} total-token guard headroom. Save and validate within these limits."
            if remaining_s<=90:notice+=" Final 90-second phase: stop speculative high-risk edits; save and validate the best correct version you have."
            messages.append({'role':'user','content':notice});warnings.append(dict(elapsed=elapsed(),notice=notice))
            payload={'model':p['model'],'messages':messages,'tools':TOOLS,'tool_choice':'auto','temperature':p['temperature'],'max_tokens':min(p['per_response_max_tokens'],p['max_generated_tokens']-generated),'provider':{'only':[p['provider']],'allow_fallbacks':False,'require_parameters':True,'data_collection':'deny'}}
            for retry in range(p['transport_retries']+1):
                if elapsed()>=p['wall_seconds']:stop='time_limit';break
                if attempts>=p['max_api_attempts']:stop='api_call_limit';break
                attempts+=1;dump(out/'requests'/f'{attempts:03}.json',payload)
                t=time.monotonic();event('api_start',call=attempts,transport_retry=retry)
                try:
                    child=subprocess.run([sys.executable,str(Path(__file__).with_name('c20_api_request.py'))],input=json.dumps(payload),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=max(.1,p['wall_seconds']-elapsed()))
                except subprocess.TimeoutExpired:
                    unknown+=1;event('api_error',call=attempts,seconds=time.monotonic()-t,error='hard_deadline',usage_unknown=True)
                    stop='time_limit';break
                if child.returncode:
                    unknown+=1;event('api_error',call=attempts,seconds=time.monotonic()-t,error='api_child_failed',usage_unknown=True)
                    raise RuntimeError('API request helper failed: '+child.stderr[-300:].replace(key,'[REDACTED]'))
                answer=json.loads(child.stdout)
                if answer['ok']:
                    reply=answer['reply'];break
                unknown+=1
                if answer['kind']=='http':
                    code=answer['status'];event('api_error',call=attempts,seconds=time.monotonic()-t,http_status=code,response_excerpt=answer['response_excerpt'],headers=answer['headers'],usage_unknown=True)
                    if code not in [429,500,502,503,504,520,521,522,524] or retry==p['transport_retries'] or p['wall_seconds']-elapsed()<8:raise RuntimeError('Model API HTTP '+str(code))
                else:
                    event('api_error',call=attempts,seconds=time.monotonic()-t,error=answer['error'],usage_unknown=True)
                    if retry==p['transport_retries'] or p['wall_seconds']-elapsed()<8:raise RuntimeError('Model API transport failure')
                time.sleep(2*(retry+1))
            if stop!='unknown':break
            usage=reply.get('usage',{});generated+=usage.get('completion_tokens',0);inputs+=usage.get('prompt_tokens',0);cost+=float(usage.get('cost') or 0)
            dump(out/'replies'/f'{attempts:03}.json',reply);event('api_end',call=attempts,seconds=time.monotonic()-t,usage=usage,provider=reply.get('provider'),model=reply.get('model'))
            if reply.get('model')!=p['model'] or reply.get('provider')!=p['provider']:raise RuntimeError('Returned model/provider does not match frozen protocol')
            if 'completion_tokens' not in usage or 'prompt_tokens' not in usage:raise RuntimeError('Missing usage; cannot enforce token limits')
            if not reply.get('choices'):raise RuntimeError('No choices')
            choice=reply['choices'][0];message=choice['message'];messages.append({k:v for k,v in message.items() if k in ['role','content','tool_calls','reasoning_details'] and v is not None})
            if elapsed()>=p['wall_seconds']:stop='time_limit';break
            if not message.get('tool_calls') and choice.get('finish_reason')=='length' and generated<p['max_generated_tokens']:
                # A per-response ceiling is not the trial's cumulative token budget.
                event('response_truncated',call=attempts,generated_tokens=generated,remaining_generated_tokens=p['max_generated_tokens']-generated)
                messages.append({'role':'user','content':'The previous response hit the per-response output limit. Continue from the current saved files within the same remaining trial budgets. This is a continuation, not a new trial; do not restart your investigation.'})
                dump(out/'messages.json',messages)
                continue
            if not message.get('tool_calls'):
                final=message.get('content','') or '';stop='generated_token_limit' if generated>=p['max_generated_tokens'] else 'total_token_threshold' if inputs+generated>=p['total_tokens_response_threshold'] else 'response_length_limit' if choice.get('finish_reason')=='length' else 'agent_finished';break
            for call in message['tool_calls']:
                if elapsed()>=p['wall_seconds']:stop='time_limit';break
                fn=call.get('function',{});name=fn.get('name');cid=call.get('id');tt=time.monotonic();event('tool_start',name=name,arguments=fn.get('arguments'))
                if not name or not cid:stop='invalid_model_tool_call';break
                try:args=json.loads(fn.get('arguments'));result=execute(name,args)
                except (ValueError,KeyError,TypeError,OSError) as e:result='Tool error: '+str(e)
                event('tool_end',name=name,seconds=time.monotonic()-tt,result=result[:24000]);messages.append({'role':'tool','tool_call_id':cid,'content':result[:24000]})
            dump(out/'messages.json',messages)
            print(condition,'call',attempts,'generated',generated,'elapsed',round(elapsed()),'benchmarks',len(benchmarks),flush=True)
            if stop!='unknown':break
        if stop=='unknown':stop='generated_token_limit' if generated>=p['max_generated_tokens'] else 'total_token_threshold' if inputs+generated>=p['total_tokens_response_threshold'] else 'api_call_limit' if attempts>=p['max_api_attempts'] else 'time_limit'
    except Exception as e:
        stop='infrastructure_error';event('error',message=(type(e).__name__+': '+str(e)).replace(key,'[REDACTED]'))
    duration=elapsed();sha=checkpoint('final');dump(out/'messages.json',messages);clock()
    benchmark_wall=sum(e.get('seconds',0) for e in events if e['kind']=='tool_end' and e['name']=='run_benchmark')
    status=dict(condition=condition,stop_reason=stop,agent_seconds=duration,
                real_wall_seconds=time.monotonic()-start,gpu_queue_wait_seconds=paused_total,
                api_calls=attempts,tool_actions=actions,generated_tokens=generated,prompt_tokens=inputs,
                total_tokens=generated+inputs,reported_cost_usd=cost,failed_requests_usage_unknown=unknown,
                final_source_sha256=sha,final_answer=final,namespace=namespace,budget_notices=len(warnings),
                api_seconds=sum(e.get('seconds',0) for e in events if e['kind'] in ['api_end','api_error']),
                tool_seconds=sum(e.get('seconds',0) for e in events if e['kind']=='tool_end'),
                benchmark_seconds=benchmark_wall,benchmark_active_seconds=benchmark_wall-paused_total)
    dump(out/'status.json',status)
    diffs=[]
    for name,src in files().items():
        base=(ROOT/'public'/name);before=base.read_text(encoding='utf-8') if base.exists() else ''
        diffs.extend(difflib.unified_diff(before.splitlines(True),src.splitlines(True),fromfile='baseline/'+name,tofile=condition+'/'+name))
    (out/'final.diff').write_text(''.join(diffs),encoding='utf-8');print('TRIAL_END',json.dumps(status,ensure_ascii=False),flush=True)
    return status


# Invoked by scripts/agent_episode.py; orchestration is separate.
