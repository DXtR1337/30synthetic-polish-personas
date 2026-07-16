# -*- coding: utf-8 -*-
"""
Run synthetic personas on Azure OpenAI GPT-5.5 with FULL TCTM-57 vignettes.
Same model + Azure config as run_gpt55.py, only difference: sends all 57 items
(22 TCTM-22 + 35 extra) so we can analyze the 35 outside-TCTM-22 items.

Output alias 'gpt55full57' — kept separate from gpt55 (TCTM-22) outputs.
"""
import json, os, sys, re, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / 'out'
OUT_DIR.mkdir(exist_ok=True)

# Load .env.local
env_path = SCRIPT_DIR / '../../../../.env.local'
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(SCRIPT_DIR))
import run_synthetic
from run_synthetic import build_system_prompt, build_user_prompt, load_tctm_vignettes

# Enable full TCTM-57 (default in run_synthetic is False = TCTM-22 only)
run_synthetic.LOAD_ALL_VIGNETTES = True

# Azure config — same GPT-5.5 deployment as run_gpt55.py
AZURE_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://synthetic-benchmark.openai.azure.com/')
AZURE_KEY = os.environ.get('AZURE_OPENAI_KEY', '')
AZURE_DEPLOYMENT = os.environ.get('AZURE_OPENAI_DEPLOYMENT_GPT55', 'gpt-5.5')
AZURE_API_VERSION = '2024-10-21'
MAX_COMPLETION_TOKENS = 24000  # higher cap — 57 items = ~2.5x more output


