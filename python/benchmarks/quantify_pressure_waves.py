"""Quantify dynamic-pressure wave magnitude across NH benchmarks.

Reads per-run timeseries.csv and writes a summary CSV plus comparison plots.
Runs and plot sets arrive from the Makefiles (project.mk UID lists); without
them the script discovers NH_* runs and derives paper plot sets by UID suffix.
Each variant is measured against twins derived from its own UID: the undamped
control (Damp token -> DampNone) and the no-feedback equilibrium (Dynp1 ->
Dynp0). Positive reduction = damped; positive error = overshoot vs equilibrium.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/quantify_pressure_waves.py --runs <uid ...> \\
      --plot-box <uid ...> --plot-sink <uid ...> --plot-laptop <uid ...> \\
      --out-csv simulation/results/pressure-wave-summary.csv --fig-dir figs/benchmarks
"""

import argparse
import csv
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS = Path("simulation/results")

UID_DAMP_RE = re.compile(r"_Damp[A-Za-z]+[\d.e]*")


def short(run):
  """Compact label from a UID: damping + refinement + resolution tag."""
  m = re.search(r"_Damp([A-Za-z]+)([\d.e]*)", run)
  damp = (m.group(1) + m.group(2)) if m else run
  mref = re.search(r"_Res(\d+)", run)
  ref = f"r{mref.group(1)}" if mref else ""
  mend = re.search(r"_End([\d.e]+)", run)
  tag = {"1e6": "test", "2e6": "laptop"}.get(mend.group(1), "") if mend else ""
  return f"{damp} [{ref}{tag}]"


def control_twin(run):
  return UID_DAMP_RE.sub("_DampNone", run, count=1)


def nodynp_twin(run):
  return run.replace("_Dynp1_", "_Dynp0_", 1)


def discover(prefix):
  runs = []
  for p in sorted(RESULTS.iterdir()):
    if p.name.startswith(prefix) and (p / "timeseries.csv").exists():
      runs.append(p.name)
  return runs


def load_series(run):
  path = RESULTS / run / "timeseries.csv"
  if not path.exists():
    return None
  t, pmax, pmin, xir = [], [], [], []
  with open(path) as f:
    for r in csv.DictReader(f):
      t.append(float(r["time_yr"]) / 1e6)
      pmax.append(float(r["nonadiabatic_pressure_max"]) / 1e6)
      pmin.append(float(r["nonadiabatic_pressure_min"]) / 1e6)
      try:
        xir.append(float(r["xi_ol_wd_max"]) - float(r["xi_ol_wd_min"]))
      except (KeyError, ValueError):
        xir.append(float("nan"))
  return {"t": np.array(t), "pmax": np.array(pmax),
          "pmin": np.array(pmin), "xir": np.array(xir)}


def peak_of(run):
  s = load_series(run)
  if s is None or len(s["t"]) < 2:
    return None
  return float((s["pmax"] - s["pmin"]).max())


def summarize(run, peaks):
  s = load_series(run)
  if s is None or len(s["t"]) < 2:
    print(f"skip {run}: single output, no wave history", file=sys.stderr)
    return None
  p2p = s["pmax"] - s["pmin"]
  i = int(np.argmax(p2p))
  peak = float(p2p[i])
  ctrl, nod = control_twin(run), nodynp_twin(run)
  cp, np_ = peaks.get(ctrl), peaks.get(nod)
  return {
    "run": run,
    "control_run": ctrl,
    "n_outputs": len(s["t"]),
    "peak_p2p_MPa": round(peak, 1),
    "tstep_peak": int(i),
    "t_peak_Myr": round(float(s["t"][i]), 3),
    "final_p2p_MPa": round(float(p2p[-1]), 1),
    "initial_p2p_MPa": round(float(p2p[0]), 1),
    "max_xi_range": round(float(np.nanmax(s["xir"])), 3),
    "reduction_vs_control": (round((cp - peak) / cp, 3) if cp else None),
    "nodynp_run": nod,
    "rel_err_vs_nodynp": (round((peak - np_) / np_, 3) if np_ else None),
  }


