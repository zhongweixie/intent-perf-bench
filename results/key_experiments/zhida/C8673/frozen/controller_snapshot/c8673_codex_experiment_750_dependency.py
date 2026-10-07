"""Controlled Codex sessions; the solver has dynamic public tools and no environment."""
import ast,concurrent.futures,datetime,hashlib,json,pathlib,queue,shutil,subprocess,threading,time,zipfile
from c8673_codex_rpc import RPC
BASE=pathlib.Path(__file__).resolve().parents[1]
SCRIPT=(BASE/'outputs/candidate8673-agent-pilot-v1/scripts/remote_controller.py').read_text(encoding='utf8')
# Extract literal system/tool declarations without importing the old API controller.
SYSTEM=next(ast.literal_eval(n.value) for n in ast.parse(SCRIPT).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='SYSTEM' for t in n.targets))
NAMES={'fused_optimizer.py','fused_adam.py','utils.py','multi_tensor_adam.cu','fused_adam_frontend.cpp','multi_tensor_apply.cuh'}
S={'type':'string'};I={'type':'integer'}
def spec(n,d,p,required=()):return {'type':'function','name':n,'description':d,'inputSchema':{'type':'object','properties':p,'required':list(required),'additionalProperties':False}}
TOOLS=[spec('list_files','List public task files.',{}),spec('read_file','Read public UTF-8 file lines inclusive.',{'path':S,'start_line':I,'end_line':I},['path']),spec('search_text','Literal search over public task files.',{'query':S,'path':S,'max_results':I},['query']),spec('write_file','Save one complete editable source file.',{'path':S,'content':S},['path','content']),spec('replace_text','Replace one exact block in an editable source file. Old block must occur exactly once.',{'path':S,'old':S,'new':S},['path','old','new']),spec('run_benchmark','Check optimizer correctness and measure the full mixed-precision step with the frozen benchmark. Reports absolute latency.',{})]
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def grade(files,ns,timeout=400,final=False,clock=None):
    req={'files':files,'namespace':ns,'timeout':max(1,timeout),'final':final}
    p=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','songcpu4','python3 /tmp/c8673_codex_grade_bridge.py'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8')
    p.stdin.write(json.dumps(req));p.stdin.close();result=None
    for line in p.stdout:
        d=json.loads(line)
        if d['kind']=='queue_start' and clock:clock.pause()
        elif d['kind']=='queue_end' and clock:clock.resume()
        elif d['kind']=='result':result=d['result']
    error=p.stderr.read();p.wait()
    if p.returncode or result is None:raise RuntimeError('remote evaluator infrastructure failure: '+error[-1200:])
    return result
class Clock:
    def __init__(self):self.start=time.monotonic();self.paused=0.;self.since=None;self.lock=threading.Lock()
    def pause(self):
        with self.lock:self.since=time.monotonic()
    def resume(self):
        with self.lock:
            if self.since is not None:self.paused+=time.monotonic()-self.since;self.since=None
    def elapsed(self):
        with self.lock:return time.monotonic()-self.start-self.paused-(time.monotonic()-self.since if self.since is not None else 0)