def run_persona_full57(persona_id):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    model_alias = 'gpt55full57'

    bio_path = SCRIPT_DIR / f'{persona_id}.md'
    bio_raw = bio_path.read_text(encoding='utf-8')
    if bio_raw.startswith('---\n'):
        parts = bio_raw.split('\n---\n', 1)
        frontmatter_raw = parts[0][4:]
        if len(parts) != 2:
            raise ValueError(
                f'{persona_id}: malformed persona front matter (missing closing ---); '
                'refusing to build a prompt that could leak researcher metadata'
            )
        bio_body = parts[1]
    else:
        frontmatter_raw = ''
        bio_body = bio_raw

    persona_version = 1
    for line in frontmatter_raw.splitlines():
        m = re.match(r'persona_version:\s*(\d+)', line.strip())
        if m:
            try: persona_version = int(m.group(1))
            except ValueError: pass

    vignettes_dict = load_tctm_vignettes()
    vignettes = list(vignettes_dict.values())
    assert len(vignettes) == 57, f'Expected 57 vignettes, got {len(vignettes)}'

    system_prompt = build_system_prompt(bio_body)
    user_prompt = build_user_prompt(vignettes_dict)

    (OUT_DIR / f'{persona_id}-{model_alias}-{stamp}-system.txt').write_text(system_prompt, encoding='utf-8')
    (OUT_DIR / f'{persona_id}-{model_alias}-{stamp}-user.txt').write_text(user_prompt, encoding='utf-8')

    print(f'[{persona_id}] biografia: {len(bio_body.split())} slow; 57 winiet; calling GPT-5.5...')

    url = f'{AZURE_ENDPOINT.rstrip("/")}/openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version={AZURE_API_VERSION}'
    req_body = json.dumps({
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'max_completion_tokens': MAX_COMPLETION_TOKENS,
    }).encode('utf-8')
    req = urllib.request.Request(url, data=req_body,
        headers={'Content-Type': 'application/json', 'api-key': AZURE_KEY}, method='POST')

    t_start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            resp_body = resp.read()
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
        raise RuntimeError(f'Azure HTTP {e.code}: {err_body[:500]}') from e

    response = json.loads(resp_body)
    elapsed = time.time() - t_start
    usage = response.get('usage', {})
    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)
    finish_reason = response['choices'][0].get('finish_reason', '?')
    raw_response = response['choices'][0]['message']['content']

    print(f'[{persona_id}] done in {elapsed:.1f}s, in={input_tokens} out={output_tokens}, stop={finish_reason}')
    (OUT_DIR / f'{persona_id}-{model_alias}-{stamp}-raw.txt').write_text(raw_response, encoding='utf-8')

    json_match = re.search(r'\{[\s\S]*\}', raw_response)
    if not json_match:
        raise RuntimeError(f'No JSON in response')
    agent_answers = json.loads(json_match.group(0))

    # Score TCTM (57 items)
    NOW_ISO = datetime.now(timezone.utc).isoformat()
    respondent_id = f'synthetic-{persona_id}-{model_alias}-v{persona_version}-{stamp}'
    tctm_answers_raw = agent_answers.get('tctm', [])
    LETTER_TO_IDX = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    tctm_answers = []
    masc = {'correct': 0, 'DOS': 0, 'NAD': 0, 'BK': 0, 'unknown': 0}
    raw_scores = {'subtext': 0, 'court': 0, 'eks': 0, 'pursuit': 0, 'repair': 0}

    for ans in tctm_answers_raw:
        iid = ans.get('id', '')
        letter = ans.get('answer', '').strip().upper()
        ci = LETTER_TO_IDX.get(letter, -1)
        vig = next((v for v in vignettes if v['id'] == iid), None)
        if not vig:
            continue
        ok = (ci == vig['correctAnswer'])
        mt = vig.get('mascTypes', [])
        cm = mt[ci] if 0 <= ci < len(mt) else 'unknown'
        if ok:
            masc['correct'] += 1
            sub = vig.get('subscale', '')
            if sub in raw_scores:
                raw_scores[sub] += 1
        elif cm in masc:
            masc[cm] += 1
        else:
            masc['unknown'] += 1
        tctm_answers.append({
            'itemId': iid, 'chosenOptionIndex': ci,
            'chosenMascType': cm if not ok else 'correct',
            'isCorrect': ok, 'responseTimeMs': 0, 'changedAnswer': False,
            'presentationOrder': len(tctm_answers) + 1,
        })

    def parse_likert(key, prefix, n):
        raw = agent_answers.get(key, {})
        return {f'{prefix}-{int(k):02d}': int(v) for k, v in raw.items() if str(k).isdigit()}

    payload = {
        'respondentId': respondent_id, 'startedAt': NOW_ISO, 'completedAt': NOW_ISO,
        'consented': True, 'consentTimestamp': NOW_ISO, 'totalDurationMs': 0, 'synthetic': True,
        'demographics': {'age': 0, 'gender': 'synthetic', 'education': 'synthetic',
                         'psychologyBackground': 'no', 'socialCompetenceSelf': 0},
        'tctm': {'answers': tctm_answers, 'mascProfile': masc, 'rawScores': raw_scores, 'durationMs': 0},
        'ecrR': {'answers': parse_likert('ecrr', 'ecrr', 36), 'durationMs': 0},
        'ments': {'answers': parse_likert('ments', 'ments', 28), 'durationMs': 0},
        'kpp': {'answers': parse_likert('kpp', 'kpp', 36), 'durationMs': 0},
        'tipiPl': {'answers': parse_likert('tipi', 'tipi', 10), 'durationMs': 0},
        'feedback': agent_answers.get('feedback', {}),
    }

    result = {
        'persona_id': persona_id, 'persona_version': persona_version,
        'biography_length': len(bio_body.split()), 'model_name': response.get('model', AZURE_DEPLOYMENT),
        'model_stop_reason': finish_reason, 'tokens_input': input_tokens, 'tokens_output': output_tokens,
        'elapsed_seconds': round(elapsed, 2), 'respondent_id': respondent_id, 'payload': payload,
    }

    out_path = OUT_DIR / f'{persona_id}-{model_alias}-{stamp}.json'
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[{persona_id}] saved: {out_path.name}; TCTM-57: {masc["correct"]}/{len(tctm_answers)} correct')
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python run_gpt55_full57.py <persona_id>')
        sys.exit(1)
    run_persona_full57(sys.argv[1])
