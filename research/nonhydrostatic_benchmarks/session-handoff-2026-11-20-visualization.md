# Session handoff — 2026-11-20: visualization overhaul, dense steps landing

Branch `agent/initial-benchmark`, HEAD `80e2e13`. Prior handoff:
`session-handoff-2026-11-19-ambient.md` (still the only other research file;
all older handoffs + raw OpenAlex JSON retired in `a4f9c05`).

## Run state

- 7 of 18 runs complete with full 21-step solutions (42 files each: 5 box +
  2 sink — box undamped/Bimpl/Bexpl/Rel/CFL0.35, sink Cap/Rel11).
- 11 still at 0 solutions (all node036 MPI-fabric deaths, resubmitted):
  box DynpOff, Cap, CFL1.4; sink DynpOff, undamped, Bimpl19, Bimpl20,
  Bexpl, Rel10, CFL0.25, CFL1.0. No-feedback controls (B2/S2) are in this
  batch — nominal re-derivation (~383 km sink expected) stays blocked.
- `TIMESTEPS` expanded 5 → all 21 outputs in `project.mk`; dense sync LANDED
  for the 7 good runs (user ran it — agent SSH to Barkla is denied, so all
  future syncs must run user-side). The 11 missing pick up 21 steps automatically.
- Next when ready: `timeseries` → `meshes` → full chain on 21 steps, then
  nominal re-derivation from new S2, forced re-mesh, `make scaling`.

## Good-batch science (5-step era; holds, gains resolution with 21 steps)

- Box Res5: undamped 47.7 MPa p2p, flat 1–10 Myr; CFL0.35 identical (step
  independence proven). Bimpl 52.3 (+9%), Bexpl 47.2 (no effect),
  Rel 406.6 MPa frozen-in −406 MPa low. Fronts +10.6 km (Rel +11.7).
- Sink Res6 (Cap + Rel11): peaks 1237/1267 MPa at 0.5 Myr → ~1140/1178 by
  5 Myr; fronts +26–28 km → +20 km. Depth profiles put dG=0 at ~381 km in
  BOTH suites (supports ~383 km sink nominal).
- Real signals: transient + excursion + nonlinear-damping distortion (old
  static On-Off displacement was reference artifact — see ambient handoff).

## Visualization overhaul (all verified by re-render)

- Labels: math shorthand with units in parens (`$\hat{P}$`,
  `$\hat{\rho}$`, `$\vec{u}_y$`, `$dG$`, `$\dot{X}$`, `$\xi$`, `$V_p$`,
  `$u_\mathrm{rms}$`, `$\Delta P$`); no figure titles; no raw variable
  names in axes. R: `expression(V[p] ~ "(km/s)")`, `Highest~dot(X)`,
  `Resolution 5/6` facets, plain damping names with units.
- Names: modules (`summarize_pressure_history`, `plot_depth_window`,
  `plot_depth_profiles`, `plot_mesh_step_sensitivity`,
  `plot_bulk_damping_check`), figures (`pressure-history-*`,
  `point-pressure-*`, `mean-flow-speed-*`, `depth-profiles-*`,
  `depth-window-*`, `mesh/step_sensitivity`, `bulk-damping-check-*`,
  `pressure-history-summary.csv`), CSV columns (`largest_range_MPa`,
  `mean_flow_speed_m_yr`, ...), target `pressure-waves` → `pressure-history`.
- Depth-window figure: exact-aspect panels (no white space), depth ticks on
  panels (313/363/413) and context (0–1000), in-panel time text, box 4th
  column = Particle Path (advected dot + arrow), sink 4th = true block
  shape (scatter, not bbox), snug 4th column.
- Mesh tiles carry the ambient correction now (sink ±656 MPa, neutral far
  field); probe plots show point-$\Delta P$ from t=0; depth profiles 11×5,
  lw 2.2.
- `config.py` `_FIELD_DEFAULTS` is a hand-aligned table (gated — see below).

## Gotchas (do not re-learn)

- Edit tool can eat trailing commas in that table → AST-check 9-tuples +
  `MeshConfig()` import after every touch (it broke the file once, silently).
- ruff `fmt: off/on` works ONLY at statement level (docs: Format
  suppression) — in-expression markers are no-ops. Markers now wrap the
  whole assignment; file-level pyproject exclude was tried and reverted.
- Never run two mesh renders concurrently (PIL reads half-written PNGs).
  `R visualize` triggers meshes via MESH_CSV deps — serialize with python runs.
- `plot_mesh` skips existing PNGs — delete tiles to force re-render after
  label changes. R `plot_exists` is forced via `FORCE_REWRITE=true`.
- `make sync-barkla` cannot run agent-side (SSH denied); always user-side.
- CSV renames (`largest_range_MPa`, `mean_flow_speed_m_yr`) require fresh
  `extract_timeseries` before any plot step.
