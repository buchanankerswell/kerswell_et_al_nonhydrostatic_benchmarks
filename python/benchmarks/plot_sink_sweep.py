"""Compare sink-block sweep runs: timeseries, front warp, halo profiles, fields.

Reads simulation/results/<run>/timeseries.csv + solution/*.pvtu files and
writes comparison figures to figs/sink_block/. Headless-safe (Agg).

Usage (repo root):
  conda run -n kerswell-et-al-mtz-kinetics python \\
    python/benchmarks/plot_sink_sweep.py [--out IDX] [run ...]

Defaults to the 7-variant laptop sweep + undamped ref-6 when no runs given.
--out selects which visualization output index to snapshot (default: last).
"""

import argparse
import csv
import glob
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS = "simulation/results"
FIGDIR = "figs/sink_block"

DEFAULT_RUNS = [
    "nh_sink_block_undamped_laptop",
    "nh_sink_block_implicit_bulk_laptop",
    "nh_sink_block_implicit_bulk_hi_laptop",
    "nh_sink_block_explicit_bulk_laptop",
    "nh_sink_block_relaxed_pressure_1kyr_laptop",
    "nh_sink_block_relaxed_pressure_10kyr_laptop",
    "nh_sink_block_capped_pressure_laptop",
    "nh_sink_block_undamped",
]

SHORT = {
    "undamped": "undamped",
    "implicit_bulk": "implicit ζ=1e19",
    "implicit_bulk_hi": "implicit ζ=1e20",
    "explicit_bulk": "explicit ζ=1e19",
    "relaxed_pressure_1kyr": "relaxed τ=1kyr",
    "relaxed_pressure_10kyr": "relaxed τ=10kyr",
    "capped_pressure": "capped 200MPa",
}


def short_name(run):
  stem = run.replace("nh_sink_block_", "")
  if stem.endswith("_laptop"):
    tag, stem = "ref5", stem[:-len("_laptop")]
  elif stem.endswith("_test"):
    tag, stem = "ref4", stem[:-len("_test")]
  else:
    tag = "ref6"
  return f"{SHORT.get(stem, stem)} [{tag}]"


def load_timeseries(run):
  path = os.path.join(RESULTS, run, "timeseries.csv")
  if not os.path.exists(path):
    return None
  with open(path) as f:
    rows = list(csv.DictReader(f))
  out = {}
  for key in rows[0]:
    try:
      out[key] = np.array([float(r[key]) for r in rows])
    except ValueError:
      pass
  return out


def plot_timeseries(runs):
  fig, ax = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
  for run in runs:
    ts = load_timeseries(run)
    if ts is None:
      print(f"  skip {run} (no timeseries.csv)")
      continue
    t = ts["time_yr"] / 1e6
    label = short_name(run)
    ax[0].plot(t, np.asarray(ts["nonadiabatic_pressure_max"]) / 1e6, label=label)
    ax[1].plot(t, np.asarray(ts["nonadiabatic_pressure_min"]) / 1e6, label=label)
    ax[2].plot(t, np.asarray(ts["xi_ol_wd_max"]) - np.asarray(ts["xi_ol_wd_min"]), label=label)
  ax[0].set_ylabel("max dyn. pressure [MPa]")
  ax[1].set_ylabel("min dyn. pressure [MPa]")
  ax[2].set_ylabel("xi range (max-min)")
  ax[2].set_xlabel("time [Myr]")
  for a in ax:
    a.grid(True, alpha=0.3)
  ax[0].legend(fontsize=8, loc="best")
  fig.suptitle("Sink-block sweep: pressure extrema and xi bounds")
  fig.tight_layout()
  return fig


def read_pvtu(run, idx, time_myr=None):
  import pyvista as pv

  files = sorted(glob.glob(os.path.join(RESULTS, run, "solution", "solution-*.pvtu")))
  if not files:
    return None, None
  if time_myr is not None:
    # Pick the output closest to the requested model time by probing TIME
    best, best_dt = len(files) - 1, None
    for i, f in enumerate(files):
      try:
        m = pv.read(f)
        t = float(np.asarray(m["TIME"]).ravel()[0]) / 1e6  # TIME is in years
        dt = abs(t - time_myr)
        if best_dt is None or dt < best_dt:
          best, best_dt = i, dt
      except Exception:
        continue
    idx = best
  else:
    idx = min(idx, len(files) - 1)
  mesh = pv.read(files[idx])
  pts = np.asarray(mesh.points)
  data = {name: np.asarray(mesh[name]).ravel() for name in mesh.array_names}
  return (mesh, pts, data), os.path.basename(files[idx])


