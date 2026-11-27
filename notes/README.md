# Notes

Working notes for the benchmark manuscript. They say what the current sink suite shows, what is still missing, and which figures present the argument. Numbers come from `simulation/results/*.csv`, rebuilt by `make postprocess`.

Old handoff files under `research/nonhydrostatic_benchmarks/` live only in git history. They use retired naming conventions and stale box/660 references; `notes/` supersedes them.

- [Feedback formulation](feedback-formulation.md) — the pressure-wave loop, the ASPECT melt comparison, and the Bimpl/Bexpl audit.
- [Key results](key-results.md) — measured effects and the open gaps.
- [Benchmark design](benchmark-design.md) — sweep expansion and ASPECT demos.
- [Key figures](key-figures.md) — which figures answer which question.
- [Session 2026-11-24](session-2026-11-24.md) — what changed and what comes next.
- [Session 2026-11-26](session-2026-11-26.md) — formulation audit, rendering, and the next checks.
- [Session 2026-11-27](session-2026-11-27.md) — formulation derivations, offset resolution, ASPECT/plugin bug fixes, and Batch D setup.

`AGENTS.md` at the repo root covers the layout and commands. `render-notes.sh` renders every note to `figs/*.html` with pandoc; pass `--force` to overwrite and `OUT_DIR` to change the destination.
