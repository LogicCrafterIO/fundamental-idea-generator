"""Lint a writeup against the house style.

The prompts in :mod:`fig.prompts` *ask* for brevity and plain language. This
module *checks* it. That distinction matters: a model asked to "be concise" will
produce something plausible and twice too long, and no amount of re-prompting
fixes that reliably. Failing a measurable check does.

Checks fall into four groups:

**Budget** -- word counts against :data:`fig.prompts.WORD_BUDGET`, and reason count.
**Substance** -- every reason must contain a number, a named company comparison,
or a causal connector. This is the check that catches filler.
**Language** -- hedging phrases, empty intensifiers, and unglossed acronyms.
**Tone** -- vague openers and definitional padding in the Description.

Levels: ``error`` fails the note, ``warn`` is a nudge. ``score`` is 0-100 with
errors weighted heavily, so a note can be ranked without being rejected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .prompts import GLOSS_REQUIRED, WORD_BUDGET

# --------------------------------------------------------------------------
# word lists
# --------------------------------------------------------------------------

HEDGES = [
    "could potentially", "might potentially", "may potentially",
    "it seems", "it appears", "arguably", "to some extent", "more or less",
    "somewhat", "fairly likely", "possibly", "perhaps", "we believe",
    "in our view", "it could be argued", "tends to suggest", "to be fair",
]

# NOTE: these are words, not prefixes, and must be matched on word boundaries.
# Plain `phrase in text` matching reported "very" inside "recovery the" -- the
# same class of substring bug that made the theme tagger call "Income" a charge
# off. See :func:`_phrase_re`.
FILLER = [
    "very", "really", "quite", "basically", "actually", "literally",
    "clearly", "obviously", "simply", "extremely", "highly",
]


def _phrase_re(phrase: str) -> re.Pattern[str]:
    """Word-boundary regex for a word or multi-word phrase."""
    escaped = re.escape(phrase.strip()).replace(r"\ ", r"\s+")
    return re.compile(r"\b" + escaped + r"\b", re.IGNORECASE)

VAGUE_OPENERS = [
    "the company is a", "this company is", "this is a company that",
    "the company operates", "xyz is a leading", "is a leading provider",
    "is a global leader", "is one of the world's",
]

# Words that look like tickers but are not.
NOT_TICKERS = {
    "AI", "US", "USA", "UK", "EU", "CEO", "CFO", "COO", "IPO", "ETF", "GDP",
    "PE", "PS", "PB", "EV", "FCF", "EPS", "YOY", "QOQ", "NCO", "RPO", "ARR",
    "TAM", "NRR", "SBC", "ROIC", "EBITDA", "GPU", "CPU", "API", "SaaS", "IT",
    "AND", "THE", "BUT", "FOR", "NOT", "YOU", "ALL", "CAN", "NOW", "ONE",
    "TWO", "NEW", "OLD", "BIG", "LOW", "HIGH", "IF", "OR", "SO", "AS", "AT",
    "BY", "IN", "ON", "OF", "TO", "IS", "IT", "BE", "DO", "WE", "MY", "NO",
    "DTE", "OI", "IV", "Q1", "Q2", "Q3", "Q4", "H1", "H2", "TTM", "NTM",
}

CAUSAL_MARKERS = [
    # Strong, explicit causation only. Weak conjunctions ("so", "will", "would",
    # "when", "makes") used to live here, which let "next-FY PE is 39.51, so the
    # market is paying less for next year's earnings" count as having a mechanism
    # and escape the valuation check entirely.
    "because", "since", "leads to", "lead to", "drives", "results in", "causes",
    "as a result", "which means", "therefore", "forces", "given that", "due to",
    "if ", "then ", "force", "forcing", "enough to", "push", "compress", "erode",
]

NUMBER_RE = re.compile(r"\d")
TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9''\-\.%$]*")
URL_RE = re.compile(r"https?://\S+|www\.[^\s)]+", re.IGNORECASE)


@dataclass
class Issue:
    level: str  # "error" | "warn"
    code: str
    where: str
    message: str

    def __str__(self) -> str:
        # The code is included so callers (and tests) can match on it rather than
        # on prose, and so a CLI reader can look it up.
        marker = "ERROR" if self.level == "error" else "warn "
        return f"[{marker}] {self.where}: {self.message} ({self.code})"

    def as_dict(self) -> dict:
        return {"level": self.level, "code": self.code, "where": self.where, "message": self.message}


# The Watch block is required only when a dated print is close: that is the moment a
# reader can act on "what would prove this wrong", and a note with no near catalyst
# has no such test to state.
WATCH_REQUIRED_WITHIN_DAYS = 21
WATCH_MAX_LINES = 4
WATCH_WORD_BUDGET = 25


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def _has_number(text: str) -> bool:
    return bool(NUMBER_RE.search(text or ""))


def _has_named_comparison(text: str) -> bool:
    """A ticker-looking token, or an explicit peer phrase."""
    for match in TICKER_RE.findall(text or ""):
        if match not in NOT_TICKERS:
            return True
    lowered = (text or "").lower()
    return any(
        phrase in lowered
        for phrase in ("compared to", "versus", "vs ", "peer", "competitor", "rival")
    )


def _has_mechanism(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in CAUSAL_MARKERS)


# A multiple, a discount, or a cheapness word -- the vocabulary of a valuation-only
# argument.
VALUATION_MARKERS = (
    "forward pe", "fwd pe", "fwdpe", "p/e", " pe ", "multiple", "trades at",
    "trading at", "priced at", "prices in", "pricing in", "valuation",
    " x forward", "x earnings", "x next-year", "p/s", "ps ratio", "cheap",
    "expensive", "discount", "premium to", "below peers", "below its peers",
    "underpriced", "overpriced",
    # price-level discounts: the same fallacy with no multiple in it, e.g.
    # "shares sit 18% below May peak -- growth has not slowed"
    "% below", "below its peak", "below the peak", "off its high", "off the high",
    "off its peak", "pullback", "pull back", "sell-off", "selloff", "sold off",
    "below its high", "below the high",
)

# What turns a valuation observation into a thesis: a statement that the market
# is wrong about something specific, or that something will change.
MISPRICING_MARKERS = (
    "market is missing", "market misses", "market has not", "market hasn't",
    "not priced", "isn't priced", "is not priced", "mispric", "ignores",
    "overpaying", "underappreciating", "underappreciated", "misread",
    "will change", "would change", "must change", "changes when", "until",
    "once ", "if ", "because", "leads to", "drives", "forces", "as a result",
    "catalyst", "reflect", "catch up", "narrow", "close the gap",
    "not sustainable", "cannot last", "can't last", "unsustainable",
)


# A forward-PE roll-forward ("next-FY 39.5 is below this year's 43.5") is
# informationally empty: every company with any earnings growth has a lower
# next-year multiple than current-year. It reads like a finding and distinguishes
# nothing, so it is checked separately from the general rule above.
_ROLLFORWARD_RE = re.compile(
    r"(next[- ]?(fy|fiscal year|year)|forward).{0,60}?(below|lower than|under|cheaper than)"
    r".{0,40}?(current|this year|current[- ]year)",
    re.IGNORECASE | re.DOTALL,
)


def is_pe_rollforward(text: str) -> bool:
    """True for a next-FY vs current-FY PE comparison presented as evidence."""
    lowered = (text or "").lower()
    if not any(token in lowered for token in ("pe", "p/e", "multiple", "x ")):
        return False
    if not _ROLLFORWARD_RE.search(text or ""):
        return False
    # If the reason also says what the market is missing, the comparison is
    # supporting detail rather than the whole argument.
    return not any(marker in lowered for marker in MISPRICING_MARKERS)


def is_valuation_only(text: str, direction: str | None = None) -> bool:
    """True when a reason rests on a multiple with no mechanism behind it.

    This encodes the most expensive reasoning error in this format: "it trades at
    12x while peers are at 20x". A discount is an observation, not a thesis --
    premium multiples usually exist for a good reason, so cheapness is not by
    itself a case for an upward rerating. Cheap things are frequently cheap
    because something is wrong.

    The juxtaposition form counts as the error, which is a deliberate call: a
    reason saying "net income rose 32% yet it trades at 16.9x" has *not* explained
    why the market pays only 16.9x -- it has restated the screen signal as if it
    were a conclusion. It passes only by adding what the market is missing or what
    will change. That is exactly the distinction the owner asked for, and an
    earlier version of this check that exempted any reason containing "yet" or
    "rose" was too loose to catch anything.

    Two deliberate limits:

    * **Short theses are exempt.** A high multiple on a business whose numbers are
      deteriorating is a standard short argument, not this fallacy.
    * **A mechanism or a mispricing claim clears it.** So ORCL's own reference
      reason 1 -- "it's not priced like Google, which is trading at a Forward PE
      of 25 while Oracle is at a Forward PE of 17" -- passes on its "because". The
      linter flags the bare form rather than rejecting the owner's own spec.
    """
    lowered = f" {(text or '').lower()} "
    if not any(marker in lowered for marker in VALUATION_MARKERS):
        return False
    if _has_mechanism(text):
        return False
    if any(marker in lowered for marker in MISPRICING_MARKERS):
        return False
    if (direction or "").lower() == "short":
        return False
    return True


def unglossed_acronyms(text: str) -> list[str]:
    """Acronyms used without a following ``[plain words]`` gloss."""
    missing = []
    for acronym in GLOSS_REQUIRED:
        # Match the acronym not immediately followed by a bracket gloss.
        pattern = rf"\b{re.escape(acronym)}\b(?!\s*\[)"
        if re.search(pattern, text or ""):
            # A gloss anywhere earlier in the note counts.
            if not re.search(rf"\b{re.escape(acronym)}\b\s*\[", text or ""):
                missing.append(acronym)
    return missing


# --------------------------------------------------------------------------
# the counts-versus-level fallacy
# --------------------------------------------------------------------------

# Ways of saying the consensus number is wrong in time rather than in value.
_STALE_WORDS = (
    "stale", "out of date", "outdated", "out-of-date", "too low", "understated",
    "has not caught up", "hasn't caught up", "not caught up", "lags the",
    "behind the curve", "not yet reflected", "not reflected in the consensus",
    "is out of step",
)

# Evidence that is a COUNT of analysts moving rather than a move in the level.
_COUNT_EVIDENCE_RE = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"(?:of\s+\d+\s+)?(?:analysts?|brokers?|estimates?)\b"
    r"|\b\d+\s+up\b|\bnone\s+(?:cutting|cut|lowering)\b|\bno\s+cuts?\b",
    re.IGNORECASE,
)

# The level moved DOWN, which is the one case where "stale" is not contradicted.
_LEVEL_FELL_RE = re.compile(r"\b(down|lower|cut|cutting|declin\w*|fell|falling|reduced)\b", re.I)


def is_stale_consensus_on_counts(reason: str, quants: dict | None) -> bool:
    """True when a reason calls the consensus stale on revision-count evidence.

    The observed error, from the BB note: *"five analysts raised estimates in 30
    days with none cutting, the 0.19 FY number is stale"*. The premise and the
    conclusion are the same fact read twice -- if five analysts raised, then 0.19
    is the number they raised *to*, which makes it the freshest number available
    rather than a stale one. The packet's own trend line agreed: the FY level was
    0.18857 thirty days earlier and 0.18857 on the day, so the raises were smaller
    than the rounding of the level and nothing had moved at all.

    It fires only on the conjunction -- a staleness claim AND count evidence AND a
    level that did not fall -- because each half alone is legitimate: "the
    consensus is too low" is an ordinary long argument, and "5 up and 0 down" is
    an ordinary fact.
    """
    text = reason or ""
    lowered = text.lower()
    if not any(word in lowered for word in _STALE_WORDS):
        return False
    if not _COUNT_EVIDENCE_RE.search(text):
        return False

    trend_text = str((quants or {}).get("eps_trend") or "")
    if _LEVEL_FELL_RE.search(trend_text):
        # Estimates were actually cut, so the level did move away from the number
        # on the page and calling it stale is at least arguable.
        return False
    return True


def lint_writeup(writeup: dict) -> dict:
    """Check one writeup dict. Returns ``{issues, errors, warnings, score, ok}``."""
    issues: list[Issue] = []

    description = (writeup.get("description") or "").strip()
    reasons = [r for r in (writeup.get("reasons") or []) if str(r).strip()]
    notes = (writeup.get("structuring") or {}).get("reflection") or writeup.get("notes") or ""

    # ---- sources ---------------------------------------------------------
    # A note is only as believable as its citations, so a reason that names no
    # source is an ERROR whenever the packet registered any -- which it always
    # does in a real run. The `sources_catalogue` presence test is what keeps this
    # honest: if the tool supplied no sources, it has no standing to demand them,
    # which is why the offline fixtures and the reference notes are unaffected.
    catalogue = writeup.get("sources_catalogue") or []
    reason_sources = writeup.get("reason_sources") or []
    if catalogue:
        for index in range(len(reasons)):
            cited = reason_sources[index] if index < len(reason_sources) else None
            if not cited:
                issues.append(
                    Issue(
                        "error",
                        "reason_no_source",
                        f"Reason {index + 1}",
                        "cites no source; add the evidence ids this reason rests on "
                        "(reason_sources), or drop the reason",
                    )
                )
        for index, reason in enumerate(reasons, start=1):
            if URL_RE.search(str(reason)):
                issues.append(
                    Issue(
                        "error",
                        "reason_contains_url",
                        f"Reason {index}",
                        "has a URL in the prose; name the source by its id in "
                        "reason_sources instead of spending words on the link",
                    )
                )
    if writeup.get("sources_unverified"):
        issues.append(
            Issue(
                "error",
                "reason_source_unknown",
                "Reasons",
                f"cited source(s) {', '.join(str(s) for s in writeup['sources_unverified'])} "
                f"are not in the evidence ({len(catalogue)} sources supplied); cite only "
                f"ids from the SOURCES list",
            )
        )
    if writeup.get("urls_redacted"):
        issues.append(
            Issue(
                "error",
                "reason_url_redacted",
                "Reasons",
                f"{len(writeup['urls_redacted'])} URL(s) written into a reason were removed "
                f"because the evidence does not contain them; use reason_sources",
            )
        )

    # ---- budget ----------------------------------------------------------
    if not description:
        issues.append(Issue("error", "missing_description", "Description", "is empty"))
    else:
        count = word_count(description)
        if count > WORD_BUDGET["description"]:
            issues.append(
                Issue(
                    "error",
                    "description_too_long",
                    "Description",
                    f"{count} words (budget {WORD_BUDGET['description']}). Cut to the business, "
                    f"not the story.",
                )
            )

    if len(reasons) < WORD_BUDGET["reasons_min"]:
        issues.append(
            Issue("error", "too_few_reasons", "Reasons", f"{len(reasons)} given, need at least {WORD_BUDGET['reasons_min']}")
        )
    if len(reasons) > WORD_BUDGET["reasons_max"]:
        issues.append(
            Issue(
                "warn",
                "too_many_reasons",
                "Reasons",
                f"{len(reasons)} given (max {WORD_BUDGET['reasons_max']}). Drop the weakest.",
            )
        )

    # ---- catalyst --------------------------------------------------------
    # The catalyst is the point of the note, so it is required, and its date must
    # match the measured one exactly -- a restated or rounded earnings date is the
    # most damaging error a note can carry.
    catalyst = writeup.get("catalyst") or {}
    why = (catalyst.get("why") or "").strip()
    if not catalyst.get("date"):
        issues.append(Issue("warn", "catalyst_missing", "Catalyst", "has no dated earnings catalyst"))
    else:
        if not why:
            issues.append(
                Issue("error", "catalyst_no_justification", "Catalyst",
                      "states the date but not why it matters")
            )
        else:
            count = word_count(why)
            if count > WORD_BUDGET["catalyst_why"]:
                issues.append(
                    Issue(
                        "error",
                        "catalyst_why_too_long",
                        "Catalyst",
                        f"{count} words (budget {WORD_BUDGET['catalyst_why']}). "
                        f"Say what the report must prove, not what the date is.",
                    )
                )
        facts = str(catalyst.get("facts_line") or "")
        if facts and str(catalyst["date"]) not in facts:
            issues.append(
                Issue("error", "catalyst_date_mismatch", "Catalyst",
                      f"date {catalyst['date']} does not appear in the stated facts")
            )
        # The justification should say what the report must prove, not repeat the
        # measured line. Referencing the date ("the 2026-09-23 report must show...")
        # is fine; reproducing its detail is not. So this fires on the *measured
        # particulars* -- the weekday, the session, or the days-remaining count --
        # rather than on the date itself, which would punish good phrasing.
        if why and catalyst.get("date"):
            measured_detail = [
                str(catalyst.get("weekday") or ""),
                str(catalyst.get("session") or ""),
                "days out" if catalyst.get("days_out") is not None else "",
            ]
            echoed = [d for d in measured_detail if d and d.lower() in why.lower()]
            if echoed:
                issues.append(
                    Issue(
                        "warn",
                        "catalyst_why_restates_date",
                        "Catalyst",
                        f"justification repeats the measured line ({', '.join(echoed)}) "
                        f"instead of saying what the report must prove",
                    )
                )

    for index, reason in enumerate(reasons, start=1):
        count = word_count(reason)
        if count > WORD_BUDGET["reason"]:
            issues.append(
                Issue(
                    "error",
                    "reason_too_long",
                    f"Reason {index}",
                    f"{count} words (budget {WORD_BUDGET['reason']})",
                )
            )
        # ---- substance ---------------------------------------------------
        # Deliberately a warning, not an error. ORCL's second reason --
        # "The market is overpricing the effects of GPU depreciation and debt
        # servicing" -- carries no number and no named comparison, so requiring
        # one would reject a verbatim reference reason. The nudge stays visible;
        # brevity (below) is the rule that actually gets enforced.
        if not (_has_number(reason) or _has_named_comparison(reason)):
            issues.append(
                Issue(
                    "warn",
                    "reason_no_anchor",
                    f"Reason {index}",
                    "no number and no named comparison; a specific figure would make it checkable",
                )
            )
        if not _has_mechanism(reason):
            issues.append(
                Issue(
                    "warn",
                    "reason_no_mechanism",
                    f"Reason {index}",
                    "no causal link (if/because/leads to); reads as an assertion",
                )
            )
        if is_valuation_only(reason, writeup.get("direction")):
            issues.append(
                Issue(
                    "error",
                    "reason_valuation_only",
                    f"Reason {index}",
                    "rests on a multiple with no mechanism -- a discount is not a "
                    "thesis; say what the market is missing or what will change",
                )
            )
        if is_pe_rollforward(reason):
            issues.append(
                Issue(
                    "warn",
                    "reason_pe_rollforward",
                    f"Reason {index}",
                    "next-year vs current-year PE is true of any grower and "
                    "distinguishes nothing; say why the multiple is wrong",
                )
            )
        # ---- the comparisons that make a true fact not misleading -----------
        hints = writeup.get("evidence_hints") or {}
        sequential = sequential_without_year(reason, hints)
        if sequential and sequential.get("conflict"):
            issues.append(
                Issue(
                    "error",
                    "reason_sequential_without_year",
                    f"Reason {index}",
                    f"quotes a sequential move in {sequential.get('label')} "
                    f"({sequential.get('qoq_pct'):+.1f}% QoQ to {sequential.get('period')}) "
                    f"without the year-over-year move, which is "
                    f"{sequential.get('yoy_pct'):+.1f}% -- state both, because the "
                    f"quarter is growing, not deteriorating",
                )
            )
        elif sequential:
            issues.append(
                Issue(
                    "warn",
                    "reason_sequential_unpaired",
                    f"Reason {index}",
                    "gives a sequential move with no year-over-year comparison; the "
                    "packet supplies both and the pair is the fact",
                )
            )

        speculative = speculative_reason(reason)
        if speculative and speculative[0] == "horizon":
            issues.append(
                Issue(
                    "warn",
                    "reason_long_horizon",
                    f"Reason {index}",
                    f'leans on "{speculative[1]}", a payoff the dated catalyst cannot '
                    f"settle; tie it to something the report will actually show",
                )
            )
        elif speculative:
            issues.append(
                Issue(
                    "warn",
                    "reason_chain_too_long",
                    f"Reason {index}",
                    f"chains several steps ({speculative[1]}); each extra link is "
                    f"unchecked, so cut it to the one the evidence supports",
                )
            )

        if is_stale_consensus_on_counts(reason, writeup.get("quants")):
            issues.append(
                Issue(
                    "error",
                    "reason_stale_consensus_on_counts",
                    f"Reason {index}",
                    "calls the consensus stale on a count of analysts who revised: the "
                    "raises are how the number got to where it is, and the packet's own "
                    "EPS trend says the level did not move -- say what the number should "
                    "be and why, not that it is old",
                )
            )

    deal = ignores_deal(reasons, writeup.get("evidence_hints"))
    if deal:
        confirmed = bool(deal.get("confirmed"))
        issues.append(
            Issue(
                "error" if confirmed else "warn",
                "reason_ignores_deal" if confirmed else "reason_deal_unattributed",
                "Reasons",
                f"{'goodwill' if confirmed else 'intangibles'} stepped "
                f"{deal.get('change_pct'):+.0f}% in {deal.get('period')}, which "
                f"{'means a deal closed' if confirmed else 'usually means a deal closed'}"
                f" in that period, so reported growth there is bought rather than organic "
                f"-- name the acquisition and what it contributes, or argue from a line it "
                f"cannot flatter",
            )
        )

    for severity, code, detail in watch_problems(writeup.get("watch"), writeup.get("evidence_hints")):
        issues.append(Issue(severity, code, "Watch", detail))

    if notes and word_count(notes) > WORD_BUDGET["notes"]:
        issues.append(
            Issue("warn", "notes_too_long", "Structuring", f"{word_count(notes)} words (budget {WORD_BUDGET['notes']})")
        )

    # A note that repeats itself at length is usually padding.
    if len(reasons) > 1:
        longest = max(reasons, key=word_count)
        if word_count(longest) > WORD_BUDGET["reason"] * 0.9 and len(reasons) >= 4:
            issues.append(
                Issue("warn", "likely_padding", "Reasons", "several long reasons; cut to the strongest three")
            )

    # ---- language --------------------------------------------------------
    all_text = " ".join([description, *[str(r) for r in reasons], str(notes)])

    for phrase in HEDGES:
        if _phrase_re(phrase).search(all_text):
            issues.append(Issue("error", "hedging", _locate(phrase, description, reasons), f'hedge "{phrase.strip()}"'))

    for phrase in FILLER:
        if _phrase_re(phrase).search(all_text):
            issues.append(Issue("warn", "filler", _locate(phrase, description, reasons), f'empty intensifier "{phrase}"'))

    for acronym in unglossed_acronyms(all_text):
        issues.append(
            Issue("warn", "unglossed_acronym", _locate(acronym, description, reasons), f'"{acronym}" used without [plain-word gloss]')
        )

    # ---- tone ------------------------------------------------------------
    desc_lower = description.lower()
    for opener in VAGUE_OPENERS:
        if desc_lower.startswith(opener):
            issues.append(
                Issue("warn", "vague_opener", "Description", f'starts with "{opener}" -- lead with what it does')
            )
            break

    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warn"]

    # Score: start at 100, errors cost 18, warnings 5.
    score = max(0, 100 - 18 * len(errors) - 5 * len(warnings))

    return {
        "issues": [str(i) for i in issues],
        "issues_detail": [i.as_dict() for i in issues],
        "errors": len(errors),
        "warnings": len(warnings),
        "score": score,
        "ok": not errors,
        "stats": {
            "description_words": word_count(description),
            "reason_words": [word_count(r) for r in reasons],
            "reason_count": len(reasons),
            "notes_words": word_count(notes),
            "catalyst_why_words": word_count((writeup.get("catalyst") or {}).get("why") or ""),
            "has_structure": bool((writeup.get("structuring") or {}).get("rows")),
        },
    }


def _locate(needle: str, description: str, reasons: list[str]) -> str:
    if needle.lower() in (description or "").lower():
        return "Description"
    for index, reason in enumerate(reasons, start=1):
        if needle.lower() in str(reason).lower():
            return f"Reason {index}"
    return "text"


def lint_batch(writeups: list[dict]) -> dict:
    """Lint several writeups and summarise."""
    results = [{"ticker": w.get("ticker"), **lint_writeup(w)} for w in writeups]
    return {
        "results": results,
        "passed": sum(1 for r in results if r["ok"]),
        "failed": sum(1 for r in results if not r["ok"]),
        "mean_score": round(sum(r["score"] for r in results) / len(results), 1) if results else 0,
    }


# --------------------------------------------------------------------------
# grounding
# --------------------------------------------------------------------------

# Numbers small enough to be ordinary counting language ("two quarters", "3 of 5")
# rather than a factual claim, so they are not worth checking.
_SMALL_INT = 13

_NUMBER_RE = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d*\.\d+)(\s*%)?")
_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")

# URLs are full of digit runs, and a bare "25" inside a link is not evidence that a
# note's "25.38" is supported. Dates are the same problem in a different shape:
# "Jun 25, 2026" harvests a "25" that can vouch for a figure that has no support.
# All three are ignored when harvesting the numbers an evidence source can vouch for.
_URL_RE = re.compile(r"\S*://\S*|\S*www\.\S*", re.IGNORECASE)
_MONTHS = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
_TEXT_DATE_RES = (
    re.compile(rf"\b(?:{_MONTHS})[a-z]*\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{2,4}}", re.I),
    re.compile(rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTHS})[a-z]*\.?,?\s+\d{{2,4}}", re.I),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
)


def _number_is_a_fragment(text: str, match: re.Match[str]) -> bool:
    """True when the match is the head of a longer number, e.g. ``202`` in ``2026``.

    ``_NUMBER_RE`` caps its integer branch at three digits so that thousands
    separators and dates parse, which means a four-digit year matches as its first
    three. Treating "202" as a figure the evidence does or does not contain is noise
    in both directions -- it was matching prose years against unrelated evidence, and
    it invented source mismatches for figures that were cited correctly.
    """
    end = match.end(1)
    return end < len(text) and text[end].isdigit()


def _ignored_spans(text: str) -> list[tuple[int, int]]:
    """Character spans whose digits are context, not evidence: dates and URLs."""
    return [
        match.span()
        for pattern in (_DATE_RE, _URL_RE, *_TEXT_DATE_RES)
        for match in pattern.finditer(text or "")
    ]


def _evidence_numbers(evidence: str) -> set[str]:
    """Every number appearing in the evidence, plus rounded variants.

    Rounding matters: a note may legitimately write "43.5" where the packet says
    43.54, and "39.5" for 39.51. Both must count as supported.

    What must NOT count is a number that only appears as part of something else. A
    date contributes "2025-09-25" and a link contributes its path digits, and either
    can hand a prose figure a match it has not earned -- the BB note's invented
    "25.38% UEM growth" was passing the grounding check on a bare "25" harvested from
    a URL. Numbers inside dates and URLs are therefore skipped, as are the heads of
    longer digit runs.
    """
    text = evidence or ""
    ignored = _ignored_spans(text)
    numbers: set[str] = set()
    for match in _NUMBER_RE.finditer(text):
        if _number_is_a_fragment(text, match):
            continue
        start, end = match.span(1)
        if any(lo <= start and end <= hi for lo, hi in ignored):
            continue
        raw = match.group(1).replace(",", "")
        try:
            value = abs(float(raw))
        except ValueError:
            continue
        numbers.add(f"{value:g}")
        numbers.add(f"{value:.1f}")
        numbers.add(f"{value:.2f}")
        numbers.add(f"{value:.0f}")
        # Percentages are often stored as fractions.
        numbers.add(f"{value * 100:g}")
        numbers.add(f"{value * 100:.1f}")
    return numbers


def _figure_candidates(raw: str, value: float) -> set[str]:
    """The forms a prose figure may legitimately take in the evidence.

    Rounding is allowed, but only downwards from the writer's precision: a note that
    writes "43" for 43.2 has chosen to round, while a note that writes "6.8" has not,
    and rounding *that* to "7" let an unrelated 7.0 market cap vouch for it. The
    asymmetry is the point -- one direction is a writer's choice, the other is the
    checker inventing a match.
    """
    candidates = {f"{value:g}", f"{value:.1f}", f"{value:.2f}"}
    if "." not in raw:
        candidates.add(f"{value:.0f}")
    return candidates


# --------------------------------------------------------------------------
# evidence-shape checks
# --------------------------------------------------------------------------
# Each of these exists because a note passed every other check while being wrong in
# a way a reader could not see without opening the sources. They read the same shape
# of evidence the writer was given (``writeup["evidence_hints"]``), so they can only
# fire when the packet actually supplied the comparison that is missing.

_SEQUENTIAL_MARKERS = (
    "sequential",
    "sequentially",
    "quarter over quarter",
    "quarter-over-quarter",
    "qoq",
    "prior quarter",
    "previous quarter",
    "last quarter",
)
_ANNUAL_MARKERS = (
    "year over year",
    "year-over-year",
    "yoy",
    "a year ago",
    "a year earlier",
    "year earlier",
    "year ago",
    "same quarter last year",
    "prior year",
    "last year",
)

# How a reason names a statement line in prose. Keyed by the canonical label the
# packet uses, because a writer says "revenue" and never "Total Revenue".
_LINE_WORDS = {
    "Total Revenue": ("revenue", "sales", "top line"),
    "Net Income": ("net income", "net profit", "profit", "earnings"),
    "EBIT": ("ebit", "operating income", "operating profit"),
    "Operating Income": ("operating income", "operating profit"),
    "EBITDA": ("ebitda",),
    "Gross Profit": ("gross profit", "gross margin"),
    "Interest Income": ("interest income", "float", "client funds", "interest on"),
    "Net Interest Income": ("net interest income",),
    "Interest Expense": ("interest expense",),
}

_DEAL_WORDS = (
    "acqui",  # acquisition, acquired, acquires
    "merger",
    "merged",
    "bought",
    "purchase",
    "takeover",
    "synerg",
    "integrat",
    "consolidat",
    "the deal",
    "deal closed",
)

# A payoff that arrives years from now cannot be decided by a dated report, and a
# chain that long cannot be checked against any single source.
_LONG_HORIZON = (
    "over time",
    "eventually",
    "in the long run",
    "in the coming years",
    "over the coming years",
    "for years to come",
    "over the next decade",
    "in a few years",
    "will ultimately",
    "structurally lower",
    "structurally higher",
    "secular",
)
# A Watch line can settle a variable without a figure: "flat or falling client counts
# confirm, rising breaks it" is a complete test. So the check accepts an explicit pair
# of readings, not only a number.
_TEST_PAIRS = (
    ("confirm", "break"),
    ("confirms", "breaks"),
    ("above", "below"),
    ("beat", "miss"),
    ("rising", "falling"),
    ("higher", "lower"),
    ("raise", "cut"),
    ("faster", "slower"),
    ("more than", "less than"),
    ("holds", "falls"),
    ("up", "down"),
)

_MULTI_HOP = (
    "which leads to",
    "which means",
    "which will",
    "which would",
    "leading to",
    "resulting in",
    "in turn",
    "and that leads",
)


def _mentioned_lines(text: str) -> list[str]:
    """Which statement lines a reason's wording refers to, if any."""
    low = text.lower()
    return [
        label
        for label, words in _LINE_WORDS.items()
        if any(word in low for word in words)
    ]


