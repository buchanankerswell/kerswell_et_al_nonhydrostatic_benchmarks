"""Plot last-output depth-average temperature + reaction-front profiles.

Reads per-run depth_average.txt (written by the ASPECT depth-average
postprocessor) and overlays the final profiles: temperature on top,
xi_ol_wd below, both vs depth. Independent cross-check of the
mesh-measured 410 displacement/width.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/plot_depth_average.py \\
      --plot-box <uid ...> --plot-sink <uid ...> --fig-dir figs/benchmarks
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import load_depth_average, uid_label


def plot_set(runs, title, out_path):
    fig, ax = plt.subplots(2, 1, figsize=(8, 8), sharey=True)
    plotted, temps = 0, []
    for run in runs:
        profile = load_depth_average(run)
        if profile is None:
            continue
        plotted += 1
        temps.append(profile["temperature"])
        ax[0].plot(profile["temperature"], profile["depth_km"], label=uid_label(run), lw=1.2, alpha=0.85)
        ax[1].plot(profile["xi"], profile["depth_km"], label=uid_label(run), lw=1.2, alpha=0.85)
    if plotted == 0:
        print(f"skip {out_path.name}: no depth_average.txt found", file=sys.stderr)
        plt.close(fig)
        return
    ax[0].set_ylabel("depth [km]")
    ax[0].set_xlabel("temperature [K]")
    t = np.concatenate(temps)
    if np.nanmax(t) - np.nanmin(t) < 1e-6 * max(abs(np.nanmean(t)), 1.0):
        mid = float(np.nanmean(t))
        ax[0].set_xlim(mid - 5, mid + 5)
    ax[1].set_ylabel("depth [km]")
    ax[1].set_xlabel("xi_ol_wd [-]")
    ax[1].set_xlim(-0.05, 1.05)
    for a in ax:
        a.grid(True, alpha=0.3)
    ax[0].invert_yaxis()
    ax[0].legend(fontsize=8, loc="best")
    fig.suptitle(title)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    print(f"wrote {plotted} profiles -> {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot-box", nargs="*", default=[])
    ap.add_argument("--plot-sink", nargs="*", default=[])
    ap.add_argument("--fig-dir", default="figs/benchmarks")
    args = ap.parse_args()
    figdir = Path(args.fig_dir)
    plot_set(args.plot_box, "Box 1-reaction: depth-average final profiles", figdir / "depth_average_box.png")
    plot_set(args.plot_sink, "Sink block (full-res): depth-average final profiles", figdir / "depth_average_sink.png")


if __name__ == "__main__":
    main()
