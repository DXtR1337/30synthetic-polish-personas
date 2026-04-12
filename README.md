# TCTM-22 Synthetic Persona Validation Dataset (N=30)

**A benchmark dataset of 30 richly-specified fictional biographies with ground-truth psychological profiles, designed to validate AI-driven psychometric scoring in a Polish-language mentalization assessment.**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

---

## Abstract

This repository contains the complete materials for a synthetic persona validation experiment conducted as part of an MA thesis at the Uniwersytet Komisji Edukacji Narodowej (UKEN) in Krakow, Poland. The thesis investigates mentalization in text-based communication among young Polish adults.

Thirty fictional characters ("personas") were authored with predetermined psychological profiles spanning four attachment styles, three mentalization subscales, personal competence, and Big Five personality traits (12 dimensions total). Each persona was written as an immersive second-person biography in Polish, averaging 1,554-2,914 words, providing enough behavioral and relational detail for a large language model (Claude Opus 4.6 / Claude Sonnet 4.6) to complete a battery of five validated psychometric instruments as if it were the persona.

The scored responses were then compared against the ground-truth profiles embedded in each biography. This dataset provides the full pipeline: biographies, expected profiles, observed scores, and statistical validation.

## Key Results

| Metric | Value |
|:---|:---|
| Attachment style match (4 categories) | **24/30 = 80.0%** |
| Cohen's kappa (attachment) | **0.735** (95% CI: 0.545-0.925, "substantial") |
| Mean directional accuracy (11 dimensions) | **84.8%** |
| Mean literature consistency (10 construct pairs) | **64.3%** |
| Mean magnitude error | **0.70 SD** |
| Mean fidelity score (composite) | **0.788** |
| TCTM-22 mean correct | **19.4/22 = 88.2%** |
| Dimension-level correlations | **11/11 significant at p < 0.001** |
| Literature construct pairs replicated | **10/10 expected directions** |

### Attachment Style Confusion Matrix

| | Predicted: Secure | Predicted: Anxious | Predicted: Dismissive | Predicted: Fearful |
|:---|:---:|:---:|:---:|:---:|
| **Expected: Secure** (n=7) | **7** | 0 | 0 | 0 |
| **Expected: Anxious** (n=8) | 2 | **4** | 1 | 1 |
| **Expected: Dismissive** (n=7) | 0 | 0 | **7** | 0 |
| **Expected: Fearful** (n=8) | 0 | 0 | 2 | **6** |

Secure and dismissive-avoidant styles achieve perfect classification (100%). Anxious-preoccupied is the most difficult category (50%), with misclassified cases typically showing attenuated anxiety scores.

### Per-Dimension Directional Accuracy

| Dimension | Accuracy | Pearson r | p-value |
|:---|:---:|:---:|:---:|
| KPP (personal competence) | 97% | 0.756 | < 0.001 |
| DBZ Anxiety (attachment) | 93% | 0.829 | < 0.001 |
| TIPI Agreeableness | 93% | 0.744 | < 0.001 |
| TIPI Conscientiousness | 93% | 0.748 | < 0.001 |
| MentS Other-directed | 90% | 0.793 | < 0.001 |
| TIPI Emotional Stability | 90% | 0.806 | < 0.001 |
| MentS Motivation | 83% | 0.749 | < 0.001 |
| DBZ Avoidance (attachment) | 80% | 0.838 | < 0.001 |
| TIPI Openness | 73% | 0.561 | 0.001 |
| TIPI Extraversion | 70% | 0.651 | < 0.001 |
| MentS Self-oriented | 70% | 0.584 | < 0.001 |

## Psychometric Instruments

The battery consists of five validated Polish-language instruments:

1. **DBZ-R** (Doswiadczanie Bliskich Zwiazkov-Rewidowany) -- Polish adaptation of ECR-R (Lubiewska et al., 2016). 36 items measuring attachment anxiety and avoidance. Norms: Lubiewska (2016).

2. **MentS** (Mentalization Scale; Janczak, 2021). 28 items across three subscales: Self-oriented mentalization, Other-directed mentalization, and Motivation to mentalize. Norms: Janczak (2021).

3. **KPP** (Kwestionariusz Kompetencji Personalnych; Matusz, 2011). 36 items measuring personal/social competence. Norms: Matusz (2011).

4. **TIPI-PL** (Ten-Item Personality Inventory, Polish adaptation; Sorokowska et al., 2014). 10 items yielding Big Five z-scores (Extraversion, Agreeableness, Conscientiousness, Emotional Stability, Openness). Norms: Sorokowska (2014).

5. **TCTM-22** (Test Cyfrowej Teorii Mentalizacji). 22 original forced-choice vignettes depicting text-message conversations in Polish. Each vignette presents a chat fragment and asks "What is this person really communicating?" with four response options. Distractor taxonomy follows the MASC error classification (Dziobek et al., 2006): DOS (under-mentalizing), NAD (over-mentalizing), BK (no mentalizing), plus one correct answer. TCTM-22 is an original instrument developed for this thesis — it is **not** an adaptation of MASC (which uses video), but borrows its error typology.

## Trait Transparency

Each biography encodes its target psychological profile through one of two strategies:

- **Narrative** (21 personas): Traits are conveyed exclusively through behavioral descriptions, relationship patterns, emotional reactions, and life history -- without any psychological terminology or labels. The LLM must infer the construct from behavior.

- **Explicit** (9 personas): Some biographies include limited psychological terminology in the author's notes section (YAML frontmatter), though the biography body itself still relies on behavioral encoding.

