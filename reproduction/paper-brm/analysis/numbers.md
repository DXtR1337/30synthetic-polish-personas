# numbers.md — primary analysis manifest (seed 20260611)

[design] corrected rows=538 (persona=424, baseline=70, zero-prompt=44); initial rows=618 (persona=426, baseline=149, zero-prompt=43)
[design] scored model runs (22-item battery, all waves) = 1156; the human sanity check (N=7) is released separately, aggregate-only
[intercepts/corrected] Anx z: mini=-1.33 vs 5.4(full)=-1.51 (gap 0.18 SD)
[intercepts/corrected] largest between-model spread: DBZ-R Avo = 1.75 z (per-dim spreads: DBZ-R Anx 1.00, DBZ-R Avo 1.75, MentS total 1.03, KPP mean 0.64, TIPI E 1.54, TIPI A 1.50, TIPI C 1.33, TIPI ES 1.06, TIPI O 0.57)
[slopes/corrected] 6-model cluster median r range: 0.948-0.989 (median of medians 0.965)
[slopes/corrected] 5.4(full)<->5.5 median r = 0.989 (min 0.944, max 0.992) — per-dim: DBZ-R Anx 0.99, DBZ-R Avo 0.99, MentS total 0.99, KPP mean 0.99, TIPI E 0.99, TIPI A 0.94, TIPI C 0.98, TIPI ES 0.99, TIPI O 0.97
[slopes/corrected] mini vs others median r range: 0.947-0.962
[fidelity/corrected run1] Sonnet 23/30; Opus 25/30; 5.4-mini 29/30; 5.4 (full) 26/30; GPT-5.5 26/30; Grok 26/30; Gemini 25/30
[fidelity/corrected] personas with <=4/7 models matching: bartek(anxious_preoccupied,1), gabriela(anxious_preoccupied,4), kamil(fearful_avoidant,4), marek(fearful_avoidant,0), michal-k(anxious_preoccupied,1)
[fidelity/corrected] personas with 7/7 unanimous correct: 21/30
[fidelity/corrected] Fleiss kappa 7 models = 0.853 [0.75, 0.94]; 6 models (excl. mini) = 0.862 [0.75, 0.94]
[fidelity/corrected run1-vs-run2 agreement] Sonnet 29/30; Opus 29/30; 5.4-mini 29/30; 5.4 (full) 29/30; GPT-5.5 30/30; Grok 28/30; Gemini 29/30
[tctm/corrected persona totals] Sonnet 95.3% (M=20.97, SD=0.61); Opus 87.0% (M=19.15, SD=1.73); 5.4-mini 83.4% (M=18.26, SD=1.64); 5.4 (full) 92.2% (M=20.28, SD=1.42); GPT-5.5 94.5% (M=20.79, SD=1.05); Grok 90.9% (M=20.00, SD=2.74); Gemini 88.2% (M=19.32, SD=2.07)
[tctm/corrected baseline totals] Sonnet M=21.00 SD=0.00; Opus M=20.00 SD=0.00; 5.4-mini M=19.10 SD=1.10; 5.4 (full) M=20.80 SD=0.42; GPT-5.5 M=21.80 SD=0.42; Grok M=21.60 SD=0.70; Gemini M=19.90 SD=0.32
[items/corrected] hardest 5 items (pooled): w22 31%, s07 72%, w19 77%, w11 84%, w28 85%
[items/corrected] easiest 5 items (pooled): r09 99%, r08 100%, pw11 100%, s08 100%, s10 100%
[items/corrected] Cochran Q: 12/20 items FDR-significant across models; largest s07 Q=127.9, q=7.2e-24
[natural-exp s07] Sonnet 1.7->100.0 (+98.3pp); Opus 6.7->28.3 (+21.7pp); 5.4-mini 0.0->8.2 (+8.2pp); 5.4 (full) 0.0->96.7 (+96.7pp); GPT-5.5 55.7->96.7 (+41.0pp); Grok 33.3->78.7 (+45.4pp); Gemini 83.1->93.3 (+10.3pp)
[natural-exp w19] Sonnet 95.0->100.0 (+5.0pp); Opus 100.0->71.7 (-28.3pp); 5.4-mini 89.8->95.1 (+5.3pp); 5.4 (full) 95.0->83.6 (-11.4pp); GPT-5.5 91.8->55.7 (-36.1pp); Grok 93.3->96.7 (+3.4pp); Gemini 75.4->38.3 (-37.1pp)
[natural-exp pw07] Sonnet 100.0->100.0 (+0.0pp); Opus 95.0->100.0 (+5.0pp); 5.4-mini 18.3->44.3 (+25.9pp); 5.4 (full) 95.0->98.4 (+3.4pp); GPT-5.5 96.7->100.0 (+3.3pp); Grok 56.7->96.7 (+40.1pp); Gemini 96.9->96.7 (-0.3pp)
[natural-exp w22] Sonnet 1.7->16.9 (+15.3pp); Opus 0.0->0.0 (+0.0pp); 5.4-mini 75.0->83.6 (+8.6pp); 5.4 (full) 0.0->0.0 (+0.0pp); GPT-5.5 59.0->50.8 (-8.2pp); Grok 55.0->57.4 (+2.4pp); Gemini 21.5->6.7 (-14.9pp)
[natural-exp totals] per-persona TCTM delta (corrected-initial): Sonnet +1.47; Opus +0.12; 5.4-mini +1.56; 5.4 (full) +0.57; GPT-5.5 +0.14; Grok +0.94; Gemini -0.27
[admin-context Sonnet s07] battery22 trunc 1.7% (n=60) vs corr 100.0% (n=60); battery57 trunc 100.0% (n=31) vs corr 100.0% (n=31)
[admin-context Sonnet w19] battery22 trunc 95.0% (n=60) vs corr 100.0% (n=60); battery57 trunc 100.0% (n=31) vs corr 54.8% (n=31)
[admin-context Sonnet w22] battery22 trunc 1.7% (n=60) vs corr 16.9% (n=59); battery57 trunc 71.0% (n=31) vs corr 54.8% (n=31)
[admin-context GPT-5.5 s07] battery22 trunc 55.7% (n=61) vs corr 96.7% (n=61); battery57 trunc 96.7% (n=30) vs corr 100.0% (n=31)
[admin-context GPT-5.5 w19] battery22 trunc 91.8% (n=61) vs corr 55.7% (n=61); battery57 trunc 100.0% (n=30) vs corr 54.8% (n=31)
[admin-context GPT-5.5 w22] battery22 trunc 59.0% (n=61) vs corr 50.8% (n=61); battery57 trunc 96.7% (n=30) vs corr 90.3% (n=31)
[determinism] zero-variance cells (n>=3): Sonnet/baseline/initial/tipi_a=5.5(n=10); Sonnet/baseline/initial/tctm_correct=19(n=10); Sonnet/baseline/corrected/tctm_correct=21(n=10); Sonnet/noprompt/corrected/tipi_a=5.5(n=6); Sonnet/noprompt/corrected/tipi_c=5.5(n=6); Sonnet/noprompt/corrected/tipi_o=6(n=6); Opus/baseline/initial/tipi_e=5(n=7); Opus/baseline/initial/tipi_c=6(n=7); Opus/baseline/initial/tipi_o=6.5(n=7); Opus/baseline/corrected/tipi_e=5(n=10); Opus/baseline/corrected/tipi_a=5(n=10); Opus/baseline/corrected/tipi_o=6.5(n=10); Opus/baseline/corrected/tctm_correct=20(n=10); Opus/noprompt/initial/tipi_e=5(n=5); Opus/noprompt/initial/tipi_a=5.5(n=5); Opus/noprompt/initial/tipi_c=5.5(n=5); Opus/noprompt/initial/tipi_es=5(n=5); Opus/noprompt/initial/tipi_o=6(n=5); Opus/noprompt/corrected/tipi_e=5(n=6); Opus/noprompt/corrected/tipi_c=5.5(n=6); Opus/noprompt/corrected/tipi_es=5(n=6); Opus/noprompt/corrected/tipi_o=6(n=6); Opus/noprompt/corrected/tctm_correct=21(n=6); 5.4 (full)/baseline/initial/anx_mean=1(n=31); 5.4 (full)/baseline/initial/kpp_mean=4.917(n=31); 5.4 (full)/baseline/initial/tctm_correct=19(n=31); 5.4 (full)/baseline/corrected/tipi_es=7(n=10); 5.4 (full)/noprompt/initial/ments_total=122(n=6); 5.4 (full)/noprompt/initial/tipi_e=5(n=6); 5.4 (full)/noprompt/initial/tipi_a=6(n=6); 5.4 (full)/noprompt/initial/tipi_c=6(n=6); 5.4 (full)/noprompt/initial/tipi_es=5(n=6); 5.4 (full)/noprompt/initial/tipi_o=6(n=6); 5.4 (full)/noprompt/initial/tctm_correct=20(n=6); 5.4 (full)/noprompt/corrected/kpp_mean=4.583(n=5); 5.4 (full)/noprompt/corrected/tipi_e=5(n=5); 5.4 (full)/noprompt/corrected/tipi_a=6(n=5); 5.4 (full)/noprompt/corrected/tipi_c=6(n=5); 5.4 (full)/noprompt/corrected/tipi_es=5(n=5); GPT-5.5/baseline/corrected/tipi_a=6(n=10); GPT-5.5/baseline/corrected/tipi_es=7(n=10); GPT-5.5/noprompt/initial/tipi_a=6(n=6); GPT-5.5/noprompt/initial/tipi_c=6(n=6); GPT-5.5/noprompt/initial/tipi_es=5(n=6); GPT-5.5/noprompt/initial/tctm_correct=22(n=6); GPT-5.5/noprompt/corrected/tipi_a=6(n=5); GPT-5.5/noprompt/corrected/tipi_c=6(n=5); GPT-5.5/noprompt/corrected/tipi_es=5(n=5); GPT-5.5/noprompt/corrected/tctm_correct=22(n=6); Grok/noprompt/corrected/tipi_e=6(n=6); Gemini/baseline/initial/tipi_c=7(n=10); Gemini/baseline/initial/tipi_es=7(n=10); Gemini/baseline/corrected/tipi_es=7(n=10); Gemini/noprompt/initial/tipi_a=6(n=7); Gemini/noprompt/corrected/tipi_a=6(n=8)
[kpp 5.4(full) baseline/initial] n=31, M=4.9170, SD=0.0000, unique=[np.float64(4.917)]
[kpp 5.4(full) baseline/corrected] n=10, M=4.9223, SD=0.0450, unique=[np.float64(4.833), np.float64(4.889), np.float64(4.917), np.float64(4.944), np.float64(4.972)]...
[avo-bimodality 5.4(full) baseline initial] N=31, BIC1=114.4 vs BIC2=108.8, bootstrap LRT p=0.0240; gap 0.556 in [3.50,4.06]; 13 below / 18 above 4; cluster means 2.87/5.36
[avo-bimodality corrected n=10] values sorted: 2.06, 2.06, 2.56, 3.17, 3.78, 4.00, 4.00, 4.44, 4.67, 4.72; 5 below / 5 above 4
[longitudinal slopes initial<->corrected] Sonnet med r=0.994 (min 0.969); Opus med r=0.991 (min 0.979); 5.4-mini med r=0.916 (min 0.860); 5.4 (full) med r=0.988 (min 0.953); GPT-5.5 med r=0.994 (min 0.972); Grok med r=0.973 (min 0.850); Gemini med r=0.980 (min 0.930)
[longitudinal style run1<->run1] Sonnet 29/30; Opus 28/30; 5.4-mini 15/30; 5.4 (full) 30/30; GPT-5.5 29/30; Grok 29/30; Gemini 28/30
[longitudinal baseline drift |delta raw|>0.5] 5.4-mini MentS total: 103.03(SD 4.09)->131.00(SD 4.69), d=+27.97; 5.4 (full) MentS total: 128.74(SD 3.39)->122.90(SD 3.81), d=-5.84; Opus MentS total: 125.86(SD 2.34)->129.00(SD 5.12), d=+3.14; 5.4-mini DBZ-R Anx: 4.68(SD 0.30)->1.69(SD 0.39), d=-2.99; 5.4-mini TIPI ES: 4.65(SD 0.29)->6.25(SD 0.26), d=+1.60; 5.4-mini TIPI O: 4.90(SD 0.30)->6.30(SD 0.35), d=+1.40; Gemini TIPI E: 4.65(SD 1.00)->3.35(SD 1.03), d=-1.30; Grok MentS total: 132.60(SD 5.58)->131.50(SD 3.63), d=-1.10; Gemini MentS total: 137.00(SD 3.74)->135.90(SD 4.70), d=-1.10; Gemini DBZ-R Avo: 1.71(SD 0.76)->2.77(SD 2.06), d=+1.06; GPT-5.5 MentS total: 128.74(SD 2.30)->127.70(SD 1.83), d=-1.04; 5.4-mini KPP mean: 4.04(SD 0.09)->4.96(SD 0.06), d=+0.92; Sonnet MentS total: 120.90(SD 2.33)->121.80(SD 1.55), d=+0.90; 5.4-mini TIPI C: 5.16(SD 0.37)->6.05(SD 0.37), d=+0.89; 5.4 (full) DBZ-R Avo: 4.32(SD 1.39)->3.54(SD 1.03), d=-0.77; GPT-5.5 TIPI E: 4.23(SD 0.52)->4.90(SD 0.57), d=+0.67; 5.4 (full) TIPI A: 6.97(SD 0.12)->6.30(SD 0.42), d=-0.67; Opus TIPI A: 5.64(SD 0.24)->5.00(SD 0.00), d=-0.64; 5.4-mini TIPI A: 5.32(SD 0.30)->5.90(SD 0.21), d=+0.58; 5.4-mini TIPI E: 4.48(SD 0.42)->3.95(SD 0.86), d=-0.53
[test-retest/corrected] Sonnet z-med r=0.99, TCTM r=0.83; Opus z-med r=0.99, TCTM r=0.92; 5.4-mini z-med r=0.96, TCTM r=0.42; 5.4 (full) z-med r=0.99, TCTM r=0.90; GPT-5.5 z-med r=0.99, TCTM r=0.90; Grok z-med r=0.95, TCTM r=0.88; Gemini z-med r=0.97, TCTM r=0.93
[test-retest/corrected absolute agreement] Sonnet TCTM CCC=0.82, Mdiff=+0.07, MAE=0.13, ident=87%, z-med CCC=0.99; Opus TCTM CCC=0.90, Mdiff=-0.03, MAE=0.43, ident=63%, z-med CCC=0.99; 5.4-mini TCTM CCC=0.42, Mdiff=+0.13, MAE=1.33, ident=30%, z-med CCC=0.95; 5.4 (full) TCTM CCC=0.88, Mdiff=-0.07, MAE=0.40, ident=63%, z-med CCC=0.99; GPT-5.5 TCTM CCC=0.89, Mdiff=-0.03, MAE=0.23, ident=77%, z-med CCC=0.99; Grok TCTM CCC=0.87, Mdiff=-0.30, MAE=0.97, ident=33%, z-med CCC=0.95; Gemini TCTM CCC=0.92, Mdiff=+0.03, MAE=0.63, ident=40%, z-med CCC=0.96
[masc/corrected baseline] Sonnet DOS 4.5 / NAD 0.0 / BK 0.0; Opus DOS 9.1 / NAD 0.0 / BK 0.0; 5.4-mini DOS 6.8 / NAD 1.4 / BK 5.0; 5.4 (full) DOS 0.9 / NAD 0.0 / BK 4.5; GPT-5.5 DOS 0.0 / NAD 0.9 / BK 0.0; Grok DOS 0.0 / NAD 1.4 / BK 0.5; Gemini DOS 0.0 / NAD 5.0 / BK 4.5
[zero-prompt/corrected] Sonnet n=6, TCTM M=20.83 SD=0.41; Opus n=6, TCTM M=21.00 SD=0.00; 5.4-mini n=6, TCTM M=17.83 SD=1.72; 5.4 (full) n=5, TCTM M=20.80 SD=0.45; GPT-5.5 n=6, TCTM M=22.00 SD=0.00; Grok n=6, TCTM M=21.50 SD=0.84; Gemini n=9, TCTM M=19.78 SD=0.44
[human sanity check] N=7 (from aggregate file), TCTM correct: M=14.29, SD=1.38, range 12-16 of 22
[author-target/corrected] median per-dim r: Sonnet 0.84 (min 0.76); Opus 0.85 (min 0.76); 5.4-mini 0.79 (min 0.57); 5.4 (full) 0.82 (min 0.68); GPT-5.5 0.82 (min 0.73); Grok 0.80 (min 0.57); Gemini 0.82 (min 0.72)
[cohen-kappa/corrected run1] Sonnet 0.69 [0.48,0.87]; Opus 0.78 [0.59,0.95]; 5.4-mini 0.96 [0.86,1.00]; 5.4 (full) 0.82 [0.64,0.96]; GPT-5.5 0.82 [0.64,0.96]; Grok 0.82 [0.64,0.96]; Gemini 0.78 [0.59,0.95]
[subsets/corrected] all7/explicit_n9=0.972; all7/narrative_n21=0.957; pair_54f_55/explicit_n9=0.991; pair_54f_55/narrative_n21=0.988
[openai/corrected baseline 5.4-mini] TCTM 19.10±1.10, Anx 1.69±0.39, Avo 3.02±0.32, MentS 131.0±4.7, KPP 4.964±0.063, styles: secure:10
[openai/corrected baseline 5.4 (full)] TCTM 20.80±0.42, Anx 1.48±0.91, Avo 3.54±1.03, MentS 122.9±3.8, KPP 4.922±0.045, styles: secure:5; dismissive_avoidant:4; fearful_avoidant:1
[openai/corrected baseline GPT-5.5] TCTM 21.80±0.42, Anx 1.26±0.09, Avo 3.42±0.34, MentS 127.7±1.8, KPP 4.886±0.053, styles: secure:9; dismissive_avoidant:1
[openai/initial baseline avo 5.4f-vs-5.5] g=+1.141, boot 95% CI [+0.65,+1.74], n=31/50
[openai/corrected baseline avo 5.4f-vs-5.5] g=+0.160, boot 95% CI [-0.71,+1.38], n=10/10
[openai/corrected persona avo 5.4f-vs-5.5] g=+0.007, boot 95% CI [-0.36,+0.35], n=61/61
[ola/corrected] TCTM ola-vs-overall: Sonnet 19.5 vs 21.0 (-1.5); Opus 11.0 vs 19.1 (-8.1); 5.4-mini 15.0 vs 18.3 (-3.3); 5.4 (full) 13.5 vs 20.3 (-6.8); GPT-5.5 16.5 vs 20.8 (-4.3); Grok 7.5 vs 20.0 (-12.5); Gemini 9.0 vs 19.3 (-10.3)
[ola/corrected] models classifying ola secure (run1): 7/7
[ccc/corrected pairwise] median CCC range 0.864-0.984; global min per-dim CCC 0.620 (Claude Sonnet 4.6-GPT-5.4-mini)
[consensus-reg/corrected Sonnet] slope b median 0.84 (range 0.69-0.93), |intercept a| median 0.19 (max 0.36), R2 median 0.95
[consensus-reg/corrected Opus] slope b median 0.91 (range 0.86-0.99), |intercept a| median 0.04 (max 0.40), R2 median 0.95
[consensus-reg/corrected 5.4-mini] slope b median 0.84 (range 0.72-0.97), |intercept a| median 0.13 (max 0.63), R2 median 0.94
[consensus-reg/corrected 5.4 (full)] slope b median 1.08 (range 1.04-1.27), |intercept a| median 0.08 (max 0.18), R2 median 0.97
[consensus-reg/corrected GPT-5.5] slope b median 1.11 (range 1.08-1.21), |intercept a| median 0.08 (max 0.28), R2 median 0.97
[consensus-reg/corrected Grok] slope b median 1.03 (range 0.85-1.09), |intercept a| median 0.20 (max 0.30), R2 median 0.96
[consensus-reg/corrected Gemini] slope b median 1.11 (range 0.97-1.28), |intercept a| median 0.12 (max 0.24), R2 median 0.95
[cross-collection r vs CCC] Sonnet r=0.994/CCC=0.993 (min CCC 0.97 on TIPI A); Opus r=0.991/CCC=0.990 (min CCC 0.98 on TIPI A); 5.4-mini r=0.916/CCC=0.864 (min CCC 0.56 on DBZ-R Avo); 5.4 (full) r=0.988/CCC=0.985 (min CCC 0.93 on TIPI A); GPT-5.5 r=0.994/CCC=0.993 (min CCC 0.97 on TIPI A); Grok r=0.973/CCC=0.971 (min CCC 0.85 on TIPI A); Gemini r=0.980/CCC=0.979 (min CCC 0.92 on TIPI A)
[strict-4class/corrected run1] Sonnet 23->21; Opus 25->22; 5.4-mini 29->26; 5.4 (full) 26->24; GPT-5.5 26->23; Grok 26->23; Gemini 25->23
[strict-4class] personas declared 'disorganized' in source headers: ewa, kamil, marek, radek
[unaffected-items delta] Sonnet med 0.0pp / max 26.7pp (w13); Opus med 0.0pp / max 18.3pp (w28); 5.4-mini med 4.3pp / max 51.7pp (r10); 5.4 (full) med 0.7pp / max 9.8pp (w28); GPT-5.5 med 0.0pp / max 4.9pp (w14); Grok med 1.7pp / max 11.7pp (r09); Gemini med 0.3pp / max 11.7pp (w11)
[weighting check] max |run-weighted - persona-weighted| TCTM M = 0.015 items
[mini baseline wave 1] n=10, Anx M=4.68 (SD 0.37), MentS M=101.2, KPP M=4.04, TIPI-ES M=4.65
[mini baseline wave 2] n=21, Anx M=4.69 (SD 0.26), MentS M=103.9, KPP M=4.05, TIPI-ES M=4.64
[mini baseline wave 3] n=10, Anx M=1.69 (SD 0.39), MentS M=131.0, KPP M=4.96, TIPI-ES M=6.25
[review2 spearman slopes] min pair median rho=0.907 (Pearson 0.947); 5.4f<->5.5 rho=0.971 (Pearson 0.989); median |rho - r| over 21 pairs = 0.025
[review2 slope CIs] min pairwise median r 95% CI [0.909,0.953]; 5.4f<->5.5 median r 95% CI [0.982,0.992]
[review2 author-target spearman] Sonnet rho=0.83 (r=0.84); Opus rho=0.83 (r=0.85); 5.4-mini rho=0.79 (r=0.79); 5.4 (full) rho=0.82 (r=0.82); GPT-5.5 rho=0.82 (r=0.82); Grok rho=0.74 (r=0.80); Gemini rho=0.83 (r=0.82)
[review2 persona avo g, persona-clustered bootstrap] g=+0.007, 95% CI [-0.51,+0.53]
[review2 exclusion of 4 disorganized personas] Sonnet 21/26 (kappa 0.74); Opus 22/26 (kappa 0.80); 5.4-mini 26/26 (kappa 1.00); 5.4 (full) 24/26 (kappa 0.90); GPT-5.5 23/26 (kappa 0.85); Grok 23/26 (kappa 0.85); Gemini 23/26 (kappa 0.85)
[review2 ola vs other-29 mean] Sonnet 19.5 vs 21.0 (-1.5); Opus 11.0 vs 19.4 (-8.4); 5.4-mini 15.0 vs 18.4 (-3.4); 5.4 (full) 13.5 vs 20.5 (-7.0); GPT-5.5 16.5 vs 20.9 (-4.4); Grok 7.5 vs 20.4 (-12.9); Gemini 9.0 vs 19.7 (-10.7)
[style threshold sensitivity t=3.5] matches 24-27/30, kappa 0.73-0.87
[style threshold sensitivity t=3.75] matches 25-26/30, kappa 0.78-0.82
[style threshold sensitivity t=4.0] matches 23-29/30, kappa 0.69-0.96
[style threshold sensitivity t=4.25] matches 23-27/30, kappa 0.69-0.87
[style threshold sensitivity t=4.5] matches 20-27/30, kappa 0.56-0.87
[target structure] 11-dim author-target space over 30 personas: median |r| between target dims = 0.28 (max |r| = 0.86); PCA: first component 35% of variance, participation-ratio effective dimensionality = 4.6 of 11
[target levels] distinct declared levels per dimension: min 6, max 8 (per-dim distribution in target_level_distribution.csv)
[first-administration-only agreement] 21 pairwise medians in [0.924, 0.975] (pooled-administration analysis reports [.947, .989]; single-administration agreement is not an artifact of retest averaging)