def plot_suite(runs, title, out_path, control, reference=None):
  fig, ax = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
  for run in runs:
    s = load_series(run)
    if s is None:
      continue
    if run == control:
      kw = dict(lw=2.5)
    elif reference is not None and run == reference:
      kw = dict(lw=1.5, ls="--", color="grey")
    else:
      kw = dict(lw=1.2, alpha=0.85)
    ax[0].plot(s["t"], s["pmax"] - s["pmin"], label=short(run), **kw)
    ax[1].plot(s["t"], s["pmin"], label=short(run), **kw)
  ax[0].set_ylabel("peak-to-peak dyn. pressure [MPa]")
  ax[1].set_ylabel("min dyn. pressure [MPa]")
  ax[1].set_xlabel("time [Myr]")
  for a in ax:
    a.grid(True, alpha=0.3)
  ax[0].legend(fontsize=8, loc="best")
  fig.suptitle(title)
  fig.tight_layout()
  out_path.parent.mkdir(parents=True, exist_ok=True)
  fig.savefig(out_path, dpi=110)
  plt.close(fig)


def paper_set(runs, ref, end):
  return sorted(r for r in runs if f"_Res{ref}_" in r and r.endswith(f"_End{end}"))


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--runs", nargs="*", default=None,
                  help="UIDs to include in the CSV (default: discover NH_* runs)")
  ap.add_argument("--plot-box", nargs="*", default=None)
  ap.add_argument("--plot-sink", nargs="*", default=None)
  ap.add_argument("--plot-laptop", nargs="*", default=None)
  ap.add_argument("--out-csv", default="simulation/results/pressure-wave-summary.csv")
  ap.add_argument("--fig-dir", default="figs/benchmarks")
  args = ap.parse_args()

  box = [r for r in (args.runs or discover("NH_Box_")) if r.startswith("NH_Box_")]
  sink = [r for r in (args.runs or discover("NH_Sink_")) if r.startswith("NH_Sink_")]
  peaks = {}
  for r in box + sink:
    p = peak_of(r)
    if p is not None:
      peaks[r] = p

  rows = []
  for r in box:
    row = summarize(r, peaks)
    if row:
      rows.append({"suite": "box", **row})
  for r in sink:
    row = summarize(r, peaks)
    if row:
      rows.append({"suite": "sink", **row})

  if not rows:
    print("no NH_* runs with timeseries.csv found; nothing to quantify", file=sys.stderr)
    return

  out_csv = Path(args.out_csv)
  out_csv.parent.mkdir(parents=True, exist_ok=True)
  with open(out_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
  print(f"wrote {len(rows)} rows -> {out_csv}")

  figdir = Path(args.fig_dir)
  box_paper = args.plot_box if args.plot_box is not None else paper_set(box, 5, "1e7")
  sink_paper = args.plot_sink if args.plot_sink is not None else paper_set(sink, 6, "5e6")
  sink_laptop = args.plot_laptop if args.plot_laptop is not None else paper_set(sink, 5, "2e6")
  und = next((r for r in box_paper if "_Dynp1_DampNone_" in r), None)
  nod = next((r for r in box_paper if "_Dynp0_DampNone_" in r), None)
  plot_suite(box_paper, "Box 1-reaction: pressure-wave magnitude",
             figdir / "pressure_waves_box.png", und, reference=nod)
  und = next((r for r in sink_paper if "_Dynp1_DampNone_" in r), None)
  nod = next((r for r in sink_paper if "_Dynp0_DampNone_" in r), None)
  plot_suite(sink_paper, "Sink block (full-res): pressure-wave magnitude",
             figdir / "pressure_waves_sink.png", und, reference=nod)
  und = next((r for r in sink_laptop if "_Dynp1_DampNone_" in r), None)
  plot_suite(sink_laptop, "Sink block (laptop): pressure-wave magnitude",
             figdir / "pressure_waves_sink_laptop.png", und)
  print(f"plots -> {figdir}/")


if __name__ == "__main__":
  sys.exit(main())