def front_depth(pts, xi, x_bins=60):
  """Depth [km] of the xi=0.5 crossing per x-bin (NaN where absent)."""
  x = pts[:, 0] / 1e3
  y = pts[:, 1] / 1e3
  edges = np.linspace(x.min(), x.max(), x_bins + 1)
  xc = 0.5 * (edges[:-1] + edges[1:])
  depth = np.full(x_bins, np.nan)
  for i in range(x_bins):
    sel = (x >= edges[i]) & (x < edges[i + 1])
    if sel.sum() < 3:
      continue
    order = np.argsort(y[sel])
    ys, xs = y[sel][order], xi[sel][order]
    for k in range(len(ys) - 1):
      if (xs[k] - 0.5) * (xs[k + 1] - 0.5) <= 0 and xs[k] != xs[k + 1]:
        f = (0.5 - xs[k]) / (xs[k + 1] - xs[k])
        depth[i] = ys[k] + f * (ys[k + 1] - ys[k])
        break
  return xc, depth


def plot_fronts(runs, idx, time_myr):
  fig, ax = plt.subplots(2, 1, figsize=(8, 8), sharex=False)
  for run in runs:
    got = read_pvtu(run, idx, time_myr)
    if got[0] is None:
      print(f"  skip {run} (no solution files)")
      continue
    (mesh, pts, data), fname = got
    label = f"{short_name(run)}"
    xc, depth = front_depth(pts, data["xi_ol_wd"])
    ax[0].plot(xc, depth, label=label)
    # Halo centerline: sample the pressure field along x = 500 km
    # (interpolated sampling smooths DG jumps for a readable profile).
    line = mesh.sample_over_line((5e5, 0, 0), (5e5, 1e6, 0), resolution=400)
    lp = np.asarray(line.points)
    nap = np.asarray(line["nonadiabatic_pressure"]).ravel()
    ax[1].plot(nap / 1e6, lp[:, 1] / 1e3, label=label)
  ax[0].set_ylabel("xi=0.5 depth [km]")
  ax[0].set_title(f"Front warp ({fname})")
  ax[0].grid(True, alpha=0.3)
  ax[1].set_xlabel("dyn. pressure [MPa]")
  ax[1].set_ylabel("depth [km]")
  ax[1].set_title("Centerline pressure halo (x = 500 km)")
  ax[1].grid(True, alpha=0.3)
  ax[1].legend(fontsize=8, loc="best")
  fig.suptitle("Sink-block sweep: front position and pressure halo")
  fig.tight_layout()
  return fig


def plot_fields(run, idx):
  from matplotlib.tri import Triangulation

  got = read_pvtu(run, idx)
  if got[0] is None:
    return None
  (mesh, pts, data), fname = got
  x, y = pts[:, 0] / 1e3, pts[:, 1] / 1e3
  tri = Triangulation(x, y)
  xi_plot = np.clip(data["xi_ol_wd"], 0.0, 1.0)  # hide DG overshoot speckle
  fig, ax = plt.subplots(1, 2, figsize=(12, 5))
  cf = ax[0].tricontourf(tri, data["nonadiabatic_pressure"] / 1e6, levels=21, cmap="RdBu_r")
  ax[0].tricontour(tri, data["xi_ol_wd"], levels=[0.5], colors="k", linewidths=1.5)
  if "block" in data:
    ax[0].tricontour(tri, data["block"], levels=[0.5], colors="lime", linewidths=1.0,
                     linestyles="dashed")
  fig.colorbar(cf, ax=ax[0], label="dyn. pressure [MPa]")
  ax[0].set_title(f"{short_name(run)}: pressure + xi=0.5 (black) + block (green)")
  ax[0].set_aspect("equal")
  cf1 = ax[1].tricontourf(tri, xi_plot, levels=np.linspace(0, 1, 12), cmap="viridis")
  fig.colorbar(cf1, ax=ax[1], label="xi_ol_wd")
  ax[1].set_title("reaction progress")
  ax[1].set_aspect("equal")
  for a in ax:
    a.set_xlabel("x [km]")
    a.set_ylabel("y [km]")
  fig.suptitle(f"{run} [{fname}]")
  fig.tight_layout()
  return fig


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("runs", nargs="*", default=DEFAULT_RUNS)
  ap.add_argument("--out", type=int, default=-1,
                  help="visualization output index to snapshot (-1 = last)")
  ap.add_argument("--time", type=float, default=None,
                  help="model time in Myr to snapshot (closest output; overrides --out)")
  ap.add_argument("--fields", default="nh_sink_block_undamped_laptop,nh_sink_block_implicit_bulk_laptop",
                  help="comma-separated runs for 2D field figures")
  args = ap.parse_args()

  os.makedirs(FIGDIR, exist_ok=True)
  print("timeseries...")
  plot_timeseries(args.runs).savefig(os.path.join(FIGDIR, "timeseries.png"), dpi=110)
  print("fronts + halos...")
  plot_fronts(args.runs, args.out, args.time).savefig(os.path.join(FIGDIR, "fronts_halos.png"), dpi=110)
  for run in args.fields.split(","):
    run = run.strip()
    print(f"fields for {run}...")
    fig = plot_fields(run, args.out)
    if fig is not None:
      stem = run.replace("nh_sink_block_", "").removesuffix("_laptop")
      fig.savefig(os.path.join(FIGDIR, f"fields_{stem}.png"), dpi=110)
  print(f"wrote -> {FIGDIR}/")


if __name__ == "__main__":
  sys.exit(main())
