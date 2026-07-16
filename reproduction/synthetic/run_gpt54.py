# -*- coding: utf-8 -*-
"""
Run synthetic personas + baseline + noprompt on Azure AI Foundry (GPT-5.4 FULL — NOT mini).

Endpoint: https://synthetic-benchmark.services.ai.azure.com/openai/v1/responses
API:      OpenAI Responses API (input/output/max_output_tokens),
          NOT Chat Completions (messages/max_completion_tokens) used by run_gpt55.py.

Mirrors paper methodology (Wiencek 2026, v17) for the new 7th model:
  - persona condition: each of 30 biographies x 2 runs (test-retest)
  - baseline condition: model answers as itself, N=10 (matches Sonnet/Opus/Grok)
  - zero-prompt condition: only user content, no system prompt, N=6

Reuses prompt builders from run_synthetic.py. Output JSON shape matches
run_gpt55.py / run_azure.py so append_to_csv works downstream.

Usage:
  python run_gpt54.py <persona_id>             # single persona, one run
  python run_gpt54.py --all-personas           # all 30, one pass each
  python run_gpt54.py --retest                 # all 30, retest pass (run 2)
  python run_gpt54.py --baseline [N]           # N baseline runs (default 10)
  python run_gpt54.py --noprompt [N]           # N noprompt runs (default 6)
  python run_gpt54.py --full                   # everything: 30x2 + 10 baseline + 6 noprompt
"""
import json, os, sys, re, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / 'out'
OUT_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(SCRIPT_DIR))
from run_synthetic import build_system_prompt, build_user_prompt, load_tctm_vignettes

# ═══════════════════════════════════════════════════════════════
# Azure AI Foundry config — GPT-5.4 (full)
# ═══════════════════════════════════════════════════════════════
FOUNDRY_ENDPOINT = os.environ.get(
    'AZURE_FOUNDRY_GPT54_ENDPOINT',
    'https://synthetic-benchmark.services.ai.azure.com/openai/v1/responses',
)
FOUNDRY_KEY = os.environ.get('AZURE_FOUNDRY_GPT54_KEY')
if not FOUNDRY_KEY:
    raise RuntimeError('AZURE_FOUNDRY_GPT54_KEY environment variable is required')
FOUNDRY_MODEL = os.environ.get('AZURE_FOUNDRY_GPT54_MODEL', 'gpt-5.4')
MAX_OUTPUT_TOKENS = 16000

# Sampling parameters (frozen for v18 reproducibility).
SAMPLING_TEMPERATURE = 1.0
SAMPLING_TOP_P = 1.0
SAMPLING_SEED = 20260528
SAMPLING_REASONING_EFFORT = 'medium'
MODEL_ALIAS = 'gpt54f'  # f = full (distinct from existing 'gpt' = gpt-5.4-mini)

# 30 personas in paper order
PERSONAS = [
    'adrian', 'agata', 'ania', 'anna-sim', 'bartek', 'dominika',
    'ewa', 'filip', 'gabriela', 'hubert', 'jakub', 'jola',
    'kamil', 'kasia', 'klaudia', 'kuba', 'lukasz', 'magda',
    'marek', 'michal-k', 'michal-sim', 'natalia', 'ola', 'pawel',
    'piotr', 'radek', 'sara', 'tomek', 'weronika', 'zuzia',
]

# Baseline system prompt — identical wording to run_baseline.py for cross-model parity
SYSTEM_BASELINE = """Jesteś modelem językowym AI. Za chwilę dostaniesz baterię pytań psychologicznych.
Odpowiedz na nie szczerze, tak jak Ty — model AI — odpowiedziałbyś, gdybyś musiał wybrać.
Nie udawaj żadnej postaci. Odpowiadaj jako Ty.

KRYTYCZNE: Zwróć wynik WYŁĄCZNIE jako jeden blok JSON w formacie podanym poniżej. Żadnego tekstu przed ani po.

Format odpowiedzi:
```json
{
  "tctm": [
    {"id": "w01", "answer": "A|B|C|D"},
    ...
  ],
  "ecrr": {"1": 1-7, "2": 1-7, ..., "36": 1-7},
  "ments": {"1": 1-5, "2": 1-5, ..., "28": 1-5},
  "kpp": {"1": 1-5, "2": 1-5, ..., "36": 1-5},
  "tipi": {"1": 1-7, "2": 1-7, ..., "10": 1-7},
  "feedback": {
    "hardestVignette": "odpowiedz",
    "unclearVignette": {"answer": "tak|nie", "details": ""},
    "disagreedAnswer": {"answer": "tak|nie|nie_wiem", "details": ""},
    "estimatedDurationMin": 0,
    "technicalIssues": {"answer": "nie", "details": ""},
    "willingFutureParticipation": "tak|byc_moze|nie",
    "additionalComments": ""
  }
}
```
"""


