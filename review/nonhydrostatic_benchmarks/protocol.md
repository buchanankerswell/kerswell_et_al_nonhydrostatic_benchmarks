# Protocol: dynamic-pressure phase transitions + bulk-viscosity damping

**Research question**: How can dynamic (non-hydrostatic) pressure govern
phase transformations in compressible mantle-convection models without
generating spurious pressure oscillations — and what role can a bulk-viscosity
term (viscous-relaxation timescale) play, in a way compatible with ASPECT's
projected density approximation (PDA)?

**Search mode**: library plus search. Seed library (user-provided, on disk):
- Gassmoller et al. 2020, GJI 221, 1264-1280 (compressible formulations, PDA).
- Curbelo et al. 2019, JFM 873, 646-687 (viscous isentropic relaxation timescale
  tr = 4/3 eta / (gamma P0); explicit steps must resolve tr).

**Inclusion criteria**
- Peer-reviewed articles or preprints on: (a) compressible convection
  formulations and pressure oscillations; (b) bulk viscosity in geodynamics /
  fluid mechanics (incl. compaction / two-phase flow, viscoelastic relaxation);
  (c) non-hydrostatic stress effects on phase-transformation kinetics
  (MTZ, metastable wedges); (d) ASPECT implementations using dynamic pressure
  in phase transitions / reactions.
- Date: any; Language: English.

**Exclusion criteria**
- Purely seismological Clapeyron-slope measurements with no dynamical model.
- Engineering acoustics / shock physics.
- Incompressible (Boussinesq-only) studies with no compressibility discussion.

**Query log** (verbatim, with date + hit count):
- 2026-11-16 Q1 `filter works --search "bulk viscosity mantle convection" --filter "type:article"` → 3975 hits, top 15 screened. Verdict: keyword noise ("bulk" = bulk Earth); 0 include, 1 background (solid-solid phase transitions review).
- 2026-11-16 Q2 `filter works --search "dynamic pressure phase transition kinetics mantle" --filter "type:article"` → 2929 hits, top 15 screened. 2 include (subduction×kinetics 2009; Mariana kinetics 2014), 1 background (1982 phase boundaries).
- 2026-11-16 Q3 `filter works --search "nonhydrostatic stress phase transformation olivine kinetics" --filter "type:article"` → 60 hits, all 15 screened. 10 include (stress-governed transformation + weakening literature).
- 2026-11-16 Q4 `filter works --search "viscous relaxation compressible convection pressure oscillations" --filter "type:article"` → 2168 hits, top 15 screened. 0 include; 2 background (multifluid relaxation terms; variational compressible flow). Rest = astrophysical convection / CFD, excluded per criteria.
- 2026-11-16 Q5 `filter works --search "compaction viscosity melt migration two-phase flow" --filter "type:article"` → 2861 hits, top 10 screened. 3 include + 1 background (compaction/bulk-viscosity precedent).
- 2026-11-16 Abstract batches by OpenAlex ID (Q2/Q3/Q4/Q5 shortlists + 2 null-abstract evidence candidates for full-text follow-up). Corpus: 70 records after dedup (`corpus.json`).
- Screening decisions recorded in `synthesis.md` §Status; full per-record reasons deferred to manuscript stage.

**Screening**: title/abstract; reasons mandatory for exclusions.
