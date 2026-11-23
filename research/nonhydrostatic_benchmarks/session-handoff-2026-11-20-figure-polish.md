# Session handoff — 2026-11-20: figure pipeline, true depth, constants

Branch `agent/initial-benchmark`, HEAD `0dad29b`, tree clean. Prior handoffs:
`session-handoff-2026-11-19-ambient.md` (physics baseline) and
`session-handoff-2026-11-20-visualization.md` (overhaul + dense steps).
This file supersedes the latter for everything after `c8f0fa1`.

## Run state (unchanged)

- 7 of 18 runs have 21-step solutions (42 files each): 5 box
  (undamped/Bimpl/Bexpl/Rel/CFL0.35) + 2 sink (Cap/Rel11).
- 11 still at 0 (node036 MPI-fabric deaths, resubmitted): box DynpOff,
  Cap, CFL1.4; sink DynpOff, undamped, Bimpl19, Bimpl20, Bexpl, Rel10,
  CFL0.25, CFL1.0. No-feedback controls (B2/S2) still missing, so sink
  nominal re-derivation (~383 km observed, now ~407 km true) stays blocked.
- User runs `make sync-barkla` (agent SSH denied); missing runs pick up
  21 steps automatically via TIMESTEPS.

## What changed since c8f0fa1 (commits, oldest first)

1. `1015b72` dash filenames: bulk/mesh/step plots + seismic CSVs
   (`seismic-profile-<UID>-t<N>-representative.csv`); R reader updated;
   verified R loads all 7 models.
2. `72fe4ae` depth-window joins `make visualize`: new `depth-window`
   target (all 18 UIDs × set0/set1, skips missing solutions);
   `visualize` now pulls meshes, setup, pressure-history, diagnostics,
   scaling, depth-window — every current fig has a producing target.
3. `fee0f4d` depth-window outputs carry the full UID
   (`depth-window-<UID>-set{0,1}.png`); short slugs deleted.
4. `7fc976d` 9-note visualization pass (all re-rendered + inspected):
   highest→Max, (-)→(dimensionless), standard damping colors
   (`DAMP_COLORS` mirrors R `damp_pal`) + `bench_label` everywhere,
   legends inside-if-clear else outside, depth profiles packed with one
   shared y, window domain schematic as lower-right inset titled Model
   Domain with bold headers + 50% colorbars + suite-global clims
   (`compute_window_clims.py` → `depth-window-clims.json`), empty
   pending panels say "no data yet", bulk log ticks plain decimals,
   mean-flow linear, R seismic legend outside + duplicate linetype scale
   removed, 294 xi tiles re-rendered for the new label.
5. `50abb33` shared plot pieces into `python/simulation/mesh/config.py`
   (style, palette, labels); `common.py` keeps loaders + UID parsing;
   dead `uid_label` removed. (Also fixed: setup/domains.py imported
   style from common — broke on refactor, caught immediately.)
6. `9bfba44` true depth axes: model top is 2 GPa (measured in solutions,
   not 10). New versioned `simulation/data/depth-datum.tsv` maps model
   pressure through the BurnMan isentrope (sink excludes block load):
   top 63 km, box nominal 373→416 km, sink 363→407 km, bottom ~980 km.
   Depth profiles/windows, setup sketches, R seismic
   (`true_depth_km` column, reference band at profile 422.6 km) all use
   it via `transitions.load_depth_datum`. Named constants stay in model
   coords; only axes change.
7. `740431f` project.mk constants into every script via CLI flags
   (gravity, block top/bot, nominals, depth-corr, surface gravity,
   Z anchors incl. R). Mesh preprocessing carries them as dataclass
   fields; defaults mirror project.mk for standalone runs.
8. `0dad29b` trimmed provenance comments; physics-only comments kept.

## Gotchas (do not re-learn)

- ruff `fmt: off/on` works ONLY at statement level; in-expression
  markers are no-ops. Table AST-check (9-tuples) after every touch.
- This matplotlib labels log *minor* ticks in sci notation: plain
  formatters need setting on both major and minor axes.
- `fig.legend(loc="outside ...")` + `tight_layout` misplaces into panels;
  prefer `ax.legend` inside clear corners.
- Never run concurrent mesh renders (PIL reads half-written PNGs); R
  `visualize` triggers meshes via CSV deps — serialize.
- `plot_mesh` skips existing PNGs: delete tiles to force re-render.
- `extract_timeseries`/`summarize` skip missing runs cleanly (exit 0).
- R `z_levels` vector was dead (matcher used literals) — now wired to
  CLI args with numeric-space matching kept.
- Mesh tiles were silently dense (21 steps, 294 xi PNGs) — check counts,
  not assumptions, before bulk deletes.

## Next

1. User runs `make sync-barkla` when jobs land; verify 18 `.run` markers.
2. `make -C python timeseries meshes` + full chain on 21 steps.
3. Re-derive nominals from new S2; `make scaling`; rebuild window/band
   figures (global clims auto-update); shared scales will shift.
4. Manuscript rewrite on the transient-wave narrative (separate work).
5. Open: R `z` tolerances + `RHO=4100` + mesh `x_step_limit` + UID/Res
   parsing remain hardcoded (not project.mk vars); R keeps its own
   palette copy (values match python).
