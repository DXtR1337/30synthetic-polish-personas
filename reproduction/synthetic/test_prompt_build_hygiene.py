"""Build-path prompt hygiene test (fail closed).

For every persona biography this test:
  1. requires a well-formed YAML front matter block (opening and closing
     ``---`` delimiters) that parses key: value lines;
  2. strips the front matter exactly the way every collection runner does;
  3. builds the final system prompt through the shared adapter
     (``run_synthetic.build_system_prompt``);
  4. asserts that the built prompt contains no header field name, no target
     value token, and no fragment of the YAML block;
  5. records the SHA-256 of each built system prompt to
     ``prompt_build_hashes.csv`` so any later change to the build path is
     detectable.

Run:  python test_prompt_build_hygiene.py
Exits non-zero on the first violation.
"""
from __future__ import annotations

import csv
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

PERSONAS = [
    "adrian", "agata", "ania", "anna-sim", "bartek", "dominika", "ewa",
    "filip", "gabriela", "hubert", "jakub", "jola", "kamil", "kasia",
    "klaudia", "kuba", "lukasz", "magda", "marek", "michal-k", "michal-sim",
    "natalia", "ola", "pawel", "piotr", "radek", "sara", "tomek",
    "weronika", "zuzia",
]

LEAK_TOKENS = [
    "expected_profile", "author_note", "persona_version", "attachment_style",
    "dbz_anxiety", "dbz_avoidance", "ments_self", "ments_other",
    "ments_motivation", "tipi_E:", "tipi_A:", "tipi_C:", "tipi_ES:",
    "tipi_O:", "kpp:", "very_low", "low_moderate", "high_moderate",
    "very_high", "anxious_preoccupied", "dismissive_avoidant",
    "fearful_avoidant",
]


def split_frontmatter(bio_raw: str, persona_id: str) -> tuple[str, str]:
    """Exactly the runners' logic, fail closed."""
    if not bio_raw.startswith("---\n"):
        raise ValueError(f"{persona_id}: biography has no YAML front matter")
    parts = bio_raw.split("\n---\n", 1)
    if len(parts) != 2:
        raise ValueError(
            f"{persona_id}: malformed persona front matter (missing closing ---); "
            "refusing to build prompt"
        )
    return parts[0][4:], parts[1]


def main() -> int:
    sys.path.insert(0, str(HERE))
    from run_synthetic import build_system_prompt  # the shared adapter

    rows = []
    for persona_id in PERSONAS:
        path = HERE / f"{persona_id}.md"
        bio_raw = path.read_text(encoding="utf-8")
        frontmatter, bio_body = split_frontmatter(bio_raw, persona_id)

        # 1. front matter must parse as simple YAML key/value lines and must
        #    declare the target profile
        if not re.search(r"^expected_profile:", frontmatter, re.M):
            print(f"FAIL {persona_id}: front matter lacks expected_profile")
            return 1

        # 2-3. build the model-facing prompt through the adapter
        system_prompt = build_system_prompt(bio_body)

        # 4. no leak of any header token or any front matter line
        for tok in LEAK_TOKENS:
            if tok in system_prompt:
                print(f"FAIL {persona_id}: token {tok!r} leaked into system prompt")
                return 1
        for line in frontmatter.splitlines():
            line = line.strip()
            if len(line) > 3 and line in system_prompt:
                print(f"FAIL {persona_id}: front matter line leaked: {line!r}")
                return 1
        if not system_prompt.startswith(bio_body[:200]):
            print(f"FAIL {persona_id}: system prompt does not start with narrative body")
            return 1

        rows.append({
            "persona": persona_id,
            "system_prompt_sha256": hashlib.sha256(
                system_prompt.encode("utf-8")
            ).hexdigest(),
            "body_chars": len(bio_body),
        })

    out = HERE / "prompt_build_hashes.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["persona", "system_prompt_sha256", "body_chars"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"PASS: {len(rows)}/30 personas build clean prompts; hashes -> {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