def sequential_without_year(reason: str, hints: dict | None) -> dict | None:
    """A sequential move quoted on its own, when the annual move says otherwise.

    The failure this exists for: a note reported "revenue down 11.2% and net income
    down 24.9% sequentially" as evidence the numbers were deteriorating. Both figures
    were right, both were sourced, and the same quarter grew 12.5% in revenue and
    41.5% in net income year over year. Sequential moves for a business with a
    seasonal calendar and a mid-year acquisition are close to meaningless, so the rule
    is not "never quote one" -- it is "never quote one without the other".
    """
    low = str(reason).lower()
    if not any(marker in low for marker in _SEQUENTIAL_MARKERS):
        return None
    if any(marker in low for marker in _ANNUAL_MARKERS):
        return None
    rows = (hints or {}).get("yoy") or []
    if not rows:
        return None

    mentioned = _mentioned_lines(reason)
    conflicts = [
        row
        for row in rows
        if row.get("conflict") and (not mentioned or row.get("label") in mentioned)
    ]
    if conflicts:
        row = conflicts[0]
        return {
            "label": row.get("label"),
            "qoq_pct": row.get("qoq_pct"),
            "yoy_pct": row.get("yoy_pct"),
            "period": row.get("period"),
            "conflict": True,
        }
    row = next((r for r in rows if r.get("label") in mentioned), rows[0])
    return {"label": row.get("label"), "conflict": False, "period": row.get("period")}


