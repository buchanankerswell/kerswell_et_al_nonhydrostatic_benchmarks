# Session handoff — 2026-11-16 (nonhydrostatic benchmarks, Steps 0–2 + sweep)

## Goal
Prototype benchmarks where 1–3 phase reactions are governed by dynamic
(non-hydrostatic) pressure, and compare damping strategies S1–S4 across the
compromise triangle: oscillation-free / physically accurate / cheap.
Paper will test ALL strategies.

## Repos & branches
- Benchmarks: `/Users/Shared/workspace/kerswell_et_al_nonhydrostatic_benchmarks`
  (`buchanankerswell/kerswell_et_al_nonhydrostatic_benchmarks`),
  work on `agent/initial-benchmark` (pushed). User pushes `main`.
- ASPECT fork: `/Users/Shared/workspace/aspect` (`buchanankerswell/aspect`,
  `origin`; `upstream`=geodynamics, main synced 67f3dc675).
  **HARD RULE: never touch geodynamics/aspect** (one mistaken PR #7472
  opened+closed 2026-11-16). S1 lives on `agent/bulk-viscosity` (pushed);
  fork PR #2 open for review.
- Template refs: `kerswell_et_al_660_kinetics/` (MTZKinetics plugin origin),
  `kerswell_et_al_410_kinetics/`; seed PDFs in workspace root
  (`gassmoller_2020.pdf`, `curbelo_2019.pdf` — both read).
- Local builds: fork `aspect/build-agent/` (has aspect-release);
  `/opt/aspect/v3.2.0-pre` + `/opt/dealii/v9.8.0` (reference).
  Benchmarks repo symlinks `aspect -> .../aspect/build-agent`,
  `dealii -> /opt/dealii/v9.8.0` (gitignored).
- Analysis env: `conda run -n kerswell-et-al-mtz-kinetics python` (pyvista).

## What exists (agent/initial-benchmark)
- `simulation/plugins/nh-kinetics.{cc,h}` (renamed from mtz-kinetics):
  S2 relaxed-pressure field (`Relaxation time for dynamic pressure`, rate
  `(P-pbar)/tau` on `relaxed_pressure` field), S1b explicit bulk force
  (`Explicit bulk viscosity`, `rhs_p = +(zeta/eta_ref)*div(u_old)`; stable
  for zeta<eta), S4 cap (`Maximum dynamic pressure correction`), dynamic
  (P-P_ref) density+Gibbs flags, disabled-reaction slot backfill fix.
- `simulation/benchmarks/nh_box_1rxn_{s0,s1,s1b,s2,s4}.prm` (300x1000 km box,
  1 ol-wd reaction Z=4.44e-04, PDA, operator splitting).
  s0=undamped, s1: zeta=1e21 implicit (fork), s1b: zeta=1e20 explicit,
  s2: tau_rel=100 kyr, s4: cap +-10 MPa.
- `simulation/benchmark_data/` (3 Mg100 TSVs, tracked).
- `python/benchmarks/extract_timeseries.py`, `locate_extrema.py`.
- `review/nonhydrostatic-benchmarks/` (protocol, corpus 70, synthesis with
  S1–S4 + literature verdicts); `research/.../project.json` (phase: analysis).

## Key results (10 Myr runs, all completed)
- S0: locks to +69 MPa bottom pile-up (init-shock wrong fixed point, NOT
  front physics) + unbounded xi overshoot [-1.45, 1.22]; 160 s.
- S4 ≈ S0 (cap changes nothing → anomaly not correction-magnitude-driven).
- S2: kills bottom high but -319 MPa bottom-corner low (corner + relaxed field).
- S1b/S1: ±110-157 MPa dipoles AT THE FRONT (bulk resists legitimate 21%
  transformation volume change; zeta far too big).
- Lesson: bulk must allow transformation divergence while damping waves:
  zeta ~1e18-1e20; setup needs consistent stepped density init.

## Agreed next (awaiting user go)
1. Stepped density init in all prms (kill bottom artifact).
2. zeta sweep 1e18/1e19/1e20 (S1/S1b) + tau sweep (S2) + cap sweep (S4).
3. Review fork PR #2 (S1 diff verified: +zeta div-div sign correct).

## Open points
- S1 follow-ups: preconditioner, Newton assembler, zeta timestep limiter,
  docs, regression test.
- `.env` holds OPENALEX_API_KEY (gitignored); OpenAlex CLI run WITHOUT key
  (polite pool) because `source .env` via shell is denied — move key to
  `~/.env` (skill-sanctioned) if throttled.
- Full claim-verification gate deferred to manuscript stage (see project.json).
- `simulation/{configs,data,results}`, plugin build outputs: gitignored.