# ═══════════════════════════════════════════════════════════════
# Foundry Responses API call
# ═══════════════════════════════════════════════════════════════
def call_foundry_gpt54(system_prompt, user_prompt):
    """Call Azure AI Foundry /openai/v1/responses with gpt-5.4.

    Returns: (raw_text, input_tokens, output_tokens, model_name, finish_reason).
    Raises RuntimeError on HTTP error or content filter block.
    """
    input_messages = []
    if system_prompt:
        input_messages.append({'role': 'system', 'content': system_prompt})
    input_messages.append({'role': 'user', 'content': user_prompt})

    # NOTE: Foundry Responses endpoint (gpt-5.4 reasoning model) rejects `seed`, `top_p`, `temperature`
    # with HTTP 400 (Unsupported/Unknown parameter). Per paper §S7.6 these were already documented
    # as non-functional. Vendor-default sampling used (matches paper §2.3 "vendor-default sampling parameters").
    body = json.dumps({
        'model': FOUNDRY_MODEL,
        'input': input_messages,
        'max_output_tokens': MAX_OUTPUT_TOKENS,
        'reasoning': {'effort': SAMPLING_REASONING_EFFORT},
    }).encode('utf-8')

    req = urllib.request.Request(
        FOUNDRY_ENDPOINT,
        data=body,
        headers={
            'Content-Type': 'application/json',
            'api-key': FOUNDRY_KEY,
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            r = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
        raise RuntimeError(f'Foundry HTTP {e.code}: {err_body[:800]}') from e

    if r.get('status') != 'completed':
        raise RuntimeError(f'Status not completed: {r.get("status")}, error={r.get("error")}')

    # Extract assistant message text. Foundry Responses output is a list of items;
    # we want the last "message"-typed item's first output_text.
    text = ''
    for item in r.get('output', []):
        if item.get('type') == 'message':
            for c in item.get('content', []):
                if c.get('type') == 'output_text':
                    text = c.get('text', '')
                    break
    if not text:
        raise RuntimeError(f'No output_text in response: {json.dumps(r)[:500]}')

    usage = r.get('usage', {})
    input_tok = usage.get('input_tokens', 0)
    output_tok = usage.get('output_tokens', 0)
    model_name = r.get('model', FOUNDRY_MODEL)
    finish = r.get('incomplete_details') or 'stop'
    return text, input_tok, output_tok, model_name, finish


# ═══════════════════════════════════════════════════════════════
# Scoring helpers (1:1 with run_gpt55.py)
# ═══════════════════════════════════════════════════════════════
LETTER_TO_IDX = {'A': 0, 'B': 1, 'C': 2, 'D': 3}


def score_payload(agent_answers, vignettes):
    tctm_raw = agent_answers.get('tctm') or agent_answers.get('winiety') or []
    if isinstance(tctm_raw, dict):
        tctm_raw = [{'id': k, 'answer': v} for k, v in tctm_raw.items()]

    tctm_answers = []
    masc_profile = {'correct': 0, 'DOS': 0, 'NAD': 0, 'BK': 0, 'unknown': 0}
    raw_scores = {'subtext': 0, 'court': 0, 'eks': 0, 'pursuit': 0, 'repair': 0}

    for ans in tctm_raw:
        iid = ans.get('id', '')
        letter = str(ans.get('answer', '')).strip().upper()
        ci = LETTER_TO_IDX.get(letter, -1)
        vig = next((v for v in vignettes if v['id'] == iid), None)
        if not vig:
            continue
        ok = (ci == vig['correctAnswer'])
        masc_types = vig.get('mascTypes', [])
        chosen_masc = masc_types[ci] if 0 <= ci < len(masc_types) else 'unknown'
        if ok:
            masc_profile['correct'] += 1
            sub = vig.get('subscale', '')
            if sub in raw_scores:
                raw_scores[sub] += 1
        elif chosen_masc in masc_profile:
            masc_profile[chosen_masc] += 1
        else:
            masc_profile['unknown'] += 1
        tctm_answers.append({
            'itemId': iid,
            'chosenOptionIndex': ci,
            'chosenMascType': chosen_masc if not ok else 'correct',
            'isCorrect': ok,
            'responseTimeMs': 0,
            'changedAnswer': False,
            'presentationOrder': len(tctm_answers) + 1,
        })

    def parse_l(key, prefix):
        raw = agent_answers.get(key, {})
        return {f'{prefix}-{int(k):02d}': int(v) for k, v in raw.items() if str(k).isdigit()}

    return {
        'tctm_answers': tctm_answers,
        'masc_profile': masc_profile,
        'raw_scores': raw_scores,
        'ecrr': parse_l('ecrr', 'ecrr'),
        'ments': parse_l('ments', 'ments'),
        'kpp': parse_l('kpp', 'kpp'),
        'tipi': parse_l('tipi', 'tipi'),
        'feedback': agent_answers.get('feedback', {}),
    }


def build_result(persona_id, persona_version, bio_word_count, model_name, finish_reason,
                 input_tok, output_tok, elapsed, respondent_id, scored, demographics_label):
    NOW_ISO = datetime.now(timezone.utc).isoformat()
    payload = {
        'respondentId': respondent_id,
        'startedAt': NOW_ISO,
        'completedAt': NOW_ISO,
        'consented': True,
        'consentTimestamp': NOW_ISO,
        'totalDurationMs': 0,
        'synthetic': True,
        'demographics': {
            'age': 0, 'gender': demographics_label, 'education': demographics_label,
            'psychologyBackground': 'no', 'socialCompetenceSelf': 0,
        },
        'tctm': {
            'answers': scored['tctm_answers'],
            'mascProfile': scored['masc_profile'],
            'rawScores': scored['raw_scores'],
            'durationMs': 0,
        },
        'ecrR': {'answers': scored['ecrr'], 'durationMs': 0},
        'ments': {'answers': scored['ments'], 'durationMs': 0},
        'kpp': {'answers': scored['kpp'], 'durationMs': 0},
        'tipiPl': {'answers': scored['tipi'], 'durationMs': 0},
        'feedback': scored['feedback'],
    }
    return {
        'persona_id': persona_id,
        'persona_version': persona_version,
        'biography_length': bio_word_count,
        'model_name': model_name,
        'model_stop_reason': finish_reason,
        'tokens_input': input_tok,
        'tokens_output': output_tok,
        'elapsed_seconds': round(elapsed, 2),
        'respondent_id': respondent_id,
        'payload': payload,
    }


# ═══════════════════════════════════════════════════════════════
# Persona run
# ═══════════════════════════════════════════════════════════════
def run_persona(persona_id):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
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
    vignettes_dict = load_tctm_vignettes()
    vignettes = list(vignettes_dict.values())

    system_prompt = build_system_prompt(bio_body)
    user_prompt = build_user_prompt(vignettes_dict)

    (OUT_DIR / f'{persona_id}-{MODEL_ALIAS}-{stamp}-system.txt').write_text(system_prompt, encoding='utf-8')
    (OUT_DIR / f'{persona_id}-{MODEL_ALIAS}-{stamp}-user.txt').write_text(user_prompt, encoding='utf-8')

    print(f'[{persona_id}] bio={bio_word_count}w, calling gpt-5.4 (Foundry)...')
    t0 = time.time()
    raw, in_tok, out_tok, model_name, finish = call_foundry_gpt54(system_prompt, user_prompt)
    elapsed = time.time() - t0
    print(f'[{persona_id}] {elapsed:.1f}s, tokens in={in_tok} out={out_tok}, stop={finish}')

    (OUT_DIR / f'{persona_id}-{MODEL_ALIAS}-{stamp}-raw.txt').write_text(raw, encoding='utf-8')

    json_match = re.search(r'\{[\s\S]*\}', raw)
    if not json_match:
        raise RuntimeError(f'No JSON in response: {raw[:200]}')
    agent = json.loads(json_match.group(0))

    scored = score_payload(agent, vignettes)
    respondent_id = f'synthetic-{persona_id}-{MODEL_ALIAS}-v{persona_version}-{stamp}'
    result = build_result(persona_id, persona_version, bio_word_count, model_name, finish,
                          in_tok, out_tok, elapsed, respondent_id, scored, 'synthetic')

    out_path = OUT_DIR / f'{persona_id}-{MODEL_ALIAS}-{stamp}.json'
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[{persona_id}] MASC: {scored["masc_profile"]}  raw: {scored["raw_scores"]}')
    return result


# ═══════════════════════════════════════════════════════════════
# Baseline run (model as itself)
# ═══════════════════════════════════════════════════════════════
def run_baseline_once():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    tag = f'baseline-{MODEL_ALIAS}'
    vignettes_dict = load_tctm_vignettes()
    vignettes = list(vignettes_dict.values())
    user_prompt = build_user_prompt(vignettes_dict)

    (OUT_DIR / f'{tag}-{stamp}-system.txt').write_text(SYSTEM_BASELINE, encoding='utf-8')
    (OUT_DIR / f'{tag}-{stamp}-user.txt').write_text(user_prompt, encoding='utf-8')

    print(f'[{tag}] calling...')
    t0 = time.time()
    raw, in_tok, out_tok, model_name, finish = call_foundry_gpt54(SYSTEM_BASELINE, user_prompt)
    elapsed = time.time() - t0
    print(f'[{tag}] {elapsed:.1f}s, tokens in={in_tok} out={out_tok}, stop={finish}')

    (OUT_DIR / f'{tag}-{stamp}-raw.txt').write_text(raw, encoding='utf-8')
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if not json_match:
        raise RuntimeError(f'No JSON: {raw[:200]}')
    agent = json.loads(json_match.group(0))
    scored = score_payload(agent, vignettes)

    respondent_id = f'{tag}-{stamp}'
    result = build_result('baseline', 0, 0, model_name, finish, in_tok, out_tok, elapsed,
                          respondent_id, scored, 'ai')
    out_path = OUT_DIR / f'{tag}-{stamp}.json'
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[{tag}] MASC: {scored["masc_profile"]}  raw: {scored["raw_scores"]}')
    return result


# ═══════════════════════════════════════════════════════════════
# Zero-prompt run (no system prompt at all)
# ═══════════════════════════════════════════════════════════════
def run_noprompt_once():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    tag = f'noprompt-{MODEL_ALIAS}'
    vignettes_dict = load_tctm_vignettes()
    vignettes = list(vignettes_dict.values())
    user_prompt = build_user_prompt(vignettes_dict)

    (OUT_DIR / f'{tag}-{stamp}-system.txt').write_text('(empty)', encoding='utf-8')
    (OUT_DIR / f'{tag}-{stamp}-user.txt').write_text(user_prompt, encoding='utf-8')

    print(f'[{tag}] calling (no system prompt)...')
    t0 = time.time()
    raw, in_tok, out_tok, model_name, finish = call_foundry_gpt54('', user_prompt)
    elapsed = time.time() - t0
    print(f'[{tag}] {elapsed:.1f}s, tokens in={in_tok} out={out_tok}, stop={finish}')

    (OUT_DIR / f'{tag}-{stamp}-raw.txt').write_text(raw, encoding='utf-8')
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if not json_match:
        raise RuntimeError(f'No JSON: {raw[:200]}')
    agent = json.loads(json_match.group(0))
    scored = score_payload(agent, vignettes)

    respondent_id = f'{tag}-{stamp}'
    result = build_result('noprompt', 0, 0, model_name, finish, in_tok, out_tok, elapsed,
                          respondent_id, scored, 'ai')
    out_path = OUT_DIR / f'{tag}-{stamp}.json'
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[{tag}] MASC: {scored["masc_profile"]}  raw: {scored["raw_scores"]}')
    return result


# ═══════════════════════════════════════════════════════════════
# Orchestration
# ═══════════════════════════════════════════════════════════════
def run_all_personas(retest=False, sleep_between=2):
    label = 'retest' if retest else 'run-1'
    print(f'\n========== ALL 30 PERSONAS ({label}) ==========')
    ok, fail = [], []
    for i, p in enumerate(PERSONAS, 1):
        print(f'\n--- [{i}/30] {p} ({label}) ---')
        try:
            run_persona(p)
            ok.append(p)
        except Exception as e:
            print(f'ERROR [{p}]: {e}')
            fail.append((p, str(e)))
        time.sleep(sleep_between)
    print(f'\n========== {label} DONE: {len(ok)} ok, {len(fail)} failed ==========')
    if fail:
        for p, e in fail:
            print(f'  FAIL {p}: {e[:200]}')
    return ok, fail


def run_baselines(n=10, sleep_between=2):
    print(f'\n========== BASELINE (N={n}) ==========')
    for i in range(n):
        print(f'\n--- baseline {i+1}/{n} ---')
        try:
            run_baseline_once()
        except Exception as e:
            print(f'ERROR baseline {i+1}: {e}')
        time.sleep(sleep_between)


def run_noprompts(n=6, sleep_between=2):
    print(f'\n========== NOPROMPT (N={n}) ==========')
    for i in range(n):
        print(f'\n--- noprompt {i+1}/{n} ---')
        try:
            run_noprompt_once()
        except Exception as e:
            print(f'ERROR noprompt {i+1}: {e}')
        time.sleep(sleep_between)


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    if args[0] == '--all-personas':
        run_all_personas(retest=False)
    elif args[0] == '--retest':
        run_all_personas(retest=True)
    elif args[0] == '--baseline':
        n = int(args[1]) if len(args) > 1 else 10
        run_baselines(n)
    elif args[0] == '--noprompt':
        n = int(args[1]) if len(args) > 1 else 6
        run_noprompts(n)
    elif args[0] == '--full':
        run_all_personas(retest=False)
        run_all_personas(retest=True)
        run_baselines(10)
        run_noprompts(6)
    else:
        run_persona(args[0])
