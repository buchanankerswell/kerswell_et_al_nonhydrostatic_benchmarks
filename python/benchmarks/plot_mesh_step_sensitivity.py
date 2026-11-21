"""Mesh and step sensitivity of the dynamic-pressure range.

Reads the history summary plus the postprocessed boundary table and draws
two figures: largest pressure range against mesh refinement, and against
the step size. Boundary offset is measured against the no-feedback control
at the same resolution. Panels with fewer than two points print a note
instead of a line.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python
    python/benchmarks/plot_mesh_step_sensitivity.py --summary simulation/results/pressure-history-summary.csv
    --postprocessed simulation/results/postprocessed.csv --out-dir figs/benchmarks
    --z-mid 4.44e-04 --cfl-box 0.7 --cfl-sink 0.5
"""

import argparse
import csv
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from simulation.mesh.config import apply_bench_style, bench_color, bench_label
from utils.logging import log_artifact, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"

apply_bench_style()


def read_rows(path, want):
    if not os.path.exists(path):
        log_warn("skip: missing " + path)
        return []
    with open(path) as f:
        rows = [r for r in csv.DictReader(f) if all(k in r for k in want)]
    return rows


def boundary_offset(post, suite, z_mid):
    err = {}
    controls = {}
    for r in post:
        if r["suite"] != suite or r["z"] != z_mid:
            continue
        try:
            disp = float(r["disp410_km"])
        except ValueError:
            continue
        if r["dynp"] == "0" and r["damp"] == "None":
            controls[r["res"]] = disp
        err.setdefault(r["run"] if "run" in r else r["model_id"], (r, disp))
    out = {}
    for run, (r, disp) in err.items():
        control = controls.get(r["res"])
        out[run] = disp - control if control is not None else float("nan")
    return out


def panel(ax, xs, ys, runs, xlabel, ylabel, logx=False, colors=None):
    seen = False
    for x, y, run in zip(xs, ys, runs):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        keep = np.isfinite(x) & np.isfinite(y)
        if keep.sum() == 0:
            continue
        seen = True
        o = np.argsort(x[keep])
        ax.plot(x[keep][o], y[keep][o], "o-", label=bench_label(run), color=bench_color(run) if colors is None else colors)
    if not seen:
        ax.text(0.5, 0.5, "no data yet", transform=ax.transAxes, ha="center")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if logx:
        ax.set_xscale("log", base=2)
    if seen:
        ax.legend(fontsize=9, loc="best", frameon=True, facecolor="white", framealpha=0.9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default=str(RESULTS / "pressure-history-summary.csv"), help="Pressure-history summary CSV path")
    ap.add_argument("--postprocessed", default=str(RESULTS / "postprocessed.csv"), help="Postprocessed boundary-table CSV path")
    ap.add_argument("--out-dir", default="figs/benchmarks", help="Output figure directory")
    ap.add_argument("--z-mid", default="4.44e-04", help="Intermediate reaction rate (1/s/K) (project.mk Z_MID)")
    ap.add_argument("--cfl-box", type=float, default=0.7, help="Box suite default CFL number, dimensionless (project.mk CFL_BOX)")
    ap.add_argument("--cfl-sink", type=float, default=0.5, help="Sink suite default CFL number, dimensionless (project.mk CFL_SINK)")
    args = ap.parse_args()

    base_cfl = {"box": args.cfl_box, "sink": args.cfl_sink}
    records = read_rows(args.summary, ["suite", "run", "largest_range_MPa", "res", "z", "damp", "dynp"])
    post = read_rows(args.postprocessed, ["suite", "model_id", "disp410_km", "res", "z", "damp", "dynp"])
    if not records:
        log_warn("no history summary rows; nothing to plot")
        return
    for r in records:
        r["cfl"] = r.get("cfl") or ""
        if r["cfl"] == "":
            r["cfl"] = base_cfl.get(r["suite"], float("nan"))
    offsets = {}
    if post:
        for suite in ("box", "sink"):
            offsets.update(boundary_offset(post, suite, args.z_mid))

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for i, suite in enumerate(("box", "sink")):
        sel = [r for r in records if r["suite"] == suite and r["z"] == args.z_mid]
        by_damp = {}
        for r in sel:
            by_damp.setdefault((r["damp"], r["dynp"]), ([], [], []))
            try:
                by_damp[(r["damp"], r["dynp"])][0].append(int(r["res"]))
                by_damp[(r["damp"], r["dynp"])][1].append(float(r["largest_range_MPa"]))
                by_damp[(r["damp"], r["dynp"])][2].append(r["run"])
            except ValueError:
                continue
        panel(
            ax[i],
            [v[0] for v in by_damp.values()],
            [v[1] for v in by_damp.values()],
            [v[2][0] for v in by_damp.values()],
            "Mesh Refinement Level",
            "Largest $\\hat{P}$ Range (MPa)",
            logx=True,
        )
    fig.tight_layout()
    fig.savefig(outdir / "mesh-sensitivity.png", dpi=300)
    plt.close(fig)
    log_artifact(outdir / "mesh-sensitivity.png")

    fig, ax = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for i, suite in enumerate(("box", "sink")):
        sel = [r for r in records if r["suite"] == suite and r["z"] == args.z_mid and r["damp"] == "None"]
        xs = [[float(r["cfl"])] for r in sel]
        ys = [[float(r["largest_range_MPa"])] for r in sel]
        runs = [r["run"] for r in sel]
        panel(ax[i], xs, ys, runs, "Time Step (CFL Number)", "Largest $\\hat{P}$ Range (MPa)")
    fig.tight_layout()
    fig.savefig(outdir / "step-sensitivity.png", dpi=300)
    plt.close(fig)
    log_artifact(outdir / "step-sensitivity.png")

    if offsets:
        fig, ax = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
        for i, suite in enumerate(("box", "sink")):
            sel = [r for r in records if r["suite"] == suite and r["z"] == args.z_mid]
            xs = [[float(r.get("cfl") or base_cfl[suite])] for r in sel]
            ys = [[offsets.get(r["run"], float("nan"))] for r in sel]
            runs = [r["run"] for r in sel]
            panel(ax[i], xs, ys, runs, "Time Step (CFL Number)", "Boundary Offset From Control (km)")
        fig.tight_layout()
        fig.savefig(outdir / "step-boundary-error.png", dpi=300)
        plt.close(fig)
        log_artifact(outdir / "step-boundary-error.png")


if __name__ == "__main__":
    sys.exit(main())
