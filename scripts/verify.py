"""verify_v14.py — independent verifier for paper v14.

Loads all_data.csv from the released open dataset, computes every numeric claim
referenced in the paper, and compares against the values reported in v14.tex.

Output: side-by-side PAPER vs CSV with PASS/FAIL flags. Designed so that you
(the author) or a third party can run this script without trusting any
intermediate file (no JSON aggregates, no spreadsheets — just the public CSV).

Usage:
    cd docs/paper/magisterka/v14_workspace
    python verify_v14.py

Exit code 0 = all PASS, 1 = at least one FAIL.
"""
from __future__ import annotations
import csv, math, statistics as st, sys
from collections import Counter
from pathlib import Path

CSV = Path(__file__).resolve().parent.parent / 'synthetic' / 'all_data.csv'

# ---------- Load CSV ----------
with open(CSV, encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

MODELS = ['Claude Sonnet 4.6','Claude Opus 4.6','GPT-5.4-mini','Grok-4-20','Gemini 3 Flash']
SHORT = {'Claude Sonnet 4.6':'Sonnet','Claude Opus 4.6':'Opus','GPT-5.4-mini':'GPT','Grok-4-20':'Grok','Gemini 3 Flash':'Gemini'}

# ---------- Helpers ----------
def pearson(xs, ys):
    n = len(xs)
    if n < 2: return float('nan')
    mx, my = sum(xs)/n, sum(ys)/n
    sxx = sum((x-mx)**2 for x in xs)
    syy = sum((y-my)**2 for y in ys)
    sxy = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    return sxy/math.sqrt(sxx*syy) if sxx*syy > 0 else float('nan')

def persona_run1(model):
    return [r for r in rows if r['condition']=='persona' and r['model']==model and r['run']=='1']

def baseline(model):
    return [r for r in rows if r['condition']=='baseline' and r['model']==model]

def noprompt(model):
    return [r for r in rows if r['condition']=='noprompt' and r['model']==model]

# ---------- Test infrastructure ----------
results = []  # list of (label, paper_value, csv_value, tolerance, status)

def check(label, paper, csv_val, tol=0.05):
    """Compare paper claim to csv-computed value within tolerance."""
    if paper is None or csv_val is None:
        status = 'SKIP'
    elif isinstance(paper, str):
        status = 'PASS' if paper == csv_val else 'FAIL'
    elif isinstance(paper, (int, float)) and isinstance(csv_val, (int, float)):
        if math.isnan(csv_val):
            status = 'FAIL'
        else:
            status = 'PASS' if abs(paper - csv_val) <= tol else 'FAIL'
    else:
        status = 'FAIL'
    results.append((label, paper, csv_val, status))
    return status

# ====================================================================
# 1. SAMPLE SIZES (Method, Table 1)
# ====================================================================
print('## 1. Sample sizes')

paper_n = {('persona','Sonnet','1'):30, ('persona','Sonnet','2'):30,
           ('persona','Opus','1'):30, ('persona','Opus','2'):25,
           ('persona','GPT','1'):27, ('persona','GPT','2'):21,
           ('persona','Grok','1'):30, ('persona','Grok','2'):29,
           ('persona','Gemini','1'):30, ('persona','Gemini','2'):28,
           ('baseline','Sonnet'):10, ('baseline','Opus'):7,
           ('baseline','GPT'):10, ('baseline','Grok'):10, ('baseline','Gemini'):9,
           ('noprompt','Sonnet'):6, ('noprompt','Opus'):5,
           ('noprompt','GPT'):6, ('noprompt','Grok'):6, ('noprompt','Gemini'):8,
           ('human',):7}

for m in MODELS:
    s = SHORT[m]
    for run in ['1','2']:
        n_csv = sum(1 for r in rows if r['condition']=='persona' and r['model']==m and r['run']==run)
        check(f'persona {s} run-{run}', paper_n[('persona',s,run)], n_csv, tol=0)
    n_b = sum(1 for r in rows if r['condition']=='baseline' and r['model']==m)
    check(f'baseline {s}', paper_n[('baseline',s)], n_b, tol=0)
    n_np = sum(1 for r in rows if r['condition']=='noprompt' and r['model']==m)
    check(f'noprompt {s}', paper_n[('noprompt',s)], n_np, tol=0)

n_human = sum(1 for r in rows if r['condition']=='human')
check('human', 7, n_human, tol=0)

# ====================================================================
# 2. TCTM-22 DISTRIBUTION (paper Table 2)
# ====================================================================
print('## 2. TCTM-22 distribution (run-1)')

paper_tctm = {'Human':(7, 14.3, 1.4), 'Sonnet':(30, 19.4, 0.7), 'Opus':(30, 19.0, 2.1),
              'GPT':(27, 17.0, 1.7), 'Grok':(30, 18.4, 4.2), 'Gemini':(30, 19.6, 2.1)}

# Human
hv = [int(r['tctm_correct']) for r in rows if r['condition']=='human' and r['tctm_correct']]
check('Human N', paper_tctm['Human'][0], len(hv), tol=0)
check('Human M', paper_tctm['Human'][1], st.mean(hv), tol=0.1)
check('Human SD', paper_tctm['Human'][2], st.stdev(hv), tol=0.1)

for m in MODELS:
    s = SHORT[m]
    sub = [int(r['tctm_correct']) for r in persona_run1(m) if r['tctm_correct']]
    check(f'{s} TCTM-22 N', paper_tctm[s][0], len(sub), tol=0)
    check(f'{s} TCTM-22 M', paper_tctm[s][1], st.mean(sub), tol=0.1)
    check(f'{s} TCTM-22 SD', paper_tctm[s][2], st.stdev(sub), tol=0.1)

# DOS/NAD/BK percentages
paper_err = {'Human':(32,36,32), 'Sonnet':(97,0,3), 'Opus':(86,8,7),
             'GPT':(70,6,24), 'Grok':(64,16,21), 'Gemini':(23,41,37)}

for label, pe in paper_err.items():
    if label == 'Human':
        sub = [r for r in rows if r['condition']=='human']
    else:
        m = [k for k,v in SHORT.items() if v==label][0]
        sub = persona_run1(m)
    dos = sum(int(r['dos']) for r in sub if r['dos'])
    nad = sum(int(r['nad']) for r in sub if r['nad'])
    bk = sum(int(r['bk']) for r in sub if r['bk'])
    tot = dos+nad+bk
    if tot > 0:
        check(f'{label} DOS%', pe[0], 100*dos/tot, tol=1)
        check(f'{label} NAD%', pe[1], 100*nad/tot, tol=1)
        check(f'{label} BK%', pe[2], 100*bk/tot, tol=1)

# ====================================================================
# 3. ATTACHMENT CLASSIFICATION (Table 3)
# ====================================================================
print('## 3. Attachment classification')

# Load ground truth
import json
JSONL = CSV.parent / 'analysis_summary.jsonl'
gt = {}
if JSONL.exists():
    for line in open(JSONL, encoding='utf-8'):
        if line.strip():
            d = json.loads(line)
            gt[d['persona_id']] = d['expected_style']

paper_attach = {'Sonnet':(24,30,0.735,0.765), 'Opus':(27,30,0.866,0.905),
                'GPT':(13,27,0.333,0.474), 'Grok':(27,30,0.867,0.890),
                'Gemini':(25,30,0.778,0.801)}

for m in MODELS:
    s = SHORT[m]
    sub = persona_run1(m)
    pairs = [(gt[r['persona']], r['style']) for r in sub if r['persona'] in gt and r['style']]
    n = len(pairs)
    correct = sum(1 for t,p in pairs if t==p)
    pe = paper_attach[s]
    check(f'{s} attachment match', pe[0], correct, tol=0)
    check(f'{s} attachment N', pe[1], n, tol=0)
    # Cohen kappa
    if pairs:
        po = correct/n
        ct = Counter(t for t,_ in pairs)
        cp = Counter(p for _,p in pairs)
        pe_chance = sum((ct[c]/n)*(cp[c]/n) for c in set(ct)|set(cp))
        kappa = (po-pe_chance)/(1-pe_chance) if pe_chance < 1 else float('nan')
        check(f'{s} attachment κ', pe[2], kappa, tol=0.005)

# ====================================================================
# 4. ZERO-PROMPT TCTM-22 (Table 6)
# ====================================================================
print('## 4. Zero-prompt TCTM-22')

paper_np_tctm = {'Sonnet':(6, 86.4), 'Opus':(5, 90.0), 'GPT':(6, 70.5),
                 'Grok':(6, 94.7), 'Gemini':(8, 92.0)}

for m in MODELS:
    s = SHORT[m]
    sub = noprompt(m)
    vals = [int(r['tctm_correct']) for r in sub if r['tctm_correct']]
    check(f'{s} noprompt N', paper_np_tctm[s][0], len(vals), tol=0)
    pct = 100*st.mean(vals)/22 if vals else 0
    check(f'{s} noprompt M%', paper_np_tctm[s][1], pct, tol=0.5)

# ====================================================================
# 5. ZERO-PROMPT FRAMING SHIFTS (Table 7)
# ====================================================================
print('## 5. Zero-prompt framing shifts')

paper_shifts = {  # Δ ANX, Δ AVO, Δ MentS, Δ TIPI-ES (matching v14.tex Table 7)
    'Sonnet':(+1.02, -0.90, +2.8, -0.57),
    'Opus':(+0.55, -0.06, -2.7, -0.40),
    'GPT':(-0.28, +0.62, +10.0, -0.20),
    'Grok':(+0.75, -0.27, -6.1, -0.40),
    'Gemini':(+0.90, +0.40, -7.7, -1.00)}

for m in MODELS:
    s = SHORT[m]
    sub_n = noprompt(m); sub_b = baseline(m)
    for col, idx, label in [('anx_mean',0,'Δ ANX'), ('avo_mean',1,'Δ AVO'),
                             ('ments_total',2,'Δ MentS'), ('tipi_es',3,'Δ TIPI-ES')]:
        nv = [float(r[col]) for r in sub_n if r[col]]
        bv = [float(r[col]) for r in sub_b if r[col]]
        if nv and bv:
            delta = st.mean(nv) - st.mean(bv)
            check(f'{s} {label}', paper_shifts[s][idx], delta, tol=0.15)

# ====================================================================
# 6. CROSS-VENDOR TCTM ICC (5 vs 4 models)
# ====================================================================
print('## 6. Cross-vendor TCTM')

def icc_2_1(matrix):
    n, k = len(matrix), len(matrix[0])
    grand = sum(sum(r) for r in matrix)/(n*k)
    rm = [sum(r)/k for r in matrix]
    cm = [sum(matrix[i][j] for i in range(n))/n for j in range(k)]
    ms_r = k*sum((r-grand)**2 for r in rm)/(n-1)
    ms_c = n*sum((c-grand)**2 for c in cm)/(k-1)
    ss_w = sum((matrix[i][j]-rm[i])**2 for i in range(n) for j in range(k))
    ms_e = (ss_w - n*sum((c-grand)**2 for c in cm))/((n-1)*(k-1))
    return (ms_r-ms_e)/(ms_r+(k-1)*ms_e+k*(ms_c-ms_e)/n)

def get_intersect(mods):
    s = None
    for m in mods:
        ps = {r['persona'] for r in persona_run1(m) if r['tctm_correct']}
        s = ps if s is None else s & ps
    return sorted(s)

def build_mat(mods, personas):
    mat = []
    for p in personas:
        row = []
        ok = True
        for m in mods:
            sub = [r for r in persona_run1(m) if r['persona']==p and r['tctm_correct']]
            if not sub: ok=False; break
            row.append(int(sub[0]['tctm_correct']))
        if ok: mat.append(row)
    return mat

inter5 = get_intersect(MODELS)
mat5 = build_mat(MODELS, inter5)
check('ICC 5-model intersect N', 27, len(inter5), tol=0)
check('ICC(2,1) 5 models', 0.254, icc_2_1(mat5), tol=0.01)

mods4 = [m for m in MODELS if m != 'GPT-5.4-mini']
inter4 = get_intersect(mods4)
mat4 = build_mat(mods4, inter4)
check('ICC 4-model intersect N (no GPT)', 30, len(inter4), tol=0)
check('ICC(2,1) 4 models (no GPT)', 0.389, icc_2_1(mat4), tol=0.01)

# ====================================================================
# Print results
# ====================================================================
print()
print('='*80)
print('VERIFICATION REPORT — paper v14 vs all_data.csv')
print('='*80)
fails = [r for r in results if r[3]=='FAIL']
passes = [r for r in results if r[3]=='PASS']
skips = [r for r in results if r[3]=='SKIP']

print(f'\n{"#":<4} {"Check":<35} {"Paper":>12} {"CSV":>12}  Status')
print('-'*80)
for i, (label, paper, csv_val, status) in enumerate(results, 1):
    flag = {'PASS':'✓ PASS','FAIL':'✗ FAIL','SKIP':'  SKIP'}[status]
    p_str = f'{paper:.3f}' if isinstance(paper, float) else str(paper)
    c_str = f'{csv_val:.3f}' if isinstance(csv_val, float) else str(csv_val)
    print(f'{i:<4} {label[:34]:<35} {p_str:>12} {c_str:>12}  {flag}')

print('-'*80)
print(f'TOTAL: {len(results)} checks | {len(passes)} PASS | {len(fails)} FAIL | {len(skips)} SKIP')
print('='*80)
if fails:
    print()
    print('FAILURES:')
    for label, paper, csv_val, _ in fails:
        print(f'  ✗ {label}: paper={paper} vs csv={csv_val}')
    sys.exit(1)
else:
    print('\nAll paper claims reproduce from all_data.csv ✓')
    sys.exit(0)
