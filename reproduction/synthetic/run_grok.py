# -*- coding: utf-8 -*-
"""
Run synthetic personas on Azure AI Foundry (Grok-4-20-reasoning).
Reuses prompts from run_synthetic.py, swaps Bedrock for Azure.
"""
import json, os, sys, re, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / 'out'
OUT_DIR.mkdir(exist_ok=True)

# Import prompt builders from existing script
sys.path.insert(0, str(SCRIPT_DIR))
from run_synthetic import build_system_prompt, build_user_prompt, load_tctm_vignettes

# Azure config
AZURE_ENDPOINT = 'https://michalseido-0654-resource.openai.azure.com/openai/v1/'
AZURE_KEY = os.environ.get('AZURE_GROK_KEY', '')
if not AZURE_KEY:
    raise RuntimeError('AZURE_GROK_KEY environment variable is required')
AZURE_DEPLOYMENT = os.environ.get('AZURE_OPENAI_DEPLOYMENT', 'grok-4-20-reasoning')
AZURE_API_VERSION = '2024-10-21'
MAX_COMPLETION_TOKENS = 16000

# Sampling parameters (frozen for v18 reproducibility).
SAMPLING_TEMPERATURE = 1.0
SAMPLING_TOP_P = 1.0
SAMPLING_SEED = 20260528
SAMPLING_REASONING_EFFORT = 'medium'

# Vignette loading
LOAD_ALL_VIGNETTES = False

def run_persona_azure(persona_id):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    model_alias = 'grok4'

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

    # 2. Load vignettes (dict keyed by item_id)
    vignettes_dict = load_tctm_vignettes()
    vignettes = list(vignettes_dict.values())
    label = 'TCTM-22'
    print(f'[{persona_id}] {len(vignettes)} winiet ({label})')

    # 3. Build prompts (build_user_prompt expects the dict)
    system_prompt = build_system_prompt(bio_body)
    user_prompt = build_user_prompt(vignettes_dict)

    # Save prompts for debugging
    (OUT_DIR / f'{persona_id}-{model_alias}-{stamp}-system.txt').write_text(system_prompt, encoding='utf-8')
    (OUT_DIR / f'{persona_id}-{model_alias}-{stamp}-user.txt').write_text(user_prompt, encoding='utf-8')

    print(f'[{persona_id}] system: {len(system_prompt)} chars, user: {len(user_prompt)} chars')

    # 4. Call Azure OpenAI
    url = f'{AZURE_ENDPOINT.rstrip("/")}/chat/completions'

    req_body = json.dumps({
        'model': AZURE_DEPLOYMENT,
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

    print(f'[{persona_id}] calling Azure Grok-4-20-reasoning...')
    t_start = time.time()

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            resp_body = resp.read()
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
        raise RuntimeError(f'Azure HTTP {e.code}: {err_body[:500]}') from e

    response = json.loads(resp_body)
    elapsed = time.time() - t_start

    # Parse response
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

    # 6. Build payload (same as run_synthetic.py)
    NOW_ISO = datetime.now(timezone.utc).isoformat()
    respondent_id = f'synthetic-{persona_id}-{model_alias}-v{persona_version}-{stamp}'

    # TCTM
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

    # Likert scales
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

    result = {
        'persona_id': persona_id,
        'persona_version': persona_version,
        'biography_length': bio_word_count,
        'model_name': model_name,
        'model_stop_reason': finish_reason,
        'tokens_input': input_tokens,
        'tokens_output': output_tokens,
        'elapsed_seconds': round(elapsed, 2),
        'respondent_id': respondent_id,
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
        LOAD_ALL_VIGNETTES = True

    if len(args) < 1:
        print(f'Usage: python run_grok.py <persona_id> [--full57]')
        sys.exit(1)

    run_persona_azure(args[0])
