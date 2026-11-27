# Feedback formulation

Written 2026-11-26 on `agent/formulation-audit`; revised 2026-11-27 on `agent/feedback-solutions`. This note explains the pressure-wave feedback in compressible phase-transition simulations, compares it with ASPECT's two-phase melt transport, audits the implicit and explicit bulk-viscosity damping formulations, and resolves the $\sim 100\;\mathrm{MPa}$ relaxed-pressure offset. Notation follows `kerswell_et_al_660_kinetics/draft/manuscript.md`, including `eq:` labels. Where the manuscript and ASPECT use the same symbol for different quantities, the distinction is stated explicitly.

## The loop

The governing equations for single-phase compressible flow in ASPECT are conservation of momentum (`eq:navier-stokes-no-inertia`) and the projected-density continuity equation (`eq:continuity-expanded`):

$$
\nabla P - \nabla\cdot\sigma^{\prime} = \rho\,\vec{g}
$$

$$
\frac{1}{\rho}\frac{\partial\rho}{\partial t} + \nabla\cdot\vec{u} + \left(\frac{1}{\rho}\nabla\rho\right)\cdot\vec{u} = 0
$$

ASPECT's standard single-phase viscous stress is purely deviatoric:

$$
\sigma^{\prime} = 2\eta\dot{\epsilon}^{\prime} = 2\eta\left(\dot{\epsilon}(\vec{u}) - \frac{1}{3}(\nabla\cdot\vec{u})\mathbf{I}\right)
$$

With zero bulk viscosity ($\zeta = 0$), the Stokes pressure $P$ equals the mechanical mean normal stress $P_\mathrm{mech} = -\frac{1}{3}\operatorname{tr}(\sigma)$. When a bulk viscosity $\zeta > 0$ is added to the viscous stress, the total Cauchy stress becomes

$$
\sigma = -P\mathbf{I} + 2\eta\dot{\epsilon}^{\prime} + \zeta(\nabla\cdot\vec{u})\mathbf{I}
$$

so the momentum equation and mechanical pressure become

$$
\nabla P - \nabla\cdot\left(2\eta\dot{\epsilon}^{\prime}\right) - \nabla\left(\zeta\nabla\cdot\vec{u}\right) = \rho\,\vec{g}, \qquad P_\mathrm{mech} = -\frac{1}{3}\operatorname{tr}(\sigma) = P - \zeta\nabla\cdot\vec{u}
$$

Density follows a linearized equation of state around the reference adiabatic profile (`eq:density-ala`) combined with the phase-transformation density jump $\Delta\rho = \rho_b - \rho_a$ weighted by the product volume fraction $X$:

$$
\rho(T, P, X) \approx \left(\bar{\rho}_a + \Delta\rho\,X\right)\left(1 - \bar{\alpha}\hat{T}\right)\left(1 + \bar{\beta}\hat{P}\right) + \Delta\rho_\mathrm{block}C_\mathrm{block}
$$

where $\hat{P} = P - \bar{P}$ and $\hat{T} = T - \bar{T}$ are the dynamic (nonadiabatic) pressure and temperature. The molar Gibbs free energy difference driving each phase transformation (`eq:gibbs`) is

$$
\Delta G \approx \Delta\bar{G} + \hat{P}\Delta\bar{V} - \hat{T}\Delta\bar{S}
$$

and the reaction rate $\dot{X}$ follows interface-controlled growth at the 410 and 520 (`eq:reaction-rate-410`) or diffusion-controlled eutectoid decomposition at the 660 (`eq:reaction-rate-660`). In `kerswell_et_al_660_kinetics/draft/manuscript.md` (`eq:reaction-rate-410`), the driving-force factor is written as $1 - \exp(-\Delta G / RT)$ with $\Delta G > 0$ defined as forward overstepping, whereas the thermodynamic tables (`simulation/data/olivine-wadsleyite-profile-Mg100.tsv`) and ASPECT's reaction plugin (`include/aspect/material_model/reaction_model/kinetics/cahn1956_interface_controlled_growth.h:38-44,67-70`) define $\Delta G = G_b - G_a < 0$ in the high-pressure product stability field and evaluate

$$
\dot{X} = Z_\mathrm{ol}\,T\,\exp\!\left(-\frac{H^{\ast} + P V^{\ast}}{R\,T}\right)\left(1 - \exp\!\left[\frac{\Delta G}{R\,T}\right]\right)(1 - X) \qquad (\Delta G < 0)
$$

In both sign conventions, because the high-pressure polymorph is denser ($\Delta\bar{V} = \bar{V}_b - \bar{V}_a = -2.07\times 10^{-6}\;\mathrm{m}^3\,\mathrm{mol}^{-1}$ and $\Delta\rho = 182\;\mathrm{kg}\,\mathrm{m}^{-3}$ at $14.14\;\mathrm{GPa}$), a positive dynamic pressure perturbation $\hat{P} > 0$ makes $\hat{P}\Delta\bar{V} < 0$ and accelerates the forward reaction toward the denser phase:

$$
\kappa \equiv \frac{\partial\dot{X}}{\partial\hat{P}} > 0
$$

Five steps close the feedback loop:

1. **Thermodynamic driving force**: A dynamic pressure perturbation $\hat{P}$ shifts $\Delta G$ by $\hat{P}\Delta\bar{V}$ and perturbs the transformation rate by $\delta\dot{X} = \kappa\,\hat{P}$.
2. **Density evolution**: Both elastic compression ($\bar{\rho}\bar{\beta}\hat{P}$) and phase progress ($\Delta\rho\,X$) modify the local density at fractional rate

$$
\frac{1}{\bar{\rho}}\frac{\partial\rho}{\partial t} \approx \bar{\beta}\frac{\partial\hat{P}}{\partial t} + \gamma\dot{X}, \qquad \gamma \equiv \frac{\Delta\rho}{\bar{\rho}} > 0
$$

3. **Mass conservation**: The projected-density continuity equation prescribes the velocity divergence required to accommodate that density change:

$$
\nabla\cdot\vec{u} = -\frac{1}{\rho}\frac{\partial\rho}{\partial t} - \left(\frac{1}{\rho}\nabla\rho\right)\cdot\vec{u} \approx -\bar{\beta}\frac{\partial\hat{P}}{\partial t} - \gamma\dot{X} - \left(\frac{1}{\rho}\nabla\rho\right)\cdot\vec{u}
$$