This design allows future analysis of whether trait inference accuracy varies with transparency level.

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
    validation_report.json           # Full validation results (structured)
    persona_scores.jsonl             # Per-persona raw scores (all instruments)
    persona_manifest.json            # Structured metadata for all 30 personas
  scripts/
    analyze_and_prepare.py           # Score computation (mirrors production code)
    validate_personas.py             # Validation pipeline (fidelity, accuracy)
    stats.py                         # Full statistical analysis (N=30)
    stats57.py                       # TCTM-57 extended analysis
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

All biographies are written in Polish. This is intentional -- the psychometric battery is normed for Polish populations, and the personas were designed for a Polish-language thesis on mentalization in text communication.

### Dimension Levels

Expected profile values use an ordinal scale mapped to approximate z-score ranges:

| Level | Approximate z | Rank |
|:---|:---:|:---:|
| very_low | -1.50 | -2 |
| low | -0.75 | -1 |
| low_moderate | -0.375 | -0.5 |
| moderate | 0.00 | 0 |
| moderate_high | +0.375 | +0.5 |
| high | +0.75 | +1 |
| very_high | +1.50 | +2 |

---

## Persona Catalog

### Secure Attachment (7 personas, 100% match rate)

<details>
<summary><strong>Kasia</strong> -- Katarzyna Wilczynska, 26F, physiotherapist, Wroclaw</summary>

Warm, emotionally literate woman raised in a supportive family in Kalisz. Works in a private physiotherapy clinic where patients describe her as "the first physiotherapist who truly listens." Lives with her boyfriend Jarek and a cat named Bobas. High mentalization across all subscales, strong personal competence.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.03 | Yes |
| DBZ Avoidance | low | -1.37 | Yes |
| MentS Self | high | +1.91 | Yes |
| MentS Other | high | +1.57 | Yes |
| MentS Motivation | high | +1.29 | Yes |
| KPP | moderate_high | +0.36 | Yes |
| TIPI E | high | -0.41 | No |
| TIPI A | high | +0.61 | Yes |
| TIPI C | moderate_high | +0.64 | Yes |
| TIPI ES | moderate_high | +0.41 | Yes |
| TIPI O | high | -0.01 | No |

**Fidelity:** 0.904 | **Dir. Accuracy:** 91% | **Lit. Consistency:** 70% | **TCTM:** 20/22

</details>

<details>
<summary><strong>Ola</strong> -- Aleksandra Zielinska, 28F, kindergarten teacher, Rzeszow</summary>

Happily married kindergarten teacher with a simple, content life. Grew up in a "normally good" family with no trauma. Married to Grzegorz for two years, together for six. Has a cat named Fistasz. Explicitly rejects the idea of needing therapy. Low mentalization scores reflect genuine psychological simplicity rather than avoidance.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.03 | Yes |
| DBZ Avoidance | low | -0.74 | Yes |
| MentS Self | low_moderate | +0.19 | Yes |
| MentS Other | low | -0.21 | Yes |
| MentS Motivation | low | -1.39 | Yes |
| KPP | low_moderate | -2.26 | Yes |
| TIPI E | moderate_high | +0.32 | Yes |
| TIPI A | high | +0.61 | Yes |
| TIPI C | moderate_high | +0.64 | Yes |
| TIPI ES | high | +1.05 | Yes |
| TIPI O | low | -1.76 | Yes |

**Fidelity:** 0.920 | **Dir. Accuracy:** 100% | **Lit. Consistency:** 60% | **TCTM:** 17/22

</details>

<details>
<summary><strong>Kuba</strong> -- Jakub Okonski, 22M, philosophy & cognitive science student, Krakow</summary>

Intellectually curious MA student at Jagiellonian University writing about theory of mind in higher primates. Lives with two roommates, in a loving relationship with Marta. High mentalization and openness, warm family background. His professor told him "you write like someone who wants to understand, not someone who wants to show off."

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.84 | Yes |
| DBZ Avoidance | low | -0.74 | Yes |
| MentS Self | high | +0.53 | Yes |
| MentS Other | high | +0.68 | Yes |
| MentS Motivation | high | +1.61 | Yes |
| KPP | high | +1.61 | Yes |
| TIPI E | moderate_high | -0.41 | No |
| TIPI A | moderate | +0.19 | Yes |
| TIPI C | moderate | -0.06 | Yes |
| TIPI ES | moderate_high | +0.41 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**Fidelity:** 0.924 | **Dir. Accuracy:** 91% | **Lit. Consistency:** 80% | **TCTM:** 19/22

</details>

<details>
<summary><strong>Weronika</strong> -- Weronika Kaczmarczyk, 24F, student (UMCS), Lublin</summary>

Secure, grounded young woman living with her boyfriend Adam in Lublin. Religious upbringing (ordered, not fanatical), warm family with a policeman father and librarian mother. Feels "quiet joy" about building a shared life. Highest fidelity score among secure personas.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.71 | Yes |
| DBZ Avoidance | low | -0.79 | Yes |
| MentS Self | moderate_high | +0.53 | Yes |
| MentS Other | high | +1.21 | Yes |
| MentS Motivation | moderate_high | +1.45 | Yes |
| KPP | moderate_high | +0.36 | Yes |
| TIPI E | moderate_high | -0.04 | Yes |
| TIPI A | high | +0.61 | Yes |
| TIPI C | moderate_high | +0.29 | Yes |
| TIPI ES | moderate_high | +0.41 | Yes |
| TIPI O | moderate | -0.01 | Yes |

**Fidelity:** 0.940 | **Dir. Accuracy:** 100% | **Lit. Consistency:** 70% | **TCTM:** 18/22

</details>

