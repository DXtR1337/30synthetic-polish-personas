# -*- coding: utf-8 -*-
"""
Re-scorer for noprompt-gpt55-*.json files.

GPT-5.5 zero-prompt outputs use Polish top-level keys (czesc_1_tctm22,
czesc_2_dbz_r, czesc_3_ments_pl, czesc_4_kpp, czesc_5_tipi_pl,
czesc_6_feedback) that run_noprompt.py's parser didn't recognize, so all
six noprompt jsons came in with mascProfile = {0,0,0,0,0}.

This script reads each raw.txt, normalizes the polish-keyed JSON into
the canonical payload schema, re-scores TCTM, and overwrites the .json
file in-place.
"""
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from run_synthetic import load_tctm_vignettes

OUT_DIR = SCRIPT_DIR / 'out'

# Polish key mapping → canonical payload keys
KEY_MAP = {
    'czesc_1_tctm22': 'tctm',
    'czesc_2_dbz_r': 'ecrR',
    'czesc_3_ments_pl': 'ments',
    'czesc_4_kpp': 'kpp',
    'czesc_5_tipi_pl': 'tipiPl',
    'czesc_6_feedback': 'feedback',
}

LETTER_TO_IDX = {'A': 0, 'B': 1, 'C': 2, 'D': 3}


def _unnest(v):
    """If v is {scale: ..., responses: {...}}, return responses; else v."""
    if isinstance(v, dict) and 'responses' in v and isinstance(v['responses'], dict):
        return v['responses']
    return v


def _list_to_dict(v):
    """If v is list-of-{id, answer|odpowiedz}, convert to {id: answer}; else v."""
    if isinstance(v, list):
        out = {}
        for it in v:
            if isinstance(it, dict):
                iid = it.get('id') or it.get('itemId')
                ans = (it.get('answer') or it.get('chosenAnswer')
                       or it.get('odpowiedz') or it.get('odpowiedź'))
                if iid and isinstance(ans, str):
                    out[iid] = ans
        return out
    return v


def rescore_one(raw_path):
    raw_text = Path(raw_path).read_text(encoding='utf-8')
    raw_clean = re.sub(r'```(?:json)?\s*', '', raw_text)
    raw_clean = re.sub(r'```\s*', '', raw_clean)
    m = re.search(r'\{[\s\S]*\}', raw_clean)
    if not m:
        return None
    data = json.loads(m.group(0))

    # Handle 3 observed GPT-5.5 noprompt formats:
    #   (a) Canonical:  czesc_1_tctm22, czesc_2_dbz_r, ...
    #   (b) Short:      tctm22, dbz_r, ments_pl, kpp, tipi_pl
    #   (c) List+nest:  tctm22 = [...], dbz_r = {scale, responses}
    tctm_data = (data.get('czesc_1_tctm22') or data.get('czesc_1_winiety')
                 or data.get('tctm22') or data.get('tctm') or data.get('winiety') or {})
    dbzr_data = data.get('czesc_2_dbz_r') or data.get('dbz_r') or data.get('ecrr') or {}
    ments_data = data.get('czesc_3_ments_pl') or data.get('ments_pl') or data.get('ments') or {}
    kpp_data = data.get('czesc_4_kpp') or data.get('kpp') or {}
    tipi_data = data.get('czesc_5_tipi_pl') or data.get('tipi_pl') or data.get('tipi') or {}
    feedback = data.get('czesc_6_feedback') or data.get('feedback') or {}

    tctm_data = _list_to_dict(tctm_data)
    dbzr_data = _unnest(dbzr_data)
    ments_data = _unnest(ments_data)
    kpp_data = _unnest(kpp_data)
    tipi_data = _unnest(tipi_data)

    # Score TCTM
    vignettes_dict = load_tctm_vignettes()
    vignettes = list(vignettes_dict.values())
    tctm_answers = []
    masc = {'correct': 0, 'DOS': 0, 'NAD': 0, 'BK': 0, 'unknown': 0}
    raw_scores = {'subtext': 0, 'court': 0, 'eks': 0, 'pursuit': 0, 'repair': 0}

    for iid, letter in tctm_data.items():
        if not isinstance(letter, str):
            continue
        ci = LETTER_TO_IDX.get(letter.strip().upper(), -1)
        vig = next((v for v in vignettes if v['id'] == iid), None)
        if not vig:
            continue
        ok = (ci == vig['correctAnswer'])
        mt = vig.get('mascTypes', [])
        cm = mt[ci] if 0 <= ci < len(mt) else 'unknown'
        if ok:
            masc['correct'] += 1
            sub = vig.get('subscale', '')
            if sub in raw_scores:
                raw_scores[sub] += 1
        elif cm in masc:
            masc[cm] += 1
        else:
            masc['unknown'] += 1
        tctm_answers.append({
            'itemId': iid,
            'chosenOptionIndex': ci,
            'chosenMascType': cm if not ok else 'correct',
            'isCorrect': ok,
            'responseTimeMs': 0,
            'changedAnswer': False,
            'presentationOrder': len(tctm_answers) + 1,
        })

    # Parse likerts (keys "1"..."N" → standardized prefix-N format)
    def parse_likert(data_d, prefix):
        return {f'{prefix}-{int(k):02d}': int(v) for k, v in data_d.items() if str(k).isdigit()}

    ecrr_answers = parse_likert(dbzr_data, 'ecrr')
    ments_answers = parse_likert(ments_data, 'ments')
    kpp_answers = parse_likert(kpp_data, 'kpp')
    tipi_answers = parse_likert(tipi_data, 'tipi')

    return {
        'masc': masc,
        'raw_scores': raw_scores,
        'tctm_answers': tctm_answers,
        'ecrr_answers': ecrr_answers,
        'ments_answers': ments_answers,
        'kpp_answers': kpp_answers,
        'tipi_answers': tipi_answers,
        'feedback': feedback,
    }


