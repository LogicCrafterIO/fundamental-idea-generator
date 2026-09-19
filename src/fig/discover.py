"""Candidate discovery: decide which tickers deserve a writeup, and which side.

The core signal
---------------
Screening on "cheap" or "expensive" alone produces consensus ideas, and the
reference writeups are explicitly *not* consensus -- the ORCL note says so
outright ("I find it a bit hard to find non-consensus longs, stuff is getting
stupid expensive"). So the primary screen here is a **divergence**:

    fundamentals (consensus EPS revisions)  versus  price

Both references are exactly this shape:

* **ORCL** -- consensus EPS revisions *up* (4 up, 0 down over 30d) while the
  price is down more than 20%. Improving estimates into a falling price is the
  dislocation, and it argues **long**.
* **OMF** -- revisions *tilted lower* (6 up, 8 down) while the thesis expects
  charge-offs to worsen. Deteriorating estimates argue **short**.

Divergence is measurable from free data, it is inherently non-consensus (the
crowd is doing the opposite on one side of it), and it produces a *direction*
rather than just a ranking. It is a triage filter, not an answer -- the packet is
what a human or model then reasons over.

The second screen is **catalyst proximity**: an idea needs an event that forces
the market to re-rate. OMF's author is explicit -- "if NCO go from 7% now to 10%
in Feb or March earnings". Both references' structures are built around earnings
dates, so a candidate with no report inside its option horizon is hard to trade.

Scoring is deliberately additive and inspectable: every candidate carries
``score_components`` so a rank can be argued with.
"""

from __future__ import annotations

from datetime import date

from . import options, quants, themes
from .sources import nasdaq, yahoo


# --------------------------------------------------------------------------
# universe
# --------------------------------------------------------------------------


def universe(
    *,
    watchlist: list[str] | None = None,
    earnings_days: int = 10,
    screener_limit: int = 60,
    min_market_cap: float = 2e9,
    include_screener: bool = True,
) -> list[dict]:
    """Assemble the raw candidate pool with the reason each name surfaced.

    Three free entry points, because each finds a different kind of idea:

    * ``watchlist``    -- names the user already cares about.
    * ``earnings``     -- catalyst-driven; a dated event to trade around.
    * ``screener``     -- attention-driven; what the market is trading today.
    """
    found: dict[str, dict] = {}

    def add(symbol: str, **meta) -> None:
        symbol = (symbol or "").strip().upper()
        if not symbol or "." in symbol or "^" in symbol:
            return  # skip odd share classes and indices
        entry = found.setdefault(symbol, {"symbol": symbol, "sources": []})
        if meta.get("source") and meta["source"] not in entry["sources"]:
            entry["sources"].append(meta["source"])
        entry.update({k: v for k, v in meta.items() if v is not None and k != "source"})

    for symbol in watchlist or []:
        add(symbol, source="watchlist")

    try:
        for row in nasdaq.earnings_window(days=earnings_days, min_market_cap=min_market_cap):
            add(
                row["symbol"],
                source="earnings",
                name=row.get("name"),
                earnings_date=row.get("date"),
                session=row.get("session"),
            )
    except Exception:
        pass

    if include_screener:
        for exchange in ("NASDAQ", "NYSE"):
            try:
                for row in nasdaq.screener(exchange=exchange, limit=screener_limit):
                    if (row.get("market_cap") or 0) < min_market_cap:
                        continue
                    add(
                        row["symbol"],
                        source="screener",
                        name=row.get("name"),
                        pct_change=row.get("pct_change"),
                        market_cap=row.get("market_cap"),
                    )
            except Exception:
                continue

    return list(found.values())


# --------------------------------------------------------------------------
# screening a single name
# --------------------------------------------------------------------------


