"""Dedicated Bimpl resolution-instability diagnostic.

Reads the mesh structure summaries and focuses on the implicit-bulk damping
across resolutions: final-timestep max reaction rate vs global refinement,
plus the rate history that exposes the Res6 transient spike.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/plot_bimpl_resolution.py --fig-dir figs/benchmarks
"""

import argparse
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RESULTS = Path("simulation/results")


def load(suite):
    path = RESULTS / f"structure-summary-{suite}.csv"
    if not path.exists():
        print(f"skip {suite}: {path} not found", file=sys.stderr)
        return None
    df = pd.read_csv(path)
    df["res"] = df["model_id"].str.extract(r"_Res(\d+)").astype(int)
    df["damp"] = df["model_id"].str.extract(r"_Damp([A-Za-z]+[\d.e]*)")
    df["dynp"] = df["model_id"].str.contains("_DynpOn_")
    rate_col = next((c for c in df.columns if "reaction_rate" in c and "410" in c), None)
    if rate_col is None:
        print(f"skip {suite}: no rate column in {list(df.columns)}", file=sys.stderr)
        return None
    df["rate"] = pd.to_numeric(df[rate_col], errors="coerce").abs()
    return df


def panel_rate_vs_res(ax, df, title):
    sub = df[df["damp"].str.contains("Bimpl|None", na=False)]
    final = sub.sort_values("timestep").groupby("model_id").tail(1)
    for damp, grp in final.groupby("damp"):
        grp = grp.sort_values("res")
        kw = dict(lw=2.5) if damp == "None" else dict(lw=1.2, marker="o")
        ax.plot(grp["res"], grp["rate"], label=damp, **kw)
    ax.set_yscale("log")
    ax.set_xlabel("global refinement (Res)")
    ax.set_ylabel("final max |rate| [1/s]")
    ax.set_title(title)
    ax.grid(True, alpha=0.3, which="both")
    ax.legend(fontsize=8, loc="best")


def panel_history(ax, df, title, damp_pat="Bimpl1e21"):
    sub = df[df["damp"] == damp_pat].copy()
    if sub.empty:
        sub = df[df["damp"].str.contains("Bimpl", na=False)].copy()
    for mid, grp in sub.groupby("model_id"):
        m = re.search(r"_Res(\d+)", mid)
        ax.plot(grp["timestep"], grp["rate"], label=f"Res{m.group(1)}" if m else mid, lw=1.5)
    ax.set_yscale("log")
    ax.set_xlabel("output timestep")
    ax.set_ylabel("max |rate| [1/s]")
    ax.set_title(title)
    ax.grid(True, alpha=0.3, which="both")
    ax.legend(fontsize=8, loc="best")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fig-dir", default="figs/benchmarks")
    args = ap.parse_args()
    figdir = Path(args.fig_dir)
    figdir.mkdir(parents=True, exist_ok=True)

    for suite in ("box", "sink"):
        df = load(suite)
        if df is None or df.empty:
            continue
        final = df.sort_values("timestep").groupby("model_id").tail(1)
        bimpl = final[final["damp"].str.contains("Bimpl", na=False)].sort_values(["damp", "res"])
        print(f"--- {suite} Bimpl final max|rate| vs Res ---")
        for _, r in bimpl.iterrows():
            print(f"  {r['model_id']}: {r['rate']:.3e} 1/s")
        ctrl = final[final["damp"] == "None"].sort_values("res")
        print(f"--- {suite} DampNone control ---")
        for _, r in ctrl.iterrows():
            print(f"  {r['model_id']}: {r['rate']:.3e} 1/s")

        fig, ax = plt.subplots(1, 2, figsize=(12, 5))
        panel_rate_vs_res(ax[0], df, f"{suite}: final max rate vs resolution")
        damp_pat = "Bimpl1e21" if suite == "box" else "Bimpl1e19"
        panel_history(ax[1], df, f"{suite}: Bimpl rate history", damp_pat)
        fig.suptitle(f"{suite}: implicit-bulk resolution robustness")
        fig.tight_layout()
        out = figdir / f"bimpl_resolution_{suite}.png"
        fig.savefig(out, dpi=110)
        plt.close(fig)
        print(f"wrote -> {out}")


if __name__ == "__main__":
    sys.exit(main())
