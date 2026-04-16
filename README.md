# TCTM-22 Synthetic Persona Sensitivity Study (N=30)

**30 fictional biographies with ground-truth psychological profiles, processed by 5 LLMs from 4 vendors (300 runs + 7 human respondents = 307 observations), to test whether psychometric instruments react to known personality variation — a sensitivity study, not a validation.**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

---

## Abstract

This repository contains the core materials for a synthetic persona sensitivity experiment conducted as part of an MA thesis at the Uniwersytet Komisji Edukacji Narodowej (UKEN) in Krakow, Poland. The thesis investigates mentalization in text-based communication among young Polish adults.

Thirty fictional characters ("personas") were authored with predetermined psychological profiles across 12 dimensions: attachment anxiety and avoidance (DBZ-R, 2 scales), mentalization self/other/motivation (MentS-PL, 3 scales), need for cognition (KPP, 1 scale), Big Five E/A/C/ES/O (TIPI-PL, 5 scales), and attachment style (4-category classification derived from DBZ-R; 11 continuous + 1 categorical = 12 total). Each persona was written as an immersive second-person biography in Polish, ranging from 1,554 to 2,914 words.

Each persona was processed by **5 models from 4 vendors**: Claude Sonnet 4.6 and Claude Opus 4.6 (Anthropic), GPT-5.4-mini (OpenAI), Grok-4-20-reasoning (xAI), and Gemini 3 Flash (Google). Each model was instructed to complete a battery of four published psychometric instruments plus one original mentalization vignette test (TCTM-22) "as that persona." (Note: GPT-5.4-mini returned incomplete TCTM responses in 20% of runs; see Limitations.) Each model was run twice (test-retest). Additionally, 7 human respondents completed the same battery. Total: **307 observations** (300 LLM + 7 human; 30 additional Sonnet runs with the full TCTM-57 vignette pool are also available).

This dataset provides the full pipeline: biographies, expected profiles, observed scores, cross-vendor comparison, test-retest reliability, and human vs LLM error profile analysis.

## Key Results

> **Note:** All cross-model tables below report the **first run** per persona per model (N=30/model). The second run (retest) is used exclusively for test-retest reliability analysis.

### TCTM-22 Scores by Group

| Group | N | M | SD | Range | DOS% | NAD% | BK% |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Human | 7 | 14.3 | 1.4 | 12–16 | 32% | **36%** | 32% |
| GPT-5.4-mini | 30 | 16.8 | 1.6 | 13–19 | 71% | 6% | 23% |
| Grok-4-20-reasoning | 30 | 18.4 | 4.2 | 6–22 | 62% | 18% | 20% |
| Opus | 30 | 19.1 | 2.0 | 9–20 | 85% | 8% | 7% |
| Sonnet | 30 | 19.6 | 0.9 | 16–21 | 96% | 0% | 4% |
| **Gemini 3 Flash** | **30** | **19.6** | **2.1** | **9–21** | **24%** | **42%** | **34%** |

**NAD (over-mentalizing) differentiates humans from most LLMs** — humans produce 36% NAD errors; Claude Sonnet produces 0%. Gemini is the exception: it over-mentalizes more than humans (42%), suggesting architecture-dependent variation in this error type.

### Attachment Classification (5 models)

| Model | Accuracy | Cohen's κ | Cramér's V |
|:---|:---:|:---:|:---:|
| Opus | 27/30 = 90% | .866 | .905 |
| Grok-4-20-reasoning | 27/30 = 90% | .867 | .890 |
| Gemini 3 Flash | 25/30 = 83% | .778 | .801 |
| Sonnet | 24/30 = 80% | .735 | .773 |
| GPT-5.4-mini | 16/30 = 53% | .372 | .491 |

Opus and Grok tie in overall accuracy (27/30, κ ≈ .87), though with different per-style error patterns. Gemini is third (κ = .78). GPT-5.4-mini performs poorly (κ = .37; chance would be ~25%).

### Rank-Score Correlations (median Pearson r, 11 continuous dimensions)

Note: 12 dimensions total = 11 continuous scales (below) + 1 categorical (attachment style, reported separately as κ).

| Model | Median r |
|:---|:---:|
| Opus | .852 |
| Grok | .833 |
| Sonnet | .819 |
| Gemini | .772 |
| GPT | .710 |

### Test-Retest Reliability

| Metric | Sonnet | Opus | GPT | Grok | Gemini |
|:---|:---:|:---:|:---:|:---:|:---:|
| z-score median r | .979 | .993 | .830 | .946 | .955 |
| TCTM total r | .691 | .992 | .203 | .530 | .900 |
| Style agreement | 29/30 | 30/30 | 26/30 | 30/30 | 27/30 |

Opus is near-deterministic across all tasks. Gemini is highly reliable (TCTM r = .90). Sonnet (r = .69) and Grok (r = .53) show moderate TCTM variance despite high questionnaire stability. GPT is unreliable on TCTM (r = .20).

### Inter-Model Consistency (z-scores, median r)

| | Sonnet | Opus | GPT | Grok | Gemini |
|:---|:---:|:---:|:---:|:---:|:---:|
| Sonnet | — | .950 | .807 | .931 | .930 |
| Opus | | — | .821 | .914 | .942 |
| GPT | | | — | .816 | .831 |
| Grok | | | | — | .932 |
| Gemini | | | | | — |

Within-Claude: r = .95. Gemini highly consistent with Sonnet, Opus, and Grok (~.93), less so with GPT (.83). GPT is the outlier across all pairs (.81-.83).

TCTM inter-model (same personas): Gemini×Opus r = .947 (highest pair). GPT×Grok r = .049 (zero). ICC(2,1) across 5 models = .282.

### Cross-Vendor Item Agreement (Ola case study)

