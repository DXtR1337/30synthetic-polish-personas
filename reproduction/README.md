# Baseline Intercepts Versus Persona Slopes — Data and Analysis Package

Reproducibility package for the manuscript:

> Wiencek, M. (2026). *Baseline Intercepts Versus Persona Slopes: Stimulus and
> Administration Fidelity of Polish Narrative-Biography Personas in Large
> Language Models.*

License: **CC BY 4.0** for all materials in this package.

## Contents

```
.
├── synthetic/
│   ├── all_data_v20_public.csv    1,156 scored model runs × 54 columns
│   │                              (22-item battery; all collection events,
│   │                              tagged in the `wave` column)
│   ├── tctm57_runs_v20.csv        123 runs of the 57-vignette extended battery
│   ├── human_pilot_aggregate.csv  human pilot (N = 7), aggregate statistics only
│   └── <persona>.md               30 persona biographies (YAML header with the
│                                  author-declared target profile + Polish
│                                  narrative body)
└── paper-brm/analysis/
    ├── primary_analysis.py        regenerates every statistic cited in the text
    ├── numbers.md                 manifest of every cited statistic (output)
    └── tables/*.csv               35 intermediate tables (output)
```

`wave` semantics: 1–2 = initial collection (truncated stimulus; wave 2 is the
May 28 extension), 3 = corrected-stimulus re-collection of the Azure-served
panel, 4 = corrected-stimulus re-collection of the Bedrock/Gemini panel,
5 = corrected-stimulus extended-battery administration.

## One-command reproduction

Requirements: Python 3.12 with `numpy`, `pandas`, `scipy`, `scikit-learn`.

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
seven individual pilot rows); all model-row statistics are identical either
way, per the pilot's consent scope (aggregate-only publication).

## Not included here

Raw per-run artifacts (verbatim JSON payloads, response files, and the exact
prompts sent — ~119 MB) are deposited alongside this package in the same
archive, as described in the manuscript's Availability statement.

## Citation

If you use these data, scripts, or biographies, please cite the manuscript
above (DOI of this deposit: to be minted on publication of the archive).
