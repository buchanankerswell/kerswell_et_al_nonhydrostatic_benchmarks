# Benchmark design

## Minimal sweep expansion

The registered axes are damping kind and value (Bimpl, Bexpl, Rel, Cap), mesh
(Res5-7), CFL (0.25, 0.5, 1.0), and kinetic prefactor Z. Only Z_MID
(4.44e-04 1/s/K) runs today; Z_LO (9.51e-08) and Z_HI (1.4e+04) are defined
but unused. Block excess density is fixed at 400 kg/m3. Add runs in this order.

1. No-feedback reference twins at Res5, Res7, CFL0.25, and CFL1.0 (four runs).
   This is the highest-value addition: it defines relative error against S2
   across the whole mesh and step sweep. Today only Res6 has a reference.
2. Complete the three-resolution ladder for the winning damper: add Rel3.156e11
   at Res5. Cap2e8 already has Res5/6/7; the relaxed ladder does not.
3. Bracket the time-step sweep: add Rel3.156e11 at CFL1.0. We currently have
   CFL0.25 and CFL0.5 for the damper, and CFL1.0 only for the undamped run.
4. Locate the tau threshold with two more relaxed runs near 30 yr and 300 yr.
   Today 10 yr rings, 100 yr cuts 40%, and 1 kyr fully suppresses.
5. Z sweep at three points (Z_LO, Z_MID, Z_HI) for S1, S2, and the winning
   damper (six runs plus three existing). Reaction rate sets the phase-change
   time, so this axis tests the timescale argument directly. Z_HI is close to
   instantaneous kinetics and may stall the ARKODE reaction solve; submit it
   with a shortened end time first.
6. Optional: vary block excess density (e.g. 200 and 800 kg/m3) for S1 and the
   winner to test whether the oscillation threshold scales with forcing.

Keep the total near ten to fifteen new runs. Prioritize items 1-3; they make
the relative-error and convergence claims possible.

## ASPECT demos worth using

The ASPECT source at `/Users/Shared/workspace/aspect` sits on branch
`cookbook-mtz-kinetics`. The built install
`/opt/aspect/v3.2.0-pre-bulk-viscosity-chain` is the pre-feature baseline
binary. Global Stokes bulk viscosity (the zeta damping term) exists only on
the `agent/bulk-viscosity` and `agent/bulk-viscosity-chain` branches.

Reduced, analytic cases that isolate the mechanism:

- `benchmarks/compressibility_formulations/` is the companion to Gassmoller et
  al. (2020), the paper we cite. `lateral_pipe_increase_pressure/` ships
  `projected_density.prm` and `projected_density_full_pressure.prm`; the plugin
  comment says the projected-density switch exists "to prevent pressure waves
  from forming". `lateral_pipe_transient/` has an analytic mass-flux solution
  and a time-step sweep. Use these to show the feedback in a case with a known
  answer, independent of our sinking block.
- `tests/box_lithostatic_pressure_2d.prm` and
  `tests/compressibility_volumetric_strain_rate.prm` give a hydrostatic column
  and a clean divergence test for the term zeta multiplies.

Physics context and controls:

- `cookbooks/mtz_kinetics/` is the actual 410/520/660 kinetic model. Its
  driving force contains (P - P_ref) dV and its PRM ships with
  `Use dynamic pressure correction for density` and `... for gibbs` set to
  false (figure names carry `Dynp0`). Turning them on reproduces our feedback;
  cite it as the community case our benchmarks sit inside.
- `cookbooks/phase_transition_kinetics/` is the single-transition version
  (metastable olivine wedge), the simplest version of the same loop.
- `cookbooks/christensen_yuen_phase_function/` and `cookbooks/latent-heat/`
  are equilibrium phase-change references with no kinetics and no dynamic
  pressure. Use them as negative controls.

Validation of the damping terms:

- `benchmarks/solitary_wave/` has an analytic compaction wave whose shape and
  speed depend on bulk/compaction viscosity. It is the cleanest check that a
  zeta term is implemented correctly.
- `benchmarks/viscoelastic_stress_build_up/` and
  `benchmarks/viscoelastic_relaxation/` are relaxation-time analogs; the
  elasticity material model carries an "elastic stabilization factor" that
  damps oscillations, a knob comparable to our tau.
- `source/postprocess/visualization/nonadiabatic_pressure.cc` outputs P-hat,
  the diagnostic we measure.

Negative control: `benchmarks/inclusion/` documents pressure oscillations at a
viscosity jump. Those are discretization artifacts, not the physical feedback;
keep them distinct in the text.

Recommendation: add one reduced pipe case and the solitary-wave case to the
argument, and cite `mtz_kinetics` as the community context. That triangulates
the mechanism, the remedy, and the implementation.
