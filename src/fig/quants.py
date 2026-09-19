"""The **Quants** block: turn raw source payloads into the short factual panel.

Every reference writeup carries a ``Quants`` block whose job is to let a reader
sanity-check the thesis in about five seconds. The lines that actually appear
across the references are:

    Price: 60.94 USD
    Market Cap: 7.07B
    Fwd PE: 7.7
    EPS trends: slightly down over the last 7 days
    EPS revisions: Split equally, with 5 up and 10 down over last 30 days
    Q2 reported increasing provisions and managed receivables
    Q2 EPS declined year-over-year.

Two of those are *derived prose*, not raw fields: the EPS trend direction and the
revision split. :func:`describe_trend` and :func:`describe_revisions` generate
that wording from the numbers so the panel can never disagree with the data.

The ``Q2 reported ...`` lines are observations pulled out of the financial
statements by :func:`fundamental_deltas`, which compares the two most recent
quarterly columns and reports the largest moves. That is what turns a statement
table into a citable fact.
"""

from __future__ import annotations

from datetime import date

from .sources import nasdaq, yahoo
from .util import human_money

# --------------------------------------------------------------------------
# wording generators
# --------------------------------------------------------------------------


def describe_trend(chg_pct: float | None, window: str = "7 days") -> str:
    """Wording for the ``EPS trends`` line, e.g. ``slightly down over the last 7 days``.

    Bands are deliberately coarse -- the point is direction and rough size, not
    precision. A 0.1% drift is noise and must read as flat, otherwise every name
    looks like it has momentum.
    """
    if chg_pct is None:
        return "no revision history"
    size = abs(chg_pct)
    if size < 0.15:
        return f"flat over the last {window}"
    if size < 1.0:
        return f"slightly {'down' if chg_pct < 0 else 'up'} over the last {window}"
    if size < 3.0:
        return f"{'down' if chg_pct < 0 else 'up'} over the last {window}"
    return f"sharply {'down' if chg_pct < 0 else 'up'} over the last {window}"


def describe_revisions(up: float | None, down: float | None, window: str = "30 days") -> str:
    """Wording for the ``EPS revisions`` line, always including the raw counts.

    The counts matter more than the adjective: "5 up and 10 down" is checkable,
    "tilted lower" is not. Note the ORCL/OMF references use the phrase "split
    equally" for a 5/10 split, which is not literally even -- we emit an accurate
    tilt word and let the counts carry the meaning.
    """
    up, down = up or 0, down or 0
    total = up + down
    if total == 0:
        return f"no revisions over last {window}"
    if down == 0:
        tilt = "all up"
    elif up == 0:
        tilt = "all down"
    else:
        share = up / total
        if 0.45 <= share <= 0.55:
            tilt = "evenly split"
        elif share > 0.55:
            tilt = "tilted higher"
        else:
            tilt = "tilted lower"
    return f"{tilt}, with {up:g} up and {down:g} down over last {window}"


# --------------------------------------------------------------------------
# panel assembly
# --------------------------------------------------------------------------


def _period(trend: dict, period: str) -> dict:
    for row in trend.get("periods", []):
        if row.get("period") == period:
            return row
    return {}


def quants_panel(symbol: str) -> dict:
    """Everything needed to render the Quants block, plus the numbers behind it.

    ``fwd_pe`` is reported on the **current-fiscal-year** basis because that is
    what the reference writeups quote (see :mod:`fig.sources.yahoo`). The one-year
    basis is returned alongside as ``fwd_pe_1y``; never compare across names
    without picking one.
    """
    symbol = symbol.upper()
    val = yahoo.valuation(symbol)
    trend = yahoo.eps_trend(symbol)
    revisions = yahoo.eps_revisions(symbol)

    cur_fy = _period(trend, "0y")
    next_fy = _period(trend, "+1y")
    cur_q = _period(trend, "0q")

    # Revision counts: prefer the current fiscal year row, fall back to quarter.
    rev_fy = _period(revisions, "0y") or _period(revisions, "0q")
    up30 = rev_fy.get("up_30d")
    down30 = rev_fy.get("down_30d")
    up7 = rev_fy.get("up_7d")
    down7 = rev_fy.get("down_7d")

    trend_chg = cur_fy.get("chg_7d_pct")
    if trend_chg is None:
        trend_chg = cur_q.get("chg_7d_pct")

    price = val.get("price")

    panel = {
        "symbol": symbol,
        "name": val.get("name"),
        "price": price,
        "market_cap": val.get("market_cap"),
        "market_cap_human": human_money(val.get("market_cap")),
        "fwd_pe": val.get("fwd_pe_0y"),
        "fwd_pe_1y": val.get("fwd_pe_1y"),
        "fwd_pe_yahoo": val.get("yf_forward_pe"),
        "trailing_pe": val.get("trailing_pe"),
        "ps": val.get("ps"),
        "ev_ebitda": val.get("ev_ebitda"),
        "sector": val.get("sector"),
        "industry": val.get("industry"),
        "eps_fy_current": cur_fy.get("current"),
        "eps_fy_next": next_fy.get("current"),
        "eps_trend": {
            "change_7d_pct": trend_chg,
            "change_30d_pct": cur_fy.get("chg_30d_pct"),
            "current": cur_fy.get("current"),
            "7d_ago": cur_fy.get("7daysAgo"),
            "30d_ago": cur_fy.get("30daysAgo"),
            "text": describe_trend(trend_chg),
        },
        "eps_revisions": {
            "up_7d": up7,
            "down_7d": down7,
            "up_30d": up30,
            "down_30d": down30,
            "net_30d": rev_fy.get("net_30d"),
            "text": describe_revisions(up30, down30),
        },
        "next_earnings": yahoo.next_earnings(symbol),
        "as_of": date.today().isoformat(),
    }
    return panel


