"""Rank a batch of ideas on stated, inspectable components.

Deliberately NOT a prediction and not a "best stock" score. It orders the notes in
a folder so a reader knows where to start, and every component is a fact about the
note rather than an opinion about the company:

======================  ======  ==================================================
component               weight  what it measures
======================  ======  ==================================================
evidence                 0.40  share of sampled runs whose end-market verdict
                               confirmed the idea (see research.evidence_verdict)
catalyst_proximity       0.20  how soon the dated catalyst arrives
revision_agreement       0.20  do the 7-day and 30-day estimate revisions point
                               the same way, or is the trend rolling over
note_quality             0.10  current lint score -- form, so weighted low
grounding                0.10  every figure in the prose traced to the evidence
======================  ======  ==================================================

Two cautions that matter more than the weights:

1. **A high lint score is not evidence of a good thesis.** The two highest-scoring
   notes in this repo's own history (COST, PAYX) were the two the owner judged
   weakest on reasoning. Lint measures form -- brevity, grounded numbers, no
   valuation-only filler -- and form is cheap to satisfy.
2. **`evidence` is the only component that reflects a view on the company**, and it
   reflects the *sampled* end-market research, which varies between runs by design.
   A note confirmed in 1 of 3 samples is genuinely less settled than one confirmed
   in 3 of 3, and the component says so instead of hiding it.
"""

from __future__ import annotations

import re

WEIGHTS = {
    # Evidence carries the most weight because it is the only component that
    # reflects a view on the company rather than on the write-up.
    "evidence": 0.40,
    "catalyst_proximity": 0.20,
    "revision_agreement": 0.20,
    # note_quality is deliberately low. Lint measures FORM, and this repo's own
    # history is the evidence: the two highest-scoring notes it produced were the
    # two the owner judged weakest on reasoning. Weighting form highly would put
    # a well-written note with contradicted evidence above a plainer one whose
    # evidence holds up, which is exactly the error this module must not make.
    "note_quality": 0.10,
    "grounding": 0.10,
}

# A catalyst inside this window scores full marks for proximity; the score then
# decays to zero at HORIZON_DAYS. An idea whose catalyst is a year out is not
# actionable yet, however good it is.
FULL_MARKS_DAYS = 60
HORIZON_DAYS = 240


def _catalyst_proximity(days_out: int | None) -> float:
    if days_out is None:
        return 0.0
    if days_out < 0:
        return 0.0
    if days_out <= FULL_MARKS_DAYS:
        return 1.0
    if days_out >= HORIZON_DAYS:
        return 0.0
    span = HORIZON_DAYS - FULL_MARKS_DAYS
    return round(1.0 - (days_out - FULL_MARKS_DAYS) / span, 3)


def _revision_agreement(quants: dict) -> float:
    """1.0 when the 7-day and 30-day revision windows point the same way.

    Disagreement is not automatically bad -- a 30-day downtrend that has turned up
    over the last week can be the inflection an idea is built on -- but it does mean
    the revision trend is not yet confirmed, so the note starts lower down the list.

    The quants block stores these as PROSE, not numbers: "all down, with 0 up and 3
    down over last 30 days" and "slightly down over the last 7 days". Reading integer
    keys that do not exist silently returned 0.5 for every note, which made a fifth
    of the conviction weight do nothing at all.
    """
    long_text = str(quants.get("eps_revisions") or "")
    short_text = str(quants.get("eps_trend") or "")

    up_match = re.search(r"(\d+)\s+up", long_text)
    down_match = re.search(r"(\d+)\s+down", long_text)
    if not (up_match or down_match):
        return 0.5
    net_long = int(up_match.group(1) if up_match else 0) - int(
        down_match.group(1) if down_match else 0
    )

    lower = short_text.lower()
    has_down, has_up = "down" in lower, "up" in lower
    if has_down == has_up:  # neither, or contradictory prose
        return 0.5
    net_short = -1 if has_down else 1

    if net_long == 0 or net_short == 0:
        return 0.5
    return 1.0 if (net_long > 0) == (net_short > 0) else 0.4


def _evidence(verdict: dict | None) -> tuple[float, str]:
    """Sampled end-market verdict, as a fraction of runs that confirmed."""
    if not verdict:
        return 0.5, "1 sample"
    total = verdict.get("samples") or 1
    confirmed = verdict.get("confirmed") or 0
    contradicted = verdict.get("contradicted") or 0
    # Confirmed runs count fully, contradicted runs count zero, mixed count half.
    score = (confirmed + 0.5 * (total - confirmed - contradicted)) / total
    label = f"{confirmed}/{total} confirm"
    if contradicted:
        label += f", {contradicted} contradict"
    return round(score, 3), label


def rank_ideas(results: list[dict]) -> list[dict]:
    """Score and order notes. ``results`` are ``generate``-style ``{writeup, lint}``."""
    entries: list[dict] = []
    for result in results:
        writeup = result.get("writeup") or {}
        lint_result = result.get("lint") or {}
        quants = writeup.get("quants") or {}
        catalyst = writeup.get("catalyst") or {}
        generation = writeup.get("generation") or result.get("generation") or {}

        evidence_score, evidence_label = _evidence(generation.get("verdict"))
        tally = generation.get("verdict") or {}
        grounding = generation.get("grounding") or {}
        components = {
            "evidence": evidence_score,
            "catalyst_proximity": _catalyst_proximity(catalyst.get("days_out")),
            "revision_agreement": _revision_agreement(quants),
            "note_quality": round((lint_result.get("score") or 0) / 100, 3),
            "grounding": 1.0 if grounding.get("grounded", True) else 0.0,
        }
        conviction = round(
            sum(components[name] * weight for name, weight in WEIGHTS.items()) * 100, 1
        )
        entries.append(
            {
                "ticker": writeup.get("ticker"),
                "direction": (writeup.get("direction") or "").lower(),
                "conviction": conviction,
                "components": components,
                "evidence_label": evidence_label,
                "confirmed": tally.get("confirmed") or 0,
                "contradicted": tally.get("contradicted") or 0,
                "samples": tally.get("samples") or 1,
                "catalyst_date": catalyst.get("date"),
                "catalyst_days": catalyst.get("days_out"),
                "fwd_pe": quants.get("fwd_pe"),
                "score": lint_result.get("score"),
                "description": writeup.get("description"),
            }
        )

    entries.sort(key=lambda entry: (-entry["conviction"], entry["ticker"] or ""))
    for position, entry in enumerate(entries, start=1):
        entry["rank"] = position
    return entries


def summarise(entries: list[dict]) -> dict:
    """Counts for a batch: how many ideas, which way, and how well evidenced."""
    longs = [e for e in entries if e["direction"] == "long"]
    shorts = [e for e in entries if e["direction"] == "short"]

    # Counted by majority verdict across samples, not by an arbitrary score
    # threshold: "contradicted in 2 of 3 runs" must show up as evidence against,
    # which a >= 0.75 cut silently dropped.
    confirmed = [e for e in entries if e["confirmed"] > e["contradicted"]]
    contradicted = [e for e in entries if e["contradicted"] > e["confirmed"]]
    sampled = max((e["samples"] for e in entries), default=1)
    return {
        "ideas": len(entries),
        "longs": len(longs),
        "shorts": len(shorts),
        "other": len(entries) - len(longs) - len(shorts),
        "mean_conviction": round(
            sum(e["conviction"] for e in entries) / len(entries), 1
        )
        if entries
        else 0.0,
        "samples": sampled,
        "well_evidenced": len(confirmed),
        "evidence_against": len(contradicted),
    }