def episode(out,arm,roundno,stamp):
    out.mkdir(parents=True); public=out/'public';public.mkdir()
    for k,v in INITIAL.items():(public/k).write_text(v,encoding='utf8')
    snapshots=out/'snapshots';snapshots.mkdir()
    c=Clock();state={'model':'gpt-6.1-sol','reasoning_effort':'medium','condition':arm,'round':roundno,'generated_tokens':0,'prompt_tokens':0,'model_responses':0,'tool_actions':0,'stop_reason':None,'isolation':'environments=[]; only dynamic public tools; native shell/apps/web disabled','transport_errors':[],'benchmarks':[]}
    dump(out/'status.json',state)
    def files():return {k:(public/k).read_text(encoding='utf8') for k in NAMES}
    def checkpoint():
        f=files();sha=hashlib.sha256(json.dumps(f,sort_keys=True).encode()).hexdigest();dump(snapshots/(sha+'.json'),f);return sha
    def event(kind,**kw):
        with (out/'events.jsonl').open('a',encoding='utf8')as f:f.write(json.dumps(dict(kind=kind,elapsed_seconds=c.elapsed(),**kw),ensure_ascii=False)+'\n')
    def notice():return f"Budget remaining: {max(0,int(750-c.elapsed()))} seconds; {max(0,40000-state['generated_tokens'])} generated tokens; {max(0,32-state['model_responses'])} model responses. Save and validate within these limits. The last saved code is the submission."
    def path(k,write=False):
        if k not in INITIAL or (write and k not in NAMES):raise ValueError('Only public file aliases are accessible')
        return public/k
    def execute(n,a):
        if n=='list_files':return '\n'.join(sorted(INITIAL))
        if n=='read_file':
            lines=path(a['path']).read_text(encoding='utf8').splitlines();lo=max(1,int(a.get('start_line',1)));hi=min(lo+499,int(a.get('end_line',lo+299)))
            return '\n'.join(f'{i+1}: {s}' for i,s in enumerate(lines) if lo<=i+1<=hi)
        if n=='search_text':
            names=sorted(INITIAL) if a.get('path','')in['','.'] else [path(a['path']).name];results=[]
            for k in names:
                for i,line in enumerate(path(k).read_text(encoding='utf8').splitlines()):
                    if a['query']in line:results.append(f'{k}:{i+1}: {line}')
            return '\n'.join(results[:min(100,int(a.get('max_results',40)))])or'No matches'
        if n in ['write_file','replace_text']:
            if c.elapsed()>=750:raise ValueError('deadline reached; source not saved')
            p=path(a['path'],True);old=p.read_text(encoding='utf8')
            if n=='replace_text':
                if not a['old']or old.count(a['old'])!=1:raise ValueError('old text must occur exactly once')
                new=old.replace(a['old'],a['new'],1)
            else:new=a['content']
            if len(new)+sum(len(v)for k,v in files().items()if k!=p.name)>400000:raise ValueError('source too large')
            p.write_text(new,encoding='utf8');return'Saved '+checkpoint()
        if n=='run_benchmark':
            checkpoint();remain=750-c.elapsed()
            if remain<8:return'Insufficient wall time to start evaluation. Saved code will be graded.'
            result=grade(files(),f'codex61m_{stamp}_r{roundno}_{arm}',remain,clock=c)
            state['benchmarks'].append({'elapsed_seconds':c.elapsed(),**result});dump(out/'benchmarks.json',state['benchmarks']);return json.dumps(result)
        raise ValueError('unknown tool')
    rpc=None;tid=None;pending=[];failure=None
    try:
        rpc=RPC(out/'session');rpc.start(TOOLS,SYSTEM);state['thread_id']=rpc.thread
        prompt=COMMON+'\n\nBackground note:\n'+PROMPTS[arm]+'\n\n'+notice()
        dump(out/'prompt_snapshot.json',{'system':SYSTEM,'prompt':prompt,'tools':TOOLS})
        # Do not charge initialization to the solver; budget starts at first turn.
        c=Clock();checkpoint();rpc.turn(prompt);tid=rpc.turnid;event('started',thread=rpc.thread);print(f'STARTED round{roundno} {arm} {rpc.thread}',flush=True)
        pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
        interrupted=False
        while True:
            if not interrupted and (c.elapsed()>=750 or state['generated_tokens']>=40000 or state['model_responses']>=32 or state['prompt_tokens']+state['generated_tokens']>=1250000):
                state['stop_reason']='time_limit' if c.elapsed()>=750 else 'generated_token_limit'if state['generated_tokens']>=40000 else 'model_response_limit'if state['model_responses']>=32 else'total_token_limit'
                rpc.n+=1;rpc.send({'id':rpc.n,'method':'turn/interrupt','params':{'threadId':rpc.thread,'turnId':tid}});interrupted=True;event('interrupt',reason=state['stop_reason'])
            for item in pending[:]:
                request,future=item
                if not future.done():continue
                pending.remove(item)
                try:content=future.result();ok=True
                except Exception as e:content=str(e);ok=False
                event('tool_result',tool=request['params']['tool'],success=ok,content=content)
                rpc.send({'id':request['id'],'result':{'contentItems':[{'type':'inputText','text':content+'\n\n'+notice()}],'success':ok}})
            try:d=rpc.next(0.2)
            except queue.Empty:
                if rpc.p.poll()is not None:raise RuntimeError('server exited')
                continue
            m=d.get('method','')
            if m=='item/tool/call':
                n=d['params']['tool'];a=d['params']['arguments'];state['tool_actions']+=1;event('tool_call',tool=n,arguments=a)
                if n not in {t['name']for t in TOOLS}:raise RuntimeError('isolation violation: '+n)
                pending.append((d,pool.submit(execute,n,a)))
            elif 'id'in d and m:
                event('unexpected_server_request',method=m)
                rpc.send({'id':d['id'],'error':{'code':-32000,'message':'Not available in isolated experiment'}})
            elif m=='thread/tokenUsage/updated':
                u=d['params']['tokenUsage']['total'];state['generated_tokens']=u['outputTokens'];state['reasoning_output_tokens']=u['reasoningOutputTokens'];state['prompt_tokens']=u['inputTokens'];state['model_responses']+=1;event('usage',usage=u)
            elif m=='error':state['transport_errors'].append(d['params']);event('api_error',error=d['params'])
            elif m=='item/completed':
                item=d['params']['item']
                if item.get('type')=='agentMessage':event('agent_message',text=item.get('text'),phase=item.get('phase'))
                if item.get('type')in['commandExecution','fileChange','mcpToolCall']:raise RuntimeError('unexpected native tool: '+item['type'])
            elif m=='turn/completed':
                state['turn_status']=d['params']['turn']['status'];state['turn_error']=d['params']['turn'].get('error');state['stop_reason']=state['stop_reason']or state['turn_status'];break
            elif d.get('eof'):raise RuntimeError('server EOF')
            state['agent_seconds']=c.elapsed();state['gpu_queue_wait_seconds']=c.paused;dump(out/'status.json',state)
        pool.shutdown(wait=True);checkpoint()
    except Exception as e:failure=str(e);state['infrastructure_error']=failure;state['stop_reason']='infrastructure_error';print('EPISODE ERROR',arm,failure,flush=True)
    finally:
        state['agent_seconds']=c.elapsed();state['gpu_queue_wait_seconds']=c.paused;state['real_wall_seconds']=time.monotonic()-c.start;dump(out/'status.json',state)
        if rpc:rpc.close()
    # Final grading is outside the agent budget, using saved submission only.
    final=grade(files(),f'codex61m_{stamp}_r{roundno}_{arm}',900,final=True)
    dump(out/'final_evaluation.json',final);print('FINAL',roundno,arm,json.dumps(final),flush=True)
    return {'condition':arm,'status':state,'final_evaluation':final}
