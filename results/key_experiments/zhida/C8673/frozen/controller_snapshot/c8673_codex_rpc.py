import json, subprocess, threading, queue, time, pathlib, os
CODEX = r'C:\Users\zhida\AppData\Local\OpenAI\Codex\bin\f544b3844e0f14e9\codex.exe'
class RPC:
    def __init__(self, folder):
        self.folder=pathlib.Path(folder).resolve(); self.folder.mkdir(parents=True,exist_ok=True)
        cfg={'features.shell_tool':False,'features.unified_exec':False,'features.shell_snapshot':False,'features.apps':False,'features.browser_use':False,'features.browser_use_external':False,'features.computer_use':False,'features.imagegen':False,'features.multi_agent':False,'features.hooks':False,'features.memory':False,'features.skill_search':False,'features.skill_mcp_dependency_install':False,'features.view_image':False,'features.skip_host_skill_discovery':True,'web_search':'disabled','history.persistence':'none','project_doc_max_bytes':0,'mcp_servers':{},'model_reasoning_effort':'medium'}
        cfg.update({'mcp_servers.node_repl.enabled':False,'mcp_servers.cua_repl.enabled':False,'features.goals':False,'features.code_mode_host':False,'features.code_mode':False,'features.image_generation':False,'features.in_app_browser':False,'memories.generate_memories':False,'memories.use_memories':False})
        cfg.pop('features.memory');cfg.pop('features.imagegen');cfg.pop('mcp_servers')
        cfg['mcp_servers.cua_repl.command']='cmd.exe'
        # The code-mode host is a V8 tool dispatcher, not filesystem/shell access.
        # Native tools remain absent because environments=[] and MCPs are disabled.
        cfg['features.code_mode_host']=True
        args=[CODEX,'app-server','--listen','stdio://']
        for k,v in cfg.items(): args+=['-c',k+'='+json.dumps(v)]
        env={k:v for k,v in os.environ.items()if not k.startswith('CODEX_')}
        self.p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(self.folder/'server-stderr.log').open('w',encoding='utf8'),text=True,encoding='utf8',cwd=self.folder,env=env)
        self.q=queue.Queue(); self.n=0; self.events=[]
        def read():
            for line in self.p.stdout:
                try:self.q.put(json.loads(line))
                except Exception:self.q.put({'raw':line})
            self.q.put({'eof':True})
        threading.Thread(target=read,daemon=True).start()
        self.call('initialize',{'clientInfo':{'name':'ipb_isolated_eval','version':'0.1'},'capabilities':{'experimentalApi':True}})
        self.send({'method':'initialized'})
    def send(self,d): self.p.stdin.write(json.dumps(d,ensure_ascii=False)+'\n'); self.p.stdin.flush()
    def next(self,timeout=1):
        d=self.q.get(timeout=timeout); self.events.append(d); return d
    def call(self,m,p,timeout=60):
        self.n+=1; rid=self.n; self.send({'id':rid,'method':m,'params':p}); end=time.monotonic()+timeout
        while time.monotonic()<end:
            d=self.next(max(0.1,end-time.monotonic()))
            if d.get('id')==rid and 'method' not in d:
                if 'error'in d:raise RuntimeError(d['error'])
                return d['result']
            if d.get('eof'):raise RuntimeError('server exited')
        raise TimeoutError(m)
    def start(self,tools,base):
        r=self.call('thread/start',{'model':'gpt-6.1-sol','allowProviderModelFallback':False,'cwd':str(self.folder),'environments':[],'ephemeral':True,'approvalPolicy':'never','sandbox':'read-only','baseInstructions':base,'dynamicTools':tools,'experimentalRawEvents':True})
        self.thread=r['thread']['id']; return r
    def turn(self,text):
        r=self.call('turn/start',{'threadId':self.thread,'model':'gpt-6.1-sol','effort':'medium','environments':[],'input':[{'type':'text','text':text}]}); self.turnid=r['turn']['id']; return r
    def close(self):
        (self.folder/'events.json').write_text(json.dumps(self.events,ensure_ascii=False),encoding='utf8')
        self.p.terminate()
if __name__=='__main__':
    r=RPC('work/codex-isolation-probe')
    try:
        models=r.call('model/list',{'includeHidden':True,'limit':100})
        print('MODELS',json.dumps([m for m in models['data'] if m['id']=='gpt-6.1-sol']))
        tool={'type':'function','name':'public_probe','description':'Test tool connection.','inputSchema':{'type':'object','properties':{},'additionalProperties':False}}
        s=r.start([tool],'You are an isolated coding agent. Only caller-provided tools are available. No file system or environment access is provided.'); print('START',s['model'],s.get('reasoningEffort'))
        r.turn('Call public_probe, then reply READY. Do not use any other tool.')
        end=time.monotonic()+120
        while time.monotonic()<end:
            try:d=r.next(2)
            except queue.Empty:continue
            m=d.get('method','')
            if m=='item/tool/call':
                print('TOOL',d['params']['tool']); r.send({'id':d['id'],'result':{'contentItems':[{'type':'inputText','text':'CONNECTED'}],'success':True}})
            elif 'id'in d and 'method'in d:
                print('UNEXPECTED_REQUEST',m);r.send({'id':d['id'],'error':{'code':-32000,'message':'Unavailable in isolated experiment'}})
            elif m in ['turn/completed','error','thread/tokenUsage/updated','item/started']:
                print(m,json.dumps(d['params'])[:1200],flush=True)
            if m=='turn/completed':break
    finally:r.close()
