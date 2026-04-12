"""
stats.py — pełna analiza statystyczna syntetycznego eksperymentu N=30.

Oblicza (replikując + rozszerzając analizę raportu pilotażowego N=2):
  1. Confusion matrix + hit rate z 95% CI (Wilson)
  2. Cohen's kappa dla stylu przywiązania (4 kategorie)
  3. Korelacje Pearson/Spearman: expected_rank vs observed z-score dla każdej skali
  4. Welch t-tests + Cohen's d (high vs low per wymiar)
  5. Efekt sufitu TCTM (M, SD, CV) + rozkład
  6. Per-item TCTM analysis: p (trudność), typ błędu dominującego, dyskryminacja
  7. Per-category TCTM accuracy (subtext / court / eks / pursuit / repair)
  8. POZ/TRAP second coding layer: NB (negative bias) i OR (over-reading) per persona
  9. Hipoteza pilotu: korelacja Ugodowość (TIPI-A) vs trafność w kategorii Repair
 10. Test spójności profilu z literaturą — 10 par konstruktów, per-persona consistency
 11. Mean pairwise euclidean distance profiles w 12-wymiarowej przestrzeni z-scorów
 12. Gemini vs Sonnet kontrast (Agata)

Wszystko zapisuje do stats_output.json + tabele LaTeX do stats_tables.tex.
"""

from __future__ import annotations
import json
import math
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = SCRIPT_DIR / 'analysis_summary.jsonl'
OUT_JSON = SCRIPT_DIR / 'stats_output.json'
OUT_TEX = SCRIPT_DIR / 'stats_tables.tex'

# ========== HELPERS ==========

LEVEL_RANK = {
    'very_low': -2, 'low': -1, 'low_moderate': -0.5, 'moderate_low': -0.5,
    'moderate': 0,
    'moderate_high': 0.5, 'high': 1, 'very_high': 2, 'extreme': 2.5,
}


def level_to_rank(level: str | None) -> float | None:
    if level is None:
        return None
    return LEVEL_RANK.get(level.strip(), None)


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval for proportion."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.959963984540054  # 95% normal
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    halfw = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (max(0, center - halfw), min(1, center + halfw))


