# Session handoff — UID finalization, Z sweep, gravity alignment, housecleaning (2026-11-18)

Branch `agent/initial-benchmark`, pushed through `0d942bd`. Tree clean.
Prior handoff: `research/nonhydrostatic_benchmarks/session-handoff-2026-11-17-analysis.md` (committed).

## Parameter sweep (final, user-approved)
- UIDs carry sweep params only: `NH_{Box,Sink}_Dynp{d}_Damp{kind+val}[_Block{b}]_Z{z}_Res{r}`. End dropped (suite constants `END_BOX=1e7`, `END_SINK=5e6`); CFL dropped (fixed `CFL_BOX=7e-01`, `CFL_SINK=5e-01` — low sensitivity: box flat, sink timing-only).
- Full damping x Res(4-7) x Z(LO/MID/HI) cross: **72 box + 96 sink = 168 UIDs**, all registered in `simulation/local.mk`, asserted against `ID_B1..12`/`ID_S1..16` (Z_MID arms).
- Z anchors: LO=9.51e-08 (410-sluggish, frozen limit), MID=4.44e-04 (current matrix), HI=1.4e+04 (660-nominal, near-instantaneous; may be stiff at Res7 — flagged).
- End-time evidence (local probes): box front/p2p steady from 0.5 Myr, but Bimpl-Res6 goes unstable at 4–5 Myr (max rate 7.6 → 196/Ma), so 1e7 covers onset+saturation; sink block leading edge reaches bottom ~4 Myr (ymin 16→8 km), p2p nearly flat at 5e6.
- Gravity aligned to 9.81 everywhere (`GRAVITY` constant → runtime gravity + init lithostatics; matches profile construction + postprocessing). `NOMINAL_410_*` STALE (measured under g=10): re-derive from Barkla2 no-feedback twins before use.

## Housecleaning (this session, committed `0d942bd`, +279/−1032)
- Makefiles: single `TIMESTEPS`; `MESH_SUITE` macro (verified via `make -n`); one Runtime constants block; dead vars removed (`FORCE_COMPOSE`, `FIGS_SETUP/KUBO`, `Z_410_NOMINAL_OL`, `BLOCK_EXCESS`, `NOMINAL_410_SINK0`); `bash all` removed; R CLEAN fixed; `figs/simulation` → `figs/benchmarks`+`figs/sink_block` in CLEAN.
- Python: slab purge (X_ps, slab UID parser, `is_bench` paths, NaN columns, dead table rows/plotter maps, `_add_vertical_line`, dead postprocessors, tile `fps`/`tiled_images`); single-profile mesh entry; `TransInfo` namedtuple; `benchmarks/common.py` (uid labels with Z + loaders); `transitions.py` now a pure library; `pair_titles.py` deleted.
- Bugs fixed: seismic `args`-scoping (nominals now params), `paper_set` trailing underscore, sink_sweep depth-as-height + TIME comment + damp-regex signs, missing `cli` dep, sync timestep over-match (exact zero-padded names), download threshold 168.
- R: Z-colored Res-faceted structure panels, numeric damping order, Z column in tables, Dynp-aware seismic colors, Sink naming unified, `cli` declared, recursive mkdir, adiabat missing-input guard, unified bool parsing.
- AGENTS.md audited (counts, sync description, no stale slab/CFL/smoke language).
- Deliberately kept: explicit 168-line REGISTER list, explicit PRMS rules (rejected `foreach`/`filter-out` rewrites as less readable/incorrect), distinct figure themes, slab-fallback trace path, adiabat plot bodies.

## Verified (no local runs — user runs everything on Barkla2)
- ruff format+check clean, R parse clean, styler/shfmt clean, py_compile + `--help` on all scripts, `make -n` across build/models/meshes/R/sync, 1680 generated configs (no placeholders, correct CFL/end/gravity per suite).

## Next
1. User pulls `agent/initial-benchmark` on Barkla2, runs 168 models.
2. Test `sync-barkla` (new UID shape + precise timestep filters).
3. Re-derive `NOMINAL_410_*` under g=9.81 from no-feedback twins; update R defaults.
4. R res-split/z-split + Bimpl-Res6-vs-Res7 instability analysis; manuscript rewrite.
- Note: local `simulation/results/` holds orphaned `_End`/`_CFL` run dirs + wiped mesh caches — leave until after sync, then `deep-clean` if desired. `figs/benchmarks` static pngs predate the UID change (regenerate post-sync).
