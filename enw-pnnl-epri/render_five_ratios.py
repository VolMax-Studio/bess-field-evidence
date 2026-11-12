"""Reproduce the ENW five-ratios PNG directly from reproduce.py output.

Requires matplotlib in addition to requirements.txt.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


HERE = Path(__file__).resolve().parent
REPRO_SCRIPT = HERE / "reproduce.py"
OUT_PNG = HERE / "five_ratios.png"


def main() -> int:
    raw_json = subprocess.check_output(
        [sys.executable, str(REPRO_SCRIPT), "--json"],
        cwd=str(HERE),
        text=True,
    )
    data = json.loads(raw_json)
    ratios = data["ratios"]
    iso = data["common_window_isolation"]

    labels = [
        "Battery DC (PDC)\nValid DC intervals only\n(70,105 min)",
        "Inverter AC (PAC)\nFull observation period\n(85,858 min)",
        "Grid connection (PGCP)\nFull observation period\n(85,858 min)",
        "Grid connection (PGCP)\nExcl. quality-flagged rows\n(70,003 min)",
        "Grid connection (PGCP)\nAuthors' \"Use\" segments\n(65 / 214 \u00b7 19,487 min)",
    ]
    values = [r["ratio_pct_exact"] for r in ratios]
    colors = ["#0b172a", "#475569", "#1e3a8a", "#2563eb", "#0ea5e9"]

    fig = plt.figure(figsize=(6.8, 8.5), dpi=200, facecolor="#ffffff")
    ax = fig.add_axes([0.36, 0.315, 0.58, 0.455], facecolor="#f8fafc")

    y_pos = list(range(len(labels)))[::-1]
    bars = ax.barh(y_pos, values, height=0.58, color=colors, edgecolor="none", zorder=3)

    ax.axvline(iso["pgcp_full_pct"], color="#1e3a8a", linestyle=":", linewidth=1.1, alpha=0.65, zorder=2)
    ax.axvline(iso["pdc_common_pct"], color="#0b172a", linestyle=":", linewidth=1.1, alpha=0.65, zorder=2)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8.3, fontweight="bold", color="#1e293b", linespacing=1.15)
    ax.set_xlim(0, 106)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xticklabels(["0%", "20%", "40%", "60%", "80%", "100%"], fontsize=8.2, color="#475569")
    ax.set_xlabel("Exported / Imported Energy Ratio (%)", fontsize=9.2, fontweight="bold", color="#1e293b", labelpad=7)
    ax.xaxis.grid(True, linestyle=":", color="#cbd5e1", alpha=0.85, zorder=1)
    ax.set_axisbelow(True)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#94a3b8")
    ax.spines["bottom"].set_color("#94a3b8")

    for bar, val in zip(bars, values):
        ax.text(
            val + 1.4,
            bar.get_y() + bar.get_height() / 2.0,
            f"{val:.1f}%",
            va="center",
            ha="left",
            fontsize=9.8,
            fontweight="bold",
            color="#0f172a",
            bbox=dict(boxstyle="square,pad=0.12", facecolor="#f8fafc", edgecolor="none", alpha=0.92),
            zorder=4,
        )

    fig.text(0.055, 0.952, "One BESS dataset. Five plausible energy ratios.", fontsize=14.8, fontweight="bold", color="#0f172a")
    fig.text(0.055, 0.921, "Which one is valid for a performance claim?", fontsize=14.8, fontweight="bold", color="#1d4ed8")
    fig.text(0.055, 0.892, "PNNL / EPRI ENW field dataset \u00b7 85,858 one-minute intervals (60 s step, 0 gaps)", fontsize=8.6, color="#475569")

    warn_box = FancyBboxPatch(
        (0.05, 0.832), 0.90, 0.042,
        boxstyle="round,pad=0.006,rounding_size=0.008",
        transform=fig.transFigure,
        facecolor="#fef2f2",
        edgecolor="#fca5a5",
        linewidth=1.0,
    )
    fig.patches.append(warn_box)
    fig.text(
        0.06, 0.853,
        "Not a verified round-trip efficiency (RTE): descriptive exported/imported ratios only.\n"
        "System SoC starts at 15.8% and ends at 92.0%; boundaries, standby intervals, and filters differ.",
        fontsize=7.9,
        fontstyle="italic",
        fontweight="bold",
        color="#b91c1c",
        va="center",
        linespacing=1.28,
    )

    fig.text(0.055, 0.793, "Exported-to-imported energy ratio across boundaries & selection rules", fontsize=9.8, fontweight="bold", color="#0f172a")

    note_box = FancyBboxPatch(
        (0.05, 0.095), 0.90, 0.122,
        boxstyle="round,pad=0.006,rounding_size=0.008",
        transform=fig.transFigure,
        facecolor="#f1f5f9",
        edgecolor="#94a3b8",
        linewidth=0.9,
    )
    fig.patches.append(note_box)

    box_text = (
        "Why this matters for commissioning (isolating boundary vs. interval selection):\n"
        f"\u2022 Common valid-DC timestamp set ({iso['common_window_min']:,} min, incl. 102 flagged): "
        f"PGCP {iso['pgcp_common_pct']:.3f}% \u2192 PDC {iso['pdc_common_pct']:.3f}% (+{iso['pure_boundary_shift_pp']:.3f} pp ratio shift).\n"
        f"\u2022 Adding {iso['disconnected_dc_min']:,} disconnected-DC standby min to PGCP (85,858 min): "
        f"{iso['pgcp_common_pct']:.3f}% \u2192 {iso['pgcp_full_pct']:.3f}% ({iso['window_extension_shift_pp']:.3f} pp).\n"
        "\u2022 Selection rules at PGCP alone shift the ratio from 74.5% to 79.8% (Authors' \"Use\" segments).\n"
        "\u2022 Descriptive ratio shifts do not attribute component losses or replace pre-agreed SAT/RTE rules."
    )
    fig.text(
        0.058, 0.156,
        box_text,
        fontsize=7.05,
        color="#1e293b",
        va="center",
        linespacing=1.42,
    )

    fig.text(
        0.055, 0.046,
        "Source: Crawford et al., Grid-Scale BESS Operational Datasets for Battery Modeling Research (2026)",
        fontsize=7.3,
        color="#475569",
    )
    fig.text(
        0.055, 0.029,
        "DOI: 10.5281/zenodo.22947521 \u00b7 Independent read-only reconstruction from ENW.feather \u00b7 VolMax Studio Lab",
        fontsize=7.3,
        color="#475569",
    )

    fig.savefig(OUT_PNG, dpi=200, facecolor="#ffffff")
    print(f"Saved {OUT_PNG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
