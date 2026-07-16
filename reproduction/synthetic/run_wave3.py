# -*- coding: utf-8 -*-
"""
Wave 3 test runner: 4 modele Azure × (30×2 persona + 10 baseline + 6 zero-prompt).

Cel: TEST WEWNĘTRZNY — ile się różnią wyniki po fix parsera v3 + fix w22 stimulus.
Outputs trafiają do out/ z timestampem 20260531+, NIE nadpisują wave 2,
NIE są appendowane do all_data.csv.

Modele:
  - gpt54mini  → Azure OpenAI Chat (run_azure.run_persona_azure)
  - gpt55      → Azure OpenAI Chat (run_gpt55.run_persona_gpt55)
  - grok4      → Azure direct Chat (run_grok.run_persona_azure)
  - gpt54f     → Azure AI Foundry Responses (run_gpt54.run_persona)

Użycie:
  python run_wave3.py --smoke               # 1 persona × 4 modele (~4 calls)
  python run_wave3.py --persona <pid>       # 1 persona × 4 modele (zadana)
  python run_wave3.py --baselines [N]       # N baselines × 4 modele (default 1, full=10)
  python run_wave3.py --noprompts [N]       # N noprompts × 4 modele (default 1, full=6)
  python run_wave3.py --full                # 30×2 persona + 10 baseline + 6 noprompt × 4 modele = 304 calls
"""
import json, os, re, sys, time, traceback
import urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / 'out'
OUT_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(SCRIPT_DIR))

# Załaduj .env.local (4 levels up: synthetic → magisterka → paper → docs → root)
ROOT = SCRIPT_DIR.parent.parent.parent.parent
env_path = ROOT / '.env.local'
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from run_synthetic import build_user_prompt, load_tctm_vignettes
from run_azure import run_persona_azure as run_persona_54mini
from run_gpt55 import run_persona_gpt55
from run_grok import run_persona_azure as run_persona_grok
from run_gpt54 import (
    run_persona as run_persona_54full,
    call_foundry_gpt54,
    score_payload,
    build_result,
    SYSTEM_BASELINE,
)

PERSONAS = [
    'adrian', 'agata', 'ania', 'anna-sim', 'bartek', 'dominika',
    'ewa', 'filip', 'gabriela', 'hubert', 'jakub', 'jola',
    'kamil', 'kasia', 'klaudia', 'kuba', 'lukasz', 'magda',
    'marek', 'michal-k', 'michal-sim', 'natalia', 'ola', 'pawel',
    'piotr', 'radek', 'sara', 'tomek', 'weronika', 'zuzia',
]

PERSONA_FNS = {
    'gpt54mini': run_persona_54mini,
    'gpt55': run_persona_gpt55,
    'grok4': run_persona_grok,
    'gpt54f': run_persona_54full,
}

