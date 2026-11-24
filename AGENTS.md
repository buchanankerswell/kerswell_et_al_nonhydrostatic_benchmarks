# Repository guide

Study of spurious pressure waves in compressible ASPECT models. Dynamic pressure drives kinetic phase transformations; with zero bulk viscosity the loop produces spurious oscillations. The sink benchmark suite compares damping treatments. Read `notes/` for the framing, results, and open questions.

## Layout

- `project.mk` — suite run names, physical constants, and all Make variables. Start here.
- `simulation/local.mk` — registers the 25 sink runs.
- `simulation/params/templates/NH/` — PRM templates (`shared/`, `sink/`).
- `simulation/plugins/nh-kinetics.{cc,h}` — kinetic material-model plugin.
- `simulation/results/` — ASPECT output and derived CSVs (generated, not tracked).
- `python/` — postprocessing and figure scripts. `R/` — structure and seismic figures.
- `figs/` — rendered figures (generated, not tracked).
- `draft/` — manuscript, SI, and bibliography.
- `notes/` — session logs, key results, benchmark and figure notes.
- `bash/` — run and sync scripts for macOS and Barkla2.

## Commands

- `make build` — fetch data, reproduce results and figures, and build the PDF; it does not run simulations.
- `make postprocess` — derive CSVs and render every figure.
- `make models` — run all ASPECT models. Needs `aspect/` and `dealii/` links at the repo root.
- `make format` — format Python, R, bash, and C++.
- `make clean` — remove generated files. `make deep-clean` also removes results.

`FIG_DPI` (100 draft, 330 manuscript) and `MESH_TIMESTEPS` come from `project.mk`; pass them on the command line to override.

## Conventions

Run names record what varies: `Dynp`, `Damp`, `Block`, `Z`, `Res`, `CFL`. S1 is the undamped full-feedback baseline; S2 is the no-feedback reference. Treat `simulation/results/` and `figs/` as build output: fix a figure by changing its script and rerunning the target. CI runs static checks only (markdownlint, typos, R, Python); models need HPC and stay local. Put session logs and handoffs in `notes/`.

Figure scripts skip outputs that already exist; pass `--force` or run `make clean` to redraw them.

Old handoff files under `research/nonhydrostatic_benchmarks/` survive only in committed history. They use retired naming and stale content; `notes/` is the live set.
