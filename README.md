# 30 Synthetic Polish Personas — Cross-Vendor Sensitivity Study

**Open-data companion to the paper:**
*Can Language Models Simulate Psychometric Respondents? A Cross-Vendor Sensitivity Study with Baseline Controls and a Replicated Zero-Prompt Framing Manipulation for a Polish Mentalization Battery.*
Michał Wiencek, Independent researcher; MA student, Institute of Psychology, UKEN Kraków.

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

---

## What is this?

Thirty fictional Polish-language biographies with predetermined psychological profiles, processed by five large language models from four vendors, scored against four published Polish psychometric instruments plus one original mentalization vignette test, and compared to a small human pilot. This is a **sensitivity study, not a validation**: it asks whether the instruments react systematically to known personality variation embedded in biographical prompts.

**Key numbers:**
- 30 fictional Polish-language biographies (1,554–2,914 file-total words; 1,489–2,861 narrative-body words)
- 12 ground-truth dimensions per persona (11 continuous + 1 categorical attachment style)
- 5 models × 4 vendors: Claude Sonnet 4.6, Claude Opus 4.6 (Anthropic) · GPT-5.4-mini (OpenAI) · Grok-4-20-reasoning (xAI) · Gemini 3 Flash (Google)
- 285 valid persona runs (300 attempted; 15 missing due to API content filters or partial outputs)
- 46 baseline runs (each model ≈ 8 times "as itself")
- 31 zero-prompt runs (5–8 per model, no system instruction)
- 7 human respondents (small pilot)
- 4 published self-report instruments + TCTM-22 author-keyed vignette test

---

## Headline findings

### TCTM-22 score distribution (first run per persona per model)

| Group | N | M | SD | Range | DOS% | NAD% | BK% |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Human | 7 | 14.3 | 1.4 | 12–16 | 32 | **36** | 32 |
| GPT-5.4-mini | 27† | 17.0 | 1.7 | 13–19 | 70 | 6 | 24 |
| Grok-4-20 | 30 | 18.4 | 4.2 | 6–22 | 64 | 16 | 21 |
| Opus | 30 | 19.0 | 2.1 | 8–20 | 86 | 8 | 7 |
| Sonnet | 30 | 19.4 | 0.7 | 17–20 | **97** | 0 | 3 |
| Gemini 3F | 30 | 19.6 | 2.1 | 9–21 | 23 | **41** | 37 |

†GPT returned no valid 22-item response for 3 of 30 personas (Paweł, Michał-K, Bartek).

LLMs systematically score above the human pilot. **Error profiles are model-dependent**: Claude Sonnet produces almost exclusively DOS errors (97%); Gemini's NAD-heavy profile is descriptively closest to the human pilot.

### Attachment classification

| Model | Accuracy | Cohen's κ | Cramér's V |
|:---|:---:|:---:|:---:|
| Opus | 27/30 = 90% | .866 | .905 |
| Grok-4-20 | 27/30 = 90% | .867 | .890 |
| Gemini 3F | 25/30 = 83% | .778 | .801 |
| Sonnet | 24/30 = 80% | .735 | .765 |
| GPT-5.4-mini | 13/27 = 48% | .333 | .474 |

### Rank–score correlations (median Pearson r across 11 continuous dimensions)

Opus .819 · Grok .815 · Sonnet .800 · Gemini .763 · GPT .711.
Across all five models, 54/55 dimension-level correlations are positive (expected direction); the single negative case is GPT on MentS-Self (r = −.06).
Literature-consistency (10 published cross-scale correlation signs): Gemini 10/10, Sonnet 10/10, Opus 9/10, GPT 9/10, Grok 8/10.

### Test–retest reliability (run 1 vs run 2, complete-pair policy)

| Metric | Sonnet | Opus | GPT | Grok | Gemini |
|:---|:---:|:---:|:---:|:---:|:---:|
| z-score median r | .981 | .993 | .890 | .950 | .962 |
| TCTM total r | .691 | .992 | .279 | .530 | .905 |
| Style agreement | 29/30 | 25/25 | 18/21 | 29/29 | 25/28 |
| N paired personas | 30 | 25 | 21 | 29 | 28 |

### Cross-vendor consistency

