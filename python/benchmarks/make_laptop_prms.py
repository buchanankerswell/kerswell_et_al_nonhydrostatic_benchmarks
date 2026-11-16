"""Generate laptop-grade benchmark prms from the full-resolution definitions.

Full-resolution prms in simulation/benchmarks/ are the Barkla2 source of
truth (ref 6, 5 Myr). This script derives ref-5 / 2-Myr laptop copies into
simulation/benchmarks/laptop/ (gitignored) with _laptop output dirs, for
fast iteration. Regenerate after any full-prm change.

Usage (repo root):
  conda run -n kerswell-et-al-mtz-kinetics python \\
    python/benchmarks/make_laptop_prms.py
"""

import glob
import os
import sys

SRC_DIR = "simulation/benchmarks"
DST_DIR = os.path.join(SRC_DIR, "laptop")

REPLACEMENTS = [
    ("set Initial global refinement          = 6",
     "set Initial global refinement          = 5"),
    ("set End time                      = 5e+06",
     "set End time                      = 2e+06"),
]


def laptop_name(src_path):
  base = os.path.basename(src_path)
  name, ext = os.path.splitext(base)
  return name + "_laptop" + ext


def main():
  os.makedirs(DST_DIR, exist_ok=True)
  made = []
  for src in sorted(glob.glob(os.path.join(SRC_DIR, "nh_sink_block_*.prm"))):
    with open(src) as f:
      text = f.read()
    for old, new in REPLACEMENTS:
      assert old in text, f"pattern missing in {src}: {old}"
      text = text.replace(old, new)
    # Redirect output dir: simulation/results/<run> -> <run>_laptop
    lines_out = []
    for line in text.splitlines():
      if line.startswith("set Output directory"):
        line = line.rstrip() + "_laptop"
      lines_out.append(line)
    dst = os.path.join(DST_DIR, laptop_name(src))
    with open(dst, "w") as f:
      f.write("\n".join(lines_out) + "\n")
    made.append(dst)
  print(f"Wrote {len(made)} laptop prms -> {DST_DIR}/")
  for m in made:
    print("  " + m)


if __name__ == "__main__":
  sys.exit(main())
