"""Reaction history and characteristic timescales for the sink suite."""

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
from utils.artifacts import add_force_argument, outputs_exist
from utils.logging import log_artifact, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"
S_PER_YR = 3.156e7
YR_PER_MA = 1e6

UNDAMPED_BASELINE_RUN = "NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res6"
NO_FEEDBACK_REFERENCE_RUN = "NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6"
REPRESENTATIVE_RUNS = [
    UNDAMPED_BASELINE_RUN,
    NO_FEEDBACK_REFERENCE_RUN,
    "NH_Sink_DynpOn_DampRel3.156e11_Block400_Z4.44e-04_Res6",
    "NH_Sink_DynpOn_DampCap2e8_Block400_Z4.44e-04_Res6",
]
TAU_RE = re.compile(r"^Rel([\d.e+-]+)$")


def read_rows(path, want):
    if not path or not Path(path).exists():
        log_warn(f"skip {path} (missing)")
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


def min_solver_step_yr(run):
    """Smallest interval between solver steps in the stats history (yr)."""
    s = load_stats_series(run)
    if not s:
        return None
    dt = np.diff(s["time_ma"]) * YR_PER_MA
    dt = dt[np.isfinite(dt) & (dt > 0)]
    return float(dt.min()) if dt.size else None


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


def ordered_ladder(t_rxn, t_flow, t_pressure, t_peak_yr, t_min_step, cadence_yr, max_step_yr, end_yr, taus):
    """Ladder entries sorted by timescale, shortest first."""
    ladder = [
        (r"$\dot{X}^{-1}$ (phase transformation)", t_rxn),
        ("Flow relaxation", t_flow),
        (r"$\hat{P}$ relaxation", t_pressure),
        (r"Largest $\hat{P}$ oscillation", t_peak_yr),
        ("Output interval", cadence_yr),
        ("Solver minimum step", t_min_step),
        ("Solver maximum step", max_step_yr),
        ("Run length", end_yr),
    ]
    if taus:
        ladder.append((r"Relaxed $\tau$ window", min(taus)))
    ladder.sort(key=lambda item: item[1] if item[1] is not None and np.isfinite(item[1]) else float("inf"))
    return ladder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--structure", default=str(RESULTS / "structure-summary-sink.csv"), help="Structure summary CSV (reaction-rate history)")
    ap.add_argument("--postprocessed", default=str(RESULTS / "postprocessed.csv"), help="Final-state boundary table CSV")
    ap.add_argument("--summary", default=str(RESULTS / "pressure-history-summary.csv"), help="Pressure-history summary CSV")
    ap.add_argument("--out-dir", default="figs/benchmarks", help="Output figure directory")
    ap.add_argument("--representative", nargs="*", default=REPRESENTATIVE_RUNS, help="Run UIDs drawn in the reaction-rate panel")
    ap.add_argument("--cadence-ma", type=float, default=0.0, help="Output cadence in Ma; 0 derives it from --viz-out-yr")
    ap.add_argument("--viz-out-yr", type=float, default=2.5e5, help="Output cadence in yr (project.mk VIZ_OUT_SINK_SUITE)")
    ap.add_argument("--max-solver-tstep-yr", type=float, default=25e3, help="Solver cap in yr (project.mk MAX_SOLVER_TSTEP)")
    ap.add_argument("--end-time-yr", type=float, default=5e6, help="Run length in yr (project.mk END_SINK)")
    ap.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI)")
    add_force_argument(ap)
    args = ap.parse_args()

    out = Path(args.out_dir) / "timescales-sink.png"
    if outputs_exist(out, args.force):
        return

    apply_bench_style(args.dpi)
    cadence_ma = args.cadence_ma if args.cadence_ma > 0 else args.viz_out_yr / YR_PER_MA

    structure = read_rows(args.structure, ["model_id", "timestep", "max_reaction_rate_410"])
    post = read_rows(args.postprocessed, ["model_id", "rate410_per_Ma"])
    summary = read_rows(args.summary, ["run", "damp", "time_largest_Ma"])

    histories = reaction_histories(structure, cadence_ma)
    taus = tau_years(summary)
    rate = scalar(post, UNDAMPED_BASELINE_RUN, "rate410_per_Ma")
    t_rxn = (1.0 / rate) * YR_PER_MA if rate else None
    t_peak = scalar(summary, UNDAMPED_BASELINE_RUN, "time_largest_Ma")
    t_peak_yr = t_peak * YR_PER_MA if t_peak is not None else None
    t_flow = flow_efold_yr(UNDAMPED_BASELINE_RUN)
    t_pressure = pressure_efold_yr(UNDAMPED_BASELINE_RUN)
    t_min_step = min_solver_step_yr(UNDAMPED_BASELINE_RUN)

    ladder = ordered_ladder(t_rxn, t_flow, t_pressure, t_peak_yr, t_min_step, args.viz_out_yr, args.max_solver_tstep_yr, args.end_time_yr, taus)
    names = [name for name, _ in ladder]
    tau_index = next((i for i, (name, _) in enumerate(ladder) if r"\tau" in name), None)

    fig, (ax_ladder, ax_rate) = plt.subplots(2, 1, figsize=(BENCH_WIDE_W, 5.6), gridspec_kw={"height_ratios": [1.6, 1.0]})

    for run in args.representative:
        series = histories.get(run)
        if not series:
            log_warn(f"skip {run} (no reaction history)")
            continue
        ax_rate.plot(
            [p[0] for p in series],
            [p[1] for p in series],
            "o-",
            ms=3,
            lw=1.3,
            color=bench_color(run),
            label=bench_label(run),
        )
    ax_rate.set_xlabel("Time (Ma)")
    ax_rate.set_ylabel(r"$\dot{X}_{max}$ (1/Ma)")
    ax_rate.set_yscale("log")
    ax_rate.set_title("Phase transformation rate")

    for i, (_, value) in enumerate(ladder):
        if i == tau_index:
            continue
        if value is not None and np.isfinite(value):
            ax_ladder.plot([value], [i], "o", color="#333333", ms=7)
            ax_ladder.annotate(fmt_yr(value), (value, i), textcoords="offset points", xytext=(7, 0), fontsize="small", va="center")
        else:
            ax_ladder.annotate("n/a", (1.0, i), fontsize="small", va="center", color="#777777")
    if taus:
        ax_ladder.axvspan(min(taus), max(taus), color="#1B7837", alpha=0.12)
        for tau in taus:
            ax_ladder.plot([tau], [tau_index], "|", color="#1B7837", ms=12, mew=1.6)
        ax_ladder.annotate(
            f"{fmt_yr(min(taus))} - {fmt_yr(max(taus))}",
            (max(taus), tau_index),
            textcoords="offset points",
            xytext=(-8, 0),
            ha="right",
            fontsize="small",
            va="center",
        )

    ax_ladder.set_yticks(range(len(names)))
    ax_ladder.set_yticklabels(names)
    ax_ladder.set_ylim(len(names) - 0.5, -0.5)
    ax_ladder.set_xscale("log")
    ax_ladder.set_xlim(1, max(args.end_time_yr * 3, 1e7))
    ax_ladder.set_xlabel("Time (yr, log)")
    ax_ladder.set_title("Characteristic timescales")
    handles, labels = ax_rate.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.34, right=0.97, hspace=0.45, top=0.92, bottom=0.11)

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=args.dpi)
    plt.close(fig)
    log_artifact(out)


if __name__ == "__main__":
    sys.exit(main())
