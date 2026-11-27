"""Dynamic-pressure diagnostics along the 410 for the transient sink steps."""

import argparse
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from benchmarks.plot_depth_window import read_step
from simulation.mesh.config import BENCH_WIDE_W, apply_bench_style, bench_color, bench_label
from simulation.params.transitions import load_depth_datum, model_to_true_km
from utils.artifacts import add_force_argument, outputs_exist
from utils.logging import log_artifact, log_warn

RESULTS = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/results"
DATUM = RESULTS.parent / "data" / "depth-datum.tsv"

MARGIN_M = 50e3
LONG_KM = 200.0
GRID_KM = 20.0


def lateral_slice(model, step, nominal_m, block_top_m, block_bottom_m, gravity):
    """Ambient-corrected pressure along nominal 410, margins excluded."""
    d = read_step(model, step, block_top_m, block_bottom_m, gravity)
    y0 = 1e6 - nominal_m
    sl = d["mesh"].slice(normal="y", origin=(0, y0, 0))
    if sl.n_points < 8 or "nonadiabatic_pressure" not in sl.point_data:
        return None, None
    x = np.asarray(sl.points[:, 0])
    vals = np.asarray(sl["nonadiabatic_pressure"])
    o = np.argsort(x)
    x, vals = x[o], vals[o]
    keep = (x > MARGIN_M) & (x < 1e6 - MARGIN_M)
    x, vals = x[keep], vals[keep]
    if x.size < 8 or not np.all(np.isfinite(vals)):
        return None, None
    # TIME is model years; lateral CSV carries Ma.
    t = d["mesh"].field_data.get("TIME", [np.nan])[0] / 1e6 if "TIME" in d["mesh"].field_data else np.nan
    return (x, vals), t


