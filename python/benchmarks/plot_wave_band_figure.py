"""Prototype: band-cropped wave-evolution figure for one NH run.

One figure, 4 rows (timesteps) x 3 columns (set fields) + 1 context
column (block-position sketch). Panels show a narrow depth band centered
on the phase transition with a per-figure shared symmetric color scale
computed from band data only, so the spotty pressure wave sets the scale.

For sinking-block runs the pressure/density panels show the TRUE ambient-
referenced driver: the file values plus the static block load included in
the 1D adiabatic reference (must match BLOCK_Y_TOP/BLOCK_Y_BOT and GRAVITY
in project.mk). Box runs have no block field and are unaffected.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python
    python/benchmarks/plot_wave_band_figure.py --model NH_Sink_..._Res6
    --steps 0002 0004 0006 0008 --out figs/benchmarks/wave-band-S1.png
"""

import argparse
import os
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from matplotlib import patches

# Ambient-reference block-load correction (must match BLOCK_Y_TOP/BLOCK_Y_BOT
# and GRAVITY in project.mk).
AMBIENT_BLOCK_TOP_Y = 875e3
AMBIENT_BLOCK_BOT_Y = 725e3
AMBIENT_GRAVITY = 9.81

RESULTS = os.path.join(os.environ.get("PROJECT_ROOT", "."), "simulation/results")

SETS = {
    "set0": [
        ("nonadiabatic_pressure", "PuOr_r", 1e-6, "dynamic pressure (MPa)", "sym"),
        ("nonadiabatic_density", "BrBG", 1e-3, "dynamic density (g/cm3)", "sym"),
        ("velocity_vertical", "PiYG", 1e2, "vertical velocity (cm/yr)", "sym"),
    ],
    "set1": [
        ("dG_driving_0", "PuOr_r", 1e-3, "dG ol-wd (kJ/mol)", "sym"),
        ("reaction_rate_C0", "RdGy_r", 3.154e13, "Log Xdot ol-wd (1/Ma)", "signedlog"),
        ("xi_ol_wd", "GnBu", 1.0, "xi ol-wd (-)", "fixed01"),
    ],
}

PANEL_W = 1500


def transform(values, mode):
    if mode == "signedlog":
        return np.sign(values) * np.log10(1.0 + np.abs(values))
    return values


def read_step(model, step):
    step = step.zfill(5)
    path = os.path.join(RESULTS, model, "solution", "solution-" + step + ".pvtu")
    m = pv.read(path)
    p = np.asarray(m["p"])
    out = {
        "mesh": m,
        "points": np.asarray(m.points),
        "nonadiabatic_pressure": p - np.asarray(m["adiabatic_pressure"]),
        "nonadiabatic_density": np.asarray(m["density"]) - np.asarray(m["adiabatic_density"]),
        "velocity_vertical": np.asarray(m["velocity"])[:, 1],
    }
    if "block" in m.point_data:
        out["block"] = np.asarray(m["block"])
        bm = re.search(r"Block(\d+)", model)
        excess = float(bm.group(1)) if bm else 0.0
        if excess:
            y = out["points"][:, 1]
            overlap = np.where(
                y < AMBIENT_BLOCK_BOT_Y,
                AMBIENT_BLOCK_TOP_Y - AMBIENT_BLOCK_BOT_Y,
                np.where(y < AMBIENT_BLOCK_TOP_Y, y - AMBIENT_BLOCK_BOT_Y, 0.0),
            )
            out["nonadiabatic_pressure"] = out["nonadiabatic_pressure"] + excess * AMBIENT_GRAVITY * overlap
            depth = 1e6 - y
            in_band = (depth > 1e6 - AMBIENT_BLOCK_TOP_Y) & (depth < 1e6 - AMBIENT_BLOCK_BOT_Y)
            out["nonadiabatic_density"] = out["nonadiabatic_density"] + excess * in_band
    for name in ("dG_driving_0", "reaction_rate_C0", "xi_ol_wd"):
        if name in m.point_data:
            out[name] = np.asarray(m[name])
    return out


def step_time_myr(model, step):
    ts = os.path.join(RESULTS, model, "timeseries.csv")
    want = "solution-" + step.zfill(5)
    try:
        with open(ts) as f:
            header = f.readline().strip().split(",")
            ti, oi = header.index("time_yr"), header.index("output")
            for line in f:
                parts = line.strip().split(",")
                if parts[oi] == want:
                    return float(parts[ti]) / 1e6
    except OSError:
        pass
    return int(step) * 0.25


