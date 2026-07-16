# -*- coding: utf-8 -*-
"""
Figures for the BRM submission manuscript — all computed from the released CSVs
(all_data_v20.csv + tctm57_runs_v20.csv), corrected-stimulus collection as primary.

  fig1_persona_validation.pdf  7x30 style-classification matrix (corrected, run 1)
  fig2_baseline_intercepts.pdf per-model baseline z-intercepts, M+-SD (corrected, n=10)
  fig3_persona_slope_matrix.pdf 7x7 median-r heatmap (corrected per-persona means)
  fig4_avo_bimodality.pdf      GPT-5.4 baseline AVO: initial N=31 + corrected n=10
  fig5_masc_fingerprint.pdf    MASC error composition per model (corrected)
  fig6_testretest.pdf          within-collection test-retest (corrected runs 1-2)
  fig7_natural_experiment.pdf  affected items: truncated -> corrected, 7 models
  fig8_longitudinal.pdf        cross-window slope stability + largest intercept drifts
  fig9_admin_context.pdf       2x2 stimulus x battery (Sonnet, GPT-5.5; s07/w19/w22)
"""
import csv
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.colors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]   # paper-brm/figures -> docs/paper/magisterka
SYNTH = ROOT / 'synthetic'
OUT = Path(__file__).parent

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 11,
    'legend.fontsize': 9,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})

MODELS = ['Claude Sonnet 4.6', 'Claude Opus 4.6', 'GPT-5.4-mini', 'GPT-5.4',
          'GPT-5.5', 'Grok-4-20', 'Gemini 3 Flash']
SHORT = {m: s for m, s in zip(MODELS, ['Sonnet', 'Opus', '5.4-mini', '5.4 (full)',
                                       'GPT-5.5', 'Grok', 'Gemini'])}
COLOR = {'Claude Sonnet 4.6': '#7a5dc7', 'Claude Opus 4.6': '#9d7bd6',
         'GPT-5.4-mini': '#a8c8a0', 'GPT-5.4': '#3b8c3b', 'GPT-5.5': '#1d5f1d',
         'Grok-4-20': '#d97757', 'Gemini 3 Flash': '#1e88e5'}
AZURE = {'GPT-5.4-mini', 'GPT-5.4', 'GPT-5.5', 'Grok-4-20'}
CORR_WAVE = {m: (3 if m in AZURE else 4) for m in MODELS}
Z_DIMS = ['z_anx', 'z_avo', 'z_ments_total', 'z_kpp', 'z_e', 'z_a', 'z_c', 'z_es', 'z_o']
DIM_LAB = ['DBZ-R\nAnx', 'DBZ-R\nAvo', 'MentS\ntotal', 'KPP\nmean',
           'TIPI\nE', 'TIPI\nA', 'TIPI\nC', 'TIPI\nES', 'TIPI\nO']

PERSONAS = ['adrian', 'agata', 'ania', 'anna-sim', 'bartek', 'dominika', 'ewa', 'filip',
            'gabriela', 'hubert', 'jakub', 'jola', 'kamil', 'kasia', 'klaudia', 'kuba',
            'lukasz', 'magda', 'marek', 'michal-k', 'michal-sim', 'natalia', 'ola',
            'pawel', 'piotr', 'radek', 'sara', 'tomek', 'weronika', 'zuzia']

with open(SYNTH / 'all_data_v20.csv', encoding='utf-8-sig') as f:
    ROWS = list(csv.DictReader(f))
with open(SYNTH / 'tctm57_runs_v20.csv', encoding='utf-8-sig') as f:
    ROWS57 = list(csv.DictReader(f))

for r in ROWS:
    r['wave'] = int(r['wave'])
    if r['model'] == 'Human':
        r['collection'] = 'human'
    elif r['wave'] in (1, 2):
        r['collection'] = 'initial'
    elif r['wave'] == CORR_WAVE.get(r['model'], -1):
        r['collection'] = 'corrected'
    else:
        r['collection'] = 'other'


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    mx = statistics.mean(p[0] for p in pairs)
    my = statistics.mean(p[1] for p in pairs)
    num = sum((p[0] - mx) * (p[1] - my) for p in pairs)
    dx = math.sqrt(sum((p[0] - mx) ** 2 for p in pairs))
    dy = math.sqrt(sum((p[1] - my) ** 2 for p in pairs))
    return num / (dx * dy) if dx * dy > 0 else None


