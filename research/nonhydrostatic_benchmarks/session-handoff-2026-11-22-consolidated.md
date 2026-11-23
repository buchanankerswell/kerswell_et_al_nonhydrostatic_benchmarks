# Handoff 2026-11-22 (consolidated): sink-only, Batch 0, corrected sweeps, audit

Branch `agent/initial-benchmark`, HEAD `4bc7690`, tree clean. Supersedes
the three earlier 11-22 notes (`sink-only`, `batch0-sweeps`,
`arkode-stall`); the one correction to carry forward is that the
"frozen tau" framing in `batch0-sweeps` is withdrawn (see units below).

## Commits this session (on top of `5e2cfa1`)

1. `81b7ab0` sink-only: box registrations, constants, build/vis targets,
   and box figure/table branches removed (25-file pipeline). Intentional
   leftovers: `project.mk` Macros section untouched (no-edits rule),
   datum keeps its box column, `templates/NH/box/` orphaned pending
   explicit `git rm`, box results/figs on disk are ignored build products.
2. `403e43a` Batch 0: `extract_lateral_pressure.py` + `make -C python
   lateral` (mean/std/p2p + long/mid/grid FFT bands along nominal 410,
   steps 0-12, scored vs undamped full feedback S1, not equilibrium).
   Registered 16 sweep UIDs (IDs S9-S24) with unique python/R colors.
3. `5fd39ae` ARKODE stall fix: sub-year taus (Rel e4/e5/e6) can never
   advance — the p_rel transient (~7x tau) sits ~100x below ARKODE's
   minimum substep (1e-6 x dt ~= 6.5 yr) and burns all 500 steps at step
   1 (`mxstep ... before reaching tout`, t ~= 2.0757e11 = step-1 time in
   internal seconds). Replaced with years-scale taus (S9/S10/S11 =
   e8/e9/e12); rescue and Res7 taus swapped e5 -> e11.
4. `6b8c707` unit labels: model-time inputs are years (ASPECT converts
   via `Use years instead of seconds`), kinetics stay SI seconds.
   Verified: mesh TIME is years, CFL0.25 abort at t = 1.05e5 yr.
5. `4bc7690` comment audit: plain language + units across python, R,
   bash, make, plugin, templates. No behavior change except two stale
   defaults (plot_depth_window nominal 379943 -> 379957; Zenodo check
   18 -> 25 models).

## Corrected physical picture (read this before the old notes)

- The model runs 5e6 YEARS, dt ~= 6560 yr, outputs every 250 kyr;
  transient steps 0-12 span ~0-3 Myr; velocities are ~m/yr.
- Taus in years: e4 = 8.8 hr, e5 = 3.65 d, e6 = 36.5 d (DOA), e8 =
  10 yr (threshold probe), e9 = 100 yr, e10 = 1000 yr (S6, works),
  e11 = 10000 yr (S7, works), e12 = 100 kyr. Resolvable window: tau
  above ~3x the 6.5 yr substep floor and below the Myr transient.
- S6/S7 were always responsive, not frozen; their -133 MPa lateral
  mean vs -96 undamped is a static bias under investigation, not
  filter lag. Batch 0 numbers stand (grid: S1 156, Bimpl1e20 225,
  Bexpl 211, Cap 48, Rel 0-5, CFL1.0 9, no-feedback 0.1, all MPa).
- Plugin relax-time is SI seconds (no year conversion); Z is 1/s/K.

## Barkla state and next actions

- Kill: any queued/running Rel e4/e5/e6 jobs (incl. e5-CFL0.25, e5-Res7
  derivatives); optionally `rm -rf` the dead `Rel3.156e[456]*`
  result dirs (unregistered, ignored by the pipeline).
- Submit corrected Batch A first (e8/e9/e12 + Cap/Bimpl rescue +
  e11-CFL0.25): pull, `make -C simulation configs`, per-run
  `mpirun -np $NTASKS ./aspect/aspect-release <prm>` with log tee,
  touch `.run` only on success. Loop variable must not be `UID`
  (bash readonly) — use `RUN`.
- Score A with `make sync-barkla` + `make -C python lateral` before B;
  C last with the tau-winner swap (Res7 currently e11).
- If e8 stalls, the floor sits between 10 and 100 yr; if e12 stalls,
  the mechanism is not the substep floor — fallback is the `fixed
  step` reaction solver (template edit + fresh configs).

## Open (not started)

- Manuscript rewrite on the transient-wave narrative (draft/ untouched;
  reference curve is S1 full feedback, not S2 equilibrium).
- Localised/evolving bulk viscosity (needs plugin change + rebuild).
- Z_HI runs (parked until a damper holds the mean at Z_MID).
- `git rm` of orphaned `templates/NH/box/`.

## Gotchas (do not re-learn)

- ruff strips `+` from exponents; no trailing comments on `:=` lines;
  `make format` after edits (ruff, styler, shfmt with repo flags, astyle).
- `plot_mesh` and tiles skip existing outputs — delete generated PNGs
  to force re-render; never run concurrent mesh renders.
- `extract_timeseries`/`summarize` skip missing runs cleanly (exit 0).
- File `dG_driving_0` in the 125-275 km band still carries the old
  flipped plugin reference (cosmetic, needs Barkla rebuild + rerun).