def screen_symbol(symbol: str) -> dict:
    """Pull the cheap facts needed to triage one candidate.

    Kept intentionally light -- no option chains -- so a few dozen names can be
    screened before paying for full packets on the survivors.
    """
    symbol = symbol.upper()
    out: dict = {"symbol": symbol}

    try:
        panel = quants.quants_panel(symbol)
    except Exception as exc:
        return {**out, "error": f"{type(exc).__name__}: {exc}"}

    out.update(
        {
            "name": panel.get("name"),
            "price": panel.get("price"),
            "market_cap": panel.get("market_cap"),
            "market_cap_human": panel.get("market_cap_human"),
            "fwd_pe": panel.get("fwd_pe"),
            "fwd_pe_1y": panel.get("fwd_pe_1y"),
            "ps": panel.get("ps"),
            "sector": panel.get("sector"),
            "eps_trend": panel["eps_trend"]["text"],
            "eps_trend_chg_7d": panel["eps_trend"]["change_7d_pct"],
            "eps_trend_chg_30d": panel["eps_trend"]["change_30d_pct"],
            "eps_revisions": panel["eps_revisions"]["text"],
            "revisions_net_30d": panel["eps_revisions"]["net_30d"],
            "next_earnings": (panel.get("next_earnings") or {}).get("next_date"),
        }
    )

    try:
        out["price_change_30d"] = yahoo.price_change_pct(symbol, 30)
    except Exception:
        out["price_change_30d"] = None
    try:
        out["price_change_90d"] = yahoo.price_change_pct(symbol, 90)
    except Exception:
        out["price_change_90d"] = None

    # News and themes: expensive, so tolerate failure.
    try:
        from .packet import collect_news

        news = collect_news(symbol, yahoo_limit=8, nasdaq_limit=8)
        story = themes.score_stories(news)
        out["news_count"] = len(news)
        out["news_specific"] = sum(1 for n in news if n.get("relevance", 0) >= 3)
        out["themes"] = [t["key"] for t in story["themes"][:4]]
        out["top_theme"] = story.get("top")
        out["headlines"] = [n.get("title") for n in news[:3]]
    except Exception:
        out["news_count"] = 0
        out["news_specific"] = 0
        out["themes"] = []
        out["headlines"] = []

    # Has a chain, and can a rule-consistent structure actually be built?
    expiries = []
    try:
        expiries = yahoo.expiries(symbol)
    except Exception:
        pass
    out["has_options"] = bool(expiries)
    out["optionable"] = bool(expiries)  # kept for backwards compatibility

    if expiries:
        try:
            pick = options.select_expiries_auto(symbol)
            out["structure_available"] = True
            out["structure_catalyst_index"] = pick["catalyst_index"]
            out["structure_short_expiry"] = pick["short"]
            out["structure_long_expiry"] = pick["long"]
            out["structure_catalyst"] = pick["catalyst"].isoformat()
        except Exception as exc:
            out["structure_available"] = False
            out["structure_error"] = str(exc)
    else:
        out["structure_available"] = False
        out["structure_error"] = "no listed options"

    out["direction_hint"], out["score"], out["score_components"] = _score(out)
    return out


def _score(row: dict) -> tuple[str, float, dict]:
    """Additive, inspectable triage score with a direction hint.

    Components (all bounded, all free-data derivable):

    ``divergence``   consensus revisions vs price move -- the core signal.
    ``catalyst``     an earnings report inside a tradeable window.
    ``salience``     how much name-specific news there is.
    ``tradeable``    options exist with a usable expiry pair.
    ``valuation``    multiple extremes, as a mild tilt only.
    """
    components: dict[str, float] = {}

    rev = row.get("revisions_net_30d")
    price_30 = row.get("price_change_30d")
    price_90 = row.get("price_change_90d")

    # ---- divergence ------------------------------------------------------
    divergence = 0.0
    direction = "long"
    if rev is not None and price_30 is not None:
        if rev > 0 and price_30 < 0:
            # Estimates rising, price falling: the classic long dislocation.
            divergence = min(40.0, 8.0 * min(rev, 5) + 0.6 * min(abs(price_30), 35))
            direction = "long"
        elif rev < 0 and price_30 > 0:
            # Estimates falling, price rising: the short dislocation.
            divergence = min(40.0, 8.0 * min(abs(rev), 5) + 0.6 * min(abs(price_30), 35))
            direction = "short"
        else:
            # Aligned, but a big move still means something is happening.
            divergence = min(12.0, 0.15 * abs(price_30))
            direction = "long" if rev >= 0 else "short"
    elif price_30 is not None:
        divergence = min(10.0, 0.15 * abs(price_30))
    components["divergence"] = round(divergence, 1)

    # A bigger 90-day move strengthens or weakens the same reading.
    if price_90 is not None and rev is not None:
        if (rev > 0 and price_90 < 0) or (rev < 0 and price_90 > 0):
            components["divergence"] += 6.0
            components["divergence"] = round(min(45.0, components["divergence"]), 1)
        elif abs(price_90) > 40:
            components["extended_move"] = round(min(8.0, (abs(price_90) - 40) * 0.2), 1)

    # ---- catalyst --------------------------------------------------------
    catalyst = 0.0
    if row.get("structure_available") and row.get("structure_catalyst"):
        try:
            days = (date.fromisoformat(row["structure_catalyst"]) - date.today()).days
            if 5 <= days <= 120:
                catalyst = 20.0 - min(10.0, abs(days - 45) * 0.2)
        except (ValueError, TypeError):
            pass
    components["catalyst"] = round(catalyst, 1)

    # ---- salience --------------------------------------------------------
    specific = row.get("news_specific") or 0
    components["salience"] = round(min(15.0, 3.0 * specific), 1)

    # ---- tradeable -------------------------------------------------------
    components["tradeable"] = 12.0 if row.get("structure_available") else 0.0

    # ---- valuation extremes ---------------------------------------------
    # Only meaningful for a profitable company; a negative or absurd multiple
    # (pre-revenue biotech P/S in the thousands) is noise, not a signal.
    valuation = 0.0
    fwd_pe = row.get("fwd_pe")
    if fwd_pe and fwd_pe > 0:
        if fwd_pe < 8:
            valuation += 5.0  # cheap enough to be a value trap or a bargain
        elif fwd_pe > 45:
            valuation += 5.0  # expensive enough that any miss hurts
    ps = row.get("ps")
    if ps and 0 < ps < 30 and ps > 15:
        valuation += 3.0
    components["valuation"] = round(valuation, 1)

    total = round(sum(components.values()), 1)
    return direction, total, components


