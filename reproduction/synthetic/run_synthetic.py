"""
Synthetic respondent runner — Claude Opus 4.6 jako ,,Piotr'' (lub inna persona)
wypełnia pełną baterię magisterki (TCTM-22 + DBZ-R + MentS-PL + KPP + TIPI-PL).

Backend: AWS Bedrock (bearer token BEDROCK_API_KEY, domyślnie eu-central-1,
model eu.anthropic.claude-opus-4-6-v1). Identyczny wzorzec co
scripts/benchmark-kit/full-benchmark.py — bezpośredni POST przez urllib,
żadnego boto3 ani SDK.

Użycie:
    python docs/paper/magisterka/synthetic/run_synthetic.py piotr

Wymagane w .env.local:
    BEDROCK_API_KEY=ABSK...                      (bearer token Bedrock)
Opcjonalne:
    BEDROCK_REGION=eu-central-1                  (default)
    BEDROCK_MODEL_ID=eu.anthropic.claude-opus-4-6-v1  (default)

Plik persony:   docs/paper/magisterka/synthetic/<persona>.md
Wyniki:         docs/paper/magisterka/synthetic/out/<persona>-<timestamp>.json
(payload 1:1 z formatem MagisterkaPayload + metadane syntetyczne)
"""
import json
import os
import sys
import re
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# Załaduj .env.local
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent  # docs/paper/magisterka/synthetic/ → repo root

