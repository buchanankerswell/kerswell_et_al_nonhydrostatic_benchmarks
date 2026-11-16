# Synthesis: dynamic-pressure reactions + bulk-viscosity damping

**Question**: How can dynamic pressure govern phase transformations without
spurious pressure oscillations, compatibly with ASPECT's PDA?

**Status**: title/abstract screening done (70-record corpus, OpenAlex,
2026-11-16, unauthenticated polite pool). Two seed papers read in full.
Claims below are abstract-level unless marked [full-text]. ASPECT source
canvas (bulk-viscosity injection points) delegated to a background agent;
strategies in §4 are preliminary pending its report.

## 1. Why dynamic pressure breaks the continuity/Stokes coupling [full-text]

- Gassmoller et al. (2020) derive the projected density approximation (PDA):
  `div u = -1/rho~ d(rho~)/dt - 1/rho~ grad(rho~).u`, where `rho~` is the
  projected density evaluated at the *hydrostatic* reference pressure `ph`.
  Excluding dynamic pressure from the density is deliberate: density changes
  from dynamic pressure are ~0.1% but reintroduce pressure waves.
  (doi:10.1093/gji/ggaa078)
- Curbelo et al. (2019), §4: with zero bulk viscosity (Stokes hypothesis),
  pressure perturbations relax on the viscous isentropic timescale
  `tr = 4/3 eta / (gamma P0)` (hundreds of yr upper mantle, tens of kyr lower
  mantle). Explicit schemes must step below `tr` or fluctuations amplify.
  (doi:10.1017/jfm.2019.420)
- Gassmoller et al. (2020) write the isotropic stress as
  `tau = eta[grad u + grad u^T] - (2/3 eta - zeta)(div u) I`, with bulk
  viscosity `zeta ≈ 0` in near-incompressible fluids. Re-introducing
  `zeta > 0` changes the longitudinal (compressional) viscosity from
  `4/3 eta` to `4/3 eta + zeta`, i.e. it directly lengthens `tr` — the exact
  knob the maintainers suggested.

## 2. Precedent: kinetics coupled to slab dynamics (hydrostatic governance)

- GJI 2009 (doi:10.1111/j.1365-246x.2009.04182.x): subduction models with
  olivine-spinel kinetics + equilibrium spinel-perovskite show a dynamic
  feedback ("parachute" effect of metastable olivine) producing 3-4 Myr
  oscillations in slab velocity and MO depth. Proves kinetics↔dynamics
  feedback exists even with hydrostatic governance; dynamic-pressure
  governance will strengthen it — hence the need for damping.
- PEPI 2014 Mariana kinetics (doi:10.1016/j.pepi.2014.12.001) [title-only;
  abstract missing in OpenAlex]: 2-D convection + phase-change kinetics.
  Full-text follow-up.
- Lithos 2016 review of solid-solid transitions (doi:10.1016/j.lithos.2016.11.007)
  [title-only]: background on transition treatment. Full-text follow-up.

## 3. Physics basis: stress (not mean pressure) governs transformations

- JGR 2016 quartz-coesite shear experiments (doi:10.1002/2016jb013084):
  coesite nucleates when the *maximum principal stress σ1* — not confining
  pressure or mean stress — enters the stability field; deformation always
  enhances kinetics. Direct experimental justification for letting the full
  (non-hydrostatic) stress state, not `ph`, drive reactions.
- Nature Commun 2022 olivine faulting (doi:10.1038/s41467-022-32923-8):
  throughgoing faults + acoustic emissions at the olivine→wadsleyite onset
  inside a metastable wedge — transformation-linked weakening under slab
  stress states.
- GJI 1998 transformational superplasticity (doi:10.1046/j.1365-246x.1998.00539.x):
  grain-reshaping strain rates accommodating transformation volume change can
  exceed tectonic strain rates by an order of magnitude; effective viscosity
  drops by up to 1-3 orders of magnitude. Sets the magnitude of mechanical
  feedback our benchmarks must resolve, not damp away.
