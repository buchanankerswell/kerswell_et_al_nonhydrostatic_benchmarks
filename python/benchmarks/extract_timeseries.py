"""Extract benchmark time series from ASPECT solution/*.pvtu files.

Maps visualization outputs to model time via the statistics file and
records per-output diagnostics sensitive to the dynamic-pressure feedback:
nonadiabatic pressure extrema, flow-speed magnitude, and xi bounds.

Usage (run from repo root):
  conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/extract_timeseries.py simulation/results/<run> -o out.csv
"""

import argparse
import csv
import os
import re
import sys

import numpy as np

from utils.logging import log_warn

# Ambient-reference block-load correction: the 1D adiabatic reference
# includes the initial block load, so add the static load back below
# the block column.


def parse_statistics(path):
    """Return {viz_base: time_years} for rows that wrote visualization output."""
    import re

    mapping = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            time = float(parts[1])
            viz = ""
            for tok in parts:
                tok = tok.strip('"')
                if re.search(r"/solution/solution-\d+$", tok):
                    viz = tok
                    break
            if viz:
                mapping[os.path.basename(viz)] = time
    return mapping


def write_stats_timeseries(stats_path, out_path):
    """Dump per-timestep velocity/temperature statistics to CSV.

    Column set is resolved from the statistics header, so runs with fewer
    postprocessors degrade to NaN columns instead of failing. Velocities are
    normalized to m/yr regardless of the run's output-year setting.
    """
    YR_S = 365.25 * 24 * 3600
    with open(stats_path) as f:
        header = [line for line in f if line.startswith("#")]
    columns = {}
    for line in header:
        m = re.match(r"#\s*(\d+):\s*(.*)", line.strip())
        if m:
            columns[m.group(2).strip()] = int(m.group(1)) - 1
    velocity_columns = [c for c in columns if re.match(r"(RMS|Max\.) velocity \(", c)]
    velocity_scale = 1.0
    if velocity_columns and "(m/s)" in velocity_columns[0]:
        velocity_scale = YR_S
    wanted_columns = {
        "mean_flow_speed_m_yr": None,
        "max_flow_speed_m_yr": None,
        "T_min_K": "Minimal temperature (K)",
        "T_avg_K": "Average temperature (K)",
        "T_max_K": "Maximal temperature (K)",
    }
    for c in velocity_columns:
        if c.startswith("RMS"):
            wanted_columns["mean_flow_speed_m_yr"] = c
        elif c.startswith("Max."):
            wanted_columns["max_flow_speed_m_yr"] = c
    rows = []
    with open(stats_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()

            def get_value(name, scale=1.0):
                i = columns.get(name)
                if i is None or i >= len(parts):
                    return float("nan")
                try:
                    return float(parts[i].strip('"')) * scale
                except ValueError:
                    return float("nan")

            row = {"timestep": parts[0], "time_yr": get_value("Time (years)")}
            for k, source_name in wanted_columns.items():
                row[k] = get_value(source_name, velocity_scale if source_name in velocity_columns else 1.0) if source_name else float("nan")
            rows.append(row)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestep", "time_yr"] + list(wanted_columns))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", help="simulation/results/<run> directory")
    ap.add_argument("-o", "--output", default=None, help="Output CSV path (default: <run_dir>/timeseries.csv)")
    ap.add_argument("--block-top-m", type=float, default=875e3, help="Block top [m] (project.mk BLOCK_Y_TOP)")
    ap.add_argument("--block-bottom-m", type=float, default=725e3, help="Block bottom [m] (project.mk BLOCK_Y_BOT)")
    ap.add_argument("--gravity", type=float, default=9.81, help="Gravity [m/s^2] (project.mk GRAVITY)")
    args = ap.parse_args()

    import pyvista as pv

    sol_dir = os.path.join(args.run_dir, "solution")
    if not os.path.isdir(sol_dir):
        log_warn(f"skip {args.run_dir}: no solution dir (run it or sync it first)")
        return
    stats_path = os.path.join(args.run_dir, "statistics")
    try:
        mapping = parse_statistics(stats_path)
    except OSError:
        log_warn(f"{args.run_dir}: no statistics file, times are NaN")
        mapping = {}
    try:
        write_stats_timeseries(stats_path, os.path.join(args.run_dir, "stats-timeseries.csv"))
    except OSError:
        log_warn(f"{args.run_dir}: no statistics file, skipping stats-timeseries.csv")

    pvtu = sorted(f for f in os.listdir(sol_dir) if f.endswith(".pvtu"))
    if not pvtu:
        log_warn(f"skip {args.run_dir}: no solution outputs to tabulate")
        return
    rows = []
    for f in pvtu:
        base = f[: -len(".pvtu")]
        mesh = pv.read(os.path.join(sol_dir, f))
        t = mapping.get(base, float("nan"))
        row = {"output": base, "time_yr": t}
        for name in ("nonadiabatic_pressure", "pressure"):
            if name in mesh.array_names:
                p = np.asarray(mesh[name]).ravel()
                row[f"{name}_min"] = float(np.min(p))
                row[f"{name}_max"] = float(np.max(p))
        if "nonadiabatic_pressure" in mesh.array_names:
            bm = re.search(r"Block(\d+)", args.run_dir)
            excess = float(bm.group(1)) if bm else 0.0
            if excess:
                nad = np.asarray(mesh["nonadiabatic_pressure"]).ravel()
                y = np.asarray(mesh.points)[:, 1]
                overlap = np.where(
                    y < args.block_bottom_m,
                    args.block_top_m - args.block_bottom_m,
                    np.where(y < args.block_top_m, args.block_top_m - y, 0.0),
                )
                amb = nad + excess * args.gravity * overlap
                row["ambient_pressure_min"] = float(np.min(amb))
                row["ambient_pressure_max"] = float(np.max(amb))
        if "velocity" in mesh.array_names:
            v = np.asarray(mesh["velocity"]).reshape(-1, 3)
            row["velocity_rms"] = float(np.sqrt(np.mean(np.sum(v**2, axis=1))))
        for name in ("xi_ol_wd", "density_field", "density"):
            if name in mesh.array_names:
                a = np.asarray(mesh[name]).ravel()
                row[f"{name}_min"] = float(np.min(a))
                row[f"{name}_max"] = float(np.max(a))
        rows.append(row)

    out = args.output or os.path.join(args.run_dir, "timeseries.csv")
    seen, keys = set(), []
    for r in rows:
        for k in r:
            if k not in ("output", "time_yr") and k not in seen:
                seen.add(k)
                keys.append(k)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["output", "time_yr"] + keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    sys.exit(main())