def load_env():
    env_path = REPO_ROOT / '.env.local'
    if not env_path.exists():
        # Public-package change: API credentials are only needed to run a
        # collection; prompt construction and the hygiene test work without.
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, val = line.split('=', 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

load_env()

# ══════════════════════════════════════════════════════════════════════
# KONFIGURACJA — AWS Bedrock bearer token (BEDROCK_API_KEY)
# ══════════════════════════════════════════════════════════════════════
# Używamy tego samego wzorca co scripts/benchmark-kit/full-benchmark.py:
# bezpośredni POST przez urllib.request, bez boto3/SDK.
# Region + model można nadpisać przez env vars.
BEDROCK_REGION = os.environ.get('BEDROCK_REGION', 'eu-central-1')

# Model aliases — można wybrać drugim argumentem CLI: python run.py piotr sonnet
MODEL_ALIASES = {
    'opus':    'eu.anthropic.claude-opus-4-6-v1',
    'sonnet':  'eu.anthropic.claude-sonnet-4-6',
    'haiku':   'eu.anthropic.claude-haiku-4-5-20251001-v1:0',
    'sonnet45': 'eu.anthropic.claude-sonnet-4-5-20250929-v1:0',
}
DEFAULT_MODEL_ALIAS = os.environ.get('SYNTHETIC_MODEL', 'opus')

MAX_TOKENS = 16000

# Stała data badania dla respondenta syntetycznego (nie ma realnego startedAt)
NOW = datetime.now(timezone.utc)
NOW_ISO = NOW.isoformat()

# ══════════════════════════════════════════════════════════════════════
# BATERIA — treści pytań i skal (ładowane raz, używane w prompcie)
# ══════════════════════════════════════════════════════════════════════

# TCTM-22 vignettes (22 pozycje w kolejności z tctm22-magisterka.ts)
# Każda winieta: id, text (pytanie), vignette chat, 4 opcje odpowiedzi.
# Struktura identyczna jak w runtime — zaciągamy z tctm54.ts przez parser TS.
# Dla prostoty: osadzamy statycznie tylko to, czego agent potrzebuje.

TCTM22_IDS = [
    'w01', 's07', 's08', 's10', 'w08', 'c07', 'c10', 'w11',
    'w13', 'w14', 'e08', 'w15', 'w19', 'pw07', 'w22', 'pw09',
    'pw11', 'w25', 'r08', 'w28', 'r09', 'r10',
]

# Global flag: set True to load all 57 vignettes instead of just TCTM-22
LOAD_ALL_VIGNETTES = False

# Leniwe ładowanie pełnych winiet z TypeScriptowego pliku — prosty parser regex.
def load_tctm_vignettes():
    """Czyta tctm54.ts i wyciąga dla każdej pozycji: text, messages, vignetteOptions."""
    ts_file = REPO_ROOT / 'src' / 'lib' / 'testy' / 'tests' / 'tctm54.ts'
    content = ts_file.read_text(encoding='utf-8')
    vignettes = {}

    # Każda pozycja zaczyna się od "id: '<id>'" i kończy przed następną lub "]"
    # Dla prostoty używamy prymitywnego splittera po "id: '".
    entries = re.split(r"\n\s*\{\s*\n\s*id: '", content)
    for entry in entries[1:]:  # pierwszy to preamble
        match_id = re.match(r"([a-z0-9]+)'", entry)
        if not match_id:
            continue
        vid = match_id.group(1)
        if not LOAD_ALL_VIGNETTES and vid not in TCTM22_IDS:
            continue

        # text: 'Co X naprawdę komunikuje...'
        # Quoted string with possible escaped apostrophes: text: '...\'u...'
        text_match = re.search(r"text: '((?:[^'\\]|\\.)*)'", entry)
        qtext = text_match.group(1).replace("\\'", "'").replace('\\"', '"') if text_match else ''

        # vignetteOptions: [ '...', '...', '...', '...' ]
        # UWAGA: opcje zawierają apostrofy escape'owane jako \' (np. "deadline'u"),
        # więc regex musi explicite pozwolić na backslash-apostrof PRZED
        # próbą zamknięcia apostrofem. Poprawny pattern: dopasuj ciąg znaków
        # który nie jest apostrofem LUB jest escape'owanym apostrofem.
        opts_block = re.search(r"vignetteOptions:\s*\[([\s\S]*?)\]", entry)
        options = []
        if opts_block:
            opts_raw = opts_block.group(1)
            # Pattern: ' (otwarcie) + zero lub więcej (znak-nie-apostrof LUB \\') + ' (zamknięcie)
            for m in re.finditer(r"'((?:[^'\\]|\\.)*)'", opts_raw):
                options.append(m.group(1).replace("\\'", "'").replace('\\"', '"'))

        # mascTypes
        masc_block = re.search(r"mascTypes:\s*\[([\s\S]*?)\]", entry)
        masc = []
        if masc_block:
            for m in re.finditer(r"'([A-Za-z]+)'", masc_block.group(1)):
                masc.append(m.group(1))

        # correctAnswer
        correct_match = re.search(r"correctAnswer:\s*(\d+)", entry)
        correct_idx = int(correct_match.group(1)) if correct_match else None

        # messages
        messages = []
        msgs_block = re.search(r"messages:\s*\[([\s\S]*?)\n\s*\],\s*\n\s*\},", entry)
        if msgs_block:
            msgs_raw = msgs_block.group(1)
            # ── REGEX HISTORY (zostawione celowo, żeby nie wpaść w to ponownie) ──
            # v1 zakładała tylko { sender, text } → pomijała winiety z timestampem.
            # v2 dodała opcjonalne isSystem + isMedia (w tej kolejności) → wciąż
            #    gubiła wiadomości z `timestamp`, `deletable`, kolejnością
            #    isSystem PO isMedia, itd. W tctm54.ts pola opcjonalne pojawiają
            #    się w DOWOLNEJ kolejności i kombinacji (timestamp, isMedia,
            #    isSystem, deletable, ...). Stary pattern dropował np. pw07
            #    (14→8), w19 (14→6), s07 (12→11).
            # v3 (current, safe): matchujemy wymagane `sender` + `text`, a po
            #    nich zero lub więcej comma-separated keyVal pairs gdzie value
            #    to string '...', true/false albo liczba. Wszystkie opcjonalne
            #    pola są IGNOROWANE — interesuje nas tylko (sender, text).
            #    isSystem detektujemy osobno w drugim kroku.
            msg_re = re.compile(
                r"\{\s*sender:\s*'([^']*)',\s*text:\s*'((?:[^'\\]|\\.)*)'"
                r"((?:\s*,\s*[a-zA-Z]+\s*:\s*(?:'(?:[^'\\]|\\.)*'|true|false|\d+))*)"
                r"\s*\}"
            )
            for line in msg_re.finditer(msgs_raw):
                sender = line.group(1)
                text = line.group(2)
                tail = line.group(3) or ''
                # Wyłap isSystem: true z opcjonalnych pól (niezależnie od kolejności).
                is_sys = bool(re.search(r"\bisSystem\s*:\s*true\b", tail))
                messages.append({
                    'sender': sender,
                    'text': text.replace("\\'", "'").replace('\\"', '"'),
                    'isSystem': is_sys,
                })

        # context (single line)
        ctx_match = re.search(r"context:\s*'((?:[^'\\]|\\.)*)'", entry)
        context = ctx_match.group(1).replace("\\'", "'").replace('\\"', '"') if ctx_match else ''

        # subscale + difficulty
        sub_match = re.search(r"subscale:\s*'([^']+)'", entry)
        diff_match = re.search(r"difficulty:\s*'([^']+)'", entry)

        vignettes[vid] = {
            'id': vid,
            'question': qtext,
            'context': context,
            'messages': messages,
            'options': options,
            'mascTypes': masc,
            'correctAnswer': correct_idx,
            'subscale': sub_match.group(1) if sub_match else '',
            'difficulty': diff_match.group(1) if diff_match else '',
        }

    return vignettes

# ---------------------------------------------------------------------------
# Third-party instrument items (DBZ-R/ECR-R, MentS-PL, KPP, TIPI-PL) are NOT
# distributed in this public package (see THIRD_PARTY_NOTICES.md). In the
# collection runs they were defined verbatim at this point in the file; the
# archived prompt SHA-256 hashes in run_manifest.csv were produced with those
# items in place. To re-run a collection, provide a local (non-distributed)
# module instruments_local.py defining ECRR_ITEMS (36 strings), MENTS_ITEMS
# (28), KPP_ITEMS (36), and TIPI_ITEMS (10) from legally obtained copies.
# ---------------------------------------------------------------------------
try:
    from instruments_local import ECRR_ITEMS, MENTS_ITEMS, KPP_ITEMS, TIPI_ITEMS
except ImportError:
    # Importing the module stays possible (system-prompt construction and the
    # hygiene test need no instrument items); building a battery fails closed.
    ECRR_ITEMS = MENTS_ITEMS = KPP_ITEMS = TIPI_ITEMS = None


def _require_instruments():
    if ECRR_ITEMS is None:
        raise SystemExit(
            "Instrument items are not distributed with this package "
            "(third-party copyright; see THIRD_PARTY_NOTICES.md). Provide "
            "instruments_local.py with ECRR_ITEMS, MENTS_ITEMS, KPP_ITEMS, "
            "TIPI_ITEMS to rebuild battery prompts."
        )

# ══════════════════════════════════════════════════════════════════════
# KONSTRUKCJA PROMPTU
# ══════════════════════════════════════════════════════════════════════

def build_tctm_block(vignettes):
    """Formatuje winiety w czytelnym bloku Markdown dla agenta."""
    # Determine ordered list of IDs: either TCTM22 or all loaded vignettes
    if LOAD_ALL_VIGNETTES:
        ordered_ids = sorted(vignettes.keys())
    else:
        ordered_ids = [vid for vid in TCTM22_IDS if vid in vignettes]
    lines = []
    for idx, vid in enumerate(ordered_ids, 1):
        v = vignettes[vid]
        lines.append(f"### Winieta {idx} [id: {vid}]")
        lines.append(f"**Pytanie:** {v['question']}")
        if v['context']:
            lines.append(f"*{v['context']}*")
        lines.append("")
        lines.append("**Rozmowa:**")
        for m in v['messages']:
            if m['isSystem']:
                lines.append(f"  _[{m['text']}]_")
            else:
                lines.append(f"  **{m['sender']}:** {m['text']}")
        lines.append("")
        lines.append("**Opcje:**")
        for i, opt in enumerate(v['options']):
            letter = chr(ord('A') + i)
            lines.append(f"  {letter}. {opt}")
        lines.append("")
    return "\n".join(lines)


def build_likert_block(title, items, scale_low, scale_mid, scale_high, scale_points):
    """Formatuje skalę Likerta w czytelnym bloku."""
    lines = [f"### {title}"]
    lines.append(f"Skala 1-{scale_points}: {scale_low} … {scale_mid} … {scale_high}")
    lines.append("")
    for i, text in enumerate(items, 1):
        lines.append(f"{i:2d}. {text}")
    lines.append("")
    return "\n".join(lines)


def build_system_prompt(biography_text):
    return f"""{biography_text}

═══════════════════════════════════════════════════════════════════
INSTRUKCJE — przeczytaj uważnie.
═══════════════════════════════════════════════════════════════════

Za chwilę dostaniesz pełną baterię pytań z pilotażu magisterskiego. Twoim zadaniem jest wypełnić ją BĘDĄC POSTACIĄ OPISANĄ WYŻEJ — nie udawaj, nie analizuj, nie wyjaśniaj czego byś oczekiwał od takiej postaci. TY JESTEŚ TĄ OSOBĄ.

Odpowiadasz tak, jak ta konkretna osoba faktycznie by odpowiedziała siedząc przed komputerem i wypełniając kwestionariusz — szybko, intuicyjnie, z głębi swojego doświadczenia życiowego. Nie wybierasz odpowiedzi ,,psychologicznie poprawnych" ani ,,takich jakie pasują do typu osobowości". Wybierasz to, co naprawdę czujesz.

KRYTYCZNE: Zwróć wynik WYŁĄCZNIE jako jeden blok JSON w formacie podanym poniżej. Żadnego tekstu przed ani po. Zero komentarzy, zero wyjaśnień. Tylko JSON.

Format odpowiedzi:
```json
{{
  "tctm": [
    {{"id": "w01", "answer": "A|B|C|D"}},
    ...
  ],
  "ecrr": {{"1": 1-7, "2": 1-7, ..., "36": 1-7}},
  "ments": {{"1": 1-5, "2": 1-5, ..., "28": 1-5}},
  "kpp": {{"1": 1-5, "2": 1-5, ..., "36": 1-5}},
  "tipi": {{"1": 1-7, "2": 1-7, ..., "10": 1-7}},
  "feedback": {{
    "hardestVignette": "krótka odpowiedź lub 'nie'",
    "unclearVignette": {{"answer": "tak|nie", "details": "opcjonalny komentarz"}},
    "disagreedAnswer": {{"answer": "tak|nie|nie_wiem", "details": "opcjonalny komentarz"}},
    "estimatedDurationMin": liczba,
    "technicalIssues": {{"answer": "nie", "details": ""}},
    "willingFutureParticipation": "tak|byc_moze|nie",
    "additionalComments": "krótki komentarz lub pusty string"
  }}
}}
```
"""


def build_user_prompt(vignettes):
    _require_instruments()
    n_vig = len(vignettes)
    label = f'TCTM-{n_vig}' if LOAD_ALL_VIGNETTES else 'TCTM-22'
    parts = []
    parts.append(f"# BATERIA PILOTAŻU {label}")
    parts.append("")
    parts.append("Odpowiedz na wszystkie poniższe pytania w formacie JSON opisanym w instrukcji.")
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append(f"## Część 1: Winiety {label}")
    parts.append("")
    parts.append("Przeczytaj każdą rozmowę i wybierz opcję (A/B/C/D), która Twoim zdaniem najlepiej oddaje, co osoba w rozmowie naprawdę chciała zakomunikować.")
    parts.append("")
    parts.append(build_tctm_block(vignettes))
    parts.append("---")
    parts.append("")
    parts.append("## Część 2: DBZ-R (Doświadczenia w Bliskich Związkach)")
    parts.append("")
    parts.append("Poniższe twierdzenia dotyczą tego, jak czujesz się w bliskich związkach. Myśl o swoich relacjach z wszystkimi bliskimi osobami w życiu. Odpowiadaj w skali 1 (zdecydowanie się nie zgadzam) do 7 (zdecydowanie się zgadzam).")
    parts.append("")
    parts.append(build_likert_block(
        'DBZ-R — 36 pozycji', ECRR_ITEMS,
        'zdecydowanie się nie zgadzam', 'nie mam zdania', 'zdecydowanie się zgadzam', 7
    ))
    parts.append("---")
    parts.append("")
    parts.append("## Część 3: MentS-PL (Skala Mentalizacji)")
    parts.append("")
    parts.append("Odpowiadaj w skali 1 (całkowicie nieprawdziwe) do 5 (całkowicie prawdziwe).")
    parts.append("")
    parts.append(build_likert_block(
        'MentS-PL — 28 pozycji', MENTS_ITEMS,
        'całkowicie nieprawdziwe', 'zarówno prawdziwe jak i nieprawdziwe', 'całkowicie prawdziwe', 5
    ))
    parts.append("---")
    parts.append("")
    parts.append("## Część 4: KPP (Kwestionariusz Potrzeby Poznania)")
    parts.append("")
    parts.append("Odpowiadaj w skali 1 (zdecydowanie się nie zgadzam) do 5 (zdecydowanie się zgadzam).")
    parts.append("")
    parts.append(build_likert_block(
        'KPP — 36 pozycji', KPP_ITEMS,
        'zdecydowanie się nie zgadzam', 'trudno powiedzieć', 'zdecydowanie się zgadzam', 5
    ))
    parts.append("---")
    parts.append("")
    parts.append("## Część 5: TIPI-PL (Krótki Inwentarz Osobowości)")
    parts.append("")
    parts.append("Odpowiadaj w skali 1 (zdecydowanie się nie zgadzam) do 7 (zdecydowanie się zgadzam).")
    parts.append("")
    parts.append(build_likert_block(
        'TIPI-PL — 10 pozycji', TIPI_ITEMS,
        'zdecydowanie się nie zgadzam', 'ani się zgadzam, ani nie zgadzam', 'zdecydowanie się zgadzam', 7
    ))
    parts.append("---")
    parts.append("")
    parts.append("## Część 6: Feedback")
    parts.append("")
    parts.append("Krótkie pytania otwarte o Twoje wrażenia z badania. Odpowiadaj szczerze, tak jak Ty (postać z biografii) byś odpowiedział po godzinie wypełniania takiego badania.")
    parts.append("")
    parts.append("1. Która winieta była najtrudniejsza?")
    parts.append("2. Czy któraś winieta była niejasna lub nierealistyczna? (tak/nie + szczegóły)")
    parts.append("3. Czy zauważyłeś winietę, gdzie wybrałeś inną odpowiedź niż to, co autor oznaczył jako poprawne? (tak/nie/nie_wiem)")
    parts.append("4. Ile minut szacujesz, że Ci to zajęło?")
    parts.append("5. Czy byłeś gotów wziąć udział w podobnym badaniu w przyszłości? (tak/byc_moze/nie)")
    parts.append("6. Dodatkowe uwagi?")
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("Teraz odpowiedz. Pamiętaj: TYLKO JSON, nic więcej. Zaczynaj.")
    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════════
# GŁÓWNY RUNNER
# ══════════════════════════════════════════════════════════════════════

def run_persona(persona_id, model_alias=DEFAULT_MODEL_ALIAS):
    # 1. Załaduj biografię
    bio_path = SCRIPT_DIR / f'{persona_id}.md'
    if not bio_path.exists():
        raise FileNotFoundError(f'Brak pliku biografii: {bio_path}')
    bio_raw = bio_path.read_text(encoding='utf-8')

    # Wyciągnij frontmatter + ciało
    if bio_raw.startswith('---\n'):
        parts = bio_raw.split('\n---\n', 1)
        frontmatter_raw = parts[0][4:]
        if len(parts) != 2:
            raise ValueError(
                f'{persona_id}: malformed persona front matter (missing closing ---); '
                'refusing to build a prompt that could leak researcher metadata'
            )
        bio_body = parts[1]
    else:
        frontmatter_raw = ''
        bio_body = bio_raw

    # Prymitywny parser frontmattera — wyciągamy tylko persona_version do respondentId.
    # Reszta frontmattera (expected_profile, author_note) to metadane researchera,
    # NIE idą do AI — Claude widzi tylko bio_body (tekst po pierwszym `---\n`).
    persona_version = 1
    for line in frontmatter_raw.splitlines():
        m = re.match(r'persona_version:\s*(\d+)', line.strip())
        if m:
            try:
                persona_version = int(m.group(1))
            except ValueError:
                pass

    bio_word_count = len(bio_body.split())
    print(f'[{persona_id}] biografia załadowana: {bio_word_count} słów')

    # 2. Załaduj winiety TCTM
    vignettes = load_tctm_vignettes()
    if not LOAD_ALL_VIGNETTES:
        missing = [vid for vid in TCTM22_IDS if vid not in vignettes]
        if missing:
            raise RuntimeError(f'Brak winiet w tctm54.ts: {missing}')
    label = f'TCTM-{len(vignettes)}' if LOAD_ALL_VIGNETTES else 'TCTM-22'
    print(f'[{persona_id}] załadowano {len(vignettes)} winiet {label}')

    # 3. Zbuduj prompt
    system_prompt = build_system_prompt(bio_body)
    user_prompt = build_user_prompt(vignettes)

    # Zapisz kopię promptów do debugowania
    out_dir = SCRIPT_DIR / 'out'
    out_dir.mkdir(exist_ok=True)
    stamp = NOW.strftime('%Y%m%dT%H%M%S')
    (out_dir / f'{persona_id}-{model_alias}-{stamp}-system.txt').write_text(system_prompt, encoding='utf-8')
    (out_dir / f'{persona_id}-{model_alias}-{stamp}-user.txt').write_text(user_prompt, encoding='utf-8')

    print(f'[{persona_id}] system prompt: {len(system_prompt)} znaków')
    print(f'[{persona_id}] user prompt:   {len(user_prompt)} znaków')
    print(f'[{persona_id}] system prompt startuje od: {system_prompt[:120]!r}')
    # Frontmatter (expected_profile, etc.) NIE idzie do AI — tylko bio_body + instrukcja.

    # 4. Wybierz model (opus/sonnet/haiku) i zbuduj endpoint URL
    if model_alias not in MODEL_ALIASES:
        raise ValueError(
            f'Nieznany alias modelu: {model_alias!r}. '
            f'Dostępne: {", ".join(MODEL_ALIASES.keys())}'
        )
    model_used = MODEL_ALIASES[model_alias]
    bedrock_url = f'https://bedrock-runtime.{BEDROCK_REGION}.amazonaws.com/model/{model_used}/invoke'

    bedrock_key = os.environ.get('BEDROCK_API_KEY')
    if not bedrock_key:
        raise RuntimeError(
            'Brak BEDROCK_API_KEY w .env.local.\n'
            'Dodaj: BEDROCK_API_KEY=ABSK...\n'
            f'Endpoint użyty: {bedrock_url}'
        )

    print(f'[{persona_id}] wywołuję [{model_alias}] {model_used} via {BEDROCK_REGION} (max_tokens={MAX_TOKENS})...')
    t_start = time.time()

    req_body = json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': MAX_TOKENS,
        'system': system_prompt,
        'messages': [
            {'role': 'user', 'content': user_prompt},
        ],
    }).encode('utf-8')

    req = urllib.request.Request(
        bedrock_url,
        data=req_body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {bedrock_key}',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            resp_body = resp.read()
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace') if hasattr(e, 'read') else ''
        raise RuntimeError(f'Bedrock HTTP {e.code}: {err_body[:500]}') from e

    response = json.loads(resp_body)
    elapsed = time.time() - t_start

    # Struktura odpowiedzi Bedrock = identyczna jak Anthropic API:
    #   {'content': [{'type': 'text', 'text': '...'}], 'usage': {'input_tokens', 'output_tokens'}, 'stop_reason': ...}
    stop_reason = response.get('stop_reason', 'unknown')
    usage = response.get('usage', {}) or {}
    input_tokens = usage.get('input_tokens', 0)
    output_tokens = usage.get('output_tokens', 0)

    print(f'[{persona_id}] odpowiedź w {elapsed:.1f}s · stop_reason={stop_reason} · tokens in={input_tokens} out={output_tokens}')

    content = response.get('content', [])
    raw_response = content[0].get('text', '') if content else ''
    if not raw_response:
        raise RuntimeError(f'Pusta odpowiedź z Bedrock: {json.dumps(response)[:500]}')

    (out_dir / f'{persona_id}-{model_alias}-{stamp}-raw.txt').write_text(raw_response, encoding='utf-8')

    # 5. Wyciągnij JSON
    json_match = re.search(r'\{[\s\S]*\}', raw_response)
    if not json_match:
        raise RuntimeError(f'Brak JSONa w odpowiedzi: {raw_response[:200]}')
    try:
        agent_answers = json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        # Zapisz surówkę, spróbuj naprawić cudzysłowy
        print(f'[{persona_id}] JSONDecodeError: {e}')
        raise

    # 6. Zbuduj payload 1:1 z MagisterkaPayload
    respondent_id = f'synthetic-{persona_id}-{model_alias}-v{persona_version}-{stamp}'

    # TCTM — konwertuj A/B/C/D na chosenOptionIndex + mascType + isCorrect
    tctm_answers_out = []
    masc_profile = {'correct': 0, 'DOS': 0, 'NAD': 0, 'BK': 0}
    raw_scores = {}
    for presentation_order, item in enumerate(agent_answers.get('tctm', []), 1):
        vid = item['id']
        v = vignettes[vid]
        letter = item['answer'].strip().upper()
        if letter not in 'ABCD':
            raise ValueError(f'Zły format odpowiedzi TCTM {vid}: {item["answer"]}')
        idx = ord(letter) - ord('A')
        masc = v['mascTypes'][idx] if idx < len(v['mascTypes']) else 'unknown'
        is_correct = idx == v['correctAnswer']
        tctm_answers_out.append({
            'itemId': vid,
            'chosenOptionIndex': idx,
            'chosenMascType': masc,
            'isCorrect': is_correct,
            'responseTimeMs': 0,  # syntetyczny respondent — brak realnego czasu
            'changedAnswer': False,
            'presentationOrder': presentation_order,
        })
        if masc == 'correct':
            masc_profile['correct'] += 1
        elif masc in masc_profile:
            masc_profile[masc] += 1
        # raw scores per subscale
        sub = v['subscale']
        if sub not in raw_scores:
            raw_scores[sub] = 0
        if is_correct:
            raw_scores[sub] += 1

    # Likert — konwertuj {"1": 5, "2": 3, ...} na {"ecrr-01": 5, ...}
    def likert_to_keyed(prefix, items_dict, n):
        out = {}
        for i in range(1, n + 1):
            key = str(i)
            if key not in items_dict:
                raise ValueError(f'{prefix} brak pozycji {i}')
            out[f'{prefix}-{i:02d}'] = int(items_dict[key])
        return out

    ecrr_answers = likert_to_keyed('ecrr', agent_answers.get('ecrr', {}), 36)
    ments_answers = likert_to_keyed('ments', agent_answers.get('ments', {}), 28)
    kpp_answers = likert_to_keyed('kpp', agent_answers.get('kpp', {}), 36)
    tipi_answers = likert_to_keyed('tipi', agent_answers.get('tipi', {}), 10)

    feedback = agent_answers.get('feedback', {})

    payload = {
        'respondentId': respondent_id,
        'startedAt': NOW_ISO,
        'completedAt': NOW_ISO,
        'totalDurationMs': int(elapsed * 1000),
        'consented': True,
        'consentTimestamp': NOW_ISO,
        'demographics': {
            'age': 24,
            'gender': 'mezczyzna',
            'education': 'mgr_w_trakcie',
            'residence': 'miasto_250plus',
            'relationshipStatus': 'nieformalny',
            'messengerHoursPerDay': '2_4h',
            'mainPlatform': 'Messenger (Facebook)',
            'socialCompetenceSelf': 3,
            'psychologyBackground': 'no',
            'consentDataStorage': True,
        },
        'tctm': {
            'answers': tctm_answers_out,
            'durationMs': 0,
            'rawScores': raw_scores,
            'mascProfile': masc_profile,
        },
        'ecrR': {'answers': ecrr_answers, 'durationMs': 0},
        'ments': {'answers': ments_answers, 'durationMs': 0},
        'kpp': {'answers': kpp_answers, 'durationMs': 0},
        'tipiPl': {'answers': tipi_answers, 'durationMs': 0},
        'feedback': feedback,
        'synthetic': True,
    }

    # 7. Zapisz pełny wynik + metadane do pliku
    result = {
        'persona_id': persona_id,
        'persona_version': persona_version,
        'biography_length': bio_word_count,
        'model_name': model_used,
        'model_stop_reason': stop_reason,
        'tokens_input': input_tokens,
        'tokens_output': output_tokens,
        'elapsed_seconds': round(elapsed, 2),
        'respondent_id': respondent_id,
        'payload': payload,
    }

    out_path = out_dir / f'{persona_id}-{model_alias}-{stamp}.json'
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[{persona_id}] zapisano: {out_path}')
    print(f'[{persona_id}] MASC profile: {masc_profile}')
    print(f'[{persona_id}] raw scores: {raw_scores}')

    return result


if __name__ == '__main__':
    # Parse --full57 flag
    args = [a for a in sys.argv[1:] if a != '--full57']
    if '--full57' in sys.argv:
        LOAD_ALL_VIGNETTES = True
        print('[CONFIG] Tryb pełnych 57 winiet włączony')

    if len(args) < 1:
        print('Użycie: python run_synthetic.py <persona_id> [opus|sonnet|haiku] [--full57]')
        print(f'  domyślny model: {DEFAULT_MODEL_ALIAS}')
        print(f'  --full57: ładuj wszystkie 57 winiet zamiast TCTM-22')
        sys.exit(1)
    persona_id_arg = args[0]
    model_arg = args[1].lower() if len(args) >= 2 else DEFAULT_MODEL_ALIAS
    if model_arg not in MODEL_ALIASES:
        print(f'Błąd: nieznany alias modelu {model_arg!r}. Dostępne: {", ".join(MODEL_ALIASES.keys())}')
        sys.exit(1)
    run_persona(persona_id_arg, model_alias=model_arg)
