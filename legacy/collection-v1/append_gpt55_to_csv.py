# =============================================================================
# ARCHIVAL ONLY -- DO NOT USE TO REPRODUCE THE CORRECTED COLLECTION.
# This is the early-snapshot pipeline (pre-correction serializer, old paths).
# The pipeline actually used for the corrected collections lives in
# /reproduction/synthetic/ (run_wave3/4/5, corrected run_synthetic.py).
# =============================================================================
# -*- coding: utf-8 -*-
"""
Append-only CSV updater for GPT-5.5 runs.

Reads out/*-gpt55-*.json (persona condition) + out/noprompt-gpt55-*.json
(noprompt condition), computes scored rows in the existing all_data.csv
schema, and APPENDS them to all_data.csv. Idempotent: re-running first
strips any existing 'GPT-5.5' rows, then re-appends from out/.

Why a separate script vs editing _export_csv.py: that script is a full
regen from scratch (could clobber human/baseline rows generated outside
of it). This is a targeted append for the new 6th vendor.
"""
import json, csv, re, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from analyze_and_prepare import score_dbzr, score_ments, score_kpp, score_tipi

# Inline-copied from _export_csv.py to avoid triggering _export_csv's main block
# (which would regenerate the entire CSV and clobber historic noprompt rows).
TCTM22_IDS = [
    'w01','s07','s08','s10','w08','c07','c10','w11',
    'w13','w14','e08','w15','w19','pw07','w22','pw09',
    'pw11','w25','r08','w28','r09','r10',
]

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

def extract_tctm_items(answers):
    items = {}
    for a in answers:
        iid = a.get('itemId', '')
        if iid in TCTM22_IDS:
            items[iid] = 1 if a.get('isCorrect', False) else 0
    return items

OUT_DIR = SCRIPT_DIR / 'out'
CSV_PATH = SCRIPT_DIR / 'all_data.csv'

MODEL_LONG = 'GPT-5.5'


def add_row_from_payload(condition, persona, run_num, payload):
    ans = payload['tctm'].get('answers', [])
    if len(ans) < 10:
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
    return make_row(condition, MODEL_LONG, persona, run_num, masc, len(ans), d, m, k, t, extract_tctm_items(ans))


def main():
    new_rows = []

    # PERSONA runs (group by persona, sort chronologically → run 1, 2, ...)
    persona_files = {}
    for f in sorted(OUT_DIR.glob('*-gpt55-*.json')):
        if any(x in f.name for x in ['baseline', 'noprompt', 'system', 'user', 'raw']):
            continue
        m = re.match(r'^(.+?)-gpt55-(\d{8}T\d{6})\.json$', f.name)
        if not m:
            continue
        persona = m.group(1)
        persona_files.setdefault(persona, []).append(f)

    persona_count = 0
    for persona, files in sorted(persona_files.items()):
        files.sort(key=lambda p: p.name)  # chronological by timestamp
        for i, f in enumerate(files):
            try:
                d = json.load(open(f, encoding='utf-8'))
                row = add_row_from_payload('persona', persona, i + 1, d['payload'])
                if row:
                    new_rows.append(row)
                    persona_count += 1
            except Exception as e:
                print(f'SKIP {f.name}: {e}')

    # NOPROMPT runs (each file = one independent noprompt try, persona='noprompt-{ts}')
    noprompt_count = 0
    for f in sorted(OUT_DIR.glob('noprompt-gpt55-*.json')):
        m = re.search(r'(\d{8}T\d{6})', f.name)
        if not m:
            continue
        persona = f'noprompt-{m.group(1)}'
        try:
            d = json.load(open(f, encoding='utf-8'))
            row = add_row_from_payload('noprompt', persona, 1, d['payload'])
            if row:
                new_rows.append(row)
                noprompt_count += 1
        except Exception as e:
            print(f'SKIP {f.name}: {e}')

    print(f'Built {len(new_rows)} GPT-5.5 rows ({persona_count} persona + {noprompt_count} noprompt)')

    # Read existing CSV
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        existing = list(reader)

    existing_before = len(existing)
    existing = [r for r in existing if r.get('model') != MODEL_LONG]
    purged = existing_before - len(existing)
    if purged > 0:
        print(f'Purged {purged} existing {MODEL_LONG} rows before re-append')

    all_rows = existing + new_rows
    print(f'Final CSV: {len(all_rows)} rows ({len(existing)} non-GPT-5.5 + {len(new_rows)} new {MODEL_LONG})')

    # Write
    with open(CSV_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)

    print(f'Wrote {CSV_PATH}')


if __name__ == '__main__':
    main()