<details>
<summary><strong>Lukasz</strong> -- Lukasz Turek, 26M, graphic designer, Wroclaw</summary>

Creative, chaotic graphic designer with ADHD-like hyperfocus patterns. Lives with girlfriend Natalia in Wroclaw. Alternates between 8-hour flow states producing brilliant work and completely unproductive days spent on Reddit. Warm but somewhat disorganized, secure attachment with moderate mentalization.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.80 | Yes |
| DBZ Avoidance | low | -0.74 | Yes |
| MentS Self | moderate | -0.50 | Yes |
| MentS Other | moderate_high | +0.32 | Yes |
| MentS Motivation | moderate_high | +0.66 | Yes |
| KPP | moderate_high | -0.10 | Yes |
| TIPI E | high | +0.69 | Yes |
| TIPI A | moderate | +0.19 | Yes |
| TIPI C | low | -1.81 | Yes |
| TIPI ES | moderate_high | +0.41 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**Fidelity:** 0.884 | **Dir. Accuracy:** 91% | **Lit. Consistency:** 60% | **TCTM:** 19/22

</details>

<details>
<summary><strong>Anna-sim</strong> -- Anna Ptasinska, 34F, educational project specialist, Krakow</summary>

Direct, warm, no-nonsense married woman with a 5-year-old daughter. Known as "the critical one" among colleagues -- she tells you the truth whether you want to hear it or not. Secure attachment expressed through practical love (coffee made without asking, pizza on Friday evenings) rather than verbal declarations.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.30 | Yes |
| DBZ Avoidance | low | -0.33 | Yes |
| MentS Self | high | +0.53 | Yes |
| MentS Other | moderate_high | +0.50 | Yes |
| MentS Motivation | moderate_high | -0.91 | No |
| KPP | moderate | -0.49 | Yes |
| TIPI E | moderate_high | +0.32 | Yes |
| TIPI A | low | -0.67 | No |
| TIPI C | moderate_high | +0.64 | Yes |
| TIPI ES | moderate_high | +0.73 | Yes |
| TIPI O | low_moderate | -1.32 | Yes |

**Fidelity:** 0.871 | **Dir. Accuracy:** 73% | **Lit. Consistency:** 90% | **TCTM:** 19/22

</details>

<details>
<summary><strong>Sara</strong> -- Sara Malinowska, 34F, pediatrician, Krakow</summary>

Pediatrician and mother of three, married to architect Marek for 14 years. Grew up in a "warm, calm" intellectual family in Tarnow. Loves her husband "not in a movie-touching way, but daily." A profile of stable, mature, high-functioning security with strong mentalization.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.03 | Yes |
| DBZ Avoidance | low | -0.91 | Yes |
| MentS Self | high | +0.71 | Yes |
| MentS Other | high | +1.57 | Yes |
| MentS Motivation | moderate | +0.98 | Yes |
| KPP | high | +0.24 | Yes |
| TIPI E | moderate_high | -0.04 | Yes |
| TIPI A | high | +0.61 | Yes |
| TIPI C | moderate_high | +0.29 | Yes |
| TIPI ES | moderate | +0.09 | Yes |
| TIPI O | moderate | -0.01 | Yes |

**Fidelity:** 0.904 | **Dir. Accuracy:** 91% | **Lit. Consistency:** 70% | **TCTM:** 19/22

</details>

### Anxious-Preoccupied Attachment (8 personas, 50% match rate)

<details>
<summary><strong>Ania</strong> -- Anna Kowalczyk, 23F, student (Polish philology), Poznan</summary>

Highly emotional university student in a seven-month relationship with Maciek. Sees him as "the rock I need" while describing herself as "a storm of words and emotions." Panics at signs of distance, writes long emotional texts, immediately assumes abandonment. High motivation to mentalize but poor self-regulation.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +2.19 | Yes |
| DBZ Avoidance | low | -0.68 | Yes |
| MentS Self | moderate_high | -0.33 | No |
| MentS Other | moderate | +0.86 | Yes |
| MentS Motivation | very_high | +1.61 | Yes |
| KPP | moderate_high | +0.13 | Yes |
| TIPI E | moderate_high | -0.04 | Yes |
| TIPI A | high | +0.61 | Yes |
| TIPI C | low | -0.76 | Yes |
| TIPI ES | very_low | -1.51 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**Fidelity:** 0.791 | **Dir. Accuracy:** 73% | **Lit. Consistency:** 50% | **TCTM:** 20/22 | **Match:** Yes

</details>

<details>
<summary><strong>Natalia</strong> -- Natalia Kowal, 25F, bartender, Lodz</summary>

Highest fidelity score in the entire dataset (0.980). Bartender in a volatile relationship with Kamil. Dropped out of psychology studies. Oscillates between 200% certainty in love and 200% certainty of abandonment. Low mentalization across the board, low personal competence. The "textbook" anxious-preoccupied persona.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +2.28 | Yes |
| DBZ Avoidance | low | -0.74 | Yes |
| MentS Self | low | -2.05 | Yes |
| MentS Other | low | -1.64 | Yes |
| MentS Motivation | low_moderate | -1.86 | Yes |
| KPP | low | -3.68 | Yes |
| TIPI E | moderate_high | -0.04 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | low | -1.81 | Yes |
| TIPI ES | very_low | -1.83 | Yes |
| TIPI O | low_moderate | -1.33 | Yes |

**Fidelity:** 0.980 | **Dir. Accuracy:** 100% | **Lit. Consistency:** 90% | **TCTM:** 19/22 | **Match:** Yes

</details>

<details>
<summary><strong>Pawel</strong> -- Pawel Radomski, 26M, car mechanic, Mielec</summary>

