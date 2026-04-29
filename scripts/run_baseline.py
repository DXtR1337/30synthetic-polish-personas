# -*- coding: utf-8 -*-
"""Run baseline: models complete battery as THEMSELVES, no persona."""
import json, os, sys, re, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / 'out'
sys.path.insert(0, str(SCRIPT_DIR))
from run_synthetic import build_user_prompt, load_tctm_vignettes

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

def run_baseline(model_alias, endpoint_fn):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    tag = f'baseline-{model_alias}'

    vignettes_dict = load_tctm_vignettes()
    vignettes = list(vignettes_dict.values())
    user_prompt = build_user_prompt(vignettes_dict)

    (OUT_DIR / f'{tag}-{stamp}-system.txt').write_text(SYSTEM_BASELINE, encoding='utf-8')
    (OUT_DIR / f'{tag}-{stamp}-user.txt').write_text(user_prompt, encoding='utf-8')

    print(f'[{tag}] calling...')
    t_start = time.time()
    raw_text, input_tok, output_tok, model_name = endpoint_fn(SYSTEM_BASELINE, user_prompt)
    elapsed = time.time() - t_start
    print(f'[{tag}] done in {elapsed:.1f}s')

    (OUT_DIR / f'{tag}-{stamp}-raw.txt').write_text(raw_text, encoding='utf-8')

    json_match = re.search(r'\{[\s\S]*\}', raw_text)
    if not json_match: raise RuntimeError(f'No JSON: {raw_text[:200]}')
    agent = json.loads(json_match.group(0))

    # Score TCTM
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
        tctm_answers.append({'itemId':iid,'chosenOptionIndex':ci,'chosenMascType':cm if not ok else 'correct','isCorrect':ok,'responseTimeMs':0,'changedAnswer':False,'presentationOrder':len(tctm_answers)+1})

    def parse_l(key, prefix):
        raw = agent.get(key, {})
        return {f'{prefix}-{int(k):02d}':int(v) for k,v in raw.items() if str(k).isdigit()}

    NOW = datetime.now(timezone.utc).isoformat()
    payload = {
        'respondentId':f'baseline-{model_alias}-{stamp}','startedAt':NOW,'completedAt':NOW,
        'consented':True,'consentTimestamp':NOW,'totalDurationMs':0,'synthetic':True,
        'demographics':{'age':0,'gender':'ai','education':'ai','psychologyBackground':'no'},
        'tctm':{'answers':tctm_answers,'mascProfile':masc,'rawScores':raw_scores,'durationMs':0},
        'ecrR':{'answers':parse_l('ecrr','ecrr'),'durationMs':0},
        'ments':{'answers':parse_l('ments','ments'),'durationMs':0},
        'kpp':{'answers':parse_l('kpp','kpp'),'durationMs':0},
        'tipiPl':{'answers':parse_l('tipi','tipi'),'durationMs':0},
        'feedback':agent.get('feedback',{}),
    }

    result = {'persona_id':'baseline','persona_version':0,'biography_length':0,
              'model_name':model_name,'tokens_input':input_tok,'tokens_output':output_tok,
              'elapsed_seconds':round(elapsed,2),'respondent_id':f'baseline-{model_alias}-{stamp}','payload':payload}

    out_path = OUT_DIR / f'{tag}-{stamp}.json'
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[{tag}] MASC: {masc}')
    print(f'[{tag}] raw: {raw_scores}')
    return result

# Endpoint functions
def call_bedrock(system, user, model_id):
    key = os.environ.get('BEDROCK_API_KEY','')
    region = 'eu-central-1'
    url = f'https://bedrock-runtime.{region}.amazonaws.com/model/{model_id}/invoke'
    body = json.dumps({'anthropic_version':'bedrock-2023-05-31','max_tokens':16000,'system':system,'messages':[{'role':'user','content':user}]}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type':'application/json','Authorization':f'Bearer {key}'}, method='POST')
    with urllib.request.urlopen(req, timeout=300) as resp:
        r = json.loads(resp.read())
    text = r['content'][0]['text']
    usage = r.get('usage',{})
    return text, usage.get('input_tokens',0), usage.get('output_tokens',0), model_id

def call_azure_gpt(system, user):
    key = os.environ.get('AZURE_GPT_KEY', '')  # set in .env.local
    url = 'https://synthetic-benchmark.openai.azure.com/openai/deployments/gpt-5.4-mini/chat/completions?api-version=2024-10-21'
    body = json.dumps({'messages':[{'role':'system','content':system},{'role':'user','content':user}],'max_completion_tokens':16000}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type':'application/json','api-key':key}, method='POST')
    with urllib.request.urlopen(req, timeout=300) as resp:
        r = json.loads(resp.read())
    text = r['choices'][0]['message']['content']
    usage = r.get('usage',{})
    return text, usage.get('prompt_tokens',0), usage.get('completion_tokens',0), 'gpt-5.4-mini'

def call_grok(system, user):
    key = os.environ.get('AZURE_GROK_KEY', '')  # set in .env.local
    url = 'https://michalseido-0654-resource.openai.azure.com/openai/v1/chat/completions'
    body = json.dumps({'model':'grok-4-20-reasoning','messages':[{'role':'system','content':system},{'role':'user','content':user}],'max_completion_tokens':16000}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type':'application/json','api-key':key}, method='POST')
    with urllib.request.urlopen(req, timeout=300) as resp:
        r = json.loads(resp.read())
    text = r['choices'][0]['message']['content']
    usage = r.get('usage',{})
    return text, usage.get('prompt_tokens',0), usage.get('completion_tokens',0), 'grok-4-20-reasoning'

def call_gemini(system, user):
    key = os.environ.get('GEMINI_API_KEY', '')  # set in .env.local
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={key}'
    body = json.dumps({'systemInstruction':{'parts':[{'text':system}]},'contents':[{'parts':[{'text':user}]}],'generationConfig':{'maxOutputTokens':16000}}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=300) as resp:
        r = json.loads(resp.read())
    text = r['candidates'][0]['content']['parts'][0]['text']
    usage = r.get('usageMetadata',{})
    return text, usage.get('promptTokenCount',0), usage.get('candidatesTokenCount',0), 'gemini-3-flash-preview'

if __name__ == '__main__':
    # Load env for Bedrock
    env_path = SCRIPT_DIR / '../../../../.env.local'
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                k,v = line.split('=',1)
                os.environ.setdefault(k.strip(), v.strip())

    models = {
        'sonnet': lambda s,u: call_bedrock(s,u,'eu.anthropic.claude-sonnet-4-6'),
        'opus': lambda s,u: call_bedrock(s,u,'eu.anthropic.claude-opus-4-6-v1'),
        'gpt': lambda s,u: call_azure_gpt(s,u),
        'grok': lambda s,u: call_grok(s,u),
        'gemini': lambda s,u: call_gemini(s,u),
    }

    targets = sys.argv[1:] if len(sys.argv) > 1 else list(models.keys())
    for m in targets:
        if m in models:
            for run in range(5):
                print(f'\n=== {m} run {run+1}/5 ===')
                try:
                    run_baseline(m, models[m])
                except Exception as e:
                    print(f'ERROR: {e}')
                time.sleep(2)
