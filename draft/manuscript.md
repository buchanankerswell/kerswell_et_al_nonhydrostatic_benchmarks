<!-- Manuscript boilerplate for the nonhydrostatic benchmark study. Body text is a skeleton; title, abstract, and keypoints live in draft/agu.yaml. -->

# Abstract {.unnumbered #sec:abstract}

TODO: 150-word abstract. Nonadiabatic (dynamic) pressure feedback on 410 km phase-change kinetics in compressible ASPECT benchmarks; spurious oscillation magnitude; which damping treatments stabilise the transient at fixed physical mean; mesh and step convergence. Baseline is the undamped full-feedback run (S1); the no-feedback run (S2) is the physics reference.

\clearpage

# Plain Language Summary {.unnumbered #sec:plain-language-summary}

TODO: plain-language summary. Why compressible flow plus pressure-driven phase changes can ring numerically, and what the benchmark suite shows about fixing it.

# Keypoints {.unnumbered #sec:keypoints}

- TODO: spurious pressure oscillation exists with full feedback and collapses without it (S1 vs S2).
- TODO: damper ranking at fixed lateral mean (grid-band power vs S1).
- TODO: mesh and time-step convergence of the stabilised solution.

\clearpage

# Definition of Symbols {.unnumbered #sec:definition-of-symbols}

TODO: expand as equations land. Minimal working set for the benchmark narrative:

|Parameter|Symbol|Unit|Equations|
|:--------|:-----|:---|:--------|
|Pressure|$P$|Pa|TBD|
|Dynamic (nonadiabatic) pressure|$\hat{P}$|Pa|TBD|
|Density|$\rho$|kg m$^{-3}$|TBD|
|Velocity|$\vec{u}$|m s$^{-1}$|TBD|
|Viscosity|$\eta$|Pa s|TBD|
|Bulk viscosity|$\zeta$|Pa s|TBD|
|Relaxed pressure timescale|$\tau$|s|TBD|
|Pressure cap|$P_{\max}$|Pa|TBD|
|Kinetic prefactor|$Z$|K s$^{-1}$|TBD|

\clearpage

# Introduction {#sec:introduction}

TODO. Frame the three science questions: (1) how nonadiabatic pressure affects 410 (and by extension 520/660) phase transformations and seismic structure; (2) magnitude of the effect; (3) how to implement the feedback stably in compressible simulations.

Compressible ASPECT applies instantaneous volume/density changes in the continuity equation, forcing pressure and velocity in the Stokes solve to change instantaneously, while kinetic rates are driven by dynamic pressure [@gassmoller2020]. With zero bulk viscosity the loop has no volumetric resistance and rings. This benchmark suite isolates that loop in a sinking-block setup crossing the 410.

# Methods {#sec:methods}

TODO. Governing equations (compressible continuity, Stokes, energy, kinetics driven by $\hat{P}$); ambient reference; suite design.

## Benchmark suite {#sec:benchmark-suite}

TODO. Frozen at 25 registered sink UIDs (S1--S24 + CFL1.0 twin): core damping comparison at Z_MID Res6, Batch A resolvable taus + damped CFL0.25 rescue twins, Batch B bulk/cap sensitivity, Batch C Res7/Res5 mesh scaling. S1 (DynpOn DampNone) is the stability baseline; S2 (DynpOff DampNone) is the no-feedback physics reference. Transient steps 0--12 score stability; final states score structure.

## Damping treatments {#sec:damping-treatments}

TODO. None; implicit bulk $\zeta$; explicit bulk; relaxed pressure with timescale $\tau$ (resolvable window ~[30 yr, 100 kyr]; SI seconds in the plugin, model years in ASPECT); pressure cap. Pass criterion: cut transient grid-band (<20 km) power at fixed lateral mean vs S1.

## Metrics {#sec:metrics}

TODO. Lateral mean/std/p2p + long/mid/grid FFT bands (`lateral-pressure.csv`); pressure range history, reduction vs S1, error vs S2 (`pressure-history-summary.csv`); displacement/width/rate + thermal-kinetic split (`postprocessed.csv`); mesh/step sensitivity.

# Results {#sec:results}

TODO. Four required figure families:

1. Spurious oscillation existence: pressure-history S1 vs S2 + lateral profiles at the peak step.
2. Diminishment magnitude: lateral-oscillation summary (mean/std/grid vs step) + reduction/error table.
3. Timescales: reaction rate vs viscous relaxation (rate410, flow diminishment, $\tau$ window).
4. Convergence: mesh-step sensitivity (range vs Res and CFL) + depth-window compositions at fixed colour limits.

Central figures: lateral-oscillation summary, pressure history, mesh-step sensitivity. Still missing: rerun under fixed colour limits for all models, relaxed-mean bias check, crashed-run resubmit decisions.

# Discussion {#sec:discussion}

TODO. Which dampers hold the mean; why bulk fails; why cap is resolution-fragile; what the relaxed offset means; implications for 520/660 and for compressible implementation (bulk viscosity vs relaxed pressure vs cap).

# Conclusions {#sec:conclusions}

TODO. Three bullets answering the three science questions once the checks land.

# Acknowledgements {.unnumbered #sec:acknowledgements}

TODO.

# Data Availability {.unnumbered #sec:data-availability}

TODO: Zenodo dataset DOI + code repo (see `project.mk` `ZENODO_*`; currently TODO placeholders).

# Conflict of Interest {.unnumbered #sec:conflict-of-interest}

The authors declare there are no conflicts of interest for this manuscript.

\clearpage

# References {.unnumbered #sec:references}

::: {#refs}
:::
