"""Prompt hygiene check: no target-header content in any model-facing prompt.

Scans every archived model-facing prompt file (the verbatim *-system.txt and
*-user.txt texts sent to the API endpoints) for (a) every field name of the
persona YAML target header and (b) every target value token. The manuscript
claims zero occurrences; this script verifies it and exits non-zero on any hit.

Usage:
    python verify_prompt_hygiene.py [PROMPT_DIR]

PROMPT_DIR defaults to the author's raw-artifact layout (../../synthetic/out
relative to this file); in the public deposit, point it at the directory
holding the raw prompt files.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HEADER_FIELDS = [
    "expected_profile",
    "persona_id",
    "persona_version",
    "author_note",
    "dbz_anxiety",
    "dbz_avoidance",
    "ments_self",
    "ments_other",
    "ments_motivation",
    "kpp:",
    "tipi_E:",
    "tipi_A:",
    "tipi_C:",
    "tipi_ES:",
    "tipi_O:",
    "attachment_style",
]

TARGET_VALUES = [
    "very_low",
    "low_moderate",
    "moderate",
    "high_moderate",
    "very_high",
    "secure",
    "anxious_preoccupied",
    "dismissive_avoidant",
    "fearful_avoidant",
    "disorganized",
]

PATTERN = re.compile(
    "|".join(re.escape(tok) for tok in HEADER_FIELDS + TARGET_VALUES)
)


def main() -> int:
    default_dir = Path(__file__).resolve().parent.parent.parent / "synthetic" / "out"
    prompt_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else default_dir
    if not prompt_dir.is_dir():
        print(f"FAIL: prompt directory not found: {prompt_dir}")
        return 2

    files = sorted(prompt_dir.glob("*-system.txt")) + sorted(
        prompt_dir.glob("*-user.txt")
    )
    if not files:
        print(f"FAIL: no *-system.txt / *-user.txt files in {prompt_dir}")
        return 2

    hits: list[tuple[str, str]] = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        m = PATTERN.search(text)
        if m:
            hits.append((f.name, m.group(0)))

    n_sys = sum(1 for f in files if f.name.endswith("-system.txt"))
    n_usr = len(files) - n_sys
    print(f"scanned {len(files)} prompt files ({n_sys} system + {n_usr} user)")
    if hits:
        print(f"FAIL: {len(hits)} file(s) contain header/target tokens:")
        for name, tok in hits[:20]:
            print(f"  {name}: {tok!r}")
        return 1
    print("PASS: zero occurrences of any header field name or target value token")
    return 0


if __name__ == "__main__":
    sys.exit(main())
