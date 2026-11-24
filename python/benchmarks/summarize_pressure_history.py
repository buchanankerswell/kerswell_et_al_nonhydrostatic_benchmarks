"""Summarize dynamic-pressure range history for the sink suite."""

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
from utils.artifacts import add_force_argument, outputs_exist
from utils.logging import log_artifact, log_warn

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


def summarize(run, by_run, baseline_peak, reference_peak):
    history = load_vtu_series(run)
    if history is None or len(history["t"]) < 2:
        log_warn(f"skip {run} (single output, no history)")
        return None
    stats = load_stats_series(run)
    if stats is not None and np.isfinite(stats["flow"]).any():
        highest_flow = float(np.nanmax(stats["flow"]))
        final_flow = float(stats["flow"][np.isfinite(stats["flow"])][-1])
        diminishment = round((highest_flow - final_flow) / highest_flow, 3) if highest_flow > 0 else None
    else:
        highest_flow, final_flow, diminishment = None, None, None
    pressure_range = history["pmax"] - history["pmin"]
    peak_index = int(np.argmax(pressure_range))
    largest = float(pressure_range[peak_index])
    control_run, no_feedback_run = undamped_control(run), no_feedback_control(run)
    control_peak, no_feedback_peak = by_run.get(control_run), by_run.get(no_feedback_run)
    return {
        "run": run,
        "control_run": control_run,
        "n_outputs": len(history["t"]),
        "largest_range_MPa": round(largest, 1),
        "step_largest": peak_index,
        "time_largest_Ma": round(float(history["t"][peak_index]), 3),
        "final_range_MPa": round(float(pressure_range[-1]), 1),
        "initial_range_MPa": round(float(pressure_range[0]), 1),
        "max_xi_range": round(float(np.nanmax(history["xir"])), 3),
        "highest_flow_speed_m_yr": (round(highest_flow, 3) if highest_flow is not None else None),
        "final_flow_speed_m_yr": (round(final_flow, 3) if final_flow is not None else None),
        "flow_diminishment": diminishment,
        "reduction_vs_control": (round((control_peak - largest) / control_peak, 3) if control_peak else None),
        "nofeedback_run": no_feedback_run,
        "rel_err_vs_nofeedback": (round((largest - no_feedback_peak) / no_feedback_peak, 3) if no_feedback_peak else None),
        "reduction_vs_baseline": (round((baseline_peak - largest) / baseline_peak, 3) if baseline_peak else None),
        "rel_err_vs_reference": (round((largest - reference_peak) / reference_peak, 3) if reference_peak else None),
        **parse_uid_columns(run),
    }


def plot_suite(runs, out_path, control, reference=None, dpi=100):
    runs = [r for r in runs if load_vtu_series(r) is not None]
    if not runs:
        log_warn(f"skip {out_path.name} (no timeseries.csv found)")
        return False
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
    return True


def paper_set(runs, ref):
    """Main runs at one refinement level: UIDs ending in _Res<ref> with no CFL suffix."""
    return sorted(r for r in runs if f"_Res{ref}" in r and r.endswith(f"_Res{ref}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="*", default=None, help="UIDs to include in the CSV (default: discover NH_Sink_* runs)")
    ap.add_argument("--plot-sink", nargs="*", default=None, help="Sink run UIDs to plot")
    ap.add_argument("--out-csv", default="simulation/results/pressure-history-summary.csv", help="Output summary CSV path")
    ap.add_argument("--fig-dir", default="figs/benchmarks", help="Output figure directory")
    ap.add_argument("--baseline-run", default="NH_Sink_DynpOn_DampNone_Block400_Z4.44e-04_Res6", help="Fixed undamped baseline UID")
    ap.add_argument("--reference-run", default="NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6", help="Fixed no-feedback reference UID")
    ap.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI; draft 100, manuscript 330)")
    add_force_argument(ap)
    args = ap.parse_args()

    out_csv = Path(args.out_csv)
    out_fig = Path(args.fig_dir) / "pressure-history-sink.png"
    if outputs_exist([out_csv, out_fig], args.force):
        return

    apply_bench_style(args.dpi)

    sink = [r for r in (args.runs or discover("NH_Sink_")) if r.startswith("NH_Sink_")]
    largest = {}
    for r in sink:
        p = largest_of(r)
        if p is not None:
            largest[r] = p
    baseline_peak, reference_peak = largest.get(args.baseline_run), largest.get(args.reference_run)
    if baseline_peak is None or reference_peak is None:
        log_warn("fixed baseline or reference run missing; fixed-reference columns will be blank")

    rows = []
    for r in sink:
        row = summarize(r, largest, baseline_peak, reference_peak)
        if row:
            rows.append({"suite": "sink", **row})

    if not rows:
        log_warn("no NH_Sink_* runs with timeseries.csv found; nothing to summarize")
        return

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    log_artifact(out_csv)

    sink_paper = args.plot_sink if args.plot_sink is not None else paper_set(sink, 6)
    undamped_run = next((r for r in sink_paper if "_DynpOn_DampNone_" in r), None)
    no_feedback_run = next((r for r in sink_paper if "_DynpOff_DampNone_" in r), None)
    if plot_suite(sink_paper, out_fig, undamped_run, reference=no_feedback_run, dpi=args.dpi):
        log_artifact(out_fig)


if __name__ == "__main__":
    sys.exit(main())
