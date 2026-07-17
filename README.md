# Baseline Intercepts Versus Persona Slopes — Open-Data Companion

**Open-data companion to the manuscript:**
*Baseline Intercepts Versus Persona Slopes: Stimulus and Administration Fidelity of Polish Narrative-Biography Personas in Large Language Models.*
Michał Wiencek, Institute of Psychology, University of the National Education Commission (UKEN), Kraków.

[![License: CC BY 4.0](https://img.shields.io/badge/Data%20%26%20stimuli-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Code: MIT](https://img.shields.io/badge/Code-MIT-lightgrey.svg)](LICENSE-CODE)
[![reproduce-analysis](https://github.com/DXtR1337/30synthetic-polish-personas/actions/workflows/reproduce.yml/badge.svg)](https://github.com/DXtR1337/30synthetic-polish-personas/actions/workflows/reproduce.yml)

---

## What is this?

Thirty fictional Polish-language narrative biographies (1,489–2,861 words of
narrative body), each encoding a predetermined 12-dimension psychological
profile, administered to **seven LLMs from four vendors** under three
conditions (persona, baseline, zero-prompt) with a five-instrument Polish
battery — twice, on two stimulus versions: an initial collection on a
rendering later found to be defective, and a full corrected-stimulus
re-collection that doubles as a longitudinal replication.

All agreement results are **stimulus fidelity, not construct validity**: the
biography targets and the TCTM-22 answer key are author-defined and not
independently adjudicated.

**Key numbers (current dataset, v20):**

- 30 biographies, 12 author-declared dimensions each (11 continuous + categorical attachment style)
- 7 models × 4 vendors: Claude Sonnet 4.6, Claude Opus 4.6 (Anthropic, via AWS Bedrock) · GPT-5.4-mini, GPT-5.4 (full), GPT-5.5 (OpenAI, via Azure) · Grok-4-20-reasoning (xAI) · Gemini 3 Flash (Google)
- Two full collections: initial (April 12 – May 11 + May 28, 2026; truncated stimulus) and corrected re-collection (May 31 Azure; June 10–11 Bedrock/Gemini)
- Scored runs: persona 426 initial + 424 corrected; baseline 149 + 70; zero-prompt 43 + 44
- Extended 57-vignette battery: 123 runs (Sonnet + GPT-5.5, both stimulus versions)
- Human sanity check N = 7 (comprehensibility check, not a psychometric pilot; released in aggregate form only, per consent scope)
- Instruments: DBZ-R, MentS-PL, KPP, TIPI-PL + TCTM-22 (author-keyed subtext-recognition vignette test)

## Interactive companion (live)

Every statistic in the manuscript can also be explored interactively — each
number links down to its formula, the underlying CSV rows, and the run that
produced them. The companion is Polish-first (the stimulus language);
**English entry point: [podtekst.app/magisterka/en](https://podtekst.app/magisterka/en)**
(study summary, live headline table, and a map of the Polish subpages).

- [podtekst.app/magisterka](https://podtekst.app/magisterka) — results dashboard (35+ charts, corrected-collection panel)
- [/magisterka/paper](https://podtekst.app/magisterka/paper) — interactive paper viewer with clickable numbers (working-draft chronicle v14–v19 + BRM manuscript PDFs)
- [/magisterka/persony](https://podtekst.app/magisterka/persony) — the 30 biographies with their 12-dimension target profiles and per-model outputs
- [/magisterka/genealogy](https://podtekst.app/magisterka/genealogy) — data genealogy: raw files → parsed → scored → aggregated → derived, with the verify-gate report
- [/magisterka/metodologia](https://podtekst.app/magisterka/metodologia) — methodology notes · [/magisterka/glossary](https://podtekst.app/magisterka/glossary) — glossary

The verbatim per-run prompt files are not publicly browsable there (the user
prompts embed third-party instrument items — same restriction as the
raw-artifacts archive); scored data, biographies, and aggregates are open.

**Headline results (corrected collection):** attachment-style agreement with
author labels κ = .69–.96 per model (Fleiss κ = .85 across the panel); all 21
between-model persona-profile correlations ≥ .947; model baselines differ by
up to 1.7 SD on Polish norms while persona orderings replicate at r ≥ .92
across collections up to eight weeks apart. Item-level key agreement can swing
by up to 98 percentage points with stimulus rendering and administration
context while aggregate scores hold.

---

## Primary data files (v20)

| File | Contents |
|:---|:---|
| `data/all_data_v20_public.csv` | 1,156 scored model runs × 54 columns, 22-item battery, all collection events (`wave` column: 1–2 = initial, 3 = corrected Azure, 4 = corrected Bedrock/Gemini, 5 = extended battery) |
| `data/tctm57_runs_v20.csv` | 123 runs of the 57-vignette extended battery |
| `data/human_pilot_aggregate.csv` | human sanity check (N = 7; file name keeps the historical `pilot` label), aggregate statistics only |
| `personas/` | 30 biographies (YAML ground-truth header + Polish narrative body) |

Every statistic cited in the manuscript regenerates with one command from the
self-contained package in `reproduction/`:

```bash
cd reproduction/paper-brm/analysis
python primary_analysis.py        # Python 3.12: numpy, pandas, scipy, scikit-learn
```

This rewrites 36 tables and `numbers.md` (the manifest of every cited
statistic) from the public data with the fixed seed 20260611; Supplement S1
maps each table and figure to its generating code. Pinned environment:
`requirements.txt`; file integrity: `reproduction/CHECKSUMS.sha256`. The same
package is deposited at Zenodo. CI (`.github/workflows/reproduce.yml`) re-runs
the analysis and the hygiene test on every push and fails if any released
output changes.

`reproduction/synthetic/` additionally contains the **collection pipeline
actually used** (per-vendor runners, wave 3/4/5 orchestrators, scoring and
CSV-assembly scripts — instrument items externalized for copyright, see
`THIRD_PARTY_NOTICES.md`) plus the audit artifacts:

- `run_manifest.csv` — 1,265 rows, one per archived API call: UTC timestamp,
  condition, persona, exact model/deployment ID, token counts, sampling
  parameters and endpoint/API version where recorded, number of vignettes
  rendered, and SHA-256 of the exact system prompt, user prompt, and raw
  response;
- `test_prompt_build_hygiene.py` + `prompt_build_hashes.csv` — fail-closed
  build-path test proving that no persona target-header content can reach a
  model-facing prompt (the YAML ground-truth headers were researcher-only
  metadata; an exhaustive scan of all 2,884 archived prompt files finds zero
  occurrences of any header field or target value);
- `verify_prompt_hygiene.py` — the corresponding scan for the raw prompt
  artifacts (deposited with the Zenodo release).

---

## Repository structure

```
.
├── manuscript/            current manuscript + supplement (PDF)
├── data/                  scored run-level data (v20 files above + legacy snapshot)
├── personas/              30 biographies (YAML ground-truth header + narrative body)
├── stimuli/               full TCTM-22/57 vignette source with author keys and
│                          MASC-style distractor tags (tctm54.ts, CC BY 4.0)
├── reproduction/          self-contained package: data + analysis + collection
│                          pipeline + audit manifests (mirrors the Zenodo deposit)
├── results/               legacy: early drafts, tables, and charts (initial collection)
├── legacy/collection-v1/  ARCHIVAL ONLY: early-snapshot collection scripts
│                          (pre-correction serializer) + the original README
├── .github/workflows/     CI: clean-environment reproduction gate
├── CITATION.cff · requirements.txt · THIRD_PARTY_NOTICES.md · LICENSE · LICENSE-CODE
```

---

## Per-persona results (corrected collection, 7 models)

Computed directly from `data/all_data_v20_public.csv` (waves 3–4). The
counts below reproduce Table 2 and Figure 1 of the manuscript exactly.

### Attachment style — first corrected-collection administration, per persona × 7 models

Author label from the biography header; `disorganized` is scored as equivalent to fearful-avoidant (see manuscript Section 2.2). Codes: **sec** secure · **anx** anxious-preoccupied · **dis** dismissive-avoidant · **fea** fearful-avoidant. Bold = mismatch with the author label.

| Persona | Author | Sonnet | Opus | 5.4-mini | 5.4 (full) | GPT-5.5 | Grok | Gemini |
|---|---|---|---|---|---|---|---|---|
| adrian | dis | dis | dis | dis | dis | dis | dis | dis |
| agata | dis | dis | dis | dis | dis | dis | dis | dis |
| ania | anx | anx | anx | anx | anx | anx | anx | anx |
| anna-sim | sec | sec | sec | sec | sec | sec | sec | sec |
| bartek | anx | **dis** | **fea** | anx | **fea** | **fea** | **fea** | **fea** |
| dominika | dis | dis | dis | dis | dis | dis | dis | dis |
| ewa | dis* | fea | fea | fea | fea | fea | fea | fea |
| filip | fea | fea | fea | fea | fea | fea | fea | fea |
| gabriela | anx | **sec** | **sec** | anx | anx | **sec** | anx | anx |
| hubert | dis | dis | dis | dis | dis | dis | dis | dis |
| jakub | dis | dis | dis | dis | dis | dis | dis | dis |
| jola | anx | anx | anx | anx | anx | anx | anx | anx |
| kamil | dis* | **dis** | fea | fea | **dis** | fea | fea | **dis** |
| kasia | sec | sec | sec | sec | sec | sec | sec | sec |
| klaudia | anx | **sec** | anx | anx | anx | anx | anx | anx |
| kuba | sec | sec | sec | sec | sec | sec | sec | sec |
| lukasz | sec | sec | sec | sec | sec | sec | sec | **anx** |
| magda | dis | dis | dis | dis | dis | dis | dis | dis |
| marek | dis* | **dis** | **dis** | **dis** | **dis** | **dis** | **dis** | **dis** |
| michal-k | anx | **fea** | **fea** | anx | **fea** | **fea** | **fea** | **fea** |
| michal-sim | fea | fea | fea | fea | fea | fea | fea | fea |
| natalia | anx | anx | anx | anx | anx | anx | anx | anx |
| ola | sec | sec | sec | sec | sec | sec | sec | sec |
| pawel | anx | anx | **fea** | anx | anx | anx | **fea** | anx |
| piotr | fea | fea | fea | fea | fea | fea | fea | fea |
| radek | dis* | fea | fea | fea | fea | fea | fea | fea |
| sara | sec | sec | sec | sec | sec | sec | sec | sec |
| tomek | dis | dis | dis | dis | dis | dis | dis | dis |
| weronika | sec | sec | sec | sec | sec | sec | sec | sec |
| zuzia | fea | **dis** | fea | fea | fea | fea | fea | fea |

Per-model agreement with the author label: Sonnet **23/30** · Opus **25/30** · 5.4-mini **29/30** · 5.4 (full) **26/30** · GPT-5.5 **26/30** · Grok **26/30** · Gemini **25/30**. Unanimously correct: **21/30** personas.

### TCTM-22 author-key agreement (of 22) — mean over the two corrected administrations

| Persona | Sonnet | Opus | 5.4-mini | 5.4 (full) | GPT-5.5 | Grok | Gemini |
|---|---|---|---|---|---|---|---|
| adrian | 21 | 19.5 | 17.3 | 21 | 21 | 20.7 | 20.5 |
| agata | 22 | 19 | 19 | 21 | 21.5 | 20.5 | 20.5 |
| ania | 21 | 20 | 19 | 20 | 21 | 19 | 19 |
| anna-sim | 21 | 18.5 | 18 | 20.5 | 21 | 18.5 | 20.5 |
| bartek | 21 | 18.5 | 17.5 | 20.5 | 21 | 22 | 19 |
| dominika | 21 | 19 | 18 | 21 | 21 | 20 | 19.5 |
| ewa | 21 | 20 | 18 | 20.5 | 21 | 21 | 18.5 |
| filip | 21 | 19 | 20 | 20.5 | 21 | 21.5 | 19 |
| gabriela | 21 | 19.5 | 17 | 20 | 21.5 | 21.5 | 19 |
| hubert | 21 | 19.5 | 18 | 20.5 | 21 | 17 | 19.5 |
| jakub | 22 | 19 | 19.5 | 20.5 | 21 | 17.5 | 20.5 |
| jola | 21 | 19 | 19 | 20 | 21 | 18.5 | 19.5 |
| kamil | 21 | 20 | 19 | 21 | 20.5 | 21.5 | 19 |
| kasia | 20 | 20 | 18.5 | 20 | 21 | 21 | 20 |
| klaudia | 21 | 20 | 18.5 | 20.5 | 21 | 22 | 19.5 |
| kuba | 21.5 | 20 | 17 | 21 | 21 | 21 | 19.5 |
| lukasz | 20 | 20 | 18 | 21 | 21 | 21.5 | 19.5 |
| magda | 21 | 18.5 | 17 | 21 | 22 | 20 | 20.5 |
| marek | 21 | 19.5 | 19.5 | 21 | 21.5 | 20 | 20 |
| michal-k | 21 | 20 | 18 | 21 | 21 | 20 | 20 |
| michal-sim | 21.5 | 17.5 | 20 | 20 | 21 | 21.5 | 20 |
| natalia | 21 | 19 | 18.5 | 18.5 | 18.5 | 19 | 18.5 |
| ola | 19.5 | 11 | 15 | 13.5 | 16.5 | 7.5 | 9 |
| pawel | 21 | 20 | 18.5 | 20 | 19 | 20.5 | 19.5 |
| piotr | 21 | 18.5 | 20 | 20 | 21 | 21 | 19.5 |
| radek | 21.5 | 21 | 21 | 21 | 21 | 21 | 19.5 |
| sara | 20 | 20 | 15.5 | 20 | 21 | 21 | 20 |
| tomek | 21 | 19 | 19 | 21 | 21.5 | 20.5 | 20 |
| weronika | 20 | 20 | 15.5 | 20.5 | 21 | 21.5 | 21 |
| zuzia | 22 | 20 | 19.5 | 21 | 21 | 21.5 | 19.5 |

**The paradox persona `ola`** (secure attachment + low mentalization by design) is classified secure by all seven models while degrading their TCTM-22 scores relative to the other 29 personas: Sonnet −1.5 · Opus −8.4 · 5.4-mini −3.4 · 5.4 (full) −7.0 · GPT-5.5 −4.4 · Grok −12.9 · Gemini −10.7 points. The models adopt the biography's low-mentalization stance at the cost of test agreement - the biography, not an answer key, governs the response.

---

### Profile-recovery summary per model (persona condition, corrected collection)

Style = personas whose first-administration classification matches the author label; author–model *r* = median per-dimension Pearson correlation between author ordinal targets and produced z-scores across nine dimensions (Spearman ρ in parentheses); error percentages use the MASC-style distractor tags (DOS undermentalizing · NAD overmentalizing · BK no mentalization), all persona runs pooled.

| Model | Style match | Cohen's κ [95% CI] | Author–model r (ρ) | TCTM-22 M ± SD | Correct % | DOS % | NAD % | BK % |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Sonnet | 23/30 (77%) | .69 [.48, .87] | .84 (.83) | 20.97 ± 0.61 | 95.3 | 3.6 | 1.1 | 0.0 |
| Opus | 25/30 (83%) | .78 [.59, .95] | .85 (.83) | 19.15 ± 1.73 | 87.0 | 10.5 | 1.4 | 1.0 |
| 5.4-mini | 29/30 (97%) | .96 [.86, 1.00] | .79 (.79) | 18.26 ± 1.64 | 83.4 | 9.6 | 2.0 | 4.9 |
| 5.4 (full) | 26/30 (87%) | .82 [.64, .96] | .82 (.82) | 20.28 ± 1.42 | 92.2 | 2.2 | 1.0 | 4.7 |
| GPT-5.5 | 26/30 (87%) | .82 [.64, .96] | .82 (.82) | 20.79 ± 1.05 | 94.5 | 3.1 | 2.4 | 0.1 |
| Grok | 26/30 (87%) | .82 [.64, .96] | .80 (.74) | 20.00 ± 2.74 | 90.9 | 3.3 | 3.5 | 2.3 |
| Gemini | 25/30 (83%) | .78 [.59, .95] | .82 (.83) | 19.32 ± 2.07 | 88.2 | 1.9 | 5.7 | 4.2 |
| Human sanity check | — | — | — | 14.29 ± 1.38 (range 12–16) | 65.0 | — | — | — |

All seven models sit in a band clinicians would call substantial agreement — and 5.9–7.5 points of 22 above the human sanity check, consistent with LLMs being closer to native speakers of text-only chat than humans operating outside their primary modality (see manuscript Section 4.4). Fleiss κ across the seven-model panel: **.85** (bootstrap 95% CI [.75, .94]); all 21 pairwise persona-profile correlations lie in **[.947, .989]**.

### Test–retest within the corrected collection (administration 1 vs 2, 30 paired runs)

| Model | Median r (9 z-dims) | TCTM-22 total r | Same style, run 1 vs 2 |
|:---|:---:|:---:|:---:|
| Sonnet | .99 | .83 | 29/30 |
| Opus | .99 | .92 | 29/30 |
| 5.4-mini | .96 | .42 | 29/30 |
| 5.4 (full) | .99 | .90 | 29/30 |
| GPT-5.5 | .99 | .90 | 30/30 |
| Grok | .95 | .88 | 28/30 |
| Gemini | .97 | .93 | 29/30 |

### Stimulus-correction recovery: the four affected items (author-key agreement %)

A serializer defect silently truncated three vignettes (s07, w19, pw07) and one stem mis-referenced its target (w22). Cells show **truncated → corrected** agreement, persona runs pooled. Restoring the stem-referenced line makes s07 recover by up to **+98 points**; restoring the full w19 escalation arc makes the item *harder* (accidental simplification); the corrected w22 key stays contested in the 22-item battery.

| Item | Sonnet | Opus | 5.4-mini | 5.4 (full) | GPT-5.5 | Grok | Gemini |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| s07 | 2 → 100 | 7 → 28 | 0 → 8 | 0 → 97 | 56 → 97 | 33 → 79 | 83 → 93 |
| w19 | 95 → 100 | 100 → 72 | 90 → 95 | 95 → 84 | 92 → 56 | 93 → 97 | 75 → 38 |
| pw07 | 100 → 100 | 95 → 100 | 18 → 44 | 95 → 98 | 97 → 100 | 57 → 97 | 97 → 97 |
| w22 | 2 → 17 | 0 → 0 | 75 → 84 | 0 → 0 | 59 → 51 | 55 → 57 | 22 → 7 |

Aggregate TCTM-22 totals barely notice these swings (per-model paired means move by −0.27 to +1.56 points of 22): item-level agreement is a property of the *(item, rendered stimulus, administration protocol)* triple, not of the item alone.

---

## Legacy snapshot (initial collection, 5–6 models)

Files from the first public snapshot of this repository describe the **initial
collection only** (truncated stimulus, before GPT-5.4 (full) joined the panel)
and are retained for the historical record — their numbers are superseded by
the corrected collection and the v20 files above:

- `data/all_data.csv` (early scored subset), `data/*.jsonl`, `data/*.json`
- `results/` (early paper drafts, tables, and charts)
- `legacy/collection-v1/` — the early-snapshot collection scripts, each marked
  `ARCHIVAL ONLY`; the pipeline used for the corrected collections lives in
  `reproduction/synthetic/`
- `legacy/collection-v1/LEGACY_README.md` — the original README with the early
  per-persona tables

Two retroactive redactions to the legacy snapshot (2026-07-17): (1) seven
individual-level human sanity-check rows were removed from
`data/all_data.csv` — the consent covers aggregate-only publication
(`data/human_pilot_aggregate.csv` is the released form; the individual rows
remain privately retained by the author); (2) verbatim third-party instrument
items were removed from the archival `run_synthetic.py` for copyright reasons
(see `THIRD_PARTY_NOTICES.md`). Earlier git history predating these
redactions is scheduled to be rewritten before the archival release.

The stimulus-rendering defect that motivated the re-collection (three vignettes
silently truncated by the serializer, one stem corrected) is documented in
Section 2.4 and Supplement S2 of the manuscript.

---

## Limitations (read before drawing conclusions)

- **Author-keyed test, author-declared targets.** No independent adjudication
  panel; all agreement figures are stimulus-fidelity quantities.
- **Generator dependency.** Biographies were drafted with Claude Opus 4.6 as a
  writing assistant; the data show no large descriptive Claude advantage, but
  shared method variance cannot be excluded.
- **Runs are nested.** Hundreds of runs are repetitions within 30 personas and
  7 models — not independent observations.
- **Human sanity check is N = 7** — a comprehensibility check and small
  descriptive reference point, not a psychometric pilot; it sets no norm.
- **Known stimulus artifact:** the `zuzia` biography contains a leaked
  editorial parenthetical (a cross-persona reference from drafting,
  self-corrected in the same sentence). It was present identically in every
  administration of that persona in both collections, so the released file
  is the stimulus exactly as administered — documented here rather than
  retroactively edited (see manuscript Supplement S8).
- Not preregistered; exploratory analyses are labeled as such in the text.

---

## Citation

> Wiencek, M. (2026). *Baseline Intercepts Versus Persona Slopes: Stimulus and
> Administration Fidelity of Polish Narrative-Biography Personas in Large
> Language Models.* Manuscript / preprint.

## License

Split by material type (full breakdown in `THIRD_PARTY_NOTICES.md`):

- **Code** (`*.py`, workflows) — **MIT** (`LICENSE-CODE`);
- **Author-created data and stimuli** (biographies, TCTM vignettes and keys,
  scored CSVs, tables, manifests) — **CC BY 4.0** (`LICENSE`);
- **Published psychometric instruments** (DBZ-R, MentS-PL, KPP, TIPI-PL) —
  **not distributed** in this repository and not covered by these licenses;
  the collection scripts load them from a local, user-supplied module.

## AI disclosure

Claude (Anthropic) assisted in biography drafting, scoring-pipeline
implementation, data analysis, and manuscript preparation. The author reviewed
all generated content and takes full responsibility for all content,
interpretations, and claims.
