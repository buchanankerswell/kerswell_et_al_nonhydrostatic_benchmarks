"""Pressure history across NH benchmarks.

Reads per-run timeseries.csv and writes a summary CSV plus comparison plots.
Runs and plot lists come from the Makefiles; without them the script finds
NH_* runs and picks main runs by UID suffix. Each run is measured against
paired runs from its own UID: the undamped control (Damp token -> DampNone)
and the no-feedback control (DynpOn -> DynpOff). Positive reduction = damped;
positive error = overshoot vs no feedback.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/summarize_pressure_history.py --runs <uid ...> \\
      --plot-box <uid ...> --plot-sink <uid ...> \\
      --out-csv simulation/results/pressure_history_summary.csv --fig-dir figs/benchmarks
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

from common import UID_DAMP_RE, apply_bench_style, load_point_series, load_stats_series, load_vtu_series, parse_uid_columns, uid_label

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"

apply_bench_style()


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


def summarize(run, by_run):
    s = load_vtu_series(run)
    if s is None or len(s["t"]) < 2:
        print(f"skip {run}: single output, no history to compare", file=sys.stderr)
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
        "time_largest_Myr": round(float(s["t"][i]), 3),
        "final_range_MPa": round(float(p2p[-1]), 1),
        "initial_range_MPa": round(float(p2p[0]), 1),
        "max_xi_range": round(float(np.nanmax(s["xir"])), 3),
        "highest_flow_speed_m_yr": (round(highest_flow, 3) if highest_flow is not None else None),
        "final_flow_speed_m_yr": (round(final_flow, 3) if final_flow is not None else None),
        "flow_diminishment": diminishment,
        "reduction_vs_control": (round((cp - largest) / cp, 3) if cp else None),
        "nofeedback_run": nofb,
        "rel_err_vs_nofeedback": (round((largest - np_) / np_, 3) if np_ else None),
        **parse_uid_columns(run),
    }


def plot_suite(runs, out_path, control, reference=None):
    runs = [r for r in runs if load_vtu_series(r) is not None]
    if not runs:
        print(f"skip {out_path.name}: no timeseries.csv found", file=sys.stderr)
        return
    fig, ax = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    for run in runs:
        s = load_vtu_series(run)
        if s is None:
            continue
        if run == control:
            kw = dict(lw=2.5)
        elif reference is not None and run == reference:
            kw = dict(lw=1.5, ls="--", color="grey")
        else:
            kw = dict(lw=1.2, alpha=0.85)
        ax[0].plot(s["t"], s["pmax"] - s["pmin"], label=uid_label(run), **kw)
        ax[1].plot(s["t"], s["pmin"], label=uid_label(run), **kw)
    ax[0].set_ylabel("Dynamic Pressure Range (MPa)")
    ax[1].set_ylabel("Lowest Dynamic Pressure (MPa)")
    ax[1].set_xlabel("Time (Myr)")
    ax[0].legend(fontsize=11, loc="upper right", frameon=False)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


def plot_mean_flow_suite(runs, out_path, control, reference=None):
    fig, ax = plt.subplots(figsize=(8, 5))
    plotted = 0
    for run in runs:
        stats = load_stats_series(run)
        if stats is None:
            continue
        plotted += 1
        if run == control:
            kw = dict(lw=2.5)
        elif reference is not None and run == reference:
            kw = dict(lw=1.5, ls="--", color="grey")
        else:
            kw = dict(lw=1.2, alpha=0.85)
        ax.plot(stats["time_myr"], stats["flow"], label=uid_label(run), **kw)
    if plotted == 0:
        print(f"skip {out_path.name}: no stats-timeseries.csv found", file=sys.stderr)
        plt.close(fig)
        return
    ax.set_yscale("log")
    ax.set_ylabel("Average Flow Speed (m/yr)")
    ax.set_xlabel("Time (Myr)")
    ax.legend(fontsize=11, loc="upper right", frameon=False)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


def plot_point_suite(runs, out_path, control, reference=None, field="pressure"):
    fig, ax = plt.subplots(figsize=(8, 5))
    plotted = 0
    for run in runs:
        point = load_point_series(run, 0, field)
        if point is None:
            continue
        # Absolute point pressure is dominated by the hydrostatic background
        # (~14 GPa); subtract the initial value so the variation is visible.
        values = point["values"] - point["values"][0]
        plotted += 1
        if run == control:
            kw = dict(lw=2.5)
        elif reference is not None and run == reference:
            kw = dict(lw=1.5, ls="--", color="grey")
        else:
            kw = dict(lw=1.2, alpha=0.85)
        ax.plot(point["time_myr"], values, label=uid_label(run), **kw)
    if plotted == 0:
        print(f"skip {out_path.name}: no point_values.txt found", file=sys.stderr)
        plt.close(fig)
        return
    ax.set_ylabel("Point Pressure Change (MPa)")
    ax.set_xlabel("Time (Myr)")
    ax.legend(fontsize=11, loc="upper right", frameon=False)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


def paper_set(runs, ref):
    return sorted(r for r in runs if f"_Res{ref}" in r and r.endswith(f"_Res{ref}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="*", default=None, help="UIDs to include in the CSV (default: discover NH_* runs)")
    ap.add_argument("--plot-box", nargs="*", default=None)
    ap.add_argument("--plot-sink", nargs="*", default=None)
    ap.add_argument("--out-csv", default="simulation/results/pressure_history_summary.csv")
    ap.add_argument("--fig-dir", default="figs/benchmarks")
    args = ap.parse_args()

    box = [r for r in (args.runs or discover("NH_Box_")) if r.startswith("NH_Box_")]
    sink = [r for r in (args.runs or discover("NH_Sink_")) if r.startswith("NH_Sink_")]
    largest = {}
    for r in box + sink:
        p = largest_of(r)
        if p is not None:
            largest[r] = p

    rows = []
    for r in box:
        row = summarize(r, largest)
        if row:
            rows.append({"suite": "box", **row})
    for r in sink:
        row = summarize(r, largest)
        if row:
            rows.append({"suite": "sink", **row})

    if not rows:
        print("no NH_* runs with timeseries.csv found; nothing to summarize", file=sys.stderr)
        return

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {out_csv}")

    figdir = Path(args.fig_dir)
    box_paper = args.plot_box if args.plot_box is not None else paper_set(box, 5)
    sink_paper = args.plot_sink if args.plot_sink is not None else paper_set(sink, 6)
    und = next((r for r in box_paper if "_DynpOn_DampNone_" in r), None)
    nod = next((r for r in box_paper if "_DynpOff_DampNone_" in r), None)
    plot_suite(box_paper, figdir / "pressure_history_box.png", und, reference=nod)
    und = next((r for r in sink_paper if "_DynpOn_DampNone_" in r), None)
    nod = next((r for r in sink_paper if "_DynpOff_DampNone_" in r), None)
    plot_suite(sink_paper, figdir / "pressure_history_sink.png", und, reference=nod)
    for runs, tag in ((box_paper, "box"), (sink_paper, "sink")):
        und = next((r for r in runs if "_DynpOn_DampNone_" in r), None)
        nod = next((r for r in runs if "_DynpOff_DampNone_" in r), None)
        plot_mean_flow_suite(runs, figdir / f"mean_flow_speed_{tag}.png", und, reference=nod)
        plot_point_suite(runs, figdir / f"point_pressure_{tag}.png", und, reference=nod)
    print(f"plots -> {figdir}/")


if __name__ == "__main__":
    sys.exit(main())
