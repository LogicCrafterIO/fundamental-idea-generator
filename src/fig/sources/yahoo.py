"""Yahoo Finance via yfinance -- the *fundamentals* half of the pipeline.

Why this source
---------------
yfinance is the only free library that, in one dependency, gives us every field
the reference writeups actually quote:

===========================  ==========================================
Writeup line                 yfinance surface
===========================  ==========================================
``Price`` / ``Market Cap``   ``Ticker.info`` / ``fast_info``
``Fwd PE``                   ``eps_trend`` (see *Forward PE* below)
``EPS trends``               ``Ticker.eps_trend``  (current vs 7d/30d ago)
``EPS revisions``            ``Ticker.eps_revisions`` (up/down, 7d & 30d)
catalyst window              ``Ticker.calendar`` / ``get_earnings_dates``
``Description`` seed         ``info['longBusinessSummary']``
``Structuring``              ``Ticker.options`` + ``Ticker.option_chain``
===========================  ==========================================

It also transparently handles Yahoo's cookie+crumb handshake, which is exactly
the part that makes raw ``quoteSummary`` calls 401 (verified: the unauthenticated
endpoint returns ``Invalid Crumb``).

Forward PE -- read this before comparing to a writeup
-----------------------------------------------------
Yahoo reports ``forwardPE`` as *price / next-fiscal-year EPS*. A hand-written
writeup more often means *price / current-fiscal-year EPS*. The gap is not
cosmetic. Live ORCL (2026-09-19, price 147.61)::

    yfinance info['forwardPE']        = 13.42   -> 147.61 / 10.99  (+1y EPS)
    price / eps_trend['0y'].current   = 18.13   -> 147.61 /  8.14  (0y EPS)

The ORCL reference writeup says **17.7** at price 150, i.e. 150/8.47 -- a
*current-year* basis. So :func:`valuation` returns both and labels them
``fwd_pe_0y`` and ``fwd_pe_1y``. Never quote an unlabelled "Fwd PE" when
comparing a name to a peer; the two bases differ by the growth rate.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timezone
from typing import Any

import yfinance as yf

from ..util import cached_json

TTL_QUOTE = 60 * 30
TTL_STATIC = 60 * 60 * 24  # business summary, sector: rarely changes
TTL_CHAIN = 60 * 15
TTL_STATEMENTS = 60 * 60 * 6  # a filing lands a few times a year


def _clean(value: Any) -> Any:
    """Make a pandas/numpy scalar JSON-safe, mapping NaN to None."""
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):  # numpy scalar
        try:
            return _clean(value.item())
        except (ValueError, AttributeError):
            return str(value)
    return value


def _frame_records(frame) -> list[dict]:
    """DataFrame -> list of JSON-safe dicts, ``None`` for missing values."""
    if frame is None or getattr(frame, "empty", True):
        return []
    out = []
    for idx, row in frame.iterrows():
        record = {"period": str(idx)}
        record.update({str(k): _clean(v) for k, v in row.items()})
        out.append(record)
    return out


def _series(frame) -> dict[str, list]:
    """Statement frame -> ``{line item: [value per period]}``, newest period first.

    Kept as a series rather than a row-per-period frame because every question asked
    of it is "how did this one line move" -- against the prior quarter, and against
    the same quarter a year earlier.
    """
    if frame is None or getattr(frame, "empty", True):
        return {}
    out: dict[str, list] = {}
    for idx, row in frame.iterrows():
        out[str(idx)] = [_clean(v) for v in row.tolist()]
    return out


def _periods(frame) -> list[str]:
    if frame is None or getattr(frame, "empty", True):
        return []
    return [str(col)[:10] for col in frame.columns]


def _ticker(symbol: str) -> yf.Ticker:
    return yf.Ticker(symbol.upper())


# --------------------------------------------------------------------------
# valuation & profile
# --------------------------------------------------------------------------


def valuation(symbol: str) -> dict:
    """Price, size, and forward PE on **both** conventions.

    Also derives ``ps`` (price/sales) because the reference writeups lean on
    relative multiples to argue a mispricing -- e.g. "20x PS compared to oracle
    at about 7x PS".
    """
    symbol = symbol.upper()

    def build() -> dict:
        info = _ticker(symbol).info or {}
        return {
            "symbol": symbol,
            "name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "price": _clean(info.get("currentPrice") or info.get("regularMarketPrice")),
            "prev_close": _clean(info.get("regularMarketPreviousClose")),
            "market_cap": _clean(info.get("marketCap")),
            "enterprise_value": _clean(info.get("enterpriseValue")),
            "total_debt": _clean(info.get("totalDebt")),
            "total_cash": _clean(info.get("totalCash")),
            "trailing_pe": _clean(info.get("trailingPE")),
            "yf_forward_pe": _clean(info.get("forwardPE")),
            "ps": _clean(info.get("priceToSalesTrailing12Months")),
            "pb": _clean(info.get("priceToBook")),
            "ev_ebitda": _clean(info.get("enterpriseToEbitda")),
            "revenue_growth": _clean(info.get("revenueGrowth")),
            "profit_margins": _clean(info.get("profitMargins")),
            "shares_outstanding": _clean(info.get("sharesOutstanding")),
            "fifty_two_week_high": _clean(info.get("fiftyTwoWeekHigh")),
            "fifty_two_week_low": _clean(info.get("fiftyTwoWeekLow")),
            "dividend_yield": _clean(info.get("dividendYield")),
            "float_shares": _clean(info.get("floatShares")),
            "short_percent_of_float": _clean(info.get("shortPercentOfFloat")),
            "beta": _clean(info.get("beta")),
        }

    data = cached_json(f"yf:valuation:{symbol}", build, TTL_QUOTE)

    # Derive the writeup-facing PE bases from the consensus trend table.
    trend = eps_trend(symbol)
    price = data.get("price")
    data["fwd_pe_0y"] = _safe_div(price, _trend_current(trend, "0y"))
    data["fwd_pe_1y"] = _safe_div(price, _trend_current(trend, "+1y"))
    if data.get("fwd_pe_0y") is None:
        data["fwd_pe_0y"] = data.get("trailing_pe")
    return data


def _safe_div(a: float | None, b: float | None) -> float | None:
    if not a or not b:
        return None
    try:
        return round(a / b, 2)
    except ZeroDivisionError:
        return None


def _trend_current(trend: dict, period: str) -> float | None:
    for row in trend.get("periods", []):
        if row.get("period") == period:
            return row.get("current")
    return None


def profile(symbol: str) -> dict:
    """Long business summary + classification, for seeding ``Description``."""

    def build() -> dict:
        info = _ticker(symbol.upper()).info or {}
        return {
            "symbol": symbol.upper(),
            "name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "summary": info.get("longBusinessSummary"),
            "employees": _clean(info.get("fullTimeEmployees")),
            "country": info.get("country"),
            "website": info.get("website"),
        }

    return cached_json(f"yf:profile:{symbol.upper()}", build, TTL_STATIC)


# --------------------------------------------------------------------------
# consensus: trends and revisions  (the "Quants" block)
# --------------------------------------------------------------------------


def eps_trend(symbol: str) -> dict:
    """Consensus EPS now vs 7/30/60/90 days ago.

    Drives the writeup line ``EPS trends: slightly down over the last 7 days``.
    Periods: ``0q`` current quarter, ``+1q`` next quarter, ``0y`` current FY,
    ``+1y`` next FY.
    """
    symbol = symbol.upper()

    def build() -> dict:
        return {"symbol": symbol, "periods": _frame_records(_ticker(symbol).eps_trend)}

    data = cached_json(f"yf:eps_trend:{symbol}", build, TTL_QUOTE)
    # Annotate each period with % drift, which is what the prose actually says.
    for row in data.get("periods", []):
        for label, key in (("7d", "7daysAgo"), ("30d", "30daysAgo"), ("90d", "90daysAgo")):
            past = row.get(key)
            cur = row.get("current")
            if cur is not None and past:
                row[f"chg_{label}_pct"] = round((cur - past) / abs(past) * 100.0, 2)
            else:
                row[f"chg_{label}_pct"] = None
    return data


def eps_revisions(symbol: str) -> dict:
    """Analyst revision counts, up and down, over the trailing 7 and 30 days.

    Drives ``EPS revisions: Split equally, with 5 up and 10 down over last 30
    days``. Note yfinance exposes ``upLast7days``/``downLast7Days`` with
    inconsistent capitalisation -- both are normalised to snake_case here.
    """
    symbol = symbol.upper()

    def build() -> dict:
        return {"symbol": symbol, "periods": _frame_records(_ticker(symbol).eps_revisions)}

    data = cached_json(f"yf:eps_revisions:{symbol}", build, TTL_QUOTE)
    for row in data.get("periods", []):
        up7 = row.get("upLast7days")
        down7 = row.get("downLast7Days", row.get("downLast7days"))
        up30 = row.get("upLast30days")
        down30 = row.get("downLast30days")
        row["up_7d"], row["down_7d"] = up7, down7
        row["up_30d"], row["down_30d"] = up30, down30
        row["net_30d"] = (up30 or 0) - (down30 or 0) if up30 is not None or down30 is not None else None
    return data


def earnings_dates(symbol: str, limit: int = 8) -> list[dict]:
    """Recent and upcoming report dates with estimate, actual and surprise."""
    symbol = symbol.upper()

    def build() -> dict:
        frame = _ticker(symbol).get_earnings_dates(limit=limit)
        rows = []
        if frame is not None and not frame.empty:
            for idx, row in frame.iterrows():
                rows.append(
                    {
                        "date": _clean(idx),
                        "eps_estimate": _clean(row.get("EPS Estimate")),
                        "eps_actual": _clean(row.get("Reported EPS")),
                        "surprise_pct": _clean(row.get("Surprise(%)")),
                    }
                )
        return {"rows": rows}

    return cached_json(f"yf:earnings_dates:{symbol}", build, TTL_QUOTE).get("rows", [])


def next_earnings(symbol: str) -> dict | None:
    """The next scheduled report: date, consensus EPS and revenue range."""
    symbol = symbol.upper()

    def build() -> dict:
        cal = _ticker(symbol).calendar or {}
        dates = cal.get("Earnings Date") or []
        if not isinstance(dates, (list, tuple)):
            dates = [dates]
        future = [d for d in dates if isinstance(d, (date, datetime)) and _as_date(d) >= date.today()]
        return {
            "dates": [_clean(d) for d in dates],
            "next_date": _clean(future[0]) if future else None,
            "eps_avg": _clean(cal.get("Earnings Average")),
            "eps_low": _clean(cal.get("Earnings Low")),
            "eps_high": _clean(cal.get("Earnings High")),
            "revenue_avg": _clean(cal.get("Revenue Average")),
        }

    payload = cached_json(f"yf:next_earnings:{symbol}", build, TTL_QUOTE)
    return payload or None


def statements(symbol: str, *, quarterly: bool = True) -> dict:
    """Income statement and balance sheet as line-item series.

    Two extra columns are the whole point. The Nasdaq tables stop at four quarters,
    so they can only compare a quarter with the one immediately before it -- and a
    note built on that reported "revenue down 11.2% sequentially" about Paychex's May
    quarter, which grew 12.5% year over year. yfinance carries five quarters and four
    fiscal years, so every line can also be compared with the same period a year
    earlier, and a goodwill step change is visible at all.
    """
    symbol = symbol.upper()

    def build() -> dict:
        ticker = _ticker(symbol)
        income = ticker.quarterly_income_stmt if quarterly else ticker.income_stmt
        balance = ticker.quarterly_balance_sheet if quarterly else ticker.balance_sheet
        return {
            "quarterly": quarterly,
            "income_periods": _periods(income),
            "income": _series(income),
            "balance_periods": _periods(balance),
            "balance": _series(balance),
        }

    return cached_json(
        f"yf:statements:{symbol}:{int(bool(quarterly))}", build, TTL_STATEMENTS
    )


def _as_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    return value


# --------------------------------------------------------------------------
# news
# --------------------------------------------------------------------------


def news(symbol: str, limit: int = 12) -> list[dict]:
    """Yahoo's per-symbol story feed, normalised to the Nasdaq news shape.

    Yahoo is the better per-name feed: stories are genuinely tagged to the
    ticker, whereas Nasdaq's topic feed returns market roundups that merely
    mention it.
    """
    symbol = symbol.upper()

    def build() -> dict:
        try:
            raw = _ticker(symbol).news or []
        except Exception:
            raw = []
        items = []
        for entry in raw[:limit]:
            content = entry.get("content", entry) if isinstance(entry, dict) else {}
            provider = content.get("provider")
            if isinstance(provider, dict):
                provider = provider.get("displayName")
            canonical = content.get("canonicalUrl")
            if isinstance(canonical, dict):
                canonical = canonical.get("url")
            items.append(
                {
                    "title": (content.get("title") or "").strip(),
                    "publisher": provider or content.get("publisher"),
                    "published": content.get("pubDate") or content.get("displayTime"),
                    "summary": content.get("summary") or content.get("description"),
                    "url": canonical or content.get("link"),
                    "type": content.get("contentType"),
                    "source": "yahoo",
                }
            )
        return {"items": items}

    return cached_json(f"yf:news:{symbol}", build, TTL_QUOTE).get("items", [])


# --------------------------------------------------------------------------
# options
# --------------------------------------------------------------------------


def expiries(symbol: str) -> list[str]:
    """Listed option expiries, ascending ISO dates.

    An empty result is returned as ``None`` so it is **not cached**. A transient
    Yahoo failure was being stored for the full chain TTL, after which the tool
    believed a name with a full chain had none -- and the note silently lost its
    Structuring block, which reads as "no legs available" rather than "the fetch
    failed". Not caching it also lets ``cached_json`` fall back to a stale non-empty
    list instead of an empty one.
    """

    def build() -> dict | None:
        items = list(_ticker(symbol).options or [])
        return {"items": items} if items else None

    return cached_json(f"yf:expiries:{symbol.upper()}", build, TTL_CHAIN).get("items", [])


def chain(symbol: str, expiry: str) -> dict:
    """Full option chain for one expiry as plain records.

    Keeps last/bid/ask *and* open interest, because structure selection has to
    respect liquidity: a mid-price credit is fiction if the strike has no OI.
    """
    symbol = symbol.upper()

    def build() -> dict | None:
        # No try/except: swallowing the failure would cache an empty chain, and an
        # empty chain is indistinguishable from an illiquid strike to everything
        # downstream. Letting it raise keeps the stale entry usable instead.
        ch = _ticker(symbol).option_chain(expiry)

        def rows(frame) -> list[dict]:
            out = []
            for _, row in frame.iterrows():
                out.append(
                    {
                        "strike": _clean(row.get("strike")),
                        "last": _clean(row.get("lastPrice")),
                        "bid": _clean(row.get("bid")),
                        "ask": _clean(row.get("ask")),
                        "mid": _mid(_clean(row.get("bid")), _clean(row.get("ask"))),
                        "volume": _clean(row.get("volume")),
                        "open_interest": _clean(row.get("openInterest")),
                        "implied_vol": _clean(row.get("impliedVolatility")),
                        "in_the_money": bool(row.get("inTheMoney")),
                    }
                )
            return out

        return {"calls": rows(ch.calls), "puts": rows(ch.puts), "expiry": expiry}

    return cached_json(f"yf:chain:{symbol}:{expiry}", build, TTL_CHAIN)


def price_change_pct(symbol: str, days: int = 30) -> float | None:
    """Percent price change over roughly ``days`` calendar days.

    No longer feeds the score in :mod:`fig.discover`, which ranks on the consensus
    revision alone; it is still shown on the screen table as context. The horizon is
    padded because markets close at weekends and on holidays: asking for exactly
    ``days`` bars would silently measure a different window.
    """
    symbol = symbol.upper()

    def build() -> dict:
        try:
            history = _ticker(symbol).history(period="6mo", interval="1d", auto_adjust=False)
        except Exception:
            return {"change_pct": None}
        if history is None or history.empty:
            return {"change_pct": None}
        closes = history["Close"].dropna()
        if len(closes) < 2:
            return {"change_pct": None}
        # ~21 trading days per calendar month.
        lookback = min(len(closes) - 1, max(1, round(days / 30 * 21)))
        latest = float(closes.iloc[-1])
        past = float(closes.iloc[-1 - lookback])
        if not past:
            return {"change_pct": None}
        return {"change_pct": round((latest - past) / past * 100.0, 2), "lookback_days": days}

    return cached_json(f"yf:price_change:{symbol}:{days}", build, TTL_QUOTE).get("change_pct")


def _mid(bid: float | None, ask: float | None) -> float | None:
    if bid and ask:
        return round((bid + ask) / 2, 2)
    return bid or ask