# --------------------------------------------------------------------------
# ranking
# --------------------------------------------------------------------------


def rank_candidates(
    rows: list[dict],
    *,
    top: int = 15,
    min_score: float = 25.0,
    require_structure: bool = True,
    require_positive_pe: bool = True,
) -> list[dict]:
    """Sort screened rows by score, after gating out names the format can't hold.

    The format *requires* a Structuring section, so a name that cannot carry a
    rule-consistent spread cannot produce a writeup. Without this gate a
    pre-revenue biotech (huge P/S, no chain) outscores everything real -- which is
    exactly what happened before the gate existed. Likewise a **negative** forward
    PE means the company is loss-making, so "Fwd PE" is not a valuation signal and
    any cheap-versus-expensive argument built on it is meaningless.

    The gate distinguishes two very different failures, because conflating them
    hid real names: "no listed options" (genuinely unoptionable) versus "no
    tradeable expiry pair" (has a chain, but every nearby catalyst falls before
    the next monthly expiry). Early on, gating on the latter mislabelled COST,
    CTAS, AZO and PAYX as having no options at all.

    Both gates are on by default and can be relaxed for exploratory scans.
    """
    usable = []
    for row in rows:
        if row.get("error"):
            continue
        if require_structure:
            if not row.get("has_options"):
                row["gated"] = "no listed options"
                continue
            if not row.get("structure_available"):
                row["gated"] = "has options but no usable expiry pair for the next 3 catalysts"
                continue
        if require_positive_pe and (row.get("fwd_pe") is None or row["fwd_pe"] <= 0):
            row["gated"] = "loss-making (fwd PE not meaningful)"
            continue
        if (row.get("score") or 0) < min_score:
            row["gated"] = "below score floor"
            continue
        usable.append(row)

    usable.sort(key=lambda r: r["score"], reverse=True)
    return usable[:top]


def scan(
    *,
    watchlist: list[str] | None = None,
    limit: int = 25,
    top: int = 12,
    earnings_days: int = 10,
    include_screener: bool = True,
    require_structure: bool = True,
    require_positive_pe: bool = True,
) -> dict:
    """End-to-end triage: build a universe, screen it, rank it.

    ``limit`` caps how many names get screened, since each screen costs several
    network calls. Names from an explicit watchlist are always screened first.
    """
    pool = universe(
        watchlist=watchlist, earnings_days=earnings_days, include_screener=include_screener
    )

    priority = {"watchlist": 0, "earnings": 1, "screener": 2}
    pool.sort(key=lambda r: min(priority.get(s, 9) for s in r["sources"]))
    selected = pool[:limit]

    rows = []
    for candidate in selected:
        row = screen_symbol(candidate["symbol"])
        row["sources"] = candidate["sources"]
        rows.append(row)

    ranked = rank_candidates(
        rows,
        top=top,
        require_structure=require_structure,
        require_positive_pe=require_positive_pe,
    )
    gated = [r for r in rows if r.get("gated")]
    return {
        "pool_size": len(pool),
        "screened": len(selected),
        "ranked": ranked,
        "all_rows": rows,
        "gated": gated,
        "failures": [r for r in rows if r.get("error")],
    }
