# -*- coding: utf-8 -*-
"""
Primary analysis for the BRM submission manuscript.

PRIMARY dataset = corrected-stimulus collection:
  - Azure-hosted models (GPT-5.4-mini, GPT-5.4, GPT-5.5, Grok-4-20): wave 3
  - Bedrock/Gemini models (Sonnet, Opus, Gemini): wave 4
INITIAL collection (waves 1-2, truncated stimulus) is used ONLY for:
  (a) the natural experiment on the stimulus-rendering correction,
  (b) longitudinal stability (initial <-> corrected),
  (c) the GPT-5.4 KPP/AVO deterministic-window findings (window-2 baseline N=31).

Inputs : ../../synthetic/all_data_v20.csv, ../../synthetic/tctm57_runs_v20.csv,
         ../../synthetic/<persona>.md (author-declared styles)
Outputs: tables/*.csv + numbers.md (manifest of every statistic cited in text)
"""
from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.mixture import GaussianMixture

SEED = 20260611
np.random.seed(SEED)

HERE = Path(__file__).resolve().parent
MAGISTERKA = HERE.parents[1]
SYNTH = MAGISTERKA / "synthetic"
TABLES = HERE / "tables"
TABLES.mkdir(parents=True, exist_ok=True)

MODEL_ORDER = [
    "Claude Sonnet 4.6", "Claude Opus 4.6", "GPT-5.4-mini", "GPT-5.4",
    "GPT-5.5", "Grok-4-20", "Gemini 3 Flash",
]
SHORT = {m: s for m, s in zip(MODEL_ORDER, [
    "Sonnet", "Opus", "5.4-mini", "5.4 (full)", "GPT-5.5", "Grok", "Gemini"])}
AZURE = {"GPT-5.4-mini", "GPT-5.4", "GPT-5.5", "Grok-4-20"}
CORRECTED_WAVE = {m: (3 if m in AZURE else 4) for m in MODEL_ORDER}

Z_DIMS = ["z_anx", "z_avo", "z_ments_total", "z_kpp", "z_e", "z_a", "z_c", "z_es", "z_o"]
RAW_DIMS = ["anx_mean", "avo_mean", "ments_total", "kpp_mean",
            "tipi_e", "tipi_a", "tipi_c", "tipi_es", "tipi_o"]
DIM_LABEL = dict(zip(Z_DIMS, ["DBZ-R Anx", "DBZ-R Avo", "MentS total", "KPP mean",
                              "TIPI E", "TIPI A", "TIPI C", "TIPI ES", "TIPI O"]))
STYLES = ["secure", "anxious_preoccupied", "dismissive_avoidant", "fearful_avoidant"]
AFFECTED = ["s07", "w19", "pw07", "w22"]

PERSONAS = ['adrian', 'agata', 'ania', 'anna-sim', 'bartek', 'dominika', 'ewa', 'filip',
            'gabriela', 'hubert', 'jakub', 'jola', 'kamil', 'kasia', 'klaudia', 'kuba',
            'lukasz', 'magda', 'marek', 'michal-k', 'michal-sim', 'natalia', 'ola',
            'pawel', 'piotr', 'radek', 'sara', 'tomek', 'weronika', 'zuzia']

MANIFEST: list[str] = []


def note(line: str) -> None:
    MANIFEST.append(line)
    print(line)


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    z = stats.norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) / n) + (z * z / (4 * n * n))) / denom
    return (center - half, center + half)


def pearson(x, y) -> float:
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3:
        return float("nan")
    return float(np.corrcoef(x[mask], y[mask])[0, 1])


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    # Public release = all_data_v20_public.csv (1,156 model rows) +
    # human_pilot_aggregate.csv. The author's full working file
    # (all_data_v20.csv, +7 individual pilot rows) is used when present;
    # otherwise the script runs unchanged on the public pair, taking the
    # pilot statistics from the aggregate file (see zero_prompt_and_human).
    src = SYNTH / "all_data_v20.csv"
    if not src.exists():
        src = SYNTH / "all_data_v20_public.csv"
    df = pd.read_csv(src)
    df57 = pd.read_csv(SYNTH / "tctm57_runs_v20.csv")
    df["wave"] = df["wave"].astype(int)
    df57["wave"] = df57["wave"].astype(int)
    # collection tag for the 22-item battery
    def tag(row):
        if row["model"] == "Human":
            return "human"
        if row["wave"] in (1, 2):
            return "initial"
        if row["wave"] == CORRECTED_WAVE.get(row["model"], -1):
            return "corrected"
        return "other"
    df["collection"] = df.apply(tag, axis=1)
    return df, df57


def expected_styles() -> dict[str, str]:
    NORM = {"disorganized": "fearful_avoidant"}
    out = {}
    for p in PERSONAS:
        path = SYNTH / f"{p}.md"
        text = path.read_text(encoding="utf-8")
        m = re.search(r"attachment_style:\s*([\w_]+)", text) or re.search(r"style:\s*([a-z_]+)", text)
        assert m, f"no style in {path}"
        out[p] = NORM.get(m.group(1), m.group(1))
    return out


# ------------------------------------------------------------------
# 1. design counts
# ------------------------------------------------------------------
def design_counts(df: pd.DataFrame) -> None:
    rows = []
    for model in MODEL_ORDER:
        for coll in ["initial", "corrected"]:
            g = df[(df.model == model) & (df.collection == coll)]
            rows.append({
                "model": model, "collection": coll,
                "persona": int((g.condition == "persona").sum()),
                "baseline": int((g.condition == "baseline").sum()),
                "zero_prompt": int((g.condition == "noprompt").sum()),
            })
    pd.DataFrame(rows).to_csv(TABLES / "design_counts.csv", index=False)
    c = df[df.collection == "corrected"]
    i = df[df.collection == "initial"]
    note(f"[design] corrected rows={len(c)} (persona={int((c.condition=='persona').sum())}, "
         f"baseline={int((c.condition=='baseline').sum())}, zero-prompt={int((c.condition=='noprompt').sum())}); "
         f"initial rows={len(i)} (persona={int((i.condition=='persona').sum())}, "
         f"baseline={int((i.condition=='baseline').sum())}, zero-prompt={int((i.condition=='noprompt').sum())})")
    note(f"[design] total scored runs incl. human sanity check = {len(df)}")


# ------------------------------------------------------------------
# 2. baseline intercepts (corrected)
# ------------------------------------------------------------------
def baseline_intercepts(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in MODEL_ORDER:
        g = df[(df.model == model) & (df.condition == "baseline") & (df.collection == "corrected")]
        row = {"model": model, "n": len(g)}
        for zd, rd in zip(Z_DIMS, RAW_DIMS):
            vals = pd.to_numeric(g[zd], errors="coerce").dropna()
            raw = pd.to_numeric(g[rd], errors="coerce").dropna()
            row[f"{zd}_M"] = vals.mean()
            row[f"{zd}_SD"] = vals.std(ddof=1)
            row[f"{rd}_M"] = raw.mean()
            row[f"{rd}_SD"] = raw.std(ddof=1)
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "baseline_intercepts_corrected.csv", index=False)
    # headline contrasts
    z = out.set_index("model")
    note(f"[intercepts/corrected] Anx z: mini={z.loc['GPT-5.4-mini','z_anx_M']:+.2f} "
         f"vs 5.4(full)={z.loc['GPT-5.4','z_anx_M']:+.2f} "
         f"(gap {z.loc['GPT-5.4-mini','z_anx_M']-z.loc['GPT-5.4','z_anx_M']:.2f} SD)")
    spread = {zd: (z[f"{zd}_M"].max() - z[f"{zd}_M"].min()) for zd in Z_DIMS}
    worst = max(spread, key=spread.get)
    note(f"[intercepts/corrected] largest between-model spread: {DIM_LABEL[worst]} = {spread[worst]:.2f} z "
         f"(per-dim spreads: " + ", ".join(f"{DIM_LABEL[d]} {spread[d]:.2f}" for d in Z_DIMS) + ")")
    return out


# ------------------------------------------------------------------
# 3. persona-slope agreement (corrected, per-persona means over runs)
# ------------------------------------------------------------------
def persona_means(df: pd.DataFrame, collection: str) -> dict[str, pd.DataFrame]:
    """model -> DataFrame indexed by persona with mean z-dims over collection runs."""
    out = {}
    g = df[(df.condition == "persona") & (df.collection == collection)]
    for model in MODEL_ORDER:
        gm = g[g.model == model]
        agg = gm.groupby("persona")[Z_DIMS + RAW_DIMS + ["tctm_correct"]].mean(numeric_only=True)
        out[model] = agg
    return out


