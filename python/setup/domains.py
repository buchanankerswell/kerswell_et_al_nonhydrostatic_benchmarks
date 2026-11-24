"""Domain sketch for the sinking-block benchmark."""

import argparse
import os
from pathlib import Path

from utils.artifacts import add_force_argument, outputs_exist
from utils.logging import log_artifact

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from simulation.mesh.config import apply_bench_style
from simulation.params.transitions import load_depth_datum, model_to_true_km, true_to_model_km

DATUM = Path(os.environ.get("PROJECT_ROOT", ".")) / "simulation/data/depth-datum.tsv"


def parse_probes(spec):
    points = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        x_str, y_str = chunk.split(",")
        points.append((float(x_str), float(y_str)))
    return points


def draw_domain(suite, width, height, trans_y, trace_x, nominal, probes, out, dpi=100):
    datum = load_depth_datum(str(DATUM))
    fig, ax = plt.subplots(figsize=(7, 8))
    ax.set_xlim(-0.08 * width, 1.45 * width)
    ax.set_ylim(-0.05 * height, 1.08 * height)
    ax.set_aspect("equal")
    ax.set_xlabel("Distance (km)")
    ax.set_ylabel("Depth (km)")

    ax.add_patch(Rectangle((0, 0), width, height, fill=False, edgecolor="black", lw=2))

    trans_depth = float(model_to_true_km((height - trans_y) / 1e3, datum, suite))
    ax.axhline(trans_y, color="black", ls="--", lw=1.5)
    ax.text(width * 1.02, trans_y + 15e3, f"initial $\\xi$ step {trans_depth:.0f} km", va="center")

    if nominal is not None:
        nom_y = height - nominal
        nom_true = float(model_to_true_km(nominal / 1e3, datum, suite))
        ax.axhspan(nom_y - 10e3, nom_y + 10e3, color="grey", alpha=0.4)
        ax.text(width * 1.02, nom_y - 15e3, f"410 nominal {nom_true:.0f} km", va="center", color="dimgrey")

    ax.axvline(trace_x, color="dimgrey", ls=":", lw=1.5)
    ax.text(
        trace_x,
        height * 0.55,
        f"trace x={trace_x / 1e3:.0f} km",
        rotation=90,
        va="center",
        ha="center",
        bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1),
    )

    for i, (px, py) in enumerate(probes):
        ax.plot(px, py, marker="o", color="black", ms=6)
        ax.text(px + width * 0.04, py, f"P{i}", va="center")

    if suite == "sink":
        bx0, bx1, by0, by1 = 4.25e5, 5.75e5, 7.25e5, 8.75e5
        ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fill=False, edgecolor="black", lw=1.5, hatch="///"))
        ax.text((bx0 + bx1) / 2, by1 + height * 0.01, "dense block", ha="center")
        ax.text(width / 2, height * 1.055, "free-slip all walls, top fixed T", ha="center")
        ax.text(width / 2, -height * 0.02, f"{width / 1e3:.0f} x {height / 1e3:.0f} km", ha="center")

    ax.set_xticks([0, width / 2, width])
    ax.set_xticklabels([0, f"{width / 2 / 1e3:.0f}", f"{width / 1e3:.0f}"])
    true_ticks = [100, 300, 500, 700, 900]
    ax.set_yticks([height - float(true_to_model_km(t, datum, suite)) * 1e3 for t in true_ticks])
    ax.set_yticklabels([f"{t}" for t in true_ticks])
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=dpi)
    plt.close(fig)
    log_artifact(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", required=True, choices=["sink"], help="Suite tag")
    ap.add_argument("--width-m", type=float, required=True, help="Model width (m)")
    ap.add_argument("--height-m", type=float, required=True, help="Model height (m)")
    ap.add_argument("--transition-y-m", type=float, required=True, help="Init-step transition height (m)")
    ap.add_argument("--trace-x-m", type=float, required=True, help="Representative-trace x (m)")
    ap.add_argument("--nominal-m", type=float, default=None, help="Runtime-adiabat 410 nominal (m)")
    ap.add_argument("--probes", default="", help="Probe points as x,y (m);x,y (m)")
    ap.add_argument("--out", required=True, help="Output figure path")
    ap.add_argument("--dpi", type=int, default=100, help="Figure resolution (project.mk FIG_DPI; draft 100, manuscript 330)")
    add_force_argument(ap)
    args = ap.parse_args()

    if outputs_exist(args.out, args.force):
        return

    apply_bench_style(args.dpi)
    draw_domain(
        args.suite,
        args.width_m,
        args.height_m,
        args.transition_y_m,
        args.trace_x_m,
        args.nominal_m,
        parse_probes(args.probes),
        Path(args.out),
        args.dpi,
    )


if __name__ == "__main__":
    main()
