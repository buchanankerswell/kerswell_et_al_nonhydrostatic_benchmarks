"""Fixed color limits shared by the sink depth-window figures."""

import argparse
import json
import os
import sys
from pathlib import Path

from utils.artifacts import add_force_argument, outputs_exist
from utils.logging import log_artifact, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"
WINDOW_HALF_M = 50e03


def main():
    from benchmarks.plot_depth_window import SETS, read_step, window_clim

    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True, help="Run UIDs sharing one color scale")
    ap.add_argument("--steps", nargs=4, default=["00000", "00002", "00006", "00012"], help="Output numbers setting the shared scale")
    ap.add_argument("--nominal-sink-m", type=float, default=379957.0, help="Sink nominal (m) (project.mk NOMINAL_410_SINK400)")
    ap.add_argument("--block-top-m", type=float, default=875e03, help="Block top (m) (project.mk BLOCK_Y_TOP)")
    ap.add_argument("--block-bottom-m", type=float, default=725e03, help="Block bottom (m) (project.mk BLOCK_Y_BOT)")
    ap.add_argument("--gravity", type=float, default=9.81, help="Gravity (m/s^2) (project.mk GRAVITY)")
    ap.add_argument("--out", required=True, help="Output JSON path")
    add_force_argument(ap)
    args = ap.parse_args()

    if outputs_exist(args.out, args.force):
        return

    nominal_m = {"sink": args.nominal_sink_m}
    half = WINDOW_HALF_M
    grouped = {"sink": []}
    for model in args.models:
        if not all((RESULTS / model / "solution" / f"solution-{s}.pvtu").exists() for s in args.steps):
            log_warn(f"skip {model} (solutions missing)")
            continue
        grouped["sink"].append([read_step(model, s, args.block_top_m, args.block_bottom_m, args.gravity) for s in args.steps])

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

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    log_artifact(out_path)


if __name__ == "__main__":
    sys.exit(main())