def pearson(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Returns (r, two-sided p-value via t-test)."""
    n = len(xs)
    if n < 3:
        return (float('nan'), float('nan'))
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))
    if denx == 0 or deny == 0:
        return (float('nan'), float('nan'))
    r = num / (denx * deny)
    # t = r * sqrt((n-2)/(1-r^2))
    if abs(r) >= 1.0:
        return (r, 0.0)
    t = r * math.sqrt((n - 2) / (1 - r * r))
    # Two-tailed p via Student t CDF approximation (Abramowitz)
    p = t_two_sided_p(t, n - 2)
    return (r, p)


def spearman(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Spearman ρ via rank Pearson."""
    def rank(arr: list[float]) -> list[float]:
        # Average ranks for ties
        order = sorted(range(len(arr)), key=lambda i: arr[i])
        ranks = [0.0] * len(arr)
        i = 0
        while i < len(arr):
            j = i
            while j < len(arr) and arr[order[j]] == arr[order[i]]:
                j += 1
            avg = (i + j - 1) / 2 + 1  # 1-indexed average rank
            for k in range(i, j):
                ranks[order[k]] = avg
            i = j
        return ranks
    return pearson(rank(xs), rank(ys))


def t_two_sided_p(t: float, df: float) -> float:
    """Two-sided p-value for Student's t. Uses incomplete beta approximation."""
    if df <= 0:
        return float('nan')
    x = df / (df + t * t)
    # Regularized incomplete beta function I_x(a, b) for a=df/2, b=1/2
    # Approximation via series (Cornish-Fisher would be cleaner but OK for our N)
    # Use the relation: P(T > |t|) = 0.5 * I_x(df/2, 1/2)
    p = incbeta(df / 2, 0.5, x)
    return max(0.0, min(1.0, p))


def incbeta(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a,b) via continued fraction (Lentz)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b + lbeta) / a
    # Continued fraction
    fpmin = 1e-30
    m = 0
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1)
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, 201):
        m2 = 2 * m
        aa = m * (b - m) * x / ((a + m2 - 1) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-10:
            break
    return front * h


def cohens_d(a: list[float], b: list[float]) -> float:
    """Cohen's d for independent samples (pooled SD)."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float('nan')
    ma, mb = sum(a) / na, sum(b) / nb
    va = sum((x - ma) ** 2 for x in a) / (na - 1)
    vb = sum((x - mb) ** 2 for x in b) / (nb - 1)
    pooled = math.sqrt(((na - 1) * va + (nb - 1) * vb) / (na + nb - 2))
    if pooled == 0:
        return float('nan')
    return (ma - mb) / pooled


def welch_t(a: list[float], b: list[float]) -> tuple[float, float, float]:
    """Welch's t-test; returns (t, df, p)."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return (float('nan'),) * 3
    ma, mb = sum(a) / na, sum(b) / nb
    va = sum((x - ma) ** 2 for x in a) / (na - 1)
    vb = sum((x - mb) ** 2 for x in b) / (nb - 1)
    se = math.sqrt(va / na + vb / nb)
    if se == 0:
        return (float('nan'),) * 3
    t = (ma - mb) / se
    # Welch-Satterthwaite df
    df_num = (va / na + vb / nb) ** 2
    df_den = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    df = df_num / df_den if df_den > 0 else float('nan')
    p = t_two_sided_p(t, df)
    return (t, df, p)


def cohens_kappa(observed: list[str], predicted: list[str]) -> tuple[float, float]:
    """Unweighted Cohen's kappa + SE (Fleiss formula)."""
    categories = sorted(set(observed) | set(predicted))
    k = len(categories)
    idx = {c: i for i, c in enumerate(categories)}
    n = len(observed)
    cm = [[0] * k for _ in range(k)]
    for o, p in zip(observed, predicted):
        cm[idx[o]][idx[p]] += 1
    po = sum(cm[i][i] for i in range(k)) / n
    row_totals = [sum(cm[i]) for i in range(k)]
    col_totals = [sum(cm[i][j] for i in range(k)) for j in range(k)]
    pe = sum(row_totals[i] * col_totals[i] for i in range(k)) / (n * n)
    if pe >= 1:
        return (1.0, 0.0)
    kappa = (po - pe) / (1 - pe)
    # SE via Fleiss approximation
    se = math.sqrt(po * (1 - po) / (n * (1 - pe) ** 2))
    return (kappa, se)


def mean_sd(xs: list[float]) -> tuple[float, float]:
    n = len(xs)
    if n == 0:
        return (float('nan'), float('nan'))
    m = sum(xs) / n
    if n < 2:
        return (m, 0.0)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return (m, sd)


# ========== LOAD DATA ==========

def load_data() -> list[dict]:
    rows = []
    for line in SUMMARY_PATH.read_text(encoding='utf-8').splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


# ========== ANALYSES ==========

def analyze(rows: list[dict]) -> dict:
    results: dict = {}
    n = len(rows)
    results['n'] = n

    # ----- 1. Hit rate + confusion matrix -----
    matches = sum(1 for r in rows if r['attachment_match'])
    hit_rate = matches / n
    ci = wilson_ci(matches, n)
    results['overall_hit_rate'] = {
        'matches': matches, 'n': n,
        'rate': hit_rate, 'ci95': ci,
    }

    # Per-category hit rate
    per_cat: dict = defaultdict(lambda: {'n': 0, 'hits': 0})
    for r in rows:
        exp = r['expected_style']
        per_cat[exp]['n'] += 1
        if r['attachment_match']:
            per_cat[exp]['hits'] += 1
    for cat, d in per_cat.items():
        d['rate'] = d['hits'] / d['n']
        d['ci95'] = wilson_ci(d['hits'], d['n'])
    results['per_category_hit_rate'] = dict(per_cat)

    # Confusion matrix
    styles = ['secure', 'anxious_preoccupied', 'dismissive_avoidant', 'fearful_avoidant']
    cm = {exp: {pred: 0 for pred in styles} for exp in styles}
    for r in rows:
        exp = r['expected_style']
        pred = r['predicted_style']
        if exp in cm and pred in cm[exp]:
            cm[exp][pred] += 1
    results['confusion_matrix'] = cm

    # Cohen's kappa
    exp_list = [r['expected_style'] for r in rows]
    pred_list = [r['predicted_style'] for r in rows]
    kappa, kappa_se = cohens_kappa(exp_list, pred_list)
    # Landis-Koch benchmarks
    kappa_interp = (
        'słaba' if kappa < 0.20 else
        'umiarkowana' if kappa < 0.40 else
        'znaczna' if kappa < 0.60 else
        'istotna' if kappa < 0.80 else
        'niemal doskonała'
    )
    results['kappa'] = {'value': kappa, 'se': kappa_se, 'interpretation': kappa_interp,
                        'ci95': (kappa - 1.96 * kappa_se, kappa + 1.96 * kappa_se)}

    # ----- 2. Rank correlations (expected level → observed z) -----
    correlations: dict = {}

    # DBZ-R anxiety dimension
    xs_anx, ys_anx = [], []
    for r in rows:
        exp = r['expected_profile'].get('dbz_anxiety')
        rank = level_to_rank(exp)
        if rank is not None:
            xs_anx.append(rank)
            ys_anx.append(r['dbzr']['z_anx'])
    r_anx, p_anx = pearson(xs_anx, ys_anx)
    rho_anx, prho_anx = spearman(xs_anx, ys_anx)
    correlations['dbz_anxiety'] = {
        'n': len(xs_anx), 'r': r_anx, 'p': p_anx, 'rho': rho_anx, 'p_rho': prho_anx,
    }

    xs_avo, ys_avo = [], []
    for r in rows:
        exp = r['expected_profile'].get('dbz_avoidance')
        rank = level_to_rank(exp)
        if rank is not None:
            xs_avo.append(rank)
            ys_avo.append(r['dbzr']['z_avo'])
    r_avo, p_avo = pearson(xs_avo, ys_avo)
    rho_avo, prho_avo = spearman(xs_avo, ys_avo)
    correlations['dbz_avoidance'] = {
        'n': len(xs_avo), 'r': r_avo, 'p': p_avo, 'rho': rho_avo, 'p_rho': prho_avo,
    }

    # MentS dimensions
    for dim_key, field in (('ments_self', 'z_self'), ('ments_other', 'z_other'),
                           ('ments_motivation', 'z_mot')):
        xs, ys = [], []
        for r in rows:
            exp = r['expected_profile'].get(dim_key)
            rank = level_to_rank(exp)
            if rank is not None:
                xs.append(rank)
                ys.append(r['ments'][field])
        r_, p_ = pearson(xs, ys)
        rho_, prho_ = spearman(xs, ys)
        correlations[dim_key] = {'n': len(xs), 'r': r_, 'p': p_, 'rho': rho_, 'p_rho': prho_}

    # KPP
    xs, ys = [], []
    for r in rows:
        exp = r['expected_profile'].get('kpp')
        rank = level_to_rank(exp)
        if rank is not None:
            xs.append(rank)
            ys.append(r['kpp']['z_mean'])
    r_kpp, p_kpp = pearson(xs, ys)
    rho_kpp, prho_kpp = spearman(xs, ys)
    correlations['kpp'] = {'n': len(xs), 'r': r_kpp, 'p': p_kpp, 'rho': rho_kpp, 'p_rho': prho_kpp}

    # TIPI dimensions
    for trait, exp_key, obs_key in (
        ('E', 'tipi_E', 'z_E'),
        ('A', 'tipi_A', 'z_A'),
        ('C', 'tipi_C', 'z_C'),
        ('ES', 'tipi_ES', 'z_ES'),
        ('O', 'tipi_O', 'z_O'),
    ):
        xs, ys = [], []
        for r in rows:
            exp = r['expected_profile'].get(exp_key)
            rank = level_to_rank(exp)
            if rank is not None:
                xs.append(rank)
                ys.append(r['tipi'][obs_key])
        r_, p_ = pearson(xs, ys)
        rho_, prho_ = spearman(xs, ys)
        correlations[f'tipi_{trait}'] = {'n': len(xs), 'r': r_, 'p': p_, 'rho': rho_, 'p_rho': prho_}

    results['correlations'] = correlations

    # ----- 3. Contrast: High (rank ≥ 1) vs Low (rank ≤ -1) per dimension -----
    contrasts: dict = {}
    for key, (exp_field, obs_path) in {
        'z_anx': ('dbz_anxiety', ('dbzr', 'z_anx')),
        'z_avo': ('dbz_avoidance', ('dbzr', 'z_avo')),
        'z_self': ('ments_self', ('ments', 'z_self')),
        'z_other': ('ments_other', ('ments', 'z_other')),
        'z_mot': ('ments_motivation', ('ments', 'z_mot')),
        'z_kpp': ('kpp', ('kpp', 'z_mean')),
        'z_E': ('tipi_E', ('tipi', 'z_E')),
        'z_A': ('tipi_A', ('tipi', 'z_A')),
        'z_C': ('tipi_C', ('tipi', 'z_C')),
        'z_ES': ('tipi_ES', ('tipi', 'z_ES')),
        'z_O': ('tipi_O', ('tipi', 'z_O')),
    }.items():
        high, low = [], []
        for r in rows:
            exp = r['expected_profile'].get(exp_field)
            rank = level_to_rank(exp)
            if rank is None:
                continue
            val = r[obs_path[0]][obs_path[1]]
            if rank >= 1:
                high.append(val)
            elif rank <= -1:
                low.append(val)
        if len(high) < 2 or len(low) < 2:
            contrasts[key] = None
            continue
        t, df, p = welch_t(high, low)
        d = cohens_d(high, low)
        mh, sh = mean_sd(high)
        ml, sl = mean_sd(low)
        contrasts[key] = {
            'n_high': len(high), 'n_low': len(low),
            'mean_high': mh, 'sd_high': sh,
            'mean_low': ml, 'sd_low': sl,
            't': t, 'df': df, 'p': p, 'd': d,
        }
    results['contrasts'] = contrasts

    # ----- 4. TCTM ceiling effect -----
    tctm_correct = [r['tctm']['correct'] for r in rows]
    tctm_m, tctm_sd = mean_sd(tctm_correct)
    tctm_cv = tctm_sd / tctm_m if tctm_m > 0 else float('nan')
    masc_dos = sum(r['tctm']['DOS'] for r in rows)
    masc_nad = sum(r['tctm']['NAD'] for r in rows)
    masc_bk = sum(r['tctm']['BK'] for r in rows)
    masc_corr = sum(r['tctm']['correct'] for r in rows)
    total_items = n * 22
    results['tctm'] = {
        'mean_correct': tctm_m, 'sd_correct': tctm_sd, 'cv': tctm_cv,
        'min_correct': min(tctm_correct), 'max_correct': max(tctm_correct),
        'total_items': total_items,
        'accuracy_pct': masc_corr / total_items * 100,
        'DOS_pct': masc_dos / total_items * 100,
        'NAD_pct': masc_nad / total_items * 100,
        'BK_pct': masc_bk / total_items * 100,
        'distribution': {
            str(x): sum(1 for c in tctm_correct if c == x)
            for x in range(min(tctm_correct), max(tctm_correct) + 1)
        },
    }

    # ----- 5. Gemini vs Sonnet (Agata specific contrast) -----
    gemini_agata = {
        'z_anx': -1.81, 'z_avo': 3.72, 'z_self': 1.40, 'z_other': 0.32,
        'z_mot': -0.13, 'z_kpp': 2.00, 'z_E': -3.35, 'z_A': -0.24,
        'z_C': 1.34, 'z_ES': 1.69, 'z_O': 1.31, 'total_ments': 114,
    }
    agata = next((r for r in rows if r['persona_id'] == 'agata'), None)
    if agata:
        sonnet_agata = {
            'z_anx': agata['dbzr']['z_anx'], 'z_avo': agata['dbzr']['z_avo'],
            'z_self': agata['ments']['z_self'], 'z_other': agata['ments']['z_other'],
            'z_mot': agata['ments']['z_mot'], 'z_kpp': agata['kpp']['z_mean'],
            'z_E': agata['tipi']['z_E'], 'z_A': agata['tipi']['z_A'],
            'z_C': agata['tipi']['z_C'], 'z_ES': agata['tipi']['z_ES'],
            'z_O': agata['tipi']['z_O'], 'total_ments': agata['ments']['total'],
        }
        results['gemini_vs_sonnet_agata'] = {
            'gemini': gemini_agata,
            'sonnet': sonnet_agata,
            'delta_magnitude': {
                k: abs(gemini_agata[k]) - abs(sonnet_agata[k])
                for k in gemini_agata if k != 'total_ments'
            },
        }

    # ----- 6. Per-item TCTM analysis (replikuje pilot tab. 2) -----
    # Zbieramy dla każdej z 22 winiet: liczba correct / DOS / NAD / BK per item
    tctm_item: dict[str, dict] = {}
    for r in rows:
        for ans in r['payload']['tctm']['answers']:
            vid = ans['itemId']
            masc = ans['chosenMascType']
            if vid not in tctm_item:
                tctm_item[vid] = {'correct': 0, 'DOS': 0, 'NAD': 0, 'BK': 0, 'unknown': 0, 'n': 0}
            tctm_item[vid]['n'] += 1
            if masc in tctm_item[vid]:
                tctm_item[vid][masc] += 1
            else:
                tctm_item[vid]['unknown'] += 1
    # Compute p and dominant error per item
    for vid, d in tctm_item.items():
        d['p'] = d['correct'] / d['n'] if d['n'] else 0.0
        errors = {k: d[k] for k in ('DOS', 'NAD', 'BK') if d[k] > 0}
        d['dominant_error'] = max(errors, key=errors.get) if errors else None
    results['tctm_items'] = tctm_item

    # Per-item discrimination: point-biserial correlation
    # item correct (0/1) vs total score (exclude item) for each persona
    # Dla 30 osób to ma sens — wyciągam korelację każdej winiety z total
    item_discr = {}
    for vid in tctm_item:
        item_scores = []
        total_minus = []
        for r in rows:
            ans_vid = next((a for a in r['payload']['tctm']['answers'] if a['itemId'] == vid), None)
            is_corr = 1 if ans_vid and ans_vid['isCorrect'] else 0
            total = r['tctm']['correct'] - is_corr
            item_scores.append(is_corr)
            total_minus.append(total)
        if len(set(item_scores)) == 1:
            item_discr[vid] = None  # no variance
        else:
            r_pb, p_pb = pearson(item_scores, total_minus)
            item_discr[vid] = {'r_pb': r_pb, 'p': p_pb}
    results['tctm_discrimination'] = item_discr

    # ----- 7. Per-category TCTM accuracy aggregated across 30 -----
    # Mapa z pilota: subscale → category label
    subscale_map = {
        'subtext': 'Rozpoznawanie ukrytych znaczeń',
        'court': 'Rozpoznawanie manipulacji',
        'eks': 'Wykrywanie wygasania relacji',
        'pursuit': 'Dynamika dążenia-wycofywania',
        'repair': 'Ocena naprawy relacyjnej',
    }
    cat_totals = {sub: {'correct': 0, 'total': 0} for sub in subscale_map}
    # Mapping itemId → subscale (z tctm54.ts, identycznie jak w pilocie):
    item_subscale = {
        'w01': 'subtext', 's07': 'subtext', 's08': 'subtext', 's10': 'subtext',
        'w08': 'court', 'c07': 'court', 'c10': 'court', 'w11': 'court',
        'w13': 'eks', 'w14': 'eks', 'w15': 'eks', 'e08': 'eks',
        'w19': 'pursuit', 'pw07': 'pursuit', 'w22': 'pursuit',
        'pw09': 'pursuit', 'pw11': 'pursuit',
        'w25': 'repair', 'r08': 'repair', 'w28': 'repair', 'r09': 'repair', 'r10': 'repair',
    }
    for r in rows:
        for ans in r['payload']['tctm']['answers']:
            sub = item_subscale.get(ans['itemId'])
            if sub:
                cat_totals[sub]['total'] += 1
                if ans['isCorrect']:
                    cat_totals[sub]['correct'] += 1
    for sub in cat_totals:
        t = cat_totals[sub]
        t['accuracy'] = t['correct'] / t['total'] if t['total'] else 0.0
        t['label'] = subscale_map[sub]
    results['tctm_per_category'] = cat_totals

    # ----- 8. POZ / TRAP second coding layer -----
    POZ_IDS = {'s08', 'pw11', 'r08', 'w28', 'r09'}
    TRAP_IDS = {'s10', 'pw09'}

    poz_per_persona = {}  # persona -> {nad: int, total: 5}
    trap_per_persona = {}
    for r in rows:
        nad_poz = 0
        nad_trap = 0
        for ans in r['payload']['tctm']['answers']:
            if ans['itemId'] in POZ_IDS and ans['chosenMascType'] == 'NAD':
                nad_poz += 1
            if ans['itemId'] in TRAP_IDS and ans['chosenMascType'] == 'NAD':
                nad_trap += 1
        poz_per_persona[r['persona_id']] = {'nad': nad_poz, 'nb': nad_poz / 5}
        trap_per_persona[r['persona_id']] = {'nad': nad_trap, 'or': nad_trap / 2}
    results['nb_per_persona'] = poz_per_persona
    results['or_per_persona'] = trap_per_persona

    nb_vals = [d['nb'] for d in poz_per_persona.values()]
    or_vals = [d['or'] for d in trap_per_persona.values()]
    results['nb_stats'] = {'mean': sum(nb_vals) / len(nb_vals),
                            'sd': mean_sd(nb_vals)[1],
                            'max': max(nb_vals), 'n_nonzero': sum(1 for v in nb_vals if v > 0)}
    results['or_stats'] = {'mean': sum(or_vals) / len(or_vals),
                            'sd': mean_sd(or_vals)[1],
                            'max': max(or_vals), 'n_nonzero': sum(1 for v in or_vals if v > 0)}

    # NB correlations with TIPI-A (Ugodowość) — pilot hipoteza 1
    # NB → TIPI-A: oczekiwanie ujemne (wyższa ugodowość → niższy negatywny bias)
    tipi_a = [r['tipi']['z_A'] for r in rows]
    nb_list = [poz_per_persona[r['persona_id']]['nb'] for r in rows]
    or_list = [trap_per_persona[r['persona_id']]['or'] for r in rows]
    tipi_es = [r['tipi']['z_ES'] for r in rows]
    ments_o = [r['ments']['z_other'] for r in rows]
    ments_m = [r['ments']['z_mot'] for r in rows]

    results['nb_or_correlations'] = {
        'NB_vs_TIPI_A':     {'r': pearson(nb_list, tipi_a)[0],      'p': pearson(nb_list, tipi_a)[1]},
        'NB_vs_MentS_O':    {'r': pearson(nb_list, ments_o)[0],     'p': pearson(nb_list, ments_o)[1]},
        'OR_vs_TIPI_ES':    {'r': pearson(or_list, tipi_es)[0],     'p': pearson(or_list, tipi_es)[1]},
        'OR_vs_MentS_Mot':  {'r': pearson(or_list, ments_m)[0],     'p': pearson(or_list, ments_m)[1]},
        'NB_vs_OR':         {'r': pearson(nb_list, or_list)[0],     'p': pearson(nb_list, or_list)[1]},
    }

    # ----- 9. Pilot hypothesis: TIPI-A vs Repair accuracy (per persona) -----
    repair_acc = []
    for r in rows:
        correct = 0
        total = 0
        for ans in r['payload']['tctm']['answers']:
            if item_subscale.get(ans['itemId']) == 'repair':
                total += 1
                if ans['isCorrect']:
                    correct += 1
        repair_acc.append(correct / total if total else 0.0)
    r_pilot, p_pilot = pearson(tipi_a, repair_acc)
    rho_pilot, prho_pilot = spearman(tipi_a, repair_acc)
    results['pilot_hypothesis_repair_agree'] = {
        'r': r_pilot, 'p': p_pilot, 'rho': rho_pilot, 'p_rho': prho_pilot,
        'n': len(repair_acc),
    }

    # ----- 10. Literature consistency test (10 pairs × 30 respondents) -----
    LIT_PAIRS = [
        ('MentS-Tot × DBZ-R Lęk', 'ments_total', 'dbz_anxiety', -0.39),
        ('MS-S × DBZ-R Lęk', 'ments_self', 'dbz_anxiety', -0.43),
        ('MS-S × DBZ-R Unik.', 'ments_self', 'dbz_avoidance', -0.30),
        ('MS-M × KPP', 'ments_mot', 'kpp_z', +0.30),
        ('MS-M × TIPI-O', 'ments_mot', 'tipi_O', +0.34),
        ('MS-O × TIPI-E', 'ments_other', 'tipi_E', +0.37),
        ('MentS-Tot × TIPI-ES', 'ments_total', 'tipi_ES', +0.26),
        ('KPP × TIPI-O', 'kpp_z', 'tipi_O', +0.40),
        ('KPP × TIPI-C', 'kpp_z', 'tipi_C', +0.25),
        ('DBZ-R Lęk × TIPI-ES', 'dbz_anxiety', 'tipi_ES', -0.45),
    ]

    def get_z(row: dict, key: str) -> float:
        mapping = {
            'ments_total': ('ments', 'z_total'),
            'ments_self': ('ments', 'z_self'),
            'ments_other': ('ments', 'z_other'),
            'ments_mot': ('ments', 'z_mot'),
            'dbz_anxiety': ('dbzr', 'z_anx'),
            'dbz_avoidance': ('dbzr', 'z_avo'),
            'kpp_z': ('kpp', 'z_mean'),
            'tipi_E': ('tipi', 'z_E'),
            'tipi_A': ('tipi', 'z_A'),
            'tipi_C': ('tipi', 'z_C'),
            'tipi_ES': ('tipi', 'z_ES'),
            'tipi_O': ('tipi', 'z_O'),
        }
        grp, field = mapping[key]
        return row[grp][field]

    # Dla każdej pary: oblicz empiryczny r Pearson w całej próbie N=30
    # Porównaj znak z literaturowym
    lit_results = []
    for name, k1, k2, r_lit in LIT_PAIRS:
        xs = [get_z(r, k1) for r in rows]
        ys = [get_z(r, k2) for r in rows]
        r_obs, p_obs = pearson(xs, ys)
        sign_match = (r_lit > 0 and r_obs > 0) or (r_lit < 0 and r_obs < 0)
        lit_results.append({
            'pair': name, 'r_lit': r_lit, 'r_obs': r_obs, 'p': p_obs,
            'sign_match': sign_match,
        })
    sign_hits = sum(1 for x in lit_results if x['sign_match'])
    results['literature_consistency'] = {
        'pairs': lit_results,
        'sign_hits': sign_hits,
        'total': len(lit_results),
        'rate': sign_hits / len(lit_results),
    }

    # ----- 11. Pairwise Euclidean distance in 12-dim z-score space -----
    def profile_vec(r: dict) -> list[float]:
        return [
            r['dbzr']['z_anx'], r['dbzr']['z_avo'],
            r['ments']['z_self'], r['ments']['z_other'],
            r['ments']['z_mot'], r['ments']['z_total'],
            r['kpp']['z_mean'],
            r['tipi']['z_E'], r['tipi']['z_A'], r['tipi']['z_C'],
            r['tipi']['z_ES'], r['tipi']['z_O'],
        ]

    vecs = [(r['persona_id'], profile_vec(r)) for r in rows]
    distances = []
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            d = math.sqrt(sum((a - b) ** 2 for a, b in zip(vecs[i][1], vecs[j][1])))
            distances.append({'a': vecs[i][0], 'b': vecs[j][0], 'd': d})
    dists_only = [x['d'] for x in distances]
    md, sdd = mean_sd(dists_only)
    distances.sort(key=lambda x: x['d'])
    results['pairwise_distance'] = {
        'n_pairs': len(distances),
        'mean': md,
        'sd': sdd,
        'min': distances[0] if distances else None,
        'max': distances[-1] if distances else None,
        'baseline_12dim_1sd': math.sqrt(12),  # gdyby 1 SD na każdym wymiarze
    }

    return results


# ========== LATEX TABLES EMITTER ==========

def fmt(x: float, d: int = 2) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return '---'
    return f'{x:.{d}f}'


def fmt_p(p: float) -> str:
    if p is None or math.isnan(p):
        return '---'
    if p < 0.001:
        return '< 0.001'
    return f'{p:.3f}'


def emit_tex(results: dict) -> str:
    lines: list[str] = []

    # ----- Table 1: Hit rate per category with Wilson CI -----
    lines.append('% ====== Table 1: Hit rate per category ======')
    lines.append('\\begin{table}[H]')
    lines.append('\\centering')
    lines.append('\\caption{Trafność predykcji stylu przywiązania w podziale na kategorie (\\textit{N}~=~30).}')
    lines.append('\\label{tab:hit-rate}')
    lines.append('\\begin{tabular}{lrrrr}')
    lines.append('\\toprule')
    lines.append('Oczekiwany styl & \\textit{n} & Trafione & Hit rate & 95\\% CI (Wilson) \\\\')
    lines.append('\\midrule')
    order = ['secure', 'anxious_preoccupied', 'dismissive_avoidant', 'fearful_avoidant', 'disorganized']
    labels = {
        'secure': 'Bezpieczny',
        'anxious_preoccupied': 'Lękowo-ambiwalentny',
        'dismissive_avoidant': 'Unikający',
        'fearful_avoidant': 'Lękowo-unikający',
        'disorganized': 'Zdezorganizowany',
    }
    per_cat = results['per_category_hit_rate']
    for cat in order:
        if cat in per_cat:
            d = per_cat[cat]
            ci_lo, ci_hi = d['ci95']
            lines.append(f"{labels[cat]} & {d['n']} & {d['hits']} & {d['rate']*100:.1f}\\% & "
                         f"[{ci_lo*100:.1f}\\%, {ci_hi*100:.1f}\\%] \\\\")
    lines.append('\\midrule')
    ov = results['overall_hit_rate']
    lines.append(f"\\textbf{{Razem}} & \\textbf{{{ov['n']}}} & \\textbf{{{ov['matches']}}} & "
                 f"\\textbf{{{ov['rate']*100:.1f}\\%}} & \\textbf{{[{ov['ci95'][0]*100:.1f}\\%, {ov['ci95'][1]*100:.1f}\\%]}} \\\\")
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('\\end{table}')
    lines.append('')

    # ----- Table 2: Confusion matrix -----
    lines.append('% ====== Table 2: Confusion matrix ======')
    lines.append('\\begin{table}[H]')
    lines.append('\\centering')
    lines.append('\\caption{Macierz pomyłek: styl oczekiwany (wiersze) \\textit{vs} przewidywany (kolumny).}')
    lines.append('\\label{tab:confusion}')
    lines.append('\\footnotesize')
    lines.append('\\begin{tabular}{l|cccc|r}')
    lines.append('\\toprule')
    lines.append(' & Bezp. & Lęk.-amb. & Unik. & Lęk.-unik. & \\textit{n} \\\\')
    lines.append('\\midrule')
    cm_labels = ['secure', 'anxious_preoccupied', 'dismissive_avoidant', 'fearful_avoidant']
    cm_short = ['Bezp.', 'Lęk.-amb.', 'Unik.', 'Lęk.-unik.']
    cm = results['confusion_matrix']
    for i, exp in enumerate(cm_labels):
        row = cm[exp]
        row_n = sum(row.values())
        cells = []
        for pred in cm_labels:
            v = row[pred]
            cells.append(f'\\textbf{{{v}}}' if exp == pred and v > 0 else str(v))
        lines.append(f'{cm_short[i]} & ' + ' & '.join(cells) + f' & {row_n} \\\\')
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('\\end{table}')
    lines.append('')

    # ----- Table 3: Correlations -----
    lines.append('% ====== Table 3: Correlations expected vs observed ======')
    lines.append('\\begin{table}[H]')
    lines.append('\\centering')
    lines.append('\\caption{Korelacje rangi oczekiwanej \\textit{vs} obserwowany z-score.}')
    lines.append('\\label{tab:correlations}')
    lines.append('\\begin{tabular}{lrrrrr}')
    lines.append('\\toprule')
    lines.append('Skala / wymiar & \\textit{n} & \\textit{r} Pearson & \\textit{p} & $\\rho$ Spearman & \\textit{p} \\\\')
    lines.append('\\midrule')
    corr_labels = {
        'dbz_anxiety': 'DBZ-R Lęk',
        'dbz_avoidance': 'DBZ-R Unikanie',
        'ments_self': 'MentS Self',
        'ments_other': 'MentS Other',
        'ments_motivation': 'MentS Motywacja',
        'kpp': 'KPP ogólne',
        'tipi_E': 'TIPI Ekstrawersja',
        'tipi_A': 'TIPI Ugodowość',
        'tipi_C': 'TIPI Sumienność',
        'tipi_ES': 'TIPI Stab. emoc.',
        'tipi_O': 'TIPI Otwartość',
    }
    for key, label in corr_labels.items():
        c = results['correlations'].get(key)
        if not c:
            continue
        sig_r = '^{***}' if c['p'] < 0.001 else ('^{**}' if c['p'] < 0.01 else ('^{*}' if c['p'] < 0.05 else ''))
        sig_rho = '^{***}' if c['p_rho'] < 0.001 else ('^{**}' if c['p_rho'] < 0.01 else ('^{*}' if c['p_rho'] < 0.05 else ''))
        lines.append(f"{label} & {c['n']} & ${fmt(c['r'], 3)}{sig_r}$ & {fmt_p(c['p'])} & "
                     f"${fmt(c['rho'], 3)}{sig_rho}$ & {fmt_p(c['p_rho'])} \\\\")
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('')
    lines.append('\\vspace{0.3em}')
    lines.append("\\footnotesize $^{*}$ \\textit{p} < .05; $^{**}$ \\textit{p} < .01; $^{***}$ \\textit{p} < .001")
    lines.append('\\end{table}')
    lines.append('')

    # ----- Table 4: High vs Low contrasts -----
    lines.append('% ====== Table 4: Welch t-test contrasts ======')
    lines.append('\\begin{table}[H]')
    lines.append('\\centering')
    lines.append('\\caption{Kontrasty \\textit{high} (rank~$\\geq$~1) \\textit{vs low} (rank~$\\leq$~$-1$) — test Welcha, \\textit{d} Cohena.}')
    lines.append('\\label{tab:contrasts}')
    lines.append('\\footnotesize')
    lines.append('\\begin{tabular}{lrrrrrrrr}')
    lines.append('\\toprule')
    lines.append('Wymiar & $n_H$ & $n_L$ & $M_H$ & $M_L$ & \\textit{t} & \\textit{df} & \\textit{p} & \\textit{d} \\\\')
    lines.append('\\midrule')
    contrast_labels = {
        'z_anx': 'DBZ-R Lęk',
        'z_avo': 'DBZ-R Unikanie',
        'z_self': 'MentS Self',
        'z_other': 'MentS Other',
        'z_mot': 'MentS Motywacja',
        'z_kpp': 'KPP',
        'z_E': 'TIPI E',
        'z_A': 'TIPI A',
        'z_C': 'TIPI C',
        'z_ES': 'TIPI ES',
        'z_O': 'TIPI O',
    }
    for key, label in contrast_labels.items():
        c = results['contrasts'].get(key)
        if not c:
            continue
        lines.append(f"{label} & {c['n_high']} & {c['n_low']} & "
                     f"{fmt(c['mean_high'])} & {fmt(c['mean_low'])} & "
                     f"{fmt(c['t'])} & {fmt(c['df'], 1)} & {fmt_p(c['p'])} & {fmt(c['d'])} \\\\")
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('\\end{table}')
    lines.append('')

    # ----- Table 5: Gemini vs Sonnet (Agata) -----
    if 'gemini_vs_sonnet_agata' in results:
        g = results['gemini_vs_sonnet_agata']['gemini']
        s = results['gemini_vs_sonnet_agata']['sonnet']
        lines.append('% ====== Table 5: Gemini vs Sonnet Agata ======')
        lines.append('\\begin{table}[H]')
        lines.append('\\centering')
        lines.append('\\caption{Porównanie Gemini \\textit{vs} Sonnet dla persony \\emph{Agata} (\\textit{dismissive-avoidant}).}')
        lines.append('\\label{tab:gemini-sonnet}')
        lines.append('\\begin{tabular}{lrrr}')
        lines.append('\\toprule')
        lines.append('Wymiar & Gemini & Sonnet & $|\\Delta|$ \\\\')
        lines.append('\\midrule')
        gs_labels = {
            'z_anx': 'DBZ-R Lęk',
            'z_avo': 'DBZ-R Unikanie',
            'z_self': 'MentS Self',
            'z_other': 'MentS Other',
            'z_mot': 'MentS Motywacja',
            'z_kpp': 'KPP',
            'z_E': 'TIPI E',
            'z_A': 'TIPI A',
            'z_C': 'TIPI C',
            'z_ES': 'TIPI ES',
            'z_O': 'TIPI O',
        }
        for k, label in gs_labels.items():
            delta = abs(g[k]) - abs(s[k])
            lines.append(f"{label} & {g[k]:+.2f} & {s[k]:+.2f} & {delta:+.2f} \\\\")
        lines.append('\\midrule')
        lines.append(f"MentS total (raw) & {g['total_ments']:.0f} & {s['total_ments']:.0f} & --- \\\\")
        lines.append('\\bottomrule')
        lines.append('\\end{tabular}')
        lines.append('')
        lines.append("\\vspace{0.3em}")
        lines.append("\\footnotesize Dodatnie $|\\Delta|$ = Gemini bardziej skrajny od Sonneta.")
        lines.append('\\end{table}')
        lines.append('')

    # ----- Table 6: TCTM ceiling stats -----
    t = results['tctm']
    lines.append('% ====== Table 6: TCTM ceiling ======')
    lines.append('\\begin{table}[H]')
    lines.append('\\centering')
    lines.append('\\caption{Efekt sufitu TCTM-22: statystyki (30 agentów $\\times$ 22 winiety = 660 odpowiedzi).}')
    lines.append('\\label{tab:tctm-ceiling}')
    lines.append('\\begin{tabular}{lr}')
    lines.append('\\toprule')
    lines.append('Statystyka & Wartość \\\\')
    lines.append('\\midrule')
    lines.append(f"Średnia poprawność (\\textit{{M}} $\\pm$ \\textit{{SD}}) & {t['mean_correct']:.2f} $\\pm$ {t['sd_correct']:.2f} / 22 \\\\")
    lines.append(f"Zakres (min--max) & {t['min_correct']}--{t['max_correct']} \\\\")
    lines.append(f"Współczynnik zmienności (CV) & {t['cv']*100:.1f}\\% \\\\")
    lines.append(f"Accuracy zagregowane & {t['accuracy_pct']:.1f}\\% \\\\")
    lines.append(f"DOS (undermentalizing) & {t['DOS_pct']:.1f}\\% \\\\")
    lines.append(f"NAD (overmentalizing) & {t['NAD_pct']:.1f}\\% \\\\")
    lines.append(f"BK (brak mentalizacji) & {t['BK_pct']:.1f}\\% \\\\")
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('\\end{table}')
    lines.append('')

    # ----- Table 7: Per-item TCTM analysis -----
    lines.append('% ====== Table 7: Per-item TCTM ======')
    lines.append('\\begin{table}[H]')
    lines.append('\\centering')
    lines.append('\\caption{Analiza pozycji TCTM-22 (N = 30 agentów): wskaźnik trudności \\textit{p}, dominujący typ błędu, korelacja punktowo-dwuseryjna \\textit{r}$_{\\text{pb}}$.}')
    lines.append('\\label{tab:tctm-items}')
    lines.append('\\footnotesize')
    lines.append('\\begin{tabular}{lllrrr}')
    lines.append('\\toprule')
    lines.append('Winieta & Kategoria & Tag & \\textit{p} & Dom. błąd (\\textit{n}) & \\textit{r}$_{\\text{pb}}$ \\\\')
    lines.append('\\midrule')
    subscale_labels_short = {
        'subtext': 'Ukryte znaczenia',
        'court': 'Manipulacja',
        'eks': 'Wygasanie',
        'pursuit': 'Dążenie-wycof.',
        'repair': 'Naprawa',
    }
    item_subscale_mapping = {
        'w01': 'subtext', 's07': 'subtext', 's08': 'subtext', 's10': 'subtext',
        'w08': 'court', 'c07': 'court', 'c10': 'court', 'w11': 'court',
        'w13': 'eks', 'w14': 'eks', 'w15': 'eks', 'e08': 'eks',
        'w19': 'pursuit', 'pw07': 'pursuit', 'w22': 'pursuit',
        'pw09': 'pursuit', 'pw11': 'pursuit',
        'w25': 'repair', 'r08': 'repair', 'w28': 'repair', 'r09': 'repair', 'r10': 'repair',
    }
    POZ = {'s08', 'pw11', 'r08', 'w28', 'r09'}
    TRAP = {'s10', 'pw09'}
    items_sorted = sorted(results['tctm_items'].items(), key=lambda x: x[1]['p'])
    for vid, d in items_sorted:
        sub = item_subscale_mapping.get(vid, '?')
        tag = 'POZ' if vid in POZ else ('TRAP' if vid in TRAP else '--')
        dom = d['dominant_error']
        dom_n = d[dom] if dom else 0
        dom_str = f'{dom}~({dom_n})' if dom else '---'
        discr = results['tctm_discrimination'].get(vid)
        r_pb = f"{discr['r_pb']:+.2f}" if discr else '---'
        lines.append(f"{vid} & {subscale_labels_short[sub]} & {tag} & {d['p']:.2f} & {dom_str} & {r_pb} \\\\")
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('')
    lines.append("\\vspace{0.3em}")
    lines.append("\\footnotesize POZ = winieta z pozytywnym podtekstem; TRAP = winieta pułapkowa (odpowiedź dosłowna).")
    lines.append('\\end{table}')
    lines.append('')

    # ----- Table 8: Per-category accuracy -----
    lines.append('% ====== Table 8: TCTM per-category ======')
    lines.append('\\begin{table}[H]')
    lines.append('\\centering')
    lines.append('\\caption{Trafność TCTM-22 w podziale na pięć kategorii treściowych (agregowane po 30 agentach).}')
    lines.append('\\label{tab:tctm-categories}')
    lines.append('\\begin{tabular}{lrrr}')
    lines.append('\\toprule')
    lines.append('Kategoria treściowa & Poprawne & Łącznie & Accuracy \\\\')
    lines.append('\\midrule')
    cat_order = ['subtext', 'court', 'eks', 'pursuit', 'repair']
    for sub in cat_order:
        c = results['tctm_per_category'][sub]
        lines.append(f"{c['label']} & {c['correct']} & {c['total']} & {c['accuracy']*100:.1f}\\% \\\\")
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('\\end{table}')
    lines.append('')

    # ----- Table 9: NB/OR per persona + correlations -----
    lines.append('% ====== Table 9: NB/OR indicators ======')
    lines.append('\\begin{table}[H]')
    lines.append('\\centering')
    lines.append('\\caption{Wskaźniki drugiej warstwy kodowania: NB (negative bias — NAD na 5 winietach POZ) oraz OR (over-reading — NAD na 2 winietach TRAP).}')
    lines.append('\\label{tab:nb-or}')
    lines.append('\\begin{tabular}{lrr}')
    lines.append('\\toprule')
    lines.append('Statystyka & NB & OR \\\\')
    lines.append('\\midrule')
    nbs = results['nb_stats']
    ors = results['or_stats']
    lines.append(f"\\textit{{M}} $\\pm$ \\textit{{SD}} & {nbs['mean']:.3f} $\\pm$ {nbs['sd']:.3f} & {ors['mean']:.3f} $\\pm$ {ors['sd']:.3f} \\\\")
    lines.append(f"Maksimum & {nbs['max']:.2f} & {ors['max']:.2f} \\\\")
    lines.append(f"Liczba non-zero & {nbs['n_nonzero']}/30 & {ors['n_nonzero']}/30 \\\\")
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('')
    lines.append("\\vspace{0.6em}")
    lines.append('\\caption*{\\textbf{Korelacje wskaźników z profilami osobowości:}}')
    lines.append('\\begin{tabular}{lrr}')
    lines.append('\\toprule')
    lines.append('Para & Pearson \\textit{r} & \\textit{p} \\\\')
    lines.append('\\midrule')
    corr_nbor_labels = {
        'NB_vs_TIPI_A': 'NB $\\times$ TIPI Ugodowość',
        'NB_vs_MentS_O': 'NB $\\times$ MentS Other',
        'OR_vs_TIPI_ES': 'OR $\\times$ TIPI Stab.~emoc.',
        'OR_vs_MentS_Mot': 'OR $\\times$ MentS Motywacja',
        'NB_vs_OR': 'NB $\\times$ OR',
    }
    for k, label in corr_nbor_labels.items():
        c = results['nb_or_correlations'][k]
        lines.append(f"{label} & {fmt(c['r'], 3)} & {fmt_p(c['p'])} \\\\")
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('\\end{table}')
    lines.append('')

    # ----- Table 10: Literature consistency -----
    lines.append('% ====== Table 10: Literature consistency ======')
    lines.append('\\begin{table}[H]')
    lines.append('\\centering')
    lines.append('\\caption{Test spójności profilu z literaturą adaptacyjną: 10 par konstruktów, empiryczne \\textit{r} Pearsona obliczone na N~=~30 syntetycznych agentach.}')
    lines.append('\\label{tab:lit-consistency}')
    lines.append('\\footnotesize')
    lines.append('\\begin{tabular}{lrrrc}')
    lines.append('\\toprule')
    lines.append('Para konstruktów & \\textit{r}$_{\\text{lit}}$ & \\textit{r}$_{\\text{obs}}$ & \\textit{p} & Znak zgodny? \\\\')
    lines.append('\\midrule')
    for p in results['literature_consistency']['pairs']:
        mark = '\\checkmark' if p['sign_match'] else '$\\times$'
        sig = '$^{*}$' if p['p'] < 0.05 else ''
        lines.append(f"{p['pair']} & {p['r_lit']:+.2f} & {p['r_obs']:+.3f}{sig} & {fmt_p(p['p'])} & {mark} \\\\")
    lc = results['literature_consistency']
    lines.append('\\midrule')
    lines.append(f"\\textbf{{Trafność znaku łącznie}} & & & & \\textbf{{{lc['sign_hits']}/{lc['total']} ({lc['rate']*100:.0f}\\%)}} \\\\")
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('')
    lines.append("\\vspace{0.3em}")
    lines.append("\\footnotesize $^{*}$ \\textit{p} < .05. Wartości \\textit{r}$_{\\text{lit}}$ pochodzą z: Jańczak (2021), Matusz \\textit{i in.} (2011), Fraley \\textit{i in.} (2000).")
    lines.append('\\end{table}')
    lines.append('')

    # ----- Table 11: Pairwise Euclidean distances -----
    lines.append('% ====== Table 11: Pairwise distances ======')
    lines.append('\\begin{table}[H]')
    lines.append('\\centering')
    lines.append('\\caption{Odległość euklidesowa profili w 12-wymiarowej przestrzeni $z$-scorów; $\\binom{30}{2} = 435$ par.}')
    lines.append('\\label{tab:pairwise-distance}')
    lines.append('\\begin{tabular}{lr}')
    lines.append('\\toprule')
    lines.append('Statystyka & Wartość \\\\')
    lines.append('\\midrule')
    pd = results['pairwise_distance']
    lines.append(f"Liczba par & {pd['n_pairs']} \\\\")
    lines.append(f"$\\bar{{d}} \\pm SD$ & ${pd['mean']:.2f} \\pm {pd['sd']:.2f}$ \\\\")
    lines.append(f"Baseline (1 SD na każdy z 12 wymiarów) & $\\sqrt{{12}} = {pd['baseline_12dim_1sd']:.2f}$ \\\\")
    lines.append(f"Średnia różnica na wymiar & ${pd['mean']/math.sqrt(12):.2f}~SD$ \\\\")
    lines.append(f"Minimum & {pd['min']['a']} $\\leftrightarrow$ {pd['min']['b']}: ${pd['min']['d']:.2f}$ \\\\")
    lines.append(f"Maksimum & {pd['max']['a']} $\\leftrightarrow$ {pd['max']['b']}: ${pd['max']['d']:.2f}$ \\\\")
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('\\end{table}')

    return '\n'.join(lines)


def main() -> None:
    rows = load_data()
    results = analyze(rows)
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    tex = emit_tex(results)
    OUT_TEX.write_text(tex, encoding='utf-8')
    print(f'Saved {OUT_JSON.name} ({len(json.dumps(results))} bytes)')
    print(f'Saved {OUT_TEX.name} ({len(tex)} bytes)')
    # Summary print
    print()
    print('=== SUMMARY ===')
    ov = results['overall_hit_rate']
    print(f"Overall hit rate: {ov['matches']}/{ov['n']} = {ov['rate']*100:.1f}% (95% CI {ov['ci95'][0]*100:.1f}%–{ov['ci95'][1]*100:.1f}%)")
    k = results['kappa']
    print(f"Cohen's kappa: {k['value']:.3f} (SE={k['se']:.3f}, 95% CI [{k['ci95'][0]:.3f}, {k['ci95'][1]:.3f}]) — {k['interpretation']}")
    print()
    print('Correlations (expected rank vs observed z):')
    for key, label in [
        ('dbz_anxiety', 'DBZ-R Lęk'),
        ('dbz_avoidance', 'DBZ-R Unikanie'),
        ('ments_self', 'MentS Self'),
        ('ments_other', 'MentS Other'),
        ('ments_motivation', 'MentS Mot'),
        ('kpp', 'KPP'),
        ('tipi_E', 'TIPI E'),
        ('tipi_A', 'TIPI A'),
        ('tipi_C', 'TIPI C'),
        ('tipi_ES', 'TIPI ES'),
        ('tipi_O', 'TIPI O'),
    ]:
        c = results['correlations'].get(key)
        if c:
            print(f"  {label:25s}: r={c['r']:+.3f} (p={fmt_p(c['p'])}), rho={c['rho']:+.3f}")


if __name__ == '__main__':
    main()
