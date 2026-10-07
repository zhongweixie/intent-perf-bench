"""700s/48-response isolated Codex rerun with bounded transport and shutdown."""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import time
import zipfile

from c8673_codex_assets import BASE, NAMES, SYSTEM, TOOLS
from c8673_codex_rpc import RPC

BUDGET = 700
RESPONSE_LIMIT = 48
OUTPUT_LIMIT = 40000
TOTAL_LIMIT = 1250000
QUEUE_LIMIT = 1800
SHUTDOWN_GRACE = 8
BRIDGE = os.environ.get('IPB_GRADE_BRIDGE','')
GRADER_HOST = os.environ.get('IPB_GRADER_HOST','songcpu4')


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')
    os.replace(temp, path)


class Clock:
    def __init__(self, now=time.monotonic):
        self.now = now
        self.start = now()
        self.paused = 0.0
        self.since = None
        self.lock = threading.Lock()

    def pause(self):
        with self.lock:
            if self.since is None:
                self.since = self.now()

    def resume(self):
        with self.lock:
            if self.since is not None:
                self.paused += self.now() - self.since
                self.since = None

    def queue_seconds(self):
        with self.lock:
            return self.paused + (self.now() - self.since if self.since is not None else 0)

    def elapsed(self):
        return self.now() - self.start - self.queue_seconds()


def stop_reason(clock, state):
    if clock.elapsed() >= BUDGET:
        return 'time_limit'
    if state['model_responses'] >= RESPONSE_LIMIT:
        return 'model_response_limit'
    if state['generated_tokens'] >= OUTPUT_LIMIT:
        return 'generated_token_limit'
    if state['generated_tokens'] + state['prompt_tokens'] >= TOTAL_LIMIT:
        return 'total_token_limit'
    if clock.queue_seconds() >= QUEUE_LIMIT:
        return 'infrastructure_queue_limit'
    return None


def update_usage(state, total):
    # Notifications can repeat. A repeated cumulative total is not another response.
    signature = tuple(total.get(k, 0) for k in ('inputTokens', 'outputTokens', 'reasoningOutputTokens', 'totalTokens'))
    if signature == state.get('_last_usage') or not any(signature):
        return False
    state['_last_usage'] = signature
    state['generated_tokens'] = max(state['generated_tokens'], total['outputTokens'])
    state['prompt_tokens'] = max(state['prompt_tokens'], total['inputTokens'])
    state['reasoning_output_tokens'] = total.get('reasoningOutputTokens', 0)
    state['model_responses'] += 1
    return True


def _grade_once(request, clock, cancel, deadline, process_factory=subprocess.Popen):
    command = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
               '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
               GRADER_HOST, 'python3 ' + __import__('shlex').quote(BRIDGE)]
    process = process_factory(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding='utf8')
    messages = queue.Queue()
    errors = []

    def write():
        try:
            process.stdin.write(json.dumps(request))
            process.stdin.close()
        except (BrokenPipeError, OSError) as exc:
            messages.put(('error', str(exc)))

    def read():
        try:
            for line in process.stdout:
                messages.put(('line', line))
        finally:
            messages.put(('eof', None))

    def read_errors():
        errors.append(process.stderr.read()[-2000:])

    for fn in (write, read, read_errors):
        threading.Thread(target=fn, daemon=True).start()
    started = time.monotonic()
    try:
        while True:
            if cancel.is_set():
                raise InterruptedError('evaluation cancelled at solver cutoff')
            if clock and clock.elapsed() >= deadline:
                raise InterruptedError('evaluation reached solver cutoff')
            if time.monotonic() - started > request['timeout'] + QUEUE_LIMIT + 30:
                raise TimeoutError('evaluation transport/queue watchdog exceeded')
            if clock and clock.queue_seconds() > QUEUE_LIMIT:
                raise TimeoutError('GPU queue watchdog exceeded')
            try:
                kind, payload = messages.get(timeout=0.1)
            except queue.Empty:
                continue
            if kind == 'error':
                raise ConnectionError(payload)
            if kind == 'eof':
                raise ConnectionError('SSH closed before evaluator result: ' + ''.join(errors))
            item = json.loads(payload)
            if item['kind'] == 'queue_start' and clock:
                clock.pause()
            elif item['kind'] == 'queue_end' and clock:
                clock.resume()
            elif item['kind'] == 'result':
                return item['result']
    finally:
        # Always pair a queue-start, including cancellation or SSH disconnect.
        if clock:
            clock.resume()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)


