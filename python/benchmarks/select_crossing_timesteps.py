"""Select visualization timesteps where advecting material crosses the 410.

For sinking-block runs (mobile `block` field): outputs whose block-centroid
depth lies within the transition window (410 km +/- block half-height +
margin). For box / static runs: early adjustment outputs plus the peak-wave
output. Always adds the peak peak-to-peak dynamic-pressure output from the
run's timeseries.csv.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/select_crossing_timesteps.py [--runs R ...] [--margin KM]

Prints JSON {run: [solution_numbers]} to stdout.
"""

import argparse
import csv
import glob
import json
import sys
from pathlib import Path

import numpy as np

RESULTS = Path("simulation/results")
TRANSITION_DEPTH_KM = 410.0


def load_timeseries(run):
  path = RESULTS / run / "timeseries.csv"
  rows = []
  with open(path) as f:
    for r in csv.DictReader(f):
      try:
        out = r["output"]
        tstep = int(out.split("-")[-1])
      except (ValueError, IndexError):
        continue
      rows.append({
        "tstep": tstep,
        "pmax": float(r["nonadiabatic_pressure_max"]),
        "pmin": float(r["nonadiabatic_pressure_min"]),
      })
  return rows


def peak_tstep(rows):
  return max(rows, key=lambda r: r["pmax"] - r["pmin"])["tstep"]


def block_centroid_km(run, tstep):
  import pyvista as pv
  matches = sorted((RESULTS / run / "solution").glob(f"solution-{tstep:05d}.pvtu"))
  if not matches:
    return None
  mesh = pv.read(matches[0])
  if "block" not in mesh.array_names:
    return None
  b = np.asarray(mesh["block"]).ravel()
  sel = b > 0.5
  if sel.sum() == 0:
    return None
  y = np.asarray(mesh.points)[:, 1][sel].mean() / 1e3
  y_max = float(mesh.bounds[3]) / 1e3
  return y_max - y  # depth km


def select_run(run, margin_km):
  sol = sorted((RESULTS / run / "solution").glob("solution-*.pvtu"))
  if not sol:
    return []
  rows = load_timeseries(run)
  if not rows:
    return []
  have = {r["tstep"] for r in rows}
  peak = peak_tstep(rows)

  # Block-crossing timesteps (sink runs with mobile block).
  depths = {}
  for r in rows:
    d = block_centroid_km(run, r["tstep"])
    if d is not None:
      depths[r["tstep"]] = d
  mobile = len(set(round(d, 1) for d in depths.values())) > 1
  if mobile:
    half = 75.0  # block half-height km
    crossing = sorted(t for t, d in depths.items()
                      if abs(d - TRANSITION_DEPTH_KM) <= half + margin_km)
    # Anchor on the output nearest the transition if the window missed.
    if not crossing:
      crossing = [min(depths, key=lambda t: abs(depths[t] - TRANSITION_DEPTH_KM))]
    # Peak waves ride the crossing; keep peak only if outside it.
    sel = sorted(set(crossing) | ({peak} if peak not in crossing else set()))
    return sorted(t for t in sel if t in have)

  # Box / static runs: init adjustment plus peak waves.
  early = [t for t in (0, 1, 2) if t in have]
  return sorted(set(early) | {peak})


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--runs", nargs="*", default=None)
  ap.add_argument("--margin", type=float, default=25.0)
  args = ap.parse_args()

  if args.runs:
    runs = args.runs
  else:
    runs = sorted(p.name for p in RESULTS.iterdir()
                  if (p / "solution").is_dir()
                  and list((p / "solution").glob("solution-*.pvtu"))
                  and (p / "timeseries.csv").exists())
  out = {}
  for run in runs:
    sel = select_run(run, args.margin)
    if sel:
      out[run] = sel
    else:
      print(f"skip {run}: no solution/timeseries", file=sys.stderr)
  print(json.dumps(out, indent=1))


if __name__ == "__main__":
  sys.exit(main())