4. **Momentum balance**: For locally uniform viscosities $\eta$ and $\zeta$, taking the divergence of the compressible Stokes momentum equation yields

$$
\nabla^2\left(\hat{P} - M\,\nabla\cdot\vec{u}\right) = \nabla\cdot\left(\hat{\rho}\,\vec{g}\right), \qquad M \equiv \frac{4}{3}\eta + \zeta
$$

where $M$ is the longitudinal (compressional) viscosity; note that ASPECT uses the 3D deviatoric factor $2/3$ even in 2D (`source/simulator/assemblers/stokes.cc:548-555`). Defining $\hat{P}_\mathrm{buoy}$ as the incompressible buoyancy pressure solving $\nabla^2\hat{P}_\mathrm{buoy} = \nabla\cdot(\hat{\rho}\,\vec{g})$, the local Stokes pressure response to a volume change is

$$
\hat{P} = \hat{P}_\mathrm{buoy} + M\,\nabla\cdot\vec{u}
$$

5. **Closure**: This updated Stokes pressure $\hat{P}$ feeds back into $\rho(T, P, X)$ and $\Delta G(T, P)$ on the next step.

### Continuum stability versus discrete lag instability

In the continuum limit, the feedback is negative (stabilizing): a positive pressure perturbation $\hat{P} > 0$ accelerates densification ($\dot{\rho} > 0$), which requires volume contraction ($\nabla\cdot\vec{u} < 0$), and inward viscous flow creates local suction ($\hat{P} - \hat{P}_\mathrm{buoy} = M\nabla\cdot\vec{u} < 0$) that opposes the initial positive $\hat{P}$. Substituting $\dot{X} = \dot{X}_0 + \kappa\hat{P}$ and the continuity relation into $\hat{P} = \hat{P}_\mathrm{buoy} + M\nabla\cdot\vec{u}$ for a short-wavelength mode gives the first-order relaxation ODE:

$$
M\bar{\beta}\,\frac{\partial\hat{P}}{\partial t} + \left(1 + M\gamma\kappa\right)\hat{P} = \hat{P}_\mathrm{buoy} - M\gamma\dot{X}_0
$$

Its solution decays monotonically with rate

$$
\lambda_\mathrm{cont} = \frac{1 + M\gamma\kappa}{M\bar{\beta}} = \frac{1}{M\bar{\beta}} + \frac{\gamma\kappa}{\bar{\beta}} > 0
$$

What oscillates in ASPECT is the **time-discretized** loop. In `Simulator<dim>::solve_timestep()` (`source/simulator/core.cc:1983-2088`) under `Nonlinear solver scheme = single Advection, single Stokes` and `Use operator splitting = true`:

1. `initialize_current_linearization_point()` (`source/simulator/helper_functions.cc:2039-2059`) sets `current_linearization_point = old_solution` on step 1, and linearly extrapolates `old_solution` and `old_old_solution` on steps $n > 1$:

$$
\Phi_\mathrm{lin}^n = \left(1 + \frac{\Delta t_n}{\Delta t_{n-1}}\right)\Phi^{n-1} - \frac{\Delta t_n}{\Delta t_{n-1}}\Phi^{n-2}
$$

2. `compute_reactions()` (`source/simulator/helper_functions.cc:1703-2034`) integrates $\dot{X}$ and `relaxed_pressure` over $[t^{n-1}, t^n]$ with ARKODE using `in.reinit(..., solution)` (`helper_functions.cc:1866`), where `solution` still holds the step-$(n-1)$ Stokes pressure $P^{n-1}$.
3. `assemble_and_solve_composition()` (`source/simulator/solver_schemes.cc:222-453`) advects the compositional fields to $t^n$ and then updates the prescribed `density_field` via `interpolate_material_output_into_advection_field()` (`solver_schemes.cc:389`, `helper_functions.cc:2132-2185`), which reads `prescribed_field_out->prescribed_field_outputs[i][projected_density_idx] = out.densities[i]` (`nh-kinetics.cc:382-384`). Because this projection executes **before** `assemble_and_solve_stokes()`, the prescribed density field at step $n$ is evaluated at the old Stokes pressure $P^{n-1}$:

$$
\rho_\mathrm{field}^n = \rho\!\left(T^n, P^{n-1}, X^n\right)
$$

4. `StokesProjectedDensityFieldTerm::execute()` (`source/simulator/assemblers/stokes.cc:789-869`) evaluates $\partial\rho/\partial t$ on the continuity right-hand side by finite-differencing `density_field` across `current_linearization_point` ($\rho_\mathrm{field}^n$), `old_solution` ($\rho_\mathrm{field}^{n-1}$), and `old_old_solution` ($\rho_\mathrm{field}^{n-2}$), using backward Euler on step 1 and BDF2 on steps $n > 1$ (`stokes.cc:838-855`).

Both the elastic compression $\bar{\beta}\hat{P}^{n-1}$ and the reaction increment $X^n - X^{n-1} \approx \Delta t\,(\dot{X}_0 + \kappa\hat{P}^{n-1})$ inside $\rho_\mathrm{field}^n$ are therefore lagged by one Stokes solve relative to $\hat{P}^n$. Writing $p^n$ for the perturbation in $\hat{P}^n$, backward Euler differencing of $\rho_\mathrm{field}$ yields the two-step recursion

$$
p^n = -M\left(\bar{\beta}\,\frac{p^{n-1} - p^{n-2}}{\Delta t} + \gamma\kappa\,p^{n-1}\right) = -(a + b)\,p^{n-1} + a\,p^{n-2}
$$

and BDF2 differencing at constant $\Delta t$ yields the three-step recursion

$$
p^n = -\frac{3}{2}(a + b)\,p^{n-1} + \frac{1}{2}(4a + b)\,p^{n-2} - \frac{1}{2}a\,p^{n-3}
$$

with dimensionless feedback gains

$$
a \equiv \frac{M\bar{\beta}}{\Delta t}, \qquad b \equiv M\gamma\kappa
$$

For the backward Euler recursion, the characteristic polynomial $\lambda^2 + (a + b)\lambda - a = 0$ has roots

$$
\lambda_{\pm} = \frac{-(a + b) \pm \sqrt{(a + b)^2 + 4a}}{2}
$$

The dominant root $\lambda_-$ is strictly negative for all $a, b > 0$, producing an alternating, sign-flipping pressure oscillation $(-1)^n|\lambda_-|^n$ at every timestep. Evaluating the characteristic polynomial at $\lambda = -1$ gives the exact growth threshold $|\lambda_-| > 1$:

$$
2a + b > 1 \quad (\text{backward Euler}), \qquad 2a + b > \frac{1}{2} \quad (\text{BDF2})
$$

Evaluating $a$ and $b$ at the 410 in the sink suite ($P = 14.14\;\mathrm{GPa}$, $T = 1769\;\mathrm{K}$, $Z_\mathrm{ol} = 4.44\times 10^{-4}\;\mathrm{K^{-1}\,s^{-1}}$, $H^{\ast} = 274\;\mathrm{kJ\,mol^{-1}}$, $V^{\ast} = 3.3\times 10^{-6}\;\mathrm{m^3\,mol^{-1}}$, $\Delta\bar{V} = -2.07\times 10^{-6}\;\mathrm{m^3\,mol^{-1}}$, $\Delta\rho = 182\;\mathrm{kg\,m^{-3}}$, $\bar{\rho} = 3520\;\mathrm{kg\,m^{-3}}$, $\bar{\beta} = 5.5\times 10^{-12}\;\mathrm{Pa^{-1}}$, $\eta = 10^{21}\;\mathrm{Pa\,s}$, $M = \frac{4}{3}\eta = 1.33\times 10^{21}\;\mathrm{Pa\,s}$) gives

$$
k_0 = Z_\mathrm{ol}\,T\,\exp\!\left(-\frac{H^{\ast} + P V^{\ast}}{R\,T}\right) \approx 2.67\times 10^{-10}\;\mathrm{s}^{-1}, \qquad \kappa = \frac{\partial\dot{X}}{\partial\hat{P}} \approx k_0\,\frac{|\Delta\bar{V}|}{R\,T}(1 - X) \approx 3.76\times 10^{-20}(1 - X)\;\mathrm{Pa^{-1}\,s^{-1}}
$$

$$
a = \frac{M\bar{\beta}}{\Delta t} \approx \frac{232\;\mathrm{yr}}{\Delta t} \approx 0.036 \quad (\Delta t \approx 6.5\;\mathrm{kyr}), \qquad b = M\gamma\kappa \approx 2.58\,(1 - X)
$$

When a mesh cell of height $\Delta y$ spans a narrower reaction front of thickness $\delta w \approx 3.5\;\mathrm{km}$, cell-averaging dilutes the local reaction source by $\min(1, \delta w / \Delta y)$, yielding an effective kinetic gain

$$
b_\mathrm{eff} \approx \min\!\left(1, \frac{\delta w}{\Delta y}\right) M\gamma\kappa
$$

At `Res5` ($\Delta y = 15.6\;\mathrm{km}$, $\delta w / \Delta y \approx 0.22$), $b_\mathrm{eff}$ is diluted below the instability threshold and the run completes cleanly ($2\;\mathrm{MPa}$ short-wavelength amplitude). At `Res6` ($\Delta y = 7.8\;\mathrm{km}$) and `Res7` ($\Delta y = 3.9\;\mathrm{km} \approx \delta w$), the mesh resolves the reaction front so $b_\mathrm{eff} \sim 1\text{--}2.6$ while halving $\Delta y$ also halves $\Delta t$ (doubling $a$), driving $2a + b_\mathrm{eff}$ across the BDF2 instability threshold. Similarly, halving the timestep from `CFL0.5` to `CFL0.25` doubles $a$ and doubles the number of sign-flipping amplification steps across the transient, causing the undamped `CFL0.25` run to blow up while `CFL1.0` completes cleanly (`notes/key-results.md:15`). The `benchmarks/compressibility_formulations/lateral_pipe_increase_pressure/` benchmark in ASPECT isolates the pure $a = M\bar{\beta}/\Delta t$ branch of this recursion ($b = 0$): its two PRM files differ only in `Use adiabatic pressure for density` (`true` versus `false`), and the plugin comment notes that the switch exists "to prevent pressure waves from forming" (`benchmarks/compressibility_formulations/plugins/compressibility_formulations.cc:130-133`).

## Why a bulk viscosity cannot damp it

In compressible single-phase Stokes flow, $\nabla\cdot\vec{u}$ is not a free kinematic variable that viscous resistance can suppress; it is fixed by the continuity equation to match $-\frac{1}{\rho}\frac{D\rho}{Dt}$. Adding an implicit bulk viscosity $\zeta(\nabla\cdot\vec{u})\mathbf{I}$ to the stress tensor penalizes $\nabla\cdot\vec{u}$ in the momentum equation, where continuity already prescribes its value. Instead of reducing $|\nabla\cdot\vec{u}|$, the penalty requires a larger Stokes pressure $\hat{P} = \hat{P}_\mathrm{buoy} + (\frac{4}{3}\eta + \zeta)\nabla\cdot\vec{u}$ to drive the mandated volume change. Because $M = \frac{4}{3}\eta + \zeta$ increases linearly with $\zeta$, both feedback gains $a = M\bar{\beta}/\Delta t$ and $b = M\gamma\kappa$ increase with $\zeta$, making the alternating root $|\lambda_-|$ larger.

The benchmark measurements confirm this scaling (`simulation/results/relaxed-mean-check.csv`, `simulation/results/pressure-history-summary.csv`):

| Run | $\zeta$ ($\mathrm{Pa\,s}$) | Peak short-wavelength amplitude ($\mathrm{MPa}$) | Largest $\hat{P}$ range ($\mathrm{MPa}$) |
| :-- | :-- | --: | --: |
| `DynpOn_DampNone` (`S1`) | $0$ | $157.3$ | $2168.2$ |
| `DynpOn_DampBimpl1e18` (`S15`) | $10^{18}$ | $164.7$ | $2172.5$ |
| `DynpOn_DampBimpl1e19` (`S3`) | $10^{19}$ | $181.2$ | $2226.3$ |
| `DynpOn_DampBimpl1e20` (`S4`) | $10^{20}$ | $225.0$ | $2529.9$ |
| `DynpOn_DampBexpl1e19` (`S5`) | $10^{19}$ (explicit) | $210.6$ | $2346.3$ |
| `DynpOn_DampBexpl1e20` (`S16`) | $10^{20}$ (explicit) | crashes at step 1 | $2052.2$ (step 1) |

No bulk-viscosity run reduces the oscillation relative to the undamped baseline (`notes/key-results.md:9`).

## What the two-phase melt models do

