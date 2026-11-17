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
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS = Path("simulation/results")


def short(run):
    m = re.search(r"_Damp([A-Za-z]+)([\d.e]*)", run)
    damp = (m.group(1) + m.group(2)) if m else run
    mref = re.search(r"_Res(\d+)", run)
    return f"{damp}[r{mref.group(1)}]" if mref else damp


def load_depth_average(run):
    path = RESULTS / run / "depth_average.txt"
    if not path.exists():
        return None
    column_names, data_rows = None, []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                column_names = s[1:].split()
                continue
            data_rows.append([float(x) for x in s.split()])
    if not data_rows or column_names is None or len(column_names) < 3:
        return None
    data = np.array(data_rows)
    times = np.unique(data[:, 0])
    last = data[data[:, 0] == times[-1]]
    try:
        temperature_index = column_names.index("temperature")
    except ValueError:
        return None
    xi_index = next((i for i, n in enumerate(column_names) if n.startswith("xi_")), None)
    if xi_index is None:
        return None
    return {"depth_km": last[:, 1] / 1e3, "temperature": last[:, temperature_index], "xi": last[:, xi_index]}


def plot_set(runs, title, out_path):
    fig, ax = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    plotted = 0
    for run in runs:
        profile = load_depth_average(run)
        if profile is None:
            continue
        plotted += 1
        ax[0].plot(profile["temperature"], profile["depth_km"], label=short(run), lw=1.2, alpha=0.85)
        ax[1].plot(profile["xi"], profile["depth_km"], label=short(run), lw=1.2, alpha=0.85)
    if plotted == 0:
        print(f"skip {out_path.name}: no depth_average.txt found", file=sys.stderr)
        plt.close(fig)
        return
    ax[0].set_ylabel("depth [km]")
    ax[0].set_xlabel("temperature [K]")
    ax[1].set_ylabel("depth [km]")
    ax[1].set_xlabel("xi_ol_wd [-]")
    ax[1].set_xlim(-0.05, 1.05)
    for a in ax:
        a.invert_yaxis()
        a.grid(True, alpha=0.3)
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
    ap.add_argument("--plot-laptop", nargs="*", default=[])
    ap.add_argument("--fig-dir", default="figs/benchmarks")
    args = ap.parse_args()
    figdir = Path(args.fig_dir)
    plot_set(args.plot_box, "Box 1-reaction: depth-average final profiles", figdir / "depth_average_box.png")
    plot_set(args.plot_sink, "Sink block (full-res): depth-average final profiles", figdir / "depth_average_sink.png")
    plot_set(args.plot_laptop, "Sink block (laptop): depth-average final profiles", figdir / "depth_average_sink_laptop.png")


if __name__ == "__main__":
    main()
