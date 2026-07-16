# =============================================================================
# ARCHIVAL ONLY -- DO NOT USE TO REPRODUCE THE CORRECTED COLLECTION.
# This is the early-snapshot pipeline (pre-correction serializer, old paths).
# The pipeline actually used for the corrected collections lives in
# /reproduction/synthetic/ (run_wave3/4/5, corrected run_synthetic.py).
# =============================================================================
# -*- coding: utf-8 -*-
"""
Full CSV regenerator — 6 vendors.

Reads from out/ directory and assembles all_data.csv from scratch:
  - persona condition: out/{persona}-{tag}-{ts}.json (run 1/2 = chronological)
  - baseline condition: out/baseline-{tag}-{ts}.json
  - noprompt condition: re-scores ALL noprompt-{tag}-{ts}-raw.txt
    (handles polish keys, list-vs-dict, nested responses)
  - human condition: from human_payloads_full.json

Used after adding GPT-5.5 as 6th vendor. Idempotent and exhaustive —
unlike _export_csv.py it doesn't use hardcoded single-file noprompt
paths; it re-scores every raw.txt in out/.
"""
import json, csv, re, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from analyze_and_prepare import score_dbzr, score_ments, score_kpp, score_tipi
from run_synthetic import load_tctm_vignettes

OUT_DIR = SCRIPT_DIR / 'out'
CSV_PATH = SCRIPT_DIR / 'all_data.csv'

# Model alias maps
PERSONA_TAG_TO_LONG = {
    'sonnet': 'Claude Sonnet 4.6',
    'opus': 'Claude Opus 4.6',
    'gpt54mini': 'GPT-5.4-mini',
    'gpt55': 'GPT-5.5',
    'grok4': 'Grok-4-20',
    'gemini3f': 'Gemini 3 Flash',
}
NOPROMPT_TAG_TO_LONG = {
    'sonnet': 'Claude Sonnet 4.6',
    'opus': 'Claude Opus 4.6',
    'gpt': 'GPT-5.4-mini',
    'gpt55': 'GPT-5.5',
    'grok': 'Grok-4-20',
    'gemini': 'Gemini 3 Flash',
}
BASELINE_TAG_TO_LONG = {
    'sonnet': 'Claude Sonnet 4.6',
    'opus': 'Claude Opus 4.6',
    'gpt': 'GPT-5.4-mini',
    'grok': 'Grok-4-20',
    'gemini': 'Gemini 3 Flash',
}

TCTM22_IDS = [
    'w01','s07','s08','s10','w08','c07','c10','w11',
    'w13','w14','e08','w15','w19','pw07','w22','pw09',
    'pw11','w25','r08','w28','r09','r10',
]

LETTER_TO_IDX = {'A': 0, 'B': 1, 'C': 2, 'D': 3}


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
    if tctm_items is None:
        tctm_items = {}
    for iid in TCTM22_IDS:
        row[f'tctm_{iid}'] = tctm_items.get(iid, '')
    return row


def extract_tctm_items_from_payload(answers):
    items = {}
    for a in answers:
        iid = a.get('itemId', '')
        if iid in TCTM22_IDS:
            items[iid] = 1 if a.get('isCorrect', False) else 0
    return items


def row_from_payload(condition, model, persona, run_num, payload):
    ans = payload['tctm'].get('answers', [])
    # Persona/baseline: strict 22-item filter (paper claims over TCTM-22).
    # Noprompt: looser — some chaotic outputs miss 1-2 items; accept >= 15
    # but reject TCTM-57 outputs (>30 answers).
    if condition == 'noprompt':
        if len(ans) < 15 or len(ans) > 30:
            return None
    else:
        if len(ans) != 22:
            return None
    masc = payload['tctm']['mascProfile']
    ecrr = payload.get('ecrR', {}).get('answers', {})
    ments_a = payload.get('ments', {}).get('answers', {})
    kpp_a = payload.get('kpp', {}).get('answers', {})
    tipi_a = payload.get('tipiPl', {}).get('answers', {})
    d = score_dbzr(ecrr) if len(ecrr) >= 30 else None
    m = score_ments(ments_a) if len(ments_a) >= 20 else None
    k = score_kpp(kpp_a) if len(kpp_a) >= 30 else None
    t = score_tipi(tipi_a) if len(tipi_a) >= 8 else None
    return make_row(condition, model, persona, run_num, masc, len(ans), d, m, k, t,
                    extract_tctm_items_from_payload(ans))


