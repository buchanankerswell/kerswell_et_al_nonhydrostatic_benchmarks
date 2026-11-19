# Session handoff — 2026-11-19: batches 2–4, sink nominal, failures, sync rewrite

Branch `agent/initial-benchmark`. Commits since `2803330` (audit): `078ba10`
(partial-batch pipeline fixes), `4db3595` (sink nominal 355700→362700),
plus user-committed sync rewrite (two-rsync fetch, drop UID-list/FORCE_SYNC,
extract_timeseries skip-empty). Prior handoff:
`session-handoff-2026-11-18-audit.md`.

## Data state (118 models with solutions: 107 full 9-output, 11 partial)
- Sink paper set S1–S8 complete at Z_MID Res6 (Rel S6/S7 landed in batch 3);
  Res7 rungs starting (1–2 outputs), Z_HI Res6 still filling (1–5 outputs).
- Box stuck at 27: paper set B1/B5 only. ID_B2 (box no-feedback twin) and
  B3/B4/B6 never ran — 50 box jobs died at MPI_Init (see below).
- 50 failed runs have `.log` only, no solutions. Resubmit retries exactly the
  missing set (no `.run` files written on failure).

## Barkla failures — triaged, infrastructure not physics
- All 50: `ompi_mpi_instance_init failed → "Unreachable" (-12)`, dead in 3–4 s
  at MPI_Init before ASPECT starts. Zero correlation with suite/damp/Z/Res.
- Node/time clustered: node036 (~28, Wed 14:00–14:23), node031 (~12, Wed
  14:50–15:05), node029 (3, Wed 13:58), node027 (5 sink Res7 Z_HI, Thu 03:10).
  node018/node020 ran fine in overlapping windows → sick nodes/transient
  fabric, not modules or configs.
- Remedy on Barkla2: `sinfo -N -R`, then `make -C simulation all-models`.
  Offered: add `EXCLUDE` var to sbatch line if a node keeps poisoning jobs.

## Sink nominal re-derived (done, committed, pushed)
- ID_S2 dG=0 crossing = 362.7 km, static across outputs → `NOMINAL_410_SINK400`
  355700→362700 (`project.mk` + R default + comments; box stays stale to 373.1).
- Verification: twin displacement re-centered +8.3→+1.3 km; Z_MID Res6 paper
  set reads undamped/Bimpl/Bexpl/Rel ≈ +20.2–20.3 km, Cap +8.3 km (≈12 km
  dynamic-pressure signal, capping removes two-thirds). Required killing the
  in-flight stale-nominal mesh (safe: caches save per chunk) + forced sink
  re-mesh; full chain re-ran green.

## Pipeline fixes this session (all committed)
- `sync-barkla2.sh`: sidecar fetch (`statistics`, `point_values.txt`, `*.log`)
  added, then rewritten to two rsyncs (markers + whole tree, one filter list);
  restart/checkpoint dirs excluded; UID-list arg and `FORCE_SYNC` dropped;
  "sidecar" jargon → "run metadata". Empty local model dirs no longer created.
- Benchmark scripts: `RESULTS` anchored to `PROJECT_ROOT` (broke under
  `make -C python`); `export-postprocessed` + `plot_bimpl_resolution` skip
  empty sink summaries instead of `EmptyDataError`.
- `R/seismic.R`: source utils before `parse_logical` (ordering bug).
- `R/utils/simulation.R`: Z matched in numeric space — `as.character()` on
  numerics formats 4.44e-04/1.4e+04 as "0.000444"/"14000", sending 10/20 rows
  to NA grey (only frozen matched by luck).
- `extract_timeseries.py`: no longer writes header-only CSVs for models
  without outputs; 50 placeholders deleted (Python pass; bare `rm` glob
  failed with ENAMETOOLONG in this shell).

## Analysis findings (all with stale→current nominals as noted)
- Sink Z_MID Res6 waves peak ~1.5 Myr (undamped ~1830 MPa p2p), decay by ~3 Myr
  as block bottoms. Damping rank: Cap (~780) ≈ no-feedback twin (~700) ≫ Rel
  flat ~950 (no decay — persistent relaxed-pressure offset) > undamped >
  Bimpl1e19 > Bexpl (~2230) > Bimpl1e20 (~2450).
- NaN dropout = validity gates working, two regimes confirmed against cached
  traces: (a) sink frozen-Z fronts advect down + broaden past the ±80–100 km
  window (347–359 km at t=0 → 357–884 km at t=20, single crossing throughout);
  (b) box Z_HI Res7 fronts collapse to one depth level with −0.07 xi overshoot,
  rejected by monotonicity/corruption gate (stiffness corner).
- `damp` shows NaN for DampNone rows under pandas only (`read_csv` maps literal
  "None" to missing); CSV + R figures correct.

## Next
1. Resubmit 50 on Barkla2; periodic `make sync-barkla` (new 2-rsync script).
2. When ID_B2 lands: re-derive box nominal, forced box re-mesh.
3. R res/z-split figures; rate-panel log scale; seismic legend/"410" label
   collision cleanup; manuscript rewrite (still 660-era content).
