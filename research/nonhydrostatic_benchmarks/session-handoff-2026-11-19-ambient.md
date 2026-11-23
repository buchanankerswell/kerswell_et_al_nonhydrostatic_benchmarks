# Session handoff — 2026-11-19 night: ambient reference, reprune, style, Barkla launch

Branch `agent/initial-benchmark`. Prior handoff:
`session-handoff-2026-11-19-reprune.md`. This file consolidates everything
since, for session compaction.

## Ambient reference (committed 82f7f55, locally tested)

ASPECT builds its 1D adiabat down a column through the initial block, baking
~589 MPa of block weight into `P_ref` (measured as uniform -0.5 GPa far-field
offset at a side column). The plugin now subtracts that static load
(`AMBIENT_REF`, `BLOCK_Y_TOP/BOT`, `project.mk`; no-op for box).
Files: `simulation/plugins/nh-kinetics.{h,cc}`,
`simulation/params/templates/NH/shared/material.prm`, `project.mk` macro.

Four local Res4 sink runs (twin/undamped/cap/bimpl): all fronts 382.8 km,
far-field driving pressure -34 MPa with localized +283 MPa block footprint,
wave intact at ~1085 MPa peak. Cap and Bimpl match undamped exactly.

Reinterpretation: with feedback on, `P_ref` cancels out of the dG zero, so
undamped fronts always found the true pressure equilibrium. The old On-Off
static displacement (+15.6 Res4 / +20 Res6) was reference artifact, as was
the old "cap removes two-thirds" (it clamped the -600 bias to -200). Real
signals: transient wave, front excursion during passage, nonlinear-damping
distortion. Box suite unaffected (clean reference throughout).
Display: ASPECT's own `nonadiabatic_pressure` field still uses the old
reference; `extract_timeseries` writes ambient columns, band figure shows
the ambient driver. `NOMINAL_410_SINK400` stale (~383 km expected at Res6).

## Ground-zero reprune (committed 711926a)

Wiped local results/configs/figs/generated data. Sweep is 18 runs: paper 6
box Res5 + 8 sink Res6 (Z_MID only) + 4 timestep-scaling runs (undamped,
half/double CFL per suite). Per-model CFL via `PARAM_cfl_*` + optional `_CFL`
UID suffix. `TIMESTEPS` covers all 21 run outputs (000-020) so time-history
figures draw full-resolution curves.
Z labels renamed sluggish/intermediate/quasi-equilibrium. New `make scaling`
(`plot_mesh_step_sensitivity.py`: range vs Res and vs CFL, boundary offset vs control).
Download threshold 18. `AGENTS.md` rewritten (local-only: the file is
gitignored, does not travel on pull/push).

## Style audits (committed 39fe8cf, 0ed5341)

Comments cut roughly in half across `project.mk`, plugin, Python/R.
Jargon out: control runs (not twins), wave run with no damping, all damping
types, center/meters/artifacts/included. Units restored on every plugin
member and parameter entry (ASPECT convention). Plugin rebuild verified.
`R/utils/simulation.R` palettes use the new level names.

## Open oddity

A 9-sparse to 11-even `TIMESTEPS` change rode into 82f7f55 without an
authoring edit. User chose minimal-5 instead, superseding it. Watch for
stray working-tree edits; verify `git diff` before each commit.

## State and next

HEAD is 0ed5341, pushed. Barkla side cleared by user; 18 jobs submitted and
running. When all show `.run` markers: sync from here, re-derive the sink
nominal from new S2, forced re-mesh, full chain, `make scaling`.
If a CFL job dies in seconds, read its log head before any bulk resubmit.