def ignores_deal(reasons: list[str], hints: dict | None) -> dict | None:
    """Growth argued from a period an acquisition landed in, with no mention of it.

    The balance sheet says a deal closed; that revenue is bought, not won. A thesis
    built on the growth rate without saying so is measuring the wrong thing.

    The returned row carries ``confirmed``: true when goodwill stepped, which only
    purchase accounting does, and false when only intangibles moved. The caller makes
    the confirmed case an error and the suspected case a warning, because a writer
    cannot be required to name an acquisition that may not have happened.
    """
    deals = (hints or {}).get("deal") or []
    if not deals:
        return None
    blob = " ".join(str(r).lower() for r in reasons)
    if any(word in blob for word in _DEAL_WORDS):
        return None
    return deals[0]


def speculative_reason(reason: str) -> tuple[str, str] | None:
    """A long-horizon payoff or an over-long causal chain. Returns (kind, detail)."""
    low = str(reason).lower()
    for phrase in _LONG_HORIZON:
        if _phrase_re(phrase).search(low):
            return ("horizon", phrase.strip())
    hops = [phrase for phrase in _MULTI_HOP if phrase in low]
    if len(hops) >= 2:
        return ("chain", ", ".join(hops))
    return None


def _states_both_readings(line: str) -> bool:
    """True when a Watch line gives both directions rather than one assertion."""
    low = str(line).lower()
    if any(a in low and b in low for a, b in _TEST_PAIRS):
        return True
    # "flat or falling ... rising breaks it" -- an explicit break clause also counts.
    return ("break" in low or "invalidat" in low) and (
        "confirm" in low or "flat" in low or "falling" in low or "rising" in low
    )


