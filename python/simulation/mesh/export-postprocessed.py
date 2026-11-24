"""Export the final-state sink table: 410 displacement split into thermal and kinetic parts."""

import argparse
import pickle
import re
from pathlib import Path

import numpy as np
import pandas as pd

from simulation.params.transitions import (
    find_surface_depth_offset,
    find_transition,
    nominal_410_for_uid,
    read_dG_profile,
)
from utils.logging import log_artifact, log_warn

RHO_DEFAULT = 4100.0  # kg/m^3, mirrors project.mk REF_DENSITY

UID_RE = re.compile(
    r"^NH_(?P<suite>Sink)_Dynp(?P<dynp>On|Off)_Damp(?P<dampkind>[A-Za-z]+)(?P<dampval>[\d.e]*)"
    r"(?:_Block(?P<block>\d+))?_Z(?P<z>[\d.e+-]+)_Res(?P<res>\d+)$"
)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Export sink postprocessed table.")
    parser.add_argument("--data-dir", required=True, help="Flattened simulation/results dir")
    parser.add_argument("--out-csv", required=True, help="Output CSV path")
    parser.add_argument("--profile-ol-wd", required=True, help="Olivine-wadsleyite thermodynamic profile TSV path")
    parser.add_argument("--model-height", type=float, required=True, help="Model height (m)")
    parser.add_argument("--surface-pressure", type=float, required=True, help="Surface pressure (Pa)")
    parser.add_argument("--depth-corr-ol-wd", type=float, default=0.0, help="Depth correction for the olivine-wadsleyite transition (m)")
    parser.add_argument("--nominal-410-sink400", type=float, default=None, help="Runtime-adiabat 410 nominal (m), sink")
    parser.add_argument("--gravity", type=float, default=9.81, help="Gravity (m/s^2) (project.mk GRAVITY)")
    parser.add_argument("--ref-density", type=float, default=None, help="Reference density (kg/m^3) for the thermal split (project.mk REF_DENSITY)")
    parser.add_argument("--force", action="store_true", help="Overwrite output.")
    return parser.parse_args()


def nominal_transition(profile_path, model_height, surface_depth_offset, depth_corr):
    headers, data = read_dG_profile(profile_path)
    pt = find_transition(headers, data, model_height, surface_depth_offset)
    return pt.depth + depth_corr, pt.clapeyron


def interp_at(rep, field, depth):
    d = np.asarray(rep[field]["depths"], dtype=float)
    v = np.asarray(rep[field]["values"], dtype=float)
    m = np.isfinite(d) & np.isfinite(v)
    if m.sum() < 2:
        return np.nan
    return float(np.interp(depth, d[m], v[m]))


def col_like(df, *needles):
    for c in df.columns:
        if all(n in c for n in needles):
            return c
    raise KeyError(f"no column matching {needles} in {list(df.columns)}")


def main():
    args = parse_arguments()
    out_path = Path(args.out_csv)
    if out_path.exists() and not args.force:
        log_warn(f"skip {out_path} (exists; use --force)")
        return

    ref_headers, ref_data = read_dG_profile(args.profile_ol_wd)
    surface_offset = find_surface_depth_offset(ref_headers, ref_data, args.surface_pressure)
    rxn410, gamma410 = nominal_transition(args.profile_ol_wd, args.model_height, surface_offset, args.depth_corr_ol_wd)
    nominals = (args.nominal_410_sink400,)
    use_runtime_nominal = all(n is not None for n in nominals)

    rows = []
    data_dir = Path(args.data_dir)
    for tag in ("sink",):
        summary_csv = data_dir / f"structure-summary-{tag}.csv"
        seis_cache = data_dir / f"seismic-profile-cache-{tag}.pkl"
        if not summary_csv.exists() or not seis_cache.exists():
            continue
        try:
            loc = pd.read_csv(summary_csv)
        except pd.errors.EmptyDataError:
            continue
        if loc.empty:
            continue
        with open(seis_cache, "rb") as f:
            seis = pickle.load(f)
        models = loc[loc["model_id"].str.startswith("NH_")]
        rate_col = col_like(loc, "reaction_rate", "410")
        vmax_col = col_like(loc, "velocity_vertical", "410")
        for mid, grp in models.groupby("model_id"):
            m = UID_RE.match(mid)
            if not m:
                log_warn(f"skip {mid} (non-UID model)")
                continue
            if not (data_dir / mid / "solution" / "solution-00020.pvtu").exists():
                log_warn(f"skip {mid} (no final output)")
                continue
            ts = int(grp["timestep"].max())
            r = grp[grp["timestep"] == ts].iloc[0]
            try:
                rep = seis[mid][ts]["representative"]
            except KeyError:
                continue
            disp410 = float(r["displacement_410"])
            rho = args.ref_density if args.ref_density is not None else RHO_DEFAULT
            rxn = nominal_410_for_uid(mid, *nominals) if use_runtime_nominal else rxn410
            hatT410 = interp_at(rep, "nonadiabatic_temperature", rxn + disp410)
            therm410 = gamma410 * hatT410 / (rho * args.gravity)
            dampkind = m.group("dampkind")
            dampval = m.group("dampval") or "0"
            rows.append(
                {
                    "suite": tag,
                    "model_id": mid,
                    "timestep": ts,
                    "damp": f"{dampkind}{dampval}" if dampkind != "None" else "None",
                    "dynp": 1 if m.group("dynp") == "On" else 0,
                    "res": int(m.group("res")),
                    "z": m.group("z"),
                    "disp410_km": disp410 / 1e3,
                    "width410_km": abs(float(r["width_410"])) / 1e3,
                    "rate410_per_Ma": float(r[rate_col]),
                    "vmax410_cm_per_yr": float(r[vmax_col]),
                    "kin410_km": (disp410 - therm410) / 1e3,
                    "therm410_km": therm410 / 1e3,
                    "hatT410_K": hatT410,
                }
            )

    df = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    log_artifact(out_path)


if __name__ == "__main__":
    main()