def persona_means(collection, dims):
    """model -> persona -> [mean over runs for each dim]"""
    acc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in ROWS:
        if r['condition'] != 'persona' or r['collection'] != collection:
            continue
        for d in dims:
            v = fnum(r[d])
            if v is not None:
                acc[r['model']][r['persona']][d].append(v)
    out = {}
    for m, per in acc.items():
        out[m] = {p: [statistics.mean(per[p][d]) if per[p][d] else None for d in dims]
                  for p in per}
    return out


def expected_styles():
    NORM = {'disorganized': 'fearful_avoidant'}
    out = {}
    for p in PERSONAS:
        text = (SYNTH / f'{p}.md').read_text(encoding='utf-8')
        m = re.search(r'attachment_style:\s*([\w_]+)', text) or re.search(r'style:\s*([a-z_]+)', text)
        out[p] = NORM.get(m.group(1), m.group(1))
    return out


# ===================================================================
def fig1_persona_validation():
    expected = expected_styles()
    matrix = defaultdict(dict)
    for r in ROWS:
        if r['condition'] == 'persona' and r['collection'] == 'corrected' and r['run'] == '1':
            matrix[r['persona']][r['model']] = r['style']

    M = np.full((len(PERSONAS), len(MODELS)), np.nan)
    annots = [['' for _ in MODELS] for _ in PERSONAS]
    ST = {'secure': 'S', 'anxious_preoccupied': 'A', 'dismissive_avoidant': 'D',
          'fearful_avoidant': 'F'}
    for i, p in enumerate(PERSONAS):
        for j, m in enumerate(MODELS):
            got = matrix.get(p, {}).get(m)
            if got is None:
                continue
            M[i, j] = 1.0 if got == expected[p] else 0.0
            annots[i][j] = ST.get(got, '?')

    fig, ax = plt.subplots(figsize=(8, 9))
    cmap = matplotlib.colors.ListedColormap(['#f4cfd4', '#bce0bc'])
    ax.imshow(M, aspect='auto', cmap=cmap, vmin=0, vmax=1)
    for i in range(len(PERSONAS)):
        for j in range(len(MODELS)):
            ax.text(j, i, annots[i][j], ha='center', va='center', fontsize=8, color='#222')
    ax.set_xticks(range(len(MODELS)))
    ax.set_xticklabels([SHORT[m] for m in MODELS], rotation=45, ha='right')
    ax.set_yticks(range(len(PERSONAS)))
    ax.set_yticklabels([f'{p} [{ST[expected[p]]}]' for p in PERSONAS], fontsize=8)
    ax.set_xlabel('Model')
    ax.set_ylabel('Persona [author-declared style]')
    ax.set_title('Per-persona attachment-style classification (corrected stimulus, run 1)\n'
                 'Green = matches author label; pink = mismatch')
    handles = [mpatches.Patch(color='#bce0bc', label='Match'),
               mpatches.Patch(color='#f4cfd4', label='Mismatch')]
    ax.legend(handles=handles, loc='lower left', bbox_to_anchor=(0, -0.12), ncol=2, frameon=False)
    ax.set_xticks(np.arange(-0.5, len(MODELS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(PERSONAS), 1), minor=True)
    ax.grid(which='minor', color='white', linewidth=1)
    plt.tight_layout()
    plt.savefig(OUT / 'fig1_persona_validation.pdf', bbox_inches='tight')
    plt.close()
    print('fig1_persona_validation.pdf')


# ===================================================================
def fig2_baseline_intercepts():
    means, sds = {}, {}
    for m in MODELS:
        rs = [r for r in ROWS if r['condition'] == 'baseline' and r['model'] == m
              and r['collection'] == 'corrected']
        means[m], sds[m] = [], []
        for d in Z_DIMS:
            vals = [fnum(r[d]) for r in rs]
            vals = [v for v in vals if v is not None]
            means[m].append(statistics.mean(vals))
            sds[m].append(statistics.stdev(vals) if len(vals) > 1 else 0)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(Z_DIMS))
    width = 0.11
    for i, m in enumerate(MODELS):
        ax.bar(x + (i - 3) * width, means[m], width, yerr=sds[m], capsize=1.5,
               error_kw={'lw': 0.7}, label=SHORT[m], color=COLOR[m], edgecolor='none')
    ax.axhline(0, color='black', linewidth=0.6, linestyle='--', alpha=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(DIM_LAB, fontsize=9)
    ax.set_ylabel('z vs Polish population norm')
    ax.set_title('Baseline-condition intercepts (corrected stimulus, n = 10 runs per model)\n'
                 'Bars = M, whiskers = SD; positive = above human norm')
    ax.legend(loc='upper left', ncol=4, fontsize=8, frameon=False, bbox_to_anchor=(0, -0.13))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT / 'fig2_baseline_intercepts.pdf', bbox_inches='tight')
    plt.close()
    print('fig2_baseline_intercepts.pdf')


