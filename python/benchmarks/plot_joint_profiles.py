"""Joint depth profiles for one suite: xi, dG, rate, and pressure vs depth.

Reads the mesh representative cache (final timestep) and overlays the
profile nominal 410 against the runtime dG = 0 crossing, locating the
maximum reaction rate in depth. Prints the offset numbers that separate
the static nominal-vs-runtime frame shift from dynamic-pressure effects.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/plot_joint_profiles.py --runs <uid ...> \\
      --suite-tag box --profile simulation/data/olivine-wadsleyite-profile-Mg100.tsv \\
      --out figs/benchmarks/joint_profiles_box.png
"""

import argparse
import pickle
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import apply_bench_style, uid_label
from simulation.params.transitions import (
    find_surface_depth_offset,
    find_transition,
    read_dG_profile,
)

RESULTS = Path("simulation/results")

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
    ap.add_argument("--nominal-km", type=float, default=None, help="Runtime-adiabat 410 nominal [km]; defaults to profile + depth-corr")
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="")
    args = ap.parse_args()

    prof_eq, prof_peq, gamma = profile_equilibrium(args.profile, args.model_height, args.surface_pressure)
    nominal = args.nominal_km if args.nominal_km is not None else prof_eq + args.depth_corr_ol_wd / 1e3
    print(f"profile dG=0 at model {prof_eq:.1f} km, P_eq = {prof_peq / 1e9:.3f} GPa, gamma = {gamma:.3e} Pa/K; nominal {nominal:.1f} km")

    fig, ax = plt.subplots(1, 4, figsize=(14, 7), sharey=True)
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
        kw = dict(lw=1.2, alpha=0.85, label=uid_label(run))
        ax[0].plot(xi, zx, **kw)
        ax[1].plot(dg / 1e3, zd, **kw)
        ax[2].plot(rate, zr, **kw)
        pmod = np.interp(zx, zp, p)
        pad = np.interp(zx, za, pa) / 1e9
        ax[3].plot(pmod - pad, zx, **kw)
        rt = zero_cross(zd, dg)
        xihalf = float(np.interp(0.5, xi, zx)) if xi.min() < 0.5 < xi.max() else float("nan")
        rt0 = rt[0] if rt else float("nan")
        pmod0 = float(np.interp(rt0, zp, p)) if rt else float("nan")
        j = int(np.nanargmax(np.abs(rate))) if np.isfinite(rate).any() else -1
        print(
            f"{uid_label(run)}: dG=0 at {rt0:.1f} km (P={pmod0:.3f} GPa vs prof {prof_peq / 1e9:.3f}), "
            f"xi0.5 at {xihalf:.1f} km, max|rate| {rate[j]:.3g}/Ma at {zr[j]:.1f} km"
        )
    for a in ax:
        a.axhline(nominal, color="grey", lw=1.0, ls="--")
        a.invert_yaxis()
        a.set_ylim(500, 250)
    ax[0].set_xlabel("xi_ol_wd [-]")
    ax[0].set_xlim(-0.05, 1.05)
    ax[1].set_xlabel("dG [kJ/mol]")
    ax[2].set_xlabel("rate [1/Ma]")
    ax[3].set_xlabel("P - P_ad [GPa]")
    ax[0].set_ylabel("depth [km]")
    ax[0].legend(fontsize=11, loc="lower left", frameon=False)
    fig.suptitle(args.title or f"Joint 410 profiles ({args.suite_tag}, final output)")
    fig.tight_layout()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=300)
    plt.close(fig)
    print(f"wrote -> {args.out}")


if __name__ == "__main__":
    sys.exit(main())
