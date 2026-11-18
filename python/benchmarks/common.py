"""Shared UID labels and run-data loaders for the benchmark figure scripts."""

import csv
import re
import sys
from pathlib import Path

import numpy as np

RESULTS = Path("simulation/results")

DAMP_RE = re.compile(r"_Damp([A-Za-z]+)([\d.e+-]*)")
UID_DAMP_RE = re.compile(r"_Damp[A-Za-z]+[\d.e+-]*")


def uid_label(run):
    """Compact label from a UID: damping + dynp state + res + Z tag."""
    m = DAMP_RE.search(run)
    damp = (m.group(1) + m.group(2)) if m else run
    mo = re.search(r"_Dynp(On|Off)_", run)
    dyn = f" {mo.group(1)}" if mo else ""
    mr = re.search(r"_Res(\d+)", run)
    res = f"r{mr.group(1)}" if mr else ""
    mz = re.search(r"_Z([\d.e+-]+)", run)
    z = f" Z{mz.group(1)}" if mz else ""
    return f"{damp}{dyn} [{res}{z}]".replace("[ ", "[")


def load_vtu_series(run):
    """Per-output vtu extrema from timeseries.csv: t (Myr), pmax/pmin (MPa), xir."""
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
    return {"t": np.array(t), "pmax": np.array(pmax), "pmin": np.array(pmin), "xir": np.array(xir)}


def load_stats_series(run):
    """Full-resolution velocity series from stats-timeseries.csv (m/yr, Myr)."""
    path = RESULTS / run / "stats-timeseries.csv"
    if not path.exists():
        return None
    times, rms_values, max_values = [], [], []
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                times.append(float(r["time_yr"]) / 1e6)
                rms_values.append(float(r["rms_velocity_m_yr"]))
                max_values.append(float(r["max_velocity_m_yr"]))
            except (KeyError, ValueError):
                continue
    if len(times) < 2:
        return None
    return {"time_myr": np.array(times), "rms": np.array(rms_values), "vmax": np.array(max_values)}


def load_probe_series(run, probe=0, field="relaxed_pressure"):
    """Probe-N field series from point_values.txt (MPa, Myr)."""
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
    if probe >= len(time_blocks[0]):
        print(f"skip {run}: probe {probe} missing", file=sys.stderr)
        return None
    field_index = column_names.index(field)
    times = np.array([b[0][0] for b in time_blocks]) / 1e6
    values = np.array([b[probe][field_index] for b in time_blocks]) / 1e6
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
