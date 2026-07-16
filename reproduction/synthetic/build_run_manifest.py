"""Build run_manifest.csv — one audit row per archived API call.

Walks every ``out/*.json`` run record together with its companion artifacts
(``*-system.txt``, ``*-user.txt``, ``*-raw.txt``) and emits a manifest with:

  run_id, utc_timestamp, condition, persona, model_alias, model_name
  (exact deployment identifier as returned/configured), stop reason, token
  counts, elapsed seconds, sampling parameters and endpoint/deployment/API
  version where the runner recorded them, biography SHA-256 where recorded,
  the number of vignettes actually rendered into the user prompt, SHA-256 of
  the exact system prompt, user prompt, and raw response, and whether the
  parsed payload contained scoreable TCTM answers.

Fields a given collection's runner did not record are left blank rather than
reconstructed. Usage:  python build_run_manifest.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

PERSONAS = {
    "adrian", "agata", "ania", "anna-sim", "bartek", "dominika", "ewa",
    "filip", "gabriela", "hubert", "jakub", "jola", "kamil", "kasia",
    "klaudia", "kuba", "lukasz", "magda", "marek", "michal-k", "michal-sim",
    "natalia", "ola", "pawel", "piotr", "radek", "sara", "tomek",
    "weronika", "zuzia",
}

STEM_RE = re.compile(r"^(?P<prefix>.+)-(?P<stamp>\d{8}T\d{6})$")


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_prefix(prefix: str) -> tuple[str, str, str]:
    """-> (condition, persona, model_alias)."""
    if prefix.startswith("baseline-"):
        return "baseline", "", prefix[len("baseline-"):]
    if prefix.startswith("noprompt-"):
        return "zero_prompt", "", prefix[len("noprompt-"):]
    # persona runs: longest persona name that prefixes the stem
    for p in sorted(PERSONAS, key=len, reverse=True):
        if prefix == p:
            return "persona", p, ""
        if prefix.startswith(p + "-"):
            return "persona", p, prefix[len(p) + 1:]
    return "unknown", "", prefix


def main() -> None:
    rows = []
    for jf in sorted(OUT.glob("*.json")):
        m = STEM_RE.match(jf.stem)
        if not m:
            continue
        prefix, stamp = m.group("prefix"), m.group("stamp")
        condition, persona, alias = split_prefix(prefix)
        try:
            rec = json.loads(jf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            rec = {}
        sampling = rec.get("sampling", {}) or {}
        dep = rec.get("azure_deployment", {}) or {}

        user_f = OUT / f"{jf.stem}-user.txt"
        system_f = OUT / f"{jf.stem}-system.txt"
        raw_f = OUT / f"{jf.stem}-raw.txt"
        n_vignettes = ""
        if user_f.exists():
            n_vignettes = user_f.read_text(encoding="utf-8", errors="replace").count("### Winieta")

        payload = rec.get("payload", {}) or {}
        tctm = (payload.get("tctm") or {})
        answers = tctm.get("answers") if isinstance(tctm, dict) else tctm
        scoreable = bool(answers)

        rows.append({
            "run_id": jf.stem,
            "utc_timestamp": f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}Z",
            "condition": condition,
            "persona": persona,
            "model_alias": alias,
            "model_name": rec.get("model_name", ""),
            "stop_reason": rec.get("model_stop_reason", ""),
            "tokens_input": rec.get("tokens_input", ""),
            "tokens_output": rec.get("tokens_output", ""),
            "elapsed_seconds": rec.get("elapsed_seconds", ""),
            "temperature": sampling.get("temperature", ""),
            "top_p": sampling.get("top_p", ""),
            "seed": sampling.get("seed", ""),
            "reasoning_effort": sampling.get("reasoning_effort", ""),
            "max_tokens": sampling.get("max_completion_tokens", ""),
            "endpoint": dep.get("endpoint", ""),
            "deployment": dep.get("deployment", ""),
            "api_version": dep.get("api_version", ""),
            "biography_sha256": rec.get("biography_sha256", ""),
            "n_vignettes_rendered": n_vignettes,
            "prompt_system_sha256": sha256_file(system_f),
            "prompt_user_sha256": sha256_file(user_f),
            "response_sha256": sha256_file(raw_f),
            "scoreable_tctm": scoreable,
        })

    out = HERE / "run_manifest.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {out.name}")


if __name__ == "__main__":
    main()
