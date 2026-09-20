"""The universe: every listed name that passes the two quantitative gates.

There are exactly two numbers in this screener
----------------------------------------------
1. **Price <= $100.** A position-size rule, the same one the parent screener
   applies at $150: option contracts come in 100-share lots, so a high-priced
   underlying breaks the arithmetic of a normal capital unit. Here it is a
   *capability* gate -- "$100 screen" -- not a statement about the business.
2. **Market cap >= $1B.** A coverage gate. Industry research, trade press and
   segment reporting exist for billion-dollar businesses; below that a screen
   that only reads qualitative sources mostly returns silence, which is
   indistinguishable from "no trend found".

Nothing else is measured. No multiple, no estimate revision, no price momentum,
no earnings date. A name is in or out on those two numbers, and everything the
screener then says about it is qualitative.

Where the numbers come from
---------------------------
Nasdaq's public screener endpoint returns the whole list -- ~4,100 NASDAQ,
~2,700 NYSE, ~290 AMEX rows -- in three calls, each row carrying a last sale and
a market cap. That is what makes the gate affordable: the pool is built for
three HTTP requests rather than two thousand. yfinance is then the authority at
the point of writing a name up (:mod:`qts.profile`), because it is the source the
parent pipeline already trusts for market cap, and because a disagreement between
the two is worth seeing rather than hiding.

What the gates actually admit (2026-09-20): 882 NASDAQ, 1,134 NYSE and 26 AMEX
names -- 2,042 businesses, once the 163 rows that are preferred issues, notes,
warrants or funds rather than companies are removed by security type. That is far
more than any research run can cover, so :func:`select` caps the batch and says so
out loud. The cap is **not** a ranking: names are ordered by market cap, which is
one of the two permitted numbers, purely so that consecutive waves start with the
businesses that have the most research coverage.
"""

from __future__ import annotations

import random
import re
from datetime import date
from pathlib import Path

from fig.sources import nasdaq
from fig.util import human_money

# The two gates. Both are overridable from the CLI; these are the defaults the
# exercise was specified with.
DEFAULT_MAX_PRICE = 100.0
DEFAULT_MIN_MARKET_CAP = 1e9

EXCHANGES = ("NASDAQ", "NYSE", "AMEX")

# Symbols the pipeline cannot process: indices and units carry a suffixed symbol
# (``ABC^A``, ``ABC/WS``) that yfinance does not resolve.
_SYMBOL_JUNK = re.compile(r"[\^/$]")

# Nasdaq's list mixes securities in with businesses: a company with a preferred
# issue contributes several extra rows (Huntington Bancshares alone adds four),
# and they pass both gates comfortably. They are not businesses -- there is no
# revenue stream to extract and no demand to research -- so they are removed by
# security *type*, which is a definition of the universe rather than a judgement
# about a company.
#
# The parenthetical is stripped before matching, and that detail is the whole
# difficulty: ``Itau Unibanco ... American Depositary Shares (Each repstg 500
# Preferred Shares)`` is a real operating bank ADR, while ``Huntington Bancshares
# ... Depositary Shares, Each Representing 1/4,000th Interest in ... Perpetual
# Preferred Stock`` is not the bank. Both mention preferred shares; only the
# second one is a preferred issue, and the difference is whether the descriptor
# is inside the parenthesis. Checked against the live pool: the surviving drops
# are warrants (305 rows), closed-end funds (262), preferred issues and notes
# (~230) and true depositary-share lines (~60) -- and every ADR, MLP and class
# share is left in place.
_NON_COMMON = re.compile(
    r"""\bwarrants?\b
      | \bnotes?\s+due\b
      | \bsubordinated\b
      | \bperpetual\b
      | \bpreferred\s+(stock|shares|securities|units)\b
      | \bdepositary\s+shares?\b
      | \b\d+(\.\d+)?\s*%
      | \bZONES\b
      | \btrust\s+(certificates?|preferred)\b
      | \bcapital\s+trust\b
      | \bclosed[-\s]end\b
      | \bexchange[-\s]traded\b
      | \bETF\b
      | \bfund\b""",
    re.IGNORECASE | re.VERBOSE,
)
_PARENTHETICAL = re.compile(r"\([^)]*\)")

