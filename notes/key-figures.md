# Key figures

`draft/manuscript.md` names four figure families: oscillation existence,
diminishment magnitude, timescales, and mesh/step convergence. Central figures
go in the main text; the rest support the supplementary information.

## Existence

- `figs/benchmarks/pressure-history-sink.png` — S1 vs S2 dynamic-pressure
  range over 5 Ma. S1 peaks at 2168 MPa, S2 at 386 MPa.
- `figs/benchmarks/lateral-pressure-profile-sink.png` — lateral profiles at
  the peak step; S1 swings -707 to +594 MPa.

## Diminishment magnitude

- `figs/benchmarks/lateral-oscillation-summary-sink.png` — mean, standard
  deviation, and grid-band power vs step for all 25 runs. This is the damper
  ranking.
- `figs/benchmarks/range-sensitivity-sink.png` — largest range vs mesh level
  and CFL; shows cap drift and undamped divergence.

## Timescales

- `figs/benchmarks/timescales-sink.png` — reaction rate history plus a
  log-time ladder of reaction, relaxation, oscillation, cadence, and tau.

## Convergence and stability

- `figs/benchmarks/range-sensitivity-sink.png` — right panel: range vs CFL.
  Undamped Res7 and CFL0.25 crash; relaxed Res7 completes.
- `figs/benchmarks/displacement-error-sink.png` — 410 position error vs the
  no-feedback reference across mesh and step.

## Trade-off and seismic structure

- `figs/benchmarks/relaxed-mean-check-sink.png` — relaxed runs suppress
  oscillation but sit ~100 MPa below the reference mean.
- `figs/seismic/seismic-sink.png` — synthetic seismic profiles across the 410
  front.

Supporting figures: `depth-profiles-sink.png` (final states), the
`depth-window-*.png` compositions and `figs/sink_suite/simulation/meshes/`
panels (qualitative fields at fixed limits), `figs/structure/structure-sink.png`
(displacement, width, and rate vs resolution), `figs/setup/sink-domain.png`, and
`figs/adiabat/*.png`.

Two figures are new this session and should join the main-text set:
`timescales-sink.png` fills the timescale family, which had no dedicated panel,
and `relaxed-mean-check-sink.png` makes the damping compromise explicit. The
relative-error claim rests on `displacement-error-sink.png` and the new
`rel_err_vs_reference` column in `pressure-history-summary.csv`; both need the
no-feedback reference runs listed in `notes/key-results.md` before the mesh
sweep is complete.
