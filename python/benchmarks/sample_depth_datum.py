"""Sample the canonical model-depth to true-depth datum table.

True depth maps model pressure through the BurnMan isentrope TSV, so the
phase transition lands near 410 km instead of at model-domain depth. The
sink adiabat carries the initial block load, which is subtracted first so
both suites share one ambient reference. Sampled once from finished runs;
figures read the versioned table (no solutions needed).

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/benchmarks/sample_depth_datum.py --profile simulation/data/olivine-wadsleyite-profile-Mg100.tsv \\
    --box-run simulation/results/NH_Box_DynpOn_DampNone_Z4.44e-04_Res5 \\
    --sink-run simulation/results/NH_Sink_DynpOn_DampCap2e8_Block400_Z4.44e-04_Res6 \\
    --out simulation/data/depth-datum.tsv
"""

import argparse
from pathlib import Path

import numpy as np
import pyvista as pv

from simulation.params.transitions import read_dG_profile

# Defaults mirror project.mk (BLOCK_Y_TOP/BLOCK_Y_BOT, GRAVITY); override
# with CLI flags to sample under different constants.


def level_adiabat(run_dir):
    """Mean adiabatic pressure per height level (the reference is 1D)."""
    mesh = pv.read(str(Path(run_dir) / "solution" / "solution-00000.pvtu"))
    pts = np.asarray(mesh.points)
    press = np.asarray(mesh["adiabatic_pressure"])
    levels = np.unique(np.round(pts[:, 1], 0))
    ym = np.array([pts[np.round(pts[:, 1], 0) == lv, 1].mean() for lv in levels])
    pm = np.array([press[np.round(pts[:, 1], 0) == lv].mean() for lv in levels])
    order = np.argsort(ym)
    return ym[order], pm[order]


def block_overlap(y, excess, top_m, bot_m):
    if not excess:
        return np.zeros_like(y)
    return np.where(
        y < bot_m,
        top_m - bot_m,
        np.where(y < top_m, y - bot_m, 0.0),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--box-run", required=True)
    ap.add_argument("--sink-run", required=True)
    ap.add_argument("--sink-excess", type=float, default=400.0)
    ap.add_argument("--block-top-m", type=float, default=875e3, help="Block top [m] (project.mk BLOCK_Y_TOP)")
    ap.add_argument("--block-bottom-m", type=float, default=725e3, help="Block bottom [m] (project.mk BLOCK_Y_BOT)")
    ap.add_argument("--gravity", type=float, default=9.81, help="Gravity [m/s^2] (project.mk GRAVITY)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    headers, data = read_dG_profile(args.profile)
    col = {h: i for i, h in enumerate(headers)}
    order = np.argsort(data[:, col["pressure"]])
    prof_p = data[order][:, col["pressure"]]
    prof_z = data[order][:, col["depth"]]

    grid_m = np.arange(0, 1_000_001, 1000)
    cols = {"model_depth_m": grid_m}
    for suite, run, excess in (("box", args.box_run, 0.0), ("sink", args.sink_run, args.sink_excess)):
        y, p = level_adiabat(run)
        p_amb = p - excess * args.gravity * block_overlap(y, excess, args.block_top_m, args.block_bottom_m)
        # Depth-ascending order; binning noise at the block interface can
        # break strict monotonicity by pascals against a GPa trend.
        depth = 1e6 - y[::-1]
        press = np.maximum.accumulate(p_amb[::-1])
        cols[suite] = np.interp(grid_m, depth, np.interp(press, prof_p, prof_z))
        assert np.all(np.diff(cols[suite]) >= 0), f"{suite} datum not monotonic"
        print(f"{suite}: top {cols[suite][0]:.0f} m, 373 km -> {np.interp(373100, grid_m, cols[suite]):.0f} m")

    out = Path(args.out)
    with open(out, "w") as f:
        f.write("# Canonical model-depth to true-depth datum (m). True depth maps ambient\n")
        f.write("# pressure through the BurnMan isentrope; sink excludes the block load.\n")
        f.write("# model_depth_m box_true_m sink_true_m\n")
        for i in range(len(grid_m)):
            f.write(f"{grid_m[i]:.0f}\t{cols['box'][i]:.1f}\t{cols['sink'][i]:.1f}\n")
    print(f"wrote -> {out}")


if __name__ == "__main__":
    raise SystemExit(main())