def slope_correlations(df: pd.DataFrame) -> pd.DataFrame:
    pm = persona_means(df, "corrected")
    rows = []
    med = np.full((7, 7), np.nan)
    for i, m1 in enumerate(MODEL_ORDER):
        for j, m2 in enumerate(MODEL_ORDER):
            if i == j:
                med[i, j] = 1.0
                continue
            common = pm[m1].index.intersection(pm[m2].index)
            rs = {d: pearson(pm[m1].loc[common, d], pm[m2].loc[common, d]) for d in Z_DIMS}
            med[i, j] = float(np.nanmedian(list(rs.values())))
            rows.append({"model_1": m1, "model_2": m2, "n_personas": len(common),
                         "median_r": med[i, j],
                         "min_r": float(np.nanmin(list(rs.values()))),
                         "max_r": float(np.nanmax(list(rs.values()))),
                         **{f"r_{d}": v for d, v in rs.items()}})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "slope_correlations_corrected.csv", index=False)

    pairs = out[out.model_1 < out.model_2]
    six = [m for m in MODEL_ORDER if m != "GPT-5.4-mini"]
    cl = pairs[pairs.model_1.isin(six) & pairs.model_2.isin(six)]
    p55 = out[(out.model_1 == "GPT-5.4") & (out.model_2 == "GPT-5.5")].iloc[0]
    mini = pairs[(pairs.model_1 == "GPT-5.4-mini") | (pairs.model_2 == "GPT-5.4-mini")]
    note(f"[slopes/corrected] 6-model cluster median r range: {cl.median_r.min():.3f}-{cl.median_r.max():.3f} "
         f"(median of medians {cl.median_r.median():.3f})")
    note(f"[slopes/corrected] 5.4(full)<->5.5 median r = {p55.median_r:.3f} "
         f"(min {p55.min_r:.3f}, max {p55.max_r:.3f}) — per-dim: "
         + ", ".join(f"{DIM_LABEL[d]} {p55[f'r_{d}']:.2f}" for d in Z_DIMS))
    note(f"[slopes/corrected] mini vs others median r range: {mini.median_r.min():.3f}-{mini.median_r.max():.3f}")
    return out


# ------------------------------------------------------------------
# 4. style classification fidelity (corrected run 1) + Fleiss kappa
# ------------------------------------------------------------------
def fleiss_kappa(table: np.ndarray) -> float:
    """table: subjects x categories counts (raters per subject constant)."""
    n_sub, _ = table.shape
    n_rat = table.sum(axis=1)[0]
    p_j = table.sum(axis=0) / (n_sub * n_rat)
    p_i = ((table ** 2).sum(axis=1) - n_rat) / (n_rat * (n_rat - 1))
    p_bar = p_i.mean()
    p_e = (p_j ** 2).sum()
    if p_e >= 1.0:
        return float("nan")
    return float((p_bar - p_e) / (1 - p_e))


def style_fidelity(df: pd.DataFrame, expected: dict[str, str]) -> pd.DataFrame:
    g = df[(df.condition == "persona") & (df.collection == "corrected") & (df.run == 1)]
    rows = []
    style_mat = {}  # persona -> {model: style}
    for model in MODEL_ORDER:
        gm = g[g.model == model].set_index("persona")
        k = sum(1 for p in PERSONAS if p in gm.index and gm.loc[p, "style"] == expected[p])
        n = sum(1 for p in PERSONAS if p in gm.index)
        lo, hi = wilson_ci(k, n)
        rows.append({"model": model, "matches": k, "n": n, "accuracy": k / n,
                     "wilson_lo": lo, "wilson_hi": hi})
        for p in PERSONAS:
            if p in gm.index:
                style_mat.setdefault(p, {})[model] = gm.loc[p, "style"]
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "style_fidelity_corrected.csv", index=False)
    note("[fidelity/corrected run1] " + "; ".join(
        f"{SHORT[r.model]} {r.matches}/{r.n}" for r in out.itertuples()))

    # persona-level matrix (+ how many of 7 match)
    mat_rows = []
    for p in PERSONAS:
        row = {"persona": p, "expected": expected[p]}
        for model in MODEL_ORDER:
            row[SHORT[model]] = style_mat.get(p, {}).get(model, "")
        row["matches_of_7"] = sum(1 for model in MODEL_ORDER
                                  if style_mat.get(p, {}).get(model) == expected[p])
        mat_rows.append(row)
    mat = pd.DataFrame(mat_rows)
    mat.to_csv(TABLES / "style_matrix_corrected_run1.csv", index=False)
    hard = mat[mat.matches_of_7 <= 4][["persona", "expected", "matches_of_7"]]
    note(f"[fidelity/corrected] personas with <=4/7 models matching: "
         + (", ".join(f"{r.persona}({r.expected},{r.matches_of_7})" for r in hard.itertuples()) or "none"))
    perfect = int((mat.matches_of_7 == 7).sum())
    note(f"[fidelity/corrected] personas with 7/7 unanimous correct: {perfect}/30")

    # Fleiss kappa across raters (7 and 6 without mini), bootstrap CI over personas
    def kappa_for(models: list[str]) -> tuple[float, float, float]:
        tab = np.zeros((len(PERSONAS), len(STYLES)), int)
        for i, p in enumerate(PERSONAS):
            for model in models:
                s = style_mat.get(p, {}).get(model)
                if s in STYLES:
                    tab[i, STYLES.index(s)] += 1
        assert (tab.sum(axis=1) == len(models)).all()
        k = fleiss_kappa(tab)
        boots = []
        rng = np.random.default_rng(SEED)
        for _ in range(2000):
            idx = rng.integers(0, len(PERSONAS), len(PERSONAS))
            boots.append(fleiss_kappa(tab[idx]))
        lo, hi = np.nanpercentile(boots, [2.5, 97.5])
        return k, float(lo), float(hi)

    k7, lo7, hi7 = kappa_for(MODEL_ORDER)
    six = [m for m in MODEL_ORDER if m != "GPT-5.4-mini"]
    k6, lo6, hi6 = kappa_for(six)
    pd.DataFrame([
        {"raters": "7 models", "fleiss_kappa": k7, "ci_lo": lo7, "ci_hi": hi7},
        {"raters": "6 models (excl. 5.4-mini)", "fleiss_kappa": k6, "ci_lo": lo6, "ci_hi": hi6},
    ]).to_csv(TABLES / "fleiss_kappa_corrected.csv", index=False)
    note(f"[fidelity/corrected] Fleiss kappa 7 models = {k7:.3f} [{lo7:.2f}, {hi7:.2f}]; "
         f"6 models (excl. mini) = {k6:.3f} [{lo6:.2f}, {hi6:.2f}]")

    # cross-run style agreement within corrected collection
    g2 = df[(df.condition == "persona") & (df.collection == "corrected") & (df.run.isin([1, 2]))]
    agree_rows = []
    for model in MODEL_ORDER:
        w = g2[g2.model == model].pivot_table(index="persona", columns="run",
                                              values="style", aggfunc="first")
        ok = int((w[1] == w[2]).sum())
        n = int(w[[1, 2]].dropna().shape[0])
        agree_rows.append({"model": model, "style_agree": ok, "n": n})
    pd.DataFrame(agree_rows).to_csv(TABLES / "style_run_agreement_corrected.csv", index=False)
    note("[fidelity/corrected run1-vs-run2 agreement] " + "; ".join(
        f"{SHORT[r['model']]} {r['style_agree']}/{r['n']}" for r in agree_rows))
    return out


# ------------------------------------------------------------------
# 5. TCTM totals + item analysis (corrected)
# ------------------------------------------------------------------
def item_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("tctm_") and c not in ("tctm_correct", "tctm_total")]


def tctm_totals(df: pd.DataFrame) -> None:
    rows = []
    for model in MODEL_ORDER:
        for cond in ["persona", "baseline", "noprompt"]:
            g = df[(df.model == model) & (df.condition == cond) & (df.collection == "corrected")]
            if g.empty:
                continue
            tot = g.tctm_total.astype(int).sum()
            cor = g.tctm_correct.astype(int).sum()
            rows.append({"model": model, "condition": cond, "n_runs": len(g),
                         "pct_correct": 100 * cor / tot,
                         "mean_correct": g.tctm_correct.mean(),
                         "sd_correct": g.tctm_correct.std(ddof=1)})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "tctm_totals_corrected.csv", index=False)
    pers = out[out.condition == "persona"].set_index("model")
    note("[tctm/corrected persona totals] " + "; ".join(
        f"{SHORT[m]} {pers.loc[m,'pct_correct']:.1f}% (M={pers.loc[m,'mean_correct']:.2f}, SD={pers.loc[m,'sd_correct']:.2f})"
        for m in MODEL_ORDER))
    base = out[out.condition == "baseline"].set_index("model")
    note("[tctm/corrected baseline totals] " + "; ".join(
        f"{SHORT[m]} M={base.loc[m,'mean_correct']:.2f} SD={base.loc[m,'sd_correct']:.2f}" for m in MODEL_ORDER))