def watch_problems(watch: list, hints: dict | None) -> list[tuple[str, str, str]]:
    """Checks for the Watch block: ``(severity, code, detail)`` per problem.

    The block is required when the print is close, because that is when the reader
    most needs to know which number decides the idea. Each line has to name a
    variable and the reading that would break the thesis -- a line that only restates
    a reason is not a test.
    """
    lines = [str(w).strip() for w in (watch or []) if str(w).strip()]
    days = (hints or {}).get("catalyst_days")
    required = days is not None and days <= WATCH_REQUIRED_WITHIN_DAYS

    if not lines:
        if required:
            return [
                (
                    "error",
                    "watch_missing",
                    f"the catalyst is {days} days out and the note has no Watch block: "
                    f"name the 2-4 variables that decide it at that report, with the "
                    f"reading that confirms and the reading that breaks the thesis",
                )
            ]
        return []

    problems: list[tuple[str, str, str]] = []
    if required and not 2 <= len(lines) <= WATCH_MAX_LINES:
        problems.append(
            ("warn", "watch_count", f"{len(lines)} line(s); 2-4 is the useful range")
        )
    elif len(lines) > WATCH_MAX_LINES:
        problems.append(("warn", "watch_count", f"{len(lines)} lines; cut to {WATCH_MAX_LINES}"))
    for index, line in enumerate(lines, start=1):
        if word_count(line) > WATCH_WORD_BUDGET:
            problems.append(
                (
                    "warn",
                    "watch_too_long",
                    f"line {index} is {word_count(line)} words (budget {WATCH_WORD_BUDGET})",
                )
            )
        if not (_has_number(line) or _has_named_comparison(line) or _states_both_readings(line)):
            problems.append(
                (
                    "warn",
                    "watch_no_test",
                    f"line {index} names no reading that would settle it; give the "
                    f"number or direction that confirms and the one that breaks it",
                )
            )
    return problems


