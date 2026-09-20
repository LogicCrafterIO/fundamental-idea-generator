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

    # The same figure is reported under several labels -- "Net Income" and "Net
    # Income Applicable to Common Shareholders" are the same number, and Nasdaq
    # repeats some rows across tables. Without this, a Quants block shows the
    # identical move twice and wastes one of its few lines.
    deduped: list[dict] = []
    seen: set[tuple[str, int]] = set()
    for item in found:
        key = (item["period"], round(abs(item["change_pct"])))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped[:top]


# Lines where a sequential move must be read against the year-earlier quarter. A
# quarter can fall 11% from the one before it and still grow 12% year over year --
# which is exactly what Paychex's May quarter did, and what a note reported as
# "revenue down 11.2% sequentially" without the other half.
_YOY_WATCH = (
    "Total Revenue",
    "Net Income",
    "Net Income Common Stockholders",
    "EBIT",
    "EBITDA",
    "Operating Income",
    "Gross Profit",
    "Interest Expense",
    "Interest Income",
    "Net Interest Income",
    "Selling General And Administration",
    "Provision for Loan Losses",
    "Provision for Credit Losses",
)

# The two sources name the same line differently, and the conflict check compares a
# Nasdaq delta against a yfinance series. Without this the check silently misses the
# lines whose names differ -- including EBIT, which is where a leveraged acquisition
# shows up.
_LABEL_ALIASES = {
    "Earnings Before Interest and Tax": "EBIT",
    "Net Income Applicable to Common Shareholders": "Net Income",
    "Net Income-Cont. Operations": "Net Income",
    "Sales, General and Admin.": "Selling General And Administration",
    "Common Stocks": "Common Stock",
}


def canonical_label(label: str) -> str:
    """The name a line has in whichever statement source uses the other convention."""
    return _LABEL_ALIASES.get(label, label)

# Balance-sheet lines that step up when a deal closes. Goodwill is excluded from the
# Quants panel as noise, and it is the one line that cannot move for any other reason:
# goodwill is created by purchase accounting alone, so a step in it proves an
# acquisition. Intangibles can also grow from capitalised contracts or a
# reclassification, so a step there is only suggestive and is reported as such.
_CONFIRMED_DEAL_LINES = ("Goodwill", "Goodwill And Intangible Assets")
_SUSPECTED_DEAL_LINES = ("Other Intangible Assets", "Intangible Assets")
_DEAL_LINES = _CONFIRMED_DEAL_LINES + _SUSPECTED_DEAL_LINES
_DEAL_STEP_PCT = 25.0

# Both legs of a sequential/annual disagreement have to be material before it counts
# as one: interest expense down 5% on the quarter and up 1.6% on the year is a wiggle,
# and flagging it beside a genuine 11% versus 12% reversal is how a warning becomes
# noise a reader learns to skip.
_CONFLICT_MIN_PCT = 2.0


def _month_day(period: str) -> tuple[int, int] | None:
    try:
        _, month, day = str(period)[:10].split("-")
        return int(month), int(day)
    except (ValueError, AttributeError):
        return None


def _year_ago_index(periods: list[str]) -> int | None:
    """The column that is the same quarter a year earlier, if the series has it.

    Matched on a 330-400 day gap rather than a fixed offset of four columns, because
    fiscal calendars drift and a column can be missing.
    """
    if len(periods) < 2:
        return None
    from datetime import date as _d

    try:
        newest = _d.fromisoformat(periods[0][:10])
    except ValueError:
        return None
    for index, period in enumerate(periods[1:], start=1):
        try:
            gap = (newest - _d.fromisoformat(str(period)[:10])).days
        except ValueError:
            continue
        if 330 <= gap <= 400:
            return index
    return None


def _change(current: float | None, prior: float | None) -> float | None:
    if current is None or prior in (None, 0):
        return None
    return round((current - prior) / abs(prior) * 100.0, 1)


def yoy_deltas(symbol: str, *, top: int = 8) -> list[dict]:
    """Each line's quarter-over-quarter move *and* its year-over-year move.

    One row per line, so the two comparisons cannot be separated: the packet shows
    them side by side and the linter can require a reason that quotes one to quote
    the other. Rows: ``{label, period, prior_period, current, prior, qoq_pct,
    year_ago_period, year_ago, yoy_pct, conflict}`` where ``conflict`` is true when
    the two comparisons point in opposite directions.
    """
    try:
        data = yahoo.statements(symbol, quarterly=True)
    except Exception:
        return []

    periods = data.get("income_periods") or []
    income = data.get("income") or {}
    if len(periods) < 2:
        return []
    yago = _year_ago_index(periods)

    rows: list[dict] = []
    seen: set[tuple] = set()
    for label in _YOY_WATCH:
        values = income.get(label)
        if not values or not values[0]:
            continue
        qoq = _change(values[0], values[1] if len(values) > 1 else None)
        yoy = _change(values[0], values[yago] if yago is not None and yago < len(values) else None)
        if qoq is None and yoy is None:
            continue
        # Two labels can carry one line ("Net Income" and "Net Income Common
        # Stockholders"); printing both wastes the writer's attention on a duplicate.
        fingerprint = (values[0], qoq, yoy)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        rows.append(
            {
                "label": label,
                "period": periods[0],
                "prior_period": periods[1],
                "current": values[0],
                "prior": values[1] if len(values) > 1 else None,
                "qoq_pct": qoq,
                "year_ago_period": periods[yago] if yago is not None else None,
                "year_ago": values[yago] if yago is not None and yago < len(values) else None,
                "yoy_pct": yoy,
                # The failure this exists for: a sequential fall reported as if it
                # were the trend, when the year-earlier comparison rose.
                "conflict": bool(
                    qoq is not None
                    and yoy is not None
                    and (qoq < 0) != (yoy < 0)
                    and abs(qoq) >= _CONFLICT_MIN_PCT
                    and abs(yoy) >= _CONFLICT_MIN_PCT
                ),
            }
        )
    return rows[:top]


