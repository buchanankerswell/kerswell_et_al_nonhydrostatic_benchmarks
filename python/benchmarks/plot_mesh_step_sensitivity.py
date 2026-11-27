"""Mesh and time-step sensitivity of pressure range and 410 position error."""

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
from utils.artifacts import add_force_argument, outputs_exist
from utils.logging import log_artifact, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"


def read_rows(path, want):
    if not os.path.exists(path):
        log_warn(f"skip {path} (missing)")
        return []
    with open(path) as f:
        rows = [r for r in csv.DictReader(f) if all(k in r for k in want)]
    return rows


def boundary_offset(post, suite, z_mid, reference_run):
    """410 position error vs no feedback; missing resolutions use the fixed reference."""
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


def shared_legend(fig, ax_left, ax_right):
    handles, labels = ax_left.get_legend_handles_labels()
    for h, lab in zip(*ax_right.get_legend_handles_labels()):
        if lab not in labels:
            handles.append(h)
            labels.append(lab)
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.34), ncol=3, frameon=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default=str(RESULTS / "pressure-history-summary.csv"), help="Pressure-history summary CSV path")
    ap.add_argument("--postprocessed", default=str(RESULTS / "postprocessed.csv"), help="Postprocessed boundary-table CSV path")
    ap.add_argument("--out-dir", default="figs/benchmarks", help="Output figure directory")
    ap.add_argument("--z-mid", default="4.44e-04", help="Intermediate reaction rate (1/s/K) (project.mk Z_MID)")
    ap.add_argument("--cfl-sink", type=float, default=0.5, help="Sink suite default CFL number, dimensionless (project.mk CFL_SINK)")
    ap.add_argument("--error-reference", default="NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6", help="Fallback no-feedback reference UID")
    ap.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI; draft 100, manuscript 330)")
    add_force_argument(ap)
    args = ap.parse_args()

    outdir = Path(args.out_dir)
    range_fig = outdir / "range-sensitivity-sink.png"
    error_fig = outdir / "displacement-error-sink.png"
    if outputs_exist([range_fig, error_fig], args.force):
        return

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

    outdir.mkdir(parents=True, exist_ok=True)
    suite = "sink"

    fig, (axm, axs) = plt.subplots(1, 2, figsize=(BENCH_WIDE_W, 4.8), sharey=True)
    sel_mesh = [r for r in records if r["suite"] == suite and r["z"] == args.z_mid and float(r["cfl"]) == base_cfl[suite]]
    by_damp = {}
    for r in sel_mesh:
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
    axm.set_xlabel("Mesh level")
    axm.set_ylabel(r"Largest $\hat{P}$ Range (MPa)")
    axm.set_xticks([5, 6, 7])

    sel_cfl = [r for r in records if r["suite"] == suite and r["z"] == args.z_mid and int(r["res"]) == 6]
    by_damp_cfl = {}
    for r in sel_cfl:
        by_damp_cfl.setdefault((r["damp"], r["dynp"]), ([], [], []))
        try:
            by_damp_cfl[(r["damp"], r["dynp"])][0].append(float(r["cfl"]))
            by_damp_cfl[(r["damp"], r["dynp"])][1].append(float(r["largest_range_MPa"]))
            by_damp_cfl[(r["damp"], r["dynp"])][2].append(r["run"])
        except ValueError:
            continue
    for xs, ys, runs in zip([v[0] for v in by_damp_cfl.values()], [v[1] for v in by_damp_cfl.values()], [v[2] for v in by_damp_cfl.values()]):
        x = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
        keep = np.isfinite(x) & np.isfinite(y)
        if keep.sum() == 0:
            continue
        o = np.argsort(x[keep])
        base_run = next((rn for rn in runs if "_CFL" not in rn), runs[0])
        axs.plot(x[keep][o], y[keep][o], "o-", label=bench_label(base_run), color=bench_color(base_run))
    axs.set_xlabel("Time step (CFL)")
    axs.set_xticks([0.25, 0.5, 1.0])
    axs.tick_params(axis="y", which="both", left=False, labelleft=False)
    shared_legend(fig, axm, axs)
    fig.subplots_adjust(left=0.16, right=0.97, wspace=0.22, top=0.92, bottom=0.42)
    fig.savefig(range_fig, dpi=args.dpi)
    plt.close(fig)
    log_artifact(range_fig)

    if offsets:
        fig, (axr, axc) = plt.subplots(1, 2, figsize=(BENCH_WIDE_W, 4.8), sharey=True)
        sel = [r for r in records if r["suite"] == suite and r["z"] == args.z_mid]
        by_damp = {}
        for r in sel:
            off = offsets.get(r["run"], float("nan"))
            try:
                res, cfl, off = int(r["res"]), float(r.get("cfl") or base_cfl[suite]), float(off)
            except (ValueError, TypeError):
                continue
            if np.isfinite(off) and cfl == base_cfl[suite]:
                by_damp.setdefault((r["damp"], r["dynp"]), ([], [], []))
                by_damp[(r["damp"], r["dynp"])][0].append(res)
                by_damp[(r["damp"], r["dynp"])][1].append(off)
                by_damp[(r["damp"], r["dynp"])][2].append(r["run"])
        for xs, ys, runs in zip([v[0] for v in by_damp.values()], [v[1] for v in by_damp.values()], [v[2] for v in by_damp.values()]):
            x = np.asarray(xs, dtype=float)
            y = np.asarray(ys, dtype=float)
            o = np.argsort(x)
            axr.plot(x[o], y[o], "o-", label=bench_label(runs[0]), color=bench_color(runs[0]))
        axr.set_xlabel("Mesh level")
        axr.set_ylabel("410 position error vs no feedback (km)")
        axr.set_xticks([5, 6, 7])
        by_damp_cfl = {}
        for r in sel:
            off = offsets.get(r["run"], float("nan"))
            try:
                res, cfl, off = int(r["res"]), float(r.get("cfl") or base_cfl[suite]), float(off)
            except (ValueError, TypeError):
                continue
            if np.isfinite(off) and res == 6:
                by_damp_cfl.setdefault((r["damp"], r["dynp"]), ([], [], []))
                by_damp_cfl[(r["damp"], r["dynp"])][0].append(cfl)
                by_damp_cfl[(r["damp"], r["dynp"])][1].append(off)
                by_damp_cfl[(r["damp"], r["dynp"])][2].append(r["run"])
        for xs, ys, runs in zip([v[0] for v in by_damp_cfl.values()], [v[1] for v in by_damp_cfl.values()], [v[2] for v in by_damp_cfl.values()]):
            x = np.asarray(xs, dtype=float)
            y = np.asarray(ys, dtype=float)
            o = np.argsort(x)
            base_run = next((rn for rn in runs if "_CFL" not in rn), runs[0])
            axc.plot(x[o], y[o], "o-", label=bench_label(base_run), color=bench_color(base_run))
        axc.set_xlabel("Time step (CFL)")
        axc.set_xticks([0.25, 0.5, 1.0])
        axc.tick_params(axis="y", which="both", left=False, labelleft=False)
        shared_legend(fig, axr, axc)
        fig.subplots_adjust(left=0.16, right=0.97, wspace=0.22, top=0.92, bottom=0.42)
        fig.savefig(error_fig, dpi=args.dpi)
        plt.close(fig)
        log_artifact(error_fig)


if __name__ == "__main__":
    sys.exit(main())