# Company-name noise stripped before de-duplicating share classes, so that
# Alphabet's two lines and Berkshire's two lines do not each get researched.
_NAME_NOISE = re.compile(
    r"\b(inc|incorporated|corp|corporation|co|company|cos|plc|ltd|limited|llc|holdings?|"
    r"group|the|class\s+[a-z]|series\s+[a-z0-9]+|common\s+stock|capital\s+stock|stock|"
    r"ordinary\s+shares?|american\s+depositary\s+shares?|depositary\s+shares?|ads|adr|"
    r"new|registered|shares?|units?|representing|limited\s+partner\s+interests?)\b",
    re.IGNORECASE,
)


# ...except that the same word appears inside the *real* security. "American
# Depositary Shares" is how nearly every foreign listing is named on NYSE and
# NASDAQ, and those are ordinary businesses with segment disclosure -- MUFG,
# Shell, Sony, TotalEnergies. So an ADR phrase is tested first and wins outright.
# Without this the type filter deleted about a thousand foreign businesses: an
# error far worse than leaving a preferred issue in, because the screener's whole
# value is breadth of industry, and much of that breadth is foreign.
_ADR = re.compile(
    r"\b(american\s+depositary\s+(shares?|receipts?)|(sponsored|unsponsored)\s+(adr|ads))\b",
    re.IGNORECASE,
)


def is_common_equity(name: str | None) -> bool:
    """Is this row a business, rather than a preferred, note, warrant or fund?

    The test runs on the name with parentheticals removed, so an ADR that merely
    *describes* preferred shares in a bracket survives -- and an ADR phrase
    anywhere in the name wins before the filter runs at all.
    """
    stripped = _PARENTHETICAL.sub(" ", name or "")
    if _ADR.search(stripped):
        return True
    return not _NON_COMMON.search(stripped)


def name_key(name: str | None) -> str:
    """A share-class-insensitive key for a company name.

    ``Alphabet Inc. Class A Common Stock`` and ``Alphabet Inc. Class C Capital
    Stock`` collapse to the same key, which is what keeps one business from being
    researched twice under two tickers.
    """
    text = _NAME_NOISE.sub(" ", name or "")
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def universe(
    *,
    max_price: float | None = DEFAULT_MAX_PRICE,
    min_market_cap: float | None = DEFAULT_MIN_MARKET_CAP,
    exchanges: tuple[str, ...] = EXCHANGES,
    screener_limit: int = 10000,
    common_equity_only: bool = True,
) -> dict:
    """Build the gated pool from Nasdaq's listed names.

    Returns ``{"rows", "duplicates", "excluded", "gates", "by_exchange"}``. Rows
    carry the two numbers and the reason the name qualified; ``excluded`` counts
    what the gates removed by cause, because a screen that reports only its
    survivors cannot be audited.
    """
    rows: dict[str, dict] = {}
    duplicates: list[dict] = []
    excluded = {"price": 0, "market_cap": 0, "no_price": 0, "symbol": 0, "security_type": 0}
    by_exchange: dict[str, int] = {}
    seen_names: dict[str, str] = {}

    for exchange in exchanges:
        try:
            listed = nasdaq.screener(exchange=exchange, limit=screener_limit)
        except Exception:
            # One exchange failing must not empty the pool; it is recorded by the
            # absence of its count below.
            continue

        for row in listed:
            symbol = (row.get("symbol") or "").strip().upper()
            if not symbol or _SYMBOL_JUNK.search(symbol):
                excluded["symbol"] += 1
                continue
            if common_equity_only and not is_common_equity(row.get("name")):
                excluded["security_type"] += 1
                continue

            price = row.get("last_sale")
            cap = row.get("market_cap")
            if price is None or price <= 0:
                excluded["no_price"] += 1
                continue
            if max_price is not None and price > max_price:
                excluded["price"] += 1
                continue
            if min_market_cap is not None and (cap or 0) < min_market_cap:
                excluded["market_cap"] += 1
                continue

            key = name_key(row.get("name")) or symbol
            if key in seen_names:
                # Two listings of one business: keep the larger, record the other.
                duplicates.append(
                    {
                        "symbol": symbol,
                        "name": row.get("name"),
                        "duplicate_of": seen_names[key],
                        "market_cap": cap,
                    }
                )
                if (cap or 0) > (rows[seen_names[key]].get("market_cap") or 0):
                    rows.pop(seen_names[key], None)
                    rows[symbol] = {
                        "symbol": symbol,
                        "name": row.get("name"),
                        "price": price,
                        "market_cap": cap,
                        "exchange": exchange,
                    }
                    seen_names[key] = symbol
                continue

            seen_names[key] = symbol
            rows[symbol] = {
                "symbol": symbol,
                "name": row.get("name"),
                "price": price,
                "market_cap": cap,
                "exchange": exchange,
            }
            by_exchange[exchange] = by_exchange.get(exchange, 0) + 1

    ordered = sorted(rows.values(), key=lambda r: r.get("market_cap") or 0, reverse=True)
    return {
        "rows": ordered,
        "duplicates": duplicates,
        "excluded": excluded,
        "by_exchange": by_exchange,
        "gates": {"max_price": max_price, "min_market_cap": min_market_cap},
        "count": len(ordered),
    }