def quants_lines(panel: dict) -> list[str]:
    """Render the panel as the terse lines used in a writeup."""
    lines = [
        f"Price: {panel['price']:.2f} USD" if panel.get("price") else "Price: n/a",
        f"Market Cap: {panel['market_cap_human']}",
        f"Fwd PE: {panel['fwd_pe']}" if panel.get("fwd_pe") else "Fwd PE: n/a",
    ]
    if panel.get("ps"):
        lines.append(f"P/S: {panel['ps']:.1f}")
    lines.append(f"EPS trends: {panel['eps_trend']['text']}")
    lines.append(f"EPS revisions: {panel['eps_revisions']['text']}")
    return lines


# --------------------------------------------------------------------------
# fundamental deltas
# --------------------------------------------------------------------------

# Line items worth reporting if they move. Anything not here is noise for an
# idea writeup (Goodwill, Common Stocks, ...).
_WATCH = {
    "Total Revenue",
    "Net Income",
    "Net Income Applicable to Common Shareholders",
    "Earnings Before Interest and Tax",
    "Other Operating Items",
    "Sales, General and Admin.",
    "Net Receivables",
    "Total Liabilities",
    "Total Equity",
    "Long-Term Investments",
    "Cash and Cash Equivalents",
    "Provision for Loan Losses",
    "Provision for Credit Losses",
}

# Names that usually mean "credit losses are coming".
_CREDIT_HINTS = ("provision", "charge-off", "charge off", "allowance", "reserve")


def fundamental_deltas(
    symbol: str, *, min_pct: float = 5.0, top: int = 6, quarterly: bool = True
) -> list[dict]:
    """Most notable period-over-period moves in the statements.

    Compares the newest quarterly column to the one before it and returns the
    largest percentage moves with a direction word. This is the mechanism behind
    reference lines such as ``Q2 reported increasing provisions and managed
    receivables``.

    Each item: ``{label, period, prior_period, current, prior, change_pct,
    direction, is_credit}``. Rows where either period is missing or the prior is
    zero are skipped, since a percentage off zero is meaningless.
    """
    try:
        tables = nasdaq.financials(symbol, quarterly=quarterly)
    except Exception:
        return []

    found: list[dict] = []
    for table_name, table in tables.items():
        periods = table.get("periods") or []
        if len(periods) < 2:
            continue
        current_period, prior_period = periods[0], periods[1]

        for row in table.get("rows") or []:
            label = row.get("label") or ""
            values = row.get("values") or []
            if len(values) < 2:
                continue
            current, prior = values[0], values[1]
            if current is None or prior in (None, 0):
                continue

            lowered = label.lower()
            interesting = label in _WATCH or any(h in lowered for h in _CREDIT_HINTS)
            if not interesting:
                continue

            change = (current - prior) / abs(prior) * 100.0
            if abs(change) < min_pct:
                continue

            found.append(
                {
                    "label": label,
                    "table": table_name,
                    "period": current_period,
                    "prior_period": prior_period,
                    "current": current,
                    "prior": prior,
                    "change_pct": round(change, 1),
                    "direction": "increasing" if change > 0 else "decreasing",
                    "is_credit": any(h in lowered for h in _CREDIT_HINTS),
                }
            )

    found.sort(key=lambda r: abs(r["change_pct"]), reverse=True)
    return found[:top]


def eps_yoy(symbol: str) -> dict | None:
    """Reported EPS this quarter vs the same quarter a year ago.

    Produces the reference line ``Q2 EPS declined year-over-year``. Matches on
    report dates ~330-400 days apart rather than assuming a fixed offset, because
    fiscal calendars drift.
    """
    rows = [r for r in yahoo.earnings_dates(symbol, limit=12) if r.get("eps_actual") is not None]
    if len(rows) < 5:
        return None

    def parse(stamp: str):
        from datetime import date as _d

        return _d.fromisoformat(str(stamp)[:10])

    rows = sorted(rows, key=lambda r: parse(r["date"]), reverse=True)
    latest = rows[0]
    latest_date = parse(latest["date"])

    for candidate in rows[1:]:
        gap = (latest_date - parse(candidate["date"])).days
        if 330 <= gap <= 400:
            change = latest["eps_actual"] - candidate["eps_actual"]
            return {
                "period": latest["date"],
                "current": latest["eps_actual"],
                "year_ago": candidate["eps_actual"],
                "year_ago_period": candidate["date"],
                "change": round(change, 3),
                "direction": "increased" if change > 0 else "declined" if change < 0 else "flat",
            }
    return None