def band_clim(steps_data, field, scale, mode, yc, half):
    vals = []
    for d in steps_data:
        y = d["points"][:, 1]
        vals.append(transform(d[field][(y >= yc - half) & (y <= yc + half)] * scale, mode))
    vals = np.concatenate(vals)
    if mode == "fixed01":
        return (0.0, 1.0)
    m = float(np.max(np.abs(vals[np.isfinite(vals)])))
    return (-m, m)


def render_band_panel(data, field, cmap, scale, mode, clim, yc, half, cx, domain_w_m):
    mesh = data["mesh"].copy()
    mesh.point_data["__band"] = transform(data[field] * scale, mode)
    height_px = int(PANEL_W * 2 * half / 1e6 / (domain_w_m / 1e3))
    pl = pv.Plotter(off_screen=True, window_size=[PANEL_W, height_px], lighting="none")
    pl.background_color = "#FFFFFF"
    pl.add_mesh(mesh, scalars="__band", cmap=cmap, clim=clim, show_scalar_bar=False, show_edges=False, lighting=False)
    pl.camera_position = [(cx, yc, 1e6), (cx, yc, 0.0), (0.0, 1.0, 0.0)]
    pl.enable_parallel_projection()
    pl.camera.parallel_scale = half
    img = pl.screenshot(return_img=True)
    pl.close()
    pv.close_all()
    return img


def block_bbox(data):
    if "block" not in data:
        return None
    pts = data["points"][data["block"] > 0.5]
    if pts.shape[0] == 0:
        return None
    return (pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())


def draw_context(ax, bbox, nominal_y, yc, half, x0, x1):
    ax.set_xlim(x0, x1)
    ax.set_ylim(0, 1e6)
    ax.set_aspect("equal")
    ax.add_patch(patches.Rectangle((x0, 0), x1 - x0, 1e6, facecolor="#E5E5E5", edgecolor="black"))
    ax.add_patch(patches.Rectangle((x0, yc - half), x1 - x0, 2 * half, facecolor="#BFBFBF", edgecolor="black", linewidth=1.0))
    ax.axhline(nominal_y, color="black", linewidth=2.5)
    if bbox is not None:
        x0, x1, y0, y1 = bbox
        ax.add_patch(patches.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="#B36B00", edgecolor="black"))
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--steps", nargs=4, required=True)
    ap.add_argument("--nominal-410-m", type=float, default=362700.0)
    ap.add_argument("--band-half-km", type=float, default=50.0)
    ap.add_argument("--set", choices=["set0", "set1"], default="set0")
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="")
    args = ap.parse_args()
    fields = SETS[args.set]

    nominal_y = 1e6 - args.nominal_410_m
    yc = nominal_y
    half = args.band_half_km * 1e3

    steps_data = [read_step(args.model, s) for s in args.steps]
    times = [step_time_myr(args.model, s) for s in args.steps]
    clims = {f[0]: band_clim(steps_data, f[0], f[2], f[4], yc, half) for f in fields}

    # Domain extent from the mesh itself, so narrow (box) and square (sink)
    # setups are framed correctly instead of assuming a fixed width.
    xs = steps_data[0]["points"][:, 0]
    x0, x1 = float(xs.min()), float(xs.max())
    cx, domain_w_m = (x0 + x1) / 2.0, max(x1 - x0, 1e3)

    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(5, 4, height_ratios=[1, 1, 1, 1, 0.12], hspace=0.03, wspace=0.05)

    for i, (data, t) in enumerate(zip(steps_data, times)):
        for j, (field, cmap, scale, label, mode) in enumerate(fields):
            ax = fig.add_subplot(gs[i, j])
            img = render_band_panel(data, field, cmap, scale, mode, clims[field], yc, half, cx, domain_w_m)
            ax.imshow(img, aspect="auto")
            ax.set_xticks([])
            ax.set_yticks([])
            if j == 0:
                ax.set_ylabel("%.2f Myr" % t, fontsize=12)
            if i == 0:
                ax.set_title(label, fontsize=12)
        axc = fig.add_subplot(gs[i, 3])
        draw_context(axc, block_bbox(data), nominal_y, yc, half, x0, x1)
        if i == 0:
            axc.set_title("block position", fontsize=12)

    for j, (field, cmap, scale, label, mode) in enumerate(fields):
        ax = fig.add_subplot(gs[4, j])
        ax.set_axis_off()
        sm = plt.cm.ScalarMappable(cmap=plt.get_cmap(cmap), norm=plt.Normalize(*clims[field]))
        plt.colorbar(sm, ax=ax, orientation="horizontal", fraction=1.0, aspect=30)

    if args.title:
        fig.suptitle(args.title)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    print("wrote " + args.out)
    print("clims: " + str({k: (round(v[0], 1), round(v[1], 1)) for k, v in clims.items()}))


if __name__ == "__main__":
    sys.exit(main())