def band_powers(x, vals):
    """RMS per wavelength band: long, mid, grid (MPa)."""
    centered = vals - vals.mean()
    dx = float(np.median(np.diff(x)))
    spec = np.fft.rfft(centered)
    freq = np.fft.rfftfreq(x.size, dx)
    amp = np.abs(spec) / x.size
    with np.errstate(divide="ignore"):
        wavelength = np.where(freq > 0, 1.0 / freq, np.inf)

    def rms(mask):
        return float(np.sqrt((amp[mask] ** 2).sum())) if np.any(mask) else 0.0

    return (
        rms(wavelength > LONG_KM * 1e3),
        rms((wavelength <= LONG_KM * 1e3) & (wavelength > GRID_KM * 1e3)),
        rms(wavelength <= GRID_KM * 1e3),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True, help="Sink run UIDs to score")
    ap.add_argument(
        "--steps",
        nargs="+",
        default=[f"{s:05d}" for s in range(13)],
        help="Transient output numbers to sample (default 00000-00012)",
    )
    ap.add_argument("--nominal-m", type=float, required=True, help="Nominal 410 depth (m) (project.mk NOMINAL_410_SINK400)")
    ap.add_argument("--block-top-m", type=float, default=875e03, help="Block top (m) (project.mk BLOCK_Y_TOP)")
    ap.add_argument("--block-bottom-m", type=float, default=725e03, help="Block bottom (m) (project.mk BLOCK_Y_BOT)")
    ap.add_argument("--gravity", type=float, default=9.81, help="Gravity (m/s^2) (project.mk GRAVITY)")
    ap.add_argument("--out-csv", default=str(RESULTS / "lateral-pressure.csv"), help="Output CSV path")
    ap.add_argument("--fig-dir", default="figs/benchmarks", help="Output figure directory")
    ap.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI; draft 100, manuscript 330)")
    add_force_argument(ap)
    args = ap.parse_args()

    out_csv = Path(args.out_csv)
    summary_fig = Path(args.fig_dir) / "lateral-oscillation-summary-sink.png"
    profile_fig = Path(args.fig_dir) / "lateral-pressure-profile-sink.png"
    if outputs_exist([out_csv, summary_fig, profile_fig], args.force):
        return

    apply_bench_style(args.dpi)

    rows = []
    profiles = {}
    for model in args.models:
        have = [s for s in args.steps if (RESULTS / model / "solution" / f"solution-{s}.pvtu").exists()]
        if len(have) < len(args.steps):
            log_warn(f"skip {model} (solutions missing)")
        for step in have:
            try:
                (x, vals), t = lateral_slice(model, step, args.nominal_m, args.block_top_m, args.block_bottom_m, args.gravity)
            except Exception as e:
                log_warn(f"skip {model} step {step} ({e})")
                continue
            if x is None:
                continue
            long, mid, grid = band_powers(x, vals)
            rows.append(
                {
                    "model_id": model,
                    "timestep": int(step),
                    "time_ma": round(float(t), 4) if np.isfinite(t) else "",
                    "mean_MPa": round(float(vals.mean()) / 1e6, 2),
                    "std_MPa": round(float(vals.std()) / 1e6, 2),
                    "p2p_MPa": round(float(vals.max() - vals.min()) / 1e6, 2),
                    "min_MPa": round(float(vals.min()) / 1e6, 2),
                    "max_MPa": round(float(vals.max()) / 1e6, 2),
                    "long_MPa": round(long / 1e6, 2),
                    "mid_MPa": round(mid / 1e6, 2),
                    "grid_MPa": round(grid / 1e6, 2),
                }
            )
            profiles[(model, step)] = (x / 1e3, vals / 1e6)
    if not rows:
        log_warn("no lateral samples collected")
        return

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    import csv

    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    log_artifact(out_csv)

    ctrl = next((m for m in args.models if "_DynpOn_DampNone_" in m and "_CFL" not in m), args.models[0])
    ctrl_grid = [(r["timestep"], r["grid_MPa"]) for r in rows if r["model_id"] == ctrl]
    peak_step = f"{max(ctrl_grid, key=lambda kv: kv[1])[0]:05d}" if ctrl_grid else args.steps[len(args.steps) // 2]

    def line_kw(model):
        if model == ctrl:
            return dict(lw=2.4, color=bench_color(model), label=bench_label(model), alpha=1.0)
        return dict(lw=1.3, color=bench_color(model), label=bench_label(model), alpha=0.85)

    fig, ax = plt.subplots(3, 1, figsize=(5.0, 8.0), sharex=True)
    for model in args.models:
        mr = [r for r in rows if r["model_id"] == model]
        ts = [r["timestep"] for r in mr]
        kw = line_kw(model)
        ax[0].plot(ts, [r["mean_MPa"] for r in mr], **kw)
        ax[1].plot(ts, [r["std_MPa"] for r in mr], **kw)
        ax[2].plot(ts, [r["grid_MPa"] for r in mr], **kw)
    for a in ax[:-1]:
        a.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)
    ax[0].set_ylabel("Mean dynamic pressure (MPa)", labelpad=8)
    ax[1].set_ylabel("Pressure standard deviation (MPa)", labelpad=8)
    ax[2].set_ylabel("Short-wavelength oscillation (MPa)", labelpad=8)
    ax[2].set_xlabel("Output Step")
    handles, labels = ax[0].get_legend_handles_labels()
    fig.subplots_adjust(left=0.13, right=0.68, top=0.95, bottom=0.07, hspace=0.2)
    fig.legend(handles, labels, loc="center left", bbox_to_anchor=(0.69, 0.5), frameon=True, facecolor="white", framealpha=0.9)
    summary_fig.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(summary_fig, dpi=args.dpi)
    plt.close(fig)
    log_artifact(summary_fig)

    t_ma = next((r["time_ma"] for r in rows if r["timestep"] == int(peak_step)), None)
    datum = load_depth_datum(str(DATUM))
    true_km = float(model_to_true_km(args.nominal_m / 1e3, datum, "sink"))
    fig, ax = plt.subplots(figsize=(BENCH_WIDE_W, 3.4))
    for model in args.models:
        if (model, peak_step) in profiles:
            x, v = profiles[(model, peak_step)]
            ax.plot(x, v, **line_kw(model))
    ax.set_xlabel("Distance (km)")
    ax.set_ylabel("Pressure (MPa)")
    ax.set_title(f"Lateral Profiles, {t_ma:.2f} Ma, {true_km:.0f} km depth")
    handles, labels = ax.get_legend_handles_labels()
    fig.subplots_adjust(right=0.74, left=0.09, top=0.88, bottom=0.14)
    fig.legend(handles, labels, loc="center left", bbox_to_anchor=(0.76, 0.5), frameon=True, facecolor="white", framealpha=0.9)
    profile_fig.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(profile_fig, dpi=args.dpi)
    plt.close(fig)
    log_artifact(profile_fig)


if __name__ == "__main__":
    sys.exit(main())
