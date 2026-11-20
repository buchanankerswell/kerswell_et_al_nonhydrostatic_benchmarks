"""Depth-window composition figure for one NH run.

One figure, 4 rows (steps) x 3 columns (field panels) + 1 context column
(particle path for the box, block shape for the sink). Panels show a narrow
depth window centered on the phase transition with a per-figure shared
symmetric color scale computed from window data only, so the localized
pressure signal sets the scale.

For sinking-block runs the pressure/density panels show the TRUE ambient-
referenced driver: the file values plus the static block load included in
the 1D adiabatic reference (must match BLOCK_Y_TOP/BLOCK_Y_BOT and GRAVITY
in project.mk). Box runs have no block field and are unaffected.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python
    python/benchmarks/plot_depth_window.py --model NH_Sink_..._Res6
    --steps 00002 00006 00012 00020 --out figs/benchmarks/depth-window-S1.png
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
        ("nonadiabatic_pressure", "PuOr_r", 1e-6, "$\\hat{P}$ (MPa)", "sym"),
        ("nonadiabatic_density", "BrBG", 1e-3, "$\\hat{\\rho}$ (g/cm$^3$)", "sym"),
        ("velocity_vertical", "PiYG", 1e2, "$\\vec{u}_y$ (cm/yr)", "sym"),
    ],
    "set1": [
        ("dG_driving_0", "PuOr_r", 1e-3, "$dG$ (kJ/mol)", "sym"),
        ("reaction_rate_C0", "RdGy_r", 3.154e13, "$\\dot{X}$ (1/Ma)", "signedlog"),
        ("xi_ol_wd", "GnBu", 1.0, "$\\xi$ (-)", "fixed01"),
    ],
}

PANEL_W = 1500

# Schematic particle for the box particle-path column: starts near the top
# and sinks at a visible rate so the downward flow reads clearly.
PARTICLE_X_M = 150e3
PARTICLE_Y0_M = 900e3
PARTICLE_SINK_M_PER_MYR = 25e3


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
            in_window = (depth > 1e6 - AMBIENT_BLOCK_TOP_Y) & (depth < 1e6 - AMBIENT_BLOCK_BOT_Y)
            out["nonadiabatic_density"] = out["nonadiabatic_density"] + excess * in_window
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


def window_clim(steps_data, field, scale, mode, yc, half):
    vals = []
    for d in steps_data:
        y = d["points"][:, 1]
        vals.append(transform(d[field][(y >= yc - half) & (y <= yc + half)] * scale, mode))
    vals = np.concatenate(vals)
    if mode == "fixed01":
        return (0.0, 1.0)
    m = float(np.max(np.abs(vals[np.isfinite(vals)])))
    return (-m, m)


def render_window_panel(data, field, cmap, scale, mode, clim, yc, half, cx, domain_w_m):
    mesh = data["mesh"].copy()
    mesh.point_data["__window"] = transform(data[field] * scale, mode)
    height_px = max(int(PANEL_W * (2 * half) / domain_w_m), 50)
    pl = pv.Plotter(off_screen=True, window_size=[PANEL_W, height_px], lighting="none")
    pl.background_color = "#FFFFFF"
    pl.add_mesh(mesh, scalars="__window", cmap=cmap, clim=clim, show_scalar_bar=False, show_edges=False, lighting=False)
    pl.camera_position = [(cx, yc, 1e6), (cx, yc, 0.0), (0.0, 1.0, 0.0)]
    pl.enable_parallel_projection()
    pl.camera.parallel_scale = half
    img = pl.screenshot(return_img=True)
    pl.close()
    pv.close_all()
    return img


def draw_particle_path(ax, time_myr, nominal_y, yc, half, x0, x1):
    face = "#E5E5E5"
    ax.set_facecolor(face)
    ax.set_xlim(x0, x1)
    ax.set_ylim(0, 1e6)
    ax.set_aspect("equal")
    ax.add_patch(patches.Rectangle((x0, yc - half), x1 - x0, 2 * half, facecolor="#BFBFBF", edgecolor="black", linewidth=1.0))
    ax.axhline(nominal_y, color="black", linewidth=2.0)
    y_now = PARTICLE_Y0_M - PARTICLE_SINK_M_PER_MYR * time_myr
    y_prev = PARTICLE_Y0_M - PARTICLE_SINK_M_PER_MYR * max(time_myr - 1.0, 0.0)
    ax.annotate(
        "",
        xy=(PARTICLE_X_M, y_now),
        xytext=(PARTICLE_X_M, y_prev + 30e3),
        arrowprops=dict(arrowstyle="->", color="black", lw=1.5),
    )
    ax.plot([PARTICLE_X_M], [y_now], marker="o", color="#B36B00", markeredgecolor="black", ms=7, zorder=5)
    set_depth_ticks(ax)


def draw_block_shape(ax, data, nominal_y, yc, half, x0, x1):
    face = "#E5E5E5"
    ax.set_facecolor(face)
    ax.set_xlim(x0, x1)
    ax.set_ylim(0, 1e6)
    ax.set_aspect("equal")
    ax.add_patch(patches.Rectangle((x0, yc - half), x1 - x0, 2 * half, facecolor="#BFBFBF", edgecolor="black", linewidth=1.0))
    ax.axhline(nominal_y, color="black", linewidth=2.0)
    if "block" in data:
        pts = data["points"][data["block"] > 0.5]
        if pts.shape[0]:
            stride = max(pts.shape[0] // 2000, 1)
            ax.scatter(pts[::stride, 0], pts[::stride, 1], s=4, color="#B36B00", edgecolors="none", zorder=4)
    set_depth_ticks(ax)


def set_depth_ticks(ax):
    depths_km = [0, 250, 500, 750, 1000]
    ax.set_yticks([1e6 - d * 1e3 for d in depths_km])
    ax.set_yticklabels([str(d) for d in depths_km], fontsize=8)
    ax.tick_params(axis="y", labelright=True, labelleft=False, length=0)
    ax.set_xticks([])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--steps", nargs=4, required=True)
    ap.add_argument("--nominal-410-m", type=float, default=362700.0)
    ap.add_argument("--window-half-km", type=float, default=50.0)
    ap.add_argument("--set", choices=["set0", "set1"], default="set0")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    fields = SETS[args.set]

    nominal_y = 1e6 - args.nominal_410_m
    yc = nominal_y
    half = args.window_half_km * 1e3

    steps_data = [read_step(args.model, s) for s in args.steps]
    times = [step_time_myr(args.model, s) for s in args.steps]
    clims = {f[0]: window_clim(steps_data, f[0], f[2], f[4], yc, half) for f in fields}

    # Domain extent from the mesh itself, so narrow (box) and square (sink)
    # setups frame correctly instead of assuming a fixed width.
    xs = steps_data[0]["points"][:, 0]
    x0, x1 = float(xs.min()), float(xs.max())
    cx, domain_w_m = (x0 + x1) / 2.0, max(x1 - x0, 1e3)
    is_sink = "block" in steps_data[0]

    # Panel widths follow the data aspect so screenshots fill their axes
    # with no stretching and no empty margins; the context column stays
    # narrow and snug against the third data column.
    r = domain_w_m / (2 * half)
    c = 1.6
    fig_w = min(1.55 * (3 * r + c) + 1.0, 20.0)
    fig = plt.figure(figsize=(fig_w, 8.5))
    gs = fig.add_gridspec(
        5,
        4,
        height_ratios=[1, 1, 1, 1, 0.12],
        width_ratios=[r, r, r, c],
        hspace=0.08,
        wspace=0.06,
    )

    for i, (data, t) in enumerate(zip(steps_data, times)):
        for j, (field, cmap, scale, label, mode) in enumerate(fields):
            ax = fig.add_subplot(gs[i, j])
            img = render_window_panel(data, field, cmap, scale, mode, clims[field], yc, half, cx, domain_w_m)
            ax.imshow(img, aspect="auto", extent=[0, 1, yc - half, yc + half])
            ax.text(
                0.03,
                0.88,
                "%.2f Million Years" % t,
                transform=ax.transAxes,
                fontsize=11,
                va="top",
                bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=2),
            )
            if j == 0:
                ax.set_yticks([yc - half, yc, yc + half])
                ax.set_yticklabels(
                    ["%.0f" % ((1e6 - y) / 1e3) for y in (yc - half, yc, yc + half)],
                    fontsize=8,
                )
            else:
                ax.set_yticks([])
            ax.set_xticks([])
            if i == 0:
                ax.set_title(label, fontsize=12)
        axc = fig.add_subplot(gs[i, 3])
        if is_sink:
            draw_block_shape(axc, data, nominal_y, yc, half, x0, x1)
            if i == 0:
                axc.set_title("Block Shape", fontsize=12)
        else:
            draw_particle_path(axc, t, nominal_y, yc, half, x0, x1)
            if i == 0:
                axc.set_title("Particle Path", fontsize=12)

    for j, (field, cmap, scale, label, mode) in enumerate(fields):
        ax = fig.add_subplot(gs[4, j])
        ax.set_axis_off()
        sm = plt.cm.ScalarMappable(cmap=plt.get_cmap(cmap), norm=plt.Normalize(*clims[field]))
        plt.colorbar(sm, ax=ax, orientation="horizontal", fraction=1.0, aspect=30)

    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    print("wrote " + args.out)
    print("clims: " + str({k: (round(v[0], 1), round(v[1], 1)) for k, v in clims.items()}))


if __name__ == "__main__":
    sys.exit(main())
