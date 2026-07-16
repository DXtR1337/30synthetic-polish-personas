# -*- coding: utf-8 -*-
"""Run synthetic personas on Gemini 3 Flash Preview."""
import hashlib, json, os, sys, re, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / 'out'
sys.path.insert(0, str(SCRIPT_DIR))
from run_synthetic import build_system_prompt, build_user_prompt, load_tctm_vignettes

GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_KEY:
    raise RuntimeError('GEMINI_API_KEY environment variable is required')
GEMINI_MODEL = 'gemini-3-flash-preview'
MODEL_ALIAS = 'gemini3f'

# Sampling: request body wysyła WYŁĄCZNIE maxOutputTokens (vendor-default
# temperature/top_p, bez seeda) — identycznie jak kolekcja kwietniowa 2026.
# Wcześniejsza wersja tego bloku deklarowała temperature/top_p/seed, których
# request body NIGDY nie wysyłał — metadane poniżej zapisują stan faktyczny.
SAMPLING_MAX_OUTPUT_TOKENS = 16000

def run_persona(persona_id):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')

    bio_path = SCRIPT_DIR / f'{persona_id}.md'
    bio_raw = bio_path.read_text(encoding='utf-8')
    if bio_raw.startswith('---\n'):
        parts = bio_raw.split('\n---\n', 1)
        if len(parts) != 2:
            raise ValueError(
                f'{persona_id}: malformed persona front matter (missing closing ---); '
                'refusing to build a prompt that could leak researcher metadata'
            )
        bio_body = parts[1]
        fm_raw = parts[0][4:]
    else:
        bio_body = bio_raw; fm_raw = ''

    persona_version = 1
    for line in fm_raw.splitlines():
        m = re.match(r'persona_version:\s*(\d+)', line.strip())
        if m:
            try: persona_version = int(m.group(1))
            except: pass

    vignettes_dict = load_tctm_vignettes()
    vignettes = list(vignettes_dict.values())

    system_prompt = build_system_prompt(bio_body)
    user_prompt = build_user_prompt(vignettes_dict)

    (OUT_DIR / f'{persona_id}-{MODEL_ALIAS}-{stamp}-system.txt').write_text(system_prompt, encoding='utf-8')
    (OUT_DIR / f'{persona_id}-{MODEL_ALIAS}-{stamp}-user.txt').write_text(user_prompt, encoding='utf-8')

    print(f'[{persona_id}] calling {GEMINI_MODEL}...')
    t_start = time.time()

    url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}'
    body = json.dumps({
        'systemInstruction': {'parts': [{'text': system_prompt}]},
        'contents': [{'parts': [{'text': user_prompt}]}],
        'generationConfig': {'maxOutputTokens': 16000},
    }).encode('utf-8')

    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            response = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
        raise RuntimeError(f'Gemini HTTP {e.code}: {err[:500]}') from e

    elapsed = time.time() - t_start
    raw_text = response['candidates'][0]['content']['parts'][0]['text']
    usage = response.get('usageMetadata', {})
    input_tokens = usage.get('promptTokenCount', 0)
    output_tokens = usage.get('candidatesTokenCount', 0)

    print(f'[{persona_id}] done in {elapsed:.1f}s, tokens in={input_tokens} out={output_tokens}')
    (OUT_DIR / f'{persona_id}-{MODEL_ALIAS}-{stamp}-raw.txt').write_text(raw_text, encoding='utf-8')

    # Parse JSON
    json_match = re.search(r'\{[\s\S]*\}', raw_text)
    if not json_match:
        raise RuntimeError(f'No JSON: {raw_text[:200]}')
    agent = json.loads(json_match.group(0))

    # Score TCTM
    NOW = datetime.now(timezone.utc).isoformat()
    rid = f'synthetic-{persona_id}-{MODEL_ALIAS}-v{persona_version}-{stamp}'
    LETTER = {'A':0,'B':1,'C':2,'D':3}
    tctm_answers = []; masc = {'correct':0,'DOS':0,'NAD':0,'BK':0,'unknown':0}
    raw_scores = {'subtext':0,'court':0,'eks':0,'pursuit':0,'repair':0}

    for ans in agent.get('tctm', []):
        iid = ans.get('id',''); letter = ans.get('answer','').strip().upper()
        ci = LETTER.get(letter, -1)
        vig = next((v for v in vignettes if v['id'] == iid), None)
        if not vig: continue
        ok = ci == vig['correctAnswer']
        mt = vig.get('mascTypes',[]); cm = mt[ci] if 0<=ci<len(mt) else 'unknown'
        if ok: masc['correct']+=1; sub=vig.get('subscale',''); raw_scores[sub]=raw_scores.get(sub,0)+1
        elif cm in masc: masc[cm]+=1
        else: masc['unknown']+=1
        tctm_answers.append({'itemId':iid,'chosenOptionIndex':ci,'chosenMascType':cm if not ok else 'correct',
                             'isCorrect':ok,'responseTimeMs':0,'changedAnswer':False,'presentationOrder':len(tctm_answers)+1})

    def parse_l(key, prefix):
        raw = agent.get(key, {})
        return {f'{prefix}-{int(k):02d}':int(v) for k,v in raw.items() if str(k).isdigit()}

    payload = {
        'respondentId':rid,'startedAt':NOW,'completedAt':NOW,'consented':True,'consentTimestamp':NOW,
        'totalDurationMs':0,'synthetic':True,
        'demographics':{'age':0,'gender':'synthetic','education':'synthetic','psychologyBackground':'no','socialCompetenceSelf':0},
        'tctm':{'answers':tctm_answers,'mascProfile':masc,'rawScores':raw_scores,'durationMs':0},
        'ecrR':{'answers':parse_l('ecrr','ecrr'),'durationMs':0},
        'ments':{'answers':parse_l('ments','ments'),'durationMs':0},
        'kpp':{'answers':parse_l('kpp','kpp'),'durationMs':0},
        'tipiPl':{'answers':parse_l('tipi','tipi'),'durationMs':0},
        'feedback':agent.get('feedback',{}),
    }

    biography_sha256 = hashlib.sha256(bio_raw.encode('utf-8')).hexdigest()

    result = {'persona_id':persona_id,'persona_version':persona_version,'biography_length':len(bio_body.split()),
              'biography_sha256':biography_sha256,
              'model_name':GEMINI_MODEL,'model_stop_reason':'stop','tokens_input':input_tokens,
              'tokens_output':output_tokens,'elapsed_seconds':round(elapsed,2),'respondent_id':rid,
              'sampling':{
                  'max_output_tokens':SAMPLING_MAX_OUTPUT_TOKENS,
                  'request_params_note':'only maxOutputTokens sent; vendor-default temperature/top_p; no seed (matches April 2026 collection protocol)',
              },
              'payload':payload}

    out_path = OUT_DIR / f'{persona_id}-{MODEL_ALIAS}-{stamp}.json'
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[{persona_id}] MASC: {masc}')
    print(f'[{persona_id}] raw: {raw_scores}')
    return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python run_gemini.py <persona_id>')
        sys.exit(1)
    run_persona(sys.argv[1])
