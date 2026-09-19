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
) -> list[dict]:
    """Merge Yahoo's per-symbol feed with Nasdaq's topic feed.

    Yahoo gives genuine per-name coverage; Nasdaq adds market-wide context that
    merely touches the ticker. Both are kept and tagged with a ``relevance``
    score so the writer can tell a company-specific story from a sector ripple.

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
    for item in yahoo.news(symbol, limit=yahoo_limit):
        items.append({**item, "relevance": _relevance(symbol, item, company_name)})
    for item in nasdaq.news_for_symbol(symbol, limit=nasdaq_limit):
        items.append({**item, "relevance": _relevance(symbol, item, company_name)})

    if include_web:
        items.extend(web_stories(symbol, company_name, per_query=web_per_query))

    merged = _dedupe_news(items)
    for item in merged:
        item["themes"] = themes.tag_text(f"{item.get('title','')} {item.get('summary','')}")
    # Most relevant first, then most recent.
    merged.sort(key=lambda i: (-i.get("relevance", 0), _recency_key(i)), reverse=False)
    return merged


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
    news = collect_news(symbol, include_web=include_web)
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
        "news": news,
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

    return packet


# --------------------------------------------------------------------------
# prompt context
# --------------------------------------------------------------------------


def to_prompt_context(packet: dict, *, max_news: int = 12) -> str:
    """Render a packet as compact evidence text for an LLM.

    Deliberately terse and fact-only: no adjectives, no thesis. The model's job
    is to *distil*, and it can only do that if the input is raw material rather
    than pre-chewed conclusions.
    """
    q = packet.get("quants", {})
    profile = packet.get("profile", {})
    lines: list[str] = []

    lines.append(f"SYMBOL: {packet['symbol']}  ({q.get('name')})")
    lines.append(f"AS OF: {packet.get('as_of')}")
    sector = q.get("sector") or profile.get("sector") or "?"
    industry = q.get("industry") or profile.get("industry") or "?"
    lines.append(f"SECTOR: {sector} / {industry}")

    summary = (profile.get("summary") or "").strip()
    if summary:
        lines.append(f"BUSINESS (raw filing language, needs distilling):\n{summary[:1200]}")

    lines.append("\nQUANTS")
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

    nxt = packet.get("next_earnings") or {}
    if nxt.get("next_date"):
        lines.append(f"\nNEXT EARNINGS: {nxt['next_date']}  consensus EPS {nxt.get('eps_avg')}")

    cat = packet.get("catalyst") or {}
    if cat.get("date"):
        lines.append("\nCATALYST (the date is measured -- copy it exactly, never round it)")
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
        lines.append(
            "  Write one sentence: what that report must show for this thesis to be "
            "right. Do not restate the date's facts."
        )

    trends = (packet.get("forward_trends") or {}).get("trends") or []
    if trends:
        lines.append(
            "\nFORWARD TRENDS (end-market research, not the company's own filings; "
            "each verified against its source)"
        )
        lines.extend(research_mod.trends_for_prompt(packet["forward_trends"]))
        lines.append(
            "  Use these to explain WHY the pressure has or has not yet reached the "
            "reported numbers. This is the qualitative half of the argument."
        )

    deltas = packet.get("fundamental_deltas") or []
    if deltas:
        lines.append("\nSTATEMENT MOVES (latest quarter vs prior)")
        for d in deltas:
            lines.append(
                f"  {d['label']}: {d['direction']} {abs(d['change_pct']):.1f}% "
                f"({d['prior_period']} -> {d['period']})"
            )

    yoy = packet.get("eps_yoy")
    if yoy:
        lines.append(
            f"\nEPS YOY: {yoy['direction']} ({yoy['year_ago']} -> {yoy['current']})"
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

    news = packet.get("news") or []
    if news:
        lines.append("\nHEADLINES (relevance 3 = company-specific)")
        # Web-search results carry the substance, so give them their snippet.
        web = [n for n in news if n.get("source") == "ollama_search"]
        feeds = [n for n in news if n.get("source") != "ollama_search"]
        for item in feeds[:max_news]:
            published = str(item.get("published") or item.get("created") or "")[:16]
            lines.append(f"  [{item.get('relevance', 0)}] {published} {item.get('title')}")
            summary_text = (item.get("summary") or "").strip()
            if summary_text:
                lines.append(f"       {summary_text[:220]}")

        if web:
            lines.append("\nWEB REPORTING (search results, best evidence first)")
            for item in web[: max(4, max_news // 2)]:
                stamp = str(item.get("published") or "")[:10]
                lines.append(
                    f"  [{item.get('relevance', 0)}] {stamp} {item.get('title')} "
                    f"-- {item.get('publisher')}"
                )
                snippet = (item.get("summary") or "").strip()
                if snippet:
                    lines.append(f"       {snippet[:500]}")
                if item.get("url"):
                    lines.append(f"       {item['url']}")

    structures = packet.get("structures") or {}
    if structures:
        lines.append("\nAVAILABLE OPTION STRUCTURES (from live chains)")
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

    return "\n".join(lines)