ASPECT's two-phase melt transport formulation (Keller et al. 2013, `10.1093/gji/ggt306`; Dannberg & Heister 2016, `10.1093/gji/ggw329`) solves for solid velocity $\vec{u}_s$, fluid (melt) pressure $p_f$, and an independent compaction pressure $p_c$. Writing melt porosity as $\varphi$ (denoted $\phi$ in the ASPECT manual, whereas our manuscript reserves $\phi$ for equilibrium phase fraction in `eq:equilibrium-fractions`), the governing three-field Stokes-Darcy system (`doc/sphinx/user/methods/melt-transport.md:18-58,100-125`) is

$$
-\nabla\cdot\left[2\eta\left(\dot{\epsilon}(\vec{u}_s) - \frac{1}{3}(\nabla\cdot\vec{u}_s)\mathbf{I}\right)\right] + \nabla p_f + \nabla p_c = \rho\,\vec{g}
$$

$$
\nabla\cdot\vec{u}_s - \nabla\cdot\left(K_D\nabla p_f\right) - K_D\nabla p_f\cdot\frac{\nabla\rho_f}{\rho_f} = -\nabla\cdot\left(K_D\rho_f\vec{g}\right) + \Gamma\left(\frac{1}{\rho_f} - \frac{1}{\rho_s}\right) - \frac{\varphi}{\rho_f}\vec{u}_s\cdot\nabla\rho_f - (1 - \varphi)\beta_s\rho_s\left(\vec{u}_s\cdot\vec{g}\right) - K_D\vec{g}\cdot\nabla\rho_f
$$

$$
\nabla\cdot\vec{u}_s + \frac{p_c}{\xi} = 0
$$

where $K_D = k/\eta_f$ is the Darcy coefficient, $\xi$ is the compaction (bulk) viscosity of the solid matrix, $\Gamma$ is the melting rate ($\mathrm{kg\,m^{-3}\,s^{-1}}$), and the compaction pressure is defined by

$$
p_c = (1 - \varphi)\left(p_s - p_f\right) = -\xi\,\nabla\cdot\vec{u}_s
$$

The melt velocity $\vec{u}_f$ and porosity advection equation (`doc/sphinx/user/methods/melt-transport.md:120-125,170-174`) are

$$
\vec{u}_f = \vec{u}_s - \frac{K_D}{\varphi}\left(\nabla p_f - \rho_f\vec{g}\right)
$$

$$
\frac{\partial\varphi}{\partial t} + \vec{u}_s\cdot\nabla\varphi = \frac{\Gamma}{\rho_s} + (1 - \varphi)\left(\nabla\cdot\vec{u}_s + \beta_s\rho_s\vec{g}\cdot\vec{u}_s\right)
$$

The structural difference from our single-phase bulk viscosity is that $\xi$ in the melt assembler enters through the auxiliary variable $p_c$: specifically the $-\frac{1}{\xi}(q_c, p_c)$ block and the two divergence couplings $-(q_c, \nabla\cdot\vec{u}_s)$ and $-(\nabla\cdot\vec{v}, p_c)$ (`source/simulator/melt.cc:539-543`). Algebraically eliminating $p_c = -\xi\nabla\cdot\vec{u}_s$ from the momentum equation yields $+\xi(\nabla\cdot\vec{v}, \nabla\cdot\vec{u}_s)$, matching the continuum operator of `StokesBulkViscosityTerm`. Numerically, however, $p_c$ is a separate finite-element field with its own scaling factor `p_c_scale` and a Schur-complement preconditioner block containing $(\frac{1}{\eta} + \frac{1}{\xi})M_{p_c}$ (`source/simulator/melt.cc:247-291`).

Typical parameters in `Katz2003MantleMelting` (`source/material_model/reaction_model/katz2003_mantle_melting.cc:291-341,450-460,526-555`) are

$$
k = k_0\,\varphi^3(1 - \varphi)^2 \quad (k_0 = 10^{-8}\;\mathrm{m}^2), \qquad \xi = \xi_0\,\frac{\varphi_0}{\varphi} \quad (\xi_0 = 10^{22}\;\mathrm{Pa\,s},\; \varphi_0 = 0.05,\; \varphi \in [10^{-4}, 0.995])
$$

with $\eta_0 = 5\times 10^{20}\;\mathrm{Pa\,s}$, $\eta_f = 10\;\mathrm{Pa\,s}$, $\rho_{s,0} - \rho_{f,0} = 500\;\mathrm{kg\,m^{-3}}$, and compaction length $\delta_c = \sqrt{(\xi + \frac{4}{3}\eta)K_D}$ (`doc/sphinx/parameters/Mesh_20refinement.md:154`; note that `source/mesh_refinement/compaction_length.cc:72-73` writes `std::sqrt((out.viscosities[i] + 4./3. * melt_out->compaction_viscosities[i]) * ...)`, swapping $\eta$ and $\xi$ relative to the manual).

**Taking the zero-porosity or zero-permeability limit does not yield our single-phase bulk-viscosity formulation.** As $K_D \to 0$ ($\varphi \to 0$), the Darcy segregation term $\nabla\cdot(K_D\nabla p_f)$ vanishes from the $p_f$ equation, leaving both $p_f$ and $p_c$ coupled only to $\nabla\cdot\vec{u}_s$ so the $(p_f, p_c)$ block becomes singular while $\xi \propto 1/\varphi \to \infty$. ASPECT avoids this singularity by a discrete cell threshold (`is_melt_cell`): in cells where porosity or $K_D$ falls below the threshold, every $p_c$ degree of freedom is constrained to zero (`constraints.constrain_dof_to_zero(index)`, `source/simulator/melt.cc:1616-1626,1644-1649`) and `p_c_scale` is set to zero. The system then collapses to standard single-phase Stokes with **zero** bulk viscosity and no compaction variable.

More importantly, ASPECT's melt models are stable for five reasons that have nothing to do with viscous damping of $\nabla\cdot\vec{u}_s$:

1. **Adiabatic pressure in reaction rates**: The equilibrium melt fraction $F_\mathrm{eq}(T, \bar{P})$ and melting rate $\Gamma$ are evaluated from `this->get_adiabatic_conditions().pressure(in.position[i])` — the static reference adiabat $\bar{P}$, never the Stokes fluid pressure $p_f$ or compaction pressure $p_c$ (`source/material_model/reaction_model/katz2003_mantle_melting.cc:189,197,209`; `source/material_model/melt_simple.cc:53-54`; `source/material_model/melt_global.cc:186-188`). ASPECT's parameter manual explicitly warns that using full pressure in reaction rates is numerically unstable when compaction pressure is present (`doc/sphinx/parameters/Material_20model.md:4180`). Because $\partial\Gamma/\partial\hat{P} = 0$, the kinetic feedback gain is $b = 0$.
2. **No projected-density $\partial\rho/\partial t$ lag**: Melt transport enforces `AssertThrow` allowing only `isentropic compression` or `incompressible` mass conservation, explicitly forbidding `projected density field` (`source/simulator/melt.cc:1738-1743`). The lagged finite-difference term $\bar{\beta}(\hat{P}^{n-1} - \hat{P}^{n-2})/\Delta t$ is therefore absent ($a = 0$).
3. **Relaxation-time rate limiting on $\Gamma$**: Melting is relaxed over a finite `Melting time scale for operator splitting` $\tau_m$ (default $10^3\;\mathrm{yr}$, required to satisfy $\tau_m \ge \Delta t_\mathrm{rxn}$) and integrated via operator splitting (`source/material_model/melt_simple.cc:64-65`; `katz2003_mantle_melting.cc:253-255,526-542,609-624`):

$$
\frac{\Gamma}{\rho_s} = \frac{F_\mathrm{eq}(T, \bar{P}) - \varphi}{\tau_m}
$$

4. **Implicit porosity-divergence coupling**: In the porosity advection equation, the $-\varphi(\nabla\cdot\vec{u}_s + \beta_s\rho_s\vec{g}\cdot\vec{u}_s)$ part of $(1-\varphi)\nabla\cdot\vec{u}_s$ is moved to the left-hand side matrix (`melt_transport_LHS`, `source/simulator/melt.cc:680-683,823-837,891`).
5. **Preconditioned three-field saddle point**: The compaction viscosity $\xi$ is represented in the Schur-complement preconditioner via $(1/\eta + 1/\xi)M_{p_c}$ (`source/simulator/melt.cc:270-274`).

## What we implemented

All damping treatments in the 25-run sink suite are configured via `project.mk:306-320` and `simulation/params/templates/NH/shared/{solver,material}.prm`:

| Kind | Parameter | Mathematical term and code location |
| :-- | :-- | :-- |
| `DynpOn` / `DynpOff` | `Use dynamic pressure correction for density`, `Use dynamic pressure correction for gibbs` | `project.mk:306-307` ties both booleans to the same `PARAM_dynp` switch: `DynpOff` removes $\hat{P}$ from $\rho$ **and** from $\Delta G$ (`nh-kinetics.cc:282,354`). |
| `Bimpl` | `Enable bulk viscosity`, `Constant bulk viscosity` ($\mathrm{Pa\,s}$) | Assembles $+\int_\Omega \zeta(\nabla\cdot\vec{v})(\nabla\cdot\vec{u})\,dV$ into the Stokes velocity-velocity block (`aspect` branch `agent/bulk-viscosity-chain`, `source/simulator/assemblers/stokes.cc:564-607`). |
| `Bexpl` | `Enable additional Stokes RHS`, `Explicit bulk viscosity` ($\mathrm{Pa\,s}$) | In the audited code, wrote $\mathrm{rhs}_p = +(\zeta/\eta)\nabla\cdot\vec{u}_\mathrm{lin}$ into the continuity RHS (`nh-kinetics.cc:183-195`); fixed on `agent/feedback-solutions` to assemble $-\int_\Omega \zeta(\nabla\cdot\vec{u}_\mathrm{lin})(\nabla\cdot\vec{v})\,dV$ in the momentum RHS via `rhs_div_u`. |
| `Rel` | `Relaxation time for dynamic pressure` ($\mathrm{s}$) | Evolves the compositional field `relaxed_pressure` ($P_\mathrm{rel}$) via $\dot{P}_\mathrm{rel} = (P - P_\mathrm{rel})/\tau_p$ (`nh-kinetics.cc:375-379`) and sets $\hat{P} = P_\mathrm{rel} - \bar{P}$ (`nh-kinetics.cc:174-177`). |
| `Cap` | `Maximum dynamic pressure correction` ($\mathrm{Pa}$) | Clamps the driving pressure to $\hat{P} \in [-P_{\max}, +P_{\max}]$ (`nh-kinetics.cc:178-181`). |

We write $\tau_p$ for the dynamic-pressure relaxation time to distinguish it from the reaction completion timescale $\tau = 1/\dot{X}_\mathrm{max}$ (`eq:reaction-timescale`). Notice that `DynpOff` in the original 25-run suite is a **double control**: it disables $\hat{P}$ in both density ($a = 0$) and Gibbs energy ($b = 0$). In `kerswell_et_al_660_kinetics/draft/manuscript.md:259-261`, the production slab stabilization sets `Use dynamic pressure correction for gibbs = false` while keeping `Use dynamic pressure correction for density = true` ($b = 0$, $a > 0$). Isolating the kinetic feedback from the equation-of-state compressibility lag requires decoupling those two switches (`DynpDens` versus `DynpOff` and `DynpOn`).

## Bugs identified and fixed

Confirmed from code inspection of `simulation/plugins/nh-kinetics.{cc,h}` and `aspect` branch `agent/bulk-viscosity-chain`, ordered by impact:

1. **`NHKinetics::evaluate()` corrupts the 1D reference adiabatic profile during startup, causing the $\sim 100\;\mathrm{MPa}$ relaxed-pressure offset (Critical).**
   When ASPECT initializes its 1D reference adiabat at startup (`AdiabaticConditions::ComputeProfile<dim>::initialize()`, `source/adiabatic_conditions/compute_profile.cc:57-191`), `this->get_adiabatic_conditions().is_initialized()` is `false`. At each depth step $z_i$, `ComputeProfile::initialize()` evaluates `initial_composition` along the domain center axis $x = 500\;\mathrm{km}$ (`source/geometry_model/box.cc:282-301`) and calls `material_model->evaluate(in, out)`. Because `NHKinetics<dim>::evaluate()` (`nh-kinetics.cc:152-182,281-284`) did not check `this->get_adiabatic_conditions().is_initialized()`, it applied a nonzero `dynamic_pressure` correction $\bar{\beta}\hat{P}_\mathrm{init}(z)$ to `out.densities[0]` *while integrating the reference adiabatic pressure itself*, permanently shifting the cached reference profile $\bar{P}_\mathrm{adiab}(z)$ by

