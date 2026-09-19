"""Print the idea funnel: how a 144-name universe becomes a handful of ideas.

Answers "only five ideas?" with the actual counts at every gate rather than an
assertion. Run it as::

    .venv/bin/python tools/funnel.py --limit 144

Screening every name costs several network calls each, so it is slow; ``--limit``
trades coverage for time. The tool reports what it actually screened, so a partial
run is never mistaken for a full one.
"""

from __future__ import annotations

import argparse
import collections
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fig import discover  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=30, help="how many names to screen")
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--max-price", type=float, default=discover.DEFAULT_MAX_PRICE)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also filter on missing option chains and loss-making, as an earlier "
        "version did (off by default: that data can be wrong)",
    )
    parser.add_argument("--watchlist", nargs="*", default=[])
    args = parser.parse_args()

    cap = None if args.max_price <= 0 else args.max_price

    print("=" * 78)
    print("STAGE 0: build the candidate pool (three free entry points)")
    print("=" * 78)
    pool = discover.universe(watchlist=args.watchlist)
    by_source = collections.Counter()
    for row in pool:
        for source in row.get("sources") or []:
            by_source[source] += 1
    print(f"  pool: {len(pool)} names")
    for source, count in by_source.most_common():
        print(f"    {source:10} {count:4}")

    priority = {"watchlist": 0, "earnings": 1, "screener": 2}
    pool.sort(key=lambda r: min(priority.get(s, 9) for s in r["sources"]))
    selected = pool[: args.limit]
    print(f"\n  screening {len(selected)} of {len(pool)} (watchlist first, then earnings, then screener)")

    print()
    print("=" * 78)
    print("STAGE 1: screen each name (light facts only -- no option chains yet)")
    print("=" * 78)
    rows = []
    started = time.time()
    for index, candidate in enumerate(selected, start=1):
        row = discover.screen_symbol(candidate["symbol"])
        row["sources"] = candidate["sources"]
        rows.append(row)
        flag = ""
        if row.get("error"):
            flag = f"  ERROR {row['error'][:40]}"
        elif not row.get("has_options"):
            flag = "  no options"
        elif not row.get("structure_available"):
            flag = "  no usable expiry pair"
        print(
            f"  [{index:3}/{len(selected)}] {row['symbol']:6} "
            f"${row.get('price') or 0:>9,.2f}  "
            f"rev30 {row.get('revisions_net_30d')}  "
            f"px30 {row.get('price_change_30d')}{flag}",
            flush=True,
        )

    print()
    print("=" * 78)
    print("STAGE 2: the only gate left is the price cap")
    print("=" * 78)
    tally = collections.Counter()
    caveats = collections.Counter()
    survivors = []
    for row in rows:
        if row.get("error"):
            tally["failed to screen (network/data)"] += 1
            continue

        # Recorded, not filtered. These come from free endpoints and a bad response
        # looks identical to a genuine absence, so deleting names on them would
        # silently remove real ideas.
        if not row.get("has_options"):
            caveats["no listed options reported"] += 1
        elif not row.get("structure_available"):
            caveats["no usable expiry pair for the next 3 catalysts"] += 1
        if row.get("fwd_pe") is None or (row.get("fwd_pe") or 0) <= 0:
            caveats["loss-making (fwd PE not meaningful)"] += 1

        if args.strict:
            if not row.get("has_options") or not row.get("structure_available"):
                tally["[strict] no usable option structure"] += 1
                continue
            if row.get("fwd_pe") is None or row["fwd_pe"] <= 0:
                tally["[strict] loss-making"] += 1
                continue

        price = row.get("price") or 0
        if cap is not None and price >= cap:
            tally[f"share price at or above the ${cap:,.0f} cap"] += 1
            continue
        direction, score, components = discover._score(row)
        row["score"], row["direction_hint"] = score, direction
        if score < 25:
            tally["score below the triage floor (25)"] += 1
            continue
        survivors.append(row)

    for reason, count in tally.most_common():
        print(f"  {count:4}  FILTERED: {reason}")
    print(f"  {len(survivors):4}  PASSED")

    print()
    print("  recorded as caveats, NOT filtered (the data can be wrong):")
    for reason, count in caveats.most_common():
        print(f"  {count:4}  {reason}")

    print()
    print("=" * 78)
    print("STAGE 3: score the survivors (additive, inspectable)")
    print("=" * 78)
    survivors.sort(key=lambda r: -r["score"])
    for row in survivors:
        _, _, components = discover._score(row)
        detail = "  ".join(f"{k} {v}" for k, v in components.items() if v)
        print(
            f"  {row['symbol']:6} {row.get('direction_hint','?'):5} "
            f"score {row['score']:5.1f}   {detail}"
        )

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"  universe            {len(pool)}")
    print(f"  screened            {len(rows)}")
    print(f"  passed all gates    {len(survivors)}")
    print(f"  elapsed             {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
