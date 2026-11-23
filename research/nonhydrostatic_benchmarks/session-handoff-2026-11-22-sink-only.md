# Handoff 2026-11-22: box removed, sink-only pipeline, Barkla sweep plan

Branch `agent/initial-benchmark`. Supersedes
`session-handoff-2026-11-21-nominals-units.md` for pipeline scope;
physics notes in the 11-19 ambient handoff still stand.

## Box removal

Sink-only now. Nine registered runs (all `NH_Sink_*_Block400_Z4.44e-04_Res6`
plus the CFL1.0 twin). Box builds, configs, figures, and table rows are gone
from the pipeline; existing box outputs on disk are ignored build products,
not inputs.

Touched: `project.mk` (can-edit sections only), `simulation/local.mk`,
`simulation/Makefile`, `python/Makefile`, `R/Makefile`, `Makefile`,
`bash/Makefile`, mesh `main.py`/`pipeline.py`/`config.py`/
`export-postprocessed.py`, `transitions.py`, `setup/domains.py`,
`benchmarks/` (`common`, `summarize_pressure_history`,
`plot_depth_profiles`, `plot_bulk_damping_check`,
`plot_mesh_step_sensitivity`, `compute_window_clims`, `plot_depth_window`),
`R/simulation.R`, `R/seismic.R`, `R/utils/simulation.R`,
`R/utils/seismic.R`, `R/utils/tables.R`.

Intentionally left in place:

- `project.mk` Macros section (`MAKE_UID_BOX`, `REGISTER_NH_BOX`,
  `GENERATE_NH_PRM` box branches): marked `(no edits)`, now dead code.
  Never triggers since no box UIDs are registered.
- `simulation/data/depth-datum.tsv` box column and
  `transitions.load_depth_datum` 3-column reader: versioned input format,
  unchanged; only the sink column is read.
- `python/benchmarks/sample_depth_datum.py`: standalone reproducer for the
  versioned datum, not wired into any Makefile target.
- `simulation/params/templates/NH/box/`: orphaned, unreferenced. Delete
  with an explicit `git rm` once this handoff is accepted.
- `simulation/results/NH_Box_*/`, `figs/box_suite/`, box PNGs/CSVs: ignored
  generated products. They regenerate sink-only on the next
  `make visualize`; no manual deletion needed.

Verification: `make -n` for `configs-sink-suite`, `meshes-sink-suite`,
`R simulation/seismic/visualize` all sink-only (9 UIDs, correct args);
`ruff format`/`ruff check` clean; `compileall` clean; all R files parse;
`make format` applied (styler touched 2 files, whitespace only).
Full `visualize` not rerun locally (heavy); Barkla sync + visualize is the
regeneration path.

Figure renames: `structure-box-sink.png` to `structure-sink.png`,
`seismic-box-sink.png` to `seismic-sink.png`. Box-only figures
(`pressure-history-box.png`, `depth-profiles-box.png`,
`mean-flow-speed-box.png`, `point-pressure-box.png`,
`bulk-damping-check-box.png`, `box-domain.png`) no longer produced.
`mesh-sensitivity`, `step-sensitivity`, `step-boundary-error` are now
single sink panels.

## Why these sweeps

At Z_MID the nine sink runs agree on finals (fronts within 2.3%) but
disagree on the transient: undamped peak-to-peak 2196 MPa; Bimpl1e20 +19%,
Bexpl +11%, Bimpl1e19 +3%; Cap -58%; relaxed -53% with a -78 MPa mean bias.
The relaxed taus (3.156e10/3.156e11 s) exceed the 5e6 s run by 6000x or more,
so they test a frozen field, not a filter. The responsive window is
1e4-1e6 s. Bulk at 1e20 amplifies the peak; 1e19 is near-neutral. Lateral
slices at nominal 410 show the same ordering (Bimpl1e20 p2p +44% vs
undamped, cap -65%, relaxed -93%), decaying to ~5 MPa by step 20 in every
run, which makes the transient the scoring window. No mesh scaling exists
(single Res6), and the CFL0.25 blowup was only ever tried undamped.

## Proposed Barkla batches (16 runs, gated A -> B -> C)

Z stays at Z_MID (4.44e-04) throughout; damping selection first, Z_HI later.
All UIDs follow the existing `NH_Sink_DynpOn_Damp<kind><val>_Block400_Z4.44e-04_Res<res>[_CFL<c>]`
shape; register in `simulation/local.mk` with `ID_*` + `VIS_IDS_SINK_SUITE`
entries in `project.mk`.

Batch 0 (local, no Barkla): implement the lateral diagnostic
(`extract_lateral_pressure.py`: fixed-depth slice at `NOMINAL_410_SINK400`,
ambient correction, 50 km margin exclusion; per step mean/std/p2p plus
long/mid/grid band powers) and re-score the existing 9 runs. Gates
everything below: the winner must cut grid-band power while holding the
lateral mean.

Batch A, stability + tau (6 runs, highest priority):

- `DampRel3.156e4`, `DampRel3.156e5`, `DampRel3.156e6`, Res6, default CFL.
  Brackets advective time (~3e5 s); smallest should recover undamped, middle
  should halve the peak at fixed mean, largest trends toward current frozen
  behaviour.
- Rescue: `DampCap2e8_CFL0.25`, `DampBimpl1e19_CFL0.25`,
  `DampRel3.156e5_CFL0.25`, Res6. Survival plus reduced grid power is the
  direct stabilisation test. The old unregistered `...CFL0.25` directory
  stays untouched; these are new registered UIDs.

Batch B, bulk/cap sensitivity (4 runs): `DampBimpl1e18`,
`DampBexpl1e20`, `DampCap1e8`, `DampCap4e8`, all Res6 default CFL.
Tests lower-is-better for implicit bulk, symmetry for explicit, and clip
threshold dependence for cap.

Batch C, resolution (6 runs): Res7 x {None, Cap2e8, best tau from A,
Bimpl1e19} plus Res5 x {None, Cap2e8}. Front width (~3.5 km) is ~0.9 dx at
Res6; Res7 puts ~2 cells across the front and should move energy out of the
grid band for every damper. Run only the A/B winners at Res7 if allocation
is tight.

Falsification: tau rejected if peak reduction under 20% or final drift over
10% across the sweep; localised bulk (follow-up, needs plugin change)
rejected if three matched pairs show no final-state gain over global at
equal peak reduction; cap kept only as the equilibrium placeholder unless a
threshold preserves the transient waveform.

## Barkla procedure

No plugin rebuild needed for A/B/C (all constants are runtime params).
On Barkla2: pull, `make -C simulation configs`,
`make -C simulation models-sink-suite`, watch for node-clustered MPI_Init
`ompi_mpi_instance_init` failures (`sinfo -N -R`), remove stale
`NH_Sink_*` configs only on hard failures, then `make sync-barkla` and
`make visualize`. `make -C simulation all-models` is now sink-only.
