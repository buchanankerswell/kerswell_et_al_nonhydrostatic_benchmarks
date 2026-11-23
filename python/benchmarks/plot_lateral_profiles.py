"""Lateral extent of the feedback variables across the 410 depth band.

For one transient output step, bin mesh cells within a depth band around
the runtime 410 nominal by lateral distance and plot the bin-mean
transformed fraction, driving energy, reaction rate, and pressure
anomaly. Companion to depth-profiles-sink.png (vertical extent).

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/plot_lateral_profiles.py --runs <uid ...> \\
    --suite-tag sink --step 00007 --nominal-m 379957 \\
    --out figs/benchmarks/lateral-profiles-sink.png
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

from benchmarks.plot_depth_window import read_step
from simulation.mesh.config import BENCH_TALL_W, S_PER_MA, apply_bench_style, bench_color, bench_label
from utils.logging import log_artifact, log_warn

N_BINS = 120


def band_mean(x, depth, values, nominal_m, half_m):
    """Bin-mean of values over lateral distance for cells inside the depth band."""
    keep = np.isfinite(x) & np.isfinite(depth) & np.isfinite(values) & (np.abs(depth - nominal_m) <= half_m)
    x, values = x[keep], values[keep]
    if x.size < 8:
        return None, None
    edges = np.linspace(x.min(), x.max(), N_BINS + 1)
    idx = np.clip(np.digitize(x, edges) - 1, 0, N_BINS - 1)
    sums = np.bincount(idx, weights=values, minlength=N_BINS)
    counts = np.bincount(idx, minlength=N_BINS)
    mean = np.where(counts > 0, sums / np.maximum(counts, 1), np.nan)
    return (edges[:-1] + edges[1:]) / 2 / 1e3, mean


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="Run UIDs to plot")
    ap.add_argument("--suite-tag", required=True, help="Suite tag: sink")
    ap.add_argument("--step", default="00007", help="Output number to render (default 00007, transient peak)")
    ap.add_argument("--nominal-m", type=float, required=True, help="Runtime-adiabat 410 nominal (m)")
    ap.add_argument("--band-half-m", type=float, default=25e3, help="Depth band half-width around nominal (m)")
    ap.add_argument("--block-top-m", type=float, default=875e03, help="Block top (m) (project.mk BLOCK_Y_TOP)")
    ap.add_argument("--block-bottom-m", type=float, default=725e03, help="Block bottom (m) (project.mk BLOCK_Y_BOT)")
    ap.add_argument("--gravity", type=float, default=9.81, help="Gravity (m/s^2) (project.mk GRAVITY)")
    ap.add_argument("--out", required=True, help="Output figure path")
    ap.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI; draft 100, manuscript 330)")
    args = ap.parse_args()
    apply_bench_style(args.dpi)

    fields = [
        ("xi_ol_wd", 1.0, "$\\xi$"),
        ("dG_driving_0", 1e-3, "$dG$ (kJ/mol)"),
        ("reaction_rate_C0", S_PER_MA, "$\\dot{X}$ (1/Ma)"),
        ("nonadiabatic_pressure", 1e-6, "$\\hat{P}$ (MPa)"),
    ]

    fig, ax = plt.subplots(4, 1, figsize=(BENCH_TALL_W, 9.0), sharex=True)
    fig.subplots_adjust(left=0.2, right=0.62, top=0.95, bottom=0.06, hspace=0.3)
    for run in args.runs:
        try:
            d = read_step(run, args.step, args.block_top_m, args.block_bottom_m, args.gravity)
        except OSError as e:
            log_warn(f"skip {run}: {e}")
            continue
        x = d["points"][:, 0]
        depth = 1e6 - d["points"][:, 1]
        kw = dict(lw=1.8, alpha=0.9, label=bench_label(run), color=bench_color(run))
        for a, (field, scale, _label) in zip(ax, fields):
            if field not in d:
                continue
            xc, mean = band_mean(x, depth, d[field] * scale, args.nominal_m, args.band_half_m)
            if xc is None:
                continue
            a.plot(xc, mean, **kw)
    for a in ax[:-1]:
        a.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)
    for a, (_field, _scale, label) in zip(ax, fields):
        a.set_ylabel(label, labelpad=8)
        a.xaxis.set_major_locator(MaxNLocator(nbins=4))
    ax[-1].set_xlabel("Distance (km)")
    handles, labels = ax[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="center left", bbox_to_anchor=(0.64, 0.5), frameon=True, facecolor="white", framealpha=0.9)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi)
    plt.close(fig)
    log_artifact(args.out)


if __name__ == "__main__":
    sys.exit(main())
