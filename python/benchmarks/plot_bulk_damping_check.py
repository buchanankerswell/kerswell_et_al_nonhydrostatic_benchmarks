"""Bulk-damping resolution check.

Reads the mesh structure summaries and focuses on the implicit-bulk damping
across resolutions: final-step highest reaction rate against mesh refinement,
plus the rate history that exposes the Res6 transient spike.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/plot_bulk_damping_check.py --fig-dir figs/benchmarks
"""

import argparse
import os
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import apply_bench_style

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"

apply_bench_style()


def load(suite):
    path = RESULTS / f"structure-summary-{suite}.csv"
    if not path.exists() or path.stat().st_size < 2:
        print(f"skip {suite}: {path} not found", file=sys.stderr)
        return None
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        print(f"skip {suite}: {path} empty", file=sys.stderr)
        return None
    if df.empty:
        print(f"skip {suite}: {path} empty", file=sys.stderr)
        return None
    df["res"] = df["model_id"].str.extract(r"_Res(\d+)").astype(int)
    df["damp"] = df["model_id"].str.extract(r"_Damp([A-Za-z]+[\d.e+-]*)")
    df["z"] = df["model_id"].str.extract(r"_Z([\d.e+-]+)")
    df["dynp"] = df["model_id"].str.contains("_DynpOn_")
    rate_col = next((c for c in df.columns if "reaction_rate" in c and "410" in c), None)
    if rate_col is None:
        print(f"skip {suite}: no rate column in {list(df.columns)}", file=sys.stderr)
        return None
    df["rate"] = pd.to_numeric(df[rate_col], errors="coerce").abs()
    return df


def panel_rate_vs_res(ax, df):
    sub = df[df["damp"].str.contains("Bimpl|None", na=False)]
    final = sub.sort_values("timestep").groupby("model_id").tail(1)
    for (damp, z), grp in final.groupby(["damp", "z"]):
        grp = grp.sort_values("res")
        kw = dict(lw=2.5) if damp == "None" else dict(lw=1.2, marker="o")
        ax.plot(grp["res"], grp["rate"], label=f"{damp} Z{z}", **kw)
    ax.set_yscale("log")
    ax.set_xlabel("Mesh Refinement Level")
    ax.set_ylabel("Final Highest $\\dot{X}$ (1/s)")
    ax.legend(fontsize=11, loc="upper right", frameon=False)


def panel_history(ax, df, damp_pat="Bimpl1e21"):
    sub = df[df["damp"] == damp_pat].copy()
    if sub.empty:
        sub = df[df["damp"].str.contains("Bimpl", na=False)].copy()
    for mid, grp in sub.groupby("model_id"):
        m = re.search(r"_Res(\d+)", mid)
        mz = re.search(r"_Z([\d.e+-]+)", mid)
        tag = f"Level {m.group(1)}" if m else mid
        if mz:
            tag += f" Z{mz.group(1)}"
        ax.plot(grp["timestep"], grp["rate"], label=tag, lw=1.5)
    ax.set_yscale("log")
    ax.set_xlabel("Output Step")
    ax.set_ylabel("Highest $\\dot{X}$ (1/s)")
    ax.legend(fontsize=11, loc="upper right", frameon=False)


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
        bulk = final[final["damp"].str.contains("Bimpl", na=False)].sort_values(["damp", "res"])
        print(f"--- {suite} bulk-damping final highest rate vs resolution ---")
        for _, r in bulk.iterrows():
            print(f"  {r['model_id']}: {r['rate']:.3e} 1/s")
        ctrl = final[final["damp"] == "None"].sort_values("res")
        print(f"--- {suite} DampNone control ---")
        for _, r in ctrl.iterrows():
            print(f"  {r['model_id']}: {r['rate']:.3e} 1/s")

        fig, ax = plt.subplots(1, 2, figsize=(12, 5))
        panel_rate_vs_res(ax[0], df)
        damp_pat = "Bimpl1e21" if suite == "box" else "Bimpl1e19"
        panel_history(ax[1], df, damp_pat)
        fig.tight_layout()
        out = figdir / f"bulk_damping_check_{suite}.png"
        fig.savefig(out, dpi=300)
        plt.close(fig)
        print(f"wrote -> {out}")


if __name__ == "__main__":
    sys.exit(main())