def grade(files, namespace, timeout=900, final=False, clock=None, cancel=None, retries=2, record=None):
    cancel = cancel or threading.Event()
    # The frozen request/namespace is identical on retries: remote jobs are cached.
    workspace = re.sub(r'_(?:b[0-9]+|final)$', '', namespace)
    request = {'files': files, 'namespace': namespace, 'workspace_namespace': workspace,
               'timeout': max(1, timeout), 'final': final}
    errors = []
    for attempt in range(retries + 1):
        if cancel.is_set() or (clock and clock.elapsed() >= BUDGET):
            raise InterruptedError('no retries after solver cutoff')
        try:
            return _grade_once(request, clock, cancel, BUDGET)
        except InterruptedError:
            raise
        except (ConnectionError, OSError, ValueError, TimeoutError) as exc:
            detail = {'attempt': attempt + 1, 'error': str(exc), 'namespace': namespace}
            errors.append(detail)
            if record:
                record('evaluation_transport_error', **detail)
            if attempt == retries:
                raise RuntimeError('evaluator infrastructure failure: ' + json.dumps(errors)) from exc
            cancel.wait(min(2 ** attempt, 4))


class SafeRPC(RPC):
    def send(self, value):
        if self.p.poll() is not None:
            raise ConnectionError('Codex app-server exited')
        try:
            super().send(value)
        except (BrokenPipeError, OSError) as exc:
            raise ConnectionError('Codex app-server pipe closed') from exc

    def close(self):
        try:
            dump(self.folder / 'events.json', self.events)
        finally:
            if self.p.poll() is None:
                self.p.terminate()
                try:
                    self.p.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.p.kill()
                    self.p.wait(timeout=2)


