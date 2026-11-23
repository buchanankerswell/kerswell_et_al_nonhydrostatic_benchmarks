# Handoff 2026-11-22: Batch 0 lateral diagnostic + A/B/C sweep registration

Branch `agent/initial-benchmark`. Follows the sink-only handoff (box
removal) from earlier today. Two things landed: the Batch 0 diagnostic
with re-scoring, and the registered A/B/C sweep UIDs.

## Reframing (user-directed, now enforced in the diagnostic)

- Reference is the undamped full-feedback run (S1 DynpOn DampNone), not
  the no-feedback equilibrium (S2). Full feedback is expected to differ
  from equilibrium; that difference is the signal under study.
- Only transient steps score (default steps 00000-00012, covering the
  block crossing). Final states are excluded by design.
- Pass criterion for any damper: cut grid-band power at fixed lateral
  mean, scored against S1.

## Batch 0: `python/benchmarks/extract_lateral_pressure.py`

Samples ambient-corrected driving pressure along nominal 410 (50 km side
margins excluded), per run and step: lateral mean/std/p2p plus FFT band
powers (long >200 km, mid 20-200 km, grid <20 km). Wired as
`make -C python lateral` (new `lateral` target, in `visualize` deps and
CLEAN). Outputs (ignored, regenerable): `simulation/results/lateral-pressure.csv`,
`figs/benchmarks/lateral-pressure-sink.png`. 117 samples for the 9
existing runs, steps 0-12.

Step-6 lateral slice (MPa), the peak window:

| Run | mean | std | grid | p2p |
|---|---|---|---|---|
| S1 None (reference) | -96 | 292 | 156 | 1378 |
| S2 equilibrium | -37 | 31 | 0.1 | 85 |
| Bimpl1e19 | -89 | 321 | 162 | 1531 |
| Bimpl1e20 | -130 | 521 | 225 | 1989 |
| Bexpl1e19 | 3 | 446 | 211 | 1695 |
| Rel (both, frozen) | -133 | 22-26 | 0-5 | 57-91 |
| Cap2e8 | -52 | 100 | 48 | 489 |
| CFL1.0 undamped | -56 | 31 | 9 | 157 |

Three findings. No feedback means no ringing (S2 grid 0.1): the
oscillation is caused by the feedback loop. Doubling the step kills it
(CFL1.0 grid 9 vs 156 at fixed output times, fronts still comparable):
the oscillation is dt-sensitive, i.e. numerical, and separable from the
feedback physics. Frozen relaxed kills everything including the mean
(-133 vs -96); cap halves the mean error (-52) while cutting the grid
band 69%.

## Batches A/B/C: 16 registered UIDs (IDs S9-S24, all in VIS lists)

- A: Rel3.156e4/5/6 at Res6 (responsive taus bracketing advective time);
  rescue `Cap2e8_CFL0.25`, `Bimpl1e19_CFL0.25`, `Rel3.156e5_CFL0.25`
  (small dt is where ringing is worst, so survival there is the test).
- B: Bimpl1e18, Bexpl1e20, Cap1e8, Cap4e8 at Res6.
- C: `None/Cap2e8/Rel3.156e5/Bimpl1e19` at Res7 (~2 cells across the
  3.5 km front) plus `None/Cap2e8` at Res5. The Res7 relaxed run uses
  the middle tau; swap it for the A winner before submitting C.
- New palette entries in python `DAMP_COLORS` and R `damp_pal`
  (hex-for-hex); `damp_key` (python) and the R damp builder append
  `_Res` for off-default resolutions. Dry-run verified all 25 PRM
  expansions (relax-time, bulk/explicit-zeta, max-cap, cfl, refine-global).

## Barkla order

Pull, `make -C simulation configs`, then submit A first
(`..._Rel3.156e[456]_...`, `..._CFL0.25` — 6 runs). Score with
`make sync-barkla` + `make -C python lateral` against the Batch 0 table
before submitting B; submit C last with the tau-winner swap if needed.
`make -C simulation all-models` now covers all 25; submit selectively per
batch with per-PRM `run-aspect` targets. Res7 is ~4x cells per level;
watch queue time (`sinfo -N -R` on MPI_Init clusters) and stale
`NH_Sink_*` configs on hard failures.

Open: localised/evolving bulk needs a plugin change (not registered);
Z_HI stays parked until a damper holds the mean at Z_MID; the manuscript
rewrite stays on the transient-wave narrative with S1 (not S2) as the
reference curve.