# Re-scorer for chaotic noprompt raw.txt — handles polish keys + list/dict variants
def _unnest(v):
    if isinstance(v, dict) and 'responses' in v and isinstance(v['responses'], dict):
        return v['responses']
    return v


def _list_to_dict_ans(v):
    if isinstance(v, list):
        out = {}
        for it in v:
            if isinstance(it, dict):
                iid = it.get('id') or it.get('itemId')
                ans = (it.get('answer') or it.get('chosenAnswer')
                       or it.get('odpowiedz') or it.get('odpowiedź'))
                if iid and isinstance(ans, str):
                    out[iid] = ans
        return out
    return v


def _normalize_key(k):
    """Lowercase, strip underscores/hyphens/diacritics-related chars."""
    if not isinstance(k, str):
        return ''
    # Replace polish diacritics + garbled cp1250 variants
    repl = (
        ('ą', 'a'), ('Ą', 'a'), ('ć', 'c'), ('Ć', 'c'),
        ('ę', 'e'), ('Ę', 'e'), ('ł', 'l'), ('Ł', 'l'),
        ('ń', 'n'), ('Ń', 'n'), ('ó', 'o'), ('Ó', 'o'),
        ('ś', 's'), ('Ś', 's'), ('ź', 'z'), ('Ź', 'z'),
        ('ż', 'z'), ('Ż', 'z'),
    )
    out = k.lower()
    for src, dst in repl:
        out = out.replace(src, dst)
    # strip non-ascii (garbled bytes from cp1250)
    out = ''.join(c if ord(c) < 128 else '' for c in out)
    return out.replace('_', '').replace('-', '').replace(' ', '')


def _find_by_substring(data, *needles):
    """Find first dict value whose normalized key contains any needle."""
    if not isinstance(data, dict):
        return None
    for k, v in data.items():
        nk = _normalize_key(k)
        if any(n in nk for n in needles):
            return v
    return None


def _dict_of_dict_to_letter(v):
    """If v is {iid: {odpowiedz/answer: 'X', ...}}, flatten to {iid: 'X'}."""
    if not isinstance(v, dict):
        return v
    out = {}
    for k, val in v.items():
        if isinstance(val, str) and len(val) == 1 and val.upper() in 'ABCD':
            out[k] = val
        elif isinstance(val, dict):
            ans = (val.get('answer') or val.get('odpowiedz') or val.get('odpowiedź')
                   or val.get('chosenAnswer'))
            if isinstance(ans, str) and ans.strip().upper() in 'ABCD':
                out[k] = ans.strip().upper()
    return out if out else v


def _list_to_likert(v, prefix=None):
    """If v is list of ints, convert to {1: v[0], 2: v[1], ...} for likert scoring."""
    if isinstance(v, list) and all(isinstance(x, (int, float)) for x in v):
        return {str(i + 1): int(x) for i, x in enumerate(v)}
    return v


