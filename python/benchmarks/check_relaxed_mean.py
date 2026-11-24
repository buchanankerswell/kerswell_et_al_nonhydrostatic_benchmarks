"""Mean dynamic pressure against short-wavelength oscillation for the sink suite."""

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
from utils.artifacts import add_force_argument, outputs_exist
from utils.logging import log_artifact, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"
UNDAMPED_BASELINE_RUN = "NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res6"
NO_FEEDBACK_REFERENCE_RUN = "NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6"
SETTLED_STEPS = (10, 11, 12)
MEAN_TOL_MPA = 50.0


def load_samples(path):
    rows = []
    if not Path(path).exists():
        log_warn(f"skip {path} (missing)")
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
    for model, samples in by_run.items():
        samples.sort(key=lambda r: r["step"])
        settled = [r["mean"] for r in samples if r["step"] in SETTLED_STEPS]
        if not settled:
            settled = [r["mean"] for r in samples[-3:]]
        if not settled:
            continue
        out[model] = {
            "mean_initial": samples[0]["mean"],
            "mean_final": float(np.mean(settled)),
            "peak_short_wavelength": max(r["grid"] for r in samples),
            "n_steps": len(samples),
        }
    return out


def run_label(model):
    u = parse_uid_columns(model)
    parts = [u["damp"] or "None"]
    if u["dynp"] == 0:
        parts.append("no feedback")
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
    add_force_argument(ap)
    args = ap.parse_args()

    out_csv = Path(args.out_csv)
    out_fig = Path(args.fig_dir) / "relaxed-mean-check-sink.png"
    if outputs_exist([out_csv, out_fig], args.force):
        return

    apply_bench_style(args.dpi)

    summary = summarise(load_samples(args.lateral))
    if UNDAMPED_BASELINE_RUN not in summary or NO_FEEDBACK_REFERENCE_RUN not in summary:
        log_warn("undamped baseline or no-feedback reference missing from lateral-pressure.csv")
        return
    mean_baseline = summary[UNDAMPED_BASELINE_RUN]["mean_final"]
    mean_reference = summary[NO_FEEDBACK_REFERENCE_RUN]["mean_final"]
    peak_reference = summary[NO_FEEDBACK_REFERENCE_RUN]["peak_short_wavelength"]

    fields = [
        "model_id",
        "damp",
        "dynp",
        "res",
        "cfl",
        "n_steps",
        "mean_initial_MPa",
        "mean_final_MPa",
        "peak_short_wavelength_MPa",
        "delta_vs_undamped_baseline_MPa",
        "delta_vs_no_feedback_reference_MPa",
        "mean_flag",
    ]
    rows = []
    for model in sorted(summary):
        d = summary[model]
        u = parse_uid_columns(model)
        delta_reference = d["mean_final"] - mean_reference
        if d["n_steps"] < len(SETTLED_STEPS):
            flag = "incomplete-run"
        elif abs(delta_reference) <= args.mean_tol_mpa:
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
                "mean_final_MPa": round(d["mean_final"], 2),
                "peak_short_wavelength_MPa": round(d["peak_short_wavelength"], 2),
                "delta_vs_undamped_baseline_MPa": round(d["mean_final"] - mean_baseline, 2),
                "delta_vs_no_feedback_reference_MPa": round(delta_reference, 2),
                "mean_flag": flag,
            }
        )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    log_artifact(out_csv)

    plotted = [r for r in rows if r["n_steps"] >= len(SETTLED_STEPS)]
    fig, ax = plt.subplots(figsize=(BENCH_WIDE_W, 4.4))
    for r in plotted:
        x, y = r["peak_short_wavelength_MPa"], r["mean_final_MPa"]
        ax.plot(x, y, "o", color=bench_color(r["model_id"]), ms=7)
        u = parse_uid_columns(r["model_id"])
        if u["res"] == 6 and not u["cfl"]:
            ax.annotate(run_label(r["model_id"]), (x, y), textcoords="offset points", xytext=(5, 4), fontsize="small")
    ax.axhline(mean_reference, ls="--", lw=1.0, color="#08306B")
    ax.axvline(peak_reference, ls="--", lw=1.0, color="#08306B")
    ax.axhline(mean_baseline, ls=":", lw=1.0, color="#000000")
    handles = [
        Line2D([0], [0], ls="--", color="#08306B", label=f"No-feedback mean ({mean_reference:.0f} MPa)"),
        Line2D([0], [0], ls=":", color="#000000", label=f"Undamped mean ({mean_baseline:.0f} MPa)"),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=True, facecolor="white", framealpha=0.9)
    ax.set_xlabel("Largest short-wavelength oscillation (MPa)")
    ax.set_ylabel("Mean dynamic pressure, last three outputs (MPa)")
    ax.set_title("Pressure oscillation and mean dynamic pressure")
    fig.subplots_adjust(left=0.16, right=0.97, top=0.9, bottom=0.13)

    out_fig.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_fig, dpi=args.dpi)
    plt.close(fig)
    log_artifact(out_fig)


if __name__ == "__main__":
    sys.exit(main())