$$
\Delta\bar{P}_\mathrm{adiab}(z) = \int_0^z \bar{\rho}(z^{\prime})\,\bar{\beta}(z^{\prime})\,\hat{P}_\mathrm{init}(z^{\prime})\,g\,dz^{\prime}
$$

   In every `Rel` run (`relaxation_time_dynamic_pressure > 0`), `evaluate()` read `p_drive = in.composition[0][relaxed_pressure_idx]` during `ComputeProfile::initialize()`, which is the unrelaxed constant-density lithostat $P_\mathrm{rel,init}(y) = 2.0\times 10^9 + 3900\,g\,(10^6 - y)$ (`simulation/params/templates/NH/sink/initial.prm:8`). Because $3900\;\mathrm{kg\,m^{-3}}$ exceeds upper-mantle olivine density ($\sim 3150\text{--}3430\;\mathrm{kg\,m^{-3}}$), $\hat{P}_\mathrm{init}(z)$ reached $+1.5\text{ to }+2.2\;\mathrm{GPa}$, compressing the reference density by $\sim 39\;\mathrm{kg\,m^{-3}}$ ($3647.13$ versus $3607.97\;\mathrm{kg\,m^{-3}}$ at $y = 635.8\;\mathrm{km}$) and baking $+\mathbf{100.7\;\mathrm{MPa}}$ permanently into `adiabatic_pressure` at the 410 depth regardless of $\tau_p$. In `DampNone`, `Bimpl`, and `Bexpl`, subtracting the ambient block load during `ComputeProfile::initialize()` gave $\hat{P}_\mathrm{init}(z) = +\Delta\rho_\mathrm{block}\,g\,\mathrm{overlap}(z)$ (up to $+588.6\;\mathrm{MPa}$), baking $+\mathbf{20.41\;\mathrm{MPa}}$ into `adiabatic_pressure`; in `Cap1e8`, `Cap2e8`, and `Cap4e8`, clamping that load to $100, 200, 400\;\mathrm{MPa}$ baked $+\mathbf{5.07}, +\mathbf{9.77}, +\mathbf{12.95\;\mathrm{MPa}}$ into `adiabatic_pressure`.

2. **`Bexpl` placed the bulk-viscosity force in the continuity equation instead of the momentum equation (Critical).**
   In `include/aspect/material_model/interface.h:1228-1232` and `source/simulator/assemblers/stokes.cc:398`, `rhs_p` is the right-hand side source for conservation of mass:

$$
-\nabla\cdot\vec{u} = \frac{1}{\rho}\frac{D\rho}{Dt} + \mathrm{rhs}_p
$$

   Setting `stokes_rhs_out->rhs_p[q] = (bulk_viscosity_explicit / viscosity) * div_u` in `nh-kinetics.cc:193-194` injected or removed mass in proportion to $\nabla\cdot\vec{u}$ rather than adding a viscous normal stress to the momentum equation.

3. **`Bexpl` had an alternating sign, dimensionless units, and linear extrapolation amplification (Critical).**
   Putting $+\frac{\zeta}{\eta}\nabla\cdot\vec{u}_\mathrm{lin}^n$ into $-\nabla\cdot\vec{u}^n = \dots + \mathrm{rhs}_p$ forced

$$
\nabla\cdot\vec{u}^n \approx -\frac{\zeta}{\eta}\nabla\cdot\vec{u}_\mathrm{lin}^n
$$

   Dividing $\zeta$ ($\mathrm{Pa\,s}$) by $\eta_\mathrm{ref}$ ($\mathrm{Pa\,s}$) produced a dimensionless ratio ($\zeta/\eta_\mathrm{ref} = 0.01$ at $10^{19}\;\mathrm{Pa\,s}$ and $0.1$ at $10^{20}\;\mathrm{Pa\,s}$) rather than a stress in $\mathrm{Pa}$. Worse, during Stokes assembly `in.strain_rate` is evaluated at `current_linearization_point` (`source/simulator/assembly.cc:655`), which for steps $n > 1$ is the linearly extrapolated velocity $\vec{u}_\mathrm{lin}^n = (1 + \Delta t_n/\Delta t_{n-1})\vec{u}^{n-1} - (\Delta t_n/\Delta t_{n-1})\vec{u}^{n-2}$ (`source/simulator/helper_functions.cc:2046-2058`). For an alternating mode $\nabla\cdot\vec{u}^{n-1} = -\nabla\cdot\vec{u}^{n-2}$ at constant $\Delta t$, linear extrapolation triples the amplitude ($\nabla\cdot\vec{u}_\mathrm{lin}^n = 3\nabla\cdot\vec{u}^{n-1}$), adding $3\zeta/\eta_\mathrm{ref}$ directly to the alternating-mode gain.

4. **`Bimpl` omitted $\zeta$ from the Stokes preconditioner and Newton assemblers (High).**
   Commit `c81034dbf` on `agent/bulk-viscosity-chain` registered `StokesBulkViscosityTerm` only in `assemblers->stokes_system` (`source/simulator/assembly.cc:81-83`), leaving `StokesPreconditioner`, `StokesCompressiblePreconditioner`, `NewtonHandler::set_assemblers()`, `NewtonStokesCompressiblePreconditioner`, and `NewtonStokesCompressibleStrainRateViscosityTerm` without the $+\zeta(\nabla\cdot\vec{v}, \nabla\cdot\vec{u})$ term. Where $\zeta = 10^{20}\;\mathrm{Pa\,s}$ and viscosity approaches its floor $\eta_{\min} = 10^{19}\;\mathrm{Pa\,s}$, the true velocity block's compressional stiffness exceeds the preconditioner's by an order of magnitude.

5. **`NHKinetics::evaluate()` did not correct the driving pressure for bulk-viscosity normal stress when $\zeta > 0$ (Medium).**
   When bulk viscosity is active, the finite-element Stokes pressure $P$ differs from the mechanical mean normal stress experienced by the mineral assemblage by $\zeta\nabla\cdot\vec{u}$:

$$
P_\mathrm{mech} = P - \zeta\,\nabla\cdot\vec{u}
$$

   Using $P$ instead of $P_\mathrm{mech}$ in $\Delta G$ feeds the artificial bulk-viscosity pressure penalty $\zeta\nabla\cdot\vec{u}$ directly into the reaction driving force.

