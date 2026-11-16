"""Extract benchmark time series from ASPECT solution/*.pvtu files.

Maps visualization outputs to model time via the statistics file and
records per-output diagnostics sensitive to the dynamic-pressure feedback:
nonadiabatic pressure extrema, velocity RMS, and xi bounds.

Usage (run from repo root):
  conda run -n kerswell-et-al-mtz-kinetics python \
    python/benchmarks/extract_timeseries.py simulation/results/<run> -o out.csv
"""

import argparse
import csv
import os
import re
import sys

import numpy as np


def parse_statistics(path):
  """Return {viz_base: time_years} for rows that wrote visualization output."""
  mapping = {}
  with open(path) as f:
    for line in f:
      line = line.strip()
      if not line or line.startswith("#"):
        continue
      parts = line.split()
      time = float(parts[1])
      viz = parts[14].strip('"') if len(parts) > 14 else ""
      if viz:
        mapping[os.path.basename(viz)] = time
  return mapping


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("run_dir", help="simulation/results/<run> directory")
  ap.add_argument("-o", "--output", default=None)
  args = ap.parse_args()

  import pyvista as pv

  sol_dir = os.path.join(args.run_dir, "solution")
  mapping = parse_statistics(os.path.join(args.run_dir, "statistics"))

  pvtu = sorted(f for f in os.listdir(sol_dir) if f.endswith(".pvtu"))
  rows = []
  for f in pvtu:
    base = f[:-len(".pvtu")]
    mesh = pv.read(os.path.join(sol_dir, f))
    t = mapping.get(base, float("nan"))
    row = {"output": base, "time_yr": t}
    for name in ("nonadiabatic_pressure", "pressure"):
      if name in mesh.array_names:
        p = np.asarray(mesh[name]).ravel()
        row[f"{name}_min"] = float(np.min(p))
        row[f"{name}_max"] = float(np.max(p))
    if "velocity" in mesh.array_names:
      v = np.asarray(mesh["velocity"]).reshape(-1, 3)
      row["velocity_rms"] = float(np.sqrt(np.mean(np.sum(v ** 2, axis=1))))
    for name in ("xi_ol_wd", "density_field", "density"):
      if name in mesh.array_names:
        a = np.asarray(mesh[name]).ravel()
        row[f"{name}_min"] = float(np.min(a))
        row[f"{name}_max"] = float(np.max(a))
    rows.append(row)

  out = args.output or os.path.join(args.run_dir, "timeseries.csv")
  keys = sorted({k for r in rows for k in r if k != "output"})
  with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["output", "time_yr"] + keys)
    w.writeheader()
    for r in rows:
      w.writerow(r)
  print(f"Wrote {len(rows)} outputs -> {out}")


if __name__ == "__main__":
  sys.exit(main())