def main():
    raw_files = sorted(OUT_DIR.glob('noprompt-gpt55-*-raw.txt'))
    print(f'Found {len(raw_files)} noprompt-gpt55 raw files')

    for raw_path in raw_files:
        ts_match = re.search(r'(\d{8}T\d{6})', raw_path.name)
        if not ts_match:
            continue
        ts = ts_match.group(1)
        json_path = OUT_DIR / f'noprompt-gpt55-{ts}.json'

        try:
            result = rescore_one(raw_path)
        except Exception as e:
            print(f'  SKIP {raw_path.name}: {e}')
            continue

        if result is None:
            print(f'  SKIP {raw_path.name}: no JSON in raw')
            continue

        # Load existing json (preserve elapsed_seconds, tokens etc.)
        if json_path.exists():
            existing = json.load(open(json_path, encoding='utf-8'))
        else:
            existing = {
                'persona_id': 'noprompt',
                'persona_version': 0,
                'biography_length': 0,
                'model_name': 'gpt-5.5',
                'tokens_input': 0,
                'tokens_output': 0,
                'elapsed_seconds': 0,
                'respondent_id': f'noprompt-gpt55-{ts}',
            }

        # Replace payload
        NOW = datetime.now(timezone.utc).isoformat()
        existing['payload'] = {
            'respondentId': existing.get('respondent_id', f'noprompt-gpt55-{ts}'),
            'startedAt': NOW,
            'completedAt': NOW,
            'consented': True,
            'consentTimestamp': NOW,
            'totalDurationMs': 0,
            'synthetic': True,
            'demographics': {'age': 0, 'gender': 'ai', 'education': 'ai', 'psychologyBackground': 'no'},
            'tctm': {
                'answers': result['tctm_answers'],
                'mascProfile': result['masc'],
                'rawScores': result['raw_scores'],
                'durationMs': 0,
            },
            'ecrR': {'answers': result['ecrr_answers'], 'durationMs': 0},
            'ments': {'answers': result['ments_answers'], 'durationMs': 0},
            'kpp': {'answers': result['kpp_answers'], 'durationMs': 0},
            'tipiPl': {'answers': result['tipi_answers'], 'durationMs': 0},
            'feedback': result['feedback'],
        }

        json_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')

        ans_count = sum(1 for v in [result['ecrr_answers'], result['ments_answers'], result['kpp_answers'], result['tipi_answers']] if v)
        print(f'  {raw_path.name}: TCTM {result["masc"]["correct"]}/22 (DOS {result["masc"]["DOS"]}, NAD {result["masc"]["NAD"]}, BK {result["masc"]["BK"]}); likerts: {ans_count}/4 OK')


if __name__ == '__main__':
    main()
