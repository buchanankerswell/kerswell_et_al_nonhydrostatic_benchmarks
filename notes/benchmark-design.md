# Benchmark design

## Suite architecture and Batch D expansion

The sink benchmark suite registers 40 runs in `project.mk` and `simulation/local.mk` (`S1`–`S24`, `SCFL10`, and Batch D `S25`–`S39`). The experimental axes are dynamic-pressure feedback mode (`DynpOn`, `DynpDens`, `DynpOff`), damping treatment and value (`None`, `Bimpl`, `Bexpl`, `Rel`, `Cap`), global mesh refinement (`Res5`–`Res7`), Courant number (`CFL` $0.25, 0.5, 1.0$), and kinetic prefactor $Z \in \{Z_\mathrm{LO}, Z_\mathrm{MID}, Z_\mathrm{HI}\}$ with $Z_\mathrm{LO} = 9.51\times 10^{-8}$, $Z_\mathrm{MID} = 4.44\times 10^{-4}$, and $Z_\mathrm{HI} = 1.4\times 10^4\;\mathrm{K^{-1}\,s^{-1}}$. Block excess density is fixed at $\Delta\rho_\mathrm{block} = 400\;\mathrm{kg\,m^{-3}}$.

The discrete pressure-wave recursion derived in `notes/feedback-formulation.md`,

$$
p^n = -\frac{3}{2}(a + b)\,p^{n-1} + \frac{1}{2}(4a + b)\,p^{n-2} - \frac{1}{2}a\,p^{n-3}, \qquad a \equiv \frac{M\bar{\beta}}{\Delta t}, \qquad b \equiv M\gamma\kappa
$$

with longitudinal viscosity $M = \frac{4}{3}\eta + \zeta$, shows that instability occurs when $2a + b_\mathrm{eff} > 1/2$ (BDF2) or $2a + b_\mathrm{eff} > 1$ (backward Euler). Batch D (`ID_S25`–`ID_S39`) expands the initial 25-run suite by 15 runs to test each term in this mechanism and complete the convergence ladders:

1. **Kinetic-versus-compressibility decoupling (`ID_S25`, 1 run)**:
   - `NH_Sink_DynpDens_DampNone_Block400_Z4.44e-04_Res6` enables dynamic pressure in the equation of state (`Use dynamic pressure correction for density = true`, $a > 0$) while excluding it from the Gibbs free energy (`Use dynamic pressure correction for gibbs = false`, $b = 0$). Comparing `DynpOn` ($a > 0, b > 0$), `DynpDens` ($a > 0, b = 0$), and `DynpOff` ($a = 0, b = 0$) isolates the kinetic feedback $b = M\gamma\kappa$ from the equation-of-state compressibility lag $a = M\bar{\beta}/\Delta t$ and directly tests the stabilization used in `kerswell_et_al_660_kinetics/draft/manuscript.md:259-261`.
2. **No-feedback reference twins across mesh and time-step sweeps (`ID_S26`–`ID_S29`, 4 runs)**:
   - `NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res5` (`ID_S26`)
   - `NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res7` (`ID_S27`)
   - `NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6_CFL0.25` (`ID_S28`)
   - `NH_Sink_DynpOff_DampNone_Block400_Z4.44e-04_Res6_CFL1.0` (`ID_S29`)
   These runs provide a matched `DynpOff` physics reference at every resolution and Courant number so relative error in $\hat{P}$ range and 410 displacement is measured against the same discretization rather than borrowing the `Res6` `CFL0.5` reference.
3. **Complete the resolution and time-step ladders for the $10\;\mathrm{kyr}$ relaxed treatment (`ID_S30`–`ID_S31`, 2 runs)**:
   - `NH_Sink_DynpOn_DampRel3.156e11_Block400_Z4.44e-04_Res5` (`ID_S30`)
   - `NH_Sink_DynpOn_DampRel3.156e11_Block400_Z4.44e-04_Res6_CFL1.0` (`ID_S31`)
   Combined with `S7` (`Res6`, `CFL0.5`), `S14` (`Res6`, `CFL0.25`), and `S21` (`Res7`, `CFL0.5`), these complete the full three-point mesh ladder (`Res5`, `Res6`, `Res7`) and three-point Courant ladder (`CFL` $0.25, 0.5, 1.0$) for `Rel3.156e11`.