def check_grounding(writeup: dict, evidence: str) -> dict:
    """Verify that numbers in the *prose* appear in the evidence.

    The generator already guarantees that the Quants block and the option legs
    come from measured data -- the model cannot reach them. Reason prose is the
    one place a model could introduce a figure from its own memory, so it is the
    one place worth checking.

    Deliberately a warning, not a failure. A note may legitimately state a
    derived figure (a price target implied by a stated % move) or a claim from a
    search snippet, so the job here is to surface anything unsupported for a human
    to eyeball rather than to block the note.
    """
    evidence_numbers = _evidence_numbers(evidence)
    evidence_dates = [m.group(0) for m in _DATE_RE.finditer(evidence or "")]
    evidence_blob = (evidence or "").lower()

    checked: list[str] = []
    unsupported: list[str] = []

    prose = [
        writeup.get("description") or "",
        *[str(r) for r in (writeup.get("reasons") or [])],
        *[str(w) for w in (writeup.get("watch") or [])],
    ]

    for text in prose:
        for match in _NUMBER_RE.finditer(text):
            raw = match.group(1).replace(",", "")
            is_percent = bool(match.group(2))
            try:
                value = abs(float(raw))
            except ValueError:
                continue

            # The head of a longer number is not a figure. See _number_is_a_fragment.
            if _number_is_a_fragment(text, match):
                continue
            # Bare small integers are counting language, not claims.
            if not is_percent and value < _SMALL_INT and "." not in raw:
                continue

            checked.append(raw)
            if _figure_candidates(raw, value) & evidence_numbers:
                continue

            # A year mentioned in prose (2026, 2027) is context, not a claim.
            if not is_percent and 2000 <= value <= 2100 and "." not in raw:
                continue
            # Any part of a date that appears in the evidence is that date.
            if any(raw in part for part in evidence_dates):
                continue
            # Last resort: does the literal string appear anywhere in evidence?
            if raw in evidence_blob:
                continue

            unsupported.append(f'"{raw}{"%" if is_percent else ""}"')

    return {
        "checked": len(checked),
        "unsupported": sorted(set(unsupported)),
        "grounded": not unsupported,
        "ratio": round(1 - len(set(unsupported)) / max(1, len(checked)), 3),
    }


