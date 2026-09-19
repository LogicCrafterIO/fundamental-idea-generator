"""**Structuring**: build the option spread that expresses an idea, and check it.

The two reference writeups turn out to be almost fully determined by a handful of
rules, which this module encodes. Each rule below was reverse-engineered from the
ORCL and OMF examples and then verified against live chains on 2026-09-19:

1. **Shape.** Buy one far-dated leg; sell a nearer-dated leg at the *same*
   strike. Both references are near-vertical calendars (a "diagonal" only in the
   sense of different expiries). Direction sets the option type: long idea ->
   calls, short idea -> puts.

2. **The short leg expires before the catalyst.** ORCL short 16-Oct-26 vs next
   earnings 11-Dec-26; OMF short 16-Oct-26 vs next earnings 30-Oct-26. Both
   shorts die *before* the event, so they decay without event risk.

3. **The long leg expires after the catalyst.** ORCL long 18-Dec-26 sits just
   past the 11-Dec-26 report; OMF long 19-Feb-27 sits past the late-Jan-27
   report. ``catalyst_index`` selects which upcoming report the thesis needs
   (OMF's author deliberately chose the *second* one: "allowing two quarters for
   the worsening consumer debt story to play out").

4. **Strike = the nearest common OTM strike to ~4% out of the money.** The strike
   must be listed in *both* expiries. OMF's 60 strike exists in the Oct-26 chain
   but not the Feb-27 chain, which is why 57.5 was used. ORCL: price 150 -> 155
   (+3.3%) beats the ATM 150.

5. **Size = ~$4,500 of long premium.** ORCL 3x15.55x100 = $4,665; OMF
   14x3.20x100 = $4,480.

6. **Credit floor = 10%**, where *credit ratio* is the definition that makes both
   references' prose work out::

       credit ratio = short premium collected / long premium paid

   OMF: 0.65*7 / (3.20*14) = 10.16%  -> "very slightly above the 10% floor"
   ORCL: 6.44*2 / (15.55*3) = 27.6%  -> "even if I halved it, it would be 13%"

   Short quantity is then solved to land on a target ratio.

Pricing convention matters for rule 6. A mid-price credit is optimistic: you
really *pay the ask* on the long and *receive the bid* on the short. Both are
computed -- ``credit_ratio_mid`` for the writeup and
``credit_ratio_conservative`` for the honest check.
"""

from __future__ import annotations

import calendar
import statistics
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .sources import yahoo

DEFAULT_CAPITAL = 4500.0  # per-structure long premium budget (see rule 5)
DEFAULT_OTM = 0.04  # target strike distance OTM (rule 4)
DEFAULT_CREDIT_TARGET = 0.12  # aim just above the 10% floor (rule 6)
CREDIT_FLOOR = 0.10  # hard minimum from the references
CONTRACT = 100  # shares per contract


# --------------------------------------------------------------------------
# date helpers
# --------------------------------------------------------------------------


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _fmt_expiry(value: str) -> str:
    """ISO expiry -> the writeup's ``16-Oct-26`` form."""
    parsed = _as_date(value)
    return parsed.strftime("%d-%b-%y") if parsed else str(value)


def upcoming_earnings(symbol: str) -> list[date]:
    """Future report dates, ascending, de-duplicated.

    yfinance only exposes the *next* scheduled report, but a thesis sometimes
    needs the one after that (the OMF reference deliberately targets the second
    report: "allowing two quarters for the worsening consumer debt story to play
    out"). So when fewer than ``MIN_PROJECTED`` dates are known we project
    forward using the median gap of historical reports, which for a quarterly
    reporter is ~91 days.
    """
    today = date.today()
    known: list[date] = []

    nxt = yahoo.next_earnings(symbol) or {}
    for raw in nxt.get("dates") or []:
        parsed = _as_date(raw)
        if parsed and parsed >= today:
            known.append(parsed)

    historical: list[date] = []
    for row in yahoo.earnings_dates(symbol, limit=12):
        parsed = _as_date(row.get("date"))
        if not parsed:
            continue
        if row.get("eps_actual") is None and parsed >= today:
            known.append(parsed)
        elif parsed < today:
            historical.append(parsed)

    dates = sorted(set(known))

    # Project additional future reports from the historical cadence.
    if historical and len(dates) < MIN_PROJECTED_FUTURE:
        historical.sort()
        gaps = [
            (historical[i + 1] - historical[i]).days
            for i in range(len(historical) - 1)
            if 45 <= (historical[i + 1] - historical[i]).days <= 200
        ]
        step = int(statistics.median(gaps)) if gaps else 91
        anchor = dates[-1] if dates else max(historical)
        while len(dates) < MIN_PROJECTED_FUTURE:
            anchor = anchor + timedelta(days=step)
            if anchor not in dates:
                dates.append(anchor)
        dates.sort()

    return dates