Ola ("secure but non-mentalizing") has the lowest cross-model mean TCTM (11.0/22) and is consistently among the hardest personas for all 5 models (though GPT's hardest is Kamil at 13/22 and Grok's is Marek at 6/22). Cross-vendor error analysis on Ola shows **systematic item-level agreement on DOS errors** — 5/5 models make the same mistake (DOS) on items s07 and w22. Several specific items show stable cross-vendor difficulty, though overall inter-model TCTM agreement remains low (ICC = .28).

### Literature Consistency

| Model | Sign matches |
|:---|:---:|
| Gemini | 10/10 |
| Sonnet | 9/10 |
| Opus | 9/10 |
| GPT | 9/10 |
| Grok | 8/10 |

## Psychometric Instruments

The battery consists of four published Polish-language instruments plus one original vignette test:

1. **DBZ-R** (Doswiadczanie Bliskich Zwiazkov-Rewidowany) -- Polish adaptation of ECR-R (Lubiewska et al., 2016). 36 items measuring attachment anxiety and avoidance. Norms: Lubiewska (2016).

2. **MentS** (Mentalization Scale; Janczak, 2021). 28 items across three subscales: Self-oriented mentalization, Other-directed mentalization, and Motivation to mentalize. Norms: Janczak (2021).

3. **KPP** (Kwestionariusz Potrzeby Poznania; Matusz, 2011). 36 items measuring need for cognition (tendency toward effortful analytical thinking). Norms: Matusz (2011).

4. **TIPI-PL** (Ten-Item Personality Inventory, Polish adaptation; Sorokowska et al., 2014). 10 items yielding Big Five z-scores (Extraversion, Agreeableness, Conscientiousness, Emotional Stability, Openness). Norms: Sorokowska (2014).

5. **TCTM-22** (Test Cyfrowej Teorii Mentalizacji). 22 original forced-choice vignettes depicting text-message conversations in Polish. Each vignette presents a chat fragment and asks "What is this person really communicating?" with four response options. Distractor taxonomy follows the MASC error classification (Dziobek et al., 2006): DOS (under-mentalizing), NAD (over-mentalizing), BK (no mentalizing), plus one correct answer. TCTM-22 is an original instrument developed for this thesis — it is **not** an adaptation of MASC (which uses video), but borrows its error typology.

## Trait Transparency

Each biography encodes its target psychological profile through one of two strategies:

**Important: the YAML frontmatter (containing `expected_profile`, `persona_version`, `author_note`) was NEVER passed to the LLM.** The runner script (`run_synthetic.py`) strips the frontmatter and sends only the biography body as the system prompt. The LLM has no access to expected scores, attachment style labels, or any metadata — it sees only the narrative text.

- **Narrative** (21 personas): The biography body contains zero hits for trait-related keywords (e.g., "wysoka", "niska", "ekstrawersja", "mentalizacja"). The LLM must infer the entire profile from behavioral descriptions alone.

- **Explicit** (9 personas): The biography body contains 2–8 incidental uses of trait-related words (e.g., "Twoja mentalizacja jest niska", "Twoja sumienność jest niska"). These appear in the text the LLM sees — not in the YAML frontmatter. They are trait *descriptions within the narrative*, not metadata labels.

### Comparison: Does explicit labeling improve fidelity?

| Metric | Narrative (n=21) | Explicit (n=9) | Δ |
|:---|:---:|:---:|:---:|
| **Fidelity score** | **0.790** | 0.783 | −0.007 |
| Directional accuracy | 83.5% | 87.9% | +4.3pp |
| Style match | 81% (17/21) | 78% (7/9) | −3pp |
| Magnitude error | 0.67 SD | 0.76 SD | +0.09 |

**Result: Composite fidelity is virtually identical** (Δ = −0.007). Directional accuracy is +4.3pp higher for explicit personas (87.9% vs 83.5%), but with n=9 vs n=21 this difference is not testable. The near-zero composite difference is consistent with the interpretation that LLMs reconstruct personality primarily from *narrative content*, not from *trait labels*, though explicit labeling may provide a small additional signal for directional accuracy.

Explicit personas (sorted by regex hits): ania (8), ola (7), filip (7), natalia (6), tomek (5), anna-sim (4), jakub (4), marek (2), kamil (2). The `trait_transparency` and `trait_regex_hits` fields in `data/persona_manifest.json` allow filtering by group.

## Dataset Structure

```
github-repo/
  README.md                          # This file
  LICENSE                            # CC BY 4.0
  personas/                          # 30 biography files (Polish)
    piotr.md                         # YAML frontmatter + narrative body
    kasia.md
    ...
  data/
    validation_report.json           # Sensitivity analysis results (structured; "validation" is legacy naming)
    persona_scores.jsonl             # Per-persona raw scores (all instruments)
    persona_manifest.json            # Structured metadata for all 30 personas
  scripts/
    analyze_and_prepare.py           # Score computation (mirrors production code)
    validate_personas.py             # Validation pipeline (fidelity, accuracy)
    stats.py                         # Full statistical analysis (N=30)
    stats57.py                       # TCTM-57 extended analysis
  # Note: raw LLM output JSON files (300+ runs) are in ../out/ outside this repo.
  # The repo contains scored/aggregated data only. Full outputs available on request.
  results/
    validation_summary.md            # Human-readable validation report
    analysis_table.md                # Per-persona comparison tables
```

### Persona File Format

Each `.md` file in `personas/` has YAML frontmatter followed by a second-person Polish narrative:

```yaml
---
persona_id: piotr
expected_profile:
  attachment_style: fearful_avoidant
  dbz_anxiety: high
  dbz_avoidance: high
  ments_self: moderate_low
  ments_other: moderate_low
  ments_motivation: moderate
  kpp: high
  tipi_E: low
  tipi_A: low
  tipi_C: high
  tipi_ES: low
  tipi_O: moderate
author_note: |
  [Design rationale for this persona]
---

# Piotr -- biografia do zanurzenia

Nazywasz sie Piotr Walczak. Masz 24 lata. ...
```

