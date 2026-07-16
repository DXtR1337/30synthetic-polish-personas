"""
analyze_and_prepare.py

Dla każdej persony:
  1. Wczytaj out/<persona>-*.json (najnowszy wynik Bedrocka)
  2. Wczytaj <persona>.md i wyparsuj frontmatter (persona_version, expected_profile, author_note)
  3. Oblicz DBZ-R, MentS, KPP, TIPI, TCTM (identycznie jak MagisterkaClient.tsx)
  4. Przypisz predicted_attachment_style + zaznacz dopasowanie do expected
  5. Zapisz zbiorczy JSONL: analysis_summary.jsonl (do batch insertu + do analizy)
  6. Zapisz ludzką tabelę: analysis_table.md

Norma Lubiewska/Jańczak + Matusz + Sorokowska — identycznie jak w klientowym scoringu.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / 'out'

# ---------- Normy + reverse sets (1:1 z MagisterkaClient.tsx) ----------

DBZR_REV_ANX = {9, 11}
DBZR_REV_AVO = {20, 22, 26, 27, 28, 29, 30, 31, 33, 34, 35, 36}
# Normy Jańczak 2021 Tabela 1 (N=431)
DBZR_ANX_M, DBZR_ANX_SD = 3.30, 1.21
DBZR_AVO_M, DBZR_AVO_SD = 3.04, 0.96

MENTS_REV = {8, 9, 11, 14, 18, 19, 21, 22, 26, 27}
MENTS_SELF  = [8, 11, 14, 18, 19, 21, 22, 26]
MENTS_OTHER = [2, 3, 5, 6, 10, 12, 20, 23, 25, 28]
MENTS_MOT   = [1, 4, 7, 9, 13, 15, 16, 17, 24, 27]
# Jańczak 2021 Table 1 norms (N=431)
MENTS_SELF_M, MENTS_SELF_SD   = 27.9, 5.8
MENTS_OTHER_M, MENTS_OTHER_SD = 38.2, 5.6
MENTS_MOT_M, MENTS_MOT_SD     = 38.8, 6.35
MENTS_TOT_M, MENTS_TOT_SD     = 105.0, 13.7

KPP_REV = {2, 3, 8, 10, 13, 15, 17, 19, 22, 26, 28, 33, 34, 35}
# Matusz 2011 — norma studentów magisterskich (najbliższa pilotowi)
KPP_MEAN_M, KPP_MEAN_SD = 3.742, 0.489  # pochodne z M_sum=134.7, SD_sum=17.6, /36 items

# Sorokowska 2014 TIPI-PL normy ważone (N=1056)
TIPI_NORMS = {
    'E':  {'m': 5.56, 'sd': 1.36},
    'A':  {'m': 5.28, 'sd': 1.17},
    'C':  {'m': 5.09, 'sd': 1.43},
    'ES': {'m': 4.36, 'sd': 1.56},
    'O':  {'m': 5.01, 'sd': 1.14},
}
TIPI_KEY = {
    'tipi-01': ('E',  False),
    'tipi-02': ('A',  True),
    'tipi-03': ('C',  False),
    'tipi-04': ('ES', True),
    'tipi-05': ('O',  False),
    'tipi-06': ('E',  True),
    'tipi-07': ('A',  False),
    'tipi-08': ('C',  True),
    'tipi-09': ('ES', False),
    'tipi-10': ('O',  True),
}


def score_dbzr(answers: Dict[str, int]) -> Dict[str, Any]:
    anx_sum = anx_n = avo_sum = avo_n = 0
    for i in range(1, 37):
        key = f'ecrr-{i:02d}'
        raw = answers.get(key)
        if raw is None:
            continue
        if i <= 18:
            score = 8 - raw if i in DBZR_REV_ANX else raw
            anx_sum += score
            anx_n += 1
        else:
            score = 8 - raw if i in DBZR_REV_AVO else raw
            avo_sum += score
            avo_n += 1
    anx_mean = anx_sum / anx_n if anx_n else 0
    avo_mean = avo_sum / avo_n if avo_n else 0
    z_anx = (anx_mean - DBZR_ANX_M) / DBZR_ANX_SD
    z_avo = (avo_mean - DBZR_AVO_M) / DBZR_AVO_SD
    anx_high = anx_mean >= 4
    avo_high = avo_mean >= 4
    if not anx_high and not avo_high:
        style = 'secure'
        style_pl = 'Bezpieczny'
    elif anx_high and not avo_high:
        style = 'anxious_preoccupied'
        style_pl = 'Lękowo-ambiwalentny'
    elif not anx_high and avo_high:
        style = 'dismissive_avoidant'
        style_pl = 'Unikający'
    else:
        style = 'fearful_avoidant'  # disorganized
        style_pl = 'Zdezorganizowany'
    return {
        'anx_mean': round(anx_mean, 3),
        'avo_mean': round(avo_mean, 3),
        'z_anx': round(z_anx, 3),
        'z_avo': round(z_avo, 3),
        'style': style,
        'style_pl': style_pl,
    }


def score_ments(answers: Dict[str, int]) -> Dict[str, Any]:
    def sum_for(nums: List[int]) -> int:
        s = 0
        for n in nums:
            key = f'ments-{n:02d}'
            raw = answers.get(key)
            if raw is None:
                continue
            score = 6 - raw if n in MENTS_REV else raw
            s += score
        return s
    self_ = sum_for(MENTS_SELF)
    other = sum_for(MENTS_OTHER)
    mot   = sum_for(MENTS_MOT)
    total = self_ + other + mot
    return {
        'self':  self_,
        'other': other,
        'mot':   mot,
        'total': total,
        'z_self':  round((self_ - MENTS_SELF_M) / MENTS_SELF_SD, 3),
        'z_other': round((other - MENTS_OTHER_M) / MENTS_OTHER_SD, 3),
        'z_mot':   round((mot - MENTS_MOT_M) / MENTS_MOT_SD, 3),
        'z_total': round((total - MENTS_TOT_M) / MENTS_TOT_SD, 3),
    }


def score_kpp(answers: Dict[str, int]) -> Dict[str, Any]:
    s = n = 0
    for i in range(1, 37):
        key = f'kpp-{i:02d}'
        raw = answers.get(key)
        if raw is None:
            continue
        score = 6 - raw if i in KPP_REV else raw
        s += score
        n += 1
    mean = s / n if n else 0
    z_mean = (mean - KPP_MEAN_M) / KPP_MEAN_SD
    if mean < 3.0:
        band = 'Niska'
    elif mean < 3.8:
        band = 'Średnia'
    else:
        band = 'Wysoka'
    return {
        'sum':    s,
        'n':      n,
        'mean':   round(mean, 3),
        'z_mean': round(z_mean, 3),
        'band':   band,
    }


def score_tipi(answers: Dict[str, int]) -> Dict[str, Any]:
    sums = {'E': 0.0, 'A': 0.0, 'C': 0.0, 'ES': 0.0, 'O': 0.0}
    counts = {'E': 0, 'A': 0, 'C': 0, 'ES': 0, 'O': 0}
    for key, (trait, rev) in TIPI_KEY.items():
        raw = answers.get(key)
        if raw is None:
            continue
        score = 8 - raw if rev else raw
        sums[trait] += score
        counts[trait] += 1
    means = {t: (sums[t] / counts[t] if counts[t] else 0) for t in sums}
    out: Dict[str, Any] = {}
    for t in ('E', 'A', 'C', 'ES', 'O'):
        out[t] = round(means[t], 3)
        norm = TIPI_NORMS[t]
        out[f'z_{t}'] = round((means[t] - norm['m']) / norm['sd'], 3)
    return out


# ---------- Frontmatter parser ----------

def parse_frontmatter(md_path: Path) -> Dict[str, Any]:
    text = md_path.read_text(encoding='utf-8')
    if not text.startswith('---'):
        return {}
    end = text.find('\n---', 3)
    if end == -1:
        return {}
    fm_raw = text[3:end].strip()
    # Very narrow YAML parser — persona_id, persona_version, expected_profile, author_note
    result: Dict[str, Any] = {}
    lines = fm_raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith('#'):
            i += 1
            continue
        if line.startswith('expected_profile:'):
            # Capture indented block
            ep: Dict[str, str] = {}
            i += 1
            while i < len(lines) and (lines[i].startswith('  ') or not lines[i].strip()):
                sub = lines[i].strip()
                if sub and ':' in sub:
                    k, v = sub.split(':', 1)
                    ep[k.strip()] = v.strip()
                i += 1
            result['expected_profile'] = ep
            continue
        if line.startswith('author_note:'):
            # Skip block scalar — not needed downstream
            i += 1
            while i < len(lines) and (lines[i].startswith('  ') or not lines[i].strip()):
                i += 1
            continue
        m = re.match(r'^([a-z_]+):\s*(.*)$', line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if v.isdigit():
                result[k] = int(v)
            else:
                result[k] = v
        i += 1
    return result


# ---------- Pipeline ----------

def latest_output_for(persona: str) -> Optional[Path]:
    matches = sorted(OUT_DIR.glob(f'{persona}-*.json'))
    # exclude -system.txt / -user.txt / -raw.txt — pure *.json only
    matches = [m for m in matches if not m.name.endswith(('-system.txt', '-user.txt', '-raw.txt'))]
    return matches[-1] if matches else None


def map_expected_style(raw: str) -> str:
    """Map frontmatter style label to canonical DBZ-R style key."""
    raw = (raw or '').lower().strip()
    mapping = {
        'secure': 'secure',
        'anxious_preoccupied': 'anxious_preoccupied',
        'preoccupied': 'anxious_preoccupied',
        'anxious': 'anxious_preoccupied',
        'dismissive_avoidant': 'dismissive_avoidant',
        'dismissive': 'dismissive_avoidant',
        'avoidant': 'dismissive_avoidant',
        'fearful_avoidant': 'fearful_avoidant',
        'fearful': 'fearful_avoidant',
        'disorganized': 'fearful_avoidant',
    }
    return mapping.get(raw, raw)


def process_persona(persona: str) -> Optional[Dict[str, Any]]:
    bio_path = SCRIPT_DIR / f'{persona}.md'
    if not bio_path.exists():
        print(f'[{persona}] BRAK biografii {bio_path}')
        return None
    out_path = latest_output_for(persona)
    if not out_path:
        print(f'[{persona}] BRAK outputu Bedrocka')
        return None

    fm = parse_frontmatter(bio_path)
    expected_profile = fm.get('expected_profile', {})
    expected_style_raw = expected_profile.get('attachment_style', '')
    expected_style = map_expected_style(expected_style_raw)

    result = json.loads(out_path.read_text(encoding='utf-8'))
    payload = result['payload']

    ecrr_answers = payload['ecrR']['answers']
    ments_answers = payload['ments']['answers']
    kpp_answers = payload['kpp']['answers']
    tipi_answers = payload['tipiPl']['answers']

    dbzr = score_dbzr(ecrr_answers)
    ments = score_ments(ments_answers)
    kpp = score_kpp(kpp_answers)
    tipi = score_tipi(tipi_answers)

    tctm_raw = payload['tctm']
    masc_profile = tctm_raw.get('mascProfile', {})
    tctm_correct = masc_profile.get('correct', 0)
    tctm_dos = masc_profile.get('DOS', 0)
    tctm_nad = masc_profile.get('NAD', 0)
    tctm_bk = masc_profile.get('BK', 0)

    predicted_style = dbzr['style']
    attachment_match = predicted_style == expected_style if expected_style else None

    summary = {
        'persona_id': persona,
        'persona_version': result.get('persona_version', fm.get('persona_version', 1)),
        'biography_length': result.get('biography_length'),
        'expected_profile': expected_profile,
        'expected_style': expected_style,
        'model_name': result.get('model_name'),
        'model_stop_reason': result.get('model_stop_reason'),
        'tokens_input': result.get('tokens_input'),
        'tokens_output': result.get('tokens_output'),
        'respondent_id': result['respondent_id'],
        'predicted_style': predicted_style,
        'attachment_match': attachment_match,
        'dbzr': dbzr,
        'ments': ments,
        'kpp': kpp,
        'tipi': tipi,
        'tctm': {
            'correct': tctm_correct,
            'DOS': tctm_dos,
            'NAD': tctm_nad,
            'BK': tctm_bk,
            'total': tctm_correct + tctm_dos + tctm_nad + tctm_bk,
        },
        'payload': payload,  # zachowujemy do inserta do Supabase
        'completed_at': payload.get('completedAt'),
    }
    return summary


PERSONAS = [
    'michal-sim', 'anna-sim', 'piotr', 'kasia', 'jakub', 'ania', 'marek', 'ola',
    'tomek', 'natalia', 'filip', 'magda', 'kuba', 'ewa', 'pawel', 'weronika',
    'adrian', 'zuzia', 'hubert', 'jola', 'radek', 'dominika', 'bartek', 'agata',
    'lukasz', 'klaudia', 'kamil', 'gabriela', 'michal-k', 'sara',
]


def main() -> None:
    summaries: List[Dict[str, Any]] = []
    for p in PERSONAS:
        s = process_persona(p)
        if s:
            summaries.append(s)

    # Zapis zbiorczy JSONL (do batch inserta do Supabase)
    jsonl_path = SCRIPT_DIR / 'analysis_summary.jsonl'
    with jsonl_path.open('w', encoding='utf-8') as f:
        for s in summaries:
            f.write(json.dumps(s, ensure_ascii=False) + '\n')
    print(f'Zapisano {len(summaries)} podsumowań do {jsonl_path}')

    # Human-readable tabela
    table_path = SCRIPT_DIR / 'analysis_table.md'
    with table_path.open('w', encoding='utf-8') as f:
        f.write('# Synthetic personas — porównanie profili (N=30)\n\n')
        f.write('## Style przywiązania (DBZ-R)\n\n')
        f.write('| Persona | Expected | Predicted | Match | z(Lęk) | z(Unik) |\n')
        f.write('|---|---|---|---|---|---|\n')
        hits = 0
        for s in summaries:
            mark = '✓' if s['attachment_match'] else '✗' if s['attachment_match'] is False else '?'
            if s['attachment_match']:
                hits += 1
            f.write(f"| {s['persona_id']} | {s['expected_style']} | {s['predicted_style']} | {mark} | {s['dbzr']['z_anx']:+.2f} | {s['dbzr']['z_avo']:+.2f} |\n")
        f.write(f'\n**Hit rate:** {hits}/{len(summaries)} = {hits/len(summaries):.1%}\n\n')

        f.write('## MentS — mentalizacja (z-scores)\n\n')
        f.write('| Persona | Expected self | Expected other | Expected mot | z(Self) | z(Other) | z(Mot) | z(Total) |\n')
        f.write('|---|---|---|---|---|---|---|---|\n')
        for s in summaries:
            ep = s['expected_profile']
            f.write(f"| {s['persona_id']} | {ep.get('ments_self','?')} | {ep.get('ments_other','?')} | {ep.get('ments_motivation','?')} | {s['ments']['z_self']:+.2f} | {s['ments']['z_other']:+.2f} | {s['ments']['z_mot']:+.2f} | {s['ments']['z_total']:+.2f} |\n")

        f.write('\n## KPP — kompetencje personalne\n\n')
        f.write('| Persona | Expected | Mean | z | Band |\n')
        f.write('|---|---|---|---|---|\n')
        for s in summaries:
            ep = s['expected_profile']
            f.write(f"| {s['persona_id']} | {ep.get('kpp','?')} | {s['kpp']['mean']:.2f} | {s['kpp']['z_mean']:+.2f} | {s['kpp']['band']} |\n")

        f.write('\n## TIPI-PL — Big Five\n\n')
        f.write('| Persona | z(E) | z(A) | z(C) | z(ES) | z(O) |\n')
        f.write('|---|---|---|---|---|---|\n')
        for s in summaries:
            t = s['tipi']
            f.write(f"| {s['persona_id']} | {t['z_E']:+.2f} | {t['z_A']:+.2f} | {t['z_C']:+.2f} | {t['z_ES']:+.2f} | {t['z_O']:+.2f} |\n")

        f.write('\n## TCTM-22 — MASC profile\n\n')
        f.write('| Persona | Correct | DOS (under) | NAD (over) | BK (none) |\n')
        f.write('|---|---|---|---|---|\n')
        for s in summaries:
            tc = s['tctm']
            f.write(f"| {s['persona_id']} | {tc['correct']}/{tc['total']} | {tc['DOS']} | {tc['NAD']} | {tc['BK']} |\n")
    print(f'Zapisano tabelę do {table_path}')


if __name__ == '__main__':
    main()