def item_analysis(df: pd.DataFrame) -> None:
    items = item_cols(df)
    rows = []
    for model in MODEL_ORDER:
        g = df[(df.model == model) & (df.condition == "persona") & (df.collection == "corrected")]
        for it in items:
            vals = pd.to_numeric(g[it], errors="coerce").dropna()
            rows.append({"model": model, "item": it.replace("tctm_", ""),
                         "n": len(vals), "accuracy": vals.mean() if len(vals) else np.nan})
    acc = pd.DataFrame(rows)
    acc.to_csv(TABLES / "item_accuracy_corrected.csv", index=False)
    grand = acc.groupby("item").apply(
        lambda x: np.average(x.accuracy, weights=x.n), include_groups=False).sort_values()
    note(f"[items/corrected] hardest 5 items (pooled): "
         + ", ".join(f"{i} {v:.0%}" for i, v in grand.head(5).items()))
    note(f"[items/corrected] easiest 5 items (pooled): "
         + ", ".join(f"{i} {v:.0%}" for i, v in grand.tail(5).items()))

    # Cochran's Q across 7 models, corrected run 1, BH-FDR
    g1 = df[(df.condition == "persona") & (df.collection == "corrected") & (df.run == 1)]
    qrows = []
    for it in items:
        wide = g1.pivot_table(index="persona", columns="model", values=it, aggfunc="first")
        if not all(m in wide.columns for m in MODEL_ORDER):
            continue
        mat = wide[MODEL_ORDER].dropna().to_numpy(float)
        k = mat.shape[1]
        c = mat.sum(axis=0)
        r = mat.sum(axis=1)
        denom = k * c.sum() - np.sum(r * r)
        if denom <= 0:
            q, p = float("nan"), float("nan")
        else:
            q = (k - 1) * (k * np.sum(c * c) - c.sum() ** 2) / denom
            p = stats.chi2.sf(q, k - 1)
        qrows.append({"item": it.replace("tctm_", ""), "n_personas": mat.shape[0],
                      "cochran_q": q, "p": p})
    qtab = pd.DataFrame(qrows).dropna(subset=["p"])
    p = qtab.p.to_numpy()
    order = np.argsort(p)
    qvals = np.empty_like(p)
    prev = 1.0
    n = len(p)
    for rank, idx in enumerate(order[::-1], start=1):
        true_rank = n - rank + 1
        prev = min(prev, p[idx] * n / true_rank)
        qvals[idx] = prev
    qtab["p_fdr_bh"] = qvals
    qtab = qtab.sort_values("cochran_q", ascending=False)
    qtab.to_csv(TABLES / "item_heterogeneity_cochranq_corrected.csv", index=False)
    sig = int((qtab.p_fdr_bh < 0.05).sum())
    top = qtab.iloc[0]
    note(f"[items/corrected] Cochran Q: {sig}/{len(qtab)} items FDR-significant across models; "
         f"largest {top['item']} Q={top.cochran_q:.1f}, q={top.p_fdr_bh:.2g}")


# ------------------------------------------------------------------
# 6. natural experiment: truncated vs corrected on affected items
# ------------------------------------------------------------------
def natural_experiment(df: pd.DataFrame) -> None:
    rows = []
    for model in MODEL_ORDER:
        for it in AFFECTED:
            col = f"tctm_{it}"
            r = {"model": model, "item": it}
            for coll in ["initial", "corrected"]:
                g = df[(df.model == model) & (df.condition == "persona") & (df.collection == coll)]
                vals = pd.to_numeric(g[col], errors="coerce").dropna()
                k, n = int(vals.sum()), len(vals)
                lo, hi = wilson_ci(k, n)
                r[f"{coll}_k"] = k
                r[f"{coll}_n"] = n
                r[f"{coll}_pct"] = 100 * k / n if n else np.nan
                r[f"{coll}_lo"] = 100 * lo
                r[f"{coll}_hi"] = 100 * hi
            r["delta_pp"] = r["corrected_pct"] - r["initial_pct"]
            rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "natural_experiment_items.csv", index=False)
    for it in AFFECTED:
        seg = out[out.item == it]
        note(f"[natural-exp {it}] " + "; ".join(
            f"{SHORT[r.model]} {r.initial_pct:.1f}->{r.corrected_pct:.1f} ({r.delta_pp:+.1f}pp)"
            for r in seg.itertuples()))

    # per-model total stability (paired per persona means)
    trows = []
    pm_i = persona_means(df, "initial")
    pm_c = persona_means(df, "corrected")
    for model in MODEL_ORDER:
        common = pm_i[model].index.intersection(pm_c[model].index)
        di = pm_c[model].loc[common, "tctm_correct"] - pm_i[model].loc[common, "tctm_correct"]
        trows.append({"model": model, "n_personas": len(common),
                      "mean_delta_items": di.mean(), "sd_delta": di.std(ddof=1)})
    tout = pd.DataFrame(trows)
    tout.to_csv(TABLES / "natural_experiment_totals.csv", index=False)
    note("[natural-exp totals] per-persona TCTM delta (corrected-initial): " + "; ".join(
        f"{SHORT[r.model]} {r.mean_delta_items:+.2f}" for r in tout.itertuples()))


# ------------------------------------------------------------------
# 7. administration-context 2x2 (22- vs 57-item battery)
# ------------------------------------------------------------------
def admin_context(df: pd.DataFrame, df57: pd.DataFrame) -> None:
    models = ["Claude Sonnet 4.6", "GPT-5.5"]
    items = ["s07", "w19", "w22"]
    rows = []
    for model in models:
        for it in items:
            col = f"tctm_{it}"
            r = {"model": model, "item": it}
            # 22-item battery
            for coll, label in [("initial", "b22_truncated"), ("corrected", "b22_corrected")]:
                g = df[(df.model == model) & (df.condition == "persona") & (df.collection == coll)]
                vals = pd.to_numeric(g[col], errors="coerce").dropna()
                r[f"{label}_k"], r[f"{label}_n"] = int(vals.sum()), len(vals)
                r[f"{label}_pct"] = 100 * vals.mean() if len(vals) else np.nan
            # 57-item battery: wave 1 = truncated, wave 5 = corrected
            for waves, label in [({1}, "b57_truncated"), ({5}, "b57_corrected")]:
                g = df57[(df57.model == model) & (df57.wave.isin(waves))]
                vals = pd.to_numeric(g[col], errors="coerce").dropna()
                r[f"{label}_k"], r[f"{label}_n"] = int(vals.sum()), len(vals)
                r[f"{label}_pct"] = 100 * vals.mean() if len(vals) else np.nan
            rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "admin_context_2x2.csv", index=False)
    for r in out.itertuples():
        note(f"[admin-context {SHORT[r.model]} {r.item}] battery22 trunc {r.b22_truncated_pct:.1f}% "
             f"(n={r.b22_truncated_n}) vs corr {r.b22_corrected_pct:.1f}% (n={r.b22_corrected_n}); "
             f"battery57 trunc {r.b57_truncated_pct:.1f}% (n={r.b57_truncated_n}) "
             f"vs corr {r.b57_corrected_pct:.1f}% (n={r.b57_corrected_n})")


