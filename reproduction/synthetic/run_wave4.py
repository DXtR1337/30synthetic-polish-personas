# -*- coding: utf-8 -*-
"""
Wave 4 runner: panel nie-Azure (Bedrock Sonnet 4.6, Bedrock Opus 4.6, Gemini 3 Flash)
× (30×2 persona + 10 baseline + 6 zero-prompt) na POPRAWIONYM renderowaniu bodźców.

Protokół = lustrzane odbicie run_wave3.py (re-kolekcja Azure 31.05):
  - identyczny builder promptów (run_synthetic.build_user_prompt, fix serializera v3
    + poprawiony stem w22) — render zweryfikowany bajt w bajt z artefaktem
    adrian-gpt54f-20260531T124106-user.txt,
  - identyczne warunki: persona (system=bio), baseline (SYSTEM_BASELINE), zero-prompt,
  - sampling jak w kolekcji kwietniowej: Bedrock wysyła tylko max_tokens=16000
    (vendor-default temperature/top_p), Gemini tylko maxOutputTokens=16000.

Outputs trafiają do out/ z timestampem 20260610T22+ (UTC), NIE nadpisują wave 1-3,
NIE są appendowane do all_data.csv (integracja CSV = osobna, świadoma decyzja).

Pass 1 person biegnie BEZ adriana: jego run 1 to runy kontrolne
adrian-{sonnet,gemini3f,opus}-20260610T2245xx (checkpoint przed startem partii).

Użycie:
  python run_wave4.py --smoke               # 1 persona × 3 modele
  python run_wave4.py --full                # 29+30 persona + 10 baseline + 6 noprompt × 3 modele = 225 calls
  python run_wave4.py --baselines [N]      # N baseline × 3 modele
  python run_wave4.py --noprompts [N]      # N zero-prompt × 3 modele
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

# run_synthetic.load_env() przy imporcie wczytuje cały .env.local
# (BEDROCK_API_KEY + GEMINI_API_KEY), więc import run_gemini PO nim nie wybuchnie.
import run_synthetic as rs                                   # noqa: E402
import run_gemini as rg                                      # noqa: E402
from run_baseline import (                                   # noqa: E402
    run_baseline as baseline_once,
    call_bedrock,
    call_gemini,
)
from run_noprompt import (                                   # noqa: E402
    run_noprompt as noprompt_once,
    call_bedrock_noprompt,
    call_gemini_noprompt,
)

# ── log: tee na konsolę + plik (przeżywa ubicie konsoli) ──
LOG_PATH = OUT_DIR / f'wave4-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")}.log'

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
# Run 1 adriana = checkpoint 20260610T2245xx (przed startem partii).
PERSONAS_PASS1 = [p for p in PERSONAS if p != 'adrian']

BEDROCK_SONNET = 'eu.anthropic.claude-sonnet-4-6'
BEDROCK_OPUS = 'eu.anthropic.claude-opus-4-6-v1'

# ── persona-runnery (aliasy plików identyczne z kolekcją kwietniową) ──

def persona_sonnet(pid):
    rs.NOW = datetime.now(timezone.utc)
    rs.NOW_ISO = rs.NOW.isoformat()
    return rs.run_persona(pid, model_alias='sonnet')

def persona_opus(pid):
    rs.NOW = datetime.now(timezone.utc)
    rs.NOW_ISO = rs.NOW.isoformat()
    return rs.run_persona(pid, model_alias='opus')

def persona_gemini(pid):
    return rg.run_persona(pid)

# kolejność: tanie modele najpierw, Opus na końcu
PERSONA_FNS = {
    'sonnet': persona_sonnet,
    'gemini3f': persona_gemini,
    'opus': persona_opus,
}

# baseline/noprompt: aliasy 'sonnet'/'opus'/'gemini' jak w kwietniu
BASELINE_FNS = {
    'sonnet': lambda s, u: call_bedrock(s, u, BEDROCK_SONNET),
    'gemini': lambda s, u: call_gemini(s, u),
    'opus': lambda s, u: call_bedrock(s, u, BEDROCK_OPUS),
}
NOPROMPT_FNS = {
    'sonnet': lambda u: call_bedrock_noprompt(u, BEDROCK_SONNET),
    'gemini': lambda u: call_gemini_noprompt(u),
    'opus': lambda u: call_bedrock_noprompt(u, BEDROCK_OPUS),
}

SLEEP_S = 2
MAX_CONSECUTIVE_FAILS = 3   # bezpiecznik kosztowy: 3 z rzędu = stop modelu

dead_models = set()
consec_fails = {}
failures = []   # (kind, model, label)


def _attempt(kind, model, label, fn):
    """Jedno wywołanie z księgowaniem błędów i bezpiecznikiem."""
    if model in dead_models:
        print(f'SKIP [{model}] {kind} {label} — model wyłączony bezpiecznikiem')
        return False
    try:
        fn()
        consec_fails[model] = 0
        return True
    except Exception as e:
        consec_fails[model] = consec_fails.get(model, 0) + 1
        failures.append((kind, model, label))
        print(f'ERROR [{model}] {kind} {label}: {e}')
        traceback.print_exc()
        if consec_fails[model] >= MAX_CONSECUTIVE_FAILS:
            dead_models.add(model)
            print(f'!!! BEZPIECZNIK: {model} ma {consec_fails[model]} błędy z rzędu — '
                  f'pomijam resztę wywołań tego modelu')
        return False
    finally:
        time.sleep(SLEEP_S)


def smoke(persona='agata'):
    print(f'\n========== SMOKE: {persona} × 3 modele ==========')
    for ma, fn in PERSONA_FNS.items():
        print(f'\n--- {ma} {persona} ---')
        _attempt('persona-smoke', ma, persona, lambda: fn(persona))


def all_personas():
    total = len(PERSONAS_PASS1) + len(PERSONAS)
    print(f'\n========== PERSONAS: pass1 {len(PERSONAS_PASS1)} + pass2 {len(PERSONAS)} '
          f'× 3 modele = {total * 3} calls ==========')
    for run_idx, plist in ((1, PERSONAS_PASS1), (2, PERSONAS)):
        for ma, fn in PERSONA_FNS.items():
            for i, p in enumerate(plist, 1):
                print(f'\n--- [{i}/{len(plist)}] {ma} {p} (pass {run_idx}) ---')
                _attempt(f'persona-pass{run_idx}', ma, p, lambda fn=fn, p=p: fn(p))


def baselines(n=10):
    print(f'\n========== BASELINES: N={n} × 3 modele ==========')
    for ma, fn in BASELINE_FNS.items():
        for i in range(n):
            print(f'\n--- baseline {ma} #{i + 1}/{n} ---')
            _attempt('baseline', ma, f'#{i + 1}', lambda ma=ma, fn=fn: baseline_once(ma, fn))


def noprompts(n=6):
    print(f'\n========== NOPROMPTS: N={n} × 3 modele ==========')
    for ma, fn in NOPROMPT_FNS.items():
        for i in range(n):
            print(f'\n--- noprompt {ma} #{i + 1}/{n} ---')
            _attempt('noprompt', ma, f'#{i + 1}', lambda ma=ma, fn=fn: noprompt_once(ma, fn))


def retry_failures():
    """Jedna tura ponowień dla wszystkiego, co poległo (bez modeli ubitych bezpiecznikiem)."""
    if not failures:
        print('\n========== RETRY: brak błędów do ponowienia ==========')
        return
    todo = [f for f in failures if f[1] not in dead_models]
    print(f'\n========== RETRY: {len(todo)} ponowień ==========')
    failures.clear()
    for kind, model, label in todo:
        print(f'\n--- retry {kind} {model} {label} ---')
        if kind.startswith('persona'):
            fn = PERSONA_FNS[model]
            _attempt(kind + '-retry', model, label, lambda fn=fn, label=label: fn(label))
        elif kind == 'baseline':
            _attempt('baseline-retry', model, label,
                     lambda model=model: baseline_once(model, BASELINE_FNS[model]))
        elif kind == 'noprompt':
            _attempt('noprompt-retry', model, label,
                     lambda model=model: noprompt_once(model, NOPROMPT_FNS[model]))


def tally(since='20260610T22'):
    """Zliczenie nowych artefaktów wave 4 (JSON-y wynikowe, bez -raw/-system/-user)."""
    print(f'\n========== TALLY (stamp >= {since}) ==========')
    import re as _re
    counts = {}
    for f in OUT_DIR.glob('*.json'):
        m = _re.search(r'-(\d{8}T\d{6})\.json$', f.name)
        if not m or m.group(1) < since:
            continue
        base = f.name[: -(len(m.group(1)) + 6)]  # utnij '-<stamp>.json'
        if base.startswith(('baseline-', 'noprompt-')):
            key = base
        else:
            key = 'persona-' + base.rsplit('-', 1)[-1]
        counts[key] = counts.get(key, 0) + 1
    for k in sorted(counts):
        print(f'  {k}: {counts[k]}')
    print('Cel: persona-sonnet 59+1chk, persona-gemini3f 59+1chk, persona-opus 59+1chk '
          '(checkpointy adriana liczą się w tally), baseline-* po 10, noprompt-* po 6')
    if dead_models:
        print(f'MODELE UBITE BEZPIECZNIKIEM: {sorted(dead_models)}')
    if failures:
        print(f'NIEDOMKNIĘTE BŁĘDY PO RETRY: {failures}')


def full():
    t0 = time.time()
    all_personas()
    baselines(10)
    noprompts(6)
    retry_failures()
    tally()
    print(f'\nWAVE 4 ZAKOŃCZONA w {(time.time() - t0) / 60:.1f} min. Log: {LOG_PATH.name}')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if args[0] == '--smoke':
        smoke(args[1] if len(args) > 1 else 'agata')
    elif args[0] == '--full':
        full()
    elif args[0] == '--baselines':
        baselines(int(args[1]) if len(args) > 1 else 1)
    elif args[0] == '--noprompts':
        noprompts(int(args[1]) if len(args) > 1 else 1)
    elif args[0] == '--tally':
        tally(args[1] if len(args) > 1 else '20260610T22')
    else:
        print(__doc__)
        sys.exit(1)