# ═══════════════════════════════════════════════════════════════
# Niskopoziomowe Chat Completions callery (dla baseline + noprompt)
# Każdy model ma swój endpoint + key + (deployment vs direct).
# ═══════════════════════════════════════════════════════════════
def call_azure_chat(url, key, system_prompt, user_prompt, model_field=None):
    """Generic Azure Chat Completions call. Zwraca (text, in_tok, out_tok, model_name, finish)."""
    msgs = []
    if system_prompt:
        msgs.append({'role': 'system', 'content': system_prompt})
    msgs.append({'role': 'user', 'content': user_prompt})
    body_dict = {
        'messages': msgs,
        'max_completion_tokens': 16000,
        'temperature': 1.0,
        'top_p': 1.0,
        'seed': 20260528,
        'reasoning_effort': 'medium',
    }
    if model_field:
        body_dict['model'] = model_field
    body = json.dumps(body_dict).encode('utf-8')
    req = urllib.request.Request(
        url, data=body,
        headers={'Content-Type': 'application/json', 'api-key': key},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            r = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
        raise RuntimeError(f'HTTP {e.code}: {err[:500]}') from e
    text = r['choices'][0]['message']['content']
    usage = r.get('usage', {})
    finish = r['choices'][0].get('finish_reason', '?')
    return text, usage.get('prompt_tokens', 0), usage.get('completion_tokens', 0), r.get('model', model_field or 'unknown'), finish

def caller_54mini(system_prompt, user_prompt):
    endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://synthetic-benchmark.openai.azure.com/').rstrip('/')
    url = f'{endpoint}/openai/deployments/gpt-5.4-mini/chat/completions?api-version=2024-10-21'
    return call_azure_chat(url, os.environ['AZURE_OPENAI_KEY'], system_prompt, user_prompt)

def caller_55(system_prompt, user_prompt):
    endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://synthetic-benchmark.openai.azure.com/').rstrip('/')
    deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT_GPT55', 'gpt-5.5')
    url = f'{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-10-21'
    return call_azure_chat(url, os.environ['AZURE_OPENAI_KEY'], system_prompt, user_prompt)

def caller_grok(system_prompt, user_prompt):
    url = 'https://michalseido-0654-resource.openai.azure.com/openai/v1/chat/completions'
    return call_azure_chat(url, os.environ['AZURE_GROK_KEY'], system_prompt, user_prompt, model_field='grok-4-20-reasoning')

def caller_54full(system_prompt, user_prompt):
    return call_foundry_gpt54(system_prompt, user_prompt)

CALLERS = {
    'gpt54mini': caller_54mini,
    'gpt55': caller_55,
    'grok4': caller_grok,
    'gpt54f': caller_54full,
}

# ═══════════════════════════════════════════════════════════════
# Baseline + Noprompt orchestration (reuse score_payload + build_result)
# ═══════════════════════════════════════════════════════════════
def run_condition_once(model_alias, condition):
    """condition ∈ {'baseline', 'noprompt'}."""
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    tag = f'{condition}-{model_alias}'
    vignettes_dict = load_tctm_vignettes()
    vignettes = list(vignettes_dict.values())
    user_prompt = build_user_prompt(vignettes_dict)
    system_prompt = SYSTEM_BASELINE if condition == 'baseline' else ''

    (OUT_DIR / f'{tag}-{stamp}-system.txt').write_text(system_prompt or '(empty)', encoding='utf-8')
    (OUT_DIR / f'{tag}-{stamp}-user.txt').write_text(user_prompt, encoding='utf-8')

    print(f'[{tag}] calling...')
    t0 = time.time()
    text, in_tok, out_tok, model_name, finish = CALLERS[model_alias](system_prompt, user_prompt)
    elapsed = time.time() - t0
    print(f'[{tag}] {elapsed:.1f}s, in={in_tok} out={out_tok}, stop={finish}')

    (OUT_DIR / f'{tag}-{stamp}-raw.txt').write_text(text, encoding='utf-8')
    m = re.search(r'\{[\s\S]*\}', text)
    if not m:
        raise RuntimeError(f'No JSON in response: {text[:200]}')
    agent = json.loads(m.group(0))
    scored = score_payload(agent, vignettes)
    respondent_id = f'{tag}-{stamp}'
    result = build_result(condition, 0, 0, model_name, finish, in_tok, out_tok, elapsed,
                          respondent_id, scored, 'ai')
    (OUT_DIR / f'{tag}-{stamp}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[{tag}] MASC: {scored["masc_profile"]}  raw: {scored["raw_scores"]}')
    return result

# ═══════════════════════════════════════════════════════════════
# Wrapper command handlers
# ═══════════════════════════════════════════════════════════════
def smoke(persona='adrian'):
    print(f'\n========== SMOKE TEST: {persona} × 4 modele ==========')
    for ma, fn in PERSONA_FNS.items():
        print(f'\n--- {ma} {persona} ---')
        try:
            fn(persona)
        except Exception as e:
            print(f'ERROR [{ma}]: {e}')
            traceback.print_exc()
        time.sleep(2)

def baselines(n=10):
    print(f'\n========== BASELINES: N={n} × 4 modele ==========')
    for ma in PERSONA_FNS:
        for i in range(n):
            print(f'\n--- baseline {ma} #{i+1}/{n} ---')
            try:
                run_condition_once(ma, 'baseline')
            except Exception as e:
                print(f'ERROR [{ma} baseline #{i+1}]: {e}')
            time.sleep(2)

def noprompts(n=6):
    print(f'\n========== NOPROMPTS: N={n} × 4 modele ==========')
    for ma in PERSONA_FNS:
        for i in range(n):
            print(f'\n--- noprompt {ma} #{i+1}/{n} ---')
            try:
                run_condition_once(ma, 'noprompt')
            except Exception as e:
                print(f'ERROR [{ma} noprompt #{i+1}]: {e}')
            time.sleep(2)

def all_personas():
    print(f'\n========== PERSONAS: 30 × 2 runs × 4 modele = 240 calls ==========')
    for run_idx in [1, 2]:
        for ma, fn in PERSONA_FNS.items():
            for i, p in enumerate(PERSONAS, 1):
                print(f'\n--- [{i}/30] {ma} {p} (run {run_idx}) ---')
                try:
                    fn(p)
                except Exception as e:
                    print(f'ERROR [{ma} {p} run{run_idx}]: {e}')
                time.sleep(2)

def full():
    all_personas()
    baselines(10)
    noprompts(6)

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if args[0] == '--smoke':
        smoke(args[1] if len(args) > 1 else 'adrian')
    elif args[0] == '--persona':
        smoke(args[1] if len(args) > 1 else 'adrian')
    elif args[0] == '--baselines':
        baselines(int(args[1]) if len(args) > 1 else 1)
    elif args[0] == '--noprompts':
        noprompts(int(args[1]) if len(args) > 1 else 1)
    elif args[0] == '--all-personas':
        all_personas()
    elif args[0] == '--full':
        full()
    else:
        print(__doc__)
        sys.exit(1)
