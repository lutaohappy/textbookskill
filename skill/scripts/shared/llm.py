import os, sys, json, urllib.request, urllib.error

API_KEY = (
    os.getenv('LLM_API_KEY')
    or os.getenv('ANTHROPIC_API_KEY')
    or os.getenv('OPENAI_API_KEY')
)

MODEL = os.getenv('LLM_MODEL', 'claude-sonnet-4-20250514')
BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.anthropic.com/v1')

def _is_anthropic():
    return 'anthropic' in BASE_URL.lower()

def call_llm(prompt, system=None, max_tokens=8192, temperature=0.7):
    if not API_KEY:
        print('错误：未找到 API Key。请设置以下环境变量之一：')
        print('  export LLM_API_KEY=sk-xxx        （推荐）')
        print('  export ANTHROPIC_API_KEY=sk-ant-xxx')
        print('  export OPENAI_API_KEY=sk-xxx')
        sys.exit(1)

    is_anthropic = _is_anthropic()

    if is_anthropic:
        body = {
            'model': MODEL,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': [{'role': 'user', 'content': prompt}],
        }
        if system:
            body['system'] = system
        headers = {
            'x-api-key': API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        }
        url = BASE_URL.rstrip('/') + '/messages'
    else:
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        body = {
            'model': MODEL,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': messages,
        }
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'content-type': 'application/json',
        }
        url = BASE_URL.rstrip('/') + '/chat/completions'

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers=headers,
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        print(f'LLM API 错误 ({e.code}): {body}')
        sys.exit(1)
    except Exception as e:
        print(f'请求失败: {e}')
        sys.exit(1)

    if is_anthropic:
        blocks = result.get('content', [])
        return ''.join(b.get('text', '') for b in blocks if b.get('type') == 'text')
    else:
        return result.get('choices', [{}])[0].get('message', {}).get('content', '')