All biographies are written in Polish. This is intentional -- four of the five instruments (DBZ-R, MentS, KPP, TIPI-PL) are normed for Polish populations; TCTM-22 is an original instrument without published norms, and the personas were designed for a Polish-language thesis on mentalization in text communication.

### Dimension Levels

Expected profile values use an ordinal scale mapped to approximate z-score ranges:

| Level | Approximate z | Rank |
|:---|:---:|:---:|
| very_low | -1.50 | -2 |
| low | -0.75 | -1 |
| low_moderate / moderate_low | -0.375 | -0.5 |
| moderate | 0.00 | 0 |
| moderate_high | +0.375 | +0.5 |
| high | +0.75 | +1 |
| very_high | +1.50 | +2 |

Note: `moderate_low` and `low_moderate` are treated as synonyms (rank = -0.5). Both forms appear in persona YAML files. The level `extreme` (rank = +2.5, approx z = +2.0) appears in two personas (Gabriela and Michal-k for TIPI-C).

---

## Persona Catalog

### Secure Attachment (7 personas)
Match rates: Sonnet: 7/7, Opus: 7/7, GPT: 5/7, Grok: 7/7, Gemini: 6/7

<details>
<summary><strong>Anna-sim</strong> ⚠️ `explicit`</summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.98 | Yes |
| DBZ Avoidance | moderate_low | -0.21 | Yes |
| MentS Self | high | +0.02 | Yes |
| MentS Other | moderate_high | +0.14 | Yes |
| MentS Motivation | moderate_high | -0.60 | No |
| KPP | moderate | -0.15 | Yes |
| TIPI E | moderate_high | -0.04 | Yes |
| TIPI A | low | -1.09 | Yes |
| TIPI C | moderate | +0.64 | No |
| TIPI ES | low | +1.05 | No |
| TIPI O | moderate_high | -0.89 | No |

**TCTM-22:** Son=19/22 | Opu=19/22 | GPT=15/22 | Grk=19/22 | Gem=21/22
**Attachment:** expected=secure, Son:Y Opu:Y GPT:Y Grk:Y Gem:Y

</details>

<details>
<summary><strong>Kasia</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.94 | Yes |
| DBZ Avoidance | low | -0.91 | Yes |
| MentS Self | high | +1.74 | Yes |
| MentS Other | high | +1.75 | Yes |
| MentS Motivation | high | +1.61 | Yes |
| KPP | moderate_high | +0.87 | Yes |
| TIPI E | high | -0.78 | No |
| TIPI A | high | +0.61 | Yes |
| TIPI C | moderate_high | +0.29 | Yes |
| TIPI ES | moderate_high | +0.41 | Yes |
| TIPI O | high | +0.87 | Yes |

**TCTM-22:** Son=19/22 | Opu=20/22 | GPT=15/22 | Grk=20/22 | Gem=21/22
**Attachment:** expected=secure, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Ola</strong> ⚠️ `explicit`</summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.26 | Yes |
| DBZ Avoidance | low | -1.26 | Yes |
| MentS Self | low_moderate | +0.19 | Yes |
| MentS Other | low | -0.21 | Yes |
| MentS Motivation | low | -1.70 | Yes |
| KPP | low_moderate | -2.20 | Yes |
| TIPI E | high | +0.69 | Yes |
| TIPI A | high | +0.61 | Yes |
| TIPI C | high | +0.64 | Yes |
| TIPI ES | high | +1.05 | Yes |
| TIPI O | low | -1.76 | Yes |

**TCTM-22:** Son=16/22 | Opu=9/22 | GPT=14/22 | Grk=7/22 | Gem=9/22
**Attachment:** expected=secure, Son:Y Opu:Y GPT:Y Grk:Y Gem:Y

</details>

<details>
<summary><strong>Kuba</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.12 | Yes |
| DBZ Avoidance | low | -0.91 | Yes |
| MentS Self | high | +0.88 | Yes |
| MentS Other | high | +0.86 | Yes |
| MentS Motivation | high | +1.61 | Yes |
| KPP | high | +1.61 | Yes |
| TIPI E | very_high | -0.04 | No |
| TIPI A | high | +0.19 | Yes |
| TIPI C | moderate | -0.06 | Yes |
| TIPI ES | high | +0.41 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**TCTM-22:** Son=20/22 | Opu=20/22 | GPT=18/22 | Grk=20/22 | Gem=20/22
**Attachment:** expected=secure, Son:Y Opu:Y GPT:Y Grk:Y Gem:Y

</details>

<details>
<summary><strong>Weronika</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.84 | Yes |
| DBZ Avoidance | low | -0.74 | Yes |
| MentS Self | moderate_high | +0.88 | Yes |
| MentS Other | high | +1.21 | Yes |
| MentS Motivation | moderate_high | +1.45 | Yes |
| KPP | moderate_high | +0.53 | Yes |
| TIPI E | moderate | -0.04 | Yes |
| TIPI A | very_high | +0.61 | Yes |
| TIPI C | very_high | +0.29 | Yes |
| TIPI ES | moderate_high | +0.41 | Yes |
| TIPI O | moderate | -0.01 | Yes |

**TCTM-22:** Son=20/22 | Opu=20/22 | GPT=16/22 | Grk=20/22 | Gem=19/22
**Attachment:** expected=secure, Son:Y Opu:Y GPT:Y Grk:Y Gem:Y

</details>

