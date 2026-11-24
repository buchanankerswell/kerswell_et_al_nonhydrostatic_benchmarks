"""Lateral-mean bias check for the sink damping treatments.

A linear relaxation filter preserves the mean of its input. A persistent shift
of the dynamic-pressure lateral mean in relaxed runs therefore points to a
change in the coupled flow (or a bias in the relaxed field), not to filter lag.
This script measures each run's settled lateral mean against the two
references (S1 undamped full feedback, S2 no feedback) and plots it against
peak grid-band oscillation power, so the tradeoff between suppressing the wave
and holding the physical mean is visible.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/check_relaxed_mean.py \\
    --lateral simulation/results/lateral-pressure.csv \\
    --out-csv simulation/results/relaxed-mean-check.csv \\
    --fig-dir figs/benchmarks --dpi 100
"""

import argparse
import csv
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from benchmarks.common import parse_uid_columns
from simulation.mesh.config import BENCH_WIDE_W, apply_bench_style, bench_color
from utils.logging import log_artifact, log_info, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"
S1 = "NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res6"
S2 = "NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6"
SETTLED_STEPS = (10, 11, 12)
MEAN_TOL_MPA = 50.0


def load_samples(path):
    rows = []
    if not Path(path).exists():
        log_warn("skip: missing " + str(path))
        return rows
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                rows.append(
                    {
                        "model_id": r["model_id"],
                        "step": int(r["timestep"]),
                        "mean": float(r["mean_MPa"]),
                        "grid": float(r["grid_MPa"]),
                    }
                )
            except (KeyError, ValueError):
                continue
    return rows


def summarise(rows):
    by_run = {}
    for r in rows:
        by_run.setdefault(r["model_id"], []).append(r)
    out = {}
    for model, rs in by_run.items():
        rs.sort(key=lambda r: r["step"])
        settled = [r["mean"] for r in rs if r["step"] in SETTLED_STEPS]
        if not settled:
            settled = [r["mean"] for r in rs[-3:]]
        if not settled:
            continue
        out[model] = {
            "mean_initial": rs[0]["mean"],
            "mean_settled": float(np.mean(settled)),
            "grid_peak": max(r["grid"] for r in rs),
            "n_steps": len(rs),
        }
    return out


def short_label(model):
    u = parse_uid_columns(model)
    parts = [u["damp"] or "None"]
    if u["dynp"] == 0:
        parts.append("Off")
    if u["res"] != 6:
        parts.append(f"R{u['res']}")
    if u["cfl"]:
        parts.append(f"C{u['cfl']}")
    return " ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lateral", default=str(RESULTS / "lateral-pressure.csv"), help="Lateral-pressure diagnostic CSV")
    ap.add_argument("--out-csv", default=str(RESULTS / "relaxed-mean-check.csv"), help="Output summary CSV path")
    ap.add_argument("--fig-dir", default="figs/benchmarks", help="Output figure directory")
    ap.add_argument("--mean-tol-mpa", type=float, default=MEAN_TOL_MPA, help="Flag means farther than this from the no-feedback reference")
    ap.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI)")
    args = ap.parse_args()
    apply_bench_style(args.dpi)

    summary = summarise(load_samples(args.lateral))
    if S1 not in summary or S2 not in summary:
        log_warn("baseline (S1) or reference (S2) missing from lateral-pressure.csv")
        return
    m_s1 = summary[S1]["mean_settled"]
    m_s2 = summary[S2]["mean_settled"]
    g_s2 = summary[S2]["grid_peak"]

    fields = [
        "model_id",
        "damp",
        "dynp",
        "res",
        "cfl",
        "n_steps",
        "mean_initial_MPa",
        "mean_settled_MPa",
        "grid_peak_MPa",
        "delta_vs_S1_MPa",
        "delta_vs_S2_MPa",
        "mean_flag",
    ]
    rows = []
    for model in sorted(summary):
        d = summary[model]
        u = parse_uid_columns(model)
        delta_s2 = d["mean_settled"] - m_s2
        if d["n_steps"] < len(SETTLED_STEPS):
            flag = "incomplete-run"
        elif abs(delta_s2) <= args.mean_tol_mpa:
            flag = "near-reference"
        else:
            flag = "offset-from-reference"
        rows.append(
            {
                "model_id": model,
                "damp": u["damp"],
                "dynp": u["dynp"],
                "res": u["res"],
                "cfl": u["cfl"],
                "n_steps": d["n_steps"],
                "mean_initial_MPa": round(d["mean_initial"], 2),
                "mean_settled_MPa": round(d["mean_settled"], 2),
                "grid_peak_MPa": round(d["grid_peak"], 2),
                "delta_vs_S1_MPa": round(d["mean_settled"] - m_s1, 2),
                "delta_vs_S2_MPa": round(delta_s2, 2),
                "mean_flag": flag,
            }
        )

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    flagged = sum(r["mean_flag"] == "offset-from-reference" for r in rows)
    log_info(f"Checked {len(rows)} runs; {flagged} sit farther than {args.mean_tol_mpa:g} MPa from S2")
    log_artifact(out_csv)

    # Crashed runs leave one or two samples and a meaningless "settled" mean;
    # keep them in the CSV but off the figure so they do not stretch the axes.
    plotted = [r for r in rows if r["n_steps"] >= len(SETTLED_STEPS)]
    fig, ax = plt.subplots(figsize=(BENCH_WIDE_W, 4.4))
    for r in plotted:
        x, y = r["grid_peak_MPa"], r["mean_settled_MPa"]
        ax.plot(x, y, "o", color=bench_color(r["model_id"]), ms=7)
        u = parse_uid_columns(r["model_id"])
        if u["res"] == 6 and not u["cfl"]:
            ax.annotate(short_label(r["model_id"]), (x, y), textcoords="offset points", xytext=(5, 4), fontsize=7)
    ax.axhline(m_s2, ls="--", lw=1.0, color="#08306B")
    ax.axvline(g_s2, ls="--", lw=1.0, color="#08306B")
    ax.axhline(m_s1, ls=":", lw=1.0, color="#000000")
    handles = [
        Line2D([0], [0], ls="--", color="#08306B", label=f"S2 no-feedback mean ({m_s2:.0f} MPa)"),
        Line2D([0], [0], ls=":", color="#000000", label=f"S1 undamped mean ({m_s1:.0f} MPa)"),
    ]
    ax.legend(handles=handles, loc="upper right", fontsize=8, frameon=True, facecolor="white", framealpha=0.9)
    ax.set_xlabel("Peak grid-band oscillation (MPa)")
    ax.set_ylabel("Settled lateral mean $\\hat{P}$ (MPa)")
    ax.set_title("Oscillation suppression vs mean bias")
    fig.subplots_adjust(left=0.13, right=0.97, top=0.9, bottom=0.13)

    figdir = Path(args.fig_dir)
    figdir.mkdir(parents=True, exist_ok=True)
    out_fig = figdir / "relaxed-mean-check-sink.png"
    fig.savefig(out_fig, dpi=args.dpi)
    plt.close(fig)
    log_artifact(out_fig)


if __name__ == "__main__":
    sys.exit(main())
