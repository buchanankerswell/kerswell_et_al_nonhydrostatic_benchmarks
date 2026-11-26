#!/usr/bin/env bash
# Render every note in this directory to self-contained HTML with pandoc.
# Math is ordinary $...$ / $$...$$ and becomes MathML, so the pages need no
# network access. Output goes to figs/ by default; set OUT_DIR to override.
# Existing HTML is skipped unless --force is given.
set -euo pipefail

usage() {
  echo "usage: $(basename "$0") [--force] [--help]"
}

force=0
case "${1:-}" in
  --force) force=1 ;;
  --help|-h) usage; exit 0 ;;
  "") ;;
  *) echo "render-notes.sh: unknown argument: $1" >&2; usage >&2; exit 2 ;;
esac

notes_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$notes_dir/.." && pwd)"
out_dir="${OUT_DIR:-$repo_root/figs}"
header="$notes_dir/pandoc-header.html"
filter="$notes_dir/pandoc-math-in-code.lua"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "render-notes.sh: pandoc is required" >&2
  exit 1
fi
for required in "$header" "$filter"; do
  if [ ! -f "$required" ]; then
    echo "render-notes.sh: missing $required" >&2
    exit 1
  fi
done

mkdir -p "$out_dir"

for note in "$notes_dir"/*.md; do
  name="$(basename "$note" .md)"
  out="$out_dir/$name.html"
  if [ "$force" -eq 0 ] && [ -f "$out" ]; then
    echo "!! Warning: skip $out (exists; use --force)"
    continue
  fi
  title="$(grep -m1 '^# ' "$note" | sed 's/^# //' || true)"
  [ -n "$title" ] || title="$name"
  pandoc "$note" \
    --from=markdown --to=html5 --standalone --wrap=none \
    --math-method=mathml \
    --lua-filter="$filter" \
    --include-in-header="$header" \
    --metadata pagetitle="$title" \
    --output="$out"
  echo "-> $out"
done
