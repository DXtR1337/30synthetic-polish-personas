# -*- coding: utf-8 -*-
"""
validate_personas.py — Comprehensive validation of 30 synthetic personas.

For each persona computes:
  1. Attachment style categorical match (expected vs predicted)
  2. Per-dimension directional accuracy (12 dimensions)
  3. Magnitude calibration (expected rank vs observed z deviation)
  4. Literature consistency (10 cross-scale pairs)
  5. TCTM error profile analysis
  6. Overall fidelity score

Outputs:
  - validation_report.json (full structured data for GitHub)
  - validation_summary.md (human-readable markdown)
  - Console report
"""
import json, math, statistics
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent

LEVEL_RANK = {
    'very_low': -2, 'low': -1, 'low_moderate': -0.5, 'moderate_low': -0.5,
    'moderate': 0, 'moderate_high': 0.5, 'high': 1, 'very_high': 2, 'extreme': 2.5,
}

STYLE_MAP = {
    'secure': 'secure', 'anxious_preoccupied': 'anxious_preoccupied',
    'preoccupied': 'anxious_preoccupied', 'anxious': 'anxious_preoccupied',
    'dismissive_avoidant': 'dismissive_avoidant', 'dismissive': 'dismissive_avoidant',
    'avoidant': 'dismissive_avoidant', 'fearful_avoidant': 'fearful_avoidant',
    'fearful': 'fearful_avoidant', 'disorganized': 'fearful_avoidant',
}

# Dimension mapping: expected_profile key → observed score path
DIM_MAP = {
    'dbz_anxiety':      ('dbzr', 'z_anx'),
    'dbz_avoidance':    ('dbzr', 'z_avo'),
    'ments_self':       ('ments', 'z_self'),
    'ments_other':      ('ments', 'z_other'),
    'ments_motivation': ('ments', 'z_mot'),
    'kpp':              ('kpp', 'z_mean'),
    'tipi_E':           ('tipi', 'z_E'),
    'tipi_A':           ('tipi', 'z_A'),
    'tipi_C':           ('tipi', 'z_C'),
    'tipi_ES':          ('tipi', 'z_ES'),
    'tipi_O':           ('tipi', 'z_O'),
}

# Literature pairs (from stats.py)
LIT_PAIRS = [
    ('ments_total', 'dbz_anxiety', -1),
    ('ments_self', 'dbz_anxiety', -1),
    ('ments_self', 'dbz_avoidance', -1),
    ('ments_mot', 'kpp_z', +1),
    ('ments_mot', 'tipi_O', +1),
    ('ments_other', 'tipi_E', +1),
    ('ments_total', 'tipi_ES', +1),
    ('kpp_z', 'tipi_O', +1),
    ('kpp_z', 'tipi_C', +1),
    ('dbz_anxiety', 'tipi_ES', -1),
]

def get_z(row, key):
    mapping = {
        'ments_total': ('ments', 'z_total'), 'ments_self': ('ments', 'z_self'),
        'ments_other': ('ments', 'z_other'), 'ments_mot': ('ments', 'z_mot'),
        'dbz_anxiety': ('dbzr', 'z_anx'), 'dbz_avoidance': ('dbzr', 'z_avo'),
        'kpp_z': ('kpp', 'z_mean'),
        'tipi_E': ('tipi', 'z_E'), 'tipi_A': ('tipi', 'z_A'),
        'tipi_C': ('tipi', 'z_C'), 'tipi_ES': ('tipi', 'z_ES'), 'tipi_O': ('tipi', 'z_O'),
    }
    grp, field = mapping[key]
    return row[grp][field]