if __name__=='__main__':
    stamp=datetime.datetime.now().strftime('%Y%m%d%H%M%S');OUT=BASE/'outputs'/f'c8673-v4-codex61-medium-750s-{stamp}';OUT.mkdir()
    with zipfile.ZipFile(BASE/'outputs/c8673-v4-public.zip')as z:
        INITIAL={pathlib.PurePosixPath(n).name:z.read(n).decode('utf8')for n in z.namelist()if not n.endswith('/')}
    if set(INITIAL)!=NAMES|{'CONTRACT.md'}:raise RuntimeError('public archive mismatch')
    private=BASE/'outputs/candidate8673-clearer-v4/private';COMMON=(private/'common.txt').read_text(encoding='utf8');PROMPTS={k:(private/(k+'.txt')).read_text(encoding='utf8')for k in ['fuzzy','flatten_hint']}
    original=json.loads((private/'protocol.json').read_text(encoding='utf8'))
    dump(OUT/'protocol.json',{'original':original,'model':'gpt-6.1-sol','reasoning_effort':'medium','rounds':2,'conditions':list(PROMPTS),'budget_seconds':750,'total_token_guard':1250000,'calibration':'Exploratory 750s rerun after observing the 1100s batch; not a retrospective truncation.','generated_token_guard':40000,'model_response_guard':32,'notes':['Codex dynamic-tool harness. No environment, shell, apps, web, memory or prior solver history.','API response guard counts app-server usage notifications; transport retry attempts are separately recorded.','Token guard is checked after model responses; no per-response 8192 hard cap exposed by this adapter. Exact overrun is recorded.','GPU queue wait excluded; final grading outside agent budget.'],'public_sha256':hashlib.sha256((BASE/'outputs/c8673-v4-public.zip').read_bytes()).hexdigest()})
    print('BATCH_DIR',OUT,flush=True)
    base=grade({k:INITIAL[k]for k in NAMES},f'codex61m_{stamp}_baseline',900,final=True);dump(OUT/'baseline.json',base);print('BASELINE',json.dumps(base),flush=True)
    if not base.get('correct'):raise RuntimeError('baseline correctness failed; no agents started')
    results=[]
    for rnd in [1,2]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
            fs=[pool.submit(episode,OUT/f'round{rnd}'/arm,arm,rnd,stamp)for arm in PROMPTS]
            rs=[f.result()for f in fs]
        dump(OUT/f'round{rnd}'/'summary.json',rs);results.extend(rs)
    dump(OUT/'completed.json',{'completed':True,'results':results});print('BATCH_COMPLETED',OUT,flush=True)