# ===================================================================
def fig3_persona_slope_matrix():
    pm = persona_means('corrected', Z_DIMS)
    M = np.eye(len(MODELS))
    for i, m1 in enumerate(MODELS):
        for j, m2 in enumerate(MODELS):
            if i == j:
                continue
            common = sorted(set(pm[m1]) & set(pm[m2]))
            rs = []
            for k in range(len(Z_DIMS)):
                r = pearson([pm[m1][p][k] for p in common], [pm[m2][p][k] for p in common])
                if r is not None:
                    rs.append(r)
            M[i, j] = statistics.median(rs)

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(M, cmap='RdYlGn', vmin=0.90, vmax=1.0)
    for i in range(len(MODELS)):
        for j in range(len(MODELS)):
            ax.text(j, i, f'{M[i, j]:.2f}', ha='center', va='center', fontsize=10, color='black')
    ax.set_xticks(range(len(MODELS)))
    ax.set_xticklabels([SHORT[m] for m in MODELS], rotation=45, ha='right')
    ax.set_yticks(range(len(MODELS)))
    ax.set_yticklabels([SHORT[m] for m in MODELS])
    ax.set_title('Cross-model agreement on persona-conditional responses\n'
                 '(median Pearson r across 9 z-dimensions; corrected stimulus,\n'
                 'per-persona means over two administrations, N = 30 personas)')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='Median r')
    plt.tight_layout()
    plt.savefig(OUT / 'fig3_persona_slope_matrix.pdf', bbox_inches='tight')
    plt.close()
    print('fig3_persona_slope_matrix.pdf')


# ===================================================================
def fig4_avo_bimodality():
    init = sorted(fnum(r['avo_mean']) for r in ROWS
                  if r['condition'] == 'baseline' and r['model'] == 'GPT-5.4'
                  and r['collection'] == 'initial' and r['avo_mean'])
    corr = sorted(fnum(r['avo_mean']) for r in ROWS
                  if r['condition'] == 'baseline' and r['model'] == 'GPT-5.4'
                  and r['collection'] == 'corrected' and r['avo_mean'])

    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(8, 5.2), sharex=True,
                                  gridspec_kw={'height_ratios': [3, 1]})
    bins = np.arange(2.0, 6.75, 0.25)
    counts, _, _ = ax.hist(init, bins=bins, color='#3b8c3b', edgecolor='white', alpha=0.85)
    ax.axvspan(3.50, 4.06, color='#ffd1c8', alpha=0.6, label='Largest gap (0.556)')
    ax.axvline(4.0, color='black', linestyle='--', linewidth=1, label='Style threshold Avo = 4')
    lower = [v for v in init if v < 4]
    upper = [v for v in init if v >= 4]
    ax.axvline(statistics.mean(lower), color='#1d5f1d', linestyle=':', linewidth=1, alpha=0.7,
               label=f'Lower cluster M = {statistics.mean(lower):.2f}')
    ax.axvline(statistics.mean(upper), color='#0d3d0d', linestyle=':', linewidth=1, alpha=0.7,
               label=f'Upper cluster M = {statistics.mean(upper):.2f}')
    for v in init:
        ax.plot([v, v], [-0.25, 0], color='black', linewidth=0.8, alpha=0.7, clip_on=False)
    ax.set_ylabel('Baseline runs (count)')
    ax.set_title('GPT-5.4 (full) baseline avoidance distribution\n'
                 f'Top: initial collection (N = {len(init)}); bottom: corrected collection (n = {len(corr)})')
    ax.set_ylim(-0.4, max(counts) + 1)
    ax.legend(loc='upper left', fontsize=8, frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax2.axvline(4.0, color='black', linestyle='--', linewidth=1)
    ax2.plot(corr, np.zeros(len(corr)), 'o', color='#3b8c3b', ms=7, alpha=0.75)
    ax2.set_yticks([])
    ax2.set_xlabel('DBZ-R Avoidance mean (1-7 Likert scale)')
    ax2.set_xlim(1.8, 6.6)
    nb = sum(1 for v in corr if v < 4)
    ax2.text(0.99, 0.78, f'corrected: {nb} below / {len(corr) - nb} at-or-above threshold',
             transform=ax2.transAxes, ha='right', fontsize=8)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT / 'fig4_avo_bimodality.pdf', bbox_inches='tight')
    plt.close()
    print('fig4_avo_bimodality.pdf')


