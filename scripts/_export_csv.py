# Export all data to single CSV for JASP/jamovi/SPSS
import json, glob, os, csv, re
from analyze_and_prepare import score_dbzr, score_ments, score_kpp, score_tipi

# TCTM-22 item IDs (canonical order)
TCTM22_IDS = [
    'w01','s07','s08','s10','w08','c07','c10','w11',
    'w13','w14','e08','w15','w19','pw07','w22','pw09',
    'pw11','w25','r08','w28','r09','r10',
]

rows = []

def make_row(condition, model, persona, run_num, masc, scored, d, m, k, t, tctm_items=None):
    row = {
        'condition': condition, 'model': model, 'persona': persona, 'run': run_num,
        'tctm_correct': masc['correct'], 'tctm_total': scored,
        'dos': masc.get('DOS', ''), 'nad': masc.get('NAD', ''), 'bk': masc.get('BK', ''),
        'anx_mean': d['anx_mean'] if d else '', 'avo_mean': d['avo_mean'] if d else '',
        'z_anx': d['z_anx'] if d else '', 'z_avo': d['z_avo'] if d else '',
        'style': d['style'] if d else '',
        'ments_self': m['self'] if m else '', 'ments_other': m['other'] if m else '',
        'ments_mot': m['mot'] if m else '', 'ments_total': m['total'] if m else '',
        'z_ments_total': m['z_total'] if m else '',
        'kpp_mean': k['mean'] if k else '', 'z_kpp': k['z_mean'] if k else '',
        'tipi_e': t['E'] if t else '', 'tipi_a': t['A'] if t else '',
        'tipi_c': t['C'] if t else '', 'tipi_es': t['ES'] if t else '',
        'tipi_o': t['O'] if t else '',
        'z_e': t['z_E'] if t else '', 'z_a': t['z_A'] if t else '',
        'z_c': t['z_C'] if t else '', 'z_es': t['z_ES'] if t else '',
        'z_o': t['z_O'] if t else '',
    }
    # Per-item TCTM (1=correct, 0=incorrect, empty=not answered)
    if tctm_items is None:
        tctm_items = {}
    for iid in TCTM22_IDS:
        row[f'tctm_{iid}'] = tctm_items.get(iid, '')
    return row

def extract_tctm_items(answers):
    """Extract per-item correct/incorrect from TCTM answer list."""
    items = {}
    for a in answers:
        iid = a.get('itemId', '')
        if iid in TCTM22_IDS:
            items[iid] = 1 if a.get('isCorrect', False) else 0
    return items

def add_from_payload(condition, model, persona, run_num, pay):
    ans = pay['tctm'].get('answers', [])
    if len(ans) < 10: return
    masc = pay['tctm']['mascProfile']
    ecrr = pay.get('ecrR', {}).get('answers', {})
    has = len(ecrr) >= 30
    ments_a = pay.get('ments', {}).get('answers', {})
    kpp_a = pay.get('kpp', {}).get('answers', {})
    tipi_a = pay.get('tipiPl', {}).get('answers', {})
    d = score_dbzr(ecrr) if has else None
    m = score_ments(ments_a) if len(ments_a) >= 20 else None
    k = score_kpp(kpp_a) if len(kpp_a) >= 30 else None
    t = score_tipi(tipi_a) if len(tipi_a) >= 8 else None
    tctm_items = extract_tctm_items(ans)
    rows.append(make_row(condition, model, persona, run_num, masc, len(ans), d, m, k, t, tctm_items))

# ============ PERSONA RUNS ============
model_tags = {
    'sonnet': 'Claude Sonnet 4.6', 'opus': 'Claude Opus 4.6',
    'gpt54mini': 'GPT-5.4-mini', 'grok4': 'Grok-4-20', 'gemini3f': 'Gemini 3 Flash',
}
for tag, mn in model_tags.items():
    pruns = {}
    for f in sorted(glob.glob('out/*-' + tag + '-*.json')):
        if any(x in f for x in ['baseline','noprompt','system','user','raw']): continue
        try:
            d = json.load(open(f, encoding='utf-8'))
            pay = d['payload']
            if len(pay['tctm'].get('answers', [])) != 22: continue
            pid = os.path.basename(f).split('-' + tag)[0]
            if pid not in pruns: pruns[pid] = []
            pruns[pid].append(d)
        except: pass
    for pid, runs in sorted(pruns.items()):
        for i, d in enumerate(runs):
            add_from_payload('persona', mn, pid, i+1, d['payload'])

# ============ BASELINE RUNS ============
bmap = {'sonnet':'Claude Sonnet 4.6','opus':'Claude Opus 4.6','gpt':'GPT-5.4-mini','grok':'Grok-4-20','gemini':'Gemini 3 Flash'}
for tag, mn in bmap.items():
    rn = 0
    for f in sorted(glob.glob('out/baseline-' + tag + '-*.json')):
        if any(x in f for x in ['system','user','raw']): continue
        try:
            d = json.load(open(f, encoding='utf-8'))
            pay = d['payload']
            if len(pay['tctm'].get('answers', [])) != 22: continue
            rn += 1
            add_from_payload('baseline', mn, 'self', rn, pay)
        except: pass

# ============ HUMAN RUNS (from Supabase, full payloads) ============
# 8 rows in DB, but first two are same person (split submit):
#   submit 1: TCTM + ECR-R + TIPI (no MentS/KPP)
#   submit 2: retest TCTM + ECR-R + MentS + KPP + TIPI
# Merge: take TCTM from submit 1 (first attempt), questionnaires from submit 2
human_full = json.load(open('human_payloads_full.json', encoding='utf-8'))
human_rids = list(human_full.keys())

