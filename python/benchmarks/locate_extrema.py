"""Locate extrema cells in the final solution of a benchmark run.

Usage (repo root):
  conda run -n kerswell-et-al-nonhydrostatic-benchmarks python \
    python/benchmarks/locate_extrema.py simulation/results/<run>
"""

import os
import sys

import numpy as np


def main(run_dir):
  import pyvista as pv

  sol_dir = os.path.join(run_dir, "solution")
  if not os.path.isdir(sol_dir):
    print(f"no solution dir: {sol_dir}")
    return
  pvtu = sorted(f for f in os.listdir(sol_dir) if f.endswith(".pvtu"))
  mesh = pv.read(os.path.join(sol_dir, pvtu[-1]))
  print(f"file: {pvtu[-1]}  bounds: {mesh.bounds}")
  for name in ("nonadiabatic_pressure", "xi_ol_wd", "density", "viscosity"):
    if name not in mesh.array_names:
      print(f"  {name}: MISSING")
      continue
    a = np.asarray(mesh[name]).ravel()
    pts = np.asarray(mesh.points)
    for tag, idx in (("max", int(np.argmax(a))), ("min", int(np.argmin(a)))):
      print(f"  {name} {tag}={a[idx]:.6g} at x={pts[idx, 0]:.3g} y={pts[idx, 1]:.3g}")


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("usage: locate_extrema.py simulation/results/<run>")
  else:
    main(sys.argv[1])
