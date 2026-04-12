# -*- coding: utf-8 -*-
"""Pelna analiza statystyczna TCTM-57 (N=30 syntetycznych respondentow)."""
import json, math, statistics
from pathlib import Path
from collections import Counter, defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
OUT = SCRIPT_DIR / 'out'

LEVEL_RANK = {
    'very_low': -2, 'low': -1, 'low_moderate': -0.5, 'moderate_low': -0.5,
    'moderate': 0, 'moderate_high': 0.5, 'high': 1, 'very_high': 2, 'extreme': 2.5,
}

SUBSCALE_TOTALS = {'subtext': 11, 'court': 12, 'eks': 11, 'pursuit': 12, 'repair': 11}
SUBSCALE_LABELS = {
    'subtext': 'Rozpoznawanie ukrytych znaczen',
    'court': 'Rozpoznawanie manipulacji',
    'eks': 'Wykrywanie wygasania relacji',
    'pursuit': 'Dynamika dazenia-wycofywania',
    'repair': 'Ocena naprawy relacyjnej',
}


def pearson_r(xs, ys):
    n = len(xs)
    if n < 3:
        return (float('nan'), float('nan'))
    mx, my = sum(xs)/n, sum(ys)/n
    num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x-mx)**2 for x in xs))
    dy = math.sqrt(sum((y-my)**2 for y in ys))
    if dx == 0 or dy == 0:
        return (float('nan'), float('nan'))
    r = num / (dx * dy)
    if abs(r) >= 1:
        return (r, 0.0)
    t = r * math.sqrt((n-2)/(1-r*r))
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
    return (r, p)


def load_data():
    data = []
    for f in sorted(OUT.glob('*-sonnet-20260412T04*.json')):
        r = json.loads(f.read_text(encoding='utf-8'))
        n_tctm = len(r['payload']['tctm']['answers'])
        if n_tctm < 50:
            continue
        mp = r['payload']['tctm']['mascProfile']
        raw = r['payload']['tctm'].get('rawScores', {})
        data.append({
            'persona': r['persona_id'],
            'correct': mp['correct'],
            'DOS': mp['DOS'],
            'NAD': mp['NAD'],
            'BK': mp['BK'],
            'total_errors': mp['DOS'] + mp['NAD'] + mp['BK'],
            'n': n_tctm,
            'raw_scores': raw,
        })
    # Deduplicate
    seen = {}
    for d in data:
        seen[d['persona']] = d
    return sorted(seen.values(), key=lambda x: x['correct'])


def load_expected():
    summary = {}
    for line in open(SCRIPT_DIR / 'analysis_summary.jsonl', encoding='utf-8'):
        if line.strip():
            s = json.loads(line)
            summary[s['persona_id']] = s
    return summary


def fmt_p(p):
    if math.isnan(p): return '      ---'
    if p < 0.001: return '  < 0.001'
    return f'   {p:.4f}'