Small-town mechanic living with girlfriend Jola in Mielec. Low education, limited vocabulary for emotions, but deeply attached to Jola and their quiet domestic life. His mentalization scores are low not because of avoidance but because of genuine simplicity. Attachment anxiety expressed through dependence rather than dramatic protest.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | +1.36 | Yes |
| DBZ Avoidance | moderate | +0.65 | Yes |
| MentS Self | low | -1.88 | Yes |
| MentS Other | low_moderate | -0.93 | Yes |
| MentS Motivation | low | -1.39 | Yes |
| KPP | low | -1.29 | Yes |
| TIPI E | moderate | -0.41 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | moderate | -0.41 | No |
| TIPI ES | low | -0.55 | Yes |
| TIPI O | low | -1.32 | Yes |

**Fidelity:** 0.927 | **Dir. Accuracy:** 82% | **Lit. Consistency:** 100% | **TCTM:** 19/22 | **Match:** Yes

</details>

<details>
<summary><strong>Jola</strong> -- Jolanta Tarczynska, 28F, executive assistant, Warsaw</summary>

Emotional, empathic executive assistant living alone on Zoliborz. Collects chestnuts with the 6-year-old neighbor girl. In relationships, tends to over-read partners' internal states and respond with intense emotional investment. High motivation to mentalize but anxiety-driven.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | +1.68 | Yes |
| DBZ Avoidance | low_moderate | +0.59 | No |
| MentS Self | high | -0.33 | No |
| MentS Other | very_high | +1.04 | Yes |
| MentS Motivation | very_high | +1.29 | Yes |
| KPP | moderate_high | +0.19 | Yes |
| TIPI E | moderate | -0.78 | Yes |
| TIPI A | moderate_high | +0.19 | Yes |
| TIPI C | moderate | -0.06 | Yes |
| TIPI ES | very_low | -1.51 | Yes |
| TIPI O | high | +0.87 | Yes |

**Fidelity:** 0.811 | **Dir. Accuracy:** 73% | **Lit. Consistency:** 60% | **TCTM:** 20/22 | **Match:** Yes

</details>

<details>
<summary><strong>Klaudia</strong> -- Klaudia Winowska, 28F, social worker, Lublin [MISS]</summary>

Social worker at MOPS (municipal welfare center) dealing with 180 families. Married to Damian, has a 2-year-old daughter Hania. Grew up with an alcoholic father and enabling mother -- Damian "rescued" her. Expected anxious-preoccupied but scored as secure: the biography emphasizes post-rescue stability more than residual anxiety, and the LLM responded to the current relationship quality rather than childhood patterns.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | +0.30 | Yes |
| DBZ Avoidance | low | +0.48 | No |
| MentS Self | low | -0.50 | Yes |
| MentS Other | very_high | +1.21 | Yes |
| MentS Motivation | very_high | +1.13 | Yes |
| KPP | moderate | -0.44 | Yes |
| TIPI E | moderate_high | -0.04 | Yes |
| TIPI A | high | +0.61 | Yes |
| TIPI C | moderate_high | +0.29 | Yes |
| TIPI ES | low | -0.55 | Yes |
| TIPI O | moderate | -0.45 | Yes |

**Fidelity:** 0.444 | **Dir. Accuracy:** 91% | **Lit. Consistency:** 40% | **TCTM:** 20/22 | **Match:** No (predicted: secure)

</details>

<details>
<summary><strong>Bartek</strong> -- Bartosz Urbaniak, 29M, backend developer, Krakow [MISS]</summary>

Quiet, internally intense programmer who "always has the expression of someone hearing something others don't." Expected anxious-preoccupied but scored as dismissive-avoidant: the biography's emphasis on social withdrawal and emotional opacity overshadowed the underlying anxiety. A case where behavioral presentation diverges from internal experience.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | -0.02 | No |
| DBZ Avoidance | moderate | +1.75 | No |
| MentS Self | very_high | -0.33 | No |
| MentS Other | moderate_high | +0.50 | Yes |
| MentS Motivation | very_high | +1.45 | Yes |
| KPP | moderate_high | +0.70 | Yes |
| TIPI E | low | -2.25 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | moderate | -0.06 | Yes |
| TIPI ES | very_low | -1.19 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**Fidelity:** 0.427 | **Dir. Accuracy:** 82% | **Lit. Consistency:** 50% | **TCTM:** 20/22 | **Match:** No (predicted: dismissive_avoidant)

</details>

<details>
<summary><strong>Gabriela</strong> -- Gabriela Sienko, 33F, OB/GYN resident physician, Warsaw [MISS]</summary>

Perfectionist gynecologist married to Rafal, a tax consultant. Everything in her apartment has its place; everything is always clean. Expected anxious-preoccupied but scored as secure: her marriage to the "genuinely good" Rafal and professional competence masked the underlying anxious patterns. The LLM responded to her current functioning rather than her perfectionistic defense structure.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | +0.26 | Yes |
| DBZ Avoidance | low | +0.31 | No |
| MentS Self | moderate_high | -0.50 | No |
| MentS Other | high | +0.68 | Yes |
| MentS Motivation | high | +1.13 | Yes |
| KPP | high | +1.10 | Yes |
| TIPI E | moderate | -0.78 | Yes |
| TIPI A | moderate_high | +0.19 | Yes |
| TIPI C | very_high | +1.34 | Yes |
| TIPI ES | low | -1.19 | Yes |
| TIPI O | moderate | -0.01 | Yes |

**Fidelity:** 0.391 | **Dir. Accuracy:** 73% | **Lit. Consistency:** 50% | **TCTM:** 20/22 | **Match:** No (predicted: secure)

