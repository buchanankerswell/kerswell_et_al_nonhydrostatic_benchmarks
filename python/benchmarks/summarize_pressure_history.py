"""Pressure history across the sink NH benchmark.

Reads per-run timeseries.csv and writes a summary CSV plus comparison plots.
Runs and plot lists come from the Makefiles; without them the script finds
NH_Sink_* runs. Each run is measured two ways: against paired runs from its
own UID (undamped control, no-feedback control), and against fixed suite-wide
references (S1 undamped, S2 no feedback). The fixed columns are defined for
every run, including mesh/CFL variants whose paired control never completed.
Positive reduction = damped; positive error = overshoot vs the reference.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/summarize_pressure_history.py --runs <uid ...> \\
      --plot-sink <uid ...> \\
      --out-csv simulation/results/pressure-history-summary.csv --fig-dir figs/benchmarks
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

from common import load_stats_series, load_vtu_series, parse_uid_columns
from simulation.mesh.config import BENCH_WIDE_W, UID_DAMP_RE, apply_bench_style, bench_color, bench_label
from utils.logging import log_artifact, log_info, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"


def undamped_control(run):
    return UID_DAMP_RE.sub("_DampNone", run, count=1)


def no_feedback_control(run):
    return run.replace("_DynpOn_", "_DynpOff_", 1)


def discover(prefix):
    runs = []
    for p in sorted(RESULTS.iterdir()):
        if p.name.startswith(prefix) and (p / "timeseries.csv").exists():
            runs.append(p.name)
    return runs


def largest_of(run):
    s = load_vtu_series(run)
    if s is None or len(s["t"]) < 2:
        return None
    return float((s["pmax"] - s["pmin"]).max())


def summarize(run, by_run, base, ref):
    s = load_vtu_series(run)
    if s is None or len(s["t"]) < 2:
        log_warn(f"skip {run}: single output, no history to compare")
        return None
    stats = load_stats_series(run)
    if stats is not None and np.isfinite(stats["flow"]).any():
        highest_flow = float(np.nanmax(stats["flow"]))
        final_flow = float(stats["flow"][np.isfinite(stats["flow"])][-1])
        diminishment = round((highest_flow - final_flow) / highest_flow, 3) if highest_flow > 0 else None
    else:
        highest_flow, final_flow, diminishment = None, None, None
    p2p = s["pmax"] - s["pmin"]
    i = int(np.argmax(p2p))
    largest = float(p2p[i])
    ctrl, nofb = undamped_control(run), no_feedback_control(run)
    cp, np_ = by_run.get(ctrl), by_run.get(nofb)
    return {
        "run": run,
        "control_run": ctrl,
        "n_outputs": len(s["t"]),
        "largest_range_MPa": round(largest, 1),
        "step_largest": int(i),
        "time_largest_Ma": round(float(s["t"][i]), 3),
        "final_range_MPa": round(float(p2p[-1]), 1),
        "initial_range_MPa": round(float(p2p[0]), 1),
        "max_xi_range": round(float(np.nanmax(s["xir"])), 3),
        "highest_flow_speed_m_yr": (round(highest_flow, 3) if highest_flow is not None else None),
        "final_flow_speed_m_yr": (round(final_flow, 3) if final_flow is not None else None),
        "flow_diminishment": diminishment,
        "reduction_vs_control": (round((cp - largest) / cp, 3) if cp else None),
        "nofeedback_run": nofb,
        "rel_err_vs_nofeedback": (round((largest - np_) / np_, 3) if np_ else None),
        "reduction_vs_baseline": (round((base - largest) / base, 3) if base else None),
        "rel_err_vs_reference": (round((largest - ref) / ref, 3) if ref else None),
        **parse_uid_columns(run),
    }


def plot_suite(runs, out_path, control, reference=None, dpi=100):
    runs = [r for r in runs if load_vtu_series(r) is not None]
    if not runs:
        log_warn(f"skip {out_path.name}: no timeseries.csv found")
        return
    fig, ax = plt.subplots(figsize=(BENCH_WIDE_W, 3.4))
    for run in runs:
        s = load_vtu_series(run)
        if s is None:
            continue
        if run == control:
            kw = dict(lw=2.5, color=bench_color(run))
        elif reference is not None and run == reference:
            kw = dict(lw=1.5, ls="--", color="grey")
        else:
            kw = dict(lw=1.2, alpha=0.85, color=bench_color(run))
        ax.plot(s["t"], s["pmax"] - s["pmin"], label=bench_label(run), **kw)
    ax.set_ylabel("$\\hat{P}$ Range (MPa)")
    ax.set_xlabel("Time (Ma)")
    fig.subplots_adjust(right=0.72)
    fig.legend(loc="center left", bbox_to_anchor=(0.73, 0.5), frameon=True, facecolor="white", framealpha=0.9)
    fig.tight_layout(rect=(0, 0, 0.72, 1))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)


def paper_set(runs, ref):
    """Main runs at one refinement level: UIDs ending in _Res<ref> with no CFL suffix."""
    return sorted(r for r in runs if f"_Res{ref}" in r and r.endswith(f"_Res{ref}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="*", default=None, help="UIDs to include in the CSV (default: discover NH_Sink_* runs)")
    ap.add_argument("--plot-sink", nargs="*", default=None, help="Sink run UIDs to plot")
    ap.add_argument("--out-csv", default="simulation/results/pressure-history-summary.csv", help="Output summary CSV path")
    ap.add_argument("--fig-dir", default="figs/benchmarks", help="Output figure directory")
    ap.add_argument("--baseline-run", default="NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res6", help="Fixed undamped baseline (S1)")
    ap.add_argument("--reference-run", default="NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6", help="Fixed no-feedback reference (S2)")
    ap.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI; draft 100, manuscript 330)")
    args = ap.parse_args()
    apply_bench_style(args.dpi)

    sink = [r for r in (args.runs or discover("NH_Sink_")) if r.startswith("NH_Sink_")]
    largest = {}
    for r in sink:
        p = largest_of(r)
        if p is not None:
            largest[r] = p
    base, ref = largest.get(args.baseline_run), largest.get(args.reference_run)
    if base is None or ref is None:
        log_warn("fixed baseline or reference run missing; fixed-reference columns will be blank")

    rows = []
    for r in sink:
        row = summarize(r, largest, base, ref)
        if row:
            rows.append({"suite": "sink", **row})

    if not rows:
        log_warn("no NH_Sink_* runs with timeseries.csv found; nothing to summarize")
        return

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    log_info(f"Summarized pressure history for {len(rows)} runs into {out_csv}")
    log_artifact(out_csv)

    figdir = Path(args.fig_dir)
    sink_paper = args.plot_sink if args.plot_sink is not None else paper_set(sink, 6)
    und = next((r for r in sink_paper if "_DynpOn_DampNone_" in r), None)
    nod = next((r for r in sink_paper if "_DynpOff_DampNone_" in r), None)
    plot_suite(sink_paper, figdir / "pressure-history-sink.png", und, reference=nod, dpi=args.dpi)
    log_artifact(figdir / "pressure-history-sink.png")


if __name__ == "__main__":
    sys.exit(main())