<details>
<summary><strong>Lukasz</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low_moderate | -0.61 | Yes |
| DBZ Avoidance | low | -0.74 | Yes |
| MentS Self | moderate | -0.67 | No |
| MentS Other | moderate_high | +0.32 | Yes |
| MentS Motivation | moderate_high | +1.13 | Yes |
| KPP | moderate_high | +0.36 | Yes |
| TIPI E | very_high | +0.69 | Yes |
| TIPI A | high | +0.19 | Yes |
| TIPI C | very_low | -2.16 | Yes |
| TIPI ES | moderate_low | +0.41 | No |
| TIPI O | very_high | +0.87 | Yes |

**TCTM-22:** Son=19/22 | Opu=20/22 | GPT=15/22 | Grk=18/22 | Gem=20/22
**Attachment:** expected=secure, Son:Y Opu:Y GPT:N Grk:Y Gem:N

</details>

<details>
<summary><strong>Sara</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | moderate_low | -1.12 | Yes |
| DBZ Avoidance | low | -1.08 | Yes |
| MentS Self | high | +0.88 | Yes |
| MentS Other | high | +1.57 | Yes |
| MentS Motivation | moderate | +1.13 | No |
| KPP | high | +0.36 | Yes |
| TIPI E | moderate_low | -0.04 | Yes |
| TIPI A | high | +0.61 | Yes |
| TIPI C | high | +0.29 | Yes |
| TIPI ES | very_low | -0.55 | Yes |
| TIPI O | high | +0.43 | Yes |

**TCTM-22:** Son=19/22 | Opu=20/22 | GPT=18/22 | Grk=18/22 | Gem=21/22
**Attachment:** expected=secure, Son:Y Opu:Y GPT:Y Grk:Y Gem:Y

</details>

### Anxious-Preoccupied Attachment (8 personas)
Match rates: Sonnet: 4/8, Opus: 5/8, GPT: 8/8, Grok: 6/8, Gemini: 5/8

<details>
<summary><strong>Ania</strong> ⚠️ `explicit`</summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +2.14 | Yes |
| DBZ Avoidance | low | -0.74 | Yes |
| MentS Self | moderate_high | -0.33 | No |
| MentS Other | moderate | +0.68 | No |
| MentS Motivation | very_high | +1.61 | Yes |
| KPP | moderate_high | +0.19 | Yes |
| TIPI E | moderate_high | -0.04 | Yes |
| TIPI A | high | +0.61 | Yes |
| TIPI C | moderate | -0.76 | No |
| TIPI ES | very_low | -1.83 | Yes |
| TIPI O | high | +0.87 | Yes |

**TCTM-22:** Son=20/22 | Opu=20/22 | GPT=19/22 | Grk=17/22 | Gem=19/22
**Attachment:** expected=anxious_preoccupied, Son:Y Opu:Y GPT:Y Grk:Y Gem:Y

</details>

<details>
<summary><strong>Natalia</strong> ⚠️ `explicit`</summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +2.23 | Yes |
| DBZ Avoidance | low | -0.91 | Yes |
| MentS Self | low | -1.88 | Yes |
| MentS Other | low | -1.64 | Yes |
| MentS Motivation | low_moderate | -1.70 | Yes |
| KPP | low | -3.56 | Yes |
| TIPI E | moderate_high | -0.04 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | low | -1.81 | Yes |
| TIPI ES | very_low | -1.83 | Yes |
| TIPI O | low_moderate | -1.32 | Yes |

**TCTM-22:** Son=20/22 | Opu=19/22 | GPT=19/22 | Grk=21/22 | Gem=20/22
**Attachment:** expected=anxious_preoccupied, Son:Y Opu:Y GPT:Y Grk:Y Gem:Y

</details>

<details>
<summary><strong>Pawel</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | +1.36 | Yes |
| DBZ Avoidance | moderate_low | +0.77 | No |
| MentS Self | low | -1.71 | Yes |
| MentS Other | low_moderate | -1.29 | Yes |
| MentS Motivation | low | -1.54 | Yes |
| KPP | low | -1.57 | Yes |
| TIPI E | moderate_high | -0.41 | No |
| TIPI A | low_moderate | -0.24 | Yes |
| TIPI C | low | -0.41 | Yes |
| TIPI ES | very_low | -0.55 | Yes |
| TIPI O | low | -1.32 | Yes |

**TCTM-22:** Son=19/22 | Opu=19/22 | GPT=16/22 | Grk=19/22 | Gem=20/22
**Attachment:** expected=anxious_preoccupied, Son:Y Opu:N GPT:Y Grk:Y Gem:Y

</details>

<details>
<summary><strong>Jola</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +1.82 | Yes |
| DBZ Avoidance | low | +0.36 | No |
| MentS Self | high | -0.33 | No |
| MentS Other | very_high | +1.57 | Yes |
| MentS Motivation | very_high | +1.45 | Yes |
| KPP | moderate_high | +0.41 | Yes |
| TIPI E | moderate_high | -0.78 | No |
| TIPI A | moderate_high | +0.19 | Yes |
| TIPI C | moderate | +0.29 | Yes |
| TIPI ES | very_low | -1.51 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**TCTM-22:** Son=20/22 | Opu=20/22 | GPT=19/22 | Grk=20/22 | Gem=20/22
**Attachment:** expected=anxious_preoccupied, Son:Y Opu:Y GPT:Y Grk:Y Gem:Y

</details>

<details>
<summary><strong>Bartek</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +0.76 | Yes |
| DBZ Avoidance | moderate | +1.87 | No |
| MentS Self | very_high | -0.50 | No |
| MentS Other | moderate_high | +0.50 | Yes |
| MentS Motivation | very_high | +1.45 | Yes |
| KPP | moderate_high | +0.53 | Yes |
| TIPI E | low | -2.25 | Yes |
| TIPI A | moderate_high | -0.24 | Yes |
| TIPI C | moderate | -0.06 | Yes |
| TIPI ES | very_low | -1.51 | Yes |
| TIPI O | high | +0.87 | Yes |

