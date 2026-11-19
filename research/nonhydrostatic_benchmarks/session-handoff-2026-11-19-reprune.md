# Session handoff — 2026-11-19 evening: ambient reference + ground-zero reprune

Branch `agent/initial-benchmark`, continuing from `82f7f55`.

## Ambient reference (committed in 82f7f55, locally tested at Res4)
- ASPECT's 1D adiabat is integrated down a column through the initial block,
  baking ~589 MPa into `P_ref`. Plugin now subtracts the static block load
  (`AMBIENT_REF`, `BLOCK_Y_TOP/BOT`, `project.mk`; no-op for box).
- 4 local Res4 sink runs (twin/undamped/cap/bimpl): fronts all 382.8 km,
  far-field driving pressure -34 MPa, wave intact at ~1085 MPa peak.
- Consequence: old On-vs-Off static displacement (+15.6 Res4 / +20 Res6) was
  reference artifact (dG algebra cancels `P_ref` for undamped fronts). Paper
  signals are now: transient wave, front excursion during passage,
  nonlinear-damping distortion. Box suite unaffected (clean ref all along).
- `NOMINAL_410_SINK400` stale (~383 km expected at Res6; re-derive from new S2).
- ASPECT's own `nonadiabatic_pressure` visualization field still uses the old
  reference; display code adds the correction inline (`extract_timeseries`
  ambient columns, band-figure script). No-feedback `DynpOff` runs still
  compute `P_ref` for profile lookup, so twins move too — that is intended.

## Ground-zero reprune (this session, uncommitted at handoff time)
- Wiped local `simulation/results`, `simulation/configs`, all `figs`, generated
  `simulation/data` (`make deep-clean` + `make clean`). Barkla side already
  cleared by user. Ready for `pull` + fresh sweep.
- Sweep is now 18 runs: paper 6 box Res5 + 8 sink Res6 (Z_MID only) + 4
  timestep-scaling runs (box undamped Res5 CFL 0.35/1.4; sink undamped Res6
  CFL 0.25/1.0; base CFLs are B1/S1). Per-model CFL via `PARAM_cfl_*` +
  optional `_CFL{c}` UID suffix (`local.mk` rewritten, `project.mk` macros).
- `TIMESTEPS` cut to 5 wave-arc steps: 000 002 006 012 020. NOTE: an
  unexplained 9-sparse→11-even TIMESTEPS change rode into 82f7f55; user
  chose minimal-5 instead. Watch for stray working-tree edits.
- Z labels renamed: frozen→sluggish, matrix→intermediate, instant→
  quasi-equilibrium (`R/utils/simulation.R`; prose in `project.mk`/AGENTS).
- New `make scaling` target + `python/benchmarks/plot_scaling.py`:
  wave size vs Res (h) and vs CFL (dt), plus front-error vs twin vs CFL.
  Parses `cfl` from UIDs (`common.py`). Sparse-data safe (skips empty).
- `bash/.../download-zenodo.sh` completeness threshold 168→18.
- Comments trimmed to minimal plain language in touched files.

## Next
1. Commit + push this session, user pulls on Barkla.
2. Barkla: `rm -f plugins/build/libnh-kinetics.*.so configs/NH_Sink_*.run`
   (already cleared, but be safe), `make -C simulation configs`,
   `make -C simulation all-models` (rebuilds plugin, 18 fresh runs).
3. New S2 lands → re-derive `NOMINAL_410_SINK400`, forced re-mesh, downstream.
4. `make scaling` once summaries exist; band-figure v3 already ambient-clean.
