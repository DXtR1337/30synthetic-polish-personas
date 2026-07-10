# Baseline Intercepts Versus Persona Slopes — Open-Data Companion

**Open-data companion to the manuscript:**
*Baseline Intercepts Versus Persona Slopes: Stimulus and Administration Fidelity of Polish Narrative-Biography Personas in Large Language Models.*
Michał Wiencek, Institute of Psychology, University of the National Education Commission (UKEN), Kraków.

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

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
- Human pilot N = 7 (released in aggregate form only, per consent scope)
- Instruments: DBZ-R, MentS-PL, KPP, TIPI-PL + TCTM-22 (author-keyed subtext-recognition vignette test)

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
| `data/human_pilot_aggregate.csv` | human pilot (N = 7), aggregate statistics only |
| `personas/` | 30 biographies (YAML ground-truth header + Polish narrative body) |

Every statistic cited in the manuscript regenerates with one command from the
self-contained package in `reproduction/`:

```bash
cd reproduction/paper-brm/analysis
python primary_analysis.py        # Python 3.12: numpy, pandas, scipy, scikit-learn
```

This rewrites 35 tables and `numbers.md` (the manifest of every cited
statistic) from the public data with the fixed seed 20260611; Supplement S1
maps each table and figure to its generating code. The same package is
deposited at Zenodo.

---

## Repository structure

```
.
├── manuscript/     current manuscript + supplement (PDF)
├── data/           scored run-level data (v20 files above + legacy snapshot)
├── personas/       30 biographies (YAML ground-truth header + narrative body)
├── reproduction/   self-contained analysis package (data + script + outputs)
├── results/        legacy: early drafts, tables, and charts (initial collection)
├── scripts/        legacy: collection and scoring scripts of the early snapshot
└── LEGACY_README.md
```

---

## Legacy snapshot (initial collection, 5–6 models)

Files from the first public snapshot of this repository describe the **initial
collection only** (truncated stimulus, before GPT-5.4 (full) joined the panel)
and are retained for the historical record — their numbers are superseded by
the corrected collection and the v20 files above:

- `data/all_data.csv` (early scored subset), `data/*.jsonl`, `data/*.json`
- `results/` (early paper drafts, tables, and charts)
- `LEGACY_README.md` — the original README with the early per-persona tables

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
- **Human pilot is N = 7**, used only as a difficulty floor.
- Not preregistered; exploratory analyses are labeled as such in the text.

---

## Citation

> Wiencek, M. (2026). *Baseline Intercepts Versus Persona Slopes: Stimulus and
> Administration Fidelity of Polish Narrative-Biography Personas in Large
> Language Models.* Manuscript / preprint.

## License

All materials (biographies, scored data, analysis scripts) are released under
**CC BY 4.0**. The TCTM vignettes are CC BY 4.0; the answer keys are
author-defined.

## AI disclosure

Claude (Anthropic) assisted in biography drafting, scoring-pipeline
implementation, data analysis, and manuscript preparation. The author reviewed
all generated content and takes full responsibility for all content,
interpretations, and claims.