def parse_noprompt_raw(raw_path, vignettes_dict):
    """Parse raw.txt → payload-like dict, handling all observed format variants."""
    raw_text = Path(raw_path).read_text(encoding='utf-8')
    raw_clean = re.sub(r'```(?:json)?\s*', '', raw_text)
    raw_clean = re.sub(r'```\s*', '', raw_clean)
    m = re.search(r'\{[\s\S]*\}', raw_clean)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None

    # Find sections by normalized-key substring match. Handles all observed
    # variants: tctm/TCTM22/TCTM57/winiety/vignettes/część_1_winiety, etc.
    tctm_data = _find_by_substring(data, 'tctm', 'winiety', 'vignette')

    # Fallback: top-level keys ARE the TCTM item IDs (no container).
    if not tctm_data:
        vignette_ids = set(vignettes_dict.keys())
        if any(k in vignette_ids for k in data.keys()):
            tctm_data = {k: v for k, v in data.items() if k in vignette_ids}

    # Nested 'responses' for likerts (GPT format: data.responses = {dbz_r: [list], ...})
    responses_section = data.get('responses') if isinstance(data.get('responses'), dict) else {}

    dbzr_data = (_find_by_substring(data, 'dbz', 'ecrr') or
                 _find_by_substring(responses_section, 'dbz', 'ecrr') or {})
    ments_data = (_find_by_substring(data, 'ments') or
                  _find_by_substring(responses_section, 'ments') or {})
    kpp_data = (_find_by_substring(data, 'kpp') or
                _find_by_substring(responses_section, 'kpp') or {})
    tipi_data = (_find_by_substring(data, 'tipi') or
                 _find_by_substring(responses_section, 'tipi') or {})

    tctm_data = _list_to_dict_ans(tctm_data) if tctm_data else {}
    tctm_data = _dict_of_dict_to_letter(tctm_data)

    dbzr_data = _unnest(_list_to_likert(dbzr_data))
    ments_data = _unnest(_list_to_likert(ments_data))
    kpp_data = _unnest(_list_to_likert(kpp_data))
    tipi_data = _unnest(_list_to_likert(tipi_data))

    # Score TCTM
    vignettes = list(vignettes_dict.values())
    tctm_answers = []
    masc = {'correct': 0, 'DOS': 0, 'NAD': 0, 'BK': 0, 'unknown': 0}
    if isinstance(tctm_data, dict):
        for iid, letter in tctm_data.items():
            if not isinstance(letter, str):
                continue
            ci = LETTER_TO_IDX.get(letter.strip().upper(), -1)
            vig = next((v for v in vignettes if v['id'] == iid), None)
            if not vig:
                continue
            ok = (ci == vig['correctAnswer'])
            mt = vig.get('mascTypes', [])
            cm = mt[ci] if 0 <= ci < len(mt) else 'unknown'
            if ok:
                masc['correct'] += 1
            elif cm in masc:
                masc[cm] += 1
            else:
                masc['unknown'] += 1
            tctm_answers.append({
                'itemId': iid,
                'chosenOptionIndex': ci,
                'chosenMascType': cm if not ok else 'correct',
                'isCorrect': ok,
            })

    def parse_likert(data_d, prefix):
        if not isinstance(data_d, dict):
            return {}
        return {f'{prefix}-{int(k):02d}': int(v) for k, v in data_d.items() if str(k).isdigit()}

    return {
        'tctm': {'answers': tctm_answers, 'mascProfile': masc},
        'ecrR': {'answers': parse_likert(dbzr_data, 'ecrr')},
        'ments': {'answers': parse_likert(ments_data, 'ments')},
        'kpp': {'answers': parse_likert(kpp_data, 'kpp')},
        'tipiPl': {'answers': parse_likert(tipi_data, 'tipi')},
    }


