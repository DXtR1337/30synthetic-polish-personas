# -*- coding: utf-8 -*-
"""
make_v20_csv.py — zunifikowany CSV v20 ze WSZYSTKICH fal zbierania danych.

NIE dotyka all_data.csv (zamrożony artefakt v19, fale 1–2). Emituje:
  - all_data_v20.csv      : administracja TCTM-22, fale 1–4, schemat v19 (53 kol.) + 'wave'
  - tctm57_runs_v20.csv   : administracja TCTM-57 (kwiecień + fala 5), ten sam schemat + 'wave'
                            (tctm_total=57; kolumny itemowe tylko dla 22 wspólnych pozycji)

Przypisanie fali — OPERACYJNE, po stampie UTC z nazwy pliku (nie po deklaracjach):
  wave 1: stamp <  20260528                  (kolekcja kwietniowo-majowa, 6 modeli)
  wave 2: 20260528 <= stamp < 20260531       (GPT-5.4 full + dosypka baseline'ów)
  wave 3: 20260531 <= stamp < 20260610T22    (re-kolekcja Azure po korekcie renderowania)
  wave 4: stamp >= 20260610T22, admin 22     (re-kolekcja nie-Azure po korekcie)
  wave 5: admin 57 i stamp >= 20260610       (TCTM-57 na poprawionym bodźcu)
  human → wave 1.

Run-numeracja: chronologiczna W OBRĘBIE (model, persona, fala) — run 1/2 w każdej fali.
Konwencje scoringu identyczne z regenerate_all_csv.py (missing-as-wrong, 20–22 odpowiedzi
dla persona/baseline; zero-prompt rescoring z surowców z dodatkową normalizacją ID
'winieta_*' zaobserwowaną w fali 4). Mislabel Gemini c07→'c06' celowo NIE jest
odzyskiwany (wiersz zachowuje scoring payloadu; pozycja c07 = brak = błąd).
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from regenerate_all_csv import (  # noqa: E402
    row_from_payload, TCTM22_IDS, LETTER_TO_IDX,
    _find_by_substring, _list_to_dict_ans, _dict_of_dict_to_letter,
    _list_to_likert, _unnest,
)
from score_noprompt import normalize_item_id  # noqa: E402
from run_synthetic import load_tctm_vignettes  # noqa: E402
import run_synthetic as rs  # noqa: E402

OUT_DIR = SCRIPT_DIR / 'out'
V20_PATH = SCRIPT_DIR / 'all_data_v20.csv'
V20_57_PATH = SCRIPT_DIR / 'tctm57_runs_v20.csv'

PERSONA_TAGS = {
    'sonnet': 'Claude Sonnet 4.6',
    'opus': 'Claude Opus 4.6',
    'gpt54mini': 'GPT-5.4-mini',
    'gpt54f': 'GPT-5.4',
    'gpt55': 'GPT-5.5',
    'grok4': 'Grok-4-20',
    'gemini3f': 'Gemini 3 Flash',
    'gpt55full57': 'GPT-5.5',          # administracja 57 — trafia do drugiego pliku
}
BASELINE_TAGS = {
    'sonnet': 'Claude Sonnet 4.6',
    'opus': 'Claude Opus 4.6',
    'gpt': 'GPT-5.4-mini',
    'gpt54mini': 'GPT-5.4-mini',
    'gpt54f': 'GPT-5.4',
    'gpt55': 'GPT-5.5',
    'grok': 'Grok-4-20',
    'grok4': 'Grok-4-20',
    'gemini': 'Gemini 3 Flash',
}
NOPROMPT_TAGS = dict(BASELINE_TAGS)


def wave_of(stamp, n_answers):
    if n_answers > 30:
        return 5 if stamp >= '20260610' else 1
    if stamp < '20260528':
        return 1
    if stamp < '20260531':
        return 2
    if stamp < '20260610T22':
        return 3
    return 4


def parse_noprompt_raw_v20(raw_path, vignettes_dict):
    """Jak regenerate_all_csv.parse_noprompt_raw + normalizacja ID itemów."""
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

    tctm_data = _find_by_substring(data, 'tctm', 'winiety', 'vignette', 'czesc', 'part1')
    if not tctm_data:
        vignette_ids = set(vignettes_dict.keys())
        if any(k in vignette_ids for k in data.keys()):
            tctm_data = {k: v for k, v in data.items() if k in vignette_ids}

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

    vignettes = list(vignettes_dict.values())
    tctm_answers = []
    masc = {'correct': 0, 'DOS': 0, 'NAD': 0, 'BK': 0, 'unknown': 0}
    if isinstance(tctm_data, dict):
        for iid_raw, letter in tctm_data.items():
            if not isinstance(letter, str):
                continue
            iid = normalize_item_id(iid_raw)
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
            tctm_answers.append({'itemId': iid, 'chosenOptionIndex': ci,
                                 'chosenMascType': cm if not ok else 'correct', 'isCorrect': ok})

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
    rows22, rows57 = [], []
    vig22 = load_tctm_vignettes()
    rs.LOAD_ALL_VIGNETTES = True
    vig57 = load_tctm_vignettes()
    rs.LOAD_ALL_VIGNETTES = False
    print(f'winiety: TCTM-22={len(vig22)}, pula 57={len(vig57)}')

    # === PERSONA (obie administracje) ===
    for tag, mn in PERSONA_TAGS.items():
        per_pw = {}
        for f in sorted(OUT_DIR.glob(f'*-{tag}-*.json')):
            if any(x in f.name for x in ['baseline', 'noprompt', '-system.', '-user.', '-raw.']):
                continue
            m = re.match(rf'^(.+?)-{re.escape(tag)}-(\d{{8}}T\d{{6}})\.json$', f.name)
            if not m:
                continue
            persona, stamp = m.group(1), m.group(2)
            try:
                d = json.load(open(f, encoding='utf-8'))
                ans = d.get('payload', {}).get('tctm', {}).get('answers', [])
            except Exception as e:
                print(f'SKIP persona {f.name}: {e}')
                continue
            n = len(ans)
            if not (20 <= n <= 22 or n > 30):
                continue
            # 'sonnet'-tag łapie też pliki gpt55full57? Nie — tag w nazwie rozdziela.
            w = wave_of(stamp, n)
            per_pw.setdefault((persona, w, n > 30), []).append((stamp, d['payload']))
        for (persona, w, is57), items in sorted(per_pw.items()):
            items.sort(key=lambda x: x[0])
            for i, (stamp, pl) in enumerate(items, 1):
                row = row_from_payload('persona', mn, persona, i, pl)
                if row is None and is57:
                    # row_from_payload odrzuca >22 — zbuduj wiersz 57 ręcznie
                    row = build_57_row(mn, persona, i, pl, vig57)
                if row:
                    row['wave'] = w
                    (rows57 if is57 else rows22).append(row)

    # === BASELINE ===
    for tag, mn in BASELINE_TAGS.items():
        per_wave_rn = Counter()
        for f in sorted(OUT_DIR.glob(f'baseline-{tag}-*.json')):
            if any(x in f.name for x in ['system', 'user', 'raw']):
                continue
            m = re.search(r'(\d{8}T\d{6})', f.name)
            if not m:
                continue
            stamp = m.group(1)
            try:
                d = json.load(open(f, encoding='utf-8'))
                pay = d['payload']
            except Exception as e:
                print(f'SKIP baseline {f.name}: {e}')
                continue
            if len(pay['tctm'].get('answers', [])) < 10:
                continue
            w = wave_of(stamp, len(pay['tctm'].get('answers', [])))
            per_wave_rn[w] += 1
            row = row_from_payload('baseline', mn, 'self', per_wave_rn[w], pay)
            if row:
                row['wave'] = w
                rows22.append(row)

    # === NOPROMPT (re-scoring surowców, z normalizacją ID) ===
    for tag, mn in NOPROMPT_TAGS.items():
        for f in sorted(OUT_DIR.glob(f'noprompt-{tag}-*-raw.txt')):
            ts_match = re.search(r'(\d{8}T\d{6})', f.name)
            if not ts_match:
                continue
            ts = ts_match.group(1)
            payload = parse_noprompt_raw_v20(f, vig22)
            if payload is None:
                continue
            if payload['tctm']['mascProfile']['correct'] == 0 and not payload['tctm']['answers']:
                continue
            row = row_from_payload('noprompt', mn, f'noprompt-{ts}', 1, payload)
            if row:
                row['wave'] = wave_of(ts, len(payload['tctm']['answers']))
                rows22.append(row)

    # === HUMAN (fala 1) ===
    human_path = SCRIPT_DIR / 'human_payloads_full.json'
    if human_path.exists():
        try:
            human_full = json.load(open(human_path, encoding='utf-8'))
            rids = list(human_full.keys())
            if len(rids) >= 2:
                merged = json.loads(json.dumps(human_full[rids[1]]))
                merged['tctm'] = human_full[rids[0]]['tctm']
                row = row_from_payload('human', 'Human', 'R01', 1, merged)
                if row:
                    row['wave'] = 1
                    rows22.append(row)
            for i, rid in enumerate(rids[2:], start=2):
                row = row_from_payload('human', 'Human', f'R{i:02d}', 1, human_full[rid])
                if row:
                    row['wave'] = 1
                    rows22.append(row)
        except Exception as e:
            print(f'human load error: {e}')

    # === RAPORT + ZAPIS ===
    for label, rows, path in (('TCTM-22 (all_data_v20)', rows22, V20_PATH),
                              ('TCTM-57 (tctm57_runs_v20)', rows57, V20_57_PATH)):
        if not rows:
            print(f'{label}: 0 wierszy — pomijam zapis')
            continue
        by_wave = Counter(r['wave'] for r in rows)
        by_cond = Counter(r['condition'] for r in rows)
        by_model = Counter(r['model'] for r in rows)
        print(f'\n{label}: {len(rows)} wierszy')
        print(f'  fale: {dict(sorted(by_wave.items()))}')
        print(f'  warunki: {dict(sorted(by_cond.items()))}')
        print(f'  modele: {dict(sorted(by_model.items()))}')
        fields = [c for c in rows[0].keys() if c != 'wave'] + ['wave']
        with open(path, 'w', newline='', encoding='utf-8-sig') as fh:
            wcsv = csv.DictWriter(fh, fieldnames=fields)
            wcsv.writeheader()
            wcsv.writerows(rows)
        print(f'  zapisano: {path.name}')


def build_57_row(mn, persona, run_num, pl, vig57):
    """Wiersz dla administracji TCTM-57: total=57, kolumny itemowe dla 22 wspólnych."""
    ans = pl['tctm'].get('answers', [])
    masc = pl['tctm']['mascProfile']
    ecrr = pl.get('ecrR', {}).get('answers', {})
    ments_a = pl.get('ments', {}).get('answers', {})
    kpp_a = pl.get('kpp', {}).get('answers', {})
    tipi_a = pl.get('tipiPl', {}).get('answers', {})
    from analyze_and_prepare import score_dbzr, score_ments, score_kpp, score_tipi
    d = score_dbzr(ecrr) if len(ecrr) >= 30 else None
    m = score_ments(ments_a) if len(ments_a) >= 20 else None
    k = score_kpp(kpp_a) if len(kpp_a) >= 30 else None
    t = score_tipi(tipi_a) if len(tipi_a) >= 8 else None
    from regenerate_all_csv import make_row, extract_tctm_items_from_payload
    return make_row('persona', mn, persona, run_num, masc, len(ans), d, m, k, t,
                    extract_tctm_items_from_payload(ans))


if __name__ == '__main__':
    main()