# ------------------------------------------------------------------
# 8. determinism: zero-variance cells + KPP event + AVO bimodality
# ------------------------------------------------------------------
def determinism(df: pd.DataFrame) -> None:
    metrics = RAW_DIMS + ["tctm_correct"]
    rows = []
    for model in MODEL_ORDER:
        for cond in ["baseline", "noprompt"]:
            for coll in ["initial", "corrected"]:
                g = df[(df.model == model) & (df.condition == cond) & (df.collection == coll)]
                if len(g) < 3:
                    continue
                for met in metrics:
                    vals = pd.to_numeric(g[met], errors="coerce").dropna()
                    if len(vals) >= 3 and vals.std(ddof=1) == 0:
                        rows.append({"model": model, "condition": cond, "collection": coll,
                                     "metric": met, "n": len(vals), "value": vals.iloc[0]})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "zero_variance_cells.csv", index=False)
    note("[determinism] zero-variance cells (n>=3): " + "; ".join(
        f"{SHORT[r.model]}/{r.condition}/{r.collection}/{r.metric}={r.value:g}(n={r.n})"
        for r in out.itertuples()))

    # KPP event: 5.4(full) baseline by collection
    for coll in ["initial", "corrected"]:
        g = df[(df.model == "GPT-5.4") & (df.condition == "baseline") & (df.collection == coll)]
        vals = pd.to_numeric(g.kpp_mean, errors="coerce").dropna()
        note(f"[kpp 5.4(full) baseline/{coll}] n={len(vals)}, M={vals.mean():.4f}, SD={vals.std(ddof=1):.4f}, "
             f"unique={sorted(vals.unique())[:5]}{'...' if vals.nunique()>5 else ''}")

    # AVO bimodality: initial window (N=31) GMM + bootstrap LRT; corrected n=10 split
    vals = pd.to_numeric(
        df[(df.model == "GPT-5.4") & (df.condition == "baseline") & (df.collection == "initial")].avo_mean,
        errors="coerce").dropna().to_numpy()
    x = np.sort(vals).reshape(-1, 1)
    gm1 = GaussianMixture(1, random_state=SEED, n_init=50).fit(x)
    gm2 = GaussianMixture(2, random_state=SEED, n_init=50).fit(x)
    lrt_obs = 2 * (gm2.score(x) - gm1.score(x)) * len(vals)
    rng = np.random.default_rng(SEED)
    boots = []
    for i in range(500):
        sim = rng.normal(vals.mean(), vals.std(ddof=1), len(vals)).reshape(-1, 1)
        b1 = GaussianMixture(1, random_state=SEED + i, n_init=10).fit(sim)
        b2 = GaussianMixture(2, random_state=SEED + i, n_init=10).fit(sim)
        boots.append(2 * (b2.score(sim) - b1.score(sim)) * len(sim))
    p_boot = (sum(b >= lrt_obs for b in boots) + 1) / 501
    gaps = np.diff(np.sort(vals))
    gi = int(np.argmax(gaps))
    lower = vals[vals < 4]
    upper = vals[vals >= 4]
    pd.DataFrame([{
        "n": len(vals), "mean": vals.mean(), "sd": vals.std(ddof=1),
        "bic_1": gm1.bic(x), "bic_2": gm2.bic(x), "lrt": lrt_obs, "p_bootstrap": p_boot,
        "largest_gap": gaps[gi], "gap_lo": np.sort(vals)[gi], "gap_hi": np.sort(vals)[gi + 1],
        "n_below_4": len(lower), "n_above_4": len(upper),
        "lower_mean": lower.mean(), "upper_mean": upper.mean(),
    }]).to_csv(TABLES / "avo_bimodality_initial.csv", index=False)
    note(f"[avo-bimodality 5.4(full) baseline initial] N={len(vals)}, BIC1={gm1.bic(x):.1f} vs BIC2={gm2.bic(x):.1f}, "
         f"bootstrap LRT p={p_boot:.4f}; gap {gaps[gi]:.3f} in [{np.sort(vals)[gi]:.2f},{np.sort(vals)[gi+1]:.2f}]; "
         f"{len(lower)} below / {len(upper)} above 4; cluster means {lower.mean():.2f}/{upper.mean():.2f}")
    cvals = pd.to_numeric(
        df[(df.model == "GPT-5.4") & (df.condition == "baseline") & (df.collection == "corrected")].avo_mean,
        errors="coerce").dropna().to_numpy()
    note(f"[avo-bimodality corrected n={len(cvals)}] values sorted: "
         + ", ".join(f"{v:.2f}" for v in np.sort(cvals))
         + f"; {np.sum(cvals < 4)} below / {np.sum(cvals >= 4)} above 4")


# ------------------------------------------------------------------
# 9. longitudinal: initial <-> corrected
# ------------------------------------------------------------------
def longitudinal(df: pd.DataFrame, expected: dict[str, str]) -> None:
    pm_i = persona_means(df, "initial")
    pm_c = persona_means(df, "corrected")
    rows = []
    for model in MODEL_ORDER:
        common = pm_i[model].index.intersection(pm_c[model].index)
        rs = {d: pearson(pm_i[model].loc[common, d], pm_c[model].loc[common, d]) for d in Z_DIMS}
        rows.append({"model": model, "weeks_apart": 8 if model not in AZURE else
                     (0.5 if model == "GPT-5.4" else 7),
                     "n_personas": len(common),
                     "median_r": float(np.nanmedian(list(rs.values()))),
                     "min_r": float(np.nanmin(list(rs.values()))),
                     **{f"r_{d}": v for d, v in rs.items()}})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "longitudinal_slope_stability.csv", index=False)
    note("[longitudinal slopes initial<->corrected] " + "; ".join(
        f"{SHORT[r.model]} med r={r.median_r:.3f} (min {r.min_r:.3f})" for r in out.itertuples()))

    # style agreement initial run1 vs corrected run1
    g = df[(df.condition == "persona") & (df.run == 1)]
    arow = []
    for model in MODEL_ORDER:
        gi = g[(g.model == model) & (g.collection == "initial")].set_index("persona")["style"]
        gc = g[(g.model == model) & (g.collection == "corrected")].set_index("persona")["style"]
        common = gi.index.intersection(gc.index)
        arow.append({"model": model, "agree": int((gi[common] == gc[common]).sum()), "n": len(common)})
    pd.DataFrame(arow).to_csv(TABLES / "longitudinal_style_agreement.csv", index=False)
    note("[longitudinal style run1<->run1] " + "; ".join(
        f"{SHORT[r['model']]} {r['agree']}/{r['n']}" for r in arow))

    # baseline intercept drift per model per dim (z-scale), all models
    drows = []
    for model in MODEL_ORDER:
        gi = df[(df.model == model) & (df.condition == "baseline") & (df.collection == "initial")]
        gc = df[(df.model == model) & (df.condition == "baseline") & (df.collection == "corrected")]
        for zd, rd in zip(Z_DIMS, RAW_DIMS):
            vi = pd.to_numeric(gi[rd], errors="coerce").dropna()
            vc = pd.to_numeric(gc[rd], errors="coerce").dropna()
            zi = pd.to_numeric(gi[zd], errors="coerce").dropna()
            zc = pd.to_numeric(gc[zd], errors="coerce").dropna()
            drows.append({"model": model, "dim": DIM_LABEL[zd],
                          "initial_M": vi.mean(), "initial_SD": vi.std(ddof=1), "n_i": len(vi),
                          "corrected_M": vc.mean(), "corrected_SD": vc.std(ddof=1), "n_c": len(vc),
                          "delta_raw": vc.mean() - vi.mean(),
                          "delta_z": zc.mean() - zi.mean()})
    dout = pd.DataFrame(drows)
    dout.to_csv(TABLES / "longitudinal_baseline_drift.csv", index=False)
    big = dout[dout.delta_raw.abs() > 0.5].sort_values("delta_raw", key=abs, ascending=False)
    note("[longitudinal baseline drift |delta raw|>0.5] " + ("; ".join(
        f"{SHORT[r.model]} {r.dim}: {r.initial_M:.2f}(SD {r.initial_SD:.2f})->{r.corrected_M:.2f}"
        f"(SD {r.corrected_SD:.2f}), d={r.delta_raw:+.2f}" for r in big.itertuples()) or "none"))