**TCTM-22:** Son=21/22 | Opu=19/22 | GPT=17/22 | Grk=21/22 | Gem=19/22
**Attachment:** expected=anxious_preoccupied, Son:N Opu:N GPT:Y Grk:N Gem:N

</details>

<details>
<summary><strong>Klaudia</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +0.30 | Yes |
| DBZ Avoidance | very_low | +0.36 | No |
| MentS Self | low | -0.33 | Yes |
| MentS Other | very_high | +1.21 | Yes |
| MentS Motivation | very_high | +1.13 | Yes |
| KPP | moderate | -0.44 | No |
| TIPI E | high | -0.41 | No |
| TIPI A | very_high | +0.61 | Yes |
| TIPI C | moderate_high | +0.29 | Yes |
| TIPI ES | low | -1.19 | Yes |
| TIPI O | moderate | -0.45 | No |

**TCTM-22:** Son=18/22 | Opu=20/22 | GPT=16/22 | Grk=22/22 | Gem=21/22
**Attachment:** expected=anxious_preoccupied, Son:N Opu:Y GPT:Y Grk:Y Gem:Y

</details>

<details>
<summary><strong>Gabriela</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | -0.06 | No |
| DBZ Avoidance | moderate_low | +0.25 | Yes |
| MentS Self | moderate_high | -0.50 | No |
| MentS Other | high | +0.50 | Yes |
| MentS Motivation | high | +1.29 | Yes |
| KPP | high | +1.15 | Yes |
| TIPI E | moderate | -1.15 | No |
| TIPI A | very_high | +0.19 | Yes |
| TIPI C | extreme | +1.34 | No |
| TIPI ES | low_moderate | -1.19 | Yes |
| TIPI O | moderate_high | -0.01 | Yes |

**TCTM-22:** Son=20/22 | Opu=20/22 | GPT=17/22 | Grk=20/22 | Gem=21/22
**Attachment:** expected=anxious_preoccupied, Son:N Opu:Y GPT:Y Grk:Y Gem:N

</details>

<details>
<summary><strong>Michal-k</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +1.13 | Yes |
| DBZ Avoidance | moderate | +1.75 | No |
| MentS Self | very_high | -0.50 | No |
| MentS Other | moderate_high | +0.32 | Yes |
| MentS Motivation | very_high | +1.13 | Yes |
| KPP | very_high | +0.81 | Yes |
| TIPI E | low | -1.88 | Yes |
| TIPI A | moderate_high | +0.19 | Yes |
| TIPI C | extreme | +1.34 | No |
| TIPI ES | very_low | -1.51 | Yes |
| TIPI O | moderate_high | -1.32 | No |

**TCTM-22:** Son=19/22 | Opu=20/22 | GPT=16/22 | Grk=20/22 | Gem=21/22
**Attachment:** expected=anxious_preoccupied, Son:N Opu:N GPT:Y Grk:N Gem:N

</details>

### Dismissive-Avoidant Attachment (7 personas)
Match rates: Sonnet: 7/7, Opus: 7/7, GPT: 1/7, Grok: 7/7, Gemini: 7/7

<details>
<summary><strong>Jakub</strong> ⚠️ `explicit`</summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.12 | Yes |
| DBZ Avoidance | high | +2.56 | Yes |
| MentS Self | moderate_high | -0.15 | Yes |
| MentS Other | moderate_low | -0.75 | Yes |
| MentS Motivation | low | -1.39 | Yes |
| KPP | high | +0.53 | Yes |
| TIPI E | low | -1.51 | Yes |
| TIPI A | low | -1.09 | Yes |
| TIPI C | high | +0.99 | Yes |
| TIPI ES | high | +1.05 | Yes |
| TIPI O | moderate | -0.89 | No |

**TCTM-22:** Son=20/22 | Opu=19/22 | GPT=18/22 | Grk=17/22 | Gem=20/22
**Attachment:** expected=dismissive_avoidant, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Tomek</strong> ⚠️ `explicit`</summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.98 | Yes |
| DBZ Avoidance | moderate_high | +2.79 | Yes |
| MentS Self | low_moderate | -1.53 | Yes |
| MentS Other | high | +1.04 | Yes |
| MentS Motivation | moderate | +0.35 | No |
| KPP | moderate_high | -0.10 | Yes |
| TIPI E | low_moderate | -1.88 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | moderate_high | +0.29 | Yes |
| TIPI ES | moderate_high | +0.73 | Yes |
| TIPI O | moderate_high | -0.01 | Yes |

**TCTM-22:** Son=21/22 | Opu=19/22 | GPT=16/22 | Grk=20/22 | Gem=20/22
**Attachment:** expected=dismissive_avoidant, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Magda</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.61 | Yes |
| DBZ Avoidance | high | +2.50 | Yes |
| MentS Self | moderate | -0.50 | No |
| MentS Other | moderate_high | +0.14 | Yes |
| MentS Motivation | moderate | +0.50 | No |
| KPP | high | +1.38 | Yes |
| TIPI E | moderate_high | -1.15 | No |
| TIPI A | low | -0.67 | Yes |
| TIPI C | very_high | +1.34 | Yes |
| TIPI ES | high | +0.41 | Yes |
| TIPI O | moderate_high | -0.01 | Yes |

**TCTM-22:** Son=20/22 | Opu=19/22 | GPT=18/22 | Grk=19/22 | Gem=20/22
**Attachment:** expected=dismissive_avoidant, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Adrian</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_low | -1.03 | Yes |
| DBZ Avoidance | very_high | +2.16 | Yes |
| MentS Self | very_low | -1.36 | Yes |
| MentS Other | low | -0.93 | Yes |
| MentS Motivation | very_low | -0.91 | Yes |
| KPP | low_moderate | +1.04 | No |
| TIPI E | very_low | -2.62 | Yes |
| TIPI A | low_moderate | -0.24 | Yes |
| TIPI C | very_high | +0.64 | Yes |
| TIPI ES | high | +1.05 | Yes |
| TIPI O | low | -0.89 | Yes |

