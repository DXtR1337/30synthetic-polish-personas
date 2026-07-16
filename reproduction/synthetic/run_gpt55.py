# -*- coding: utf-8 -*-
"""
Run synthetic personas on Azure OpenAI (GPT-5.5).
Reuses prompts from run_synthetic.py, swaps Bedrock for Azure.
Shares resource (synthetic-benchmark.openai.azure.com) with gpt-5.4-mini,
different deployment.
"""
import hashlib, json, os, sys, re, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / 'out'
OUT_DIR.mkdir(exist_ok=True)

# Load .env.local from project root (4 levels up: synthetic -> magisterka -> paper -> docs -> root)
env_path = SCRIPT_DIR / '../../../../.env.local'
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8').splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

# Import prompt builders from existing script
sys.path.insert(0, str(SCRIPT_DIR))
from run_synthetic import build_system_prompt, build_user_prompt, load_tctm_vignettes

# Azure config — GPT-5.5 deployment
AZURE_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://synthetic-benchmark.openai.azure.com/')
AZURE_KEY = os.environ.get('AZURE_OPENAI_KEY', '')
AZURE_DEPLOYMENT = os.environ.get('AZURE_OPENAI_DEPLOYMENT_GPT55', 'gpt-5.5')
AZURE_API_VERSION = '2024-10-21'
MAX_COMPLETION_TOKENS = 16000

# Sampling parameters (frozen for v18 reproducibility).
SAMPLING_TEMPERATURE = 1.0
SAMPLING_TOP_P = 1.0
SAMPLING_SEED = 20260528
SAMPLING_REASONING_EFFORT = 'medium'

LOAD_ALL_VIGNETTES = False