# A bare integer this size or smaller is counting language ("30 days", "four
# quarters"), not a claim, so it is not worth matching to a source. Decimals and
# percentages are always checked whatever their size, because that is the shape a
# real figure takes here.
_SOURCE_SMALL_INT = 100


def _number_is_a_fragment(text: str, match: re.Match[str]) -> bool:
    """True when the match is the head of a longer number, e.g. ``202`` in ``2026``.

    ``_NUMBER_RE`` caps its integer branch at three digits, so a four-digit year
    matches as its first three -- and "202 not in S19" is noise, not a finding. The
    pattern is deliberate for money ("1,234") and dates, so the fix belongs here
    rather than in the regex.
    """
    end = match.end(1)
    return end < len(text) and text[end].isdigit()


# Direction words a survey or series reading uses. Coarse on purpose: the question is
# only whether two readings of the same driver point the same way, and a false
# "check this" costs a reader a minute while a missed reversal costs the idea.
_DIRECTION_UP = (
    "rose",
    "rises",
    "rising",
    " up ",
    "higher",
    "highest",
    "increased",
    "increasing",
    "accelerat",
    "grew",
    "growing",
    "improved",
    "stronger",
    "rebounded",
)
_DIRECTION_DOWN = (
    "fell",
    "falls",
    "falling",
    " down ",
    "lower",
    "lowest",
    "decreased",
    "decreasing",
    "declin",
    "slowed",
    "slowing",
    "weaken",
    "eased",
    "easing",
    "softened",
)


