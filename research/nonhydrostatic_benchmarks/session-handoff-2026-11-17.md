# Session handoff — NH benchmarks build/pipeline/visualize (2026-11-17)

## Starting state
Prototype scaffolded from `kerswell_et_al_660_kinetics`. Undamped controls for
both suites already existed (verified `Use dynamic ... = true`, all dampening
knobs 0, no bulk/Stokes-RHS flags) — not created. Box is quasi-static
(control P2P 77 MPa flat, +72 MPa bottom-boundary feature); sink shows the
hundreds-of-MPa dipole (laptop peak 773 MPa at crossing, full-res 1725 MPa).

## Done this session (branch `agent/initial-benchmark`, 3 commits)
1. `0aeeea8` stand-alone: `libmtz-kinetics`→`libnh-kinetics` (local.mk,
   KN/globals.prm), `MTZ kinetics`→`NH kinetics` + TODO (KN/material.prm),
   conda env renames, README clone/DOI, `.gitignore` for `benchmarks/*.run`.
2. `91a27b3` pipeline wiring: `NH_BOX/SINK_PRMS/RUNS`, `RESULTS_BOX/SINK`,
   `TAG/TIMESTEPS/MESH_CSV/DATA_MESH` box/sink in project.mk (single source);
   `benchmarks[-box/-sink-suite]` in simulation/Makefile (test prm excluded
   from HPC runs, no ASPECT_PROFILES dep); `meshes-box/sink-suite` +
   `visualize-benchmarks` via shared `mesh/main.py` on versioned
   `benchmark_data/` profiles; mesh pipeline suite branch (`suite_tag`
   box/sink: `xi_ol_wd`@410 trans_info, bench field set/tiles,
   height-normalized camera ×1.5, `-1` = last output); slab paths unchanged;
   help text corrected slab-only/NH-TBD; operator-column formatting pass.
3. `dcd6760` analysis tools: `select_crossing_timesteps.py` (block-centroid
   410-window + peak-P2P picker), `quantify_pressure_waves.py` (summary CSV +
   comparison plots).
- Removed stale pre-ReactionChain results (`nh_box_1rxn_{s0,s1,s1b,s2,s4}`).
- Rendered 648 PNGs (`figs/{box,sink}_suite` + tiles) covering init,
  410-crossing (outputs 2–4 laptop/full, 3–4 test) and peak transients;
  fixed colorbar/scale-bar overlap (camera framing assumed wide slab).
- `simulation/data/pressure-wave-summary.csv` (15 runs) +
  `figs/benchmarks/pressure_waves_{box,sink,sink_laptop}.png`.

## Key numbers
Box: undamped 76.9 flat; capped +7%; implicit −18% early; relaxed −312%
(still growing @10 Myr). Sink laptop: undamped 773 @t4; implicit/explicit
±1%; relaxed −10%; capped +1.5%. Full-res undamped peak 1725 @t6 (2.2×
laptop — resolution dependence). Noblock static 85.4 (no-block/no-wave proof).

## Open / caveats
- Full-res damped sink runs never finished (killed; only undamped + 1-output
  implicit exist) — no full-res diminishment numbers.
- Full-run `time_yr` is NaN in timeseries (statistics viz-time mapping fails);
  use `tstep_*` columns instead.
- Sink late-time field is near-uniform ≈ −580 MPa (dipole is transient-only);
  physics TBD, not a rendering bug (verified percentiles).
- Laptop runs are NOT in `meshes-sink-suite` (full-prm lists only); rendered
  manually — wire in if laptop becomes first-class.
- KN slab templates still 660-era (see header TODO); R has no NH wiring;
  slab `make visualize`/`sync-barkla`/`download` unchanged.
- Local env is `kerswell-et-al-mtz-kinetics`; repo declares
  `kerswell-et-al-nonhydrostatic-benchmarks` — override with
  `CONDA_PYTHON="conda run -n kerswell-et-al-mtz-kinetics python"` until the
  new env is created.
- zsh does NOT word-split `$VAR` — inline CLI args literally in background
  jobs (two failed jobs this session). `zsh script.sh` background launches
  were transiently permission-denied; inline commands worked.
- AGENTS.md updated (gitignored — local only). Commits signed on
  `agent/initial-benchmark`; working tree clean.