</details>

<details>
<summary><strong>Michal-k</strong> -- Michal Krasowski, 28M, accountant, Poznan [MISS]</summary>

Accountant with diagnosed OCD (checking subtype). Checks VAT declarations twelve times in a row. In therapy for three years. Expected anxious-preoccupied but scored as fearful-avoidant: the OCD-driven checking behavior elevated avoidance scores alongside the expected anxiety, pushing him into the fearful quadrant rather than the anxious one.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +0.90 | Yes |
| DBZ Avoidance | moderate | +1.87 | No |
| MentS Self | very_high | -0.33 | No |
| MentS Other | moderate_high | +0.32 | Yes |
| MentS Motivation | very_high | +1.13 | Yes |
| KPP | very_high | +1.15 | Yes |
| TIPI E | low | -1.88 | Yes |
| TIPI A | moderate_high | +0.19 | Yes |
| TIPI C | high | +0.99 | Yes |
| TIPI ES | very_low | -1.51 | Yes |
| TIPI O | moderate | -0.45 | Yes |

**Fidelity:** 0.391 | **Dir. Accuracy:** 73% | **Lit. Consistency:** 50% | **TCTM:** 19/22 | **Match:** No (predicted: fearful_avoidant)

</details>

### Dismissive-Avoidant Attachment (7 personas, 100% match rate)

<details>
<summary><strong>Jakub</strong> -- Jakub Wieczorek, 32M, senior software engineer, Warsaw</summary>

Lives alone in a 62m2 apartment he bought on a 30-year mortgage. Single for 2.5 years -- his last relationship ended when Karolina asked "so what are we?" and he said "nothing concrete, I guess." Team lead at a German fintech company, valued for being "the quiet one." The problem/solution loop at work gives him daily purpose. High competence, very low motivation to mentalize.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.40 | Yes |
| DBZ Avoidance | very_high | +2.62 | Yes |
| MentS Self | moderate_high | -0.15 | No |
| MentS Other | moderate_low | -1.11 | Yes |
| MentS Motivation | low | -2.17 | Yes |
| KPP | high | +1.15 | Yes |
| TIPI E | very_low | -1.88 | Yes |
| TIPI A | low | -1.09 | Yes |
| TIPI C | high | +0.99 | Yes |
| TIPI ES | high | +1.05 | Yes |
| TIPI O | low_moderate | -1.32 | Yes |

**Fidelity:** 0.864 | **Dir. Accuracy:** 91% | **Lit. Consistency:** 50% | **TCTM:** 19/22

</details>

<details>
<summary><strong>Tomek</strong> -- Tomasz Debski, 27M, copywriter, Gdansk</summary>

Solitary copywriter who can inhabit any brand voice except his own. Lives in a 26m2 studio where he can see a sliver of the sea if he stands on a chair. Has hosted exactly three women in his apartment; none were invited back. Professionally excellent, personally absent.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.94 | Yes |
| DBZ Avoidance | very_high | +2.91 | Yes |
| MentS Self | low_moderate | -1.53 | Yes |
| MentS Other | high | +1.04 | Yes |
| MentS Motivation | moderate | +0.35 | Yes |
| KPP | moderate_high | -0.04 | Yes |
| TIPI E | very_low | -2.25 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | moderate_high | +0.29 | Yes |
| TIPI ES | high | +1.05 | Yes |
| TIPI O | moderate_high | -0.01 | Yes |

**Fidelity:** 0.860 | **Dir. Accuracy:** 100% | **Lit. Consistency:** 30% | **TCTM:** 20/22

</details>

<details>
<summary><strong>Magda</strong> -- Magdalena Pawlicka, 31F, strategy consultant, Warsaw</summary>

