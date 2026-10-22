"""Candidate discovery: decide which tickers deserve a writeup, and which side.

The core signal
---------------
The primary screen is the **consensus EPS revision** itself:

* **ORCL** -- revisions *up* (4 up, 0 down over 30d) argues **long**.
* **OMF** -- revisions *tilted lower* (6 up, 8 down) argues **short**.

The magnitude of the net revision sets the rank and its sign sets the side. It is
measurable from free data and it produces a *direction* rather than just a
ranking. It is a triage filter, not an answer -- the packet is what a human or
model then reasons over.

What this signal no longer does
-------------------------------
It used to be a **divergence** -- consensus revisions *versus* price -- so that a
name whose estimates improved into a falling tape, or deteriorated into a rising
one, outscored a name whose estimates and price agreed. That rewarded a
dislocation the crowd was on the other side of, which is what made the screen
non-consensus by construction.

It was removed because the price leg, not the revisions, was doing much of the
ranking: identical revision moves scored ~30 points apart depending only on the
direction of the tape, and 24 of 50 names in a real screen sat in the collapsed
"aligned" branch. **The cost is real and should be stated: a revision-following
rank is closer to consensus than a gap was.** The non-consensus character of an
idea now has to come from the reasons, not from the screen -- which the format
already demands, since `fig lint` rejects a reason that merely restates the screen
signal as a conclusion (`reason_valuation_only`, and the README's "a discount is
not a thesis").

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
# the two sizing rules that shape the pool
# --------------------------------------------------------------------------

# Ideas are capped by share price. The reason is practical, not stylistic: the
# reference structures size a position from a ~$4,500 capital unit against
# 100-share contracts, and a high-priced underlying breaks that arithmetic -- AZO
# at ~$2,855 had a single option contract costing $13,275, three times the unit.
# A $150 ceiling keeps a normal position tradeable inside the unit.
#
# This is the ONE gate on by default in :func:`rank_candidates`, because it is a
# tradeability rule rather than a judgement about the data.
DEFAULT_MAX_PRICE = 150.0

# The pool's market-cap floor. It is not a quality filter: it keeps the option
# requirement satisfiable, because microcaps rarely have listed strikes worth
# trading. `fig screen --min-market-cap` and `fig generate --min-market-cap` move
# it; the owner's tighter scans use $1B.
DEFAULT_MIN_MARKET_CAP = 2e9


# --------------------------------------------------------------------------
# universe
# --------------------------------------------------------------------------


def universe(
    *,
    watchlist: list[str] | None = None,
    earnings_days: int = 10,
    screener_limit: int = 60,
    min_market_cap: float = DEFAULT_MIN_MARKET_CAP,
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

        # A feed outage is already recorded inside the packet, not raised here; the
        # screen only wants the headlines it did get.
        news, _failures = collect_news(symbol, yahoo_limit=8, nasdaq_limit=8)
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

    ``revisions``    the consensus EPS revision -- the core signal, and the side.
    ``catalyst``     an earnings report inside a tradeable window.
    ``salience``     how much name-specific news there is.
    ``tradeable``    options exist with a usable expiry pair.
    ``valuation_fragility``  multiple extremes, as a mild tilt only.
    """
    components: dict[str, float] = {}

    rev = row.get("revisions_net_30d")

    # ---- revisions -------------------------------------------------------
    # Rank on the SIZE of the consensus revision; take the side from its sign.
    # Price deliberately does not enter the score.
    #
    # This used to reward a revision-versus-price *gap* and collapse to <=12 when
    # the two agreed. That made the rank a bet on the price leg rather than on the
    # estimates: two names with identical revision moves scored ~30 points apart
    # purely because one had the tape going its way, and half a screened universe
    # sat in the collapsed branch. The revision term below is the same one the old
    # formula used; only the price term and the branch structure are gone.
    revisions = 0.0
    direction = "long"
    if rev is not None:
        # Saturates at 5 net revisions -- the same term, and so the same ceiling,
        # the old formula's revision half used. (The 45 cap that used to sit here
        # was only reachable via the +6 price confirmation, which is gone.)
        revisions = min(40.0, 8.0 * min(abs(rev), 5))
        direction = "long" if rev >= 0 else "short"
    components["revisions"] = round(revisions, 1)

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
    #
    # A multiple only AMPLIFIES a signal that already exists; it never creates one.
    # Cheapness is not a reason to be long -- a stock at 7x is usually at 7x
    # because something is wrong -- and a premium is usually justified, so an
    # expensive name is not automatically a short either. This component used to
    # award a flat bonus for a low multiple, which biased the entire ranking toward
    # discounted names looking for an upward rerating. The tilt is now conditional
    # on which way estimates are already going:
    #
    #   falling + cheap  -> fragile; the discount is deserved, not a bargain
    #   falling + pricey -> vulnerable to a de-rating
    #   rising  + either -> no bonus; a cheap name that is rising needs a stated
    #                       mechanism before it is worth writing up
    #
    # The ceiling is low so valuation can never outrank the revisions signal.
    valuation = 0.0
    fwd_pe = row.get("fwd_pe")
    falling = (rev or 0) < 0
    if fwd_pe and fwd_pe > 0 and falling:
        if fwd_pe < 12:
            valuation += 3.0
        elif fwd_pe > 30:
            valuation += 4.0
    ps = row.get("ps")
    if ps and 15 < ps < 30 and falling:
        valuation += 2.0
    if valuation:
        components["valuation_fragility"] = round(valuation, 1)

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
    require_structure: bool = False,
    require_positive_pe: bool = False,
    max_price: float | None = DEFAULT_MAX_PRICE,
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

    The option and profitability gates are OFF by default, deliberately, on the
    owner's instruction. Both rest on data that can simply be wrong:

    1. **A missing chain may be a missing response.** These facts come from free
       endpoints, and a name that fails on a bad response is indistinguishable
       from one that genuinely has no chain. Filtering on possibly-corrupt data
       silently deletes real ideas, and the deletion is invisible in the output.
    2. **A missing option chain is not a missing idea.** Structuring is optional
       downstream: the note is written from the catalyst and the reasons, with the
       absent legs stated explicitly. A loss-making company can still have a dated
       catalyst and a clear reason to be short, and a negative forward PE only
       means "Fwd PE" is not a valuation signal -- it does not make the idea
       meaningless, as an earlier version of this docstring claimed.

    Both remain available as opt-in filters for a stricter scan, and both are
    recorded per row under ``caveats`` so a caller can still see which names carry
    them. The price cap is the one gate left on by default, because it is a
    tradeability rule rather than a judgement about the data.
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
        if max_price is not None and (row.get("price") or 0) >= max_price:
            row["gated"] = f"share price ${row.get('price')} is at or above the ${max_price:.0f} cap"
            continue

        # Not filtered any more, but recorded: these are the facts an earlier
        # version treated as disqualifying. Keeping them visible is the point --
        # the notes must state when a name has no usable chain or no meaningful
        # forward PE rather than quietly pretending the fact is not there.
        caveats = []
        if not row.get("has_options"):
            caveats.append("no listed options reported")
        elif not row.get("structure_available"):
            caveats.append("no usable expiry pair for the next 3 catalysts")
        if row.get("fwd_pe") is None or (row.get("fwd_pe") or 0) <= 0:
            caveats.append("loss-making (fwd PE not meaningful)")
        if caveats:
            row["caveats"] = caveats
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
    require_structure: bool = False,
    require_positive_pe: bool = False,
    max_price: float | None = DEFAULT_MAX_PRICE,
    min_market_cap: float = DEFAULT_MIN_MARKET_CAP,
) -> dict:
    """End-to-end triage: build a universe, screen it, rank it.

    ``limit`` caps how many names get screened, since each screen costs several
    network calls. Names from an explicit watchlist are always screened first.

    ``min_market_cap`` is applied twice and for the same reason both times: to the
    earnings calendar when the pool is built (microcaps rarely carry tradeable
    options) and to the screener rows. It is a *pool* filter, not a ranking input --
    a name below the floor is never added, so it cannot appear as "gated" either.
    """
    pool = universe(
        watchlist=watchlist,
        earnings_days=earnings_days,
        include_screener=include_screener,
        min_market_cap=min_market_cap,
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
        max_price=max_price,
    )
    gated = [r for r in rows if r.get("gated")]
    return {
        "pool_size": len(pool),
        "screened": len(selected),
        "ranked": ranked,
        "all_rows": rows,
        "gated": gated,
        "failures": [r for r in rows if r.get("error")],
        # The rules the pool was built under, so a run's coverage is auditable
        # rather than inferred from the numbers it happened to produce.
        "settings": {
            "max_price": max_price,
            "min_market_cap": min_market_cap,
            "earnings_days": earnings_days,
            "include_screener": include_screener,
            "require_structure": require_structure,
            "require_positive_pe": require_positive_pe,
            "limit": limit,
            "top": top,
        },
    }
