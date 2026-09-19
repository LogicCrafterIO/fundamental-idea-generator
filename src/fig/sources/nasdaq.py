"""Nasdaq's free public JSON API -- the *discovery* half of the pipeline.

Why this source
---------------
Nasdaq serves the same JSON that powers nasdaq.com/market-activity behind an
open endpoint that needs no key, no login and no cookie/crumb dance (unlike
Yahoo's ``quoteSummary``). That makes it the right place to answer the two
questions that start any idea:

1. *What is happening right now?*  -> screeners, market-wide news.
2. *What is about to happen?*      -> the earnings calendar, which defines the
   catalyst window an option structure has to cover.

It also carries sell-side consensus *revision* counts in 4-week buckets, which
is the closest free analogue of the "5 up and 10 down over last 30 days" line in
the reference writeups.

Caveats
-------
* Undocumented and unversioned. Treat every field as optional -- the parsers
  here are defensive by design and return ``None`` rather than raising.
* Some endpoints intermittently 301 to a canonical path; ``allow_redirects`` in
  :func:`fig.util.http_json` handles that.
* ``earnings-forecast`` revisions are "over the last 4 weeks" (~28d), not a true
  30-day window. yfinance's ``eps_revisions`` gives exact 7d/30d buckets, so
  prefer that one for the Quants block and use this for corroboration.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ..util import cached_json, http_json, parse_money

BASE = "https://api.nasdaq.com/api"

# TTLs: calendars move fast, reference data does not.
TTL_CALENDAR = 60 * 60  # 1h
TTL_NEWS = 60 * 30  # 30m
TTL_REFERENCE = 60 * 60 * 12  # 12h


def _get(path: str, ttl: int, **params: Any) -> Any:
    query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    url = f"{BASE}/{path}" + (f"?{query}" if query else "")
    return cached_json(f"nasdaq:{path}?{query}", lambda: http_json(url), ttl)


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------


def earnings_calendar(day: date | str) -> list[dict]:
    """Companies reporting on ``day``.

    Rows look like::

        {"symbol": "OMF", "name": "...", "marketCap": "$7,070,000,000",
         "epsForecast": "$1.88", "lastYearEPS": "$1.60", "noOfEsts": "9",
         "time": "time-after-hours", "fiscalQuarterEnding": "Sep/2026"}
    """
    stamp = day.isoformat() if isinstance(day, date) else str(day)
    payload = _get("calendar/earnings", TTL_CALENDAR, date=stamp)
    rows = (payload or {}).get("data", {}).get("rows") or []
    out = []
    for row in rows:
        out.append(
            {
                "symbol": (row.get("symbol") or "").strip().upper(),
                "name": row.get("name"),
                "date": stamp,
                "session": row.get("time"),  # before/after hours
                "market_cap": parse_money(row.get("marketCap")),
                "eps_forecast": parse_money(row.get("epsForecast")),
                "eps_last_year": parse_money(row.get("lastYearEPS")),
                "num_estimates": parse_money(row.get("noOfEsts")),
                "fiscal_quarter_ending": row.get("fiscalQuarterEnding"),
            }
        )
    return [r for r in out if r["symbol"]]


def earnings_window(
    start: date | None = None, days: int = 7, min_market_cap: float = 2e9
) -> list[dict]:
    """Earnings calendar across a date range, filtered to name-size companies.

    The market-cap floor keeps the option-structure requirement satisfiable:
    microcaps rarely have listed strikes worth trading.
    """
    start = start or date.today()
    seen: dict[str, dict] = {}
    for offset in range(days):
        for row in earnings_calendar(start + timedelta(days=offset)):
            cap = row.get("market_cap") or 0
            if cap < min_market_cap:
                continue
            seen.setdefault(row["symbol"], row)
    return sorted(seen.values(), key=lambda r: r.get("market_cap") or 0, reverse=True)


def screener(
    *,
    exchange: str = "NASDAQ",
    limit: int = 100,
    table_only: bool = True,
) -> list[dict]:
    """Screen listed stocks. ``exchange`` in {NASDAQ, NYSE, AMEX}.

    Returns normalised rows with symbol/name/last_sale/pct_change/market_cap.
    """
    payload = _get(
        "screener/stocks",
        TTL_CALENDAR,
        tableonly=str(table_only).lower(),
        limit=limit,
        exchange=exchange,
        download="false",
    )
    rows = ((payload or {}).get("data", {}) or {}).get("table", {}).get("rows") or []
    out = []
    for row in rows:
        out.append(
            {
                "symbol": (row.get("symbol") or "").strip().upper(),
                "name": row.get("name"),
                "last_sale": parse_money(row.get("lastsale")),
                "net_change": parse_money(row.get("netchange")),
                "pct_change": parse_money(row.get("pctchange")),
                "market_cap": parse_money(row.get("marketCap")),
                "exchange": exchange,
            }
        )
    return [r for r in out if r["symbol"]]


def market_news(limit: int = 40) -> list[dict]:
    """Market-wide headlines (not symbol-scoped)."""
    payload = _get(
        "news/topic/articlebysymbol",
        TTL_NEWS,
        q="stocks",
        offset=0,
        limit=limit,
    )
    rows = (payload or {}).get("data", {}).get("rows") or []
    return [_normalise_news(r) for r in rows]


def news_for_symbol(symbol: str, limit: int = 15) -> list[dict]:
    """Headlines tagged to ``symbol``.

    Nasdaq's topic feed is noisy: it returns market roundups that merely *mention*
    the ticker. ``related_symbols`` lets callers filter for genuine coverage, and
    :func:`fig.packet` scores relevance rather than trusting the tag alone.
    """
    symbol = symbol.upper()
    payload = _get(
        "news/topic/articlebysymbol",
        TTL_NEWS,
        q=f"{symbol}|stocks",
        offset=0,
        limit=limit,
    )
    rows = (payload or {}).get("data", {}).get("rows") or []
    return [_normalise_news(r) for r in rows]


def _normalise_news(row: dict) -> dict:
    related = row.get("related_symbols") or []
    return {
        "title": (row.get("title") or "").strip(),
        "publisher": row.get("publisher"),
        "created": row.get("created"),
        "ago": row.get("ago"),
        "url": row.get("url") or row.get("link"),
        "primary_symbol": (row.get("primarysymbol") or "").split("|")[0].upper() or None,
        "related_symbols": [str(s).split("|")[0].upper() for s in related],
        "summary": row.get("summary") or row.get("description"),
        "source": "nasdaq",
    }


# --------------------------------------------------------------------------
# per-symbol facts
# --------------------------------------------------------------------------


def quote_summary(symbol: str) -> dict:
    """Valuation + classification snapshot for one symbol."""
    payload = _get(f"quote/{symbol.upper()}/summary", TTL_REFERENCE, assetclass="stocks")
    data = (payload or {}).get("data") or {}
    summary = data.get("summaryData") or {}

    def field(name: str):
        entry = summary.get(name) or {}
        return entry.get("value") if isinstance(entry, dict) else entry

    return {
        "symbol": data.get("symbol"),
        "exchange": field("Exchange"),
        "sector": field("Sector"),
        "industry": field("Industry"),
        "market_cap": parse_money(field("MarketCap")),
        "forward_pe": parse_money(field("ForwardPE1Yr")),
        "pe_ratio": parse_money(field("PERatio")),
        "eps_forecast": parse_money(field("ForecastEarningsPerShare")),
        "year_high": parse_money(field("FiftTwoWeekHigh")),
        "year_low": parse_money(field("FiftTwoWeekLow")),
        "shares_outstanding": parse_money(field("SharesOutstanding")),
    }


def earnings_forecast(symbol: str) -> dict:
    """Consensus EPS by period, with 4-week up/down revision counts.

    Returns ``{"quarterly": [...], "yearly": [...]}``. Each row keeps the raw
    ``up``/``down`` revision counts (see module caveat: 4-week window).
    """
    payload = _get(f"analyst/{symbol.upper()}/earnings-forecast", TTL_REFERENCE)
    data = (payload or {}).get("data") or {}

    def rows(key: str) -> list[dict]:
        table = data.get(key) or {}
        out = []
        for row in table.get("rows") or []:
            out.append(
                {
                    "period": row.get("fiscalEnd"),
                    "eps_consensus": parse_money(row.get("consensusEPSForecast")),
                    "eps_high": parse_money(row.get("highEPSForecast")),
                    "eps_low": parse_money(row.get("lowEPSForecast")),
                    "num_estimates": parse_money(row.get("noOfEstimates")),
                    "revisions_up_4w": parse_money(row.get("up")),
                    "revisions_down_4w": parse_money(row.get("down")),
                }
            )
        return out

    return {"quarterly": rows("quarterlyForecast"), "yearly": rows("yearlyForecast")}


def financials(symbol: str, quarterly: bool = True) -> dict:
    """Income statement / balance sheet / cash flow / ratios tables.

    The ``frequency`` query parameter is **inverted** relative to intuition:
    ``frequency=2`` returns *quarterly* columns and ``frequency=1`` returns
    *annual* ones. Verified against OMF, where ``frequency=2`` gives columns
    6/30/2026, 3/31/2026, ... labelled "Quarterly Ending:", while
    ``frequency=1`` gives 12/31/2025, 12/31/2024, ... labelled "Period Ending:".
    This function hides that quirk behind ``quarterly=``.

    Return shape::

        {"incomeStatement": {"periods": ["6/30/2026", ...],
                             "rows": [{"label": "Total Revenue",
                                       "values": [1624000.0, 1584000.0, ...]}]}}

    Values are parsed to floats in the table's own units (Nasdaq reports these
    in **thousands**), so compare ratios, not absolute levels.
    """
    frequency = 2 if quarterly else 1
    payload = _get(
        f"company/{symbol.upper()}/financials", TTL_REFERENCE, frequency=frequency
    )
    data = (payload or {}).get("data") or {}

    tables: dict[str, Any] = {}
    for name in (
        "incomeStatementTable",
        "balanceSheetTable",
        "cashFlowTable",
        "financialRatiosTable",
    ):
        table = data.get(name) or {}
        raw_rows = table.get("rows") or []
        if not raw_rows:
            continue

        # Column labels live in "headers"; the first header is the row-label
        # column ("Period Ending:" / "Quarterly Ending:").
        headers = table.get("headers") or {}
        ordered = [headers.get(f"value{i}") for i in range(1, len(raw_rows[0]) + 1)]
        periods = [h for h in ordered[1:] if h]

        rows = []
        for row in raw_rows:
            cells = [row.get(f"value{i}") for i in range(1, len(ordered) + 1)]
            label = (cells[0] or "").strip()
            if not label:
                continue
            values = []
            for cell in cells[1:]:
                # Ratios carry "%"; keep the magnitude but flag the unit.
                if isinstance(cell, str) and cell.strip().endswith("%"):
                    num = parse_money(cell.rstrip("%"))
                    values.append(round(num / 100.0, 6) if num is not None else None)
                else:
                    values.append(parse_money(cell))
            rows.append({"label": label, "values": values})

        tables[name.replace("Table", "")] = {"periods": periods, "rows": rows}
    return tables


def historical(symbol: str, fromdate: date | str | None = None, limit: int = 30) -> list[dict]:
    """Daily OHLC bars, newest first."""
    if fromdate is None:
        fromdate = date.today() - timedelta(days=limit * 2)
    stamp = fromdate.isoformat() if isinstance(fromdate, date) else str(fromdate)
    payload = _get(
        f"quote/{symbol.upper()}/historical",
        TTL_CALENDAR,
        assetclass="stocks",
        fromdate=stamp,
        limit=limit,
    )
    rows = ((payload or {}).get("data", {}) or {}).get("tradesTable", {}).get("rows") or []
    out = []
    for row in rows:
        out.append(
            {
                "date": row.get("date"),
                "close": parse_money(row.get("close")),
                "volume": parse_money(row.get("volume")),
                "open": parse_money(row.get("open")),
                "high": parse_money(row.get("high")),
                "low": parse_money(row.get("low")),
            }
        )
    return out
