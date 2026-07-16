# -*- coding: utf-8 -*-
"""
Wave 5 runner: TCTM-57 na POPRAWIONYM renderowaniu — domknięcie kwadratu 2×2
(bodziec: obcięty/poprawiony × administracja: 22/57 itemów).

Kwietniowa komórka full57 (12.04, bodziec sprzed korekty): Sonnet 31 runów,
GPT-5.5 30 runów — itemy s07/w22 zachowywały się radykalnie inaczej niż
w administracji TCTM-22 (s07 Sonnet: 100% vs 1,7%). Ta fala daje brakującą
komórkę: te same dwa modele, pełna pula 57 winiet, bodziec poprawiony.

Design: 30 person × 1 run × {sonnet --full57, gpt55full57} = 60 wywołań.
Aliasy plików jak w kwietniu: '{persona}-sonnet-' (57 odpowiedzi, rozróżnialne
po liczbie itemów i stampie) oraz '{persona}-gpt55full57-'.

Użycie:
  python run_wave5_full57.py --smoke      # 1 persona × 2 modele
  python run_wave5_full57.py --full       # 30 person × 2 modele
"""
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / 'out'
OUT_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(SCRIPT_DIR))

import run_synthetic as rs                                  # noqa: E402
from run_gpt55_full57 import run_persona_full57 as gpt55_full57  # noqa: E402

# run_gpt55_full57 ustawia rs.LOAD_ALL_VIGNETTES = True przy imporcie;
# potwierdzamy jawnie, żeby ścieżka Sonneta też ładowała 57 winiet.
rs.LOAD_ALL_VIGNETTES = True

LOG_PATH = OUT_DIR / f'wave5-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")}.log'

class _Tee:
    def __init__(self, path):
        self.f = open(path, 'a', encoding='utf-8')
        self.console = sys.stdout
    def write(self, s):
        try:
            self.console.write(s)
        except Exception:
            pass
        self.f.write(s)
        self.f.flush()
    def flush(self):
        try:
            self.console.flush()
        except Exception:
            pass
        self.f.flush()

sys.stdout = _Tee(LOG_PATH)
sys.stderr = sys.stdout

PERSONAS = [
    'adrian', 'agata', 'ania', 'anna-sim', 'bartek', 'dominika',
    'ewa', 'filip', 'gabriela', 'hubert', 'jakub', 'jola',
    'kamil', 'kasia', 'klaudia', 'kuba', 'lukasz', 'magda',
    'marek', 'michal-k', 'michal-sim', 'natalia', 'ola', 'pawel',
    'piotr', 'radek', 'sara', 'tomek', 'weronika', 'zuzia',
]


def sonnet_full57(pid):
    vigs = rs.load_tctm_vignettes()
    assert len(vigs) == 57, f'Sonnet full57: oczekiwano 57 winiet, jest {len(vigs)}'
    rs.NOW = datetime.now(timezone.utc)
    rs.NOW_ISO = rs.NOW.isoformat()
    return rs.run_persona(pid, model_alias='sonnet')


FNS = {
    'sonnet57': sonnet_full57,
    'gpt55full57': gpt55_full57,
}

SLEEP_S = 2
MAX_CONSECUTIVE_FAILS = 3
dead_models = set()
consec_fails = {}
failures = []


def _attempt(model, label, fn):
    if model in dead_models:
        print(f'SKIP [{model}] {label} — model wyłączony bezpiecznikiem')
        return False
    try:
        fn()
        consec_fails[model] = 0
        return True
    except Exception as e:
        consec_fails[model] = consec_fails.get(model, 0) + 1
        failures.append((model, label))
        print(f'ERROR [{model}] {label}: {e}')
        traceback.print_exc()
        if consec_fails[model] >= MAX_CONSECUTIVE_FAILS:
            dead_models.add(model)
            print(f'!!! BEZPIECZNIK: {model} — {consec_fails[model]} błędy z rzędu, stop')
        return False
    finally:
        time.sleep(SLEEP_S)


def smoke(persona='adrian'):
    print(f'\n========== SMOKE WAVE5: {persona} × 2 modele (full57, poprawiony bodziec) ==========')
    for ma, fn in FNS.items():
        print(f'\n--- {ma} {persona} ---')
        _attempt(ma, persona, lambda fn=fn: fn(persona))


def full():
    t0 = time.time()
    print(f'\n========== WAVE 5 FULL57: 30 person × 2 modele = 60 wywołań ==========')
    for ma, fn in FNS.items():
        for i, p in enumerate(PERSONAS, 1):
            print(f'\n--- [{i}/30] {ma} {p} ---')
            _attempt(ma, p, lambda fn=fn, p=p: fn(p))
    # retry raz
    todo = [f for f in failures if f[0] not in dead_models]
    failures.clear()
    if todo:
        print(f'\n========== RETRY: {len(todo)} ==========')
        for ma, p in todo:
            print(f'\n--- retry {ma} {p} ---')
            _attempt(ma, p, lambda ma=ma, p=p: FNS[ma](p))
    print(f'\nNIEDOMKNIĘTE: {failures}')
    print(f'WAVE 5 ZAKOŃCZONA w {(time.time() - t0) / 60:.1f} min. Log: {LOG_PATH.name}')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if args[0] == '--smoke':
        smoke(args[1] if len(args) > 1 else 'adrian')
    elif args[0] == '--full':
        full()
    else:
        print(__doc__)
        sys.exit(1)