# ===================================================================
def fig5_masc_fingerprint():
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, cond, title in [(axes[0], 'baseline', 'Baseline (model as itself)'),
                            (axes[1], 'persona', 'Persona (model as biography)')]:
        labels, correct, dos, nad, bk = [], [], [], [], []
        for m in MODELS:
            rs = [r for r in ROWS if r['condition'] == cond and r['model'] == m
                  and r['collection'] == 'corrected']
            tot = sum(int(r['tctm_total']) for r in rs)
            if tot == 0:
                continue
            labels.append(SHORT[m])
            correct.append(sum(int(r['tctm_correct']) for r in rs) / tot * 100)
            dos.append(sum(int(r['dos']) for r in rs if r['dos']) / tot * 100)
            nad.append(sum(int(r['nad']) for r in rs if r['nad']) / tot * 100)
            bk.append(sum(int(r['bk']) for r in rs if r['bk']) / tot * 100)
        x = np.arange(len(labels))
        ax.bar(x, correct, color='#bce0bc', edgecolor='white', label='Correct')
        ax.bar(x, dos, bottom=correct, color='#7a9cc6', edgecolor='white',
               label='DOS (undermentalizing)')
        ax.bar(x, nad, bottom=[c + d for c, d in zip(correct, dos)], color='#e57373',
               edgecolor='white', label='NAD (overmentalizing)')
        ax.bar(x, bk, bottom=[c + d + n for c, d, n in zip(correct, dos, nad)],
               color='#9b9b9b', edgecolor='white', label='BK (no mentalization)')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
        ax.set_title(title)
        ax.set_ylim(0, 100)
        ax.set_ylabel('% of TCTM items' if ax is axes[0] else '')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        if ax is axes[1]:
            ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), fontsize=9, frameon=False)
    fig.suptitle('MASC error fingerprint per model and condition (corrected stimulus)', fontsize=12)
    plt.tight_layout()
    plt.savefig(OUT / 'fig5_masc_fingerprint.pdf', bbox_inches='tight')
    plt.close()
    print('fig5_masc_fingerprint.pdf')