def annual_deltas(symbol: str, *, min_pct: float = 5.0, top: int = 6) -> list[dict]:
    """Fiscal-year-over-fiscal-year moves, the slower-moving comparison.

    A quarterly column can be distorted by a deal, a rate move or a calendar; the
    annual series is what says whether the business is growing at all. Paychex's
    FY26 revenue grew 16.9% on this comparison while its May quarter fell 11.2% on
    the sequential one.
    """
    try:
        data = yahoo.statements(symbol, quarterly=False)
    except Exception:
        return []

    periods = data.get("income_periods") or []
    income = data.get("income") or {}
    if len(periods) < 2:
        return []

    rows: list[dict] = []
    for label in _YOY_WATCH:
        values = income.get(label)
        if not values or len(values) < 2:
            continue
        change = _change(values[0], values[1])
        if change is None:
            continue
        rows.append(
            {
                "label": label,
                "period": periods[0],
                "prior_period": periods[1],
                "current": values[0],
                "prior": values[1],
                "change_pct": change,
                "direction": "increasing" if change > 0 else "decreasing",
            }
        )

    # Revenue and net income are kept even when a rate or deal line moved further:
    # "is the business growing" is the question the annual comparison is asked for,
    # and a top-6-by-magnitude cut can drop both of them.
    must = ("Total Revenue", "Net Income", "Net Income Applicable to Common Shareholders")
    kept = [r for r in rows if r["label"] in must][:2]
    rest = sorted(
        (r for r in rows if r not in kept and abs(r["change_pct"]) >= min_pct),
        key=lambda r: abs(r["change_pct"]),
        reverse=True,
    )
    return (kept + rest)[:top]


def deal_activity(symbol: str) -> list[dict]:
    """Step changes in goodwill or intangibles: the footprint of an acquisition.

    Reported growth in a period that contains a deal is not organic growth, and a
    thesis that treats it as organic is wrong in a way no amount of prose discipline
    fixes -- the note on Paychex argued from a sequential revenue fall without
    knowing that Paycor had added most of the year's growth. This finds the deal on
    the balance sheet, which is available for every filer, rather than relying on the
    writer to remember it.

    Each row carries ``confidence``: ``confirmed`` when **goodwill** stepped, which
    only purchase accounting does, and ``suspected`` when only intangibles moved --
    those can also grow from capitalised contracts. The linter treats the two
    differently, so a suspected deal cannot force a writer to name an acquisition
    that may not exist.
    """
    steps: dict[str, list[dict]] = {}
    for quarterly in (False, True):
        try:
            data = yahoo.statements(symbol, quarterly=quarterly)
        except Exception:
            continue
        periods = data.get("balance_periods") or []
        balance = data.get("balance") or {}
        basis = "quarter" if quarterly else "fiscal year"
        # Only the newest steps in each series count: a deal three years ago is not
        # today's growth story, and raising it would be noise on most balance sheets.
        reach = 4 if quarterly else 2
        for label in _DEAL_LINES:
            values = balance.get(label)
            if not values or len(values) < 2:
                continue
            for index in range(min(reach, len(values) - 1)):
                current, prior = values[index], values[index + 1]
                if current is None or prior in (None, 0):
                    continue
                change = _change(current, prior)
                if change is None or change < _DEAL_STEP_PCT:
                    continue
                key = f"{basis}:{periods[index] if index < len(periods) else index}"
                steps.setdefault(key, []).append(
                    {
                        "label": label,
                        "basis": basis,
                        "period": periods[index] if index < len(periods) else None,
                        "prior_period": periods[index + 1] if index + 1 < len(periods) else None,
                        "current": current,
                        "prior": prior,
                        "change_pct": change,
                        "confirmed": label in _CONFIRMED_DEAL_LINES,
                    }
                )

    out: list[dict] = []
    for key, rows in steps.items():
        # Goodwill leads when both lines moved: it is the fact, and intangibles is
        # the corroboration.
        primary = next((r for r in rows if r["confirmed"]), max(rows, key=lambda r: r["change_pct"]))
        others = [r for r in rows if r is not primary]
        out.append({**primary, "also": others[:2]})
    out.sort(key=lambda r: (not r["confirmed"], str(r.get("period") or "")))
    return out[:2]


def consensus_bar(panel: dict) -> dict | None:
    """The number the next print has to beat, and the last one that did or did not.

    A note that says only "estimates were cut" leaves out the bar, which is what the
    reaction is actually measured against.
    """
    nxt = panel.get("next_earnings") or {}
    if not nxt:
        return None
    bar = {
        "date": nxt.get("next_date") or (nxt.get("dates") or [None])[0],
        "eps_avg": nxt.get("eps_avg"),
        "eps_low": nxt.get("eps_low"),
        "eps_high": nxt.get("eps_high"),
        "revenue_avg": nxt.get("revenue_avg"),
    }
    if bar["eps_avg"] is None and bar["revenue_avg"] is None:
        return None
    return bar


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
