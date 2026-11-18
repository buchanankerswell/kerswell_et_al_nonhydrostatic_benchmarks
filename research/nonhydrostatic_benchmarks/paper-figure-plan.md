# Paper figure + pipeline plan (2026-11-17; decisions locked)

> UID cutover (2026-11-18, uncommitted work on `agent/initial-benchmark`,
> updated 2026-11-18: Res4 + End2e6/End1e6 removed, Res7 paper twins added):
> static `simulation/benchmarks/nh_*.prm` are GONE. All benchmarks are now
> generated configs (`simulation/configs/{uid}.prm` from
> `simulation/params/templates/NH/`) with UIDs
> `NH_{Box,Sink}_Dynp{d}_Damp{kind+val}[_Block{b}]_Z{z}_Res{r}_CFL{c}_End{e}`
> registered in `simulation/local.mk` (40 total: 20 box, 20 sink; paper sets
> `ID_B1..B6`/`ID_S1..S8` + Res7 twins `ID_B7..B12`/`ID_S9..S16` + scaling).
> `make benchmarks`/`visualize-benchmarks` and the old derived-prm generators
> are deleted; use `make models` / `make visualize`.
> `quantify_pressure_waves.py` is UID-native (per-UID control/nodynp twins).
> Fixed-x representative traces per suite (`TRACE_X_*`); runtime-adiabat
> nominals (`NOMINAL_410_*`). R structure panels color by Res.

## Scientific questions
1. How does nonadiabatic (dynamic) pressure affect phase transformations and
   seismic structures (410, 520, 660)?
2. What is the magnitude of these effects?
3. How to implement the feedbacks in compressible geodynamic simulations?

## Mechanism under test
Instantaneous volume/density change in the continuity equation feeds the
Stokes solve, producing pressure spikes that re-enter the Gibbs energy and
drive further transformation: a numerical feedback loop. Gassmoller et al.
2020 (GJI 221(2), ggaa078) addressed the mass-conservation side with the
projected-density formulation (already used here); the remaining loop is
kinetic. Motivation: real transformations are not instantaneous and flowing
mantle is not under hydrostatic stress -> move beyond equilibrium kinetics
and TALA/ALA/Boussinesq.

## Frozen benchmark matrix (410, single ol-wd reaction; static prms)

| suite | base cases | solutions | controls |
|---|---|---|---|
| box (300x1000 km, inflow, ref5, 10 Myr) | nodynp (NEW: corrections OFF = equilibrium ground truth), undamped (spurious demonstrator) | implicit_bulk (Formulation zeta=1e21), explicit_bulk (plugin zeta=1e20), relaxed (tau=100 kyr), capped (10 MPa) | — |
| sink (1000x1000 closed, 150 km block drho+400, ref6, 5 Myr) | nodynp (NEW), undamped | implicit_bulk (zeta=1e19 matched), implicit_bulk_hi (1e20 over-damped), explicit_bulk (1e19), relaxed 1 kyr / 10 kyr, capped (200 MPa) | test (ref4 smoke), test_noblock (no-block/no-wave proof) |

Solution parameters are re-anchored: zeta ~ K*tau_rxn ~ 1e19, tau_rel ~ kyr,
cap ~ 200 MPa (sink) / 10 MPa (box).

## Scaling matrix (derived prms in simulation/benchmarks/scaling/, gitignored)
- Box sweep: {undamped, implicit_bulk, relaxed_pressure, capped_pressure,
  nodynp} x ref {4,5,6} x CFL {0.7} + undamped ref5 x CFL {0.35, 1.4}
  (21 prms, generated).
- Sink check: {undamped, implicit_bulk} x ref {5} x CFL {0.5, 0.25}
  (4 prms, generated). Same end time + viz cadence as sources.
- Regenerate: python/benchmarks/make_scaling_prms.py (NEW).

## Figure list v0 (maps to the 4 requirements)
- F1 spurious issue (qual): crossing snapshots pressure + xi, undamped vs
  nodynp, block at 410 (outputs 2-4). Exists via shared pipeline.
- F2 spurious issue (quant): P2P(t) + min/max(t) with nodynp reference curve
  (grey dashed, NEW in quantify_pressure_waves.py) + front-displacement
  overlay from structure-summary.
- F3 diminishment (quant): peak-P2P reduction vs undamped + signed peak error
  vs nodynp (rel_err_vs_nodynp, NEW column; empty until nodynp runs exist).
- F4 timescales (quant): tau markers on P2P(t) — tau_rxn from kinetics vs
  imposed tau_rel (1/10/100 kyr) vs viscous relaxation. NOT YET BUILT.
- F5 scaling (quant): peak P2P + front error vs h and vs dt/CFL. Runs NOT
  YET DONE (prms generated); plot mode NOT YET BUILT.
- F6 Earth-like placeholder (Sec-4 style): slab displacement/width/seismic
  profiles. Pipeline exists for slab suites; NH N=3 suite DEFERRED (Step 2).
- F7 setup schematic: box/sink geometry + feedback-loop diagram. NOT YET BUILT.

## Pipeline upgrades (ordered)
1. DONE: nodynp prms; run lists include nodynp; error column + ref curve.
2. Timeseries as make target; fix NaN time_yr (statistics viz-time mapping
   fails on full runs) or standardize x-axis on output index. TODO.
3. Front tracking across selected timesteps into structure-summary (currently
   make uses -1 = last only; manual batches overwrite CSVs). TODO.
4. F4 timescale markers: compute tau_rxn from kinetic params, annotate. TODO.
5. F5 scaling mode in quantify (h/dt convergence plots incl. scaling/ runs). TODO.
6. Paper-figure script with fixed F1..F7 names under figs/, separate from
   exploratory plots. TODO.

## Barkla2 submission list (not yet run)
Box: nodynp (new) + 17 scaling prms. Sink: nodynp (new) + 4 scaling prms +
  6 missing full-res damped runs (implicit/explicit/relaxed x2/capped/hi killed
  earlier). Laptop stays local-only for iteration.

## Deferred
N=3 (520/660) MTZ suite; KN template ReactionChain conversion; R wiring for NH.