MIN_PROJECTED_FUTURE = 3


# --------------------------------------------------------------------------
# monthly expiry detection
# --------------------------------------------------------------------------


def _nth_weekday(year: int, month: int, weekday: int = 4, n: int = 3) -> int:
    """Day-of-month of the nth given weekday (Monday=0; Friday=4)."""
    weeks = calendar.monthcalendar(year, month)
    days = [week[weekday] for week in weeks if week[weekday] != 0]
    return days[n - 1]


def is_monthly_expiry(expiry: str, tolerance_days: int = 1) -> bool:
    """True for a standard monthly expiry, i.e. the third Friday of its month.

    All four legs of the two reference writeups are monthlies -- ORCL 16-Oct-26
    and 18-Dec-26, OMF 16-Oct-26 and 19-Feb-27. Weeklies are listed too (ORCL has
    10/02, 10/09, 10/23, ...) but are skipped because they carry worse liquidity
    for the same job. A one-day tolerance absorbs exchange holiday shifts.
    """
    parsed = _as_date(expiry)
    if not parsed:
        return False
    third_friday = _nth_weekday(parsed.year, parsed.month)
    return abs(parsed.day - third_friday) <= tolerance_days


def select_expiries(
    symbol: str,
    *,
    catalyst_index: int = 0,
    min_short_days: int = 21,
    monthly_only: bool = True,
) -> dict:
    """Pick the short (pre-catalyst) and long (post-catalyst) expiries.

    ``catalyst_index`` chooses which upcoming earnings the thesis needs: 0 is the
    next report, 1 the one after. Returns ``{"short", "long", "catalyst",
    "rationale"}`` or raises ``ValueError`` when the chain cannot support it.
    """
    expiries = yahoo.expiries(symbol)
    if not expiries:
        raise ValueError(f"no listed options for {symbol}")

    if monthly_only:
        monthlies = [e for e in expiries if is_monthly_expiry(e)]
        if monthlies:
            expiries = monthlies

    earnings = upcoming_earnings(symbol)
    if not earnings:
        raise ValueError(f"no upcoming earnings date for {symbol}")

    catalyst = earnings[min(catalyst_index, len(earnings) - 1)]

    # Short leg: the *nearest* usable expiry before the catalyst. Nearest, not
    # furthest, because a shorter-dated short decays faster, and the references
    # take roughly one month of premium.
    floor_date = date.today() + timedelta(days=min_short_days)
    pre = [
        e
        for e in expiries
        if (_as_date(e) or date.min) < catalyst and (_as_date(e) or date.min) >= floor_date
    ]
    if not pre:
        # Fall back to any expiry before the catalyst, then to the nearest one.
        pre = [e for e in expiries if (_as_date(e) or date.min) < catalyst]
    short = pre[0] if pre else None
    if short is None:
        raise ValueError(f"no expiry before catalyst {catalyst} for {symbol}")

    # Long leg: the first expiry after the catalyst.
    post = [e for e in expiries if (_as_date(e) or date.min) > catalyst]
    if not post:
        raise ValueError(f"no expiry after catalyst {catalyst} for {symbol}")
    long_expiry = post[0]

    return {
        "short": short,
        "long": long_expiry,
        "catalyst": catalyst,
        "earnings": earnings,
        "monthly_only": monthly_only,
        "rationale": (
            f"short expires {_fmt_expiry(short)}, before the {catalyst} catalyst; "
            f"long expires {_fmt_expiry(long_expiry)}, after it"
        ),
    }


# --------------------------------------------------------------------------
# leg selection
# --------------------------------------------------------------------------