# ------------------------------------------------------------------
# 10. test-retest within corrected collection
# ------------------------------------------------------------------
def test_retest(df: pd.DataFrame) -> None:
    g = df[(df.condition == "persona") & (df.collection == "corrected") & (df.run.isin([1, 2]))]
    rows = []
    for model in MODEL_ORDER:
        gm = g[g.model == model]
        w = gm.pivot_table(index="persona", columns="run", values="tctm_correct", aggfunc="first")
        r_tctm = pearson(w[1], w[2])
        # Absolute-agreement companions to r (r tracks ordering only; near a
        # ceiling it can be low despite tiny point differences).
        pair = w.dropna()
        diff = pair[2] - pair[1]
        ccc_tctm = ccc(pair[1], pair[2])
        mean_diff = float(diff.mean())
        mae = float(diff.abs().mean())
        pct_identical = float((diff == 0).mean())
        zrs, zcccs = [], []
        for d in Z_DIMS:
            wd = gm.pivot_table(index="persona", columns="run", values=d, aggfunc="first")
            zrs.append(pearson(wd[1], wd[2]))
            zcccs.append(ccc(wd.dropna()[1], wd.dropna()[2]))
        rows.append({"model": model, "tctm_r": r_tctm,
                     "tctm_ccc": ccc_tctm, "tctm_mean_diff": mean_diff,
                     "tctm_mae": mae, "tctm_pct_identical": pct_identical,
                     "median_z_r": float(np.nanmedian(zrs)),
                     "min_z_r": float(np.nanmin(zrs)),
                     "median_z_ccc": float(np.nanmedian(zcccs)),
                     "min_z_ccc": float(np.nanmin(zcccs)),
                     **{f"r_{d}": v for d, v in zip(Z_DIMS, zrs)}})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "test_retest_corrected.csv", index=False)
    note("[test-retest/corrected] " + "; ".join(
        f"{SHORT[r.model]} z-med r={r.median_z_r:.2f}, TCTM r={r.tctm_r:.2f}" for r in out.itertuples()))
    note("[test-retest/corrected absolute agreement] " + "; ".join(
        f"{SHORT[r.model]} TCTM CCC={r.tctm_ccc:.2f}, Mdiff={r.tctm_mean_diff:+.2f}, "
        f"MAE={r.tctm_mae:.2f}, ident={r.tctm_pct_identical:.0%}, z-med CCC={r.median_z_ccc:.2f}"
        for r in out.itertuples()))


# ------------------------------------------------------------------
# 11. MASC error fingerprint (corrected)
# ------------------------------------------------------------------
def masc_fingerprint(df: pd.DataFrame) -> None:
    rows = []
    for model in MODEL_ORDER:
        for cond in ["persona", "baseline"]:
            g = df[(df.model == model) & (df.condition == cond) & (df.collection == "corrected")]
            tot = g.tctm_total.astype(int).sum()
            rows.append({"model": model, "condition": cond, "n_runs": len(g),
                         "correct_pct": 100 * g.tctm_correct.astype(int).sum() / tot,
                         "dos_pct": 100 * pd.to_numeric(g.dos, errors="coerce").sum() / tot,
                         "nad_pct": 100 * pd.to_numeric(g.nad, errors="coerce").sum() / tot,
                         "bk_pct": 100 * pd.to_numeric(g.bk, errors="coerce").sum() / tot})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "masc_fingerprint_corrected.csv", index=False)
    b = out[out.condition == "baseline"].set_index("model")
    note("[masc/corrected baseline] " + "; ".join(
        f"{SHORT[m]} DOS {b.loc[m,'dos_pct']:.1f} / NAD {b.loc[m,'nad_pct']:.1f} / BK {b.loc[m,'bk_pct']:.1f}"
        for m in MODEL_ORDER))


# ------------------------------------------------------------------
# 12. zero-prompt condition (corrected) + human sanity check
# ------------------------------------------------------------------
def zero_prompt_and_human(df: pd.DataFrame) -> None:
    rows = []
    for model in MODEL_ORDER:
        g = df[(df.model == model) & (df.condition == "noprompt") & (df.collection == "corrected")]
        rows.append({"model": model, "n_scored": len(g),
                     "tctm_mean": g.tctm_correct.mean(), "tctm_sd": g.tctm_correct.std(ddof=1),
                     "anx_mean": pd.to_numeric(g.anx_mean, errors="coerce").mean(),
                     "avo_mean": pd.to_numeric(g.avo_mean, errors="coerce").mean()})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "zero_prompt_corrected.csv", index=False)
    note("[zero-prompt/corrected] " + "; ".join(
        f"{SHORT[r.model]} n={r.n_scored}, TCTM M={r.tctm_mean:.2f} SD={r.tctm_sd:.2f}" for r in out.itertuples()))

    h = df[df.model == "Human"]
    if len(h) > 0:
        vals = h.tctm_correct.astype(int)
        note(f"[human sanity check] N={len(h)}, TCTM correct: M={vals.mean():.2f}, SD={vals.std(ddof=1):.2f}, "
             f"range {vals.min()}-{vals.max()} of 22")
    else:
        # Public release: individual pilot records are not distributed —
        # read the published aggregate instead.
        agg = pd.read_csv(SYNTH / "human_pilot_aggregate.csv").set_index("statistic")["value"]
        note(f"[human sanity check] N={agg['n_respondents']} (from aggregate file), TCTM correct: "
             f"M={agg['tctm22_total_mean']}, SD={agg['tctm22_total_sd']}, "
             f"range {agg['tctm22_total_min']}-{agg['tctm22_total_max']} of 22")


# ------------------------------------------------------------------
# 13. author-target agreement, Cohen's kappa, subsets, OpenAI contrast, ola
# ------------------------------------------------------------------
LEVEL_RANK = {
    "very_low": -2, "low": -1, "low_moderate": -0.5, "moderate_low": -0.5,
    "moderate": 0, "moderate_high": 0.5, "high": 1, "very_high": 2, "extreme": 2.5,
}
EXPECT_KEYS = {  # frontmatter key -> z column (MentS total handled separately)
    "dbz_anxiety": "z_anx", "dbz_avoidance": "z_avo", "kpp": "z_kpp",
    "tipi_E": "z_e", "tipi_A": "z_a", "tipi_C": "z_c", "tipi_ES": "z_es",
    "tipi_O": "z_o",
}
EXPLICIT = {"ania", "anna-sim", "filip", "jakub", "kamil", "marek", "natalia",
            "ola", "tomek"}


def author_targets() -> dict[str, dict[str, float]]:
    """persona -> {z_dim: ordinal author target}; ments total = mean of 3 subscales."""
    out = {}
    for p in PERSONAS:
        text = (SYNTH / f"{p}.md").read_text(encoding="utf-8")
        vals = dict(re.findall(r"^\s{2}(\w+):\s*([\w_]+)\s*$", text.split("---")[1],
                               re.MULTILINE))
        t = {}
        for k, zc in EXPECT_KEYS.items():
            t[zc] = LEVEL_RANK[vals[k]]
        t["z_ments_total"] = float(np.mean([LEVEL_RANK[vals[k]] for k in
                                            ("ments_self", "ments_other", "ments_motivation")]))
        out[p] = t
    return out


def cohen_kappa(a: list[str], b: list[str]) -> float:
    cats = sorted(set(a) | set(b))
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    if pe >= 1.0:
        return float("nan")
    return (po - pe) / (1 - pe)