- Inter-model z-score median r ranged from **.78** (GPT × Gemini) to **.96** (Sonnet × Opus)
- TCTM-22 cross-vendor agreement was low: ICC(2,1) = **.254** across 5 models on the N = 27 intersect
- Highest TCTM pair: Gemini × Opus (r = .94); lowest: GPT × Grok (r = −.05)
- Fleiss' κ for attachment classification (5 models as raters, N = 27): **.619** ("substantial")
- Cochran's Q on 22 TCTM items: **14/22 significant uncorrected**, **8/22 Bonferroni** (α/22 = .00227, χ² > 16.64), **13/22 BH FDR** at q = .05

### Baseline default response profiles (no persona)

| Model | Style | ANX | AVO | MentS | KPP | TCTM | TIPI-ES |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Sonnet | Dismissive* | 2.09 | 3.88 | 121 | 4.66 | 19.0 | 5.4 |
| Opus | Secure | 2.18 | 2.82 | 126 | 4.69 | 19.6 | 5.4 |
| GPT | Anxious | 4.68 | 2.97 | 101 | 4.04 | 17.3 | 4.7 |
| Grok | Secure | 1.80 | 2.63 | 133 | 4.82 | 20.6 | 6.4 |
| Gemini | Secure | 1.11 | 1.74 | 137 | 4.99 | 20.0 | 7.0 |
| *Polish norms* | | 3.30 | 3.04 | 105 | 3.74 | — | 4.36 |

*Sonnet: dismissive in 6/10 runs, secure in 4/10 (AVO oscillates around 4.0 cutoff).

GPT is anxious-preoccupied in 100% of baseline runs — the only model with a non-secure default. Gemini exhibits a pronounced ceiling effect on every self-report scale.