@dataclass
class Structure:
    """A candidate spread plus everything needed to judge and render it."""

    symbol: str
    direction: str  # "long" | "short"
    option_type: str  # "CALL" | "PUT"
    price: float
    long_leg: dict
    short_leg: dict
    # Defaulted so a Structure can be constructed directly (tests, replay from a
    # saved packet) without having to invent a catalyst date.
    catalyst: date | None = None
    notes: list[str] = field(default_factory=list)

    # --- derived -----------------------------------------------------------
    @property
    def long_total(self) -> float:
        return self.long_leg["premium"] * self.long_leg["qty"] * CONTRACT

    @property
    def short_total(self) -> float:
        return self.short_leg["premium"] * self.short_leg["qty"] * CONTRACT

    @property
    def net_debit(self) -> float:
        return self.long_total - self.short_total

    @property
    def credit_ratio_mid(self) -> float | None:
        """short premium / long premium, at mid prices -- the writeup figure."""
        if not self.long_total:
            return None
        return self.short_total / self.long_total

    @property
    def credit_ratio_conservative(self) -> float | None:
        """Same ratio priced against you: long at ask, short at bid."""
        long_px = self.long_leg.get("ask") or self.long_leg["premium"]
        short_px = self.short_leg.get("bid")
        if short_px is None:
            short_px = self.short_leg["premium"]
        long_total = long_px * self.long_leg["qty"] * CONTRACT
        if not long_total:
            return None
        return (short_px * self.short_leg["qty"] * CONTRACT) / long_total

    def passes_floor(self, floor: float = CREDIT_FLOOR) -> bool:
        ratio = self.credit_ratio_conservative
        return ratio is not None and ratio >= floor

    def rows(self) -> list[dict]:
        """The Structuring table, in reference column order."""
        out = []
        for side, leg in (("Long", self.long_leg), ("Short", self.short_leg)):
            total = leg["premium"] * leg["qty"] * CONTRACT
            out.append(
                {
                    "side": side,
                    "type": self.option_type,
                    "expiry": _fmt_expiry(leg["expiry"]),
                    "strike": leg["strike"],
                    "qty": leg["qty"],
                    "underlying": self.price,
                    "multiplier": CONTRACT,
                    "price": leg["premium"],
                    # Sign convention copied from the references: the premium
                    # paid shows positive, the credit received shows negative.
                    #   Long  ...  $ 15.55  ...  $ 4,665.00
                    #   Short ...  $  6.44  ...  $ (1,288.00)
                    "total": total if side == "Long" else -total,
                    "open_interest": leg.get("open_interest"),
                }
            )
        return out

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "option_type": self.option_type,
            "price": self.price,
            "catalyst": self.catalyst.isoformat() if self.catalyst else None,
            "long_leg": self.long_leg,
            "short_leg": self.short_leg,
            "long_total": round(self.long_total, 2),
            "short_total": round(self.short_total, 2),
            "net_debit": round(self.net_debit, 2),
            "credit_ratio_mid": round(self.credit_ratio_mid, 4) if self.credit_ratio_mid else None,
            "credit_ratio_conservative": (
                round(self.credit_ratio_conservative, 4) if self.credit_ratio_conservative else None
            ),
            "passes_floor": self.passes_floor(),
            "rows": self.rows(),
            "notes": self.notes,
        }


def _common_strikes(symbol: str, far_expiry: str, near_expiry: str, side: str) -> list[float]:
    """Strikes listed in both expiries, restricted to OTM ones for ``side``."""
    far = yahoo.chain(symbol, far_expiry)[side]
    near = yahoo.chain(symbol, near_expiry)[side]
    far_strikes = {r["strike"] for r in far if r.get("strike")}
    near_strikes = {r["strike"] for r in near if r.get("strike")}
    return sorted(far_strikes & near_strikes)


def _quote_for(symbol: str, expiry: str, side: str, strike: float, price_mode: str = "mid") -> dict | None:
    """Find the contract row for ``strike`` in one chain."""
    rows = yahoo.chain(symbol, expiry)[side]
    match = next((r for r in rows if r.get("strike") == strike), None)
    if not match:
        return None

    if price_mode == "last" and match.get("last"):
        premium = match["last"]
    elif price_mode == "conservative":
        # Pay the ask on a buy; this is the worst-case entry.
        premium = match.get("ask") or match.get("mid") or match.get("last")
    else:
        premium = match.get("mid") or match.get("last") or match.get("bid")
    if not premium:
        return None

    return {
        "expiry": expiry,
        "strike": strike,
        "premium": round(float(premium), 2),
        "bid": match.get("bid"),
        "ask": match.get("ask"),
        "mid": match.get("mid"),
        "last": match.get("last"),
        "open_interest": match.get("open_interest"),
        "volume": match.get("volume"),
        "implied_vol": match.get("implied_vol"),
    }