def main():
    data = load_data()
    expected = load_expected()
    N = len(data)

    correct_vals = [d['correct'] for d in data]
    nad_vals = [d['NAD'] for d in data]
    dos_vals = [d['DOS'] for d in data]
    bk_vals = [d['BK'] for d in data]
    err_vals = [d['total_errors'] for d in data]

    print('=' * 72)
    print(f'ANALIZA STATYSTYCZNA TCTM-57  (N = {N} syntetycznych respondentow)')
    print('=' * 72)
    print()

    # 1. Descriptive
    m, sd = statistics.mean(correct_vals), statistics.stdev(correct_vals)
    print('-' * 72)
    print('1. STATYSTYKI OPISOWE - WYNIK OGOLNY')
    print('-' * 72)
    print(f'  M = {m:.2f}, SD = {sd:.2f}')
    print(f'  Min = {min(correct_vals)}, Max = {max(correct_vals)}, Rozstep = {max(correct_vals)-min(correct_vals)}')
    print(f'  Mediana = {statistics.median(correct_vals):.1f}')
    print(f'  CV = {sd/m*100:.1f}%')
    print(f'  Accuracy = {m/57*100:.1f}%')
    print()

    # 2. MASC aggregate
    total_items = N * 57
    print('-' * 72)
    print(f'2. PROFIL BLEDOW MASC (N x 57 = {total_items} odpowiedzi)')
    print('-' * 72)
    for label, vals in [('Correct', correct_vals), ('DOS', dos_vals), ('NAD', nad_vals), ('BK', bk_vals)]:
        s = sum(vals)
        print(f'  {label:10s}: {s:5d}/{total_items} ({s/total_items*100:.1f}%)')
    print()

    # 3. Per-persona error stats
    print('-' * 72)
    print('3. TYPY BLEDOW (per persona)')
    print('-' * 72)
    for label, vals in [('Total errors', err_vals), ('NAD', nad_vals), ('DOS', dos_vals), ('BK', bk_vals)]:
        m2, sd2 = statistics.mean(vals), statistics.stdev(vals)
        print(f'  {label:14s}: M = {m2:.2f}, SD = {sd2:.2f}, min = {min(vals)}, max = {max(vals)}')
    print()

    # 4. Distribution
    print('-' * 72)
    print('4. ROZKLAD WYNIKOW')
    print('-' * 72)
    dist = Counter(correct_vals)
    for k in sorted(dist):
        print(f'  {k}/57: n={dist[k]:2d}  {"#" * dist[k]}')
    print()

    # 5. Per category
    print('-' * 72)
    print(f'5. WYNIKI PER KATEGORIA (N={N})')
    print('-' * 72)
    for sub in ['subtext', 'court', 'eks', 'pursuit', 'repair']:
        vals_sub = [d['raw_scores'].get(sub, 0) for d in data]
        total_sub = SUBSCALE_TOTALS[sub]
        m_sub, sd_sub = statistics.mean(vals_sub), statistics.stdev(vals_sub)
        print(f'  {SUBSCALE_LABELS[sub]:40s}: M={m_sub:.1f}/{total_sub} ({m_sub/total_sub*100:.0f}%), SD={sd_sub:.2f}, [{min(vals_sub)}-{max(vals_sub)}]')
    print()

    # 6. Full table
    print('-' * 72)
    print('6. TABELA PELNA')
    print('-' * 72)
    header = f'{"Persona":15s} {"Corr":>4s} {"DOS":>4s} {"NAD":>4s} {"BK":>3s} {"Err":>3s}  sub  crt  eks  pur  rep'
    print(header)
    print('-' * len(header))
    for d in data:
        rs = d['raw_scores']
        print(f'{d["persona"]:15s} {d["correct"]:4d} {d["DOS"]:4d} {d["NAD"]:4d} {d["BK"]:3d} {d["total_errors"]:3d}  {rs.get("subtext",0):3d}  {rs.get("court",0):3d}  {rs.get("eks",0):3d}  {rs.get("pursuit",0):3d}  {rs.get("repair",0):3d}')
    print()

    # 7. Correlations
    print('-' * 72)
    print('7. KORELACJE Z OCZEKIWANYMI PROFILAMI')
    print('-' * 72)

    valid = []
    for d in data:
        pid = d['persona']
        if pid not in expected:
            continue
        ep = expected[pid]['expected_profile']
        valid.append({
            **d,
            'anx_rank': LEVEL_RANK.get(ep.get('dbz_anxiety', ''), None),
            'avo_rank': LEVEL_RANK.get(ep.get('dbz_avoidance', ''), None),
            'ments_self_rank': LEVEL_RANK.get(ep.get('ments_self', ''), None),
            'ments_other_rank': LEVEL_RANK.get(ep.get('ments_other', ''), None),
        })
    valid = [v for v in valid if v['anx_rank'] is not None]

    tests = [
        ('H1:  Lek x Total correct',     'anx_rank', 'correct'),
        ('H2:  Unikanie x Total correct', 'avo_rank', 'correct'),
        ('H3:  MentS-O x Total correct',  'ments_other_rank', 'correct'),
        ('H1a: Lek x Liczba NAD',         'anx_rank', 'NAD'),
        ('H2a: Unikanie x Liczba DOS',    'avo_rank', 'DOS'),
        ('---  Lek x Liczba DOS',         'anx_rank', 'DOS'),
        ('---  Unikanie x Liczba NAD',    'avo_rank', 'NAD'),
        ('---  MentS-Self x Total',       'ments_self_rank', 'correct'),
        ('---  MentS-O x Total errors',   'ments_other_rank', 'total_errors'),
    ]

    for label, x_key, y_key in tests:
        xs = [v[x_key] for v in valid]
        ys = [v[y_key] for v in valid]
        r, p = pearson_r(xs, ys)
        sig = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else ''))
        print(f'  {label:38s}: r = {r:+.3f}, p ={fmt_p(p)} {sig}')
    print()

    # 8. Contrasts
    print('-' * 72)
    print('8. KONTRASTY HIGH vs LOW (ranga >= 1 vs <= -1)')
    print('-' * 72)

    contrasts = [
        ('Lek -> Total correct', 'anx_rank', 'correct'),
        ('Lek -> NAD', 'anx_rank', 'NAD'),
        ('Unikanie -> Total correct', 'avo_rank', 'correct'),
        ('Unikanie -> DOS', 'avo_rank', 'DOS'),
        ('MentS-O -> Total correct', 'ments_other_rank', 'correct'),
        ('MentS-O -> Total errors', 'ments_other_rank', 'total_errors'),
    ]

    for label, rank_key, val_key in contrasts:
        high = [v[val_key] for v in valid if v[rank_key] >= 1]
        low = [v[val_key] for v in valid if v[rank_key] <= -1]
        if len(high) < 2 or len(low) < 2:
            print(f'  {label:35s}: n_high={len(high)}, n_low={len(low)} (za malo)')
            continue
        mh, ml = statistics.mean(high), statistics.mean(low)
        sh, sl = statistics.stdev(high), statistics.stdev(low)
        pooled = math.sqrt(((len(high)-1)*sh**2 + (len(low)-1)*sl**2) / (len(high)+len(low)-2))
        d_cohen = (mh - ml) / pooled if pooled > 0 else float('nan')
        print(f'  {label:35s}: M_H={mh:.1f} (n={len(high)}), M_L={ml:.1f} (n={len(low)}), d={d_cohen:+.2f}')

    # 9. TCTM-22 vs TCTM-57 comparison
    print()
    print('-' * 72)
    print('9. POROWNANIE TCTM-22 vs TCTM-57')
    print('-' * 72)
    # Load TCTM-22 data from stats_output.json
    s22 = json.loads((SCRIPT_DIR / 'stats_output.json').read_text(encoding='utf-8'))
    t22 = s22['tctm']
    print(f'  {"Metryka":25s} {"TCTM-22":>12s} {"TCTM-57":>12s}')
    print(f'  {"-"*25} {"-"*12} {"-"*12}')
    print(f'  {"M (correct)":25s} {t22["mean_correct"]:12.2f} {m:12.2f}')
    print(f'  {"SD":25s} {t22["sd_correct"]:12.2f} {sd:12.2f}')
    print(f'  {"CV":25s} {t22["cv"]*100:11.1f}% {sd/m*100:11.1f}%')
    print(f'  {"Min-Max":25s} {t22["min_correct"]:5d}-{t22["max_correct"]:<6d} {min(correct_vals):5d}-{max(correct_vals):<6d}')
    print(f'  {"Rozstep":25s} {t22["max_correct"]-t22["min_correct"]:12d} {max(correct_vals)-min(correct_vals):12d}')
    print(f'  {"Accuracy":25s} {t22["accuracy_pct"]:11.1f}% {m/57*100:11.1f}%')
    print(f'  {"NAD max":25s} {max(int(s22["tctm_items"][vid]["NAD"]) for vid in s22["tctm_items"]):12d} {max(nad_vals):12d}')

    # Per-category comparison
    print()
    print(f'  Per kategoria (accuracy):')
    for sub in ['subtext', 'court', 'eks', 'pursuit', 'repair']:
        c22 = s22['tctm_per_category'][sub]
        vals_57 = [d['raw_scores'].get(sub, 0) for d in data]
        m_57 = statistics.mean(vals_57)
        acc_22 = c22['accuracy'] * 100
        acc_57 = m_57 / SUBSCALE_TOTALS[sub] * 100
        print(f'    {SUBSCALE_LABELS[sub]:40s}: {acc_22:5.1f}% -> {acc_57:5.1f}%')

    print()
    print('=' * 72)
    print('KONIEC ANALIZY')
    print('=' * 72)


if __name__ == '__main__':
    main()