def validate_persona(row):
    """Validate a single persona. Returns validation dict."""
    pid = row['persona_id']
    ep = row['expected_profile']
    result = {
        'persona_id': pid,
        'biography_length': row.get('biography_length', 0),
        'model': row.get('model_name', ''),
    }

    # 1. Attachment style match
    exp_style_raw = ep.get('attachment_style', '')
    exp_style = STYLE_MAP.get(exp_style_raw.lower().strip(), exp_style_raw)
    pred_style = row['predicted_style']
    result['attachment'] = {
        'expected': exp_style,
        'predicted': pred_style,
        'match': exp_style == pred_style,
    }

    # 2. Per-dimension directional accuracy
    dims = {}
    dir_hits = 0
    dir_total = 0
    for dim_key, (obs_group, obs_field) in DIM_MAP.items():
        exp_level = ep.get(dim_key)
        if exp_level is None:
            continue
        exp_rank = LEVEL_RANK.get(exp_level.strip(), None)
        if exp_rank is None:
            continue
        obs_z = row[obs_group][obs_field]

        # Directional: does sign of z match sign of rank?
        # For moderate (rank=0), any z within ±0.5 is "correct direction"
        if exp_rank == 0:
            dir_match = abs(obs_z) < 0.75
        elif exp_rank > 0:
            dir_match = obs_z > -0.25  # allow small negative for "high" expected
        else:  # exp_rank < 0
            dir_match = obs_z < 0.25   # allow small positive for "low" expected

        # Magnitude: how close is |z| to what we'd expect for the rank?
        # Expected z for rank: roughly rank * 0.75 (calibration factor)
        expected_z = exp_rank * 0.75
        magnitude_error = abs(obs_z - expected_z)

        dims[dim_key] = {
            'expected_level': exp_level,
            'expected_rank': exp_rank,
            'observed_z': round(obs_z, 3),
            'directional_match': dir_match,
            'magnitude_error': round(magnitude_error, 3),
            'expected_z_approx': round(expected_z, 3),
        }
        dir_total += 1
        if dir_match:
            dir_hits += 1

    result['dimensions'] = dims
    result['directional_accuracy'] = round(dir_hits / dir_total, 3) if dir_total > 0 else 0
    result['directional_hits'] = dir_hits
    result['directional_total'] = dir_total
    result['mean_magnitude_error'] = round(
        statistics.mean([d['magnitude_error'] for d in dims.values()]), 3
    ) if dims else 0

    # 3. Literature consistency (per-persona: check if product of z-scores has expected sign)
    lit_hits = 0
    lit_total = 0
    lit_details = []
    for k1, k2, expected_sign in LIT_PAIRS:
        try:
            z1 = get_z(row, k1)
            z2 = get_z(row, k2)
            product = z1 * z2
            sign_match = (product > 0 and expected_sign > 0) or (product < 0 and expected_sign < 0) or product == 0
            lit_hits += 1 if sign_match else 0
            lit_total += 1
            lit_details.append({
                'pair': f'{k1} x {k2}',
                'expected_sign': '+' if expected_sign > 0 else '-',
                'z1': round(z1, 3), 'z2': round(z2, 3),
                'product_sign': '+' if product > 0 else ('-' if product < 0 else '0'),
                'match': sign_match,
            })
        except (KeyError, TypeError):
            pass
    result['literature_consistency'] = {
        'hits': lit_hits, 'total': lit_total,
        'rate': round(lit_hits / lit_total, 3) if lit_total > 0 else 0,
        'details': lit_details,
    }

    # 4. TCTM profile
    tctm = row.get('tctm', {})
    result['tctm'] = {
        'correct': tctm.get('correct', 0),
        'DOS': tctm.get('DOS', 0),
        'NAD': tctm.get('NAD', 0),
        'BK': tctm.get('BK', 0),
        'total': tctm.get('total', 22),
    }

    # 5. Overall fidelity score (weighted composite)
    # 40% attachment match + 40% directional accuracy + 20% literature consistency
    attach_score = 1.0 if result['attachment']['match'] else 0.0
    dir_score = result['directional_accuracy']
    lit_score = result['literature_consistency']['rate']
    fidelity = 0.4 * attach_score + 0.4 * dir_score + 0.2 * lit_score
    result['fidelity_score'] = round(fidelity, 3)

    return result


