# Session handoff — postprocessors, formatters, plugin paths, DynpOn/Off (2026-11-17)

Branch `agent/initial-benchmark`, pushed through `55b31ee`. Tree clean.
Prior context: `research/nonhydrostatic_benchmarks/session-handoff-2026-11-18.md`
(note: `research/` + `review/` note dirs renamed `-` → `_` this session).

## Commits this session (all signed, all pushed)
- `2871ffa` Inputs in simulation/data, all outputs in simulation/results
- `e34d744` Per-step diagnostics, pinned formatters, naming cleanup
- `4e03a5d` Point plugin paths at out-of-source build dir
- `552bd93` Minor formatting (user's own commit)
- `e38cc03` Clean aspect symlinks via find pattern, keep plugin up to date
- `55b31ee` Spell dynamic-pressure UID slug DynpOn/DynpOff

## What changed
- **Layout rule**: required inputs in `simulation/data` (3 tracked Mg100 TSVs +
  adiabat products), everything produced in `simulation/results` (runs, mesh
  summaries/caches, `postprocessed.*`, `pressure-wave-summary.csv`).
- **Postprocess** (`shared/postprocess.prm`): added `velocity statistics`,
  `temperature statistics`, `depth average` (100 zones, T/composition/adiabatic-p/
  velocity/viscosity, viz cadence), `point values` every step with suite probes
  (`POINTS_BOX/SINK` in project.mk: 410 + deep control / block start).
- **Routes**: `extract_timeseries` → `timeseries.csv` + full-res
  `stats-timeseries.csv`; `quantify` → peak/final RMS + diminishment columns,
  per-step RMS-velocity + 410-probe pressure figures; new `plot_depth_average.py`
  (final T/xi, wired into `pressure-waves`); `reaction_rate_C0` in box/sink
  `fields_to_plot` + (pressure, rate, xi) tile set. Tested end-to-end on STEST
  (16 s Res4 run): stats cols 29–34, point_values.txt, depth_average.txt all land;
  table + all figures generate.
- **Formatters** (`make format`): ruff (env-pinned, `pyproject.toml`, 150 col) +
  `ruff check`, styler + lintr (R, incl. `styler`/`lintr` in environment.R),
  `shfmt -i 2 -ci`, astyle 2.04 with ASPECT's `astyle.rc` (repo root;
  `.clang-format` deleted). `ruff` caught one real F821. `lintr` fully clean
  after renaming SCREAMING R names + wrapping 2 long lines. Idempotent.
- **Separators**: no dash-dirs, no underscore filenames left (UIDs + python
  modules exempt). `research/` + `review/` → underscores; 8 `openalex_*` →
  dashes with cross-refs updated; `.ruff_cache` removed + gitignored.
- **Plugin paths**: `ASPECT_PLUGIN` → `plugins/build/*` + out-of-source
  `cmake ..` recipe (was stale in-source paths forcing rebuild every make).
  `make clean` removes `build/aspect*` via widened find pattern
  (`*/plugins*/aspect*`) + `build/compile_commands.json` via list; stale root
  `compile_commands.json` deleted (live one is in build/). Rebuilt twice
  against `/opt/aspect/v3.2.0-pre-bulk-viscosity-chain`; dry-run shows no-op.
- **UIDs**: `Dynp1/Dynp0` → `DynpOn/DynpOff` (numeric PARAM_dynp unchanged).
  Exporter/quantify/sweep/R-seismic parsers updated; 420 configs regenerated,
  all new spelling. Old `results/` dirs orphaned by the rename.
- **Permissions**: user granted push to `agent/*`; pushed. Cannot kill the
  user's (`bck`) processes — EPERM; user stops their own runs.

## Active state
- User is running the full 42-model set locally right now. When done:
  `timeseries` → `pressure-waves` → `postprocess` → meshes + R, then iterate.
- After iteration: Barkla2 high-res, Z sweep (520 values still unknown),
  R tailoring, manuscript rewrite (still 660-era), montages.

## Gotchas hit
- `make -C simulation <target>` needs repo-absolute (or simulation-rel) paths;
  repo-relative `simulation/configs/...` fails to resolve the prm.
- The aspect root symlink re-point (14:52) newer than old .so correctly forced
  a plugin rebuild — that logic is what caught the stale list.
- Symlinks in ASPECT_PLUGIN = permanent rebuild trap (make follows links;
  `build/aspect` and the `aspect-release` prerequisite resolve to different
  binaries with different mtimes — prerequisite always newer).
- `make clean` wipes the plugin (CLEAN includes ASPECT_PLUGIN) — any clean
  needs a rebuild before models; `%.run` guards live in wiped `configs/`.
- `ls --time-style` is GNU-only; macOS `ls -D` instead.
- `.run` guard written only on exit 0 — killed runs re-run cleanly.
- `git add -A` stages `research/` notes (tracked); AGENTS.md is gitignored
  local-only — doc edits there never travel with commits.
- zsh does not word-split `$VAR`; conda env hand-fixed (numpy→2.4.6, +ruff).
- conda-forge astyle is 3.x — must use deal.II's bundled 2.04 binary.
