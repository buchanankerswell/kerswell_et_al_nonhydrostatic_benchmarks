"""Mesh and step sensitivity of the dynamic-pressure range.

Reads the history summary plus the postprocessed boundary table and draws
a combined figure: largest pressure range against mesh refinement and
against the step size (shared y-axis), plus a 410-displacement-error figure
(measured front position minus the no-feedback equilibrium at the same
resolution, falling back to a fixed reference run when that resolution has
no no-feedback twin) against the same two axes.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/plot_mesh_step_sensitivity.py --summary simulation/results/pressure-history-summary.csv \\
    --postprocessed simulation/results/postprocessed.csv --out-dir figs/benchmarks \\
    --z-mid 4.44e-04 --cfl-sink 0.5
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

from simulation.mesh.config import BENCH_WIDE_W, apply_bench_style, bench_color, bench_label
from utils.logging import log_artifact, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"


def read_rows(path, want):
    if not os.path.exists(path):
        log_warn("skip: missing " + path)
        return []
    with open(path) as f:
        rows = [r for r in csv.DictReader(f) if all(k in r for k in want)]
    return rows


def boundary_offset(post, suite, z_mid, reference_run):
    """Front-position error vs the no-feedback equilibrium.

    Prefers a same-resolution no-feedback control. Runs at resolutions with no
    such twin fall back to the fixed reference run, so the mesh-sweep panels
    keep their Res5/Res7 points instead of going blank.
    """
    err = {}
    controls = {}
    global_ref = None
    for r in post:
        if r["suite"] != suite or r["z"] != z_mid:
            continue
        try:
            disp = float(r["disp410_km"])
        except ValueError:
            continue
        if r["dynp"] == "0" and r["damp"] == "None":
            controls[r["res"]] = disp
        key = r["run"] if "run" in r else r["model_id"]
        if key == reference_run:
            global_ref = disp
        err.setdefault(key, (r, disp))
    out = {}
    for run, (r, disp) in err.items():
        control = controls.get(r["res"])
        if control is None:
            control = global_ref
        out[run] = disp - control if control is not None else float("nan")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default=str(RESULTS / "pressure-history-summary.csv"), help="Pressure-history summary CSV path")
    ap.add_argument("--postprocessed", default=str(RESULTS / "postprocessed.csv"), help="Postprocessed boundary-table CSV path")
    ap.add_argument("--out-dir", default="figs/benchmarks", help="Output figure directory")
    ap.add_argument("--z-mid", default="4.44e-04", help="Intermediate reaction rate (1/s/K) (project.mk Z_MID)")
    ap.add_argument("--cfl-sink", type=float, default=0.5, help="Sink suite default CFL number, dimensionless (project.mk CFL_SINK)")
    ap.add_argument("--error-reference", default="NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6", help="Fallback no-feedback reference run (S2)")
    ap.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI; draft 100, manuscript 330)")
    args = ap.parse_args()
    apply_bench_style(args.dpi)

    base_cfl = {"sink": args.cfl_sink}
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
        for suite in ("sink",):
            offsets.update(boundary_offset(post, suite, args.z_mid, args.error_reference))

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    suite = "sink"

    # One figure, two panels sharing the pressure-range axis: largest
    # range against mesh refinement (left) and against step size (right).
    fig, (axm, axs) = plt.subplots(1, 2, figsize=(BENCH_WIDE_W, 3.0), sharey=True)
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
    for xs, ys, runs in zip([v[0] for v in by_damp.values()], [v[1] for v in by_damp.values()], [v[2] for v in by_damp.values()]):
        x = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
        keep = np.isfinite(x) & np.isfinite(y)
        if keep.sum() == 0:
            continue
        o = np.argsort(x[keep])
        run = runs[0]
        axm.plot(x[keep][o], y[keep][o], "o-", label=bench_label(run), color=bench_color(run))
    axm.set_xlabel("Mesh Refinement Level")
    axm.set_ylabel("Largest $\\hat{P}$ Range (MPa)")
    axm.set_xticks([5, 6, 7])

    sel = [r for r in records if r["suite"] == suite and r["z"] == args.z_mid and r["damp"] == "None"]
    for r in sel:
        try:
            cfl, rng = float(r["cfl"]), float(r["largest_range_MPa"])
        except ValueError:
            continue
        if np.isfinite(cfl) and np.isfinite(rng):
            axs.plot(cfl, rng, "o", label=bench_label(r["run"]), color=bench_color(r["run"]))
    axs.set_xlabel("Time Step (CFL Number)")
    axs.set_xticks([0.5, 1.0])
    axs.tick_params(axis="y", which="both", left=False, labelleft=False)
    handles, labels = axm.get_legend_handles_labels()
    for h, lab in zip(*axs.get_legend_handles_labels()):
        if lab not in labels:
            handles.append(h)
            labels.append(lab)
    fig.subplots_adjust(right=0.74, wspace=0.08, left=0.09, top=0.94, bottom=0.13)
    fig.legend(handles, labels, loc="center left", bbox_to_anchor=(0.75, 0.5), frameon=True, facecolor="white", framealpha=0.9)
    fig.savefig(outdir / "range-sensitivity-sink.png", dpi=args.dpi)
    plt.close(fig)
    log_artifact(outdir / "range-sensitivity-sink.png")

    if offsets:
        # Front-position error: measured 410 displacement minus the
        # equilibrium no-feedback displacement at the same resolution.
        # Left panel varies mesh refinement, right panel varies step size.
        fig, (axr, axc) = plt.subplots(1, 2, figsize=(BENCH_WIDE_W, 3.0), sharey=True)
        sel = [r for r in records if r["suite"] == suite and r["z"] == args.z_mid]
        by_damp = {}
        for r in sel:
            off = offsets.get(r["run"], float("nan"))
            try:
                res, cfl, off = int(r["res"]), float(r.get("cfl") or base_cfl[suite]), float(off)
            except (ValueError, TypeError):
                continue
            if np.isfinite(off):
                by_damp.setdefault((r["damp"], r["dynp"]), ([], [], []))
                by_damp[(r["damp"], r["dynp"])][0].append(res)
                by_damp[(r["damp"], r["dynp"])][1].append(off)
                by_damp[(r["damp"], r["dynp"])][2].append(r["run"])
        for xs, ys, runs in zip([v[0] for v in by_damp.values()], [v[1] for v in by_damp.values()], [v[2] for v in by_damp.values()]):
            x = np.asarray(xs, dtype=float)
            y = np.asarray(ys, dtype=float)
            o = np.argsort(x)
            axr.plot(x[o], y[o], "o-", label=bench_label(runs[0]), color=bench_color(runs[0]))
        axr.set_xlabel("Mesh Refinement Level")
        axr.set_ylabel("410 Position Error vs No-Feedback (km)")
        axr.set_xticks([5, 6, 7])
        for r in sel:
            off = offsets.get(r["run"], float("nan"))
            try:
                cfl, off = float(r.get("cfl") or base_cfl[suite]), float(off)
            except (ValueError, TypeError):
                continue
            if np.isfinite(off):
                axc.plot(cfl, off, "o", label=bench_label(r["run"]), color=bench_color(r["run"]))
        axc.set_xlabel("Time Step (CFL Number)")
        axc.set_xticks([0.5, 1.0])
        axc.tick_params(axis="y", which="both", left=False, labelleft=False)
        handles, labels = axr.get_legend_handles_labels()
        for h, lab in zip(*axc.get_legend_handles_labels()):
            if lab not in labels:
                handles.append(h)
                labels.append(lab)
        fig.subplots_adjust(left=0.16, right=0.76, top=0.92, bottom=0.15, wspace=0.1)
        fig.legend(handles, labels, loc="center left", bbox_to_anchor=(0.77, 0.5), frameon=True, facecolor="white", framealpha=0.9)
        fig.savefig(outdir / "displacement-error-sink.png", dpi=args.dpi)
        plt.close(fig)
        log_artifact(outdir / "displacement-error-sink.png")


if __name__ == "__main__":
    sys.exit(main())