def extras(df: pd.DataFrame, expected: dict[str, str]) -> None:
    pm = persona_means(df, "corrected")
    targets = author_targets()

    # author-target agreement: per model per dim r (n=30), median over 9 dims
    rows = []
    for model in MODEL_ORDER:
        rs = {}
        for d in Z_DIMS:
            xs = [targets[p][d] for p in PERSONAS]
            ys = [pm[model].loc[p, d] if p in pm[model].index else np.nan for p in PERSONAS]
            rs[d] = pearson(xs, ys)
        rows.append({"model": model, "median_r": float(np.nanmedian(list(rs.values()))),
                     "min_r": float(np.nanmin(list(rs.values()))),
                     "max_r": float(np.nanmax(list(rs.values()))),
                     **{f"r_{d}": v for d, v in rs.items()}})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "author_target_agreement_corrected.csv", index=False)
    note("[author-target/corrected] median per-dim r: " + "; ".join(
        f"{SHORT[r.model]} {r.median_r:.2f} (min {r.min_r:.2f})" for r in out.itertuples()))

    # Cohen's kappa per model (style, corrected run 1) + percentile bootstrap CI
    g1 = df[(df.condition == "persona") & (df.collection == "corrected") & (df.run == 1)]
    rng = np.random.default_rng(SEED)
    krows = []
    for model in MODEL_ORDER:
        gm = g1[g1.model == model].set_index("persona")
        pl = [p for p in PERSONAS if p in gm.index]
        a = [expected[p] for p in pl]
        b = [gm.loc[p, "style"] for p in pl]
        k = cohen_kappa(a, b)
        boots = []
        for _ in range(5000):
            idx = rng.integers(0, len(pl), len(pl))
            boots.append(cohen_kappa([a[i] for i in idx], [b[i] for i in idx]))
        lo, hi = np.nanpercentile(boots, [2.5, 97.5])
        krows.append({"model": model, "kappa": k, "ci_lo": lo, "ci_hi": hi})
    kout = pd.DataFrame(krows)
    kout.to_csv(TABLES / "cohen_kappa_corrected.csv", index=False)
    note("[cohen-kappa/corrected run1] " + "; ".join(
        f"{SHORT[r.model]} {r.kappa:.2f} [{r.ci_lo:.2f},{r.ci_hi:.2f}]" for r in kout.itertuples()))

    # explicit vs narrative-only subset slope correlations
    def subset_median(models: list[str], personas: set[str]) -> float:
        meds = []
        for i, m1 in enumerate(models):
            for m2 in models[i + 1:]:
                common = [p for p in pm[m1].index.intersection(pm[m2].index) if p in personas]
                rs = [pearson(pm[m1].loc[common, d], pm[m2].loc[common, d]) for d in Z_DIMS]
                meds.append(float(np.nanmedian(rs)))
        return float(np.median(meds))

    narrative = set(PERSONAS) - EXPLICIT
    sub_rows = []
    for label, models in [("all7", MODEL_ORDER),
                          ("pair_54f_55", ["GPT-5.4", "GPT-5.5"])]:
        for sname, pset in [("explicit_n9", EXPLICIT), ("narrative_n21", narrative)]:
            sub_rows.append({"models": label, "subset": sname,
                             "median_of_pairwise_medians": subset_median(models, pset)})
    sout = pd.DataFrame(sub_rows)
    sout.to_csv(TABLES / "subset_slopes_corrected.csv", index=False)
    note("[subsets/corrected] " + "; ".join(
        f"{r.models}/{r.subset}={r.median_of_pairwise_medians:.3f}" for r in sout.itertuples()))

    # OpenAI corrected baseline contrast (raw scale) + persona-conditioned avo g
    orows = []
    for model in ["GPT-5.4-mini", "GPT-5.4", "GPT-5.5"]:
        g = df[(df.model == model) & (df.condition == "baseline") & (df.collection == "corrected")]
        styles = g["style"].value_counts().to_dict()
        orows.append({"model": model, "n": len(g),
                      "tctm_M": g.tctm_correct.mean(), "tctm_SD": g.tctm_correct.std(ddof=1),
                      "anx_M": g.anx_mean.mean(), "anx_SD": g.anx_mean.std(ddof=1),
                      "avo_M": g.avo_mean.mean(), "avo_SD": g.avo_mean.std(ddof=1),
                      "ments_M": g.ments_total.mean(), "ments_SD": g.ments_total.std(ddof=1),
                      "kpp_M": g.kpp_mean.mean(), "kpp_SD": g.kpp_mean.std(ddof=1),
                      "styles": "; ".join(f"{k}:{v}" for k, v in styles.items())})
    oout = pd.DataFrame(orows)
    oout.to_csv(TABLES / "openai_baseline_corrected.csv", index=False)
    for r in oout.itertuples():
        note(f"[openai/corrected baseline {SHORT[r.model]}] TCTM {r.tctm_M:.2f}±{r.tctm_SD:.2f}, "
             f"Anx {r.anx_M:.2f}±{r.anx_SD:.2f}, Avo {r.avo_M:.2f}±{r.avo_SD:.2f}, "
             f"MentS {r.ments_M:.1f}±{r.ments_SD:.1f}, KPP {r.kpp_M:.3f}±{r.kpp_SD:.3f}, styles: {r.styles}")

    def hedges_g(x: np.ndarray, y: np.ndarray) -> float:
        nx, ny = len(x), len(y)
        sp = math.sqrt(((nx - 1) * x.std(ddof=1) ** 2 + (ny - 1) * y.std(ddof=1) ** 2)
                       / (nx + ny - 2))
        d = (x.mean() - y.mean()) / sp
        return d * (1 - 3 / (4 * (nx + ny) - 9))

    # Initial-window contrast cited in the manuscript (g = 1.15 [0.66, 1.75]):
    # recomputed here so every in-text statistic traces to this script.
    xi = df[(df.model == "GPT-5.4") & (df.condition == "baseline")
            & (df.collection == "initial")].avo_mean.to_numpy(float)
    yi = df[(df.model == "GPT-5.5") & (df.condition == "baseline")
            & (df.collection == "initial")].avo_mean.to_numpy(float)
    gi = hedges_g(xi, yi)
    boots_i = []
    for _ in range(5000):
        xb = rng.choice(xi, len(xi))
        yb = rng.choice(yi, len(yi))
        if xb.std(ddof=1) == 0 and yb.std(ddof=1) == 0:
            continue
        boots_i.append(hedges_g(xb, yb))
    lo_i, hi_i = np.percentile(boots_i, [2.5, 97.5])
    note(f"[openai/initial baseline avo 5.4f-vs-5.5] g={gi:+.3f}, boot 95% CI [{lo_i:+.2f},{hi_i:+.2f}], "
         f"n={len(xi)}/{len(yi)}")

    for cond in ["baseline", "persona"]:
        x = df[(df.model == "GPT-5.4") & (df.condition == cond)
               & (df.collection == "corrected")].avo_mean.to_numpy(float)
        y = df[(df.model == "GPT-5.5") & (df.condition == cond)
               & (df.collection == "corrected")].avo_mean.to_numpy(float)
        g = hedges_g(x, y)
        boots = []
        for _ in range(5000):
            xb = rng.choice(x, len(x))
            yb = rng.choice(y, len(y))
            if xb.std(ddof=1) == 0 and yb.std(ddof=1) == 0:
                continue
            boots.append(hedges_g(xb, yb))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        note(f"[openai/corrected {cond} avo 5.4f-vs-5.5] g={g:+.3f}, boot 95% CI [{lo:+.2f},{hi:+.2f}], "
             f"n={len(x)}/{len(y)}")

    # ola (H4): corrected TCTM vs model overall; unanimity on secure
    olarows = []
    for model in MODEL_ORDER:
        g = df[(df.model == model) & (df.condition == "persona")
               & (df.collection == "corrected")]
        ola = g[g.persona == "ola"].tctm_correct
        olarows.append({"model": model, "ola_M": ola.mean(),
                        "overall_M": g.tctm_correct.mean(),
                        "delta": ola.mean() - g.tctm_correct.mean()})
    ola = pd.DataFrame(olarows)
    ola.to_csv(TABLES / "ola_paradox_corrected.csv", index=False)
    note("[ola/corrected] TCTM ola-vs-overall: " + "; ".join(
        f"{SHORT[r.model]} {r.ola_M:.1f} vs {r.overall_M:.1f} ({r.delta:+.1f})"
        for r in ola.itertuples()))
    note(f"[ola/corrected] models classifying ola secure (run1): "
         f"{sum(1 for m in MODEL_ORDER if (lambda gm: 'ola' in gm.index and gm.loc['ola','style']=='secure')(g1[g1.model==m].set_index('persona')))}/7")


