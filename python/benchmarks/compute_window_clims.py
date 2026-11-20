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

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"

NOMINAL_M = {"box": 373100.0, "sink": 362700.0}
WINDOW_HALF_KM = 50.0


def main():
    from benchmarks.plot_depth_window import SETS, read_step, window_clim

    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--steps", nargs=4, default=["00000", "00002", "00006", "00012"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    half = WINDOW_HALF_KM * 1e3
    grouped = {"box": [], "sink": []}
    for model in args.models:
        suite = "sink" if model.startswith("NH_Sink_") else "box"
        if not all((RESULTS / model / "solution" / f"solution-{s}.pvtu").exists() for s in args.steps):
            print(f"skip {model}: solutions missing", file=sys.stderr)
            continue
        yc = 1e6 - NOMINAL_M[suite]
        grouped[suite].append([read_step(model, s) for s in args.steps])
        print(f"read {model} ({suite}, yc={1e6 - yc:.0f} m)")

    out = {}
    for suite, runs in grouped.items():
        if not runs:
            continue
        yc = 1e6 - NOMINAL_M[suite]
        steps_all = [d for run in runs for d in run]
        out[suite] = {}
        for setname, fields in SETS.items():
            out[suite][setname] = {}
            for field, _cmap, scale, _label, mode in fields:
                lo, hi = window_clim(steps_all, field, scale, mode, yc, half)
                out[suite][setname][field] = [round(float(lo), 3), round(float(hi), 3)]
        print(f"{suite}: " + ", ".join(f"{f}={out[suite]['set0'][f]}" for f, *_ in SETS["set0"]))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote -> {out_path}")


if __name__ == "__main__":
    sys.exit(main())