**Persona manipulation expands variance 2–51-fold over baseline stochasticity.** Model-level medians (across 9 nonzero-baseline-SD dimensions): Grok 3.5×, GPT 3.5×, Gemini 6.7×, Sonnet 6.7×, Opus 8.9×.
On MentS, persona manipulation reduced scores by 17–29 points relative to baseline (Cohen's d = −1.1 to −1.6); GPT was the exception (Δ = +8, d = +0.9).

### Zero-prompt condition: replicated framing effect

With the system instruction removed entirely, each model was queried 5–8 times: 31 valid TCTM-22 payloads (Sonnet 6, Opus 5, GPT 6, Grok 6, Gemini 8) and 30 parseable self-report payloads.

| Scale | Sonnet | Opus | GPT | Grok | Gemini |
|:---|:---:|:---:|:---:|:---:|:---:|
| N self-report | 6 | 5 | 5 | 6 | 8 |
| Δ ANX | **+1.02** | **+0.55** | −0.28 | **+0.75** | **+0.90** |
| Δ AVO | **−0.90** | −0.06 | **+0.62** | −0.27 | +0.40 |
| Δ MentS | +2.7 | −2.8 | **+10.2** | **−6.5** | **−8.0** |
| Δ TIPI-ES | **−0.57** | −0.40 | −0.20 | −0.40 | **−1.00** |

(Δ = no-instruction M − "answer-as-yourself" baseline M; bold |Δ| > 0.5 Likert or > 5 MentS.)

**The "answer as yourself, you are an AI" instruction is not neutral.** Relative to no instruction, it is associated with ≈0.9 scale points higher attachment avoidance for Sonnet, 1.0 point higher emotional stability for Gemini, suppressed self-reported anxiety in four of five models, and acts as a variance-reducing constraint on Sonnet (TCTM-22 SD moves from 0.00 under instruction to 7.4 pp without instruction). GPT inverts the framing effect on MentS and anxiety. **TCTM-22 accuracy is preserved across framing conditions** for four of five models; GPT drops 8 percentage points without the instruction.

---

## Repository structure

```
.
├── personas/             30 .md biographies (YAML frontmatter + Polish narrative body)
├── data/
│   ├── all_data.csv              persona + baseline + human, 343 rows × 52 columns
│   ├── analysis_summary.jsonl    per-persona ground-truth profiles
│   ├── persona_manifest.json     per-persona metadata (version, trait-transparency tag)
│   ├── persona_scores.jsonl      per-run scored payloads
│   ├── validation_report.json    fidelity / directional accuracy / literature consistency
│   └── noprompt_scoring.json     zero-prompt scored aggregates per model
├── results/
│   ├── paper.pdf                 the paper itself (17 pages)
│   ├── paper.tex                 LaTeX source
│   ├── analysis_table.md         per-persona observed-vs-expected breakdown
│   ├── validation_summary.md     plain-text fidelity summary
│   └── charts/                   9 figures used in the paper (PNG)
└── scripts/
    ├── run_synthetic.py          batch-runs all personas through all 5 vendor APIs
    ├── run_baseline.py           batch-runs the baseline ("answer as yourself") condition
    ├── run_noprompt.py           batch-runs the zero-prompt condition
    ├── analyze_and_prepare.py    per-persona scoring (DBZ-R, MentS, KPP, TIPI, TCTM)
    ├── _export_csv.py            assembles all_data.csv from out/*.json
    ├── score_noprompt.py         universal scorer for chaotic zero-prompt JSON formats
    ├── score_noprompt_likert.py  applies score_dbzr/ments/kpp/tipi to noprompt raws
    ├── stats.py / stats57.py     statistics helpers (TCTM-22 / TCTM-57)
    └── validate_personas.py      ground-truth-vs-observed fidelity computation
```

---

## How to reproduce

1. **Generate persona/baseline/zero-prompt runs** (requires API keys for the five vendors):
   ```bash
   python scripts/run_synthetic.py    # all 30 personas × 5 models × 2 runs
   python scripts/run_baseline.py     # 7–10 baseline runs per model
   python scripts/run_noprompt.py     # zero-prompt runs (no system instruction)
   ```
   Outputs land in `out/*.json` (raw per-run payloads).

2. **Score and aggregate:**
   ```bash
   python scripts/analyze_and_prepare.py    # produces per-persona scored outputs
   python scripts/_export_csv.py            # produces data/all_data.csv
   python scripts/score_noprompt.py         # aggregates zero-prompt TCTM
   python scripts/score_noprompt_likert.py  # aggregates zero-prompt self-report
   ```

3. **Validate fidelity vs ground truth:**
   ```bash
   python scripts/validate_personas.py      # produces data/validation_report.json
   ```

The headline tables in the paper are reproduced from `data/all_data.csv` directly. Per-run scoring artifacts (raw API responses, per-persona JSON payloads) are kept locally in the `out/` directory of the source-repo working copy — they are not committed here, but `all_data.csv` plus the scoring scripts reproduce every number in the paper.

---

## Citation

If you use these data, scripts, or biographies in your own work, please cite the paper:

> Wiencek, M. (2026). *Can Language Models Simulate Psychometric Respondents? A Cross-Vendor Sensitivity Study with Baseline Controls and a Replicated Zero-Prompt Framing Manipulation for a Polish Mentalization Battery.* Preprint.

---

## Limitations (read these before drawing conclusions)

- **Sensitivity ≠ validity.** Human data is required for actual construct validity; this study tests only whether the instruments respond systematically to embedded variation.
- **TCTM-22 is author-keyed.** The 22-item vignette test was authored and keyed by the first author. Cross-vendor TCTM agreement is low (ICC = .25), suggesting TCTM-22 in this study is better described as a *response-style probe sensitive to model-specific defaults* than a clean mentalization-construct measure. An independent-keying study is the natural next step.
- **GPT-5.4-mini is unreliable on TCTM** (test–retest r = .28 on the N = 21 paired intersect). GPT also dropped items in 20% of attempts.
- **Human pilot is N = 7.** All human-vs-LLM comparisons are exploratory only.
- **Zero-prompt sample sizes remain modest** (N = 5–8 per model). Headline framing shifts (Sonnet AVO Δ = −0.90, Gemini TIPI-ES Δ = −1.00, anxiety suppression in 4/5 models) are large enough to remain robust under any reasonable inferential treatment, but precise effect-size estimation would benefit from N ≥ 30 per model.
- **No formal preregistration.** All zero-prompt-vs-baseline framing comparisons should be treated as exploratory hypotheses.

---

## License

All materials in this repository (biographies, scored data, analysis scripts) are released under **CC BY 4.0**. You may share and adapt the work, including for commercial purposes, provided you give appropriate credit.

The TCTM-22 vignettes themselves are also CC BY 4.0; the answer keys are author-defined.

---

## AI disclosure

Claude Opus 4.6 and 4.7 (Anthropic) assisted in biography drafting, scoring-pipeline implementation, data analysis, chart generation, and manuscript preparation. All numerical claims were produced by manual inspection of raw response files and verified using the validated scoring routines in `scripts/analyze_and_prepare.py` (the same code used to score the human pilot). The author takes full responsibility for all content, interpretations, and claims.