# Entries that are not dated readings of an external driver: a statement column, a
# consensus snapshot or an option chain has a date but no "latest reading" to prefer.
_NOT_A_READING = ("statements", "consensus", "fundamentals", "options", "catalyst")

# Words that carry no subject: they appear in almost every reading of every series,
# so overlap on them would pair unrelated drivers.
_SUBJECT_STOP = {
    "about",
    "after",
    "their",
    "there",
    "these",
    "those",
    "which",
    "would",
    "could",
    "should",
    "since",
    "level",
    "levels",
    "points",
    "reports",
    "report",
    "reported",
    "remains",
    "remain",
    "still",
    "highest",
    "lowest",
    "increase",
    "increased",
    "decrease",
    "decreased",
    "according",
    "company",
    "companies",
}


def _reading_text(entry: dict) -> str:
    """The entry's own wording, for judging subject overlap."""
    return f"{entry.get('label') or ''} {entry.get('text') or ''}"


def _reading_claim(entry: dict) -> str:
    """Just the reading, without the note-style gloss that follows it.

    The direction has to come from the claim itself. Trend entries carry a second
    sentence explaining what the reading means for the company ("slowing payroll
    volume", "weighing on revenue"), and that gloss is written in the direction of
    the thesis, not of the survey -- counting it turns "highest since 2024" into a
    tie and loses the reversal.
    """
    text = str(entry.get("text") or entry.get("label") or "")
    head = text.split(". ")[0]
    return head[:240]


def _content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{5,}", str(text).lower()) if w not in _SUBJECT_STOP}