4. **Bracket the relaxation-time stability threshold (`ID_S32`–`ID_S33`, 2 runs)**:
   - `NH_Sink_DynpOn_DampRel9.468e8_Block400_Z4.44e-04_Res6` (`ID_S32`, $\tau_p = 30\;\mathrm{yr}$)
   - `NH_Sink_DynpOn_DampRel9.468e9_Block400_Z4.44e-04_Res6` (`ID_S33`, $\tau_p = 300\;\mathrm{yr}$)
   Placed logarithmically between $10\;\mathrm{yr}$ (`S9`, $132.6\;\mathrm{MPa}$ short-wavelength amplitude), $100\;\mathrm{yr}$ (`S10`, $123.5\;\mathrm{MPa}$), and $1\;\mathrm{kyr}$ (`S6`, $7.1\;\mathrm{MPa}$), these locate the transition where $b_\mathrm{eff}(\tau_p) = b\,\Delta t / (\Delta t + \tau_p)$ crosses the BDF2 stability boundary.
5. **Kinetic prefactor $Z$ sweep (`ID_S34`–`ID_S39`, 6 runs)**:
   - Sluggish ($Z_\mathrm{LO} = 9.51\times 10^{-8}\;\mathrm{K^{-1}\,s^{-1}}$): `DynpOn_DampNone` (`ID_S34`), `DynpOff_DampNone` (`ID_S35`), and `DynpOn_DampRel3.156e11` (`ID_S36`).
   - Quasi-equilibrium ($Z_\mathrm{HI} = 1.4\times 10^4\;\mathrm{K^{-1}\,s^{-1}}$): `DynpOn_DampNone` (`ID_S37`), `DynpOff_DampNone` (`ID_S38`), and `DynpOn_DampRel3.156e11` (`ID_S39`).
   Varying $Z$ over eleven orders of magnitude tests the direct dependence of the oscillation gain $b = M\gamma\kappa \propto Z$ on reaction timescale $\tau = 1/\dot{X}_\mathrm{max}$.

## Code fixes incorporated before running Batch D and rerunning crashed cases

1. **Adiabatic reference startup guard and zero-initialized dynamic-pressure relaxation (`simulation/plugins/nh-kinetics.cc`, `simulation/params/templates/NH/sink/initial.prm`)**:
   - `NHKinetics::evaluate()` now keeps `dynamic_pressure = 0.0` while `!this->get_adiabatic_conditions().is_initialized()`, preventing `AdiabaticConditions::ComputeProfile::initialize()` from baking a $+100.7\;\mathrm{MPa}$ (`Rel`), $+20.41\;\mathrm{MPa}$ (`DampNone`/`Bimpl`/`Bexpl`), or $+5.1\text{--}13.0\;\mathrm{MPa}$ (`Cap`) density-compression bias into `adiabatic_pressure`.
   - `relaxed_pressure` is initialized to $0\;\mathrm{Pa}$ in `initial.prm` and relaxes toward the instantaneous mechanical dynamic pressure $\hat{P}_\mathrm{mech} = P_\mathrm{mech} - P_\mathrm{ref}$, eliminating both the $t = 0$ lithostatic mismatch and the advective lag $-\tau_p(\vec{u}\cdot\nabla\bar{P})$.
   - Postprocessing (`python/benchmarks/common.py`, `plot_depth_window.py`, `extract_lateral_pressure.py`, `extract_timeseries.py`, `plot_depth_profiles.py`, `simulation/mesh/preprocess.py`) evaluates $\hat{P}$ for $t > 0$ against the uncorrupted 1D reference adiabat from `DynpOff` (`S2`), removing the startup `adiabatic_pressure` offset from all existing Barkla2 outputs.
2. **Mechanical mean normal stress in $\Delta G$ and $\rho$ (`simulation/plugins/nh-kinetics.cc`)**:
   - When implicit or explicit bulk viscosity $\zeta = \zeta_\mathrm{impl} + \zeta_\mathrm{expl} > 0$ is active, `NHKinetics::evaluate()` evaluates $P_\mathrm{mech} = P - \zeta\nabla\cdot\vec{u}$ so the thermodynamic driving force and density use the mean normal stress rather than the finite-element pressure.