# Merge R01: TCTM from [0], questionnaires from [1]
merged_r01 = json.loads(json.dumps(human_full[human_rids[1]]))  # start with submit 2 (has all questionnaires)
merged_r01['tctm'] = human_full[human_rids[0]]['tctm']  # overwrite TCTM with first attempt
add_from_payload('human', 'Human', 'R01', 1, merged_r01)

# R02-R07: remaining 6 respondents (indices 2-7 in DB)
for i, rid in enumerate(human_rids[2:], start=2):
    pay = human_full[rid]
    label = f'R{i:02d}'
    add_from_payload('human', 'Human', label, 1, pay)

# ============ NO-PROMPT RUNS ============
import run_synthetic
run_synthetic.LOAD_ALL_VIGNETTES = True
vignettes = run_synthetic.load_tctm_vignettes()
vigs_list = list(vignettes.values())
run_synthetic.LOAD_ALL_VIGNETTES = False
LETTER = {'A':0,'B':1,'C':2,'D':3}

def score_tctm_dict(ad):
    masc = {'correct':0,'DOS':0,'NAD':0,'BK':0}
    sc = 0
    items = {}
    for iid, letter in ad.items():
        if not isinstance(letter, str): continue
        ci = LETTER.get(letter.strip().upper(), -1)
        vig = next((v for v in vigs_list if v['id'] == iid), None)
        if not vig: continue
        sc += 1
        ok = ci == vig['correctAnswer']
        mt = vig.get('mascTypes', [])
        cm = mt[ci] if 0 <= ci < len(mt) else 'unknown'
        if ok: masc['correct'] += 1
        elif cm in masc: masc[cm] += 1
        if iid in TCTM22_IDS:
            items[iid] = 1 if ok else 0
    return masc, sc, items

def list_to_dict(lst, prefix):
    return {f'{prefix}-{i+1:02d}': int(v) for i, v in enumerate(lst)}

np_files = {
    'Claude Sonnet 4.6': 'out/noprompt-sonnet-20260416T100229-raw.txt',
    'Claude Opus 4.6': 'out/noprompt-opus-20260416T100257-raw.txt',
    'GPT-5.4-mini': 'out/noprompt-gpt-20260416T100330-raw.txt',
    'Grok-4-20': 'out/noprompt-grok-20260416T100338-raw.txt',
    'Gemini 3 Flash': 'out/noprompt-gemini-20260416T100410-raw.txt',
}
for mn, path in np_files.items():
    with open(path, encoding='utf-8') as f:
        text = f.read()
    match = re.search(r'\{[\s\S]*\}', text)
    data = json.loads(match.group(0))

    # Find TCTM dict
    td = None
    for key in data:
        if isinstance(data[key], dict):
            vals = list(data[key].values())
            if len(vals) > 20 and all(isinstance(v, str) and len(v) == 1 for v in vals[:10]):
                td = data[key]; break
    masc, sc, np_tctm_items = score_tctm_dict(td) if td else ({'correct':0,'DOS':0,'NAD':0,'BK':0}, 0, {})

    # Find Likerts
    ecrr = ments_d = kpp_d = tipi_d = None
    # Normalize keys: strip Polish diacritics for matching
    for key in data:
        val = data[key]
        lk = key.lower().replace('_', '').replace('-', '')
        # Also handle garbled Polish chars (część -> cz??2 etc)
        is_list36 = isinstance(val, list) and len(val) == 36
        is_list28 = isinstance(val, list) and len(val) == 28
        is_list10 = isinstance(val, list) and len(val) == 10
        is_dict36 = isinstance(val, dict) and len(val) == 36
        is_dict28 = isinstance(val, dict) and len(val) == 28
        is_dict10 = isinstance(val, dict) and len(val) == 10
        if is_dict36 and ('dbz' in lk or 'ecrr' in lk):
            ecrr = {f'ecrr-{int(k):02d}': int(v) for k, v in val.items()}
        elif is_list36 and ecrr is None:  # first list of 36 = DBZ-R
            ecrr = list_to_dict(val, 'ecrr')
        elif is_dict28 and 'ment' in lk:
            ments_d = {f'ments-{int(k):02d}': int(v) for k, v in val.items()}
        elif is_list28 and ments_d is None:  # first list of 28 = MentS
            ments_d = list_to_dict(val, 'ments')
        elif is_dict36 and 'kpp' in lk:
            kpp_d = {f'kpp-{int(k):02d}': int(v) for k, v in val.items()}
        elif is_list36 and ecrr is not None and kpp_d is None:  # second list of 36 = KPP
            kpp_d = list_to_dict(val, 'kpp')
        elif is_dict10 and 'tipi' in lk:
            tipi_d = {f'tipi-{int(k):02d}': int(v) for k, v in val.items()}
        elif is_list10 and tipi_d is None:  # first list of 10 = TIPI
            tipi_d = list_to_dict(val, 'tipi')

    dd = score_dbzr(ecrr) if ecrr else None
    mm = score_ments(ments_d) if ments_d else None
    kk = score_kpp(kpp_d) if kpp_d else None
    tt = score_tipi(tipi_d) if tipi_d else None
    rows.append(make_row('noprompt', mn, 'self', 1, masc, sc, dd, mm, kk, tt, np_tctm_items))

# ============ WRITE ============
fields = list(rows[0].keys())
with open('all_data.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

conds = {}; mods = {}
for r in rows:
    conds[r['condition']] = conds.get(r['condition'], 0) + 1
    mods[r['model']] = mods.get(r['model'], 0) + 1
print(f'Total: {len(rows)} rows, {len(fields)} columns')
print('By condition:', {k: v for k, v in sorted(conds.items())})
print('By model:', {k: v for k, v in sorted(mods.items())})
