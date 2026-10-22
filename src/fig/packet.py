"""The **evidence packet**: everything known about one candidate, in one object.

The packet is the contract between data and prose. Nothing downstream of this
module touches the network, so a writeup can always be re-rendered, audited or
diffed from a saved packet, and a bad number can be traced back to the exact
upstream call that produced it (see the ``provenance`` list).

A packet deliberately carries *more* than a writeup needs. The reference writeups
are short because the author discarded most of what they knew -- so the raw
evidence has to be present for that discarding to be possible.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from . import catalyst as catalyst_mod, options, quants, research as research_mod, themes
from .sources import nasdaq, yahoo
from .util import human_money


# --------------------------------------------------------------------------
# news
# --------------------------------------------------------------------------


def _dedupe_news(items: list[dict]) -> list[dict]:
    """Merge feeds, dropping near-duplicate headlines.

    The same story syndicates across publishers with slightly different titles,
    so compare on a normalised token set rather than exact strings.
    """
    def fingerprint(title: str) -> frozenset[str]:
        words = re.sub(r"[^a-z0-9 ]", " ", (title or "").lower()).split()
        return frozenset(w for w in words if len(w) > 3)

    seen: list[frozenset[str]] = []
    out = []
    for item in items:
        title = item.get("title") or ""
        if not title:
            continue
        fp = fingerprint(title)
        if not fp:
            continue
        # Jaccard overlap above 0.6 counts as the same story.
        if any(len(fp & prev) / max(1, len(fp | prev)) > 0.6 for prev in seen):
            continue
        seen.append(fp)
        out.append(item)
    return out


def _recency_key(item: dict) -> str:
    for field in ("published", "created", "ago"):
        value = item.get(field)
        if value:
            return str(value)
    return ""


def collect_news(
    symbol: str,
    *,
    yahoo_limit: int = 12,
    nasdaq_limit: int = 15,
    include_web: bool = False,
    web_per_query: int = 5,
) -> tuple[list[dict], list[dict]]:
    """Merge Yahoo's per-symbol feed with Nasdaq's topic feed.

    Returns ``(items, failures)``. Yahoo gives genuine per-name coverage; Nasdaq
    adds market-wide context that merely touches the ticker. Both are kept and
    tagged with a ``relevance`` score so the writer can tell a company-specific
    story from a sector ripple.

    A feed that errors is recorded in ``failures`` and the note is built from the
    feeds that answered. The asymmetry is deliberate: a 403 from one free endpoint
    is a condition of *that endpoint* -- it carries no claim about the company --
    so letting it drop the name loses a note over an outage. A real run lost six
    of ten names exactly that way, on Nasdaq's news feed alone. The failure is
    carried on the packet and printed by the renderer, so the thinner evidence is
    visible rather than left to be inferred from a short source list.

    ``include_web`` adds Ollama web-search results. It is **off by default**
    because screening calls this once per candidate, and three searches per name
    across a universe is slow and wastes quota; packet building turns it on.
    """
    # The company's common name is needed to spot analyst-role mentions
    # (see :func:`_relevance`); failure here is not fatal.
    try:
        company_name = yahoo.profile(symbol).get("name")
    except Exception:
        company_name = None

    items: list[dict] = []
    failures: list[dict] = []

    def _add(source: str, fetch) -> None:
        try:
            found = fetch()
        except Exception as exc:  # noqa: BLE001 - one feed's outage is not the note's
            failures.append({"source": source, "error": f"{type(exc).__name__}: {exc}"})
            return
        for item in found or []:
            items.append({**item, "relevance": _relevance(symbol, item, company_name)})

    _add("yahoo", lambda: yahoo.news(symbol, limit=yahoo_limit))
    _add("nasdaq", lambda: nasdaq.news_for_symbol(symbol, limit=nasdaq_limit))

    if include_web:
        try:
            items.extend(web_stories(symbol, company_name, per_query=web_per_query))
        except Exception as exc:  # noqa: BLE001 - search is additive, as elsewhere
            failures.append({"source": "ollama_search", "error": f"{type(exc).__name__}: {exc}"})

    merged = _dedupe_news(items)
    for item in merged:
        item["themes"] = themes.tag_text(f"{item.get('title','')} {item.get('summary','')}")
    # Most relevant first, then most recent.
    merged.sort(key=lambda i: (-i.get("relevance", 0), _recency_key(i)), reverse=False)
    return merged, failures


# Phrases that put a company in the *analyst* role rather than making it the
# subject of the story.
_ANALYST_ROLE = re.compile(
    r"\b(says|said|is bullish|is bearish|favors|favours|keeps faith|stays bullish|"
    r"launches coverage|initiates coverage|starts coverage|upgrades|downgrades|"
    r"price target|target (cut|raised|falls|rises)|sees|expects|previews|"
    r"weighs in|on why|is betting|picks)\b",
    re.IGNORECASE,
)


def _relevance(symbol: str, item: dict, company_name: str | None = None) -> int:
    """0-3 score for how much this story is actually about ``symbol``.

    Name matching alone is not enough for research houses. Jefferies (JEF) is
    itself a broker, so headlines like "McDonald's target falls to $325, but
    Jefferies keeps faith" contain the ticker's name while being *about*
    McDonald's -- every "company-specific" JEF story was one of these. Where the
    name appears only in an analyst role, the story is demoted to 1 (a mention).
    """
    symbol = symbol.upper()
    title = (item.get("title") or "").upper()
    primary = (item.get("primary_symbol") or "").upper()
    related = [str(s).upper() for s in (item.get("related_symbols") or [])]

    # Does the ticker's own name appear in analyst role?
    analyst_role = False
    if company_name:
        first_word = company_name.split()[0]
        if first_word and first_word.upper() in title:
            analyst_role = bool(
                _ANALYST_ROLE.search(item.get("title") or "")
            )

    if primary == symbol:
        return 1 if analyst_role else 3
    if symbol in title:
        return 1 if analyst_role else 3
    if related and symbol in related:
        if analyst_role:
            return 1
        return 2 if len(related) <= 8 else 1
    return 0


def web_stories(
    symbol: str, company_name: str | None, *, per_query: int = 5
) -> list[dict]:
    """Web-search evidence, normalised into the news shape.

    Search snippets are long-form and often carry an explicit date in the body
    ("Sept 18 (Reuters) - ..."), so a date is recovered from the text where
    possible; otherwise the item sorts as undated rather than pretending to be
    fresh.
    """
    from .sources import ollama

    if not ollama.has_key():
        return []

    raw = ollama.search_stories(symbol, company_name, per_query=per_query)
    out = []
    for item in raw:
        if item.get("error"):
            continue
        published = _date_from_text(f"{item.get('title','')} {item.get('content','')}")
        out.append(
            {
                "title": item["title"],
                "publisher": item.get("publisher"),
                "url": item.get("url"),
                "summary": (item.get("content") or "")[:600],
                "published": published,
                "source": "ollama_search",
                "query": item.get("query"),
                # Search is query-targeted, so a result naming the company is
                # on-topic by construction; without the name it is only context.
                "relevance": _relevance(symbol, item, company_name),
                "themes": themes.tag_text(f"{item.get('title','')} {item.get('content','')[:400]}"),
            }
        )
    return out


# Matches "Sept 18", "19 September 2026", "2026-09-18", "Friday, 19 Sep 2026".
_DATE_PATTERNS = (
    re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"),
    re.compile(
        r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{4})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})\b",
        re.IGNORECASE,
    ),
    # Dateless form, very common in wire copy: "Sept 18 (Reuters) - ...". The year
    # is assumed to be the current one, which is right for news search results and
    # is only used for recency ordering, never quoted as a fact.
    re.compile(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})\b(?!\s*,?\s*\d{4})",
        re.IGNORECASE,
    ),
)

_MONTHS = {
    m: i
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1
    )
}


def _date_from_text(text: str) -> str | None:
    """Best-effort ISO date from a snippet, or ``None``."""
    text = text or ""

    match = _DATE_PATTERNS[0].search(text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    match = _DATE_PATTERNS[1].search(text)
    if match:
        month = _MONTHS.get(match.group(2)[:3].lower())
        if month:
            return f"{match.group(3)}-{month:02d}-{int(match.group(1)):02d}"

    match = _DATE_PATTERNS[2].search(text)
    if match:
        month = _MONTHS.get(match.group(1)[:3].lower())
        if month:
            return f"{match.group(3)}-{month:02d}-{int(match.group(2)):02d}"

    match = _DATE_PATTERNS[3].search(text)
    if match:
        month = _MONTHS.get(match.group(1)[:3].lower())
        if month:
            # Yearless: assume the current year (recency ordering only).
            return f"{date.today().year}-{month:02d}-{int(match.group(2)):02d}"
    return None


# --------------------------------------------------------------------------
# peers
# --------------------------------------------------------------------------


def peer_multiples(symbols: list[str]) -> list[dict]:
    """Valuation table for a peer set.

    The reference writeups argue by comparison -- ORCL's 17.7 forward PE against
    GOOG's 25, its ~7x P/S against SNOW's 20x. Those comparisons are only valid
    if every name is quoted on the same basis, which is why both PE bases and
    P/S are returned.
    """
    rows = []
    for sym in symbols:
        try:
            val = yahoo.valuation(sym)
        except Exception:
            continue
        rows.append(
            {
                "symbol": sym.upper(),
                "name": val.get("name"),
                "price": val.get("price"),
                "market_cap": val.get("market_cap"),
                "market_cap_human": human_money(val.get("market_cap")),
                "fwd_pe_0y": val.get("fwd_pe_0y"),
                "fwd_pe_1y": val.get("fwd_pe_1y"),
                "trailing_pe": val.get("trailing_pe"),
                "ps": val.get("ps"),
                "ev_ebitda": val.get("ev_ebitda"),
                "revenue_growth": val.get("revenue_growth"),
            }
        )
    return rows


# --------------------------------------------------------------------------
# packet
# --------------------------------------------------------------------------


def build_packet(
    symbol: str,
    *,
    peers: list[str] | None = None,
    include_structures: bool = True,
    directions: tuple[str, ...] = ("long", "short"),
    catalyst_index: int = 0,
    capital: float = options.DEFAULT_CAPITAL,
    include_web: bool = True,
    include_trends: bool = True,
) -> dict:
    """Assemble everything known about ``symbol`` for idea generation."""
    symbol = symbol.upper()

    try:
        profile = yahoo.profile(symbol)
    except Exception:
        profile = {"symbol": symbol}

    panel = quants.quants_panel(symbol)
    news, news_failures = collect_news(symbol, include_web=include_web)
    story = themes.score_stories(news)

    packet: dict = {
        "symbol": symbol,
        "as_of": date.today().isoformat(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "profile": profile,
        "quants": panel,
        "quants_lines": quants.quants_lines(panel),
        "fundamental_deltas": quants.fundamental_deltas(symbol),
        "eps_yoy": quants.eps_yoy(symbol),
        # The comparisons without which a sequential move reads as a trend: the same
        # quarter a year earlier, the fiscal year, and whether a deal landed in the
        # period. Paychex's May quarter fell 11.2% sequentially and grew 12.5% year
        # over year, and a note reported only the first half.
        "yoy_deltas": quants.yoy_deltas(symbol),
        "annual_deltas": quants.annual_deltas(symbol),
        "deal_activity": quants.deal_activity(symbol),
        "consensus_bar": quants.consensus_bar(panel),
        "news": news,
        # Which feeds were down when this packet was built. Kept on the packet so a
        # note written from a partial feed is auditable after the fact, and so the
        # renderer can say so in the note rather than leaving it to be noticed.
        "news_failures": news_failures,
        "story": story,
        "peer_pairings": themes.theme_pairing([t["key"] for t in story["themes"]]),
        "next_earnings": panel.get("next_earnings"),
        "catalyst": catalyst_mod.build_catalyst(symbol),
        "forward_trends": (
            research_mod.forward_trends(
                symbol,
                profile.get("name"),
                None,
                profile.get("summary"),
            )
            if (include_web and include_trends)
            else {"queries": [], "results_count": 0, "trends": [], "dropped": []}
        ),
        "provenance": [
            "yfinance Ticker.info (price, market cap, multiples, business summary)",
            "yfinance Ticker.eps_trend / eps_revisions (consensus drift, 7d & 30d buckets)",
            "yfinance Ticker.option_chain (leg premiums, open interest)",
            "yfinance Ticker.news + api.nasdaq.com news/topic/articlebysymbol (headlines)",
            "api.nasdaq.com company financials frequency=2 (quarterly statements)",
            "yfinance quarterly and annual statements (same-quarter-last-year and "
            "fiscal-year comparisons, goodwill and intangibles steps)",
            "api.nasdaq.com calendar/earnings + analyst/earnings-forecast (catalyst, consensus)",
            "ollama.com api/web_search (current reporting, when a key is configured)",
            "ollama.com api/web_search + v1/chat/completions (forward end-market trends, "
            "each kept only if its supporting quote is found in the retrieved text)",
        ],
    }

    if peers:
        packet["peers"] = peer_multiples([symbol] + [p for p in peers if p.upper() != symbol])

    if include_structures:
        structures = {}
        for direction in directions:
            try:
                structure = options.build_structure(
                    symbol, direction, catalyst_index=catalyst_index, capital=capital
                )
                structures[direction] = {
                    **structure.as_dict(),
                    "advice": options.suggest_short_adjustment(structure),
                    "credit_ladder": options.credit_ladder(structure),
                }
            except Exception as exc:  # a chain may not support the idea
                structures[direction] = {"error": f"{type(exc).__name__}: {exc}"}
        packet["structures"] = structures

    # The register of everything a reason can cite. Built last, because it indexes
    # the packet; stored on the packet, because the ids the writer was shown have
    # to be recoverable later to check what it cited.
    packet["sources"] = source_catalogue(packet)
    packet["trailing_vs_consensus"] = trailing_vs_consensus(packet)

    return packet


# --------------------------------------------------------------------------
# prompt context
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# sources
# --------------------------------------------------------------------------

# Every source below is a page a reader can open. That is the point: a reason is
# only checkable if the claim points at the evidence behind it, and a source that
# cannot be opened is not a source. Provider URLs are derived from the symbol
# rather than stored, so they stay correct for any ticker.
_YAHOO_QUOTE = "https://finance.yahoo.com/quote/{sym}"
_YAHOO_STATS = "https://finance.yahoo.com/quote/{sym}/key-statistics/"
_YAHOO_ANALYSIS = "https://finance.yahoo.com/quote/{sym}/analysis/"
_YAHOO_OPTIONS = "https://finance.yahoo.com/quote/{sym}/options/"
_NASDAQ_FINANCIALS = "https://www.nasdaq.com/market-activity/stocks/{low}/financials"
_NASDAQ_EARNINGS = "https://www.nasdaq.com/market-activity/stocks/{low}/earnings"

# How many feed headlines get their own citable source, and are printed in the
# prompt. A packet carries 17-25 of them, and this is deliberately above that: an
# earlier cap of 10 kept fourteen headlines out of the prompt entirely, which both
# starved the writer of evidence it used to have and made the notes written before
# the cap look unsourced. The limit exists only to bound a pathological feed.
MAX_NEWS_SOURCES = 40


def _publisher(url: str | None, fallback: str | None = None) -> str | None:
    if not url:
        return fallback
    host = str(url).split("//", 1)[-1].split("/", 1)[0]
    host = host[4:] if host.startswith("www.") else host
    return host or fallback


def source_catalogue(packet: dict, *, max_news: int = MAX_NEWS_SOURCES) -> list[dict]:
    """Every evidence source in the packet, numbered so a reason can cite it.

    A reason that states a fact without a source is not checkable, and this repo's
    whole claim is that its reasoning is checkable. So each block of evidence is
    registered here with an id, a provider, a real URL and the text a cited figure
    should be findable in, and the writer cites ids rather than copying URLs --
    copying is where models invent them.

    The catalogue is built from the packet alone, so it is deterministic: the ids
    the writer is shown are the ids used to resolve its citations, which is what
    makes a fabricated id detectable instead of silently accepted.

    Order is stable and grouped: the tool's own fundamentals first (they are what
    most reasons rest on), then headlines, then search research, then the chain.
    """
    symbol = (packet.get("symbol") or "").upper()
    low = symbol.lower()
    q = packet.get("quants") or {}
    entries: list[dict] = []

    def add(kind: str, label: str, url: str | None, *, text: str = "", date: str | None = None,
            provider: str | None = None, ref: str | None = None, weight: Any = None) -> dict:
        entry = {
            "id": f"S{len(entries) + 1}",
            "kind": kind,
            "ref": ref,
            "label": label,
            "provider": provider or _publisher(url),
            "url": url,
            "date": date,
            "weight": weight,
            "text": text,
        }
        entries.append(entry)
        return entry

    # ---- the tool's own fundamentals ------------------------------------
    add(
        "fundamentals",
        f"Yahoo Finance quote and key statistics for {symbol}",
        _YAHOO_STATS.format(sym=symbol),
        provider="Yahoo Finance (via yfinance)",
        text=" ".join(
            [
                *(packet.get("quants_lines") or []),
                f"price {q.get('price')}",
                f"market cap {q.get('market_cap_human')}",
                f"forward PE {q.get('fwd_pe')}",
                f"forward PE next FY {q.get('fwd_pe_1y')}",
                f"trailing PE {q.get('trailing_pe')}",
                f"P/S {q.get('ps')}",
                f"EV/EBITDA {q.get('ev_ebitda')}",
            ]
        ),
        date=packet.get("as_of"),
        ref="fundamentals",
    )

    trend = q.get("eps_trend") or {}
    rev = q.get("eps_revisions") or {}
    add(
        "consensus",
        f"Analyst EPS estimates and revision counts for {symbol}",
        _YAHOO_ANALYSIS.format(sym=symbol),
        provider="Yahoo Finance (via yfinance)",
        text=(
            f"FY consensus {trend.get('current')} now, {trend.get('7d_ago')} 7 days ago, "
            f"{trend.get('30d_ago')} 30 days ago, change over 30 days "
            f"{trend.get('change_30d_pct')}%; EPS revisions {rev.get('up_30d')} up and "
            f"{rev.get('down_30d')} down over 30 days, {rev.get('up_7d')} up and "
            f"{rev.get('down_7d')} down over 7 days"
        ),
        date=packet.get("as_of"),
        ref="consensus",
    )

    deltas = packet.get("fundamental_deltas") or []
    yoy = packet.get("eps_yoy") or {}
    if deltas or yoy:
        add(
            "statements",
            f"{symbol} quarterly income statement and EPS history",
            _NASDAQ_FINANCIALS.format(low=low),
            provider="Nasdaq company financials",
            text=" ".join(
                [
                    *[
                        f"{d.get('label')} {d.get('direction')} {abs(d.get('change_pct') or 0):.1f}% "
                        f"({d.get('prior_period')} to {d.get('period')})"
                        for d in deltas
                    ],
                    f"EPS {yoy.get('direction')} year over year {yoy.get('year_ago')} to "
                    f"{yoy.get('current')}",
                    *[
                        f"{d.get('label')} {d.get('qoq_pct')}% quarter over quarter and "
                        f"{d.get('yoy_pct')}% year over year to {d.get('period')}"
                        for d in (packet.get("yoy_deltas") or [])
                    ],
                    *[
                        f"{d.get('label')} {d.get('direction')} {abs(d.get('change_pct') or 0):.1f}% "
                        f"in fiscal {d.get('period')} vs {d.get('prior_period')}"
                        for d in (packet.get("annual_deltas") or [])
                    ],
                ]
            ),
            date=(deltas[0].get("period") if deltas else None),
            ref="statements",
        )

    deals = packet.get("deal_activity") or []
    if deals:
        add(
            "statements",
            f"{symbol} balance sheet: acquisition footprint",
            _NASDAQ_FINANCIALS.format(low=low),
            provider="Yahoo Finance (via yfinance) statements",
            text=" ".join(
                f"{d.get('label')} rose {d.get('change_pct')}% from "
                f"{d.get('prior')} in {d.get('prior_period')} to {d.get('current')} in "
                f"{d.get('period')} ({d.get('basis')}), which "
                f"{'is an acquisition' if d.get('confirmed') else 'is probably an acquisition'} "
                f"closing in that period"
                + " ".join(
                    f"{e.get('label')} rose {e.get('change_pct')}% in the same period"
                    for e in (d.get("also") or [])
                )
                for d in deals
            ),
            date=deals[0].get("period"),
            ref="deal",
        )

    cat = packet.get("catalyst") or {}
    if cat.get("date") or packet.get("next_earnings"):
        reports = " ".join(
            f"{r.get('date')} estimate {r.get('eps_estimate')} actual {r.get('eps_actual')} "
            f"surprise {r.get('surprise_pct')}%"
            for r in (cat.get("recent_reports") or [])
        )
        add(
            "catalyst",
            f"{symbol} earnings calendar and reported results",
            _NASDAQ_EARNINGS.format(low=low),
            provider="Nasdaq earnings calendar",
            text=" ".join(
                [
                    str(cat.get("facts_line") or ""),
                    f"beat streak {cat.get('beat_streak')}",
                    f"median gap {cat.get('median_gap_days')} days",
                    reports,
                ]
            ),
            date=cat.get("date"),
            ref="catalyst",
        )

    # ---- headlines -------------------------------------------------------
    # Only items carrying a URL, because an uncitable headline is not evidence a
    # reader can check, and the two feeds are registered separately so that both
    # are represented: ranking them together lets a busy search result bury every
    # per-symbol headline, which is the coverage the free feeds are there for.
    news = [n for n in (packet.get("news") or []) if n.get("url")]
    # Both feeds are registered whole. Search results are already capped upstream by
    # research.MAX_CLAIMS, and half-capping them here (max_news // 2) dropped the rest
    # of the strongest evidence in the packet for no gain the prompt did not pay for.
    web = [n for n in news if n.get("source") == "ollama_search"][:max_news]
    feeds = [n for n in news if n.get("source") != "ollama_search"][:max_news]
    for index, item in enumerate(feeds):
        add(
            item.get("source") or "news",
            f"{item.get('publisher') or _publisher(item.get('url')) or 'news'}: "
            f"{item.get('title')}",
            item.get("url"),
            text=f"{item.get('title')} {item.get('summary') or ''}".strip(),
            date=str(item.get("published") or item.get("created") or "")[:10] or None,
            ref=f"news:{index}",
            weight=item.get("relevance"),
        )
    for index, item in enumerate(web):
        add(
            item.get("source") or "ollama_search",
            f"{item.get('publisher') or _publisher(item.get('url')) or 'search'}: "
            f"{item.get('title')}",
            item.get("url"),
            text=f"{item.get('title')} {item.get('summary') or ''}".strip(),
            date=str(item.get("published") or "")[:10] or None,
            ref=f"web:{index}",
            weight=item.get("relevance"),
        )

    # ---- end-market research --------------------------------------------
    # Each trend already carries the verbatim quote and the URL it came from, so
    # this is the strongest evidence in the packet: the quote was checked against
    # the retrieved text before the trend was kept.
    for index, item in enumerate((packet.get("forward_trends") or {}).get("trends") or []):
        add(
            "research",
            f"{item.get('publisher') or _publisher(item.get('url')) or 'search'}: "
            f"{item.get('claim')}",
            item.get("url"),
            text=f"{item.get('claim')} {item.get('why') or ''} \"{item.get('quote') or ''}\"",
            date=item.get("as_of"),
            ref=f"trend:{index}",
        )

    if packet.get("structures"):
        add(
            "options",
            f"{symbol} listed option chain",
            _YAHOO_OPTIONS.format(sym=symbol),
            provider="Yahoo Finance (via yfinance)",
            text=" ".join(
                f"{direction} {s.get('option_type')} strike {ll.get('strike')} "
                f"expiry {ll.get('expiry')} premium {ll.get('premium')}"
                for direction, s in (packet.get("structures") or {}).items()
                if "error" not in s
                for ll in [s.get("long_leg") or {}]
            ),
            date=packet.get("as_of"),
            ref="options",
        )

    return entries


def sources_for_prompt(catalogue: list[dict]) -> list[str]:
    """The catalogue as compact, numbered lines for the evidence block."""
    lines = []
    for entry in catalogue:
        bits = [f"{entry['id']}", entry.get("provider") or "?", str(entry.get("label") or "")]
        if entry.get("date"):
            bits.append(f"({entry['date']})")
        if entry.get("url"):
            bits.append(entry["url"])
        lines.append("  " + "  ".join(bits))
    return lines


# --------------------------------------------------------------------------
# two readings the prose keeps getting wrong
# --------------------------------------------------------------------------


def revisions_reading(quants_panel: dict) -> str:
    """A line stating whether the consensus *level* moved, next to the counts.

    The counts and the level are different facts and the difference is exactly
    where a plausible-sounding note goes wrong. Observed on BB: the writer read
    "5 up and 0 down over 30 days" as *the number has been raised*, and concluded
    the 0.19 FY consensus was stale -- while the same packet's trend line said the
    level had not moved at all in 30 days (0.18857 then, 0.18857 now). Five
    analysts nudging their estimate inside the same cent raises the *count* and
    leaves the *level* where it was.

    Stated as arithmetic rather than as advice, because it is a fact about this
    packet and the writer can check it.
    """
    trend = quants_panel.get("eps_trend") or {}
    rev = quants_panel.get("eps_revisions") or {}
    change = trend.get("change_30d_pct")
    up, down = rev.get("up_30d"), rev.get("down_30d")
    if change is None and up is None:
        return ""

    net = None
    if up is not None and down is not None:
        net = up - down

    if change is None:
        moved = "unknown"
    elif abs(change) < 0.05:
        moved = "unchanged"
    elif change > 0:
        moved = "raised"
    else:
        moved = "cut"

    detail = (
        f" ({trend.get('30d_ago')} -> {trend.get('current')}, {change:+.2f}%)"
        if change is not None
        else ""
    )
    body = (
        f"  LEVEL READING: {up or 0} analyst(s) raised and {down or 0} cut over 30 days; "
        f"the FY consensus level itself is {moved}{detail}."
    )
    if moved == "unchanged" and (net or 0) > 0:
        body += (
            " The raises did not move the number, so the consensus is current and not "
            "stale: a count of analysts moving cannot make a level that has not moved "
            "out of date."
        )
    elif moved == "raised":
        body += " The current consensus already includes those revisions."
    return body


def trailing_vs_consensus(packet: dict) -> dict | None:
    """Compare the last four reported quarters' EPS with the current-FY consensus.

    A beat streak is the most common reason given for "consensus is too low", and
    it is usually already in the number: analysts who set the estimate watch the
    same reported beats. On BB the trailing four actuals summed to exactly the
    0.18857 FY consensus, which makes the streak evidence that the consensus is
    right, not that it is stale.

    Only stated when the two are close enough to be comparable -- an FY whose
    quarters are not the trailing four would make the comparison meaningless, and
    a number that is not comparable is not evidence of anything.
    """
    cat = packet.get("catalyst") or {}
    reports = [r for r in (cat.get("recent_reports") or []) if r.get("eps_actual") is not None]
    fy = (packet.get("quants") or {}).get("eps_fy_current")
    if len(reports) < 3 or not fy:
        return None

    recent = reports[:4]
    total = sum(float(r["eps_actual"]) for r in recent)
    if not total:
        return None
    ratio = total / float(fy)
    if not 0.75 <= ratio <= 1.25:
        return None

    beat = sum(1 for r in recent if r.get("beat"))
    detail = " + ".join(f"{float(r['eps_actual']):g}" for r in recent)
    verdict = (
        "the streak is already in the consensus, so a trailing beat cannot by itself "
        "make that number stale"
        if beat >= len(recent) - 1
        else "read it against the streak before treating either as stale"
    )
    return {
        "trailing_sum": round(total, 4),
        "fy_consensus": float(fy),
        "ratio": round(ratio, 3),
        "beats": beat,
        "quarters": len(recent),
        "line": (
            f"TRAILING CHECK: the last {len(recent)} reported quarters' EPS actuals "
            f"({detail}) total {total:g}, against a current-FY consensus of {fy:g} -- "
            f"{verdict}."
        ),
    }


# --------------------------------------------------------------------------
# prompt context
# --------------------------------------------------------------------------


def to_prompt_context(packet: dict, *, max_news: int = MAX_NEWS_SOURCES) -> str:
    """Render a packet as compact evidence text for an LLM.

    Deliberately terse and fact-only: no adjectives, no thesis. The model's job
    is to *distil*, and it can only do that if the input is raw material rather
    than pre-chewed conclusions.
    """
    q = packet.get("quants", {})
    profile = packet.get("profile", {})
    lines: list[str] = []

    # Every block of evidence below is tagged with the id of its source, and the
    # full list is repeated at the end. A writer can then cite `S3` instead of
    # copying a URL -- copying is where models invent links, and an id that does
    # not exist is detectable where a plausible-looking URL is not.
    catalogue = packet.get("sources") or source_catalogue(packet)
    ids = {str(e.get("ref")): e["id"] for e in catalogue if e.get("ref")}
    trend_entries = [e for e in catalogue if str(e.get("ref", "")).startswith("trend:")]

    def tag(*refs: str) -> str:
        found = [ids[r] for r in refs if r in ids]
        return f"  [{' '.join(found)}]" if found else ""

    lines.append(f"SYMBOL: {packet['symbol']}  ({q.get('name')})")
    lines.append(f"AS OF: {packet.get('as_of')}")
    sector = q.get("sector") or profile.get("sector") or "?"
    industry = q.get("industry") or profile.get("industry") or "?"
    lines.append(f"SECTOR: {sector} / {industry}")

    summary = (profile.get("summary") or "").strip()
    if summary:
        lines.append(f"BUSINESS (raw filing language, needs distilling):\n{summary[:1200]}")

    lines.append(f"\nQUANTS{tag('fundamentals', 'consensus')}")
    for line in packet.get("quants_lines", []):
        lines.append(f"  {line}")
    if q.get("fwd_pe_1y") is not None:
        lines.append(f"  Fwd PE on next-FY consensus: {q['fwd_pe_1y']}")
    if q.get("ev_ebitda") is not None:
        lines.append(f"  EV/EBITDA: {q['ev_ebitda']}")

    trend = q.get("eps_trend", {})
    if trend.get("change_7d_pct") is not None:
        lines.append(
            f"  EPS trend detail: FY consensus {trend.get('current')} now, "
            f"{trend.get('7d_ago')} 7d ago, {trend.get('30d_ago')} 30d ago"
        )
    rev = q.get("eps_revisions", {})
    lines.append(
        f"  EPS revisions: {rev.get('up_7d')} up / {rev.get('down_7d')} down (7d); "
        f"{rev.get('up_30d')} up / {rev.get('down_30d')} down (30d); net {rev.get('net_30d')}"
    )
    # The distinction that matters and that prose keeps collapsing: a revision
    # COUNT is not a revision of the LEVEL. Five analysts nudging their number
    # inside the same cent leaves the consensus where it was, and saying the
    # consensus is "stale" on that evidence contradicts the level line above it.
    lines.append(revisions_reading(q))

    nxt = packet.get("next_earnings") or {}
    if nxt.get("next_date"):
        lines.append(
            f"\nNEXT EARNINGS: {nxt['next_date']}  consensus EPS {nxt.get('eps_avg')}"
            + tag("catalyst")
        )

    cat = packet.get("catalyst") or {}
    if cat.get("date"):
        lines.append(
            f"\nCATALYST (the date is measured -- copy it exactly, never round it){tag('catalyst')}"
        )
        lines.append(f"  {cat['facts_line']}")
        for fact in catalyst_mod.justification_facts(cat):
            lines.append(f"  - {fact}")
        if cat.get("recent_reports"):
            lines.append("  Recent reports against consensus (newest first):")
            for row in cat["recent_reports"]:
                surprise = row.get("surprise_pct")
                verdict = (
                    f"beat by {surprise:.1f}%"
                    if row.get("beat") and surprise is not None
                    else (f"missed by {abs(surprise):.1f}%" if surprise is not None else "reported")
                )
                lines.append(
                    f"    {row['date']}: estimate {row.get('eps_estimate')} vs actual "
                    f"{row.get('eps_actual')} ({verdict})"
                )
        trailing = trailing_vs_consensus(packet)
        if trailing:
            lines.append(f"  {trailing['line']}")
        lines.append(
            "  Write one sentence: what that report must show for this thesis to be "
            "right. Do not restate the date's facts."
        )

    trends = (packet.get("forward_trends") or {}).get("trends") or []
    if trends:
        lines.append(
            "\nFORWARD TRENDS (end-market research, not the company's own filings; "
            "each verified against its source)" + tag(*[f"trend:{i}" for i in range(len(trends))])
        )
        lines.extend(
            research_mod.trends_for_prompt(
                packet["forward_trends"], ids=[e["id"] for e in trend_entries]
            )
        )
        lines.append(
            "  Use these to explain WHY the pressure has or has not yet reached the "
            "reported numbers. This is the qualitative half of the argument."
        )

    deltas = packet.get("fundamental_deltas") or []
    if deltas:
        lines.append(f"\nSTATEMENT MOVES (latest quarter vs prior){tag('statements')}")
        for d in deltas:
            lines.append(
                f"  {d['label']}: {d['direction']} {abs(d['change_pct']):.1f}% "
                f"({d['prior_period']} -> {d['period']})"
            )

    # Sequential and annual moves for the same line, side by side. This block exists
    # because a quarter can be down 11% from the one before it and up 12% on the year:
    # a reason that quotes one of those numbers without the other is not evidence, and
    # the two are never separated here so the omission is visible.
    yoy_rows = packet.get("yoy_deltas") or []
    if yoy_rows:
        lines.append(
            f"\nQUARTER: SEQUENTIAL vs SAME QUARTER A YEAR AGO"
            f"{tag('statements')}{tag('consensus')}"
        )
        for d in yoy_rows:
            bits = [f"{d['label']}:"]
            if d.get("current") is not None:
                bits.append(f"{human_money(d['current'])} in {d['period']}")
            if d.get("qoq_pct") is not None:
                bits.append(f"({d['qoq_pct']:+.1f}% QoQ)")
            if d.get("yoy_pct") is not None:
                bits.append(
                    f"vs {human_money(d.get('year_ago'))} in {d.get('year_ago_period')} "
                    f"({d['yoy_pct']:+.1f}% YoY)"
                )
            lines.append("  " + " ".join(bits))
        conflicts = [d for d in yoy_rows if d.get("conflict")]
        if conflicts:
            names = ", ".join(d["label"] for d in conflicts[:3])
            lines.append(
                f"  NOTE: {names} move in opposite directions sequentially and on the "
                f"year. A sequential move is NOT a trend here -- quote the year-over-year "
                f"comparison with it, and do not present the sequential fall as deterioration."
            )

    annual = packet.get("annual_deltas") or []
    if annual:
        lines.append(f"\nANNUAL (fiscal year vs prior year){tag('statements')}")
        for d in annual:
            lines.append(
                f"  {d['label']}: {human_money(d.get('prior'))} -> "
                f"{human_money(d.get('current'))} ({d['period']} vs {d['prior_period']}, "
                f"{d['change_pct']:+.1f}%)"
            )

    deals = packet.get("deal_activity") or []
    if deals:
        lines.append(f"\nDEAL ACTIVITY (an acquisition landed in these periods){tag('deal')}")
        for d in deals:
            lines.append(
                f"  {d['label']}: {human_money(d.get('prior'))} -> "
                f"{human_money(d.get('current'))} ({d['prior_period']} to {d['period']}, "
                f"{d['basis']}, {d['change_pct']:+.1f}%)"
                + (
                    " -- goodwill only moves through purchase accounting"
                    if d.get("confirmed")
                    else " -- a step in intangibles usually, but not always, means a deal"
                )
            )
            for extra in d.get("also") or []:
                lines.append(
                    f"    {extra['label']} also moved {extra['change_pct']:+.1f}% in the "
                    f"same period ({extra['prior_period']} to {extra['period']})"
                )
        dates = [d.get("period") for d in deals if d.get("period")]
        lines.append(
            f"  Any growth in the periods at or after {max(dates) if dates else 'the deal'} "
            f"includes acquired revenue, so it is NOT organic growth. If a reason argues "
            f"from growth, say how much of it is acquired; if it argues from a decline, "
            f"check whether the deal year flatters the comparison."
        )

    bar = packet.get("consensus_bar")
    if bar:
        bits = []
        if bar.get("eps_avg") is not None:
            rng = ""
            if bar.get("eps_low") is not None and bar.get("eps_high") is not None:
                rng = f" (range {bar['eps_low']}-{bar['eps_high']})"
            bits.append(f"EPS {bar['eps_avg']}{rng}")
        if bar.get("revenue_avg") is not None:
            bits.append(f"revenue {human_money(bar['revenue_avg'])}")
        lines.append(
            f"\nCONSENSUS BAR (what the {bar.get('date')} print is measured against): "
            + ", ".join(bits)
            + tag("catalyst")
            + tag("consensus")
        )

    yoy = packet.get("eps_yoy")
    if yoy:
        lines.append(
            f"\nEPS YOY: {yoy['direction']} ({yoy['year_ago']} -> {yoy['current']})"
            + tag("statements")
        )

    peers = packet.get("peers") or []
    if peers:
        lines.append("\nPEERS (same basis as above -- compare like for like)")
        for p in peers:
            lines.append(
                f"  {p['symbol']:<6} fwdPE(current FY) {p['fwd_pe_0y']}  "
                f"fwdPE(next FY) {p['fwd_pe_1y']}  P/S {p['ps']}  "
                f"mcap {p['market_cap_human']}  rev growth {p.get('revenue_growth')}"
            )

    story = packet.get("story") or {}
    if story.get("themes"):
        lines.append("\nLIVE THEMES IN THIS NAME'S NEWS")
        for t in story["themes"][:4]:
            lines.append(f"  {t['label']} ({t['count']} stories): {t['description']}")
            for ev in t.get("evidence", [])[:2]:
                lines.append(f"    - {ev['title']}")

    news = [n for n in (packet.get("news") or []) if n.get("url")]
    if news:
        lines.append("\nHEADLINES (relevance 3 = company-specific; [S#] is the source id)")
        # Web-search results carry the substance, so give them their snippet.
        web = [n for n in news if n.get("source") == "ollama_search"]
        feeds = [n for n in news if n.get("source") != "ollama_search"]
        for index, item in enumerate(feeds[:max_news]):
            published = str(item.get("published") or item.get("created") or "")[:16]
            lines.append(
                f"  [{item.get('relevance', 0)}] {published} {item.get('title')}"
                f"{_cite(ids.get(f'news:{index}'))}"
            )
            summary_text = (item.get("summary") or "").strip()
            if summary_text:
                lines.append(f"       {summary_text[:220]}")

        if web:
            lines.append("\nWEB REPORTING (search results, best evidence first)")
            for index, item in enumerate(web[:max_news]):
                stamp = str(item.get("published") or "")[:10]
                lines.append(
                    f"  [{item.get('relevance', 0)}] {stamp} {item.get('title')} "
                    f"-- {item.get('publisher')}{_cite(ids.get(f'web:{index}'))}"
                )
                snippet = (item.get("summary") or "").strip()
                if snippet:
                    lines.append(f"       {snippet[:500]}")

    structures = packet.get("structures") or {}
    if structures:
        lines.append(f"\nAVAILABLE OPTION STRUCTURES (from live chains){tag('options')}")
        for direction, s in structures.items():
            if "error" in s:
                lines.append(f"  {direction}: unavailable ({s['error']})")
                continue
            ll, sl = s["long_leg"], s["short_leg"]
            lines.append(
                f"  {direction.upper()}: long {s['option_type']} {ll['strike']:g} "
                f"exp {ll['expiry']} @{ll['premium']} x{ll['qty']}; "
                f"short {s['option_type']} {sl['strike']:g} exp {sl['expiry']} "
                f"@{sl['premium']} x{sl['qty']}"
            )
            lines.append(
                f"     credit ratio mid {(s['credit_ratio_mid'] or 0)*100:.1f}% / "
                f"conservative {(s['credit_ratio_conservative'] or 0)*100:.1f}% "
                f"(floor 10%); net debit ${s['net_debit']:,.0f}"
            )
            if s.get("advice"):
                lines.append(f"     {s['advice']}")

    if catalogue:
        lines.append(
            "\nSOURCES (cite these ids in reason_sources; never write a URL into a reason)"
        )
        lines.extend(sources_for_prompt(catalogue))

    return "\n".join(lines)


def _cite(source_id: str | None) -> str:
    return f"  [{source_id}]" if source_id else ""
