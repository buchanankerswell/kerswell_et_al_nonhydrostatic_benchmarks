"""Standardized depth-window color limits per suite and field set.

Reads the same steps for every run with solutions and takes the per-field
max over the union, so all depth-window figures for a suite share one
scale. Writes JSON {suite: {set: {field: [lo, hi]}}}.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/compute_window_clims.py --models <uid ...> \\
    --out simulation/results/depth-window-clims.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

from utils.logging import log_artifact, log_info, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"
WINDOW_HALF_M = 50e3


def main():
    from benchmarks.plot_depth_window import SETS, read_step, window_clim

    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--steps", nargs=4, default=["00000", "00002", "00006", "00012"])
    ap.add_argument("--nominal-box-m", type=float, default=379943.0, help="Box nominal [m] (project.mk NOMINAL_410_BOX)")
    ap.add_argument("--nominal-sink-m", type=float, default=379957.0, help="Sink nominal [m] (project.mk NOMINAL_410_SINK400)")
    ap.add_argument("--block-top-m", type=float, default=875e3, help="Block top [m] (project.mk BLOCK_Y_TOP)")
    ap.add_argument("--block-bottom-m", type=float, default=725e3, help="Block bottom [m] (project.mk BLOCK_Y_BOT)")
    ap.add_argument("--gravity", type=float, default=9.81, help="Gravity [m/s^2] (project.mk GRAVITY)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    nominal_m = {"box": args.nominal_box_m, "sink": args.nominal_sink_m}

    half = WINDOW_HALF_M
    grouped = {"box": [], "sink": []}
    for model in args.models:
        suite = "sink" if model.startswith("NH_Sink_") else "box"
        if not all((RESULTS / model / "solution" / f"solution-{s}.pvtu").exists() for s in args.steps):
            log_warn(f"skip {model}: solutions missing")
            continue
        yc = 1e6 - nominal_m[suite]
        grouped[suite].append([read_step(model, s, args.block_top_m, args.block_bottom_m, args.gravity) for s in args.steps])

    out = {}
    for suite, runs in grouped.items():
        if not runs:
            continue
        yc = 1e6 - nominal_m[suite]
        steps_all = [d for run in runs for d in run]
        out[suite] = {}
        for setname, fields in SETS.items():
            out[suite][setname] = {}
            for field, _cmap, scale, _label, mode in fields:
                lo, hi = window_clim(steps_all, field, scale, mode, yc, half)
                out[suite][setname][field] = [round(float(lo), 3), round(float(hi), 3)]
        log_info(f"{suite}: " + ", ".join(f"{f}={out[suite]['set0'][f]}" for f, *_ in SETS["set0"]))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    log_artifact(out_path)


if __name__ == "__main__":
    sys.exit(main())
