"""The earnings catalyst, dated and justified.

Why this is its own module
--------------------------
The catalyst *is* the trade: it sets when a thesis gets tested. The references
make this explicit -- the OMF note's whole structure exists because
"targeting earnings in late January, allowing two quarters for the worsening
consumer debt story to play out". That sentence does three jobs at once:

1. **the date**         -- late January
2. **the mechanism**    -- credit deterioration needs two quarters to show
3. **the payoff**       -- a $36 target, ~40% downside

The option legs are a second-order detail on top of that, which is why this
module exists separately from :mod:`fig.options` and why a note can be produced
when no usable option chain exists at all.

What is measured, and what is left to prose
-------------------------------------------
Measured here: the exact date, whether it is scheduled or projected, the days
remaining, the session (before the open / after the close), the consensus for
that report, and the company's recent record against consensus. Those are facts.

Left to the writer: *why that date matters for this particular thesis*. A date is
not a justification, so the note carries a short `why` in the author's own words
on top of the measured line.
"""

from __future__ import annotations

import statistics
from datetime import date, datetime, timedelta

from .prompts import WORD_BUDGET
from .sources import yahoo

# A report at or before 09:00 ET is before the open; at or after 16:00 is after
# the close. Anything between is ambiguous and reported as unknown rather than
# guessed, because it changes whether the trade can react same-day.
PRE_OPEN_HOUR = 9
POST_CLOSE_HOUR = 16

# Two dates within this many days of each other, a year apart, are "the same slot".
SAME_SLOT_DAYS = 12

RECENT_REPORTS = 4


def _parse(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(raw)[: len(fmt) + 4], fmt)
        except ValueError:
            continue
    return None


def _session(moment: datetime | None) -> str | None:
    if moment is None:
        return None
    # The offset in the source string carries the exchange-local hour already.
    hour = moment.hour
    if hour <= PRE_OPEN_HOUR:
        return "before the open"
    if hour >= POST_CLOSE_HOUR:
        return "after the close"
    return None


def build_catalyst(symbol: str) -> dict:
    """Everything needed to state and justify the next earnings date."""
    today = date.today()

    scheduled: list[tuple[date, datetime | None, dict]] = []
    for row in yahoo.earnings_dates(symbol, limit=16):
        moment = _parse(row.get("date"))
        if not moment:
            continue
        moment_date = moment.date()
        if moment_date >= today:
            scheduled.append((moment_date, moment, row))

    scheduled.sort(key=lambda r: r[0])

    basis = "scheduled"
    target_date: date | None = None
    session: str | None = None
    consensus: dict = {}

    if scheduled:
        target_date, moment, row = scheduled[0]
        session = _session(moment)
        consensus = {
            "eps_avg": row.get("eps_estimate"),
            "eps_low": row.get("eps_low"),
            "eps_high": row.get("eps_high"),
            "revenue_avg": row.get("revenue_avg"),
        }

    # Fall back to the projection used by the options layer, and say so.
    if target_date is None:
        try:
            from . import options as options_mod

            projected = [d for d in options_mod.upcoming_earnings(symbol) if d >= today]
            if projected:
                target_date = min(projected)
                basis = "estimated"
        except Exception:
            pass

    # The consensus block from Nasdaq is richer for the *next* report than the
    # per-date estimate Yahoo returns, so prefer it when the dates agree.
    next_block = yahoo.next_earnings(symbol) or {}
    if target_date and str(next_block.get("next_date"))[:10] == target_date.isoformat():
        consensus = {
            "eps_avg": next_block.get("eps_avg") or consensus.get("eps_avg"),
            "eps_low": next_block.get("eps_low") or consensus.get("eps_low"),
            "eps_high": next_block.get("eps_high") or consensus.get("eps_high"),
            "revenue_avg": next_block.get("revenue_avg") or consensus.get("revenue_avg"),
        }

    # History: most recent reported quarters, newest first.
    history: list[dict] = []
    for row in yahoo.earnings_dates(symbol, limit=16):
        moment = _parse(row.get("date"))
        if not moment or moment.date() >= today:
            continue
        actual, estimate = row.get("eps_actual"), row.get("eps_estimate")
        history.append(
            {
                "date": moment.date().isoformat(),
                "eps_estimate": estimate,
                "eps_actual": actual,
                "surprise_pct": row.get("surprise_pct"),
                "beat": (actual is not None and estimate is not None and actual >= estimate),
            }
        )
    history.sort(key=lambda h: h["date"], reverse=True)
    recent = history[:RECENT_REPORTS]

    beat_streak = 0
    for row in recent:
        if row["beat"]:
            beat_streak += 1
        else:
            break

    report_dates = sorted(date.fromisoformat(h["date"]) for h in history)
    gaps = [
        (report_dates[i + 1] - report_dates[i]).days
        for i in range(len(report_dates) - 1)
        if 45 <= (report_dates[i + 1] - report_dates[i]).days <= 200
    ]
    median_gap = int(statistics.median(gaps)) if gaps else None

    # Did the company report in about the same calendar slot a year ago? This is
    # what makes a projected date credible and a scheduled one unsurprising.
    same_slot_last_year = None
    if target_date:
        for row in history:
            past = date.fromisoformat(row["date"])
            if 330 <= (target_date - past).days <= 400:
                delta = abs(
                    (target_date - timedelta(days=365)) - past
                ).days
                same_slot_last_year = delta <= SAME_SLOT_DAYS
                break

    days_out = (target_date - today).days if target_date else None

    catalyst = {
        "date": target_date.isoformat() if target_date else None,
        "weekday": target_date.strftime("%A") if target_date else None,
        "days_out": days_out,
        "basis": basis,
        "session": session,
        "consensus": {k: v for k, v in consensus.items() if v is not None},
        "recent_reports": recent,
        "beat_streak": beat_streak,
        "beat_rate": round(sum(1 for h in recent if h["beat"]) / len(recent), 2) if recent else None,
        "median_gap_days": median_gap,
        "same_slot_last_year": same_slot_last_year,
    }
    catalyst["facts_line"] = facts_line(catalyst)
    return catalyst