def select_expiries_auto(
    symbol: str, *, start_index: int = 0, max_catalyst_index: int = 2, **kwargs
) -> dict:
    """Pick expiries, walking forward through upcoming catalysts until one fits.

    A name reporting in a few days cannot be structured at all by rule 2/3: there
    is no monthly expiry left *before* the event to sell. That is a real
    constraint, not an error -- COST reporting 2026-09-24 from a 2026-09-19 start
    has no pre-earnings monthly, but its December report works fine.

    So try the next report instead of giving up. The returned dict carries
    ``catalyst_index`` so the caller can report *which* report the trade targets.

    ``start_index`` is honoured rather than always starting at 0, because an
    explicitly requested catalyst must not be silently replaced by an earlier
    one. OMF's reference trade deliberately targets the *second* report, which is
    why ``fig demo`` passes ``catalyst_index=1``.
    """
    last_error: Exception | None = None
    for index in range(start_index, max_catalyst_index + 1):
        try:
            pick = select_expiries(symbol, catalyst_index=index, **kwargs)
            pick["catalyst_index"] = index
            return pick
        except ValueError as exc:
            last_error = exc
    raise ValueError(str(last_error) if last_error else f"no usable catalyst for {symbol}")


def select_strike(
    symbol: str,
    far_expiry: str,
    near_expiry: str,
    *,
    direction: str,
    price: float,
    otm_target: float = DEFAULT_OTM,
) -> tuple[float, list[float]]:
    """Nearest common OTM strike to ``otm_target`` out of the money.

    Returns ``(strike, alternatives)``.
    """
    side = "calls" if direction == "long" else "puts"
    common = _common_strikes(symbol, far_expiry, near_expiry, side)
    if not common:
        raise ValueError(f"no common strikes between {near_expiry} and {far_expiry} for {symbol}")

    if direction == "long":
        otm = [s for s in common if s >= price]
    else:
        otm = [s for s in common if s <= price]
    if not otm:
        otm = common  # no OTM strike listed; fall back to whatever is shared

    def distance(strike: float) -> float:
        return abs(abs(strike - price) / price - otm_target)

    ranked = sorted(otm, key=distance)
    return ranked[0], ranked


def solve_short_qty(
    long_premium: float,
    short_premium: float,
    long_qty: int,
    *,
    target_ratio: float,
    max_ratio_to_long: float = 1.0,
) -> int:
    """Contracts to sell so that short/long premium lands near ``target_ratio``.

    Capped at ``long_qty`` by default: both references short *fewer* contracts
    than they are long, which keeps the structure net long the thesis rather
    than turning it into a credit spread.
    """
    if not short_premium or not long_premium:
        return 0
    ideal = long_qty * target_ratio * long_premium / short_premium
    qty = int(round(ideal))
    qty = max(0, min(qty, int(long_qty * max_ratio_to_long)))
    return qty


