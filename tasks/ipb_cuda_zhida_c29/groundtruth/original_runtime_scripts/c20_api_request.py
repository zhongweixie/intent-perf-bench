"""Single direct DeepInfra request in a killable child process; never print a credential."""
import json, os, re, sys, urllib.error, urllib.request

def secret():
    value = os.environ.get('DEEPINFRA_API_KEY')
    if not value:
        raise RuntimeError('Remote API key not in current environment')
    return value.strip()

def main():
    key = secret()
    payload = json.load(sys.stdin)
    req = urllib.request.Request(
        'https://api.deepinfra.com/v1/openai/chat/completions',
        data=json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=360) as response:
            result = {'ok': True, 'reply': json.load(response)}
    except urllib.error.HTTPError as exc:
        raw = exc.read(4000).decode('utf-8', 'replace').replace(key, '[REDACTED]')
        raw = re.sub(r'sk-[A-Za-z0-9_-]+', '[REDACTED]', raw)
        headers = {k: v for k, v in exc.headers.items() if k.lower() in ['cf-ray', 'x-request-id', 'retry-after', 'content-type', 'server', 'date']}
        result = {'ok': False, 'kind': 'http', 'status': exc.code, 'response_excerpt': raw, 'headers': headers}
    except (TimeoutError, OSError) as exc:
        result = {'ok': False, 'kind': 'transport', 'error': type(exc).__name__}
    # ASCII-only JSON is invariant across Windows console code pages.
    sys.stdout.write(json.dumps(result, ensure_ascii=True))

if __name__ == '__main__':
    main()
