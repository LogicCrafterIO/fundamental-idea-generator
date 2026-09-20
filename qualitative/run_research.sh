#!/usr/bin/env sh
# The research run that produced qualitative/tickers/ and qualitative/themes/THEMES.md.
#
#   --limit 20       the top 20 names by market cap (coverage order, not a ranking)
#   --workers 5      five companies researched concurrently; the work is latency-bound
#   --refresh        re-research even where an artifact exists, so every artifact in a
#                    published batch came from the same prompts
#
# Re-running without --refresh costs nothing: existing artifacts are reused and only
# the rendering and theme merge are redone. To deepen the theme file rather than
# replace it, run a second wave with --start 20 (and again at 40, 60, ...).
set -e
here=$(cd "$(dirname "$0")" && pwd)
"$here/qs" research --limit 20 --workers 5 --refresh --start "${1:-0}"