# ===================================================================
def fig6_testretest():
    tctm_rs, zmed_rs, labels = [], [], []
    for m in MODELS:
        by_pp = defaultdict(dict)
        for r in ROWS:
            if r['condition'] == 'persona' and r['model'] == m and r['collection'] == 'corrected':
                by_pp[r['persona']][r['run']] = r
        paired = [(by_pp[p]['1'], by_pp[p]['2']) for p in by_pp
                  if '1' in by_pp[p] and '2' in by_pp[p]]
        labels.append(SHORT[m])
        tctm_rs.append(pearson([fnum(a['tctm_correct']) for a, b in paired],
                               [fnum(b['tctm_correct']) for a, b in paired]) or 0)
        zrs = [pearson([fnum(a[d]) for a, b in paired], [fnum(b[d]) for a, b in paired])
               for d in Z_DIMS]
        zmed_rs.append(statistics.median([r for r in zrs if r is not None]))

    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(labels))
    width = 0.35
    ax.bar(x - width / 2, zmed_rs, width, color='#9d7bd6', edgecolor='white',
           label='Median r across 9 self-report z-dims')
    ax.bar(x + width / 2, tctm_rs, width, color='#d97757', edgecolor='white',
           label='TCTM-22 total r')
    for i, (z, t) in enumerate(zip(zmed_rs, tctm_rs)):
        ax.text(i - width / 2, z + 0.02, f'{z:.2f}', ha='center', fontsize=8)
        ax.text(i + width / 2, t + 0.02, f'{t:.2f}', ha='center', fontsize=8)
    ax.axhline(0.5, color='black', linestyle='--', linewidth=0.6, alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_ylabel('Pearson r (administration 1 vs 2)')
    ax.set_ylim(0, 1.1)
    ax.set_title('Test-retest stability within the corrected collection (30 paired persona runs)')
    ax.legend(loc='lower right', fontsize=9, frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT / 'fig6_testretest.pdf', bbox_inches='tight')
    plt.close()
    print('fig6_testretest.pdf')


# ===================================================================
def item_acc(model, item, collection):
    ok = n = 0
    for r in ROWS:
        if r['model'] != model or r['condition'] != 'persona' or r['collection'] != collection:
            continue
        v = r.get(f'tctm_{item}', '')
        if v == '':
            continue
        n += 1
        ok += int(v)
    return (100.0 * ok / n if n else float('nan')), n


def fig7_natural_experiment():
    items = ['s07', 'w19', 'pw07', 'w22']
    fig, axes = plt.subplots(1, 4, figsize=(12.6, 4.6), sharey=True)
    for ii, (ax, item) in enumerate(zip(axes, items)):
        for mi, model in enumerate(MODELS):
            y = len(MODELS) - 1 - mi
            a, _ = item_acc(model, item, 'initial')
            b, _ = item_acc(model, item, 'corrected')
            c = COLOR[model]
            ax.plot([a, b], [y, y], color=c, lw=1.6, alpha=0.55, zorder=1)
            ax.scatter([a], [y], facecolor='white', edgecolor=c, s=40, zorder=2,
                       label='Truncated' if (ii == 0 and mi == 0) else None)
            ax.scatter([b], [y], facecolor=c, edgecolor=c, s=44, zorder=3,
                       label='Corrected' if (ii == 0 and mi == 0) else None)
            if abs(b - a) > 12:
                ax.annotate('', xy=(b, y), xytext=(a, y),
                            arrowprops=dict(arrowstyle='-|>', color=c, lw=1.3))
        ax.set_yticks(range(len(MODELS)))
        if ii == 0:
            ax.set_yticklabels([SHORT[m] for m in reversed(MODELS)])
        ax.set_xlim(-5, 105)
        ax.set_title(item)
        ax.grid(axis='x', alpha=0.25, lw=0.6)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    axes[0].legend(loc='lower right', fontsize=8, framealpha=0.9)
    fig.supxlabel('Author-key agreement (%), persona condition, all runs pooled', fontsize=10)
    fig.suptitle('Correction-affected items: truncated stimulus (initial collection) '
                 'vs corrected stimulus', fontsize=11)
    plt.tight_layout(rect=(0, 0.02, 1, 1))
    plt.savefig(OUT / 'fig7_natural_experiment.pdf', bbox_inches='tight')
    plt.close()
    print('fig7_natural_experiment.pdf')


# ===================================================================
def fig8_longitudinal():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4),
                                   gridspec_kw={'width_ratios': [1.45, 1.0]})
    # (a) per-dimension cross-window persona-stability r (7 models)
    pm_i = persona_means('initial', Z_DIMS)
    pm_c = persona_means('corrected', Z_DIMS)
    xpos = np.arange(len(Z_DIMS))
    for mi, model in enumerate(MODELS):
        common = sorted(set(pm_i[model]) & set(pm_c[model]))
        rs = []
        for k in range(len(Z_DIMS)):
            rs.append(pearson([pm_i[model][p][k] for p in common],
                              [pm_c[model][p][k] for p in common]))
        ax1.plot(xpos + (mi - 3) * 0.09, rs, 'o', color=COLOR[model], ms=4.5,
                 label=SHORT[model])
    ax1.set_xticks(xpos)
    ax1.set_xticklabels([l.replace('\n', ' ') for l in DIM_LAB], rotation=30, ha='right', fontsize=8)
    ax1.set_ylim(0.82, 1.01)
    ax1.axhline(1.0, color='#999999', lw=0.7, ls=':')
    ax1.set_ylabel('Pearson r (initial vs corrected)')
    ax1.set_title('(a) Persona-slope stability across collections')
    ax1.grid(axis='y', alpha=0.25, lw=0.6)
    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.26), ncol=4, fontsize=8,
               frameon=False)

    # (b) largest baseline-intercept drifts (z-scale dumbbells)
    drifts = []
    for model in MODELS:
        gi = [r for r in ROWS if r['model'] == model and r['condition'] == 'baseline'
              and r['collection'] == 'initial']
        gc = [r for r in ROWS if r['model'] == model and r['condition'] == 'baseline'
              and r['collection'] == 'corrected']
        for d, lab in zip(Z_DIMS, [l.replace('\n', ' ') for l in DIM_LAB]):
            vi = [fnum(r[d]) for r in gi]
            vi = [v for v in vi if v is not None]
            vc = [fnum(r[d]) for r in gc]
            vc = [v for v in vc if v is not None]
            drifts.append((abs(statistics.mean(vc) - statistics.mean(vi)), model, lab,
                           statistics.mean(vi), statistics.mean(vc)))
    drifts.sort(reverse=True)
    top = drifts[:6][::-1]
    for yi, (mag, model, lab, mi_, mc_) in enumerate(top):
        c = COLOR[model]
        ax2.plot([mi_, mc_], [yi, yi], color=c, lw=1.6, alpha=0.6)
        ax2.scatter([mi_], [yi], facecolor='white', edgecolor=c, s=44, zorder=3)
        ax2.scatter([mc_], [yi], facecolor=c, edgecolor=c, s=48, zorder=3)
        ax2.annotate('', xy=(mc_, yi), xytext=(mi_, yi),
                     arrowprops=dict(arrowstyle='-|>', color=c, lw=1.3))
    ax2.set_yticks(range(len(top)))
    ax2.set_yticklabels([f'{SHORT[m]} · {lab}' for _, m, lab, _, _ in top], fontsize=8)
    ax2.axvline(0, color='#999999', lw=0.7, ls=':')
    ax2.set_xlabel('Baseline M (z vs Polish norm)')
    ax2.set_title('(b) Six largest intercept drifts\n(open = initial, filled = corrected)')
    ax2.grid(axis='x', alpha=0.25, lw=0.6)
    plt.tight_layout()
    plt.savefig(OUT / 'fig8_longitudinal.pdf', bbox_inches='tight')
    plt.close()
    print('fig8_longitudinal.pdf')