# ------------------------------------------------------------------
# 14. formal decomposition: Lin's CCC + consensus regression + strict coding
# ------------------------------------------------------------------
def ccc(x, y) -> float:
    """Lin's concordance correlation coefficient (penalizes level and gain)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) < 3:
        return float("nan")
    sx, sy = x.std(ddof=1), y.std(ddof=1)
    r = np.corrcoef(x, y)[0, 1]
    return float(2 * r * sx * sy / (sx ** 2 + sy ** 2 + (x.mean() - y.mean()) ** 2))


def formal_decomposition(df: pd.DataFrame) -> None:
    pm_c = persona_means(df, "corrected")
    pm_i = persona_means(df, "initial")

    # (a) pairwise CCC matrix on corrected persona means
    rows = []
    for i, m1 in enumerate(MODEL_ORDER):
        for m2 in MODEL_ORDER[i + 1:]:
            common = pm_c[m1].index.intersection(pm_c[m2].index)
            cs = {d: ccc(pm_c[m1].loc[common, d], pm_c[m2].loc[common, d]) for d in Z_DIMS}
            rows.append({"model_1": m1, "model_2": m2,
                         "median_ccc": float(np.nanmedian(list(cs.values()))),
                         "min_ccc": float(np.nanmin(list(cs.values()))),
                         **{f"ccc_{d}": v for d, v in cs.items()}})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "pairwise_ccc_corrected.csv", index=False)
    note(f"[ccc/corrected pairwise] median CCC range {out.median_ccc.min():.3f}-{out.median_ccc.max():.3f}; "
         f"global min per-dim CCC {out.min_ccc.min():.3f} "
         f"({out.loc[out.min_ccc.idxmin(), 'model_1']}-{out.loc[out.min_ccc.idxmin(), 'model_2']})")

    # (b) leave-one-out consensus regression per model per dim (corrected)
    crows = []
    for m in MODEL_ORDER:
        others = [o for o in MODEL_ORDER if o != m]
        slopes, icepts, r2s = [], [], []
        for d in Z_DIMS:
            cons = pd.concat([pm_c[o][d] for o in others], axis=1).mean(axis=1)
            common = cons.index.intersection(pm_c[m].index)
            x = cons.loc[common].to_numpy(float)
            y = pm_c[m].loc[common, d].to_numpy(float)
            b, a = np.polyfit(x, y, 1)
            yhat = a + b * x
            r2 = 1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum()
            slopes.append(b)
            icepts.append(a)
            r2s.append(r2)
            crows.append({"model": m, "dim": DIM_LABEL[d], "slope_b": b,
                          "intercept_a": a, "r2": r2})
        note(f"[consensus-reg/corrected {SHORT[m]}] slope b median {np.median(slopes):.2f} "
             f"(range {min(slopes):.2f}-{max(slopes):.2f}), |intercept a| median "
             f"{np.median(np.abs(icepts)):.2f} (max {max(np.abs(icepts)):.2f}), R2 median {np.median(r2s):.2f}")
    pd.DataFrame(crows).to_csv(TABLES / "consensus_regression_corrected.csv", index=False)

    # (c) cross-collection per-model: r vs CCC per dim (level vs ordering diagnostic)
    xrows = []
    for m in MODEL_ORDER:
        common = pm_i[m].index.intersection(pm_c[m].index)
        rs, cs = {}, {}
        for d in Z_DIMS:
            rs[d] = pearson(pm_i[m].loc[common, d], pm_c[m].loc[common, d])
            cs[d] = ccc(pm_i[m].loc[common, d], pm_c[m].loc[common, d])
        xrows.append({"model": m,
                      "median_r": float(np.nanmedian(list(rs.values()))),
                      "median_ccc": float(np.nanmedian(list(cs.values()))),
                      "min_ccc": float(np.nanmin(list(cs.values()))),
                      "min_ccc_dim": DIM_LABEL[min(cs, key=lambda d: cs[d])],
                      **{f"r_{d}": rs[d] for d in Z_DIMS},
                      **{f"ccc_{d}": cs[d] for d in Z_DIMS}})
    xout = pd.DataFrame(xrows)
    xout.to_csv(TABLES / "cross_collection_r_vs_ccc.csv", index=False)
    note("[cross-collection r vs CCC] " + "; ".join(
        f"{SHORT[r.model]} r={r.median_r:.3f}/CCC={r.median_ccc:.3f} (min CCC {r.min_ccc:.2f} on {r.min_ccc_dim})"
        for r in xout.itertuples()))


def revision_checks(df: pd.DataFrame, expected: dict[str, str]) -> None:
    # strict four-class sensitivity (no disorganized=fearful equivalence)
    raw_styles = {}
    for p in PERSONAS:
        text = (SYNTH / f"{p}.md").read_text(encoding="utf-8")
        m = re.search(r"attachment_style:\s*([\w_]+)", text)
        raw_styles[p] = m.group(1)
    g1 = df[(df.condition == "persona") & (df.collection == "corrected") & (df.run == 1)]
    rows = []
    for model in MODEL_ORDER:
        gm = g1[g1.model == model].set_index("persona")
        k_equiv = sum(1 for p in PERSONAS if p in gm.index and gm.loc[p, "style"] == expected[p])
        k_strict = sum(1 for p in PERSONAS if p in gm.index and gm.loc[p, "style"] == raw_styles[p])
        rows.append({"model": model, "matches_equiv": k_equiv, "matches_strict": k_strict})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "strict_coding_sensitivity.csv", index=False)
    note("[strict-4class/corrected run1] " + "; ".join(
        f"{SHORT[r.model]} {r.matches_equiv}->{r.matches_strict}" for r in out.itertuples()))
    note(f"[strict-4class] personas declared 'disorganized' in source headers: "
         + ", ".join(p for p, v in raw_styles.items() if v == "disorganized"))

    # unaffected-item deltas (difference-in-differences control)
    items = item_cols(df)
    urows = []
    for model in MODEL_ORDER:
        deltas = {}
        for it in items:
            if it.replace("tctm_", "") in AFFECTED:
                continue
            acc = {}
            for coll in ("initial", "corrected"):
                g = df[(df.model == model) & (df.condition == "persona") & (df.collection == coll)]
                vals = pd.to_numeric(g[it], errors="coerce").dropna()
                acc[coll] = 100 * vals.mean()
            deltas[it.replace("tctm_", "")] = acc["corrected"] - acc["initial"]
        med = float(np.median([abs(v) for v in deltas.values()]))
        mx_item = max(deltas, key=lambda k: abs(deltas[k]))
        urows.append({"model": model, "median_abs_delta_pp": med,
                      "max_abs_delta_pp": abs(deltas[mx_item]), "max_item": mx_item})
    uout = pd.DataFrame(urows)
    uout.to_csv(TABLES / "unaffected_item_deltas.csv", index=False)
    note("[unaffected-items delta] " + "; ".join(
        f"{SHORT[r.model]} med {r.median_abs_delta_pp:.1f}pp / max {r.max_abs_delta_pp:.1f}pp ({r.max_item})"
        for r in uout.itertuples()))

    # run-weighted vs persona-weighted TCTM totals (retained-retry impact)
    rows2 = []
    pm = persona_means(df, "corrected")
    for model in MODEL_ORDER:
        g = df[(df.model == model) & (df.condition == "persona") & (df.collection == "corrected")]
        rows2.append({"model": model, "run_weighted_M": g.tctm_correct.mean(),
                      "persona_weighted_M": pm[model]["tctm_correct"].mean()})
    w = pd.DataFrame(rows2)
    w.to_csv(TABLES / "run_vs_persona_weighting.csv", index=False)
    note("[weighting check] max |run-weighted - persona-weighted| TCTM M = "
         f"{(w.run_weighted_M - w.persona_weighted_M).abs().max():.3f} items")

    # GPT-5.4-mini baseline by collection event (bounds the change window)
    for w_ in (1, 2, 3):
        g = df[(df.model == "GPT-5.4-mini") & (df.condition == "baseline") & (df.wave == w_)]
        if g.empty:
            continue
        note(f"[mini baseline wave {w_}] n={len(g)}, Anx M={g.anx_mean.mean():.2f} "
             f"(SD {g.anx_mean.std(ddof=1):.2f}), MentS M={g.ments_total.mean():.1f}, "
             f"KPP M={g.kpp_mean.mean():.2f}, TIPI-ES M={g.tipi_es.mean():.2f}")


# ------------------------------------------------------------------
# 15. second-review additions: Spearman, bootstrap CIs, coding sensitivities
# ------------------------------------------------------------------
def review2_checks(df: pd.DataFrame, expected: dict[str, str]) -> None:
    pm = persona_means(df, "corrected")
    rng = np.random.default_rng(SEED + 1)

    def pair_median(m1: str, m2: str, personas: list[str], method: str = "pearson") -> float:
        a, b = pm[m1], pm[m2]
        rs = []
        for d in Z_DIMS:
            xs, ys = [], []
            for p in personas:
                if p in a.index and p in b.index:
                    xs.append(a.loc[p, d])
                    ys.append(b.loc[p, d])
            if len(xs) > 2:
                if method == "spearman":
                    rs.append(stats.spearmanr(xs, ys).statistic)
                else:
                    rs.append(pearson(xs, ys))
        return float(np.nanmedian(rs))

    common_all = sorted(set.intersection(*[set(pm[m].index) for m in MODEL_ORDER]))
    pairs = [(m1, m2) for i, m1 in enumerate(MODEL_ORDER) for m2 in MODEL_ORDER[i + 1:]]

    # Spearman versions of the headline medians (orderings are literal here).
    sp = {(m1, m2): pair_median(m1, m2, common_all, "spearman") for m1, m2 in pairs}
    pe = {(m1, m2): pair_median(m1, m2, common_all, "pearson") for m1, m2 in pairs}
    note(f"[review2 spearman slopes] min pair median rho={min(sp.values()):.3f} "
         f"(Pearson {min(pe.values()):.3f}); 5.4f<->5.5 rho="
         f"{sp[('GPT-5.4', 'GPT-5.5')]:.3f} (Pearson {pe[('GPT-5.4', 'GPT-5.5')]:.3f}); "
         f"median |rho - r| over 21 pairs = "
         f"{np.median([abs(sp[k] - pe[k]) for k in pairs]):.3f}")

    # Persona-bootstrap CIs for the two headline medians (2,000 resamples).
    boots_min, boots_pair = [], []
    for _ in range(2000):
        sample = list(rng.choice(common_all, len(common_all)))
        meds = [pair_median(m1, m2, sample) for m1, m2 in pairs]
        boots_min.append(min(meds))
        boots_pair.append(pair_median("GPT-5.4", "GPT-5.5", sample))
    lo1, hi1 = np.percentile(boots_min, [2.5, 97.5])
    lo2, hi2 = np.percentile(boots_pair, [2.5, 97.5])
    note(f"[review2 slope CIs] min pairwise median r 95% CI [{lo1:.3f},{hi1:.3f}]; "
         f"5.4f<->5.5 median r 95% CI [{lo2:.3f},{hi2:.3f}]")

    # Author-target agreement: Spearman version.
    targets = author_targets()
    rows = []
    for model in MODEL_ORDER:
        rs_p, rs_s = [], []
        for d in Z_DIMS:
            xs = [targets[p][d] for p in PERSONAS if p in pm[model].index]
            ys = [pm[model].loc[p, d] for p in PERSONAS if p in pm[model].index]
            rs_p.append(pearson(xs, ys))
            rs_s.append(stats.spearmanr(xs, ys).statistic)
        rows.append({"model": model, "median_pearson": float(np.nanmedian(rs_p)),
                     "median_spearman": float(np.nanmedian(rs_s))})
    at = pd.DataFrame(rows)
    at.to_csv(TABLES / "author_target_spearman.csv", index=False)
    note("[review2 author-target spearman] " + "; ".join(
        f"{SHORT[r.model]} rho={r.median_spearman:.2f} (r={r.median_pearson:.2f})"
        for r in at.itertuples()))

    # Persona-clustered bootstrap for the corrected persona-condition avoidance
    # contrast (both administrations of a resampled persona enter together).
    def hedges_g(x: np.ndarray, y: np.ndarray) -> float:
        nx, ny = len(x), len(y)
        sp_ = math.sqrt(((nx - 1) * x.std(ddof=1) ** 2 + (ny - 1) * y.std(ddof=1) ** 2)
                        / (nx + ny - 2))
        return (x.mean() - y.mean()) / sp_ * (1 - 3 / (4 * (nx + ny) - 9))

    ga = df[(df.model == "GPT-5.4") & (df.condition == "persona") & (df.collection == "corrected")]
    gb = df[(df.model == "GPT-5.5") & (df.condition == "persona") & (df.collection == "corrected")]
    persa = sorted(ga.persona.unique())
    persb = sorted(gb.persona.unique())
    boots = []
    for _ in range(5000):
        xa = np.concatenate([ga[ga.persona == p].avo_mean.to_numpy(float)
                             for p in rng.choice(persa, len(persa))])
        xb = np.concatenate([gb[gb.persona == p].avo_mean.to_numpy(float)
                             for p in rng.choice(persb, len(persb))])
        boots.append(hedges_g(xa, xb))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    g_obs = hedges_g(ga.avo_mean.to_numpy(float), gb.avo_mean.to_numpy(float))
    note(f"[review2 persona avo g, persona-clustered bootstrap] g={g_obs:+.3f}, "
         f"95% CI [{lo:+.2f},{hi:+.2f}]")

    # Sensitivity: exclude the four disorganized-labeled personas entirely.
    raw_styles = {}
    for p in PERSONAS:
        text = (SYNTH / f"{p}.md").read_text(encoding="utf-8")
        m = re.search(r"attachment_style:\s*([\w_]+)", text)
        raw_styles[p] = m.group(1)
    keep = [p for p in PERSONAS if raw_styles[p] != "disorganized"]
    g1 = df[(df.condition == "persona") & (df.collection == "corrected") & (df.run == 1)]
    rows2 = []
    for model in MODEL_ORDER:
        gm = g1[g1.model == model].set_index("persona")
        pl = [p for p in keep if p in gm.index]
        a = [expected[p] for p in pl]
        b = [gm.loc[p, "style"] for p in pl]
        k = cohen_kappa(a, b)
        rows2.append({"model": model, "matches": sum(1 for x, y in zip(a, b) if x == y),
                      "n": len(pl), "kappa": k})
    ex = pd.DataFrame(rows2)
    ex.to_csv(TABLES / "disorganized_exclusion_sensitivity.csv", index=False)
    note("[review2 exclusion of 4 disorganized personas] " + "; ".join(
        f"{SHORT[r.model]} {r.matches}/{r.n} (kappa {r.kappa:.2f})" for r in ex.itertuples()))

    # Ola versus the mean of the OTHER 29 personas (not a mean including her).
    orows = []
    for model in MODEL_ORDER:
        g = df[(df.model == model) & (df.condition == "persona") & (df.collection == "corrected")]
        ola = g[g.persona == "ola"].tctm_correct.mean()
        others = g[g.persona != "ola"].tctm_correct.mean()
        orows.append({"model": model, "ola": ola, "others": others, "delta": ola - others})
    oo = pd.DataFrame(orows)
    oo.to_csv(TABLES / "ola_vs_others_corrected.csv", index=False)
    note("[review2 ola vs other-29 mean] " + "; ".join(
        f"{SHORT[r.model]} {r.ola:.1f} vs {r.others:.1f} ({r.delta:+.1f})" for r in oo.itertuples()))


def style_threshold_sensitivity(df: pd.DataFrame, expected: dict[str, str]) -> None:
    """Sensitivity of attachment-style classification to the scale-midpoint
    threshold (the operational cut at 4.0 on the 1-7 DBZ-R means). Re-derives
    per-run style labels at thresholds 3.5-4.5 and reports per-model matches
    and Cohen's kappa versus the author labels."""
    g = df[(df.condition == "persona") & (df.collection == "corrected") & (df.run == 1)]

    def derive(anx: float, avo: float, t: float) -> str:
        if anx >= t and avo >= t:
            return "fearful_avoidant"
        if anx >= t:
            return "anxious_preoccupied"
        if avo >= t:
            return "dismissive_avoidant"
        return "secure"

    # Guard: the derivation must reproduce the recorded style column at t=4.0.
    mismatches = sum(
        derive(r.anx_mean, r.avo_mean, 4.0) != r.style
        for r in df[df.condition == "persona"].itertuples()
    )
    assert mismatches == 0, f"threshold-4 rule does not reproduce style column ({mismatches})"

    rows = []
    for t in (3.5, 3.75, 4.0, 4.25, 4.5):
        for model in MODEL_ORDER:
            gm = g[g.model == model].set_index("persona")
            present = [p for p in PERSONAS if p in gm.index]
            a = [derive(gm.loc[p, "anx_mean"], gm.loc[p, "avo_mean"], t) for p in present]
            b = [expected[p] for p in present]
            k = sum(x == y for x, y in zip(a, b))
            rows.append({"threshold": t, "model": model, "matches": k,
                         "n": len(present), "accuracy": k / len(present),
                         "kappa": cohen_kappa(a, b)})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "style_threshold_sensitivity.csv", index=False)
    for t in (3.5, 3.75, 4.0, 4.25, 4.5):
        sub = out[out.threshold == t]
        note(f"[style threshold sensitivity t={t}] matches "
             f"{int(sub.matches.min())}-{int(sub.matches.max())}/30, "
             f"kappa {sub.kappa.min():.2f}-{sub.kappa.max():.2f}")


def main() -> None:
    df, df57 = load()
    exp = expected_styles()
    note(f"# numbers.md — primary analysis manifest (seed {SEED})")
    note("")
    design_counts(df)
    baseline_intercepts(df)
    slope_correlations(df)
    style_fidelity(df, exp)
    tctm_totals(df)
    item_analysis(df)
    natural_experiment(df)
    admin_context(df, df57)
    determinism(df)
    longitudinal(df, exp)
    test_retest(df)
    masc_fingerprint(df)
    zero_prompt_and_human(df)
    extras(df, exp)
    formal_decomposition(df)
    revision_checks(df, exp)
    review2_checks(df, exp)
    style_threshold_sensitivity(df, exp)
    (HERE / "numbers.md").write_text("\n".join(MANIFEST) + "\n", encoding="utf-8")
    print(f"\nWrote {len(list(TABLES.glob('*.csv')))} tables to {TABLES}")
    print(f"Wrote manifest to {HERE / 'numbers.md'}")


if __name__ == "__main__":
    main()