6. **`BulkViscosityOutputs::average()` and `AdditionalMaterialOutputsStokesRHS::average()` were unimplemented no-ops, and `nh-kinetics.cc` wrote dead `out.reaction_terms` for `density_field` (Medium).**
   Both `average()` overrides in `include/aspect/material_model/interface.h:1214-1219,1258-1263` contained `// TODO: not implemented` instead of calling `MaterialAveraging::average_property(...)`. In `nh-kinetics.cc:371-373`, `out.reaction_terms[q][projected_density_idx]` was populated even though `density_field` is a `prescribed field` updated via `PrescribedFieldOutputs` (`nh-kinetics.cc:382-384`) and `Use operator splitting = true` ignores `out.reaction_terms`.

Two items confirmed **not** to be bugs: `Bimpl`'s sign and $\frac{4}{3}\eta + \zeta$ longitudinal viscosity factor in `StokesBulkViscosityTerm` are exact (`StokesIncompressibleTerms` supplies $+2\eta\dot{\epsilon}:\dot{\epsilon}$ and `StokesCompressibleStrainRateViscosityTerm` supplies $-\frac{2}{3}\eta(\nabla\cdot\vec{v},\nabla\cdot\vec{u})$), and all reaction prefactors $Z$ and relaxation times $\tau_p$ use consistent SI seconds (`nh-kinetics.cc:360-361,378-379`).

## Resolution of the $\sim 100\;\mathrm{MPa}$ relaxed-pressure offset

In `simulation/results/relaxed-mean-check.csv`, all seven completed `Rel` runs ($\tau_p$ spanning four orders of magnitude from $10\;\mathrm{yr}$ to $100\;\mathrm{kyr}$) report a final mean `nonadiabatic_pressure` (`p - adiabatic_pressure + 588.6 MPa`) along the 410 slice of $-133.6$ to $-137.8\;\mathrm{MPa}$, compared with $-37.0\;\mathrm{MPa}$ for `DynpOff` (`S2`), $-57.4\;\mathrm{MPa}$ for `DynpOn_DampNone` (`S1`), and $-42.1, -46.8, -49.9\;\mathrm{MPa}$ for `Cap1e8`, `Cap2e8`, `Cap4e8`.

Inspecting the actual Stokes pressure $P$ and `relaxed_pressure` ($P_\mathrm{rel}$) in `point_values.txt` at probe 0 ($(x, y) = (500\;\mathrm{km}, 635.8\;\mathrm{km})$, just above the 410) proves that the physical Stokes pressure in the `Rel` runs is **not** offset at all:

| Run | $P(t=0)$ ($\mathrm{MPa}$) | $P_\mathrm{rel}(t=0)$ ($\mathrm{MPa}$) | $P(t=2.5\;\mathrm{Ma})$ ($\mathrm{MPa}$) | $P(t=5.0\;\mathrm{Ma})$ ($\mathrm{MPa}$) | $P_\mathrm{rel}(t=5.0\;\mathrm{Ma})$ ($\mathrm{MPa}$) | Reported $\langle\hat{P}\rangle_\mathrm{final}$ ($\mathrm{MPa}$) |
| :-- | --: | --: | --: | --: | --: | --: |
| `DynpOff_DampNone` (`S2`) | $13\,903.7$ | $15\,933.9$ (passive) | $13\,753.9$ | $13\,756.5$ | $5\,213.4$ (passive) | $-37.00$ |
| `DynpOn_DampNone` (`S1`) | $13\,925.4$ | $15\,933.9$ (passive) | $13\,754.0$ | $13\,757.1$ | $5\,278.0$ (passive) | $-57.41$ |
| `DynpOn_DampRel3.156e11` (`S7`) | $13\,999.0$ | $15\,933.9$ | $13\,754.7$ | $13\,757.0$ | $13\,754.2$ | $-137.68$ |

At $t = 2.5\;\mathrm{Ma}$ and $t = 5.0\;\mathrm{Ma}$, the true Stokes pressure $P$ at $(500\;\mathrm{km}, 635.8\;\mathrm{km})$ agrees across `DynpOff` ($13\,756.5\;\mathrm{MPa}$), `DampNone` ($13\,757.1\;\mathrm{MPa}$), and `Rel3.156e11` ($13\,757.0\;\mathrm{MPa}$) to within **$0.6\;\mathrm{MPa}$** ($< 0.005\%$), and $P_\mathrm{rel}$ tracks $P$ to within $2.8\;\mathrm{MPa}$.

The entire $-100.7\;\mathrm{MPa}$ discrepancy in reported `nonadiabatic_pressure` (`p - adiabatic_pressure`) — as well as the $-20.41\;\mathrm{MPa}$ offset in `DampNone` and the $-5.07, -9.77, -12.95\;\mathrm{MPa}$ offsets in `Cap1e8`, `Cap2e8`, `Cap4e8` — is the static startup error $\Delta\bar{P}_\mathrm{adiab}(z_{410})$ from Bug 1 above:

- At $t = 0$, before `relaxed_pressure` relaxes, both the Stokes solve at step 0 and `ComputeProfile::initialize()` see the same unrelaxed initial field $P_\mathrm{rel,init}(y) = 2.0\times 10^9 + 3900\,g\,(10^6 - y)$, so both $P(t=0)$ and $\bar{P}_\mathrm{adiab}$ at the 410 are inflated by $\sim 95\text{--}101\;\mathrm{MPa}$ ($13\,999.0$ versus $13\,903.7\;\mathrm{MPa}$ at $y = 635.8\;\mathrm{km}$) and their difference $P(t=0) - \bar{P}_\mathrm{adiab}$ cancels out at step 0 (`mean_initial_MPa = 94.13 MPa` versus `94.26 MPa`).
- Once $t \gg \tau_p$, $P_\mathrm{rel}$ relaxes to $P$, the extra density compression disappears, and $P$ converges to the true settled pressure ($13\,757.0\;\mathrm{MPa}$). Because `ComputeProfile` never recomputes `pressures[i]` after startup, its cached `adiabatic_pressure` remains permanently $+100.7\;\mathrm{MPa}$ too high, shifting $P - \bar{P}_\mathrm{adiab}$ by $-100.7\;\mathrm{MPa}$ in every `Rel` run independent of $\tau_p$.

Guarding `dynamic_pressure = 0.0` while `!this->get_adiabatic_conditions().is_initialized()` in `nh-kinetics.cc` ensures that every run integrates the exact same uncorrupted 1D reference adiabat $\bar{P}_\mathrm{adiab}(z)$, and referencing postprocessed dynamic pressure against that common uncorrupted reference adiabat removes the artificial offset across all existing runs.

