# Baseline Intercepts Versus Persona Slopes — Data and Analysis Package

Reproducibility package for the manuscript:

> Wiencek, M. (2026). *Baseline Intercepts Versus Persona Slopes: Stimulus and
> Administration Fidelity of Polish Narrative-Biography Personas in Large
> Language Models.*

Licenses (see `THIRD_PARTY_NOTICES.md` for the full breakdown):
**code** (`*.py`) — MIT; **author-created data and stimuli** (biographies,
scored CSVs, tables, manifests) — CC BY 4.0; **published psychometric
instruments** (DBZ-R, MentS-PL, KPP, TIPI-PL) — not distributed here and not
covered by these licenses.

## Contents

```
.
├── synthetic/
│   ├── all_data_v20_public.csv    1,156 scored model runs × 54 columns
│   │                              (22-item battery; all collection events,
│   │                              tagged in the `wave` column)
│   ├── tctm57_runs_v20.csv        123 runs of the 57-vignette extended battery
│   ├── human_pilot_aggregate.csv  human sanity check (N = 7; file name keeps
│   │                              the historical `pilot` label), aggregate
│   │                              statistics only
│   ├── <persona>.md               30 persona biographies (YAML header with the
│   │                              author-declared target profile + Polish
│   │                              narrative body)
│   ├── run_*.py                   collection runners actually used (Azure,
│   │                              Foundry, Bedrock, Gemini; wave orchestrators
│   │                              run_wave3/4/5); run_synthetic.py holds the
│   │                              shared prompt builder and corrected
│   │                              serializer — instrument items externalized,
│   │                              see THIRD_PARTY_NOTICES.md
│   ├── make_v20_csv.py, analyze_and_prepare.py, score_noprompt.py,
│   │   validate_personas.py       scoring and assembly pipeline
│   ├── test_prompt_build_hygiene.py  build-path test: strips YAML fail-closed,
│   │                              builds every persona's system prompt, asserts
│   │                              zero header/target leakage, records SHA-256
│   ├── prompt_build_hashes.csv    SHA-256 of each built system prompt (output)
│   ├── build_run_manifest.py      builds the per-call audit manifest from the
│   │                              raw artifacts
│   └── run_manifest.csv           1,265 rows — one per archived API call:
│                                  UTC timestamp, condition, persona, exact
│                                  model/deployment ID, tokens, sampling params
│                                  and endpoint/API version where recorded,
│                                  vignettes rendered, SHA-256 of system prompt,
│                                  user prompt, and raw response
└── paper-brm/
    ├── analysis/
    │   ├── primary_analysis.py    regenerates every statistic cited in the text
    │   ├── verify_prompt_hygiene.py  proves no target-header content reached
    │   │                          any model-facing prompt (run against the raw
    │   │                          prompt artifacts; see below)
    │   ├── numbers.md             manifest of every cited statistic (output)
    │   └── tables/*.csv           36 intermediate tables (output)
    └── figures/
        └── make_figures.py, make_revision_figures.py   Figures 1–9
```

`wave` semantics: 1–2 = initial collection (truncated stimulus; wave 2 is the
May 28 extension), 3 = corrected-stimulus re-collection of the Azure-served
panel, 4 = corrected-stimulus re-collection of the Bedrock/Gemini panel,
5 = corrected-stimulus extended-battery administration.

## One-command reproduction

Requirements: Python 3.12; pinned library versions in `requirements.txt`
(`pip install -r requirements.txt`). File integrity: `CHECKSUMS.sha256`.

```bash
cd paper-brm/analysis
python primary_analysis.py
```

This rewrites `tables/*.csv` and `numbers.md` from the released data. All
bootstraps and the mixture model use the fixed seed 20260611, so every value
reproduces exactly. Supplement S1 of the manuscript maps each table and figure
to its generating code.

The script reads the public pair (`all_data_v20_public.csv` +
`human_pilot_aggregate.csv`) as released. On the author's machine it picks up
the private working file (`all_data_v20.csv`, which additionally contains the
seven individual sanity-check rows); all model-row statistics are identical
either way (aggregate-only publication of the human rows).

## Not included here

Raw per-run artifacts (verbatim JSON payloads, response files, and the exact
prompts sent — ~119 MB) are deposited alongside this package in the same
archive, as described in the manuscript's Availability statement.
`verify_prompt_hygiene.py PROMPT_DIR` scans those raw prompt files (2,884
files: 1,442 system + 1,442 user) and confirms that no persona target-header
field name or target value token occurs in any model-facing prompt.
`run_manifest.csv` in this package indexes those artifacts by SHA-256, so
each raw file can be verified against the manifest.

Also not included: the verbatim items of the third-party instruments (DBZ-R,
MentS-PL, KPP, TIPI-PL); the collection runners load them from a local,
non-distributed module, so the released code documents the exact pipeline but
re-running a collection requires locally supplied instrument copies and API
credentials (see `THIRD_PARTY_NOTICES.md`). The author-owned TCTM-22/57
vignette source with keys IS included (`stimuli/tctm54.ts`).

## Citation

If you use these data, scripts, or biographies, please cite the manuscript
above. DOI of this deposit: https://doi.org/10.5281/zenodo.21406224 (release v1.0.1).