def _shared_subject(left: set[str], right: set[str]) -> bool:
    """True when two readings are about enough of the same thing to be one series."""
    if not left or not right:
        return False
    return len(left & right) / max(1, min(len(left), len(right))) >= 0.25


def reading_direction(text: str) -> int:
    """``+1`` rising, ``-1`` falling, ``0`` no clear direction."""
    low = str(text).lower()
    up = sum(1 for word in _DIRECTION_UP if word in low)
    down = sum(1 for word in _DIRECTION_DOWN if word in low)
    if up > down:
        return 1
    if down > up:
        return -1
    return 0


def superseded_readings(writeup: dict, catalogue: list[dict]) -> list[str]:
    """Reasons resting on an older reading of a driver that the packet says reversed.

    The failure this exists for: a note's lead reason said small-business job openings
    "fell to 29%, the lowest since May 2020" -- sourced, accurate, and the newest
    reading in the packet was the opposite, with employment plans up 9 points and a
    June report showing hiring difficulty at its highest since 2024. Nothing in the
    note was false; the note simply used the reading that fitted. Picking the latest
    observation of a series is not a style preference, it is the difference between
    describing a trend and selecting one.
    """
    by_id = {str(e.get("id") or "").upper(): e for e in catalogue}
    reason_sources = writeup.get("reason_sources") or []
    reasons = [str(r) for r in (writeup.get("reasons") or [])]
    findings: list[str] = []

    for index, reason in enumerate(reasons):
        cited = reason_sources[index] if index < len(reason_sources) else []
        for entry in cited:
            entry = entry if isinstance(entry, dict) else by_id.get(str(entry).upper())
            if not entry or entry.get("kind") in _NOT_A_READING:
                continue
            direction = reading_direction(_reading_claim(entry))
            date = str(entry.get("date") or "")[:10]
            provider = str(entry.get("provider") or "")
            if direction == 0 or not date or not provider:
                continue
            words = _content_words(_reading_text(entry))
            newer = [
                other
                for other in catalogue
                if other is not entry
                and str(other.get("provider") or "") == provider
                and str(other.get("date") or "")[:10] > date
                and reading_direction(_reading_claim(other)) == -direction
                # Same provider is not enough: two articles on one site are not one
                # series. The pair must be about the same subject, which is what the
                # wording overlap tests.
                and _shared_subject(words, _content_words(_reading_text(other)))
            ]
            if not newer:
                continue
            latest = max(newer, key=lambda e: str(e.get("date") or ""))
            findings.append(
                f'Reason {index + 1}: cites {entry.get("id")} '
                f'({date}, {provider}, reading '
                f'{"up" if direction > 0 else "down"}) but {latest.get("id")} '
                f'({str(latest.get("date"))[:10]}, same provider) reads the other way '
                f'-- use the latest reading and say what changed'
            )
    return findings


def check_source_grounding(writeup: dict, catalogue: list[dict] | None = None) -> dict:
    """Find figures cited to a source that does not contain them.

    ``check_grounding`` answers "is this figure in the packet somewhere?". That is
    weaker than it sounds once a reason names its evidence, and this check is the
    stronger question: the reader sent to ``S7`` has to find the figure in ``S7``.

    It reports only figures that are **in the packet but in a different source**, and
    names that source. That restriction is what makes the output trustworthy rather
    than noisy: if a figure appears in no catalogue entry at all, it is either
    derived (a target implied by a stated move) or absent from that entry's stored
    summary, and neither is evidence of a miscitation -- ``check_grounding`` already
    covers "nowhere in the packet". A figure that is in exactly one other source,
    though, has an obvious right answer and was cited to the wrong place.

    A warning rather than an error. A reason may legitimately rest on a source for
    its claim and quote a figure introduced by the reason above it.
    """
    catalogue = catalogue if catalogue is not None else (writeup.get("sources_catalogue") or [])
    by_id = {str(e.get("id") or "").upper(): e for e in catalogue}
    reason_sources = writeup.get("reason_sources") or []
    reasons = [str(r) for r in (writeup.get("reasons") or [])]

    # Built once: the numbers each source can vouch for.
    source_numbers = {
        str(e.get("id") or "").upper(): _evidence_numbers(str(e.get("text") or ""))
        for e in catalogue
    }

    mismatches: list[str] = []
    checked = 0

    for index, reason in enumerate(reasons):
        cited = reason_sources[index] if index < len(reason_sources) else []
        if not cited:
            continue
        cited_ids = [str(e.get("id") or "").upper() for e in cited]
        cited_numbers: set[str] = set()
        for source_id in cited_ids:
            cited_numbers |= source_numbers.get(source_id, set())
            # A citation may resolve to an entry the catalogue passed in does not
            # carry, in which case the note's own stored copy is still checkable.
            if source_id not in source_numbers:
                entry = by_id.get(source_id) or {}
                cited_numbers |= _evidence_numbers(str(entry.get("text") or ""))

        elsewhere = [
            (source_id, numbers)
            for source_id, numbers in source_numbers.items()
            if source_id not in cited_ids
        ]

        for match in _NUMBER_RE.finditer(reason):
            raw = match.group(1).replace(",", "")
            is_percent = bool(match.group(2))
            try:
                value = abs(float(raw))
            except ValueError:
                continue
            if _number_is_a_fragment(reason, match):
                continue
            if not is_percent and "." not in raw:
                if value < _SOURCE_SMALL_INT or 2000 <= value <= 2100:
                    continue

            checked += 1
            candidates = _figure_candidates(raw, value)
            if candidates & cited_numbers:
                continue

            homes = [source_id for source_id, numbers in elsewhere if candidates & numbers]
            if not homes:
                continue
            mismatches.append(
                f'Reason {index + 1}: "{raw}{"%" if is_percent else ""}" is cited to '
                f'{", ".join(cited_ids)} but appears in {", ".join(homes)}'
            )

    superseded = superseded_readings(writeup, catalogue) if catalogue else []

    return {
        "checked": checked,
        "mismatches": mismatches,
        "superseded": superseded,
        "ok": not mismatches and not superseded,
        "ratio": round(1 - (len(mismatches) + len(superseded)) / max(1, checked), 3),
    }