**TCTM-22:** Son=20/22 | Opu=19/22 | GPT=16/22 | Grk=18/22 | Gem=20/22
**Attachment:** expected=dismissive_avoidant, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Hubert</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.07 | Yes |
| DBZ Avoidance | high | +1.98 | Yes |
| MentS Self | very_low | -1.71 | Yes |
| MentS Other | low | -1.11 | Yes |
| MentS Motivation | low | -0.44 | Yes |
| KPP | high | +1.44 | Yes |
| TIPI E | very_low | -2.62 | Yes |
| TIPI A | low_moderate | -0.24 | Yes |
| TIPI C | very_high | +0.99 | Yes |
| TIPI ES | moderate | +1.05 | No |
| TIPI O | high | -0.01 | No |

**TCTM-22:** Son=20/22 | Opu=19/22 | GPT=17/22 | Grk=7/22 | Gem=20/22
**Attachment:** expected=dismissive_avoidant, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Dominika</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.61 | Yes |
| DBZ Avoidance | moderate_high | +2.39 | Yes |
| MentS Self | moderate | -1.02 | No |
| MentS Other | very_high | +1.04 | Yes |
| MentS Motivation | moderate | +0.50 | No |
| KPP | moderate_high | +1.44 | Yes |
| TIPI E | very_high | -0.04 | No |
| TIPI A | very_low | -0.67 | Yes |
| TIPI C | very_high | +0.99 | Yes |
| TIPI ES | high | +0.41 | Yes |
| TIPI O | moderate | +0.87 | No |

**TCTM-22:** Son=20/22 | Opu=20/22 | GPT=18/22 | Grk=20/22 | Gem=20/22
**Attachment:** expected=dismissive_avoidant, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Agata</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_low | -1.21 | Yes |
| DBZ Avoidance | very_high | +2.74 | Yes |
| MentS Self | moderate | +0.71 | No |
| MentS Other | low | +0.14 | No |
| MentS Motivation | low | +0.35 | No |
| KPP | very_high | +1.44 | Yes |
| TIPI E | very_low | -2.62 | Yes |
| TIPI A | low | -0.24 | Yes |
| TIPI C | high | +0.99 | Yes |
| TIPI ES | high | +0.73 | Yes |
| TIPI O | very_high | +0.43 | Yes |

**TCTM-22:** Son=20/22 | Opu=19/22 | GPT=18/22 | Grk=18/22 | Gem=20/22
**Attachment:** expected=dismissive_avoidant, Son:Y Opu:Y GPT:Y Grk:Y Gem:Y

</details>

### Fearful-Avoidant Attachment (8 personas)
Match rates: Sonnet: 6/8, Opus: 8/8, GPT: 2/8, Grok: 7/8, Gemini: 7/8

<details>
<summary><strong>Michal-sim</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | moderate_high | +0.99 | Yes |
| DBZ Avoidance | moderate_high | +2.79 | Yes |
| MentS Self | moderate | -1.71 | No |
| MentS Other | moderate | -0.57 | No |
| MentS Motivation | moderate_high | -0.13 | Yes |
| KPP | moderate_high | +0.93 | Yes |
| TIPI E | moderate | -1.88 | No |
| TIPI A | moderate_high | +0.19 | Yes |
| TIPI C | moderate | +0.29 | Yes |
| TIPI ES | low_moderate | -0.55 | Yes |
| TIPI O | moderate_high | -0.01 | Yes |

**TCTM-22:** Son=19/22 | Opu=19/22 | GPT=16/22 | Grk=21/22 | Gem=19/22
**Attachment:** expected=fearful_avoidant, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Piotr</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | +0.72 | Yes |
| DBZ Avoidance | high | +2.68 | Yes |
| MentS Self | moderate_low | -2.22 | Yes |
| MentS Other | moderate_low | -1.64 | Yes |
| MentS Motivation | moderate | -0.76 | No |
| KPP | high | -0.04 | No |
| TIPI E | low | -2.62 | Yes |
| TIPI A | low | -0.24 | Yes |
| TIPI C | high | -0.06 | No |
| TIPI ES | low | -1.19 | Yes |
| TIPI O | moderate | -0.45 | No |

**TCTM-22:** Son=20/22 | Opu=19/22 | GPT=16/22 | Grk=19/22 | Gem=19/22
**Attachment:** expected=fearful_avoidant, Son:Y Opu:Y GPT:Y Grk:Y Gem:Y

</details>

<details>
<summary><strong>Marek</strong> ⚠️ `explicit`</summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | -1.12 | No |
| DBZ Avoidance | high | +2.74 | Yes |
| MentS Self | low | -1.88 | Yes |
| MentS Other | low | -3.07 | Yes |
| MentS Motivation | low | -2.49 | Yes |
| KPP | low_moderate | -2.60 | Yes |
| TIPI E | low | -2.62 | Yes |
| TIPI A | moderate | -0.67 | No |
| TIPI C | low_moderate | -0.06 | Yes |
| TIPI ES | very_low | -0.23 | Yes |
| TIPI O | low | -2.20 | Yes |

**TCTM-22:** Son=19/22 | Opu=19/22 | GPT=18/22 | Grk=6/22 | Gem=20/22
**Attachment:** expected=fearful_avoidant, Son:N Opu:Y GPT:Y Grk:N Gem:N

</details>

