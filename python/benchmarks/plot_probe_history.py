"""Per-step probe history: Stokes P, relaxed pbar, and xi at fixed points.

The relaxed_pressure field is initialized to an analytic lithostatic
(rho=3900, g=10) and, with tau = 0, frozen per parcel: its Eulerian
decline at a fixed probe then measures slow background creep advecting
the initial gradient, not a true pressure change. Stokes P at the same
probe stays flat. Prints linear decline slopes per run and probe.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/plot_probe_history.py --runs <uid ...> \\
      --out figs/benchmarks/probe_history_box.png --title "..."
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
    mo = re.search(r"_Dynp(On|Off)_", run)
    dyn = f" {mo.group(1)}" if mo else ""
    mref = re.search(r"_Res(\d+)", run)
    return f"{damp}{dyn}[r{mref.group(1)}]" if mref else f"{damp}{dyn}"


def load_probes(run):
    cols, blocks, cur = None, [], []
    with open(RESULTS / run / "point_values.txt") as f:
        for line in f:
            s = line.strip()
            if s.startswith("#"):
                cols = [w.strip("<>") for w in s[1:].split()]
                continue
            if not s:
                if cur:
                    blocks.append(cur)
                    cur = []
                continue
            cur.append([float(x) for x in s.split()])
    if cur:
        blocks.append(cur)
    a = np.array(blocks)
    return cols, a


def slope(t, v):
    m = np.isfinite(t) & np.isfinite(v) & (t > 0.2 * t.max())
    if m.sum() < 3:
        return float("nan")
    return float(np.polyfit(t[m], v[m], 1)[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="")
    args = ap.parse_args()

    fig, ax = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
    for run in args.runs:
        try:
            cols, a = load_probes(run)
        except OSError as e:
            print(f"skip {run}: {e}", file=sys.stderr)
            continue
        ti, pi, ri, xi, vy = (cols.index(k) for k in ("time", "pressure", "relaxed_pressure", "xi_ol_wd", "velocity_y"))
        t = a[:, 0, ti] / 1e6
        for p, ls in ((0, "-"), (1, "--")):
            kw = dict(lw=1.2, alpha=0.85, ls=ls)
            ax[0].plot(t, a[:, p, pi] / 1e6, label=short(run) if p == 0 else None, **kw)
            ax[1].plot(t, a[:, p, ri] / 1e6, **kw)
            ax[2].plot(t, a[:, p, xi], **kw)
        sp0 = slope(t, a[:, 0, ri] / 1e6)
        sp1 = slope(t, a[:, 1, ri] / 1e6)
        flip = t[np.where(a[:, 0, xi] < 0.5)[0][0]] if (a[:, 0, xi] < 0.5).any() else float("nan")
        dy0 = float(np.sum(0.5 * (a[1:, 0, vy] + a[:-1, 0, vy]) * np.diff(a[:, 0, ti]))) / 1e3
        dy1 = float(np.sum(0.5 * (a[1:, 1, vy] + a[:-1, 1, vy]) * np.diff(a[:, 0, ti]))) / 1e3
        dp0 = float(a[-1, 0, ri] - a[0, 0, ri]) / 1e6
        print(
            f"{short(run)}: pbar slope p0 {sp0:.0f} MPa/Myr, p1 {sp1:.0f} MPa/Myr, "
            f"xi-flip p0 at {flip:.2f} Myr, cum dy p0 {dy0:.0f} km -> adv {39 * -dy0:.0f} MPa vs actual {dp0:.0f} MPa, "
            f"cum dy p1 {dy1:.0f} km"
        )
    ax[0].set_ylabel("Stokes P [MPa]")
    ax[1].set_ylabel("relaxed pbar [MPa]")
    ax[2].set_ylabel("xi_ol_wd [-]")
    ax[2].set_xlabel("time [Myr]")
    for a_ in ax:
        a_.grid(True, alpha=0.3)
    ax[0].legend(fontsize=8, loc="best")
    fig.suptitle(args.title or "Probe history (solid p0/410, dashed p1)")
    fig.tight_layout()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=110)
    plt.close(fig)
    print(f"wrote -> {args.out}")


if __name__ == "__main__":
    sys.exit(main())
