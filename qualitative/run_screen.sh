#!/usr/bin/env sh
# The screen that produced qualitative/runs/screen-<date>.json.
#
# The two gates are the exercise defaults -- share price <= $100, market cap
# >= $1B -- and --limit only chooses how many names to print as the next batch.
set -e
here=$(cd "$(dirname "$0")" && pwd)
"$here/qs" screen --max-price 100 --min-market-cap 1b --limit 20 --order cap