<details>
<summary><strong>Filip</strong> ⚠️ `explicit`</summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | +1.45 | Yes |
| DBZ Avoidance | moderate_high | +2.79 | Yes |
| MentS Self | very_high | -1.02 | No |
| MentS Other | high | +0.32 | Yes |
| MentS Motivation | very_high | +1.29 | Yes |
| KPP | very_high | +1.15 | Yes |
| TIPI E | low_moderate | -1.88 | Yes |
| TIPI A | moderate_high | -0.67 | No |
| TIPI C | moderate | -1.11 | No |
| TIPI ES | low | -1.51 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**TCTM-22:** Son=20/22 | Opu=19/22 | GPT=18/22 | Grk=21/22 | Gem=19/22
**Attachment:** expected=fearful_avoidant, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Ewa</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +0.95 | Yes |
| DBZ Avoidance | very_high | +2.27 | Yes |
| MentS Self | high | -0.33 | No |
| MentS Other | moderate_high | +1.39 | Yes |
| MentS Motivation | very_high | +1.29 | Yes |
| KPP | very_high | +1.49 | Yes |
| TIPI E | low | -2.25 | Yes |
| TIPI A | moderate_low | -0.24 | Yes |
| TIPI C | high | -0.06 | No |
| TIPI ES | very_low | -1.19 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**TCTM-22:** Son=20/22 | Opu=19/22 | GPT=15/22 | Grk=21/22 | Gem=19/22
**Attachment:** expected=fearful_avoidant, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Zuzia</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | +0.85 | Yes |
| DBZ Avoidance | moderate_high | +2.16 | Yes |
| MentS Self | very_high | -0.50 | No |
| MentS Other | high | +1.21 | Yes |
| MentS Motivation | very_high | +1.13 | Yes |
| KPP | high | +0.70 | Yes |
| TIPI E | moderate | -1.51 | No |
| TIPI A | moderate_high | -0.24 | Yes |
| TIPI C | moderate_high | -0.76 | No |
| TIPI ES | low | -1.19 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**TCTM-22:** Son=20/22 | Opu=20/22 | GPT=19/22 | Grk=22/22 | Gem=21/22
**Attachment:** expected=fearful_avoidant, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Radek</strong></summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +2.09 | Yes |
| DBZ Avoidance | moderate_high | +2.16 | Yes |
| MentS Self | very_low | -2.22 | Yes |
| MentS Other | moderate_high | +0.68 | Yes |
| MentS Motivation | moderate | -0.28 | Yes |
| KPP | low | -2.43 | Yes |
| TIPI E | high | -0.41 | No |
| TIPI A | moderate_high | -0.67 | No |
| TIPI C | very_low | -1.81 | Yes |
| TIPI ES | very_low | -1.51 | Yes |
| TIPI O | high | -0.01 | No |

**TCTM-22:** Son=20/22 | Opu=20/22 | GPT=18/22 | Grk=20/22 | Gem=20/22
**Attachment:** expected=fearful_avoidant, Son:Y Opu:Y GPT:N Grk:Y Gem:Y

</details>

<details>
<summary><strong>Kamil</strong> ⚠️ `explicit`</summary>

| Dimension | Expected | Sonnet z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | -0.29 | No |
| DBZ Avoidance | high | +1.98 | Yes |
| MentS Self | moderate | -0.67 | No |
| MentS Other | moderate | +0.14 | Yes |
| MentS Motivation | low | +0.66 | No |
| KPP | low_moderate | +0.41 | No |
| TIPI E | low | -2.62 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | high | +0.29 | Yes |
| TIPI ES | very_low | -0.55 | Yes |
| TIPI O | moderate_low | -0.45 | Yes |

**TCTM-22:** Son=19/22 | Opu=19/22 | GPT=13/22 | Grk=21/22 | Gem=20/22
**Attachment:** expected=fearful_avoidant, Son:N Opu:Y GPT:N Grk:Y Gem:Y

</details>

## Models Used

All 30 personas were processed by 5 models from 4 vendors, each run twice (test + retest):

| Model | Vendor | Platform | Runs |
|:---|:---|:---|:---:|
| Claude Sonnet 4.6 | Anthropic | AWS Bedrock | 30 + 30 retest |
| Claude Opus 4.6 | Anthropic | AWS Bedrock | 30 + 30 retest |
| GPT-5.4-mini | OpenAI | Azure OpenAI | 30 + 30 retest |
| Grok-4-20-reasoning | xAI | Azure AI Foundry | 30 + 30 retest |
| Gemini 3 Flash | Google | Gemini API | 30 + 30 retest |
| **Total LLM** | | | **300** (5 × 30 × 2) |
| Human respondents | — | — | **7** |

All models used default sampling parameters. The scoring pipeline (`scripts/analyze_and_prepare.py`) uses published Polish norms for DBZ-R, MentS, KPP, and TIPI-PL. TCTM-22 is scored against author-defined answer keys (no published norms).

**Key cross-vendor findings:**
- Questionnaire z-scores: high agreement across all 5 models (median r = .81–.95)
- TCTM-22: low cross-vendor agreement (ICC = .28); models disagree on which vignettes are hard
- Error profiles differ by architecture: Claude Sonnet → almost exclusively DOS (96%); Claude Opus → DOS-dominant (85%) with some NAD (8%) and BK (7%); Gemini → closest to human pilot error profile (DOS 24%, NAD 42%, BK 34%); Grok → mixed with notable NAD (18%); GPT → DOS-dominant with elevated BK (23%)

## Scoring Norms

Z-scores and classifications for the four published instruments use the following Polish norms (TCTM-22 has no published norms):

