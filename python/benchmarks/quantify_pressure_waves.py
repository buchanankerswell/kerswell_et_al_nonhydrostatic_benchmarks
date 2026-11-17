"""Quantify dynamic-pressure wave magnitude across NH benchmarks.

Reads per-run timeseries.csv (peak-to-peak nonadiabatic pressure over time)
and writes a summary CSV plus comparison plots. No mesh reads; front
displacement/width at chosen timesteps come from the shared-pipeline
structure-summary CSVs.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/quantify_pressure_waves.py --out-csv simulation/data/pressure-wave-summary.csv \\
      --fig-dir figs/benchmarks

Control-relative reduction is measured against the suite undamped run's peak:
  reduction = (control_peak - variant_peak) / control_peak  (positive = damped)
"""

import argparse
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS = Path("simulation/results")

BOX_RUNS = [
    "nh_box_1rxn_undamped",
    "nh_box_1rxn_implicit_bulk",
    "nh_box_1rxn_explicit_bulk",
    "nh_box_1rxn_relaxed_pressure",
    "nh_box_1rxn_capped_pressure",
]
SINK_RUNS = [
    "nh_sink_block_undamped",
    "nh_sink_block_implicit_bulk",
    "nh_sink_block_explicit_bulk",
    "nh_sink_block_implicit_bulk_hi",
    "nh_sink_block_relaxed_pressure_1kyr",
    "nh_sink_block_relaxed_pressure_10kyr",
    "nh_sink_block_capped_pressure",
    "nh_sink_block_test",
    "nh_sink_block_test_noblock",
]
SINK_LAPTOP_RUNS = [
    "nh_sink_block_undamped_laptop",
    "nh_sink_block_implicit_bulk_laptop",
    "nh_sink_block_implicit_bulk_hi_laptop",
    "nh_sink_block_explicit_bulk_laptop",
    "nh_sink_block_relaxed_pressure_1kyr_laptop",
    "nh_sink_block_relaxed_pressure_10kyr_laptop",
    "nh_sink_block_capped_pressure_laptop",
]


def short(run):
  return (run.removeprefix("nh_box_1rxn_")
             .removeprefix("nh_sink_block_")
             .removesuffix("_laptop"))


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


def summarize(run, control_peak, control_run):
  s = load_series(run)
  if s is None:
    return None
  p2p = s["pmax"] - s["pmin"]
  i = int(np.argmax(p2p))
  peak = float(p2p[i])
  return {
    "run": run,
    "control_run": control_run,
    "n_outputs": len(s["t"]),
    "peak_p2p_MPa": round(peak, 1),
    "tstep_peak": int(i),
    "t_peak_Myr": round(float(s["t"][i]), 3),
    "final_p2p_MPa": round(float(p2p[-1]), 1),
    "initial_p2p_MPa": round(float(p2p[0]), 1),
    "max_xi_range": round(float(np.nanmax(s["xir"])), 3),
    "reduction_vs_control": (round((control_peak - peak) / control_peak, 3)
                              if control_peak else 0.0),
  }


def plot_suite(runs, title, out_path, control):
  fig, ax = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
  for run in runs:
    s = load_series(run)
    if s is None:
      continue
    kw = dict(lw=2.5) if run == control else dict(lw=1.2, alpha=0.85)
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


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--out-csv", default="simulation/data/pressure-wave-summary.csv")
  ap.add_argument("--fig-dir", default="figs/benchmarks")
  args = ap.parse_args()

  box = [r for r in BOX_RUNS if (RESULTS / r / "timeseries.csv").exists()]
  sink = [r for r in SINK_RUNS + SINK_LAPTOP_RUNS
          if (RESULTS / r / "timeseries.csv").exists()]

  rows = []
  box_control = "nh_box_1rxn_undamped"
  box_series = {r: load_series(r) for r in box}
  control_box_peak = float((box_series[box_control]["pmax"]
                            - box_series[box_control]["pmin"]).max())
  for r in box:
    s = box_series[r]
    if len(s["t"]) < 2:
      print(f"skip {r}: single output, no wave history", file=sys.stderr)
      continue
    rows.append({"suite": "box", **summarize(r, control_box_peak, box_control)})
  sink_full_control = "nh_sink_block_undamped"
  sink_laptop_control = "nh_sink_block_undamped_laptop"
  peaks = {}
  for c in (sink_full_control, sink_laptop_control):
    cs = load_series(c)
    peaks[c] = float((cs["pmax"] - cs["pmin"]).max()) if cs else 0.0
  for r in sink:
    if load_series(r) is not None and len(load_series(r)["t"]) < 2:
      print(f"skip {r}: single output, no wave history", file=sys.stderr)
      continue
    ctrl = (sink_laptop_control if r.endswith("_laptop") else sink_full_control)
    rows.append({"suite": "sink", **summarize(r, peaks[ctrl], ctrl)})

  out_csv = Path(args.out_csv)
  out_csv.parent.mkdir(parents=True, exist_ok=True)
  with open(out_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
  print(f"wrote {len(rows)} rows -> {out_csv}")

  figdir = Path(args.fig_dir)
  plot_suite(box, "Box 1-reaction: pressure-wave magnitude", figdir / "pressure_waves_box.png",
             BOX_RUNS[0])
  plot_suite([r for r in sink if not r.endswith("_laptop") and r != "nh_sink_block_test_noblock"],
             "Sink block (full-res): pressure-wave magnitude",
             figdir / "pressure_waves_sink.png", sink_full_control)
  plot_suite([r for r in sink if r.endswith("_laptop")],
             "Sink block (laptop): pressure-wave magnitude",
             figdir / "pressure_waves_sink_laptop.png", sink_laptop_control)
  print(f"plots -> {figdir}/")


if __name__ == "__main__":
  sys.exit(main())
