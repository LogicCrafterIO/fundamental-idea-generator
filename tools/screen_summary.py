#!/usr/bin/env python3
"""Turn `fig screen` output into a master Markdown summary.

Why this exists
---------------
`fig screen` prints its ranked table to stdout and writes **no file at all**: it is
read-only by design, so a screen leaves nothing behind but a terminal scrollback.
That makes the run impossible to cite a week later, and the ranking impossible to
compare against a later one.

Usage::

    .venv/bin/fig screen --limit 500 --top 60 > /tmp/screen.log 2>&1
    .venv/bin/python tools/screen_summary.py /tmp/screen.log -o research/screen-2026-10-01.md

Reads a log (or stdin with ``-``) and writes Markdown. yfinance 404 chatter for bad
symbols from Nasdaq's screener is ignored: it lands on stderr in the log and does not
match the table.

The side in the table is the screener's **revision hint**, not a recommendation --
see the README's "core screen" section.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path


def parse(text: str) -> dict:
    lines = text.splitlines()

    rules = next((line for line in lines if line.startswith("rules:")), "")
    pool = next((line for line in lines if line.startswith("pool ")), "")

    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("TICKER"))
        end = next(i for i, line in enumerate(lines) if line.startswith("Gated out"))
    except StopIteration:
        raise SystemExit(
            "could not find the ranked table in this input -- pass the output of "
            "`fig screen`, not something else"
        )

    # The gated header carries the *names* gated; the lines under it are the reasons.
    match = re.search(r"Gated out \((\d+)\)", lines[end])
    gated_names = int(match.group(1)) if match else 0

    rows: list[list[str]] = []
    for line in lines[start + 2 : end]:
        if not line.strip():
            continue
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) >= 8:
            rows.append(parts)

    reasons: list[str] = []
    for line in lines[end + 1 :]:
        if line.startswith("Score components") or not line.strip():
            break
        if not line.startswith("Gated"):
            reasons.append(line.strip())

    longs = [row for row in rows if row[1] == "long"]
    shorts = [row for row in rows if row[1] == "short"]
    return {
        "rules": rules,
        "pool": pool,
        "rows": rows,
        "longs": longs,
        "shorts": shorts,
        "gated_names": gated_names,
        "reasons": reasons,
    }


def _table(rows: list[list[str]]) -> str:
    out = [
        "| # | Ticker | Side | Score | Fwd PE | P/S | 30D | Rev net | Earnings | Themes |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for index, row in enumerate(rows, start=1):
        cells = (row + [""] * 9)[:9]
        out.append(
            "| {i} | **{t}** | {side} | {score} | {pe} | {ps} | {move} | {rev} | "
            "{earn} | {themes} |".format(
                i=index,
                t=cells[0],
                side=cells[1],
                score=cells[2],
                pe=cells[3],
                ps=cells[4],
                move=cells[5],
                rev=cells[6],
                earn=cells[7],
                themes=cells[8],
            )
        )
    return "\n".join(out)


def render(data: dict, *, as_of: str | None = None, command: str | None = None) -> str:
    date = as_of or datetime.date.today().isoformat()
    rows, longs, shorts = data["rows"], data["longs"], data["shorts"]
    gated = data["gated_names"]
    reasons = "\n".join(f"- {reason}" for reason in data["reasons"]) or "- _none_"

    return f"""# Screen summary -- {date}

Master record of one full-universe `fig screen` run. `fig screen` prints to stdout
and writes no file, so this summary is the run's durable trace; the raw log is the
source of truth.

## Rules applied

`{data['rules']}`

- `{data['pool']}`

Screening is **model-free**: it costs time and no API quota. The share-price cap is a
tradeability rule (a position has to fit the ~$4,500 capital unit) and the market-cap
floor keeps the option requirement satisfiable.

## Result

**{len(rows)} ranked** -- **{len(longs)} long** hints, **{len(shorts)} short** hints.
**{gated}** name(s) gated out before ranking.

### Longs ({len(longs)})

{_table(longs)}

### Shorts ({len(shorts)})

{_table(shorts)}

## Gated out ({gated} names)

{reasons}

## Notes

- A side is the screener's **revision hint** (the sign of the net consensus
  revision), not a recommendation. It is a triage filter, not an answer:
  `score_components` is returned for every candidate so a rank can be argued with.
- A blank or negative Fwd PE is a loss-maker whose multiple is meaningless; it was not
  used to rank the name.
- Defaults: **$150/share** cap, **$2B** market-cap floor, earnings within 10 days.
{f"- Regenerate with: `{command}`" if command else ""}

## What was generated from this screen

| batch | notes |
|---|---|
| the top of this table, by score | see [`README.md`](README.md) for the generated index |

Each generated note has a `.packet.json` beside it holding the exact evidence used.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("log", help="a log holding `fig screen` output, or - for stdin")
    parser.add_argument("-o", "--out", help="write here instead of stdout")
    parser.add_argument("--as-of", help="date to stamp the summary with (default: today)")
    parser.add_argument("--command", help="the command line to record in the summary")
    args = parser.parse_args()

    text = sys.stdin.read() if args.log == "-" else Path(args.log).read_text()
    markdown = render(parse(text), as_of=args.as_of, command=args.command)

    if args.out:
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown)
        print(f"wrote {target}", file=sys.stderr)
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