def build_structure(
    symbol: str,
    direction: str,
    *,
    capital: float = DEFAULT_CAPITAL,
    otm_target: float = DEFAULT_OTM,
    credit_target: float = DEFAULT_CREDIT_TARGET,
    catalyst_index: int = 0,
    strike: float | None = None,
    price_mode: str = "mid",
    min_open_interest: int = 10,
) -> Structure:
    """Assemble the spread for one idea.

    ``direction`` is the *thesis* direction: ``"long"`` buys calls, ``"short"``
    buys puts. The short leg is always a sale of the same strike at a nearer
    expiry.
    """
    direction = direction.lower()
    if direction not in {"long", "short"}:
        raise ValueError("direction must be 'long' or 'short'")

    symbol = symbol.upper()
    valuation = yahoo.valuation(symbol)
    price = valuation.get("price")
    if not price:
        raise ValueError(f"no price for {symbol}")

    pick = select_expiries_auto(symbol, start_index=catalyst_index)
    far, near = pick["long"], pick["short"]
    side = "calls" if direction == "long" else "puts"

    if strike is None:
        strike, alternatives = select_strike(
            symbol, far, near, direction=direction, price=price, otm_target=otm_target
        )
    else:
        alternatives = []

    long_leg = _quote_for(symbol, far, side, strike, price_mode)
    short_leg = _quote_for(symbol, near, side, strike, price_mode)
    if not long_leg or not short_leg:
        raise ValueError(f"missing quotes for {symbol} {strike} in {near}/{far}")

    notes: list[str] = []
    if long_leg.get("open_interest") is not None and long_leg["open_interest"] < min_open_interest:
        notes.append(f"thin long leg: {long_leg['open_interest']} open interest")
    if short_leg.get("open_interest") is not None and short_leg["open_interest"] < min_open_interest:
        notes.append(f"thin short leg: {short_leg['open_interest']} open interest")
    notes.append(pick["rationale"])
    if pick.get("catalyst_index"):
        notes.append(
            f"targets report #{pick['catalyst_index'] + 1} "
            f"({pick['catalyst']}); earlier reports fall before the next monthly expiry"
        )

    # Long size from the capital budget.
    per_contract = long_leg["premium"] * CONTRACT
    long_qty = max(1, int(capital // per_contract)) if per_contract else 1

    short_qty = solve_short_qty(
        long_leg["premium"], short_leg["premium"], long_qty, target_ratio=credit_target
    )

    structure = Structure(
        symbol=symbol,
        direction=direction,
        option_type="CALL" if direction == "long" else "PUT",
        price=price,
        long_leg={**long_leg, "qty": long_qty},
        short_leg={**short_leg, "qty": short_qty},
        catalyst=pick["catalyst"],
        notes=notes,
    )
    if alternatives:
        structure.notes.append(
            "alternative strikes: " + ", ".join(f"{s:g}" for s in alternatives[:4])
        )
    return structure


def suggest_short_adjustment(structure: Structure, floor: float = CREDIT_FLOOR) -> str:
    """Advice when the conservative credit ratio misses the floor.

    Mirrors the hand-written note in the OMF reference ("I could sell 1 or 2
    more to increase that").
    """
    ratio = structure.credit_ratio_conservative
    if ratio is None:
        return "no short leg; nothing to adjust"
    if ratio >= floor:
        margin = ratio - floor
        extra = _extra_shorts_for(structure, floor)
        base = f"Credit ratio {ratio*100:.1f}% clears the {floor*100:.0f}% floor."
        return base + (f" Room for ~{extra} more short(s)." if extra > 0 else "")

    needed = _extra_shorts_for(structure, floor)
    return (
        f"Credit ratio {ratio*100:.1f}% is below the {floor*100:.0f}% floor; "
        f"sell ~{needed} more short contract(s) to clear it."
    )


def _extra_shorts_for(structure: Structure, floor: float) -> int:
    """Additional short contracts needed to reach ``floor``, or 0 if already there.

    Must use the *same* pricing basis as :meth:`Structure.credit_ratio_conservative`
    (long at ask, short at bid), otherwise the shortfall it computes disagrees
    with the ratio it is trying to fix.
    """
    long_px = structure.long_leg.get("ask") or structure.long_leg["premium"]
    long_qty = structure.long_leg["qty"]
    short_px = structure.short_leg.get("bid") or structure.short_leg["premium"]
    if not short_px or not long_px:
        return 0

    needed_total = floor * long_px * long_qty * CONTRACT
    current = structure.short_leg["qty"] * short_px * CONTRACT
    shortfall = needed_total - current
    if shortfall <= 0:
        return 0
    return int(-(-shortfall // (short_px * CONTRACT)))  # ceil division


def credit_ladder(structure: Structure, max_extra: int | None = None) -> list[dict]:
    """Credit ratio at each possible short quantity.

    The references reason about this explicitly -- "I could sell 1 or 2 more to
    increase that", "even if I halved it, it would be 13%" -- so expose the whole
    ladder rather than a single solved quantity. Reports the conservative ratio
    (the one that matters) alongside the mid ratio (the one quoted in writeups).
    """
    long_qty = structure.long_leg["qty"]
    long_px = structure.long_leg["premium"]
    long_ask = structure.long_leg.get("ask") or long_px
    short_px = structure.short_leg["premium"]
    short_bid = structure.short_leg.get("bid") or short_px

    upper = long_qty if max_extra is None else min(long_qty, structure.short_leg["qty"] + max_extra)
    rows = []
    for qty in range(0, upper + 1):
        mid = (short_px * qty * CONTRACT) / (long_px * long_qty * CONTRACT) if long_px else 0
        conservative = (short_bid * qty * CONTRACT) / (long_ask * long_qty * CONTRACT) if long_ask else 0
        rows.append(
            {
                "short_qty": qty,
                "credit_ratio_mid": round(mid, 4),
                "credit_ratio_conservative": round(conservative, 4),
                "passes_floor": conservative >= CREDIT_FLOOR,
                "cash_collected": round(short_px * qty * CONTRACT, 2),
            }
        )
    return rows
