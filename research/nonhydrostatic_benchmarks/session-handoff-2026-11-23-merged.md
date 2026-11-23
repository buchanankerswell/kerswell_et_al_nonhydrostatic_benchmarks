# Handoff 2026-11-23 (post-merge): sink-only suite, scored Batch A, print-spec figures

Branches merged to main. This supersedes `session-handoff-2026-11-22-consolidated.md`
(which described the mid-session state). Next work starts from a fresh `agent/*` branch.

## Where things stand

- **Suite:** sink-only, 25 registered UIDs (S1-S24 + controls). Box suite fully removed
  (code, figs, results references). Postprocess + visualize collapsed to a single
  `make postprocess` (Python + R); `make build` = environments, download, postprocess,
  manuscript. Test knobs: `MESH_TIMESTEPS` render subset (postprocess always full),
  `FIG_DPI` (100 draft / 330 manuscript), per-model CFL.
- **Physics baseline:** ambient reference (block load subtracted); model time in years,
  kinetics SI. Resolvable relaxed-tau window is ~[30 yr, 100 kyr].
- **Runs:** 20 complete, 5 crashed (Bexpl1e20, Bimpl1e19 CFL0.25/Res7, None CFL0.25/Res7).
  All die in the first ~400 kyr with dt collapse: negative density x c_P, or xi
  overshoot at Res7. Finer mesh/smaller step fails where coarser passes (numerical
  mode, confirmed by CFL1.0 completing clean at grid 9 MPa). None CFL1.0 log-tail
  MPI error is a stale relaunch artifact; the run finished to 5.0 Myr.
- **Batch A scores** (transient steps 0-12 lateral diagnostic, MPa, vs S1 grid 157):
  relaxed e9-e12 grid 0.3-7 (full suppression incl. Res7/CFL0.25); e8 rings (133).
  Cap non-monotonic and resolution-fragile (Res5 4.3 / Res6 48 / Res7 139).
  Bulk does nothing (Bimpl 165-225, worse than undamped; Bexpl1e20 crashes).
- **Figures:** fixed suite-wide mesh clims (measured 441-file scan); print spec
  (6.5 in rows, 3.5 in talls, 14 pt ggplot2-parity type, single outside legends);
  double-scaling bug fixed (cache stores display units; `rate410_per_Ma` /
  `vmax410_cm_per_yr` renamed); bulk-damping/mean-flow/point-pressure figures removed;
  new `lateral-profiles-sink.png`; R structure redesigned (values vs numeric res).
  Lateral summary lives at 5 in (25-entry legend cannot fit single column).
- **Data:** PYR adiabat tables tracked (copied from identical-PYR.dat 660-kinetics
  build); explicit make targets; `numba>=0.60` pinned (old numba refused NumPy 2.x).
  Full `make clean && make postprocess` verified end to end.

## Open questions (for the manuscript iteration)

1. Relaxed mean ~-100 MPa vs S1 -27 MPa: linear filter preserves the mean, so this
   is a static offset, not lag. True physical load or relaxed-field bias? Needs a
   dedicated check. Visible in final state too (depth-profiles P-hat panel).
2. Cap2e8 Res7 final rate 1.17e15/Ma (~10x Res6 and ~10x Rel Res7): unresolved sharp
   front or unsettled run?
3. R structure x-labels readable; the `UID_RE` pattern still excludes `_CFL` runs
   from postprocessed.csv by design (paper set = no-CFL suffix).

## Likely next moves

- Full mesh re-render under fixed clims (only 2 models x 3 steps done so far).
- Manuscript rewrite on the transient-wave narrative (S1 undamped feedback as
  reference, not S2 equilibrium); draft/ still holds stale 660 content.
- Localised/evolving bulk viscosity (plugin change + rebuild); Z_HI runs (parked
  until a damper holds the mean at Z_MID).
- Rerun `make postprocess` after any new Barkla sync; crashed-run UIDs need
  resubmit decisions (Batch B/C never submitted).
