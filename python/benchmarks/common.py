"""Shared run-data loaders for the benchmark figure scripts."""

import csv
import os
import re
import sys
from pathlib import Path

import numpy as np

from simulation.mesh.config import DAMP_RE

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"


def parse_uid_columns(run):
    """Split a UID into suite/damp/dynp/z/res/cfl columns for summary tables."""
    suite = "sink" if run.startswith("NH_Sink_") else "box" if run.startswith("NH_Box_") else ""
    damp_match = DAMP_RE.search(run)
    damp = (damp_match.group(1) + damp_match.group(2)) if damp_match else ""
    dynp_match = re.search(r"_Dynp(On|Off)_", run)
    dynp = 1 if dynp_match and dynp_match.group(1) == "On" else 0
    res_match = re.search(r"_Res(\d+)", run)
    res = int(res_match.group(1)) if res_match else None
    z_match = re.search(r"_Z([\d.e+-]+)", run)
    z = z_match.group(1) if z_match else ""
    cfl_match = re.search(r"_CFL([\d.]+)", run)
    cfl = float(cfl_match.group(1)) if cfl_match else None
    return {"suite": suite, "damp": damp, "dynp": dynp, "res": res, "z": z, "cfl": cfl}


def load_vtu_series(run):
    """Per-output vtu extrema from timeseries.csv: t (Myr), pmax/pmin (MPa), xir.

    Prefers ambient-referenced extrema when present (sinking-block runs
    under the ambient reference column), falling back to raw file values.
    """
    path = RESULTS / run / "timeseries.csv"
    if not path.exists():
        return None
    t, pmax, pmin, xir = [], [], [], []
    with open(path) as f:
        for r in csv.DictReader(f):
            t.append(float(r["time_yr"]) / 1e6)

            def pick(*names):
                for n in names:
                    try:
                        return float(r[n])
                    except (KeyError, ValueError):
                        continue
                return float("nan")

            pmax.append(pick("ambient_pressure_max", "nonadiabatic_pressure_max") / 1e6)
            pmin.append(pick("ambient_pressure_min", "nonadiabatic_pressure_min") / 1e6)
            try:
                xir.append(float(r["xi_ol_wd_max"]) - float(r["xi_ol_wd_min"]))
            except (KeyError, ValueError):
                xir.append(float("nan"))
    return {"t": np.array(t), "pmax": np.array(pmax), "pmin": np.array(pmin), "xir": np.array(xir)}


def load_stats_series(run):
    """Full-resolution flow-speed series from stats-timeseries.csv (m/yr, Myr)."""
    path = RESULTS / run / "stats-timeseries.csv"
    if not path.exists():
        return None
    times, mean_values, max_values = [], [], []
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                times.append(float(r["time_yr"]) / 1e6)
                mean_values.append(float(r["mean_flow_speed_m_yr"]))
                max_values.append(float(r["max_flow_speed_m_yr"]))
            except (KeyError, ValueError):
                continue
    if len(times) < 2:
        return None
    return {"time_myr": np.array(times), "flow": np.array(mean_values), "fastest": np.array(max_values)}


def load_point_series(run, point=0, field="pressure"):
    """Point-N field series from point_values.txt (MPa, Myr)."""
    path = RESULTS / run / "point_values.txt"
    if not path.exists():
        return None
    column_names, time_blocks, block_rows = None, [], []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if s.startswith("#"):
                column_names = [w.strip("<>") for w in s[1:].split()]
                continue
            if not s:
                if block_rows:
                    time_blocks.append(block_rows)
                    block_rows = []
                continue
            block_rows.append([float(x) for x in s.split()])
    if block_rows:
        time_blocks.append(block_rows)
    if not time_blocks or column_names is None or field not in column_names:
        return None
    if point >= len(time_blocks[0]):
        print(f"skip {run}: point {point} missing", file=sys.stderr)
        return None
    field_index = column_names.index(field)
    times = np.array([b[0][0] for b in time_blocks]) / 1e6
    values = np.array([b[point][field_index] for b in time_blocks]) / 1e6
    return {"time_myr": times, "values": values}


def load_depth_average(run):
    """Final depth-average temperature + xi profiles from depth_average.txt."""
    path = RESULTS / run / "depth_average.txt"
    if not path.exists():
        return None
    column_names, data_rows = None, []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                column_names = s[1:].split()
                continue
            data_rows.append([float(x) for x in s.split()])
    if not data_rows or column_names is None or len(column_names) < 3:
        return None
    data = np.array(data_rows)
    times = np.unique(data[:, 0])
    last = data[data[:, 0] == times[-1]]
    try:
        temperature_index = column_names.index("temperature")
    except ValueError:
        return None
    xi_index = next((i for i, n in enumerate(column_names) if n.startswith("xi_")), None)
    if xi_index is None:
        return None
    return {"depth_km": last[:, 1] / 1e3, "temperature": last[:, temperature_index], "xi": last[:, xi_index]}