- Supporting (title-level): Burnley & Green 1989 (stress-dependent mechanism);
  Green et al. 1993 (shear-promoted transitions); 2021 oriented-nucleation
  model under nonhydrostatic stress (doi:10.1016/j.jsg.2020.104275);
  2019 incoherent-interface continuum model (doi:10.1016/j.pepi.2019.03.001);
  2025 transient weakening in quartz+olivine (doi:10.1038/s41561-025-01703-6);
  2026 olivine-ringwoodite seismicity (doi:10.1038/s41467-026-71661-z) and
  quasi-diffusionless olivine shear transition (doi:10.1126/sciadv.adu5181).

## 4. Precedent: nonzero bulk viscosity in geodynamics

- GJI 2012 partially-molten-rock viscosities (doi:10.1111/j.1365-246x.2012.05596.x):
  porosity-dependent effective bulk *and* shear viscosities with fitting
  equations "allowing direct implementation into two-phase flow
  melt-matrix formulations". Closest existing template for packaging a bulk
  viscosity as an implementable material-model output.
- Bercovici et al. 2001 two-phase compaction+damage (doi:10.1029/2000jb900430):
  general theory coupling compaction (bulk-viscous matrix response) to
  damage/weakening. Theoretical home for combining our ζ-damping with
  transformation weakening.
- JGR 1990 stress-induced melt migration (doi:10.1029/jb095ib05p06979):
  the dilatational component of differential stress drives melt segregation,
  rate-limited by compaction/dilation kinetics of the residuum. Closest
  experimental analogue of dynamic-pressure-driven mass redistribution.
- Ann. ENS 2019 multifluid relaxation (doi:10.24033/asens.2387):
  relaxation terms equilibrating pressures between coexisting fluids —
  mathematical analogue if we treat reactant/product assemblages as
  relaxing toward a common pressure on timescale τ.

## 5. Research gaps (evidence of absence)

1. No OpenAlex hit couples *bulk viscosity* to *solid-state phase
   transformations* in single-phase compressible convection (Q1 returned only
   general convection; two-phase/compaction literature never addresses MTZ
   reactions).
2. No benchmark with *dynamic-pressure-governed* kinetics exists in ASPECT's
   documented set (PDA explicitly excludes dynamic pressure; kinetics studies
   use adiabatic/hydrostatic pressure).
3. No published calibration of ζ magnitude for transformation volume change
   (compaction literature calibrates against melt fraction, not reaction
   progress).

## 6. Strategies (FINAL — grounded in ASPECT canvas, 2026-11-16)

Canvas results (background agent; ASPECT 3.2.0-pre `/opt/aspect/v3.2.0-pre`,
upstream-main line numbers ±10, local source unreadable):
- Bulk viscosity ξ exists **only** in the melt subsystem
  (`MeltOutputs::compaction_viscosities`); the standard Stokes assembler is
  shear-only plus the `-2η/3` deviatoric correction — **no ξ(∇·u) LHS term**.
- `MaterialModelOutputs` has **no bulk-viscosity slot**; without melt
  transport any ξ a plugin computes is silently ignored.
- Plugin-reachable explicit path: `AdditionalMaterialOutputsStokesRHS`
  (`rhs_u`, `rhs_p`) — RHS force only, no implicit LHS damping.
- PDA continuity (`StokesProjectedDensityFieldTerm`) reads the projected
  `density_field`, fed plugin-side by
  `out.reaction_terms[density_idx] = out.densities - in.composition[density]`
  (`mtz-kinetics.cc:521`, verified) — the feedback loop to damp.
- No `use_dynamic_pressure` switch upstream; `latent_heat.cc` uses full
  `in.pressure`, `steinberger.cc` uses adiabatic. The
  `phase_transition_kinetics` cookbook is the dynamic-pressure prototype;
  our `mtz-kinetics` already gates `(P - P_ref)` density/Gibbs corrections
  behind flags (`mtz-kinetics.cc:338,415,447,479`, verified) currently OFF.
- No upstream benchmark combines phase transitions with compressibility;
  no ξ-based timestep limiter exists (CFL + max step only).

