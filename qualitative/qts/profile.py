"""One company's identity and its two numbers, from yfinance.

What comes out of here
----------------------
* ``description`` -- the company's own business summary, which is the raw
  material for the writeup's Description section. It is *detailed on purpose*:
  the parent pipeline distils a description down to four words because its
  product is a trade note. This screener's product is the opposite -- a reader
  who wants to know what the business actually does and where the money comes
  from, so the summary is carried nearly whole and the model is asked to make it
  more precise, not shorter.
* ``price`` and ``market_cap`` -- the only two numbers the screener uses, taken
  here from yfinance so that the writeup quotes the same source the parent
  pipeline quotes.

The gate conflict, and why it is reported instead of resolved
------------------------------------------------------------
The pool was built on Nasdaq's last sale and market cap, because that costs
three HTTP calls for two thousand names; yfinance is fetched one name at a time.
The two sources disagree often enough to matter -- a stale Nasdaq close, a share
count that moved -- and when they do, the name is **kept and flagged**, not
dropped. Dropping it would silently shrink the batch over a data discrepancy that
the reader can see and judge for themselves, and the whole point of publishing
the two numbers is that they are checkable.
"""

from __future__ import annotations

from fig.sources import yahoo
from fig.util import human_money

# How far yfinance and Nasdaq may differ on each number before it is worth
# printing as a conflict: a 2% price move or a 10% market-cap gap is a stale
# quote, not a different company.
PRICE_TOLERANCE = 0.02
CAP_TOLERANCE = 0.10


def fetch(symbol: str, *, listed: dict | None = None) -> dict:
    """Profile one symbol. Never raises for a missing field, only for a dead fetch.

    ``listed`` is the Nasdaq row the name came from, if there was one, used only
    to detect and report disagreement.
    """
    symbol = symbol.upper()
    profile = yahoo.profile(symbol) or {}
    valuation = yahoo.valuation(symbol) or {}

    price = valuation.get("price")
    market_cap = valuation.get("market_cap")

    conflicts = []
    if listed:
        listed_price = listed.get("price")
        if price and listed_price and abs(price - listed_price) / listed_price > PRICE_TOLERANCE:
            conflicts.append(f"price {price} vs Nasdaq {listed_price}")
        listed_cap = listed.get("market_cap")
        if market_cap and listed_cap and abs(market_cap - listed_cap) / listed_cap > CAP_TOLERANCE:
            conflicts.append(
                f"market cap {human_money(market_cap)} vs Nasdaq {human_money(listed_cap)}"
            )

    summary = (profile.get("summary") or "").strip()
    return {
        "symbol": symbol,
        "name": profile.get("name") or valuation.get("name") or (listed or {}).get("name"),
        "sector": profile.get("sector") or valuation.get("sector"),
        "industry": profile.get("industry") or valuation.get("industry"),
        "country": profile.get("country"),
        "website": profile.get("website"),
        "employees": profile.get("employees"),
        "summary": summary,
        "summary_words": len(summary.split()),
        "price": price,
        "market_cap": market_cap,
        "market_cap_human": human_money(market_cap),
        "exchange": valuation.get("exchange") or (listed or {}).get("exchange"),
        "nasdaq_price": (listed or {}).get("price"),
        "nasdaq_market_cap": (listed or {}).get("market_cap"),
        "gate_conflicts": conflicts,
        # The gates as re-checked against yfinance. A conflict is a flag, not a
        # rejection -- see the module docstring.
        "passes_price_gate": None if price is None else price <= 100.0,
        "passes_cap_gate": None if market_cap is None else market_cap >= 1e9,
    }