3. **Momentum-equation assembly for explicit bulk viscosity (`Bexpl`)**:
   - `AdditionalMaterialOutputsStokesRHS<dim>` in ASPECT (`include/aspect/material_model/interface.h`, `source/simulator/assemblers/stokes.cc`, `source/simulator/assemblers/newton_stokes.cc`) now provides `rhs_div_u`, assembling $+\int_\Omega \mathrm{rhs}_{\mathrm{div}\,u}\,(\nabla\cdot\vec{v})\,dV$ on the Stokes momentum right-hand side.
   - `NHKinetics::evaluate()` sets `stokes_rhs_out->rhs_div_u[q] = -bulk_viscosity_explicit * div_u` (in $\mathrm{Pa}$) and `rhs_p[q] = 0.0`, replacing the broken continuity mass source (`Bexpl1e19` `S5` and `Bexpl1e20` `S16` can now be rerun as true explicit momentum stresses).
4. **Preconditioner, Newton, and material-averaging support for implicit bulk viscosity (`Bimpl`) on `aspect` branch `agent/bulk-viscosity-chain`**:
   - `StokesPreconditioner` scales the pressure Schur-complement mass matrix by $1/(\eta + \zeta)$, and `StokesCompressiblePreconditioner` adds $+\zeta(\nabla\cdot\vec{v}, \nabla\cdot\vec{u})$ to the velocity block ( enabling `Bimpl1e19_CFL0.25` `S13` and `Bimpl1e19_Res7` `S22` to use a consistent preconditioner).
   - `NewtonHandler::set_assemblers()`, `NewtonStokesPreconditioner`, `NewtonStokesCompressiblePreconditioner`, and `NewtonStokesCompressibleStrainRateViscosityTerm` include $\zeta$, and `BulkViscosityOutputs::average()` and `AdditionalMaterialOutputsStokesRHS::average()` average their quadrature-point vectors via `MaterialAveraging::average_property()`.

## ASPECT demos worth using

The ASPECT source at `/Users/Shared/workspace/aspect` sits on branch `agent/bulk-viscosity-chain`. The built install `/opt/aspect/v3.2.0-pre-bulk-viscosity-chain` points its include path to `/Users/Shared/workspace/aspect/include`; rebuild the binary in `/opt/aspect/v3.2.0-pre-bulk-viscosity-chain` (and on Barkla2) before running the updated `Bimpl` and `Bexpl` models.

Reduced, analytic cases that isolate the mechanism:

- `benchmarks/compressibility_formulations/` is the companion to Gassmöller et al. (2020). `lateral_pipe_increase_pressure/` ships `projected_density.prm` and `projected_density_full_pressure.prm`; the plugin comment states that `Use adiabatic pressure for density` exists "to prevent pressure waves from forming". `lateral_pipe_transient/` has an analytic mass-flux solution and a time-step sweep. Use these to demonstrate the pure $a = M\bar{\beta}/\Delta t$ feedback ($b = 0$) in a geometry with an analytic solution, independent of the sinking block.
- `tests/box_lithostatic_pressure_2d.prm` and `tests/compressibility_volumetric_strain_rate.prm` provide a hydrostatic column and a clean divergence test for the $+\zeta(\nabla\cdot\vec{v}, \nabla\cdot\vec{u})$ bilinear form.

Physics context and controls:

- `cookbooks/mtz_kinetics/` is the 410/520/660 kinetic model. Its driving force contains $(P - P_\mathrm{ref})\Delta\bar{V}$ and its PRM ships with `Use dynamic pressure correction for density` and `... for gibbs` set to `false` (figure names include `Dynp0`). Turning them on reproduces our feedback loop; cite it as the community application that frames our benchmarks.
- `cookbooks/phase_transition_kinetics/` is the single-transition version (metastable olivine wedge), the simplest slab realization of the same loop.
- `cookbooks/christensen_yuen_phase_function/` and `cookbooks/latent-heat/` are equilibrium phase-transformation references with no kinetic rate law and no dynamic-pressure driving term. Use them as negative controls.

Validation of the damping terms:

- `benchmarks/solitary_wave/` has an analytic compaction wave whose shape and phase speed depend on bulk/compaction viscosity, providing a direct check of the $\zeta$ operator.
- `benchmarks/viscoelastic_stress_build_up/` and `benchmarks/viscoelastic_relaxation/` are relaxation-time analogs; the elasticity material model uses an elastic stabilization factor analogous to $\tau_p$.
- `source/postprocess/visualization/nonadiabatic_pressure.cc` outputs $\hat{P}$, the diagnostic we measure.

Negative control: `benchmarks/inclusion/` documents Stokes pressure oscillations at a sharp viscosity jump. Those are finite-element discretization artifacts rather than the compressible pressure-reaction feedback; treat them separately in the Discussion.