def run_persona_gpt55(persona_id):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    model_alias = 'gpt55'

    # 1. Load biography
    bio_path = SCRIPT_DIR / f'{persona_id}.md'
    if not bio_path.exists():
        raise FileNotFoundError(f'Brak biografii: {bio_path}')
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

    bio_word_count = len(bio_body.split())
    print(f'[{persona_id}] biografia: {bio_word_count} slow')

    # 2. Load vignettes
    vignettes_dict = load_tctm_vignettes()
    vignettes = list(vignettes_dict.values())
    label = 'TCTM-22'
    print(f'[{persona_id}] {len(vignettes)} winiet ({label})')

    # 3. Build prompts
    system_prompt = build_system_prompt(bio_body)
    user_prompt = build_user_prompt(vignettes_dict)

    (OUT_DIR / f'{persona_id}-{model_alias}-{stamp}-system.txt').write_text(system_prompt, encoding='utf-8')
    (OUT_DIR / f'{persona_id}-{model_alias}-{stamp}-user.txt').write_text(user_prompt, encoding='utf-8')

    print(f'[{persona_id}] system: {len(system_prompt)} chars, user: {len(user_prompt)} chars')

    # 4. Call Azure OpenAI (GPT-5.5)
    url = f'{AZURE_ENDPOINT.rstrip("/")}/openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version={AZURE_API_VERSION}'

    req_body = json.dumps({
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'max_completion_tokens': MAX_COMPLETION_TOKENS,
        'temperature': SAMPLING_TEMPERATURE,
        'top_p': SAMPLING_TOP_P,
        'seed': SAMPLING_SEED,
        'reasoning_effort': SAMPLING_REASONING_EFFORT,
    }).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=req_body,
        headers={
            'Content-Type': 'application/json',
            'api-key': AZURE_KEY,
        },
        method='POST',
    )

    print(f'[{persona_id}] calling Azure GPT-5.5 (deployment={AZURE_DEPLOYMENT})...')
    t_start = time.time()

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            resp_body = resp.read()
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
        raise RuntimeError(f'Azure HTTP {e.code}: {err_body[:500]}') from e

    response = json.loads(resp_body)
    elapsed = time.time() - t_start

    model_name = response.get('model', AZURE_DEPLOYMENT)
    usage = response.get('usage', {})
    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)
    finish_reason = response['choices'][0].get('finish_reason', '?')
    raw_response = response['choices'][0]['message']['content']

    print(f'[{persona_id}] done in {elapsed:.1f}s, tokens in={input_tokens} out={output_tokens}, stop={finish_reason}')

    (OUT_DIR / f'{persona_id}-{model_alias}-{stamp}-raw.txt').write_text(raw_response, encoding='utf-8')

    # 5. Extract JSON
    json_match = re.search(r'\{[\s\S]*\}', raw_response)
    if not json_match:
        raise RuntimeError(f'No JSON in response: {raw_response[:200]}')
    agent_answers = json.loads(json_match.group(0))

    # 6. Build payload (same shape as run_synthetic.py / run_azure.py)
    NOW_ISO = datetime.now(timezone.utc).isoformat()
    respondent_id = f'synthetic-{persona_id}-{model_alias}-v{persona_version}-{stamp}'

    tctm_answers_raw = agent_answers.get('tctm', [])
    LETTER_TO_IDX = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    tctm_answers = []
    masc_profile = {'correct': 0, 'DOS': 0, 'NAD': 0, 'BK': 0, 'unknown': 0}
    raw_scores = {'subtext': 0, 'court': 0, 'eks': 0, 'pursuit': 0, 'repair': 0}

    for ans in tctm_answers_raw:
        item_id = ans.get('id', '')
        letter = ans.get('answer', '').strip().upper()
        chosen_idx = LETTER_TO_IDX.get(letter, -1)

        vig = next((v for v in vignettes if v['id'] == item_id), None)
        if not vig:
            continue

        is_correct = (chosen_idx == vig['correctAnswer'])
        masc_types = vig.get('mascTypes', [])
        chosen_masc = masc_types[chosen_idx] if 0 <= chosen_idx < len(masc_types) else 'unknown'

        if is_correct:
            masc_profile['correct'] += 1
            sub = vig.get('subscale', '')
            if sub in raw_scores:
                raw_scores[sub] += 1
        elif chosen_masc in masc_profile:
            masc_profile[chosen_masc] += 1
        else:
            masc_profile['unknown'] += 1

        tctm_answers.append({
            'itemId': item_id,
            'chosenOptionIndex': chosen_idx,
            'chosenMascType': chosen_masc if not is_correct else 'correct',
            'isCorrect': is_correct,
            'responseTimeMs': 0,
            'changedAnswer': False,
            'presentationOrder': len(tctm_answers) + 1,
        })

    def parse_likert(key, prefix, n_items):
        raw = agent_answers.get(key, {})
        return {f'{prefix}-{int(k):02d}': int(v) for k, v in raw.items() if str(k).isdigit()}

    ecrr_answers = parse_likert('ecrr', 'ecrr', 36)
    ments_answers = parse_likert('ments', 'ments', 28)
    kpp_answers = parse_likert('kpp', 'kpp', 36)
    tipi_answers = parse_likert('tipi', 'tipi', 10)

    feedback = agent_answers.get('feedback', {})

    payload = {
        'respondentId': respondent_id,
        'startedAt': NOW_ISO,
        'completedAt': NOW_ISO,
        'consented': True,
        'consentTimestamp': NOW_ISO,
        'totalDurationMs': 0,
        'synthetic': True,
        'demographics': {
            'age': 0, 'gender': 'synthetic', 'education': 'synthetic',
            'psychologyBackground': 'no', 'socialCompetenceSelf': 0,
        },
        'tctm': {
            'answers': tctm_answers,
            'mascProfile': masc_profile,
            'rawScores': raw_scores,
            'durationMs': 0,
        },
        'ecrR': {'answers': ecrr_answers, 'durationMs': 0},
        'ments': {'answers': ments_answers, 'durationMs': 0},
        'kpp': {'answers': kpp_answers, 'durationMs': 0},
        'tipiPl': {'answers': tipi_answers, 'durationMs': 0},
        'feedback': feedback,
    }

    biography_sha256 = hashlib.sha256(bio_raw.encode('utf-8')).hexdigest()

    result = {
        'persona_id': persona_id,
        'persona_version': persona_version,
        'biography_length': bio_word_count,
        'biography_sha256': biography_sha256,
        'model_name': model_name,
        'model_stop_reason': finish_reason,
        'tokens_input': input_tokens,
        'tokens_output': output_tokens,
        'elapsed_seconds': round(elapsed, 2),
        'respondent_id': respondent_id,
        'sampling': {
            'temperature': SAMPLING_TEMPERATURE,
            'top_p': SAMPLING_TOP_P,
            'seed': SAMPLING_SEED,
            'reasoning_effort': SAMPLING_REASONING_EFFORT,
            'max_completion_tokens': MAX_COMPLETION_TOKENS,
        },
        'azure_deployment': {
            'endpoint': AZURE_ENDPOINT,
            'deployment': AZURE_DEPLOYMENT,
            'api_version': AZURE_API_VERSION,
        },
        'payload': payload,
    }

    out_path = OUT_DIR / f'{persona_id}-{model_alias}-{stamp}.json'
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[{persona_id}] saved: {out_path}')
    print(f'[{persona_id}] MASC: {masc_profile}')
    print(f'[{persona_id}] raw: {raw_scores}')
    return result


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--full57']
    if '--full57' in sys.argv:
        # The vignette loader lives in run_synthetic and reads ITS module
        # global; setting this file's LOAD_ALL_VIGNETTES did nothing (the
        # historical bug). The 57-item collections were run via the dedicated
        # runners (run_gpt55_full57.py / run_wave5_full57.py), which set the
        # attribute correctly, as below.
        import run_synthetic
        run_synthetic.LOAD_ALL_VIGNETTES = True
        LOAD_ALL_VIGNETTES = True

    if len(args) < 1:
        print(f'Usage: python run_gpt55.py <persona_id> [--full57]')
        sys.exit(1)

    run_persona_gpt55(args[0])
