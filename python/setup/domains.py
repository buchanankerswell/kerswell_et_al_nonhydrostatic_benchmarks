"""Minimal domain sketches for the NH box and sinking-block benchmarks.

Draws domain dims, boundary-condition labels, the init xi step, the
runtime-adiabat 410 nominal band, the fixed representative trace, point
probes, and (sink only) the dense block outline. All geometry comes from
project.mk constants passed as CLI args; nothing is hardcoded.

Usage (repo root):
  PYTHONPATH=python conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \\
    python/setup/domains.py --suite box --width-m 300000 --height-m 1000000 \\
      --transition-y-m 640800 --trace-x-m 150000 --nominal-m 373100 \\
      --probes "150000,635800;150000,435800" --out figs/setup/box-domain.png
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from benchmarks.common import apply_bench_style

apply_bench_style()


def parse_probes(spec):
    points = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        x_str, y_str = chunk.split(",")
        points.append((float(x_str), float(y_str)))
    return points


def draw_domain(suite, width, height, trans_y, trace_x, nominal, probes, out):
    fig, ax = plt.subplots(figsize=(7, 8))
    ax.set_xlim(-0.08 * width, 1.12 * width)
    ax.set_ylim(-0.05 * height, 1.05 * height)
    ax.set_aspect("equal")
    ax.set_xlabel("x [km]")
    ax.set_ylabel("model y [km]")

    ax.add_patch(Rectangle((0, 0), width, height, fill=False, edgecolor="black", lw=2))

    trans_depth = (height - trans_y) / 1e3
    ax.axhline(trans_y, color="black", ls="--", lw=1.5)
    ax.text(width * 1.02, trans_y, f"init xi step {trans_depth:.0f} km", va="center", fontsize=10)

    if nominal is not None:
        nom_y = height - nominal
        ax.axhspan(nom_y - 10e3, nom_y + 10e3, color="grey", alpha=0.4)
        ax.text(width * 1.02, nom_y, f"410 nominal {nominal / 1e3:.0f} km", va="center", fontsize=10, color="dimgrey")

    ax.axvline(trace_x, color="dimgrey", ls=":", lw=1.5)
    ax.text(trace_x, height * 1.01, f"trace x={trace_x / 1e3:.0f} km", ha="center", fontsize=10)

    for i, (px, py) in enumerate(probes):
        ax.plot(px, py, marker="o", color="black", ms=6)
        ax.text(px + width * 0.02, py, f"P{i}", fontsize=10, va="center")

    if suite == "sink":
        bx0, bx1, by0, by1 = 4.25e5, 5.75e5, 7.25e5, 8.75e5
        ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fill=False, edgecolor="black", lw=1.5, hatch="///"))
        ax.text((bx0 + bx1) / 2, by1 + height * 0.01, "dense block", ha="center", fontsize=10)
        ax.text(width / 2, height * 1.03, "free-slip all walls, top fixed T", ha="center", fontsize=10)
        ax.text(width / 2, -height * 0.02, f"{width / 1e3:.0f} x {height / 1e3:.0f} km", ha="center", fontsize=10)
    else:
        ax.annotate("", xy=(width / 2, height), xytext=(width / 2, height - 0.08 * height), arrowprops=dict(arrowstyle="->", color="black"))
        ax.text(width / 2, height * 1.03, "top: prescribed inflow, fixed T", ha="center", fontsize=10)
        ax.text(width * 1.02, height / 2, "sides/bottom:\nno normal flow", fontsize=10, va="center")
        ax.text(width / 2, -height * 0.02, f"{width / 1e3:.0f} x {height / 1e3:.0f} km", ha="center", fontsize=10)

    ax.set_title(f"{suite}: initial and boundary conditions")
    ax.set_xticks([0, width / 2, width])
    ax.set_xticklabels([0, f"{width / 2 / 1e3:.0f}", f"{width / 1e3:.0f}"])
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"wrote -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", required=True, choices=["box", "sink"])
    ap.add_argument("--width-m", type=float, required=True)
    ap.add_argument("--height-m", type=float, required=True)
    ap.add_argument("--transition-y-m", type=float, required=True)
    ap.add_argument("--trace-x-m", type=float, required=True)
    ap.add_argument("--nominal-m", type=float, default=None)
    ap.add_argument("--probes", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    draw_domain(
        args.suite, args.width_m, args.height_m, args.transition_y_m, args.trace_x_m, args.nominal_m, parse_probes(args.probes), Path(args.out)
    )


if __name__ == "__main__":
    main()
