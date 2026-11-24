# Benchmark design 2026-11-24: spurious pressure feedback, frozen suite, S1 baseline

Branch `agent/benchmark-design-pipeline` (from `agent/session-handoff-2026-11-23`).
Supersedes the 2026-11-23 merged handoff for design decisions; physics notes in
the 11-19 ambient handoff and Batch 0 scores in the 11-22 notes still stand.

I am using the research-methodology, hypothesis-testing, and
quantitative-analysis skills to frame this.

## Classification

Comparative + causal-mechanism question. The phenomenon is a numerical
oscillation driven by a known feedback loop (Gassmoller et al. 2020,
https://doi.org/10.1093/gji/ggaa078): compressible ASPECT applies
instantaneous volume/density changes in the continuity equation, forcing
pressure and velocity in the Stokes solve to change instantaneously, while
kinetic phase-change rates are driven by dynamic pressure. Zero bulk
viscosity (outside solid-melt exceptions; see `/Users/Shared/workspace/aspect`
source) means nothing resists the volumetric rate, so the loop
pressure -> rate -> density -> pressure rings instead of relaxing.

## Hypotheses

- **H0:** Dynamic-pressure coupling does not change the pressure history
  beyond equilibrium (S1 transient equals S2 up to a static offset, no
  grid-band energy, no dt/mesh dependence).
- **H1:** Full feedback rings numerically: S1 carries transient grid-band
  (<20 km) energy far above S2 that shrinks with larger dt (CFL1.0) and
  shifts with refinement, separable from the physical lateral mean.
- **Mechanism:** Zero-bulk-viscosity instantaneous compaction + kinetic
  rate driven by dynamic pressure = undamped discrete feedback at the
  front width (~3.5 km, ~0.9 dx at Res6).

Rejected already by Batch 0: H0 is out (S1 grid 156 MPa vs S2 0.1 MPa at
step 6; CFL1.0 grid 9 MPa at fixed fronts). The live question is which
damper kills the grid band while holding the lateral mean (physical load).

## Variable matrix

| Variable | Role | Operational definition |
|---|---|---|
| Damping treatment | IV | None / Bimpl / Bexpl / Rel(tau) / Cap(clip), from UID |
| Mesh (Res5/6/7), CFL (0.25/0.5/1.0) | Moderator | Convergence: grid power and p2p vs dx, dt |
| Grid-band power, p2p, std (transient steps 0-12) | DV (stability) | `lateral-pressure.csv` FFT bands; `pressure-history-summary.csv` largest_range |
| Lateral mean pressure | DV (physics) | Must hold at S1 value; a damper that zeroes grid but drags the mean fails |
| Final displacement/width/rate (step 20) | DV (structure) | `postprocessed.csv` disp410/width410/rate410, thermal-kinetic split |
| Z (kinetic prefactor) | Control | Frozen at Z_MID (4.44e-04); Z_LO/Z_HI parked |
| End time, default CFL, output cadence | Control | Suite constants, absent from UIDs |

## Frozen suite (25 UIDs, no new runs)

Core 9 (S1-S8 + CFL1.0 twin): S1 undamped control, S2 no-feedback physics
reference, Bimpl1e19/1e20, Bexpl1e19, Rel e10/e11, Cap2e8, undamped CFL1.0.
Batch A (S9-S14): resolvable taus e8/e9/e12 + damped CFL0.25 rescue twins
(Cap, Bimpl1e19, Rel e11); undamped CFL0.25 blowup is the stability test.
Batch B (S15-S18): Bimpl1e18, Bexpl1e20, Cap1e8/4e8 at Res6.
Batch C (S19-S24): Res7 x {None, Cap2e8, Rel e11, Bimpl1e19} + Res5 x
{None, Cap2e8}. Res7 puts ~2 cells across the front.

## Falsification (pre-registered, Batch 0 thresholds)

- Relaxed tau rejected if peak-grid reduction under 20% vs S1 or final
  displacement drift over 10% across the tau sweep.
- Bulk rejected if three matched pairs show no final-state gain over global
  damping at equal peak reduction (localised/evolving bulk needs a plugin
  change; not registered).
- Cap kept as equilibrium placeholder unless a threshold preserves the
  transient waveform (currently non-monotonic across Res5/6/7: 4.3/48/139
  MPa grid, so fragile).
- Pass criterion for any damper: cut transient grid-band power at fixed
  lateral mean vs S1. Final states are excluded from stability scoring by
  design.

## Validity and limits

- Threat: relaxed mean offset (~-100 MPa vs S1 -27 MPa at step 6) is a
  static bias under investigation, not filter lag; do not claim mean
  preservation until the dedicated check lands.
- Threat: 5 crashed UIDs (Bexpl1e20, Bimpl1e19 CFL0.25/Res7, None
  CFL0.25/Res7) die in the first ~400 kyr; resubmit decisions pending, do
  not silently drop them from convergence claims.
- Limit: single phase change near 410 km, isothermal sink, one Z. 520/660
  and Z-rate scaling are out of scope until a damper holds the mean.

## Pipeline (idempotent, fail-safe)

- Every benchmark script exits 0 on missing inputs (skip + warn):
  `extract_timeseries`, `summarize_pressure_history`,
  `extract_lateral_pressure`, `export-postprocessed` (skips incomplete runs
  without final output, skips non-UID and `_CFL` models in the final-state
  table by design).
- Make targets are thin wrappers: `visualize` (canonical; `postprocess`
  kept as alias) = adiabat + meshes + postprocessed table + timeseries +
  setup sketch + `benchmarks` group (pressure-history-summary,
  lateral-oscillation, mesh-step-sensitivity, depth-window-figures).
- R `visualize` reads the Python CSVs; arg order stays `(util_dir first)`.
- Regeneration: `make clean && make visualize` reproduces all figures from
  synced results; `MESH_TIMESTEPS` subsets mesh renders only.

## Figures (four required families)

1. Spurious oscillation existence: pressure-history S1 vs S2 + lateral
   profiles at the peak step.
2. Diminishment magnitude: lateral-oscillation summary (mean/std/grid vs
   step) + reduction_vs_control / rel_err_vs_nofeedback table.
3. Timescales: reaction rate vs viscous/diffusive relaxation (rate410,
   flow diminishment, tau window [30 yr, 100 kyr]).
4. Convergence: mesh-step-sensitivity (range vs Res and CFL) + depth-window
   compositions at fixed clims.

Central for the manuscript: lateral-oscillation summary + pressure-history
+ mesh-step-sensitivity. Still missing: rerun under fixed clims for all
models, the relaxed-mean bias check, and crashed-run resubmit decisions.