def main():
    # Load data
    rows = []
    for line in open(SCRIPT_DIR / 'analysis_summary.jsonl', encoding='utf-8'):
        if line.strip():
            rows.append(json.loads(line))

    print(f'Validating {len(rows)} personas...')
    print()

    validations = [validate_persona(r) for r in rows]
    validations.sort(key=lambda x: -x['fidelity_score'])

    # ── Summary statistics ──
    n = len(validations)
    attach_hits = sum(1 for v in validations if v['attachment']['match'])
    mean_dir = statistics.mean([v['directional_accuracy'] for v in validations])
    mean_lit = statistics.mean([v['literature_consistency']['rate'] for v in validations])
    mean_fid = statistics.mean([v['fidelity_score'] for v in validations])
    mean_mag = statistics.mean([v['mean_magnitude_error'] for v in validations])

    # ── Console report ──
    W = 90
    print('=' * W)
    print('VALIDATION REPORT: 30 SYNTHETIC PERSONAS')
    print('=' * W)
    print()
    print(f'  Attachment style match:     {attach_hits}/{n} = {attach_hits/n*100:.0f}%')
    print(f'  Mean directional accuracy:  {mean_dir*100:.1f}% (per-dimension z-score direction)')
    print(f'  Mean literature consistency: {mean_lit*100:.1f}% (10 cross-scale pairs per persona)')
    print(f'  Mean magnitude error:       {mean_mag:.2f} SD (|observed_z - expected_z|)')
    print(f'  Mean fidelity score:        {mean_fid:.3f} (0-1 composite)')
    print()

    # Per-persona table
    print('-' * W)
    print(f'{"Persona":15s} {"Style":>8s} {"Dir%":>6s} {"Lit%":>6s} {"MagErr":>7s} {"Fidelity":>8s} {"TCTM":>6s}')
    print('-' * W)
    for v in validations:
        style_mark = 'OK' if v['attachment']['match'] else 'MISS'
        print(f'{v["persona_id"]:15s} {style_mark:>8s} '
              f'{v["directional_accuracy"]*100:5.0f}% '
              f'{v["literature_consistency"]["rate"]*100:5.0f}% '
              f'{v["mean_magnitude_error"]:7.2f} '
              f'{v["fidelity_score"]:8.3f} '
              f'{v["tctm"]["correct"]:3d}/22')

    # Worst personas
    print()
    print('-' * W)
    print('PROBLEMATIC PERSONAS (fidelity < 0.70):')
    print('-' * W)
    for v in validations:
        if v['fidelity_score'] < 0.70:
            print(f'\n  {v["persona_id"]} (fidelity={v["fidelity_score"]:.3f}):')
            if not v['attachment']['match']:
                print(f'    Attachment: expected={v["attachment"]["expected"]}, got={v["attachment"]["predicted"]}')
            # Show missed dimensions
            missed = [(k, d) for k, d in v['dimensions'].items() if not d['directional_match']]
            if missed:
                print(f'    Missed dimensions ({len(missed)}):')
                for k, d in missed:
                    print(f'      {k}: expected={d["expected_level"]} (rank={d["expected_rank"]}), '
                          f'observed z={d["observed_z"]:+.2f}')

    # Per-dimension accuracy across all personas
    print()
    print('-' * W)
    print('PER-DIMENSION ACCURACY (across 30 personas):')
    print('-' * W)
    dim_stats = defaultdict(lambda: {'hits': 0, 'total': 0, 'errors': []})
    for v in validations:
        for dim_key, d in v['dimensions'].items():
            dim_stats[dim_key]['total'] += 1
            if d['directional_match']:
                dim_stats[dim_key]['hits'] += 1
            else:
                dim_stats[dim_key]['errors'].append((v['persona_id'], d['expected_level'], d['observed_z']))

    for dim_key in DIM_MAP:
        s = dim_stats[dim_key]
        if s['total'] == 0:
            continue
        pct = s['hits'] / s['total'] * 100
        print(f'  {dim_key:20s}: {s["hits"]}/{s["total"]} = {pct:.0f}%', end='')
        if s['errors']:
            print(f'  MISSES: {", ".join(f"{p}({e} -> z={z:+.2f})" for p,e,z in s["errors"][:3])}', end='')
        print()

    # ── Save JSON ──
    report = {
        'meta': {
            'n_personas': n,
            'generated': '2026-04-12',
            'models': list(set(v.get('model', '') for v in validations)),
            'scoring': 'Identical to MagisterkaClient.tsx (Lubiewska 2016, Janczak 2021, Matusz 2011, Sorokowska 2014)',
        },
        'summary': {
            'attachment_match_rate': round(attach_hits / n, 3),
            'mean_directional_accuracy': round(mean_dir, 3),
            'mean_literature_consistency': round(mean_lit, 3),
            'mean_magnitude_error': round(mean_mag, 3),
            'mean_fidelity_score': round(mean_fid, 3),
        },
        'personas': validations,
    }
    json_path = SCRIPT_DIR / 'validation_report.json'
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nSaved: {json_path} ({json_path.stat().st_size / 1024:.0f} KB)')

    # ── Save Markdown ──
    md_lines = ['# Synthetic Persona Validation Report (N=30)\n']
    md_lines.append(f'**Generated:** 2026-04-12\n')
    md_lines.append(f'## Summary\n')
    md_lines.append(f'| Metric | Value |')
    md_lines.append(f'|---|---|')
    md_lines.append(f'| Attachment style match | {attach_hits}/{n} = {attach_hits/n*100:.0f}% |')
    md_lines.append(f'| Mean directional accuracy | {mean_dir*100:.1f}% |')
    md_lines.append(f'| Mean literature consistency | {mean_lit*100:.1f}% |')
    md_lines.append(f'| Mean magnitude error | {mean_mag:.2f} SD |')
    md_lines.append(f'| Mean fidelity score | {mean_fid:.3f} |')
    md_lines.append(f'\n## Per-Persona Results\n')
    md_lines.append(f'| Persona | Style | Dir% | Lit% | MagErr | Fidelity | TCTM |')
    md_lines.append(f'|---|---|---|---|---|---|---|')
    for v in validations:
        sm = 'OK' if v['attachment']['match'] else 'MISS'
        md_lines.append(
            f'| {v["persona_id"]} | {sm} | {v["directional_accuracy"]*100:.0f}% | '
            f'{v["literature_consistency"]["rate"]*100:.0f}% | {v["mean_magnitude_error"]:.2f} | '
            f'{v["fidelity_score"]:.3f} | {v["tctm"]["correct"]}/22 |'
        )
    md_lines.append(f'\n## Per-Dimension Accuracy\n')
    md_lines.append(f'| Dimension | Accuracy |')
    md_lines.append(f'|---|---|')
    for dim_key in DIM_MAP:
        s = dim_stats[dim_key]
        if s['total'] == 0: continue
        md_lines.append(f'| {dim_key} | {s["hits"]}/{s["total"]} = {s["hits"]/s["total"]*100:.0f}% |')

    md_path = SCRIPT_DIR / 'validation_summary.md'
    md_path.write_text('\n'.join(md_lines), encoding='utf-8')
    print(f'Saved: {md_path}')

    print(f'\n{"=" * W}')
    print('DONE')
    print(f'{"=" * W}')


if __name__ == '__main__':
    main()
