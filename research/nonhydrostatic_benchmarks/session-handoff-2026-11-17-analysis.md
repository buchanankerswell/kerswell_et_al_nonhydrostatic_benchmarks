# Session handoff — full-suite analysis, Q1–Q4 diagnostics, runtime nominals (2026-11-17, evening)

Branch `agent/initial-benchmark`, pushed through `00140ee`. Tree clean.
Prior handoff: `research/nonhydrostatic_benchmarks/session-handoff-2026-11-17.md` (committed).

## Starting state
All 42 runs finished (20 box + 22 sink; laptop End2e6 = 9 outputs, test End1e6 = 5).
Paper matrix (6 box Res5 + 8 sink Res6) already postprocessed in a prior pass.

## Done this session (committed `00140ee`, pushed)
- **Timeseries for all 42** (`extract_timeseries.py`; 2 background jobs), full
  42-row `pressure-wave-summary.csv` via discover mode (paper + laptop figs).
- **Q1 — nominal vs runtime offset, confirmed + fixed.** Integrating the Mg100
  table densities at g=9.81 puts P_eq at 373.4 km = ASPECT's 373.1 km: the
  runtime is self-consistent; the profile depth scale is the odd one out
  (built with stronger effective gravity). ASPECT evaluates profiles at
  `profile_pos(P_ref)` (`nh-kinetics.cc:154`), so equilibrium is pressure-defined.
  ASPECT's adiabat integrates the *initial* composition, so sink P_ad carries
  the block weight (+0.6 GPa = 400 kg/m3 × 9.81 × 150 km, verified).
  Exact closure: sink DynpOn dG=0 at 373.9 km where dG_ref(−2090 J/mol) +
  dynp·dV(+2064) ≈ 0 with dynp = −645 MPa standing pressure.
- **Nominal alignment implemented.** `NOMINAL_410_{BOX,SINK400,SINK0}` =
  373100/355700/373100 m in `project.mk` (measured dG=0 on B2/S2; Block0 = box
  P_ad by construction). `main.py --nominal-410` per invocation (sink recipe
  split by block), per-row selection in exporter, per-suite R seismic bands.
  Full clean re-mesh + postprocessed + R regenerated. Equilibria read ~0
  (+X0.9 convention); sink DynpOn reads +18–19 km; Cap2e8 +7/+10.
- **Q2**: xi overshoot [−0.028, 1.0003] is ARKODE under/overshoot + clamping —
  benign, no action.
- **Q3 — probe decline, closed.** Box p0 pbar −392 MPa/Myr with Stokes P flat:
  τ=0 freezes pbar per parcel (init analytic lithostatic); ~9 mm/yr background
  creep advects the 39 MPa/km gradient past the fixed probe. Cumulative −92 km
  × 39 MPa/km = −3.6 GPa predicted vs −3.9 observed (7%). Rel run relaxes to P
  instead (τ=0.1 Myr), proving the mechanism. New `plot_probe_history.py`.
- **Q4 — max-rate location.** New `plot_joint_profiles.py` (xi | dG | rate |
  P−P_ad vs depth): box max rate +3–4/Ma ~1 km below xi0.5 forward lobe;
  sink residual rate backward just above front; Cap2e8 shows both lobes.
- **Pipeline fixes**: dynp-disambiguated labels, rate units 1/s→1/Ma (cached
  maxima inherit the tile ×3.154e13 scale), depth-average T panel (sharex→sharey
  + degenerate-limits guard + single invert), R left margin + legend placement.
- **Make 3.81 gotcha**: patterns with two `%` never match (`%_Block400_%`
  silently empty). Used `foreach`+`findstring`. Existing single-`%` filters safe.

## Key science numbers
- Sink DynpOn doubles peak p2p vs equilibrium (1503 vs 777 MPa); Bimpl1e20/
  Bexpl1e19 amplify (~2x); Rel flattens peak (~1000) but leaves high residual;
  Cap2e8 nearly restores equilibrium (peak 787, front −1.0 km).
- Box static (flat ~34 MPa); Rel3.156e12 pathological (405 MPa).
- Scaling: box peak 30.4/33.9/38.0 MPa at Res4/5/6 (grows with res), CFL-flat;
  sink Res5 CFL 0.25 vs 0.5 shifts transient timing (926 vs 802).
- **Bimpl-Res6 box outlier is real**: −182/Ma backward spike + −0.35 GPa dynp
  spike at the front — implicit bulk not resolution-robust.

## Open / next
- Trace-degeneracy: isothermal runs pick representative trace at x=0 (far field).
  Proposed per-suite trace-x override — awaiting user sign-off, not implemented.
- R res-split coloring + Bimpl-Res6 instability need dedicated analysis.
- Manuscript rewrite, Z sweep (520 values), Barkla2 high-res still deferred.
- ruff + Rscript parse clean. `make clean` wipes mesh products (regenerable);
  `figs/benchmarks` survives clean. AGENTS.md edits are local-only (ignored).
- Scratch: /private/tmp/opencode/outlier.png (Bimpl-Res6 joint fig) kept.
