"""Depth profiles for one suite: transformed fraction, driving energy, rate, and pressure.

Reads the mesh representative cache (final step) and overlays the
profile nominal 410 against the runtime dG = 0 crossing, locating the
max reaction rate in depth. Prints the offset numbers that separate
the static nominal-vs-runtime frame shift from dynamic-pressure effects.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/plot_depth_profiles.py --runs <uid ...> \\
      --suite-tag box --profile simulation/data/olivine-wadsleyite-profile-Mg100.tsv \\
      --out figs/benchmarks/depth-profiles-box.png
"""

import argparse
import os
import pickle
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from simulation.mesh.config import apply_bench_style, bench_color, bench_label
from simulation.params.transitions import (
    find_surface_depth_offset,
    find_transition,
    load_depth_datum,
    model_to_true_km,
    read_dG_profile,
)

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"
DATUM = RESULTS.parent / "data" / "depth-datum.tsv"

apply_bench_style()


def clean(field):
    z = np.asarray(field["depths"], float)
    v = np.asarray(field["values"], float)
    m = np.isfinite(z) & np.isfinite(v)
    o = np.argsort(z[m])
    return z[m][o] / 1e3, v[m][o]


def load_rep(run, tag):
    with open(RESULTS / f"seismic-profile-cache-{tag}.pkl", "rb") as f:
        seis = pickle.load(f)
    ts = max(seis[run].keys())
    return seis[run][ts]["representative"], ts


def zero_cross(z, v):
    s = np.sign(v)
    j = np.where(np.diff(s) != 0)[0]
    return [float(z[t] + (z[t + 1] - z[t]) * abs(v[t]) / (abs(v[t]) + abs(v[t + 1]))) for t in j]


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
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--suite-tag", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--model-height", type=float, required=True)
    ap.add_argument("--surface-pressure", type=float, required=True)
    ap.add_argument("--depth-corr-ol-wd", type=float, default=5e3)
    ap.add_argument("--nominal-km", type=float, default=None, help="Runtime-adiabat 410 nominal (km); defaults to profile + depth correction")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    prof_eq, prof_peq, gamma = profile_equilibrium(args.profile, args.model_height, args.surface_pressure)
    nominal = args.nominal_km if args.nominal_km is not None else prof_eq + args.depth_corr_ol_wd / 1e3
    print(f"profile dG=0 at model {prof_eq:.1f} km, P_eq = {prof_peq / 1e9:.3f} GPa, gamma = {gamma:.3e} Pa/K; nominal {nominal:.1f} km")
    datum = load_depth_datum(str(DATUM))
    suite = args.suite_tag
    nominal_true = float(model_to_true_km(nominal, datum, suite))
    print(f"true depth: nominal {nominal_true:.1f} km (model {nominal:.1f} km)")

    fig, ax = plt.subplots(1, 4, figsize=(10, 5), sharey=True)
    fig.subplots_adjust(wspace=0.08)
    for run in args.runs:
        try:
            rep, ts = load_rep(run, args.suite_tag)
        except (OSError, KeyError) as e:
            print(f"skip {run}: {e}", file=sys.stderr)
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
        ax[1].plot(dg / 1e3, model_to_true_km(zd, datum, suite), **kw)
        ax[2].plot(rate, tr, **kw)
        pmod = np.interp(zx, zp, p)
        pad = np.interp(zx, za, pa) / 1e9
        ax[3].plot(pmod - pad, tx, **kw)
        rt = zero_cross(zd, dg)
        xihalf = float(np.interp(0.5, xi, zx)) if xi.min() < 0.5 < xi.max() else float("nan")
        rt0 = rt[0] if rt else float("nan")
        pmod0 = float(np.interp(rt0, zp, p)) if rt else float("nan")
        j = int(np.nanargmax(np.abs(rate))) if np.isfinite(rate).any() else -1
        print(
            f"{bench_label(run)}: dG=0 at {float(model_to_true_km(rt0, datum, suite)):.1f} km (P={pmod0:.3f} GPa vs prof {prof_peq / 1e9:.3f}), "
            f"xi0.5 at {float(model_to_true_km(xihalf, datum, suite)):.1f} km, max|rate| {rate[j]:.3g}/Ma at {float(model_to_true_km(zr[j], datum, suite)):.1f} km"
        )
    for a in ax:
        a.axhline(nominal_true, color="grey", lw=1.5, ls="--")
        a.invert_yaxis()
        a.set_ylim(float(model_to_true_km(500, datum, suite)), float(model_to_true_km(250, datum, suite)))
    for a in ax[1:]:
        a.tick_params(labelleft=False)
    ax[0].set_xlabel("$\\xi$ (dimensionless)")
    ax[0].set_xlim(-0.05, 1.05)
    ax[1].set_xlabel("$dG$ (kJ/mol)")
    ax[2].set_xlabel("$\\dot{X}$ (1/Ma)")
    ax[3].set_xlabel("$\\hat{P}$ (GPa)")
    ax[0].set_ylabel("Depth (km)")
    handles, labels = ax[0].get_legend_handles_labels()
    ax[0].legend(handles, labels, fontsize=10, loc="lower left", frameon=True, facecolor="white", framealpha=0.9)
    fig.tight_layout()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=300)
    plt.close(fig)
    print(f"wrote -> {args.out}")


if __name__ == "__main__":
    sys.exit(main())