def select(
    pool: list[dict],
    *,
    limit: int | None = 20,
    order: str = "cap",
    seed: int | None = None,
    start: int = 0,
) -> list[dict]:
    """Take a batch out of the pool, in an order that is stated rather than scored.

    ``order`` is ``cap`` (largest first -- the default, and the reason is
    coverage, not quality), ``name`` (alphabetical, a neutral sweep) or
    ``random`` (a seeded sample, for a wave that should not just be mega-caps).
    ``start`` skips into the ordered pool so later waves do not redo the first
    batch. **No ordering here is a ranking of the business**: there is no score,
    and the batch a name lands in says nothing about it.
    """
    ordered = list(pool)
    if order == "cap":
        ordered.sort(key=lambda r: r.get("market_cap") or 0, reverse=True)
    elif order == "name":
        ordered.sort(key=lambda r: (r.get("name") or r["symbol"]).lower())
    elif order == "random":
        random.Random(seed).shuffle(ordered)
    else:
        raise ValueError(f"unknown order {order!r} (cap, name, random)")

    sliced = ordered[max(0, start) :]
    return sliced if limit is None else sliced[:limit]


def describe(result: dict) -> str:
    """A short human summary of what the gates admitted."""
    gates = result["gates"]
    price = "no cap" if gates["max_price"] is None else f"<= ${gates['max_price']:.0f}"
    cap = "no floor" if gates["min_market_cap"] is None else f">= {human_money(gates['min_market_cap'])}"
    parts = [f"{result['count']} names pass (price {price}, market cap {cap})"]
    for exchange, count in sorted(result.get("by_exchange", {}).items()):
        parts.append(f"{exchange} {count}")
    excluded = result.get("excluded") or {}
    if excluded:
        parts.append(
            "excluded: "
            + ", ".join(f"{count} on {cause.replace('_', ' ')}" for cause, count in excluded.items() if count)
        )
    if result.get("duplicates"):
        parts.append(f"{len(result['duplicates'])} duplicate listings collapsed")
    return " | ".join(parts)


def run_path(root: Path, stamp: date | None = None) -> Path:
    """Where a screen snapshot is written, so a batch can be reproduced later."""
    day = (stamp or date.today()).isoformat()
    return root / "runs" / f"screen-{day}.json"