## Why relaxation and decoupling work

Unlike bulk viscosity (which increases $M = \frac{4}{3}\eta + \zeta$ and amplifies both $a$ and $b$), pressure relaxation (`Rel`), pressure capping (`Cap`), and Gibbs pressure decoupling (`DynpDens`: `dynp-density = true`, `dynp-gibbs = false`) reduce the loop gain directly:

1. **Gibbs decoupling (`DynpDens`)**: Setting $\Delta G = \Delta\bar{G} - \hat{T}\Delta\bar{S}$ sets $\kappa = \partial\dot{X}/\partial\hat{P} = 0$ and therefore $b = 0$, breaking the kinetic feedback loop completely while retaining $\bar{\beta}\hat{P}$ in density (`manuscript.md:259-261`). Because $a = M\bar{\beta}/\Delta t \approx 0.036 \ll 1/2$, the remaining equation-of-state compressibility recursion $p^n = -a(p^{n-1} - p^{n-2})$ is damped ($|\lambda_-| \approx \sqrt{a} \approx 0.19 < 1$).
2. **Relaxed driving pressure (`Rel`)**: Filtering the driving pressure through

$$
\frac{DP_\mathrm{rel}}{Dt} = \frac{P - P_\mathrm{rel}}{\tau_p}
$$

   attenuates the step-to-step alternating mode ($\omega \sim \pi/\Delta t$) by the first-order low-pass transfer factor

$$
G(\tau_p, \Delta t) \approx \frac{\Delta t}{\Delta t + \tau_p}
$$

   reducing the effective kinetic gain to $b_\mathrm{eff}(\tau_p) = b\,\Delta t / (\Delta t + \tau_p)$ and the effective compressibility lag gain to $a_\mathrm{eff}(\tau_p) = a\,\Delta t / (\Delta t + \tau_p)$. Once $\tau_p \gtrsim 2\,b\,\Delta t \approx 1\text{--}10\;\mathrm{kyr}$, $2a_\mathrm{eff} + b_\mathrm{eff} < 1/2$, suppressing short-wavelength oscillations to $0.3\text{--}7\;\mathrm{MPa}$ while preserving slow physical pressure variations over the $\sim 419\;\mathrm{kyr}$ phase-transformation and $\sim 3\;\mathrm{Ma}$ flow-relaxation timescales (`notes/key-results.md:11,19`).
3. **Pressure capping (`Cap`)**: Clamping $|\hat{P}| \le P_{\max}$ limits the maximum amplitude of the limit cycle to $\mathcal{O}(P_{\max})$, but leaves the linearized gain $2a + b$ inside $[-P_{\max}, +P_{\max}]$ untouched. As mesh refinement or smaller CFL increases $a$ and $b_\mathrm{eff}$, small-amplitude oscillations inside the cap grow faster and saturate at the cap boundary across more cells, explaining why `Cap2e8`'s short-wavelength oscillation grows from $4.3\;\mathrm{MPa}$ at `Res5` to $47.8\;\mathrm{MPa}$ at `Res6` and $138.7\;\mathrm{MPa}$ at `Res7` (`notes/key-results.md:13`).

## Implemented solutions

1. **Startup adiabat guard in `nh-kinetics.cc`**: Keep `dynamic_pressure = 0.0` whenever `!this->get_adiabatic_conditions().is_initialized()` so that `AdiabaticConditions::ComputeProfile::initialize()` integrates an identical, unperturbed 1D reference profile $\bar{P}_\mathrm{adiab}(z)$ across all damping and feedback modes.
2. **Common reference adiabat in postprocessing**: Reference $\hat{P}$ in `extract_timeseries.py`, `extract_lateral_pressure.py`, and `plot_depth_window.py` against the uncorrupted reference adiabat (`DynpOff` at matching resolution, with fallback to analytical depth interpolation) so that existing Barkla2 outputs are scored without the startup `adiabatic_pressure` bias.
3. **Mechanical pressure correction in `nh-kinetics.cc`**: When implicit or explicit bulk viscosity $\zeta > 0$ is active and `in.strain_rate` is available, evaluate the mechanical pressure $P_\mathrm{mech} = P - \zeta\nabla\cdot\vec{u}$ so that $\Delta G$ and $\rho$ see the mean normal stress rather than the unadjusted finite-element pressure.
4. **Momentum-equation assembly for `Bexpl`**: Add `rhs_div_u` (isotropic stress tested against $\nabla\cdot\vec{v}$ in the momentum equation, units $\mathrm{Pa}$) to `AdditionalMaterialOutputsStokesRHS<dim>` in ASPECT (`include/aspect/material_model/interface.h`, `source/simulator/assemblers/stokes.cc`, `source/simulator/assemblers/newton_stokes.cc`) and set `stokes_rhs_out->rhs_div_u[q] = -bulk_viscosity_explicit * div_u` in `nh-kinetics.cc`, retiring the broken `rhs_p` continuity mass source.
5. **Preconditioner, Newton, and material-averaging support for `Bimpl` in ASPECT**: Include $+\zeta(\nabla\cdot\vec{v}, \nabla\cdot\vec{u})$ in `StokesCompressiblePreconditioner`, `NewtonStokesCompressiblePreconditioner`, and `NewtonStokesCompressibleStrainRateViscosityTerm`, scale the pressure Schur complement in `StokesPreconditioner` by $1/(\eta + \zeta)$, register bulk-viscosity assemblers in `NewtonHandler::set_assemblers()`, and implement `BulkViscosityOutputs::average()` and `AdditionalMaterialOutputsStokesRHS::average()`.
6. **Decoupled dynamic-pressure modes (`DynpOn`, `DynpDens`, `DynpOff`)**: Extend `project.mk` and `simulation/local.mk` so `DynpDens` (`dynp-density = true`, `dynp-gibbs = false`) isolates the kinetic feedback ($b = 0$, $a > 0$) alongside `DynpOn` ($a > 0$, $b > 0$) and `DynpOff` ($a = 0$, $b = 0$).

Sources: `aspect` branch `agent/bulk-viscosity-chain`; `simulation/plugins/nh-kinetics.{cc,h}`; `simulation/results/point_values.txt`; `simulation/results/relaxed-mean-check.csv`; `simulation/results/pressure-history-summary.csv`; `notes/key-results.md`; `notes/benchmark-design.md`.
