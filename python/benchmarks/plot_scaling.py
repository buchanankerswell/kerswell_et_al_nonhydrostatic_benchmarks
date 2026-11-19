"""Mesh and timestep scaling of the dynamic-pressure wave.

Reads the wave summary plus the postprocessed front table and draws two
figures: peak wave size against mesh resolution, and against the CFL
timestep. Front error is measured against the no-feedback twin at the
same resolution. Panels with fewer than two points print a note instead
of a line.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python
    python/benchmarks/plot_scaling.py --summary simulation/results/pressure-wave-summary.csv
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

from common import apply_bench_style, uid_label

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"

apply_bench_style()


def read_rows(path, want):
    if not os.path.exists(path):
        print("skip: missing " + path, file=sys.stderr)
        return []
    with open(path) as f:
        rows = [r for r in csv.DictReader(f) if all(k in r for k in want)]
    return rows


def front_error(post, suite, z_mid):
    err = {}
    twins = {}
    for r in post:
        if r["suite"] != suite or r["z"] != z_mid:
            continue
        try:
            disp = float(r["disp410_km"])
        except ValueError:
            continue
        if r["dynp"] == "0" and r["damp"] == "None":
            twins[r["res"]] = disp
        err.setdefault(r["run"] if "run" in r else r["model_id"], (r, disp))
    out = {}
    for run, (r, disp) in err.items():
        twin = twins.get(r["res"])
        out[run] = disp - twin if twin is not None else float("nan")
    return out


def panel(ax, xs, ys, labels, xlabel, ylabel, title, logx=False):
    seen = False
    for x, y, lab in zip(xs, ys, labels):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        keep = np.isfinite(x) & np.isfinite(y)
        if keep.sum() == 0:
            continue
        seen = True
        o = np.argsort(x[keep])
        ax.plot(x[keep][o], y[keep][o], "o-", label=lab)
    if not seen:
        ax.text(0.5, 0.5, "no data yet", transform=ax.transAxes, ha="center")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if logx:
        ax.set_xscale("log", base=2)
    ax.legend(fontsize=9, frameon=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default=str(RESULTS / "pressure-wave-summary.csv"))
    ap.add_argument("--postprocessed", default=str(RESULTS / "postprocessed.csv"))
    ap.add_argument("--out-dir", default="figs/benchmarks")
    ap.add_argument("--z-mid", default="4.44e-04")
    ap.add_argument("--cfl-box", type=float, default=0.7)
    ap.add_argument("--cfl-sink", type=float, default=0.5)
    args = ap.parse_args()

    base_cfl = {"box": args.cfl_box, "sink": args.cfl_sink}
    waves = read_rows(args.summary, ["suite", "run", "peak_p2p_MPa", "res", "z", "damp", "dynp"])
    post = read_rows(args.postprocessed, ["suite", "model_id", "disp410_km", "res", "z", "damp", "dynp"])
    if not waves:
        print("no wave summary rows; nothing to plot", file=sys.stderr)
        return
    for r in waves:
        r["cfl"] = r.get("cfl") or ""
        if r["cfl"] == "":
            r["cfl"] = base_cfl.get(r["suite"], float("nan"))
    err = {}
    if post:
        for suite in ("box", "sink"):
            err.update(front_error(post, suite, args.z_mid))

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for i, suite in enumerate(("box", "sink")):
        sel = [r for r in waves if r["suite"] == suite and r["z"] == args.z_mid]
        by_damp = {}
        for r in sel:
            by_damp.setdefault((r["damp"], r["dynp"]), ([], [], []))
            try:
                by_damp[(r["damp"], r["dynp"])][0].append(int(r["res"]))
                by_damp[(r["damp"], r["dynp"])][1].append(float(r["peak_p2p_MPa"]))
                by_damp[(r["damp"], r["dynp"])][2].append(r["run"])
            except ValueError:
                continue
        panel(
            ax[i],
            [v[0] for v in by_damp.values()],
            [v[1] for v in by_damp.values()],
            [uid_label(v[2][0]) for v in by_damp.values()],
            "global refinement (Res)",
            "peak wave size (MPa)",
            suite + ": wave size vs mesh",
            logx=True,
        )
    fig.tight_layout()
    fig.savefig(outdir / "scaling_h.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for i, suite in enumerate(("box", "sink")):
        sel = [r for r in waves if r["suite"] == suite and r["z"] == args.z_mid and r["damp"] == "None"]
        xs = [[float(r["cfl"])] for r in sel]
        ys = [[float(r["peak_p2p_MPa"])] for r in sel]
        labs = [uid_label(r["run"]) + (" (twin)" if str(r["dynp"]) == "0" else "") for r in sel]
        panel(ax[i], xs, ys, labs, "CFL number", "peak wave size (MPa)", suite + ": wave size vs timestep")
    fig.tight_layout()
    fig.savefig(outdir / "scaling_dt.png", dpi=300)
    plt.close(fig)

    if err:
        fig, ax = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
        for i, suite in enumerate(("box", "sink")):
            sel = [r for r in waves if r["suite"] == suite and r["z"] == args.z_mid]
            xs = [[float(r.get("cfl") or base_cfl[suite])] for r in sel]
            ys = [[err.get(r["run"], float("nan"))] for r in sel]
            labs = [uid_label(r["run"]) for r in sel]
            panel(ax[i], xs, ys, labs, "CFL number", "front error vs twin (km)", suite + ": front error vs timestep")
        fig.tight_layout()
        fig.savefig(outdir / "scaling_dt_error.png", dpi=300)
        plt.close(fig)
    print("plots -> " + str(outdir))


if __name__ == "__main__":
    sys.exit(main())
