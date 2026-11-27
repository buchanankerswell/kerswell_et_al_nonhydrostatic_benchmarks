"""Final-state depth profiles of phase fraction, driving energy, rate, and pressure."""

import argparse
import os
import pickle
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

from benchmarks.common import reference_adiabatic_pressure
from simulation.mesh.config import BENCH_WIDE_W, apply_bench_style, bench_color, bench_label
from simulation.params.transitions import (
    find_surface_depth_offset,
    find_transition,
    load_depth_datum,
    model_to_true_km,
    read_dG_profile,
)
from utils.artifacts import add_force_argument, outputs_exist
from utils.logging import log_artifact, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"
DATUM = RESULTS.parent / "data" / "depth-datum.tsv"


def clean(field):
    z = np.asarray(field["depths"], float)
    v = np.asarray(field["values"], float)
    m = np.isfinite(z) & np.isfinite(v)
    o = np.argsort(z[m])
    return z[m][o] / 1e3, v[m][o]


def load_rep(run, tag):
    if not (RESULTS / run / "solution" / "solution-00020.pvtu").exists():
        raise OSError(f"incomplete run (no final output): {run}")
    with open(RESULTS / f"seismic-profile-cache-{tag}.pkl", "rb") as f:
        seis = pickle.load(f)
    ts = max(seis[run].keys())
    return seis[run][ts]["representative"], ts


def profile_equilibrium(profile_path, model_height, surface_pressure):
    headers, data = read_dG_profile(profile_path)
    offset = find_surface_depth_offset(headers, data, surface_pressure)
    pt = find_transition(headers, data, model_height, offset)
    col = {h: i for i, h in enumerate(headers)}
    order = np.argsort(data[:, col["depth"]])
    dep = data[order][:, col["depth"]]
    pre = data[order][:, col["pressure"]]
    prof_depth = pt.depth + offset
    peq = float(np.interp(prof_depth, dep, pre))
    return pt.depth / 1e3, peq, pt.clapeyron


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="Run UIDs to plot")
    ap.add_argument("--suite-tag", required=True, help="Suite tag: sink")
    ap.add_argument("--profile", required=True, help="Olivine-wadsleyite thermodynamic profile TSV path")
    ap.add_argument("--model-height", type=float, required=True, help="Model height (m)")
    ap.add_argument("--surface-pressure", type=float, required=True, help="Surface pressure (Pa)")
    ap.add_argument("--depth-corr-ol-wd", type=float, default=5e3, help="Depth correction for the olivine-wadsleyite transition (m)")
    ap.add_argument("--nominal-m", type=float, default=None, help="Runtime-adiabat 410 nominal (m); defaults to profile + depth correction")
    ap.add_argument("--out", required=True, help="Output figure path")
    ap.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI; draft 100, manuscript 330)")
    add_force_argument(ap)
    args = ap.parse_args()

    if outputs_exist(args.out, args.force):
        return

    apply_bench_style(args.dpi)

    prof_eq, prof_peq, gamma = profile_equilibrium(args.profile, args.model_height, args.surface_pressure)
    nominal = args.nominal_m / 1e3 if args.nominal_m is not None else prof_eq + args.depth_corr_ol_wd / 1e3
    datum = load_depth_datum(str(DATUM))
    suite = args.suite_tag
    nominal_true = float(model_to_true_km(nominal, datum, suite))

    fig, ax = plt.subplots(1, 4, figsize=(BENCH_WIDE_W, 3.2), sharey=True)
    fig.subplots_adjust(wspace=0.25, left=0.08, right=0.78, top=0.92, bottom=0.15)
    for run in args.runs:
        try:
            rep, ts = load_rep(run, args.suite_tag)
        except (OSError, KeyError) as e:
            log_warn(f"skip {run} ({e})")
            continue
        zx, xi = clean(rep["xi_ol_wd"])
        zd, dg = clean(rep["dG_driving_0"])
        zr, rate = clean(rep["reaction_rate_C0"])
        zp, p = clean(rep["p"])
        za, pa = clean(rep["adiabatic_pressure"])
        tx = model_to_true_km(zx, datum, suite)
        tr = model_to_true_km(zr, datum, suite)
        kw = dict(lw=2.2, alpha=0.9, label=bench_label(run), color=bench_color(run))
        ax[0].plot(xi, tx, **kw)
        ax[1].plot(dg, model_to_true_km(zd, datum, suite), **kw)
        ax[2].plot(rate, tr, **kw)
        pmod = np.interp(zx, zp, p)
        y_m = args.model_height - zx * 1e3
        pad_fallback = np.interp(zx, za, pa)
        pad = reference_adiabatic_pressure(y_m, pad_fallback, step_num=ts, results_dir=RESULTS) / 1e9
        ax[3].plot(pmod - pad, tx, **kw)
    for a in ax:
        a.axhline(nominal_true, color="grey", lw=1.5, ls="--")
        a.invert_yaxis()
        a.set_ylim(float(model_to_true_km(500, datum, suite)), float(model_to_true_km(250, datum, suite)))
        a.xaxis.set_major_locator(MaxNLocator(nbins=3))
    for a in ax[1:]:
        a.tick_params(axis="y", which="both", left=False, labelleft=False)
    ax[0].set_xlabel("$\\xi$")
    ax[0].set_xlim(-0.05, 1.05)
    ax[1].set_xlabel("$dG$ (kJ/mol)")
    ax[2].set_xlabel("$\\dot{X}$ (1/Ma)")
    ax[3].set_xlabel("$\\hat{P}$ (GPa)")
    ax[0].set_ylabel("Depth (km)")
    handles, labels = ax[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="center left", bbox_to_anchor=(0.79, 0.5), frameon=True, facecolor="white", framealpha=0.9)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi)
    plt.close(fig)
    log_artifact(args.out)


if __name__ == "__main__":
    sys.exit(main())
