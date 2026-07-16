"""Generate figures used only by the non-destructive Codex revision files."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
MAGISTERKA = PAPER.parent
TABLES = PAPER / "analysis" / "tables"
SYNTH = MAGISTERKA / "synthetic"


def test_retest_heatmap() -> None:
    data = pd.read_csv(TABLES / "test_retest_corrected.csv")
    columns = [
        "r_z_anx", "r_z_avo", "r_z_ments_total", "r_z_kpp", "r_z_e",
        "r_z_a", "r_z_c", "r_z_es", "r_z_o",
    ]
    labels = ["Anx", "Avo", "MentS", "KPP", "E", "A", "C", "ES", "O"]
    model_labels = ["Sonnet", "Opus", "GPT-5.4-mini", "GPT-5.4", "GPT-5.5", "Grok", "Gemini"]
    matrix = data[columns].to_numpy(float)

    fig, ax = plt.subplots(figsize=(9.2, 4.9))
    image = ax.imshow(matrix, vmin=0.80, vmax=1.00, cmap="YlGn", aspect="auto")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_yticks(range(len(model_labels)), model_labels)
    ax.set_title("Per-dimension test-retest (corrected collection, 30 personas x 2 administrations)")
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix[row, col]
            color = "white" if value > 0.965 else "black"
            ax.text(col, row, f"{value:.2f}".lstrip("0"), ha="center", va="center", color=color, fontsize=9)
    ax.add_patch(plt.Rectangle((0.5, -0.5), 1, matrix.shape[0], fill=False, edgecolor="#b23a48", linewidth=2.0))
    cbar = fig.colorbar(image, ax=ax, fraction=0.03, pad=0.03)
    cbar.set_label("test-retest r (administration 1 vs 2)")
    fig.tight_layout()
    fig.savefig(HERE / "figS1_testretest_dimensions.pdf", bbox_inches="tight")
    plt.close(fig)


def threshold_distributions() -> None:
    data = pd.read_csv(SYNTH / "all_data_v20_public.csv")
    gpt = data[
        (data["model"] == "GPT-5.4")
        & (data["condition"] == "baseline")
        & (data["wave"].isin([1, 2]))
    ]["avo_mean"].astype(float)
    gemini = data[
        (data["model"] == "Gemini 3 Flash")
        & (data["condition"] == "baseline")
        & (data["wave"] == 4)
    ]["avo_mean"].astype(float)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), sharey=False)
    panels = [
        (axes[0], gpt, "GPT-5.4 (full), kolekcja wstępna"),
        (axes[1], gemini, "Gemini 3 Flash, kolekcja skorygowana"),
    ]
    for ax, values, title in panels:
        bins = np.linspace(1, 7, 19)
        ax.hist(values, bins=bins, color="#4c956c", edgecolor="white")
        ax.axvline(4, color="#b23a48", linestyle="--", linewidth=1.8, label="próg stylu = 4")
        ax.set_xlim(1, 7)
        ax.set_xlabel("średnia DBZ-R: unikanie")
        ax.set_ylabel("liczba odpowiedzi")
        ax.set_title(f"{title}\nN={len(values)}, próbne SD={values.std(ddof=1):.2f}")
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Rozkłady bazowe przecinające próg klasyfikacyjny (opisowo)", y=1.02)
    fig.tight_layout()
    fig.savefig(HERE / "figS2_threshold_distributions.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    test_retest_heatmap()
    threshold_distributions()