def episode(out, arm, number, stamp, initial, common, prompt_text, rpc_factory=SafeRPC):
    out.mkdir(parents=True)
    public = out / 'public'
    public.mkdir()
    for name, text in initial.items():
        (public / name).write_text(text, encoding='utf8')
    clock = Clock()
    cancel = threading.Event()
    source_lock = threading.RLock()
    event_lock = threading.Lock()
    state = dict(model='gpt-6.1-sol', reasoning_effort='medium', condition=arm,
        round=number, generated_tokens=0, prompt_tokens=0, model_responses=0,
        usage_notifications=0, tool_actions=0, stop_reason=None, transport_errors=[],
        benchmarks=[], infrastructure_affected=False,
        isolation='environments=[]; only dynamic public tools; native shell/apps/web disabled')
    rpc = None
    pending = []
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    frozen = None

    def files():
        with source_lock:
            return {name: (public / name).read_text(encoding='utf8') for name in sorted(NAMES)}

    def checkpoint():
        snapshot = files()
        digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        dump(out / 'snapshots' / (digest + '.json'), snapshot)
        return digest

    def event(kind, **detail):
        with event_lock:
            with (out / 'events.jsonl').open('a', encoding='utf8') as stream:
                stream.write(json.dumps(dict(kind=kind, elapsed_seconds=clock.elapsed(), **detail), ensure_ascii=False) + '\n')

    def notice():
        return (f"Budget remaining: {max(0, int(BUDGET-clock.elapsed()))} seconds; "
                f"{max(0, OUTPUT_LIMIT-state['generated_tokens'])} generated tokens; "
                f"{max(0, RESPONSE_LIMIT-state['model_responses'])} model responses. "
                'Save and validate within these limits. The last saved code is the submission.')

    def allowed(name, write=False):
        if name not in initial or (write and name not in NAMES):
            raise ValueError('Only public file aliases are accessible')
        return public / name

    def execute(name, args):
        if cancel.is_set() or stop_reason(clock, state):
            raise InterruptedError('budget ended; no tool action or source write permitted')
        if name == 'list_files':
            return '\n'.join(sorted(initial))
        if name == 'read_file':
            lines = allowed(args['path']).read_text(encoding='utf8').splitlines()
            lo = max(1, int(args.get('start_line', 1)))
            hi = min(lo + 499, int(args.get('end_line', lo + 299)))
            return '\n'.join(f'{i+1}: {text}' for i, text in enumerate(lines) if lo <= i+1 <= hi)
        if name == 'search_text':
            names = sorted(initial) if args.get('path', '') in ('', '.') else [allowed(args['path']).name]
            found = [f'{key}:{i+1}: {line}' for key in names
                for i, line in enumerate(allowed(key).read_text(encoding='utf8').splitlines()) if args['query'] in line]
            return '\n'.join(found[:min(100, int(args.get('max_results', 40)))]) or 'No matches'
        if name in ('write_file', 'replace_text'):
            with source_lock:
                path = allowed(args['path'], True)
                old = path.read_text(encoding='utf8')
                if name == 'replace_text':
                    if not args['old'] or old.count(args['old']) != 1:
                        raise ValueError('old text must occur exactly once')
                    new = old.replace(args['old'], args['new'], 1)
                else:
                    new = args['content']
                if len(new) + sum(len(v) for k, v in files().items() if k != path.name) > 400000:
                    raise ValueError('source too large')
                if cancel.is_set() or stop_reason(clock, state):
                    raise InterruptedError('deadline reached; source not saved')
                path.write_text(new, encoding='utf8')
                return 'Saved ' + checkpoint()
        if name == 'run_benchmark':
            checkpoint()
            remaining = BUDGET - clock.elapsed()
            if remaining < 8:
                return 'Insufficient wall time to start evaluation. Saved code will be graded.'
            index = len(state['benchmarks']) + 1
            try:
                result = grade(files(), f'codex61m_{stamp}_r{number}_{arm}_b{index}', remaining,
                    clock=clock, cancel=cancel, record=event)
            except InterruptedError:
                raise
            except Exception:
                state['infrastructure_affected'] = True
                raise
            state['benchmarks'].append(dict(elapsed_seconds=clock.elapsed(), **result))
            dump(out / 'benchmarks.json', state['benchmarks'])
            return json.dumps(result)
        raise ValueError('unknown tool')

    def freeze(reason):
        nonlocal frozen
        with source_lock:
            cancel.set()
            state['stop_reason'] = state['stop_reason'] or reason
            if reason.startswith('infrastructure'):
                state['infrastructure_affected'] = True
            if frozen is None:
                frozen = files()
                state['cutoff_agent_seconds'] = clock.elapsed()
                state['submission_sha256'] = checkpoint()
                dump(out / 'frozen_submission.json', frozen)
                event('submission_frozen', reason=reason, sha256=state['submission_sha256'])

    try:
        rpc = rpc_factory(out / 'session')
        rpc.start(TOOLS, SYSTEM)
        state['thread_id'] = rpc.thread
        clock = Clock()
        prompt = common + '\n\nBackground note:\n' + prompt_text + '\n\n' + notice()
        dump(out / 'prompt_snapshot.json', {'system': SYSTEM, 'prompt': prompt, 'tools': TOOLS})
        checkpoint()
        rpc.turn(prompt)
        event('started', thread=rpc.thread)
        print('STARTED', number, arm, rpc.thread, flush=True)
        last_tick = time.monotonic()
        last_status = 0
        interrupted_at = None
        while True:
            now = time.monotonic()
            if now - last_tick > 15 and interrupted_at is None:
                state['infrastructure_error'] = 'local controller paused/suspended for more than 15s'
                freeze('infrastructure_local_suspend')
            last_tick = now
            reason = state['stop_reason'] if cancel.is_set() else stop_reason(clock, state)
            if reason and interrupted_at is None:
                freeze(reason)
                interrupted_at = now
                rpc.n += 1
                try:
                    rpc.send({'id': rpc.n, 'method': 'turn/interrupt',
                        'params': {'threadId': rpc.thread, 'turnId': rpc.turnid}})
                except ConnectionError as exc:
                    state['shutdown_error'] = str(exc)
                event('interrupt', reason=reason)
            if interrupted_at is not None and now - interrupted_at >= SHUTDOWN_GRACE:
                state['forced_shutdown'] = True
                break
            for item in pending[:]:
                request, future = item
                if not future.done():
                    continue
                pending.remove(item)
                try:
                    content, success = future.result(), True
                except Exception as exc:
                    content, success = str(exc), False
                event('tool_result', tool=request['params']['tool'], success=success, content=content)
                if interrupted_at is None:
                    rpc.send({'id': request['id'], 'result': {'contentItems': [
                        {'type': 'inputText', 'text': content + '\n\n' + notice()}], 'success': success}})
            try:
                message = rpc.next(0.1)
            except queue.Empty:
                if rpc.p.poll() is not None:
                    raise ConnectionError('Codex app-server exited')
                continue
            method = message.get('method', '')
            if method == 'item/tool/call':
                name = message['params']['tool']
                if name not in {tool['name'] for tool in TOOLS}:
                    raise RuntimeError('isolation violation: ' + name)
                state['tool_actions'] += 1
                event('tool_call', tool=name, arguments=message['params']['arguments'])
                if interrupted_at is None:
                    pending.append((message, pool.submit(execute, name, message['params']['arguments'])))
            elif 'id' in message and method:
                event('unexpected_server_request', method=method)
                if interrupted_at is None:
                    rpc.send({'id': message['id'], 'error': {'code': -32000, 'message': 'Not available in isolated experiment'}})
            elif method == 'thread/tokenUsage/updated':
                state['usage_notifications'] += 1
                usage = message['params']['tokenUsage']['total']
                counted = update_usage(state, usage)
                event('usage', usage=usage, counted_as_response=counted)
            elif method == 'error':
                state['transport_errors'].append(message['params'])
                event('api_error', error=message['params'])
                # Native retries stay within the same solver budget/context.
                if not message['params'].get('willRetry', False):
                    freeze('infrastructure_model_transport')
            elif method == 'item/completed':
                item = message['params']['item']
                if item.get('type') == 'agentMessage':
                    event('agent_message', text=item.get('text'), phase=item.get('phase'))
                if item.get('type') in ('commandExecution', 'fileChange', 'mcpToolCall'):
                    raise RuntimeError('unexpected native tool: ' + item['type'])
            elif method == 'turn/completed':
                state['turn_status'] = message['params']['turn']['status']
                state['turn_error'] = message['params']['turn'].get('error')
                reason = 'infrastructure_model_transport' if state['turn_status'] == 'failed' else state['turn_status']
                freeze(reason)
                break
            elif message.get('eof'):
                raise ConnectionError('Codex app-server EOF')
            if now - last_status >= 1:
                state['agent_seconds'] = clock.elapsed()
                dump(out / 'status.json', state)
                last_status = now
    except Exception as exc:
        state['infrastructure_error'] = str(exc)
        state['infrastructure_affected'] = True
        freeze('infrastructure_error')
        print('EPISODE_ERROR', number, arm, str(exc), flush=True)
    finally:
        if frozen is None:
            freeze('infrastructure_controller_exit')
        if rpc:
            try:
                rpc.close()
            except Exception as exc:
                state['shutdown_error'] = str(exc)
        # Cancellation stops the evaluator attachment and prohibits queued writes.
        pool.shutdown(wait=True, cancel_futures=True)
        clock.resume()
        state['agent_seconds'] = state['cutoff_agent_seconds']
        state['shutdown_elapsed_seconds'] = clock.elapsed()
        state['gpu_queue_wait_seconds'] = clock.queue_seconds()
        state['real_wall_seconds'] = time.monotonic() - clock.start
        state.pop('_last_usage', None)
        dump(out / 'status.json', state)
    assert files() == frozen, 'source changed after freeze'
    try:
        final = grade(frozen, f'codex61m_{stamp}_r{number}_{arm}_final', final=True, record=event)
    except Exception as exc:
        final = {'correct': None, 'infrastructure_error': str(exc)}
        state['infrastructure_affected'] = True
        dump(out / 'status.json', state)
    dump(out / 'final_evaluation.json', final)
    print('FINAL', number, arm, json.dumps(final), flush=True)
    return {'condition': arm, 'status': state, 'final_evaluation': final}