def main():
    rows = []
    vignettes_dict = load_tctm_vignettes()

    # === PERSONA ===
    persona_count = 0
    for tag, mn in PERSONA_TAG_TO_LONG.items():
        per_persona = {}
        for f in sorted(OUT_DIR.glob(f'*-{tag}-*.json')):
            if any(x in f.name for x in ['baseline', 'noprompt', '-system.', '-user.', '-raw.']):
                continue
            m = re.match(rf'^(.+?)-{re.escape(tag)}-(\d{{8}}T\d{{6}})\.json$', f.name)
            if not m:
                continue
            persona = m.group(1)
            per_persona.setdefault(persona, []).append(f)

        for persona, files in sorted(per_persona.items()):
            files.sort(key=lambda p: p.name)
            # First pass: load all valid 22-item payloads in chronological order.
            valid = []
            for f in files:
                try:
                    d = json.load(open(f, encoding='utf-8'))
                    ans = d.get('payload', {}).get('tctm', {}).get('answers', [])
                    if len(ans) == 22:
                        valid.append(d)
                except Exception as e:
                    print(f'SKIP persona {f.name}: {e}')
            # Second pass: assign run=1, 2, 3 to chronologically valid runs only.
            for i, d in enumerate(valid):
                row = row_from_payload('persona', mn, persona, i + 1, d['payload'])
                if row:
                    rows.append(row)
                    persona_count += 1

    # === BASELINE ===
    baseline_count = 0
    for tag, mn in BASELINE_TAG_TO_LONG.items():
        rn = 0
        for f in sorted(OUT_DIR.glob(f'baseline-{tag}-*.json')):
            if any(x in f.name for x in ['system', 'user', 'raw']):
                continue
            try:
                d = json.load(open(f, encoding='utf-8'))
                pay = d['payload']
                if len(pay['tctm'].get('answers', [])) < 10:
                    continue
                rn += 1
                row = row_from_payload('baseline', mn, 'self', rn, pay)
                if row:
                    rows.append(row)
                    baseline_count += 1
            except Exception as e:
                print(f'SKIP baseline {f.name}: {e}')

    # === NOPROMPT (from raw.txt — re-score everything) ===
    noprompt_count = 0
    for tag, mn in NOPROMPT_TAG_TO_LONG.items():
        for f in sorted(OUT_DIR.glob(f'noprompt-{tag}-*-raw.txt')):
            ts_match = re.search(r'(\d{8}T\d{6})', f.name)
            if not ts_match:
                continue
            ts = ts_match.group(1)
            payload = parse_noprompt_raw(f, vignettes_dict)
            if payload is None:
                continue
            if payload['tctm']['mascProfile']['correct'] == 0 and not payload['tctm']['answers']:
                # No TCTM parsed → skip (corrupted output)
                continue
            row = row_from_payload('noprompt', mn, f'noprompt-{ts}', 1, payload)
            if row:
                rows.append(row)
                noprompt_count += 1

    # === HUMAN ===
    human_count = 0
    human_path = SCRIPT_DIR / 'human_payloads_full.json'
    if human_path.exists():
        try:
            human_full = json.load(open(human_path, encoding='utf-8'))
            human_rids = list(human_full.keys())
            if len(human_rids) >= 2:
                merged_r01 = json.loads(json.dumps(human_full[human_rids[1]]))
                merged_r01['tctm'] = human_full[human_rids[0]]['tctm']
                row = row_from_payload('human', 'Human', 'R01', 1, merged_r01)
                if row:
                    rows.append(row); human_count += 1
            for i, rid in enumerate(human_rids[2:], start=2):
                row = row_from_payload('human', 'Human', f'R{i:02d}', 1, human_full[rid])
                if row:
                    rows.append(row); human_count += 1
        except Exception as e:
            print(f'human load error: {e}')

    print(f'Built {len(rows)} rows: {persona_count} persona + {baseline_count} baseline + {noprompt_count} noprompt + {human_count} human')

    # By condition / by model breakdown
    from collections import Counter
    by_cond = Counter(r['condition'] for r in rows)
    by_model = Counter(r['model'] for r in rows)
    print(f'By condition: {dict(sorted(by_cond.items()))}')
    print(f'By model: {dict(sorted(by_model.items()))}')

    # WRITE
    fields = list(rows[0].keys())
    with open(CSV_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f'Wrote {CSV_PATH}')


if __name__ == '__main__':
    main()
