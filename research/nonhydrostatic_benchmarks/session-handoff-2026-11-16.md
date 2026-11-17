# Session handoff — nonhydrostatic benchmarks (2026-11-16, consolidated)

## Goal
Paper testing ALL damping strategies (S1 implicit bulk, S1b explicit bulk,
S2 relaxed pressure, S4 capped pressure, S0/S3 undamped reference) for
dynamic-pressure-governed phase transformations across 1–3 box benchmarks,
framing oscillation-free / accuracy / cost compromises.

## Repos & branches (all work pushed; user pushes `main`s)
- Benchmarks: `/Users/Shared/workspace/kerswell_et_al_nonhydrostatic_benchmarks`
  (`buchanankerswell/...`), branch `agent/initial-benchmark` (pushed).
- ASPECT fork: `/Users/Shared/workspace/aspect` (`buchanankerswell/aspect`,
  `origin`; `upstream`=geodynamics). Branches (all local==origin):
  - `reaction-chain-core` — tolerance 1e20 + `<=` fix (upstream PR #7319)
  - `operator-split-core` — clamp hook (fork PR #1 onto reaction-chain-core)
  - `cookbook-mtz-kinetics` — MTZ cookbook (upstream PR #7119, still [WIP] title)
  - `agent/bulk-viscosity` — S1 minimal (fork PR #2)
  - `agent/bulk-viscosity-chain` — stack + S1 combined; `build-agent/` built here
- HARD RULE: never touch `geodynamics/aspect` (one mistaken PR #7472 opened+closed).
- Upstream #7331 is lhy11009's (visco-plastic chain), not ours; references #7287.
- Local builds: fork `build-agent/` (aspect-release, currently chain-branch build);
  `/opt/aspect/v3.2.0-pre` + `/opt/dealii/v9.8.0` reference. Bench repo symlinks
  `aspect -> .../aspect/build-agent`, `dealii -> /opt/dealii/v9.8.0` (gitignored).
- Analysis env: `conda run -n kerswell-et-al-mtz-kinetics python` (pyvista, mpl).

## Plugin: nh-kinetics (ReactionChain rewrite, committed)
- `simulation/plugins/nh-kinetics.{cc,h}` ("NH kinetics"): owns
  `ReactionChain`, N from `Reaction chain/Kinetic models`, Cahn kinetics
  (Interface controlled growth / Eutectoid decomposition), per-reaction TSV
  profiles, chain clamp + `clamp_reaction_progress_fields` override,
  N-generalized Gibbs viscosity, seismic outputs.
- NH extensions kept: relaxed-pressure drive (S2 rate), explicit bulk RHS force
  (needs `Enable additional Stokes RHS`), ±cap, dynamic density/Gibbs flags,
  `block` density-excess scaffolding; chain indices = `xi_*` fields only.
- Units decision (user): Z entered SI direct, NO time_scale division
  (Z=4.44e-04 reproduces cookbook's effective 1.4e4/yr kinetics);
  cookbook division flagged for separate upstream fix PR (not done).
- Outputs: `phase_mass_fractions`, `visc_temperature_dependence`,
  `corrected_gibbs` per reaction (arrhenius/thermo splits dropped).

## Benchmarks (`simulation/benchmarks/`, all `--validate`d)
- Box (300x1000 km, uniform inflow, stable control):
  `nh_box_1rxn_{undamped,implicit_bulk,explicit_bulk,relaxed_pressure,capped_pressure}.prm`
  (ζ=1e21/1e20, τ=100 kyr, cap 10 MPa; stepped 3200/3850 init).
- Sink block (1000² km closed free-slip, 150 km +400 block through 410):
  `nh_sink_block_{undamped,implicit_bulk,implicit_bulk_hi,explicit_bulk,relaxed_pressure_1kyr,relaxed_pressure_10kyr,capped_pressure}.prm`
  + `nh_sink_block_test.prm` (ref 4, 1 Myr, ~30 s smoke test, committed).
- Laptop loop: `python/benchmarks/make_laptop_prms.py` generates gitignored
  `benchmarks/laptop/*_laptop.prm` (ref 5, 2 Myr) from Barkla truth (ref 6, 5 Myr).
- Tooling: `extract_timeseries.py` (viz-time by pattern), `locate_extrema.py`,
  `plot_sink_sweep.py` (timeseries + time-matched fronts/halos + 2D fields).
  Figs -> `figs/sink_block/` (gitignored).

## Units finding (affects all reported velocities)
With `Use years instead of seconds`, ASPECT VTU velocity is scaled by
year_in_seconds (m/yr numbers): proved by block advection (345 km/1.25 Myr =
9e-9 m/s vs 0.3 VTU) + CFL dt consistency. True fields sane; pressures fine.
`velocity_rms` CSV column is likewise m/yr. Reaction rates are SI s^-1
(splitter integrates seconds) — our no-division convention is correct.

## Results
- Box refactored: all quasi-static (fast kinetics + slow inflow); old S0 blowup
  and S1 dipoles traced to missing post-integration clamp (now fixed by chain).
  +72 MPa bottom high is a setup boundary feature (survived stepped init).
  implicit adds only a −9 MPa transient at +20% Stokes cost.
- Sink block (the hundreds-of-MPa regime): −540 MPa dipole → −650/−850 MPa as
  block crosses; front warps ~12 km; phase-amplified central collapse drags
  block ~100x Stokes speed. Ref5==ref6 to ~1% (ref4 within ~15%).
- Re-anchored sweep (ζ≈K·τ_rxn≈1e19, τ_rel≈kyr, cap 200 MPa), Maxwell rule from
  Curbelo-2019 §4 tr=(4/3)η/γP + τ_V=ζ/K argument (paper: ideal-gas EOS, no ζ
  prescription — rule is our derivation): implicit 1e19 ≈ explicit 1e19
  (−677/−679 MPa); 1e20 slightly worse (−700); relaxed deeper (−850, lag);
  capped clips (−450) but shallows mean front ~8 km. Geometry barely separates.
- Full ref-6 sink `undamped` (5 Myr) done; ref-6 sweep killed after it (too slow);
  laptop 7/7 done (~95 s/run).

## Open / next
1. Upstream reviews: #7319 roadmap comment posted by user; #7319 indent CI flaked
   on apt setup (re-run failed jobs); de-WIP #7119; open hook PR post-#7319;
   close fork #1 then.
2. Upstream cookbook time_scale units fix PR (user decision, not started).
3. Barkla: ref-6/7 confirmation of sink 7; 2-3-reaction boxes later.
4. If strategy split too modest: slower kinetics (smaller Z) or softer η variant.
5. `.env` OpenAlex key unused (CLI ran keyless); full claim-verification gate
   deferred to manuscript stage (see project.json).