# ===================================================================
def fig9_admin_context():
    def acc57(model, item, wave):
        ok = n = 0
        for r in ROWS57:
            if r['model'] != model or int(r['wave']) != wave:
                continue
            v = r.get(f'tctm_{item}', '')
            if v == '':
                continue
            n += 1
            ok += int(v)
        return 100.0 * ok / n if n else float('nan')

    models = ['Claude Sonnet 4.6', 'GPT-5.5']
    items = ['s07', 'w19', 'w22']
    fig, axes = plt.subplots(2, 3, figsize=(8.4, 5.2))
    for mi, model in enumerate(models):
        for ii, item in enumerate(items):
            ax = axes[mi][ii]
            grid = np.array([
                [item_acc(model, item, 'initial')[0], item_acc(model, item, 'corrected')[0]],
                [acc57(model, item, 1), acc57(model, item, 5)],
            ])
            ax.imshow(grid, cmap='RdYlGn', vmin=0, vmax=100, aspect='auto')
            for (yy, xx), val in np.ndenumerate(grid):
                ax.text(xx, yy, f'{val:.0f}%', ha='center', va='center', fontsize=11,
                        fontweight='bold',
                        color='black' if 25 < val < 90 else ('white' if val <= 25 else 'black'))
            ax.set_xticks([0, 1])
            ax.set_xticklabels(['truncated', 'corrected'], fontsize=8)
            ax.set_yticks([0, 1])
            ax.set_yticklabels(['22-item', '57-item'], fontsize=8)
            if mi == 0:
                ax.set_title(item)
            if ii == 0:
                ax.set_ylabel(SHORT[model], fontsize=11)
    fig.suptitle('Administration-context effect: stimulus version × battery composition\n'
                 '(author-key agreement, %)', fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    plt.savefig(OUT / 'fig9_admin_context.pdf', bbox_inches='tight')
    plt.close()
    print('fig9_admin_context.pdf')


if __name__ == '__main__':
    fig1_persona_validation()
    fig2_baseline_intercepts()
    fig3_persona_slope_matrix()
    fig4_avo_bimodality()
    fig5_masc_fingerprint()
    fig6_testretest()
    fig7_natural_experiment()
    fig8_longitudinal()
    fig9_admin_context()
    print('All figures done')
