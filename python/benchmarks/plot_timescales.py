"""Phase-change and relaxation timescales for the sink benchmark suite.

Two panels:

  left   reaction-rate history for representative runs. The inverse of the
         settled rate is the phase-change timescale.
  right  a log-time ladder placing the measured timescales (reaction, flow and
         dynamic-pressure relaxation, oscillation peak, output cadence, solver
         cap, run length) beside the relaxed-pressure tau window.

Reads only CSV products of `make postprocess`; no VTU files are opened.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/plot_timescales.py \\
    --structure simulation/results/structure-summary-sink.csv \\
    --postprocessed simulation/results/postprocessed.csv \\
    --summary simulation/results/pressure-history-summary.csv \\
    --out-dir figs/benchmarks --dpi 100
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from benchmarks.common import load_stats_series, load_vtu_series
from simulation.mesh.config import BENCH_WIDE_W, apply_bench_style, bench_color, bench_label
from utils.logging import log_artifact, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"
S_PER_YR = 3.156e7
YR_PER_MA = 1e6

S1 = "NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res6"
S2 = "NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6"
REPRESENTATIVE = [
    S1,
    S2,
    "NH_Sink_DynpOn_DampRel3.156e11_Block400_Z4.44e-04_Res6",
    "NH_Sink_DynpOn_DampCap2e8_Block400_Z4.44e-04_Res6",
]
TAU_RE = re.compile(r"^Rel([\d.e+-]+)$")


def read_rows(path, want):
    if not path or not Path(path).exists():
        log_warn("skip: missing " + str(path))
        return []
    with open(path) as f:
        return [r for r in csv.DictReader(f) if all(k in r for k in want)]


def reaction_histories(rows, cadence_ma):
    """(time Ma, rate 1/Ma) per run; drop the step-0 init spike."""
    out = {}
    for r in rows:
        try:
            step = int(r["timestep"])
            rate = float(r["max_reaction_rate_410"])
        except (KeyError, ValueError):
            continue
        if step == 0 or not np.isfinite(rate) or rate <= 0:
            continue
        out.setdefault(r["model_id"], []).append((step * cadence_ma, rate))
    for series in out.values():
        series.sort()
    return out


def efold_yr(t_ma, values):
    """First time (yr) at which values fall to 1/e of the peak, after the peak."""
    t = np.asarray(t_ma, dtype=float)
    v = np.asarray(values, dtype=float)
    ok = np.isfinite(t) & np.isfinite(v) & (v > 0)
    if ok.sum() < 2:
        return None
    t, v = t[ok], v[ok]
    ip = int(np.argmax(v))
    below = np.where(v[ip + 1 :] <= v[ip] / np.e)[0]
    if below.size == 0:
        return None
    return float(t[ip + 1 + int(below[0])] * YR_PER_MA)


def flow_efold_yr(run):
    s = load_stats_series(run)
    return efold_yr(s["time_ma"], s["flow"]) if s else None


def pressure_efold_yr(run):
    s = load_vtu_series(run)
    if not s:
        return None
    return efold_yr(s["t"], s["pmax"] - s["pmin"])


def scalar(rows, run, key):
    for r in rows:
        if r.get("run") == run or r.get("model_id") == run:
            try:
                return float(r[key])
            except (KeyError, ValueError):
                return None
    return None


def tau_years(summary_rows):
    out = []
    for r in summary_rows:
        m = TAU_RE.match(r.get("damp", ""))
        if m:
            try:
                out.append(float(m.group(1)) / S_PER_YR)
            except ValueError:
                continue
    return sorted(set(out))


def fmt_yr(v):
    if v >= 1e6:
        return f"{v / 1e6:.2f} Ma"
    if v >= 1e3:
        return f"{v / 1e3:.0f} kyr"
    return f"{v:.0f} yr"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--structure", default=str(RESULTS / "structure-summary-sink.csv"), help="Structure summary CSV (reaction-rate history)")
    ap.add_argument("--postprocessed", default=str(RESULTS / "postprocessed.csv"), help="Final-state boundary table CSV")
    ap.add_argument("--summary", default=str(RESULTS / "pressure-history-summary.csv"), help="Pressure-history summary CSV")
    ap.add_argument("--out-dir", default="figs/benchmarks", help="Output figure directory")
    ap.add_argument("--representative", nargs="*", default=REPRESENTATIVE, help="Run UIDs drawn in the reaction-rate panel")
    ap.add_argument("--cadence-ma", type=float, default=0.0, help="Output cadence in Ma; 0 derives it from --viz-out-yr")
    ap.add_argument("--viz-out-yr", type=float, default=2.5e5, help="Output cadence in yr (project.mk VIZ_OUT_SINK_SUITE)")
    ap.add_argument("--max-solver-tstep-yr", type=float, default=25e3, help="Solver cap in yr (project.mk MAX_SOLVER_TSTEP)")
    ap.add_argument("--end-time-yr", type=float, default=5e6, help="Run length in yr (project.mk END_SINK)")
    ap.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI)")
    args = ap.parse_args()
    apply_bench_style(args.dpi)
    cadence_ma = args.cadence_ma if args.cadence_ma > 0 else args.viz_out_yr / YR_PER_MA

    structure = read_rows(args.structure, ["model_id", "timestep", "max_reaction_rate_410"])
    post = read_rows(args.postprocessed, ["model_id", "rate410_per_Ma"])
    summary = read_rows(args.summary, ["run", "damp", "time_largest_Ma"])

    histories = reaction_histories(structure, cadence_ma)
    taus = tau_years(summary)
    rate = scalar(post, S1, "rate410_per_Ma")
    t_rxn = (1.0 / rate) * YR_PER_MA if rate else None
    t_peak = scalar(summary, S1, "time_largest_Ma")
    t_peak_yr = t_peak * YR_PER_MA if t_peak is not None else None
    t_flow, t_pressure = flow_efold_yr(S1), pressure_efold_yr(S1)

    ladder = [
        ("Phase change 1/Xdot", t_rxn),
        ("Flow relaxation 1/e", t_flow),
        ("P-hat relaxation 1/e", t_pressure),
        ("Oscillation peak (S1)", t_peak_yr),
        ("Output cadence", args.viz_out_yr),
        ("Solver max step", args.max_solver_tstep_yr),
        ("Run length", args.end_time_yr),
    ]
    names = [n for n, _ in ladder] + ["Relaxed tau window"]
    tau_row = len(names) - 1

    fig, (axr, axl) = plt.subplots(1, 2, figsize=(BENCH_WIDE_W * 1.7, 4.0), gridspec_kw={"width_ratios": [1.0, 1.35]})

    for run in args.representative:
        series = histories.get(run)
        if not series:
            log_warn("skip reaction curve: " + run)
            continue
        axr.plot(
            [p[0] for p in series],
            [p[1] for p in series],
            "o-",
            ms=3,
            lw=1.3,
            color=bench_color(run),
            label=bench_label(run),
        )
    axr.set_xlabel("Time (Ma)")
    axr.set_ylabel("$\\dot{X}_{max}$ (1/Ma)")
    axr.set_yscale("log")
    axr.set_title("Phase-change rate")
    axr.legend(fontsize=8, frameon=False)

    for i, (_, val) in enumerate(ladder):
        if val is not None and np.isfinite(val):
            axl.plot([val], [i], "o", color="#333333", ms=7)
            axl.annotate(fmt_yr(val), (val, i), textcoords="offset points", xytext=(7, 0), fontsize=9, va="center")
        else:
            axl.annotate("n/a", (1.0, i), fontsize=9, va="center", color="#777777")
    if taus:
        axl.axvspan(min(taus), max(taus), color="#1B7837", alpha=0.12)
        for tau in taus:
            axl.plot([tau], [tau_row], "|", color="#1B7837", ms=12, mew=1.6)
        axl.annotate(
            f"{fmt_yr(min(taus))} - {fmt_yr(max(taus))}",
            (max(taus), tau_row),
            textcoords="offset points",
            xytext=(7, 0),
            fontsize=9,
            va="center",
        )
    else:
        axl.annotate("no relaxed runs", (1.0, tau_row), fontsize=9, va="center", color="#777777")

    axl.set_yticks(range(len(names)))
    axl.set_yticklabels(names, fontsize=9)
    axl.set_ylim(len(names) - 0.5, -0.5)
    axl.set_xscale("log")
    axl.set_xlim(1, max(args.end_time_yr * 3, 1e7))
    axl.set_xlabel("Time (yr, log)")
    axl.set_title("Timescale ladder")
    fig.subplots_adjust(left=0.21, right=0.97, wspace=0.45, top=0.88, bottom=0.13)

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "timescales-sink.png"
    fig.savefig(out, dpi=args.dpi)
    plt.close(fig)
    log_artifact(out)


if __name__ == "__main__":
    sys.exit(main())