Senior manager at a consulting firm, bought her own apartment at 29. Remembers exactly what she wore when she signed the notarial deed. After signing, she stood under a streetlamp smoking a cigarette (she doesn't smoke) and felt "something between relief and emptiness." Highly competent, emotionally controlled, dismissive of vulnerability.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.84 | Yes |
| DBZ Avoidance | very_high | +2.68 | Yes |
| MentS Self | moderate | -0.33 | Yes |
| MentS Other | moderate_high | +0.50 | Yes |
| MentS Motivation | moderate | +0.66 | Yes |
| KPP | high | +1.55 | Yes |
| TIPI E | low | -1.51 | Yes |
| TIPI A | low | -0.67 | Yes |
| TIPI C | very_high | +1.34 | Yes |
| TIPI ES | moderate_high | +0.73 | Yes |
| TIPI O | moderate | -0.01 | Yes |

**Fidelity:** 0.884 | **Dir. Accuracy:** 91% | **Lit. Consistency:** 60% | **TCTM:** 20/22

</details>

<details>
<summary><strong>Adrian</strong> -- Adrian Majchrowski, 33M, DevOps engineer, Katowice</summary>

Lives alone with his Persian cat Pixel in a 38m2 apartment. Works remotely for a medical EHR company; his body tenses an hour before the rare office visit because he knows he'll be "surrounded by people" all day. Visits family in Chorzow during holidays for two precisely scheduled meetings. His apartment has one poster: a 1910 Berlin railway map he bought on Allegro without knowing why he liked it.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.03 | Yes |
| DBZ Avoidance | very_high | +2.79 | Yes |
| MentS Self | very_low | -1.19 | Yes |
| MentS Other | low | -1.11 | Yes |
| MentS Motivation | very_low | -0.76 | Yes |
| KPP | low_moderate | +1.66 | No |
| TIPI E | very_low | -2.62 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | high | +0.99 | Yes |
| TIPI ES | high | +1.05 | Yes |
| TIPI O | low | -0.89 | Yes |

**Fidelity:** 0.864 | **Dir. Accuracy:** 91% | **Lit. Consistency:** 50% | **TCTM:** 20/22

</details>

<details>
<summary><strong>Hubert</strong> -- Hubert Nowik, 31M, actuary, Wroclaw</summary>

Insurance actuary who declined a management promotion because it would mean "managing people." His apartment is nearly empty. At his grandmother's funeral, everyone cried; he stood still, thinking "there is grandmother, she is gone, this is the end" -- a thought that was "knowledge, not feeling. Like a mathematical theorem: true but not painful."

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.07 | Yes |
| DBZ Avoidance | very_high | +2.04 | Yes |
| MentS Self | very_low | -1.71 | Yes |
| MentS Other | low | -1.29 | Yes |
| MentS Motivation | low | -0.28 | Yes |
| KPP | high | +1.55 | Yes |
| TIPI E | very_low | -2.62 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | high | +0.99 | Yes |
| TIPI ES | high | +1.05 | Yes |
| TIPI O | moderate | -0.45 | No |

**Fidelity:** 0.827 | **Dir. Accuracy:** 82% | **Lit. Consistency:** 50% | **TCTM:** 20/22

</details>

<details>
<summary><strong>Dominika</strong> -- Dominika Wronska, 30F, marketing director, Warsaw</summary>

Marketing director with a 12-person team, 8M PLN annual budget. Lives in a 95m2 Srodmiescie apartment with carefully curated art. Raised by demanding intellectual parents who gave attention for achievements, not for being. Had 8-9 boyfriends, none lasting more than 9 months. One ex told her: "Dominika, I feel like you use me as another strategic project." She thanked him for the observation and broke up a week later.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -0.61 | Yes |
| DBZ Avoidance | very_high | +2.39 | Yes |
| MentS Self | moderate | -0.84 | Yes |
| MentS Other | very_high | +1.04 | Yes |
| MentS Motivation | moderate | +0.66 | Yes |
| KPP | moderate_high | +1.66 | Yes |
| TIPI E | moderate_high | +0.32 | Yes |
| TIPI A | low | -0.67 | Yes |
| TIPI C | very_high | +1.34 | Yes |
| TIPI ES | moderate_high | +0.41 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**Fidelity:** 0.907 | **Dir. Accuracy:** 82% | **Lit. Consistency:** 90% | **TCTM:** 20/22

</details>

<details>
<summary><strong>Agata</strong> -- Agata Rejdak, 34F, data analyst, Torun</summary>

Remote data analyst who has never met her colleagues in person (hired during COVID, office is 300km away, "Zoom is enough"). Paid off her mortgage in 5 years by channeling every bonus into prepayments because she "wanted to be free from obligations." Walks to the forest every day regardless of weather. Raised in a quiet intellectual home with a classicist father who recited Virgil on walks.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | low | -1.21 | Yes |
| DBZ Avoidance | very_high | +2.74 | Yes |
| MentS Self | moderate | +0.71 | Yes |
| MentS Other | low | +0.32 | No |
| MentS Motivation | low | +0.50 | No |
| KPP | very_high | +1.95 | Yes |
| TIPI E | very_low | -2.62 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | high | +0.99 | Yes |
| TIPI ES | moderate_high | +0.73 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**Fidelity:** 0.887 | **Dir. Accuracy:** 82% | **Lit. Consistency:** 80% | **TCTM:** 20/22

</details>

### Fearful-Avoidant (Disorganized) Attachment (8 personas, 75% match rate)

<details>
<summary><strong>Piotr</strong> -- Piotr Walczak, 24M, student (mechatronics), Krakow</summary>

The first persona created as a pilot test. Father left when he was six (remembers three things: the Biedronka bag, mother's quiet voice, ice cream he never ate). Oscillates between craving closeness and withdrawing. Met Ola through a study group, fell in love, then systematically sabotaged the relationship. Low mentalization, high anxiety and avoidance simultaneously.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | +1.68 | Yes |
| DBZ Avoidance | high | +2.79 | Yes |
| MentS Self | moderate_low | -2.05 | Yes |
| MentS Other | moderate_low | -1.46 | Yes |
| MentS Motivation | moderate | -0.76 | Yes |
| KPP | high | +0.41 | Yes |
| TIPI E | low | -2.62 | Yes |
| TIPI A | low | +0.19 | No |
| TIPI C | high | -0.06 | No |
| TIPI ES | low | -1.51 | Yes |
| TIPI O | moderate | -1.32 | Yes |

**Fidelity:** 0.867 | **Dir. Accuracy:** 82% | **Lit. Consistency:** 70% | **TCTM:** 19/22

</details>

<details>
<summary><strong>Michal-sim</strong> -- Michal Seidowski, 24M, student (mechatronics), Krakow</summary>

Engineering student who cannot talk about problems with close people. Mother who "loved too much" and father who was physically present but emotionally absent. Relationship with Ola is marked by approach-avoidance cycling. The second pilot persona.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | +1.54 | Yes |
| DBZ Avoidance | very_high | +2.74 | Yes |
| MentS Self | moderate | -1.71 | Yes |
| MentS Other | moderate | -1.29 | Yes |
| MentS Motivation | moderate_high | -0.60 | No |
| KPP | moderate_high | +0.76 | Yes |
| TIPI E | very_low | -2.25 | Yes |
| TIPI A | moderate_high | +0.61 | Yes |
| TIPI C | moderate_high | +0.29 | Yes |
| TIPI ES | very_low | -1.19 | Yes |
| TIPI O | moderate | -0.45 | Yes |

**Fidelity:** 0.778 | **Dir. Accuracy:** 55% | **Lit. Consistency:** 80% | **TCTM:** 19/22

</details>

<details>
<summary><strong>Filip</strong> -- Filip Zurek, 30M, book editor, Warsaw</summary>

Book editor currently working on a transgenerational trauma book -- ironic because he is a living example. Lives alone, struggles with intimacy despite high verbal intelligence. His biography encodes very high mentalization coexisting with fearful attachment, a theoretically coherent but difficult-to-detect pattern.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | +1.27 | Yes |
| DBZ Avoidance | high | +2.33 | Yes |
| MentS Self | very_high | -1.02 | No |
| MentS Other | high | +0.32 | Yes |
| MentS Motivation | very_high | +1.29 | Yes |
| KPP | very_high | +1.15 | Yes |
| TIPI E | low | -1.88 | Yes |
| TIPI A | low | -0.67 | Yes |
| TIPI C | low | -1.11 | Yes |
| TIPI ES | very_low | -1.51 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**Fidelity:** 0.811 | **Dir. Accuracy:** 73% | **Lit. Consistency:** 60% | **TCTM:** 20/22

</details>

<details>
<summary><strong>Ewa</strong> -- Ewa Lisowska, 35F, literary translator, Gdynia</summary>

Literary translator who cried for twenty minutes after her bathroom renovation was finished -- "not because she was proud, but because it was hers." Translates American novels into Polish, lives in a 1936 tenement. High mentalization of others and motivation, but combined with simultaneous high anxiety and avoidance.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | moderate_high | +0.90 | Yes |
| DBZ Avoidance | high | +1.64 | Yes |
| MentS Self | high | -0.15 | No |
| MentS Other | moderate_high | +1.39 | Yes |
| MentS Motivation | very_high | +1.45 | Yes |
| KPP | very_high | +1.49 | Yes |
| TIPI E | low | -1.88 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | moderate | -0.06 | Yes |
| TIPI ES | very_low | -1.19 | Yes |
| TIPI O | very_high | +1.31 | Yes |

**Fidelity:** 0.920 | **Dir. Accuracy:** 100% | **Lit. Consistency:** 60% | **TCTM:** 19/22

</details>

<details>
<summary><strong>Zuzia</strong> -- Zuzanna Kaczor, 29F, freelance photographer, Lodz</summary>

Portrait photographer whose clients say she makes them "see themselves, not the version they show others." Raised by a mother who alternated unpredictably between warmth and emotional absence. Her ex-boyfriend Marcin called her "Zuzka" (too childish, she never told him). In therapy, working through disorganized attachment rooted in inconsistent maternal care.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | moderate_high | +0.85 | Yes |
| DBZ Avoidance | high | +2.04 | Yes |
| MentS Self | very_high | -0.33 | No |
| MentS Other | high | +0.86 | Yes |
| MentS Motivation | very_high | +1.13 | Yes |
| KPP | high | +0.36 | Yes |
| TIPI E | low | -1.51 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | moderate | -0.06 | Yes |
| TIPI ES | very_low | -1.19 | Yes |
| TIPI O | very_high | +0.87 | Yes |

**Fidelity:** 0.847 | **Dir. Accuracy:** 82% | **Lit. Consistency:** 60% | **TCTM:** 20/22

</details>

<details>
<summary><strong>Radek</strong> -- Radoslaw Kedziora, 27M, bartender, Poznan</summary>

Fifth job this year. Married at 21 after three months of dating (during a fight: "Stay. Let's get married."), divorced within two years. Currently bartending at Republika after being fired from a grocery store for disappearing for five days. Chaotic attachment history, high anxiety and avoidance, low conscientiousness. His mother calls him "Radziusiu" and is happy when he calls after a month-long silence.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | very_high | +1.73 | Yes |
| DBZ Avoidance | high | +1.87 | Yes |
| MentS Self | very_low | -2.05 | Yes |
| MentS Other | moderate_high | +0.50 | Yes |
| MentS Motivation | moderate | -0.44 | Yes |
| KPP | low | -2.03 | Yes |
| TIPI E | moderate | -0.41 | Yes |
| TIPI A | low | -0.67 | Yes |
| TIPI C | very_low | -1.81 | Yes |
| TIPI ES | very_low | -1.51 | Yes |
| TIPI O | moderate | -0.45 | No |

**Fidelity:** 0.871 | **Dir. Accuracy:** 73% | **Lit. Consistency:** 90% | **TCTM:** 20/22

</details>

<details>
<summary><strong>Marek</strong> -- Marek Pietruczyk, 29M, courier driver, Radom [MISS]</summary>

Courier driver living alone in a 38m2 apartment with one chair at the kitchen table. His brother Adam died in a car accident four years ago; Marek was in the passenger seat, broke his pelvis and three ribs, was in a coma for four days. Since then, "dark." Expected fearful-avoidant but scored as dismissive-avoidant: the grief-driven shutdown eliminated visible anxiety, presenting as pure avoidance.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | -0.61 | No |
| DBZ Avoidance | very_high | +2.85 | Yes |
| MentS Self | low | -2.40 | Yes |
| MentS Other | low | -2.36 | Yes |
| MentS Motivation | low | -2.02 | Yes |
| KPP | low_moderate | -2.99 | Yes |
| TIPI E | very_low | -2.62 | Yes |
| TIPI A | low | -0.67 | Yes |
| TIPI C | moderate | -0.06 | Yes |
| TIPI ES | low | -0.55 | Yes |
| TIPI O | very_low | -2.20 | Yes |

**Fidelity:** 0.504 | **Dir. Accuracy:** 91% | **Lit. Consistency:** 70% | **TCTM:** 19/22 | **Match:** No (predicted: dismissive_avoidant)

</details>

<details>
<summary><strong>Kamil</strong> -- Kamil Wojtczak, 32M, security guard (ex-military), Rzeszow [MISS]</summary>

Former soldier with PTSD from combat missions. Works as a night security guard because his hypervigilance is useful there rather than pathological. Has a therapy dog (Bur, adopted at his psychologist's suggestion). Expected fearful-avoidant but scored as dismissive-avoidant: his military-trained emotional suppression flattened anxiety scores, while avoidance remained high.

| Dimension | Expected | Observed z | Dir. Match |
|:---|:---|:---:|:---:|
| DBZ Anxiety | high | -0.29 | No |
| DBZ Avoidance | very_high | +2.16 | Yes |
| MentS Self | moderate | -0.67 | Yes |
| MentS Other | moderate | -0.04 | Yes |
| MentS Motivation | low | +0.19 | No |
| KPP | low_moderate | -0.21 | Yes |
| TIPI E | very_low | -2.62 | Yes |
| TIPI A | moderate | -0.24 | Yes |
| TIPI C | moderate_high | +0.29 | Yes |
| TIPI ES | low | -0.55 | Yes |
| TIPI O | moderate | -0.45 | Yes |

**Fidelity:** 0.444 | **Dir. Accuracy:** 91% | **Lit. Consistency:** 40% | **TCTM:** 19/22 | **Match:** No (predicted: dismissive_avoidant)

</details>

---

## Models Used

Persona responses were generated by two Claude models via AWS Bedrock:

- **eu.anthropic.claude-opus-4-6-v1** -- primary model for pilot personas
- **eu.anthropic.claude-sonnet-4-6** -- used for the majority of the N=30 batch

Each persona was presented with its biography and then completed the five instruments sequentially. The scoring pipeline (`scripts/analyze_and_prepare.py`) uses published Polish norms for all instruments.

## Scoring Norms

All z-scores and classifications use published Polish norms:

- **DBZ-R:** Lubiewska, K. (2016). *Doswiadczanie Bliskich Zwiazkov-Rewidowany*. Wydawnictwo Uniwersytetu Kazimierza Wielkiego.
- **MentS:** Janczak, M. O. (2021). Polish adaptation and validation of the Mentalization Scale (MentS). *Psychiatria Polska*, 55(6), 1257-1274.
- **KPP:** Matusz, P. (2011). *Kwestionariusz Kompetencji Personalnych*.
- **TIPI-PL:** Sorokowska, A. et al. (2014). *TIPI-PL -- polska adaptacja Ten Item Personality Inventory (TIPI)*. Roczniki Psychologiczne, 17(2), 353-366.
- **TCTM-22:** Original instrument by Wiencek (2026). Error typology based on: Dziobek, I. et al. (2006). *Introducing MASC: A Movie for the Assessment of Social Cognition*. Journal of Autism and Developmental Disorders, 36(5), 623-636.

## Fidelity Score

The composite fidelity score (0.0-1.0) weights:

1. **Attachment style match** (binary, 50% weight) -- correct 4-category classification
2. **Directional accuracy** (proportion, 25% weight) -- do observed z-scores have the expected sign?
3. **Literature consistency** (proportion, 25% weight) -- do 10 theoretically-expected cross-scale correlations hold?

Mean fidelity across all 30 personas: **0.788**.

## Limitations

1. **Synthetic ceiling effect:** LLM personas consistently score high on TCTM-22 (M=19.4/22), likely reflecting language models' strong theory-of-mind performance rather than persona fidelity.

2. **Anxious-preoccupied difficulty:** The 50% match rate for anxious-preoccupied personas suggests that behavioral descriptions of anxiety are harder for LLMs to translate into elevated anxiety scores compared to avoidance, which manifests in more overtly scoreable behavioral patterns.

3. **State vs. trait:** Biographies describing current well-functioning (e.g., Klaudia's stable marriage) may override childhood-rooted anxious patterns, as the LLM responds to current presentation rather than developmental history.

4. **Single-run design:** Each persona was scored once. Inter-run variance was not measured.

5. **Polish-only:** Biographies and instruments are in Polish; generalizability to other languages is unknown.

## How to Cite

```bibtex
@mastersthesis{wiencek2026tctm,
  author  = {Wiencek, Micha{\l}},
  title   = {Kompetencja mentalizacji w polskiej komunikacji tekstowej: pilota{\.z}owa walidacja {TCTM-22}},
  school  = {Uniwersytet Komisji Edukacji Narodowej w Krakowie},
  year    = {2026},
  type    = {Praca magisterska},
  note    = {Synthetic persona validation dataset (N=30)}
}
```

If citing the dataset specifically:

```bibtex
@dataset{wiencek2026tctm_synthetic,
  author    = {Wiencek, Micha{\l}},
  title     = {{TCTM-22} Synthetic Persona Validation Dataset ({N}=30)},
  year      = {2026},
  publisher = {GitHub},
  note      = {30 synthetic biographies with ground-truth psychological profiles across 12 dimensions}
}
```

## License

This dataset is released under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).

You are free to share and adapt the material for any purpose, including commercial, provided you give appropriate credit.

## Acknowledgments

This work was conducted as part of an MA thesis at UKEN Krakow. The psychometric scoring pipeline and all 30 biographies were developed by Michal Wiencek. LLM inference was performed using Claude models (Anthropic) via AWS Bedrock (eu-central-1).
