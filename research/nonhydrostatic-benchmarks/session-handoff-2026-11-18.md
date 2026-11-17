# Session handoff — repo housecleaning + UID pipeline cutover (2026-11-18)

Branch `agent/initial-benchmark`, pushed by user. Prior commits for context:
`0aeeea8` stand-alone, `91a27b3` NH pipeline wiring, `dcd6760` analysis tools.

## New commits this session (both signed)
- `9e96512` Generate NH benchmark configs from UIDs in project.mk
- `227e456` Rewire Python/R/bash pipelines to NH suites; houseclean
- (research/*.md session notes rode along in 227e456 — flagged, no objection)

## What changed
- **UIDs** (660-manner, defined project.mk, registered local.mk, asserted):
  `NH_{Box,Sink}_Dynp{0|1}_Damp{None|Bimpl|Bexpl|Rel|Cap..}[_Block{b}]_Z{z}_Res{r}_CFL{c}_End{e}`
  (Res = global-refinement resolution). 42 explicit UIDs, no cartesian sweep.
- **Configs**: flat `simulation/configs/{uid}[.*].prm` from `simulation/params/templates/NH/`
  (shared + box/sink). ABSOLUTE paths throughout (output, includes, plugin, data dir) —
  `make -C bash` leaves CWD ambiguous, so 660-style relative paths cannot work here.
- **Slab sweep fully removed**: SW/NC/TEST UIDs, KN/shared templates, static params,
  `benchmarks/*.prm` (15), laptop/scaling generators, slab misc scripts, geometry.py,
  make-compositions.sh. `pair_titles.py` kept for future montages.
- **Pipelines**: `make models/visualize/manuscript`; `timeseries` + `pressure-waves`
  targets (run lists from project.mk `UIDS_*`/`PLOT_*_RUNS`); R rewritten minimal for
  box/sink (structure panels, Vp profiles with 410 band, tables); export-postprocessed
  emits per-model thermal-kinetic split at 410.
- **Init step corrected** (user note 9): `TRANSITION_Y_OL_WD = 6.408e5` (359.2 km profile
  equilibrium). Measured loaded front ~375 km; mesh/R display band 364.2 km (+5 km corr).
  Old value 5.9e5 was ~50 km off-equilibrium.
- **Z brackets ready**: `Z_660_SLUGGISH_OL=4.44e-04` (matrix), `Z_660_NOMINAL_OL=1.4e+04`,
  `Z_410_SLUGGISH_OL=9.51e-08`, `Z_410_NOMINAL_OL=2.22e+00` (410-repo ends ÷ 3.154e7;
  direction verified: 410 plugin divides rate by time_scale, ours does not).
  520 values unknown (410 repo is ol-wd only) — needed for N=3.
- **Env fixed**: declared env had pypi numpy 1.26.4 vs conda-forge pandas (needs ≥2);
  `pip install -U numpy` → 2.4.6, all imports verified. Use declared env (AGENTS updated).
- **Stale outputs wiped** (user-approved): `simulation/results/*`, `figs/{box,sink}_suite`,
  `figs/benchmarks`, `figs/sink_block`, `simulation/data/*`. Regenerate after reruns.
- **Graceful everywhere**: extract skips missing dirs / warns on missing statistics;
  quantify empty-discovery message; R simulation NULL-guards; export writes stable
  schema; locate argv guard; sweep empty-CSV guard; `make configs` re-run is a no-op;
  run-aspect `.run`-guarded; download/sync force flags kept.

## Verified
- 420 generated configs; include-expansion diff vs retired statics = only intended
  changes (init step, UID spellings, absolute paths, ordering, explicit no-op defaults).
- `make -n` all targets; `py_compile`; `Rscript parse`; exporter fixture incl. `res` column.

## Open / next
- Results dirs are empty (`NH_*` names, old `nh_*` gone) → rerun models (local smoke:
  `ID_STEST`/`ID_SNOBLOCK`), then regenerate figures; Barkla2 submission = 42 configs.
- Deferred per user: R tailoring for manuscript figs, manuscript rewrite (still 660-era),
  montage helpers, Z sweep execution, nodynp equilibrium runs.
- Watch: `git add -A` also stages research/ notes now that the dir is tracked;
  conda env is hand-fixed (not reproducible from environment.yaml — consider pinning numpy).

## Gotchas hit
- zsh does not word-split `$VAR` (inline CLI args literally in background jobs).
- Stale `.git/index.lock` blocked git; removed the single lock file.
- `git commit --amend` after `git add -A` folded two planned commits into one;
  recovered via `git reset --soft` + resplit (safe: nothing pushed yet at the time).
- `make -C` recipes run with CWD=bash ⇒ relative prm paths unreliable ⇒ absolute.