def load_task():
    with zipfile.ZipFile(BASE / 'groundtruth/public_snapshot.zip') as archive:
        initial = {Path(name).name: archive.read(name).decode('utf8') for name in archive.namelist() if not name.endswith('/')}
    assert set(initial) == NAMES | {'CONTRACT.md'}
    private = BASE / 'evaluation/runtime/private'
    return initial, (private / 'common.txt').read_text(encoding='utf8'), {
        arm: (private / (arm + '.txt')).read_text(encoding='utf8') for arm in ('fuzzy', 'flatten_hint')}


def main(out):
    initial, common, prompts = load_task()
    stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    out.mkdir(parents=True, exist_ok=False)
    protocol = dict(model='gpt-6.1-sol', reasoning_effort='medium', rounds=2,
        conditions=list(prompts), budget_seconds=BUDGET, model_response_guard=RESPONSE_LIMIT,
        generated_token_guard=OUTPUT_LIMIT, total_token_guard=TOTAL_LIMIT,
        max_queue_wait_seconds=QUEUE_LIMIT,
        response_counting='distinct cumulative token-usage updates; deduplicate identical notifications; not provider HTTP attempts',
        controller='700s-fixed-v2', controller_host='local Windows',
        notes=['Local PC must remain awake and connected; full shutdown cannot be survived.',
               'GPU queue excluded; native model retries and SSH reconnect overhead charged.',
               'Frozen source at cutoff; interrupt grace 8s; no additional solver turn.',
               'SSH reattachment reuses the same detached evaluator job/result.',
               'Infrastructure-affected episodes flagged, never converted to wrong-answer scores.'],
        public_sha256=hashlib.sha256((BASE / 'groundtruth/public_snapshot.zip').read_bytes()).hexdigest(),
        controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        prompt_sha256={arm: hashlib.sha256((common+'\n\nBackground note:\n'+text).encode()).hexdigest() for arm, text in prompts.items()})
    dump(out / 'protocol.json', protocol)
    print('BATCH_DIR', out, flush=True)
    try:
        base = grade({name: initial[name] for name in NAMES}, f'codex61m_{stamp}_baseline', final=True)
        dump(out / 'baseline.json', base)
        if not base.get('correct'):
            raise RuntimeError('baseline validation failed')
        # Caller-only reference benchmark; the solver never receives these files/results.
        reference = json.loads((BASE / 'groundtruth/reference.json').read_text(encoding='utf-8-sig'))
        if set(reference) != NAMES:
            raise RuntimeError('reference source alias mismatch')
        ref = grade(reference, f'codex61m_{stamp}_reference', final=True)
        dump(out / 'reference_evaluation.json', ref)
        if not ref.get('correct'):
            raise RuntimeError('reference validation failed')
        print('PREFLIGHT_PASS', base['latency_ms'], ref['latency_ms'], flush=True)
        results = []
        for number in (1, 2):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(episode, out / f'round{number}' / arm, arm, number, stamp, initial, common, text) for arm, text in prompts.items()]
                entries = [future.result() for future in futures]
            dump(out / f'round{number}' / 'summary.json', entries)
            results.extend(entries)
            dump(out / 'batch_status.json', {'finished_rounds': number, 'results': results})
        affected = any(entry['status']['infrastructure_affected'] for entry in results)
        dump(out / 'completed.json', {'completed': True, 'clean_batch': not affected, 'results': results})
        print('BATCH_COMPLETED', out, 'clean=', not affected, flush=True)
    except Exception as exc:
        dump(out / 'failed.json', {'infrastructure_error': str(exc)})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not BRIDGE:parser.error('Set IPB_GRADE_BRIDGE to the absolute path of scripts/codex/grade_bridge.py on the grading host')
    (BASE/'.state').mkdir(exist_ok=True)
    # Avoid accidental duplicate batches; closing this process releases the OS lock.
    import msvcrt
    with (BASE / '.state/codex.lock').open('a+b') as lock:
        lock.seek(0)
        if not lock.read(1):
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        import ctypes
        # Keep the controller awake while solving; restore on exit. No display setting changes.
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        try:
            main(args.out.resolve())
        finally:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