- **DBZ-R:** Lubiewska, K. (2016). *Doswiadczanie Bliskich Zwiazkov-Rewidowany*. Wydawnictwo Uniwersytetu Kazimierza Wielkiego.
- **MentS:** Janczak, M. O. (2021). Polish adaptation and validation of the Mentalization Scale (MentS). *Psychiatria Polska*, 55(6), 1257-1274.
- **KPP:** Matusz, P. J., Traczyk, J., & Gąsiorowska, A. (2011). Kwestionariusz potrzeby poznania — konstrukcja i weryfikacja empiryczna. *Psychologia Społeczna*, 6(2), 113-128.
- **TIPI-PL:** Sorokowska, A. et al. (2014). *TIPI-PL -- polska adaptacja Ten Item Personality Inventory (TIPI)*. Roczniki Psychologiczne, 17(2), 353-366.
- **TCTM-22:** Original instrument by Wiencek (2026). Error typology based on: Dziobek, I. et al. (2006). *Introducing MASC: A Movie for the Assessment of Social Cognition*. Journal of Autism and Developmental Disorders, 36(5), 623-636.

## Fidelity Score

The composite fidelity score (0.0-1.0) weights:

1. **Attachment style match** (binary, 40% weight) -- correct 4-category classification
2. **Directional accuracy** (proportion, 40% weight) -- does the observed z-score go in the expected direction? For directional levels (`high`, `very_high`, `extreme` → z > 0; `low`, `very_low` → z < 0), any z with the correct sign counts as a match regardless of magnitude. For near-center levels (`moderate_low`/`low_moderate`, `moderate_high`), a z within |z| < 0.3 counts as a match; beyond that, sign must match the level's direction. For `moderate`, only |z| < 0.3 counts as a match.
3. **Literature consistency** (proportion, 20% weight) -- do 10 theoretically-expected cross-scale correlations hold?

Mean fidelity across all 30 personas (Sonnet data): **0.788**.

## Limitations

1. **Sensitivity, not validity.** This is a sensitivity study — it shows instruments react to known personality variation in LLM responses, not that they measure those constructs validly in humans.

2. **TCTM-22 ceiling effect (Claude and Gemini):** Claude and Gemini score near-ceiling (M ≈ 19.4–19.6/22). GPT and Grok show more variance: GPT M=16.8, Grok range 6–22. Ola consistently scores low across all 5 vendors (7–16/22), confirmed by retest as systematic.

3. **GPT-5.4-mini is unreliable on TCTM:** Test-retest r = .20 (TCTM), with individual personas shifting by up to ±5 points. GPT also drops items (20% of runs returned 20-21 instead of 22 vignette answers; missing items were scored as incorrect). Impact: GPT M=16.8/22 with missing-as-incorrect vs M=16.9/22 for complete runs only (+0.1, negligible). GPT questionnaire data is moderately reliable (z-score r = .83) but TCTM data is not.

4. **Cross-vendor TCTM agreement is low:** ICC(2,1) = .28 across 5 models. Models disagree on which vignettes are hard for which personas. GPT × Grok TCTM correlation is r = .05 (effectively zero).

5. **Shared authorship:** The same person wrote the personas and designed TCTM-22, creating potential circularity in two ways: (a) biographical writing style may align with questionnaire keying — partially addressed by the trait transparency analysis (narrative ≈ explicit fidelity); (b) TCTM-22 answer keys were authored by the same person who wrote the personas — this circularity is not addressed and would require independent answer key validation.

6. **Human N = 7:** The human pilot provides exploratory observations only. In the pilot sample, NAD errors were more frequent among humans than most LLMs, but the sample is too small for statistical inference.

7. **Polish-only:** Biographies and instruments are in Polish; generalizability to other languages is unknown.

8. **Gemini NAD > human NAD (42% vs 36%):** Gemini 3 Flash over-mentalizes more than humans. This may reflect the model's training on conversational data or a tendency to "read between the lines" more aggressively than warranted.

## How to Cite

```bibtex
@mastersthesis{wiencek2026tctm,
  author  = {Wiencek, Micha{\l}},
  title   = {Kompetencja mentalizacji w polskiej komunikacji tekstowej: pilota{\.z}owa walidacja {TCTM-22}},
  school  = {Uniwersytet Komisji Edukacji Narodowej w Krakowie},
  year    = {2026},
  type    = {Praca magisterska},
  note    = {Synthetic persona sensitivity study (N=30, 5 models, 4 vendors)}
}
% Note: the thesis title uses "walidacja" (validation) as the official registered title;
% the analyses in this repository are framed as a sensitivity study, not classical validation.
```

If citing the dataset specifically:

```bibtex
@dataset{wiencek2026tctm_synthetic,
  author    = {Wiencek, Micha{\l}},
  title     = {{TCTM-22} Synthetic Persona Sensitivity Dataset ({N}=30)},
  year      = {2026},
  publisher = {GitHub},
  note      = {30 synthetic biographies, 5 LLM models (4 vendors), 300 runs + 7 human respondents}
}
```

## License

This dataset is released under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).

You are free to share and adapt the material for any purpose, including commercial, provided you give appropriate credit.

## Acknowledgments

This work was conducted as part of an MA thesis at UKEN Krakow. All 30 biographies were authored by Michal Wiencek using Claude Opus 4.6 as a writing assistant — the author specified the psychological profile, narrative constraints, and stylistic requirements for each persona; the model generated drafts which were reviewed and edited by the author. The psychometric scoring pipeline was also developed by Michal Wiencek. LLM inference was performed using Claude Sonnet/Opus 4.6 (Anthropic, AWS Bedrock), GPT-5.4-mini (OpenAI, Azure), Grok-4-20-reasoning (xAI, Azure AI Foundry), and Gemini 3 Flash (Google). Claude (Anthropic) assisted in analysis and manuscript preparation.

**AI Disclosure.** Claude (Anthropic) was used to assist in data analysis, statistical computation, chart generation, and manuscript preparation. The author takes full responsibility for the content.
