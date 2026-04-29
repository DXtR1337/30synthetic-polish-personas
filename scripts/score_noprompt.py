"""score_noprompt.py — universal scorer for chaotic zero-prompt outputs.

Models without system instructions produce wildly inconsistent JSON formats.
This script handles all observed variants:
- dict-of-letters: {"w01": "D", "s07": "B", ...}
- list-of-dicts: [{"id": "w01", "answer": "D"}, ...]
- nested under: tctm, winiety, vignettes, part1_*, czesc*, część*, TCTM*

Filters to standard 22 TCTM-22 items so all runs are comparable.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from run_synthetic import load_tctm_vignettes

OUT_DIR = SCRIPT_DIR / 'out'

# Possible TCTM container keys (case-insensitive lookup)
TCTM_KEYS_PATTERNS = [
    'tctm', 'tctm22', 'tctm_22', 'tctm-22', 'tctm57', 'tctm_57',
    'winiety', 'vignettes',
    'part1_winiety', 'part1_vignettes', 'part1', 'part_1',
    'czesc1', 'czesc_1', 'czesc1_winiety', 'czesc_1_winiety',
    'część1', 'część_1', 'część_1_winiety',
]

LETTER_TO_INT = {'A': 0, 'B': 1, 'C': 2, 'D': 3}


def find_tctm_container(d, depth=0):
    """Walk dict to find a container with TCTM answers. Returns (container, key_path)."""
    if depth > 4 or not isinstance(d, dict):
        return None, None
    keys_lower = {k.lower(): k for k in d.keys()}
    for pattern in TCTM_KEYS_PATTERNS:
        if pattern in keys_lower:
            return d[keys_lower[pattern]], keys_lower[pattern]
    # Try nested dicts
    for k, v in d.items():
        if isinstance(v, dict):
            result, path = find_tctm_container(v, depth + 1)
            if result is not None:
                return result, f'{k}.{path}'
    return None, None


def extract_answers(container):
    """Convert any TCTM container to {item_id: letter}.
    Handles all observed Sonnet/Opus/GPT/Grok/Gemini formats including Polish keys odpowiedz/odpowiedź."""
    answers = {}
    if isinstance(container, dict):
        for k, v in container.items():
            if isinstance(v, str) and len(v) == 1 and v.upper() in 'ABCD':
                answers[k] = v.upper()
            elif isinstance(v, dict):
                # Try multiple keys: answer, odpowiedz, odpowiedź, chosenAnswer
                ans = (v.get('answer') or v.get('odpowiedz') or v.get('odpowiedź')
                       or v.get('chosenAnswer'))
                if isinstance(ans, str) and ans.strip().upper() in 'ABCD':
                    answers[k] = ans.strip().upper()
    elif isinstance(container, list):
        for item in container:
            if isinstance(item, dict):
                iid = item.get('id') or item.get('itemId')
                ans = (item.get('answer') or item.get('odpowiedz') or item.get('odpowiedź')
                       or item.get('chosenAnswer'))
                if iid and isinstance(ans, str) and ans.strip().upper() in 'ABCD':
                    answers[iid] = ans.strip().upper()
    return answers


def score_raw_file(raw_path, vignettes_dict):
    """Read raw.txt, extract answers, score against TCTM-22 ground truth."""
    raw = Path(raw_path).read_text(encoding='utf-8')
    # Strip markdown code fences
    raw = re.sub(r'```(?:json)?\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)
    # Find first JSON object
    m = re.search(r'\{[\s\S]*\}', raw)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None

    # First, try to find a TCTM container
    container, key_path = find_tctm_container(d)
    answers = extract_answers(container) if container is not None else {}

    # Fallback: scan top-level for item IDs directly
    if not answers:
        item_ids = set(vignettes_dict.keys())
        for k, v in d.items():
            if k in item_ids and isinstance(v, str) and v.strip().upper() in 'ABCD':
                answers[k] = v.strip().upper()

    # Score
    masc = {'correct': 0, 'DOS': 0, 'NAD': 0, 'BK': 0, 'unknown': 0}
    raw_scores = {'subtext': 0, 'court': 0, 'eks': 0, 'pursuit': 0, 'repair': 0}
    n_items = 0  # only count items that exist in TCTM-22
    for iid, letter in answers.items():
        if iid not in vignettes_dict:
            continue  # filter to 22 standard items
        n_items += 1
        vig = vignettes_dict[iid]
        ci = LETTER_TO_INT.get(letter, -1)
        ok = ci == vig['correctAnswer']
        if ok:
            masc['correct'] += 1
            sub = vig.get('subscale', '')
            if sub in raw_scores:
                raw_scores[sub] += 1
        else:
            mt = vig.get('mascTypes', [])
            cm = mt[ci] if 0 <= ci < len(mt) else 'unknown'
            if cm in masc:
                masc[cm] += 1
            else:
                masc['unknown'] += 1

    # Paper convention: missing TCTM items scored as wrong; denominator is fixed at 22
    return {
        'file': Path(raw_path).name,
        'key_path': key_path,
        'n_answered_in_22': n_items,
        'masc': masc,
        'raw_scores': raw_scores,
        'n_items_total': len(answers),
        'pct_of_22': 100.0 * masc['correct'] / 22.0,
    }


def main():
    vignettes = load_tctm_vignettes()
    print(f'TCTM-22 ground truth loaded: {len(vignettes)} vignettes')
    print(f'Item IDs: {sorted(vignettes.keys())}')
    print()

    raw_files = sorted(OUT_DIR.glob('noprompt-*-raw.txt'))
    print(f'Found {len(raw_files)} raw files\n')

    by_model = {}
    for path in raw_files:
        name = path.stem
        # Parse model from filename: noprompt-{model}-{timestamp}-raw
        parts = name.split('-')
        model = parts[1] if len(parts) >= 2 else 'unknown'
        result = score_raw_file(path, vignettes)
        if result is None:
            print(f'  SKIP {path.name}: no JSON')
            continue
        by_model.setdefault(model, []).append(result)
        c = result['masc']['correct']
        n22 = result['n_answered_in_22']
        pct22 = result['pct_of_22']  # paper convention: /22 fixed denominator
        print(f'  {model:8s} {result["file"][:50]:50s}: TCTM-22 score = {c}/22 = {pct22:.1f}%  (answered {n22}/22; key={result["key_path"]})')

    print('\n' + '=' * 70)
    print('AGGREGATED PER-MODEL ZERO-PROMPT TCTM-22 SCORES')
    print('=' * 70)
    import statistics as st
    summary_lines = []
    for model in ['sonnet', 'opus', 'gpt', 'grok', 'gemini']:
        runs = by_model.get(model, [])
        if not runs:
            continue
        # Paper convention: missing TCTM items = wrong; denominator fixed at 22
        scores_pct = [r['pct_of_22'] for r in runs]
        scores_raw = [r['masc']['correct'] for r in runs]
        n22s = [r['n_answered_in_22'] for r in runs]
        if not scores_pct:
            continue
        m_pct = st.mean(scores_pct)
        sd_pct = st.stdev(scores_pct) if len(scores_pct) > 1 else 0
        m_raw = st.mean(scores_raw)
        sd_raw = st.stdev(scores_raw) if len(scores_raw) > 1 else 0
        summary_lines.append(f'  {model:8s} N={len(scores_pct)}  M={m_pct:.1f}%  SD={sd_pct:.1f}%  raw_M={m_raw:.1f}/22  SD={sd_raw:.2f}  range=[{min(scores_pct):.1f}%, {max(scores_pct):.1f}%]')
        print(summary_lines[-1])

    # Save summary
    out = {
        'tctm_22_items': sorted(vignettes.keys()),
        'by_model': {m: [{'file': r['file'], 'correct': r['masc']['correct'],
                          'n_answered_in_22': r['n_answered_in_22'],
                          'masc': r['masc']} for r in by_model.get(m, [])]
                     for m in ['sonnet', 'opus', 'gpt', 'grok', 'gemini']},
    }
    (OUT_DIR.parent / 'noprompt_scoring_v6.json').write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\nSaved: noprompt_scoring_v6.json')


if __name__ == '__main__':
    main()