Revised recommendation (implementability order):
- **S2 (do first, plugin-only)**: relaxed pressure at kinetics level. Evolve
  `dp̄/dt = (p - p̄)/τ_rel` and replace `(P - P_ref)` in the Gibbs/density
  corrections with `(p̄ - P_ref)`. τ_rel is the ζ-knob via
  `τ_rel ~ (4/3 η + ζ)/(γP)`. Zero solver changes; works with the installed
  3.2.0-pre build. State variable can ride as an additional compositional
  field or hidden plugin member updated under operator splitting.
- **S1b (parallel prototype, plugin-only)**: explicit bulk force through
  `AdditionalMaterialOutputsStokesRHS` from the previous iterate's `∇·u`.
  Tests whether lagged damping suffices; expected to be timestep-limited,
  which itself quantifies the need for implicit treatment.
- **S1 (upstream contribution, needs ASPECT source access + rebuild)**:
  new `BulkViscosityOutputs` + `StokesBulkViscosityTerm` assembler
  (`+ξ·divφᵢ·divφⱼ`) + preconditioner awareness + ξ-based dt limiter.
  Blocked on `/Users/bck/Working/aspect` readability; propose to ASPECT
  maintainers as the follow-up PR.
- **S3 (reference)**: small-box runs with `dt < tr` characterizing the raw
  oscillation (Curbelo §4), the target S2/S1b must reproduce at large dt.
- **S4 (fallback, nearly free)**: switch the existing Gibbs flag on with a
  magnitude cap on `(P - P_ref)·ΔV`; sensitivity test without closing the
  full density loop.

Proposed Step-2 build: copy `mtz-kinetics` plugin into this repo as a
benchmark material model (1–3 reactions, box geometry per
`reaction-chain-box.prm`), implement S2 + S4 flags, add
`simulation/configs` box benchmark prms.

## References (screened-in set)

- Gassmoller et al. 2020, doi:10.1093/gji/ggaa078 [full-text]
- Curbelo et al. 2019, doi:10.1017/jfm.2019.420 [full-text, §4 + setup]
- GJI 2009, doi:10.1111/j.1365-246x.2009.04182.x [abstract]
- PEPI 2014, doi:10.1016/j.pepi.2014.12.001 [title-only]
- Lithos 2016, doi:10.1016/j.lithos.2016.11.007 [title-only]
- JGR 2016, doi:10.1002/2016jb013084 [abstract]
- Nature Commun 2022, doi:10.1038/s41467-022-32923-8 [abstract]
- GJI 1998, doi:10.1046/j.1365-246x.1998.00539.x [abstract]
- GJI 2012, doi:10.1111/j.1365-246x.2012.05596.x [abstract]
- JBR 2001 (Bercovici), doi:10.1029/2000jb900430 [abstract]
- JGR 1990, doi:10.1029/jb095ib05p06979 [abstract]
- Ann. ENS 2019, doi:10.24033/asens.2387 [abstract]
- Title-only stress-kinetics set: Nature 1989 doi:10.1038/338753a0; JGR 1993
  doi:10.1029/93jb01614; JSG 2021 doi:10.1016/j.jsg.2020.104275; PEPI 2019
  doi:10.1016/j.pepi.2019.03.001; Nature Geosci 2025 doi:10.1038/s41561-025-01703-6;
  Nature Commun 2026 doi:10.1038/s41467-026-71661-z; Sci Adv 2026
  doi:10.1126/sciadv.adu5181.

**Retrieval summary**: 20 records at abstract/title level included as above;
2 evidence candidates need full text (PEPI 2014 Mariana; Lithos 2016 review).
Drop-in: place legally obtained PDFs at
`review/nonhydrostatic-benchmarks/papers/{key}/paper.pdf` and run
`read_paper.py --key {key}` for a re-run. Q1/Q2/Q4 excluded records: general
convection without bulk-viscosity treatment; mineral-physics-only studies;
astrophysical compressible convection; CFD algorithms.
