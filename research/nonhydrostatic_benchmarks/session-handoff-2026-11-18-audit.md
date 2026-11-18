# Session handoff — analysis/visualization audits + Barkla2 smoke test (2026-11-18)

Branch `agent/initial-benchmark`. Commits this session: `5c000d8` (audit implementation), `2803330` (follow-up cuts + seismic palette). Prior handoff: `session-handoff-2026-11-18-housecleaning.md` (`0d942bd`).

## User decisions (asked before acting, all answered)
1. Tiles: cut to 2 sets — A) buoyancy (`P_hat`, `rho_hat`, `u_y`), B) kinetic feedback (`dG`, `rate`, `xi`). Rationale: isothermal suites (no T gradient), uniform viscosity.
2. Theme master: R `theme_bench` (grey92, no grid, dpi 300) for matplotlib too.
3. Setup figures: yes, new `python/setup/domains.py` generating `figs/setup/box|sink-domain.png` from `project.mk` constants.
4. Probe duplication: keep `probe_pressure` (make-wired), cut `plot_probe_history.py`.
5. Cuts/wiring: cut `depth_average` + `sink_block` from paper; keep `plot_joint_profiles.py` wired into `pressure-waves`; add `diagnostics` target for bimpl.
6. Follow-up: delete `locate_extrema.py` + `select_crossing_timesteps.py`; delete `plot_depth_average.py` entirely; unify seismic colors on shared damp palette; leave `draft/manuscript.md` refs for the rewrite.

## Implemented (`5c000d8`)
- `main.py`: 6 plotted fields, 2 tile sets (set0 buoyancy, set1 kinetic feedback).
- `config.py`: new `dG_driving_0` entry (PuOr_r, kJ/mol, trace on).
- `common.py`: `apply_bench_style()` (grey92, no grid, dpi 300, legend 11) + `parse_uid_columns()` (suite/damp/dynp/res/z for tables).
- `quantify_pressure_waves.py`: probe-call crash fixed (`load_probe_series(run, 0, field)`), CSV gains damp/dynp/res/z columns, bench style, legends upper-right.
- `plot_joint_profiles.py` + `plot_bimpl_resolution.py`: bench style, dpi 300.
- `pressure-waves` target: quantify + joint box/sink (nominal km via awk from `NOMINAL_410_*`); `depth_average` unwired. New `diagnostics` target (needs postprocess). `visualize` now `meshes + setup`; CLEAN drops `figs/sink_block`, gains `FIGS_SETUP` + `pressure-wave-summary.csv`. `project.mk`: `FIGS_SETUP`.
- Deleted: `plot_probe_history.py`, `plot_sink_sweep.py`.
- AGENTS.md pipelines section rewritten to match.

## Implemented (`2803330`)
- Deleted: `plot_depth_average.py`, `locate_extrema.py`, `select_crossing_timesteps.py`.
- `R/utils/seismic.R`: Vp color = damping value on shared family-grouped manual palette (`damp_pal`: None black, Bimpl reds, Bexpl blues, Rel greens, Cap purples), Dynp on/off as linetype (solid/dashed). Replaces default-hue `damp_dynp`.

## Verified
- ruff format+check clean, py_compile all, R parse OK, `make -n` across setup/pressure-waves/diagnostics/meshes, `make -C python setup` executed (both PNGs render).
- Two self-caught errors fixed before commit: a wrong function rename in seismic.R (reverted, diff clean) and a dropped nominal-defaults block (restored).

## Barkla2 smoke test — SUCCESS
- Test UID `NH_Box_DynpOn_DampNone_Z4.44e-04_Res4` on login node, 8 cores: full 10 Myr run in 46 s, clean end-time termination. Do NOT use `run-aspect-macos.sh` on Barkla2 (its `pkill -f mpirun` would kill other users' jobs).
- Local `make sync-barkla`: exact 9 sparse steps + final 020 for the test model, other 167 skip gracefully. Zero-padded filter fix confirmed working.
- Compositions show slight overshoot (-0.0381/1.013) — noted, not triaged.

## Next
1. Submit full sweep on Barkla2: `make -C simulation all-models` (or per-suite halves). Watch Z_HI Res7 arm (flagged stiff, 2.5-day walltime).
2. When no-feedback twins land (ID_B2 box Res5, ID_S2 sink Res6): `make sync-barkla`, then re-derive `NOMINAL_410_BOX/SINK400` under g=9.81 from dG=0 crossings; update `project.mk` + `R/utils/seismic.R` defaults. This unblocks thermal-kinetic split, structure panels, seismic band.
3. User will periodically sync; then R res/z-split + Bimpl-Res analysis, manuscript rewrite.
- Nominal staleness is the one load-bearing caveat: everything displacement/thermal downstream of `NOMINAL_410_*` inherits the g=10 offset until step 2.
