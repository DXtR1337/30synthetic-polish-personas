"""Apply paper-validated score_dbzr/ments/kpp/tipi to all noprompt raw.txt files.
Uses analyze_and_prepare module (same as _export_csv.py uses).
"""
from __future__ import annotations
import json, re, sys, statistics as st
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from analyze_and_prepare import score_dbzr, score_ments, score_kpp, score_tipi

OUT_DIR = Path(__file__).parent / 'out'

DBZR_KEYS = ['dbz_r','DBZR','DBZ_R','dbz-r','part2_dbzr','part2_dbz_r','part2_DBZ_R','part2_DBZR','dbzr','m_dbz','part2','czesc_2_dbz_r','część_2_dbz_r','czesc2_dbz_r']
MENTS_KEYS = ['ments_pl','MentS_PL','MentSPL','ments-pl','part3_ments_pl','part3_MentS_PL','part3_ments','part3','ments','m_ents_pl','czesc_3_ments_pl','część_3_ments_pl','czesc3_ments_pl','czesc_3_ments']
KPP_KEYS = ['kpp','KPP','part4_kpp','part4_KPP','part4','czesc_4_kpp','część_4_kpp','czesc4_kpp']
TIPI_KEYS = ['tipi_pl','TIPI_PL','TIPIPL','tipi-pl','part5_tipi_pl','part5_TIPI_PL','part5_tipi','part5','tipi','czesc_5_tipi_pl','część_5_tipi_pl','czesc5_tipi_pl','czesc_5_tipi']


def find_array(d, keys, depth=0):
    if depth > 4 or not isinstance(d, dict):
        return None
    for k in keys:
        if k in d:
            v = d[k]
            if isinstance(v, list):
                # Two cases: flat list of ints, or list-of-dicts {"item": N, "answer": V}
                if v and isinstance(v[0], dict):
                    # Sort by item index, extract answer
                    items = []
                    for entry in v:
                        if isinstance(entry, dict):
                            idx = entry.get('item') or entry.get('id') or entry.get('nr')
                            ans = entry.get('answer') or entry.get('odpowiedz') or entry.get('odpowiedź') or entry.get('value')
                            if idx is not None and isinstance(ans, (int, float)):
                                items.append((int(idx), ans))
                    items.sort(key=lambda x: x[0])
                    return [a for _, a in items]
                return v
            if isinstance(v, dict):
                if 'odpowiedzi' in v and isinstance(v['odpowiedzi'], (list, dict)):
                    v = v['odpowiedzi']
                if isinstance(v, dict):
                    nums = sorted(v.keys(), key=lambda x: int(x) if str(x).isdigit() else 0)
                    return [v[n] for n in nums if isinstance(v[n], (int, float))]
                if isinstance(v, list):
                    return v
    for k, v in d.items():
        if isinstance(v, dict):
            r = find_array(v, keys, depth+1)
            if r: return r
    return None


def array_to_dict(arr, prefix):
    return {f'{prefix}-{i+1:02d}': int(v) for i, v in enumerate(arr) if isinstance(v, (int, float))}


def main():
    by_model = {}
    for path in sorted(OUT_DIR.glob('noprompt-*-raw.txt')):
        raw = path.read_text(encoding='utf-8')
        raw = re.sub(r'```(?:json)?\s*', '', raw)
        m = re.search(r'\{[\s\S]*\}', raw)
        if not m: continue
        try: d = json.loads(m.group(0))
        except: continue
        model = path.stem.split('-')[1]
        dbz_arr = find_array(d, DBZR_KEYS)
        ments_arr = find_array(d, MENTS_KEYS)
        kpp_arr = find_array(d, KPP_KEYS)
        tipi_arr = find_array(d, TIPI_KEYS)
        result = {'file': path.stem}
        if dbz_arr and len(dbz_arr) >= 30:
            d = score_dbzr(array_to_dict(dbz_arr, 'ecrr'))
            if d.get('anx_mean', 0) > 0 or d.get('avo_mean', 0) > 0:
                result['dbz'] = d
        if ments_arr and len(ments_arr) >= 20:
            m_ = score_ments(array_to_dict(ments_arr, 'ments'))
            if m_.get('total', 0) > 0:
                result['ments'] = m_
        if kpp_arr and len(kpp_arr) >= 30:
            k_ = score_kpp(array_to_dict(kpp_arr, 'kpp'))
            if k_.get('mean', 0) > 0:
                result['kpp'] = k_
        if tipi_arr and len(tipi_arr) >= 8:
            t_ = score_tipi(array_to_dict(tipi_arr, 'tipi'))
            if any(t_.get(k, 0) > 0 for k in ['E','A','C','ES','O']):
                result['tipi'] = t_
        by_model.setdefault(model, []).append(result)

    for model in ['sonnet','opus','gpt','grok','gemini']:
        runs = by_model.get(model, [])
        print(f'\n=== {model.upper()} (N={len(runs)} runs) ===')
        for r in runs:
            d = r.get('dbz', {}); m_ = r.get('ments', {}); k = r.get('kpp', {}); t = r.get('tipi', {})
            print(f"  {r['file'][:48]:48s} | "
                  f"ANX={d.get('anx_mean','?'):>5} AVO={d.get('avo_mean','?'):>5} style={d.get('style','?'):20s} | "
                  f"MentS={m_.get('total','?'):>4} | KPP={k.get('mean','?'):>5} | "
                  f"E={t.get('E','?')} A={t.get('A','?')} C={t.get('C','?')} ES={t.get('ES','?')} O={t.get('O','?')}")
        # Aggregate
        if not runs: continue
        for field, sub in [('dbz',['anx_mean','avo_mean']), ('ments',['total','self','other','mot']), ('kpp',['mean']), ('tipi',['E','A','C','ES','O'])]:
            vals_per_sub = {s: [r[field][s] for r in runs if field in r and s in r[field]] for s in sub}
            for s, vals in vals_per_sub.items():
                if not vals: continue
                m_v = st.mean(vals); sd_v = st.stdev(vals) if len(vals)>1 else 0
                print(f"  -- {field}.{s}: M={m_v:.2f} SD={sd_v:.2f}  (N={len(vals)}, range [{min(vals):.2f}, {max(vals):.2f}])")


if __name__ == '__main__':
    main()
