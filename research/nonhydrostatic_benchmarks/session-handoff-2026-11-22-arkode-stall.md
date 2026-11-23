# Handoff 2026-11-22: ARKODE stall kills sub-year taus, years-scale correction

Branch `agent/initial-benchmark`. Supersedes the tau window in
`session-handoff-2026-11-22-batch0-sweeps.md`; Batch 0 lateral numbers
stand (empirical, unit-independent).

## Symptom

Batch A `Rel3.156e4/5/6` (plus the `e5` CFL0.25 and Res7 derivatives)
never advance past timestep 1. Logs show ~173k
`[ARKODE ERROR] arkEvolve ... mxstep steps taken before reaching tout`
at `t = 2.0757e11`, i.e. the reaction ODE burns all 500 substeps without
covering the step. Old runs show zero ARKODE lines and `4 substep(s)`.

## Root cause (two parts, both verified in source)

`simulation/params/templates/NH/shared/globals.prm` sets
`Use years instead of seconds = true`, and ASPECT then converts all
time inputs by `year_in_seconds`
(`source/simulator/parameters.cc`). So the model runs 5e6 YEARS, not
5e6 seconds: dt ~= 6560 yr (~2.07e11 s, matching the ARKODE `t`),
outputs every 250 kyr, transient steps 0-12 span ~3 Myr, velocities are
~0.1-0.3 m/yr (the `m/s` labels on velocities are wrong; Batch 0 MPa
and step indices are unaffected).

The reaction solve (`compute_reactions`, operator splitting, ARKODE;
`source/simulator/helper_functions.cc`) integrates over the full dt
with `minimum_step_size = 1e-6 x dt` ~= 6.5 yr and no exposed mxstep
knob. The `relaxed_pressure` ODE `dp/dt = (P - p)/tau` equilibrates in
~7x tau. Sub-year taus (e4 = 8.8 hr, e5 = 3.65 d, e6 = 36.5 d) finish
their transient ~1000x below the minimum substep: unresolvable,
infinite rejections, mxstep death. Threshold is quantitative: e6
(0.7 yr transient vs 6.5 yr floor) dies, e10 (7000 yr transient) passes
in 4 substeps.

## Correction to the previous analysis

The "frozen tau" claim compared seconds to seconds and is withdrawn.
In years: e10 = 1000 yr, e11 = 10000 yr, dt ~= 6560 yr. S6/S7 were
already responsive filters, not frozen fields — S6/S7 ARE the current
best evidence relaxed filtering works (grid 5/0.1 MPa vs 156 undamped).
The resolvable window is tau in [~30 yr, ~100 kyr] = [1e9 s, 3e12 s]:
above ~3x the 6.5 yr substep floor, below the Myr transient. The
identical -133 MPa means of S6/S7 point at a static bias (init offset),
not filter lag, and stay open.

## Swap (registered, IDs S9-S11/S14/S21, palettes updated)

- S9/S10/S11: Rel3.156e8 (10 yr, threshold probe), Rel3.156e9
  (100 yr), Rel3.156e12 (100 kyr). Brackets the proven S6/S7 pair.
- S14: Rel3.156e11_CFL0.25 (proven 10 kyr tau for the rescue).
- S21: Rel3.156e11_Res7 (proven tau for the fine mesh).
- B/C otherwise unchanged. Dry-run verified all 25 PRM expansions.

Prediction: e8/e9/e12 advance (e8 marginally); a stall in e8 puts the
floor between 10 and 100 yr. If e12 stalls, the mechanism is not the
substep floor and the fixed-step reaction solver is the fallback
(`Reaction solver type = fixed step` + `Reaction time steps per
advection step`, template edit + fresh configs).

## Barkla actions

`scancel` the e4/e5/e6 jobs and any e5-CFL0.25 / e5-Res7 jobs; they can
never advance and burn allocation grinding substeps. Pull, regenerate
configs, submit corrected A. Stale `Rel3.156e[456]*` result dirs are
unregistered and ignored by the pipeline; remove them on Barkla to
avoid confusion with the corrected UIDs. Then score with
`make sync-barkla` + `make -C python lateral` as before.