def facts_line(catalyst: dict) -> str:
    """The measured half of the justification, as one plain sentence.

    This is always present in a note even if the writer's own `why` is missing,
    so a note can never end up asserting a catalyst without saying where the date
    came from.
    """
    if not catalyst.get("date"):
        return "No future earnings date is available from the free sources."

    parts = [f"{catalyst['date']} ({catalyst.get('weekday') or 'weekday unknown'}"]
    if catalyst.get("session"):
        parts.append(f", {catalyst['session']}")
    parts.append(")")

    if catalyst.get("days_out") is not None:
        parts.append(f", {catalyst['days_out']} days out")

    if catalyst.get("basis") == "estimated":
        gap = catalyst.get("median_gap_days")
        parts.append(
            f" -- estimated from the reporting pattern"
            + (f", a median gap of {gap} days" if gap else "")
            + "; no scheduled date is published yet"
        )
    else:
        parts.append(" -- from the earnings calendar")

    eps = (catalyst.get("consensus") or {}).get("eps_avg")
    if eps is not None:
        # Two decimals: the sources carry full float precision (1.87559), which
        # reads as noise in a note whose whole point is plain language.
        parts.append(f", consensus EPS {eps:.2f}".rstrip("0").rstrip("."))

    return "".join(parts) + "."


def _justification_facts_keyed(catalyst: dict) -> list[tuple[str, str]]:
    """The justification facts, each tagged with a stable key.

    The key exists so :func:`fallback_why` can prefer the fact that speaks to what
    the print has to *prove* over the ones that only date it. Callers that just
    want the sentences use :func:`justification_facts`.
    """
    facts: list[tuple[str, str]] = []
    if not catalyst.get("date"):
        return facts

    if catalyst.get("same_slot_last_year"):
        facts.append(
            ("same_slot", "The company reported in about the same calendar slot a year ago.")
        )
    if catalyst.get("median_gap_days"):
        facts.append(
            (
                "cadence",
                f"Reports roughly every {catalyst['median_gap_days']} days "
                "(one quarter), so the date is consistent with its own cadence.",
            )
        )
    streak = catalyst.get("beat_streak")
    if streak:
        facts.append(
            (
                "beat_streak",
                f"Beat consensus in each of the last {streak} reports, so the bar is "
                "already high and a miss is what moves the stock.",
            )
        )
    rate = catalyst.get("beat_rate")
    if rate is not None and not streak:
        facts.append(("beat_rate", f"Beat consensus in {rate:.0%} of the last few reports."))

    if catalyst.get("basis") == "estimated":
        facts.append(
            (
                "estimated",
                "No date is published yet, so this is projected from the historical "
                "reporting gap -- treat it as approximate.",
            )
        )
    return facts


def justification_facts(catalyst: dict) -> list[str]:
    """Plain facts a writer can use to justify the date. No conclusions."""
    return [text for _key, text in _justification_facts_keyed(catalyst)]


# Preference order for the fallback sentence: the beat record first, because it
# names the bar the print has to clear, then the facts that only date the report.
_FALLBACK_PRIORITY = ("beat_streak", "beat_rate", "cadence", "estimated", "same_slot")


def fallback_why(catalyst: dict, max_words: int | None = None) -> str:
    """One budget-safe sentence, used only when the writer supplied no ``why``.

    A note must never assert a catalyst without justifying it, so something has to
    fill the block. The filler also has to be a line this repo's own linter accepts:
    the previous fallback joined **every** fact that fired into one line, which
    produced 51 words against a 25-word budget as soon as two of them applied. That
    breach is an *error*, so the note could never converge -- and the repair round
    made it permanent, because the revision's required shape omitted ``catalyst_why``
    and so erased the writer's own line on every retry (see
    :func:`fig.generate._repair_messages`). ORCL shipped with exactly that defect.

    So: pick the single most useful fact that fits, and truncate to the budget as a
    last resort rather than ever returning an over-long line.
    """
    from .lint import word_count  # local: the linter's own notion of a word

    budget = WORD_BUDGET["catalyst_why"] if max_words is None else max_words
    keyed = _justification_facts_keyed(catalyst)
    if not keyed:
        return ""

    rank = {key: index for index, key in enumerate(_FALLBACK_PRIORITY)}
    ordered = sorted(keyed, key=lambda pair: rank.get(pair[0], len(rank)))
    for _key, text in ordered:
        if word_count(text) <= budget:
            return text

    # Nothing fits, so keep the most useful fact and cut it to the budget.
    words = ordered[0][1].split()
    return " ".join(words[:budget]).rstrip(" ,;:-") + "."

