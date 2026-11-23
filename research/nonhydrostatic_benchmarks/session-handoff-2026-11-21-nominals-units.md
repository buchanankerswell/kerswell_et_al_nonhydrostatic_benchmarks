# Session handoff — 2026-11-21: nominals, CFL0.25 removal, strip fix, units/style

Branch `agent/initial-benchmark`, HEAD `d2d9640`, tree clean. Prior handoffs:
`session-handoff-2026-11-19-ambient.md` (physics) and
`session-handoff-2026-11-20-figure-polish.md` (pipeline/true-depth/constants,
through `2e90ac1`). This file covers `d220b43..d2d9640` (8 commits).

## Run state

- 17 registered runs (CFL0.25 removed, see below); all 17 have full
  21-step solutions. The dead `...CFL0.25/` directory is still on disk
  (1 pvtu + failed log) but unregistered and ignored by the pipeline.
- `make -C python visualize` + `make -C R visualize tables` are green.

## What changed (oldest first)

1. `d220b43` nominals re-derived: box 373100→379943, sink 362700→379957
   (dG=0 on B2/S2, static across 21 outputs; ~380 km shared ambient
   adiabat). Controls re-centered to +3.2/+2.7 km; full chain rebuilt.
2. `a8b029b` dropped sink CFL0.25 from the set (17 runs now). It blows up
   deterministically on resubmission (t≈1e5 s, velocity 0.09→22 m/yr,
   ASPECT aborts on negative density*c_P); CFL0.5/1.0 twins run clean.
   Scaling rests on S1 vs CFL1.0 + intact box pair.
3. `b60b65c` **ambient-ramp sign fix + 9-note viz batch.** The block-load
   overlap ramped the wrong way inside the block (`y - bot` instead of
   `top - y`), painting a static orange/purple strip on every sink
   pressure panel. Fixed in plugin + 5 python copies; sink datum
   regenerated (≤16 km shift in-block). Reported results unaffected:
   error lives at 125–275 km, kinetics at ~380 km use the correct full
   overlap. Tiles autocrop whitespace + 24 px gaps; box renders use
   aspect-matched 576×1920 window with scaled fonts; depth profiles
   tight with outside legend; window titles all normal, insets +12%
   retitled Domain, taller colorbars, all-980 tick bug fixed (m/km
   mixup); `(dimensionless)` removed; per-variant unique colors
   (None grays + navy controls, python/R hex-synced); gutter-log
   hygiene across benchmarks/.
4. `c75ab2a` SI everywhere; `--nominal-m` (awk shim gone); **rate-unit
   mislabel fixed** (file 1/s plotted as 1/Ma in depth profiles, R
   structure, tables — now scaled by `S_PER_MA`); scripts log only
   out-files, no directory lines.
5. `52be25b` constants to project.mk: `REF_DENSITY`, `DEPTH_WINDOW_STEPS`,
   `TRACE_X_STEP_LIMIT` (+`--x-step-limit-m` plumbing),
   adiabat inputs; every script arg carries `[units]`; mk units in prose
   (inline `# unit` tags poison make values with trailing space —
   verified clean via dry-run).
6. `224e3c2` curved brackets for units throughout (kept `[]` only for code
   syntax and optional-arg markers like `[cfl]`).
7. `46a160d` consistent notation, then `d2d9640` Ma/ka reversal: durations
   Ma, rates 1/Ma (`S_PER_MA`, `time_ma` keys, `time_largest_Ma`,
   `rate410_per_Ma`); `R/utils/constants.R` holds `s_per_ma` (R analogue
   of config.py); exponents ruff-canonical `e03` (no plus; UID-embedded
   Z values frozen); table Z scientific (`4.44e-04`); table headers and
   postprocessed columns carry units (`rate410_per_s`,
   `vmax410_m_per_s`, `hatT410_K`).

## Gotchas (do not re-learn)

- ruff format strips `+` from exponents (`150e+03`→`150e03`) and AST-checks
  after every touch; `fmt: off/on` is statement-level only.
- Never put trailing comments on `:=` lines in make: the spaces become
  part of the value (`Mg100     .tsv`). Units live in prose above.
- `plot_mesh` skips existing PNGs and tiles skip existing outputs — delete
  generated PNGs/tiles dirs to force re-render (scoped python delete, not
  `rm`). Never run concurrent mesh renders.
- `extract_timeseries`/`summarize` skip missing runs cleanly (exit 0).
- File `dG_driving_0` in the 125–275 km band still carries the old
  flipped plugin reference (needs Barkla rebuild + rerun to fix; cosmetic,
  unflagged, transition band unaffected).
- `simulation/configs` are untracked build artifacts; `PRM` text changed
  (`0.7` vs `7e-01`) — regenerate on Barkla via `make -C simulation configs`.

## Next

1. Barkla: rebuild plugin (ambient-ramp fix) before the next sweep.
2. Manuscript rewrite on the transient-wave narrative (draft/ untouched;
   still stale 660 content).
3. Open: R keeps its own palette copy (values match python); `x_buffer` /
   `anomaly_threshold` stay code-local (dead branch for isothermal suites).
