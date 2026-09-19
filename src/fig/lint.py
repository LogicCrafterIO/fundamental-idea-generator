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
    "because", "since", "so ", "then ", "if ", "leads to", "drives", "results in",
    "causes", "as a result", "which means", "therefore", "forces", "makes",
    "given that", "due to", "means that", "would ", "will ", "when ",
]

NUMBER_RE = re.compile(r"\d")
TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9''\-\.%$]*")


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


def lint_writeup(writeup: dict) -> dict:
    """Check one writeup dict. Returns ``{issues, errors, warnings, score, ok}``."""
    issues: list[Issue] = []

    description = (writeup.get("description") or "").strip()
    reasons = [r for r in (writeup.get("reasons") or []) if str(r).strip()]
    notes = (writeup.get("structuring") or {}).get("reflection") or writeup.get("notes") or ""

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


def _evidence_numbers(evidence: str) -> set[str]:
    """Every number appearing in the evidence, plus rounded variants.

    Rounding matters: a note may legitimately write "43.5" where the packet says
    43.54, and "39.5" for 39.51. Both must count as supported.
    """
    numbers: set[str] = set()
    for match in _NUMBER_RE.finditer(evidence or ""):
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
    evidence_dates = set(_DATE_RE.findall(evidence or ""))
    evidence_blob = (evidence or "").lower()

    checked: list[str] = []
    unsupported: list[str] = []

    prose = [writeup.get("description") or "", *[str(r) for r in (writeup.get("reasons") or [])]]

    for text in prose:
        for match in _NUMBER_RE.finditer(text):
            raw = match.group(1).replace(",", "")
            is_percent = bool(match.group(2))
            try:
                value = abs(float(raw))
            except ValueError:
                continue

            # Bare small integers are counting language, not claims.
            if not is_percent and value < _SMALL_INT and "." not in raw:
                continue

            checked.append(raw)
            candidates = {f"{value:g}", f"{value:.1f}", f"{value:.2f}", f"{value:.0f}"}
            if candidates & evidence_numbers:
                continue

            # A year mentioned in prose (2026, 2027) is context, not a claim.
            if not is_percent and 2000 <= value <= 2100 and "." not in raw:
                continue
            # Dates: check the ISO form is present.
            if any(part == raw for part in evidence_dates):
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
