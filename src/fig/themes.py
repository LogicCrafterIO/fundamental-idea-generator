"""Theme tagging: turn a pile of headlines into the *story* behind an idea.

Why this exists
---------------
Neither reference writeup is a reaction to a single headline. ORCL is a thesis
about AI infrastructure capex, GPU depreciation, RPO conversion and agentic
enterprise software; OMF is a thesis about AI-driven job losses feeding through
to consumer credit losses. Both are **themes**, and the ticker is the vehicle.

So the pipeline needs a story layer: which macro/industry narratives are live
right now, and which names sit in their path.

Why keyword rules instead of embeddings
---------------------------------------
This is a deliberate engineering trade-off, not a limitation to apologise for:

* It is **free and offline** -- no API key, no model download, no per-run cost,
  which is the whole point of a free-data pipeline.
* It is **deterministic and auditable**: every tag traces to matched phrases, so
  a surprising theme assignment can be explained rather than shrugged at.
* Themes in financial media are **highly lexical** -- "data center", "net charge
  off", "forward guidance", "rate cut" are near-perfect signals.

The seam for a smarter tagger is :func:`tag_text(headline, summary)`: swap the
body for an embedding/LLM classifier and the rest of the pipeline is unchanged.
Each theme therefore carries ``keywords`` (matched) and can report ``evidence``.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Theme:
    """A narrative with the phrases that signal it."""

    key: str
    label: str
    keywords: tuple[str, ...]
    description: str
    # Theme pairs that tend to be two sides of the same trade.
    transmission: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)


# Ordering matters only for display. Keep phrases specific: "charge off" is a
# strong signal, "loss" is not.
THEMES: tuple[Theme, ...] = (
    Theme(
        key="ai_capex",
        label="AI infrastructure capex",
        keywords=(
            "data center", "datacenter", "capex", "capital expenditure", "gpu",
            "accelerator", "hyperscaler", "ai infrastructure", "buildout",
            "compute", "nvidia", "tsmc", "power demand", "megawatt",
        ),
        description="Spending on AI compute and the data centres that house it.",
        transmission="Capex funds the buildout but depreciates fast and is often debt-financed.",
        tags=("long_infra", "short_depreciation"),
    ),
    Theme(
        key="ai_monetisation",
        label="AI revenue and monetisation",
        keywords=(
            "rpo", "remaining performance obligation", "backlog", "bookings",
            "ai revenue", "monetis", "monetiz", "agentic", "copilot", "inference",
            "cloud revenue", "ai product", "adoption",
        ),
        description="Whether AI spending is converting into recognised revenue.",
        transmission="Backlog is not revenue; conversion timing is the whole debate.",
        tags=("long_software",),
    ),
    Theme(
        key="consumer_credit",
        label="Consumer credit deterioration",
        keywords=(
            "net charge-off", "net charge off", "charge-off", "charge off", "nco",
            "delinquen", "provision", "credit loss", "default rate", "subprime",
            "nonprime", "consumer credit", "write-off", "write off", "allowance",
            "loan loss", "unemployment", "jobless", "layoff", "job losses",
        ),
        description="Stress in household balance sheets showing up as loan losses.",
        transmission="Rising unemployment hits lenders through provisions and charge-offs.",
        tags=("short_credit",),
    ),
    Theme(
        key="rates",
        label="Rates and funding costs",
        keywords=(
            "interest rate", "fed", "fomc", "rate cut", "rate hike", "yield",
            "treasury", "funding cost", "debt servicing", "refinanc", "spread",
            "credit spread", "duration",
        ),
        description="The cost of money, and who pays more for it.",
        transmission="High funding costs punish levered balance sheets and long-duration equities.",
        tags=("macro",),
    ),
    Theme(
        key="depreciation_debt",
        label="Depreciation and balance-sheet strain",
        keywords=(
            "depreciation", "useful life", "impairment", "goodwill", "debt",
            "leverage", "covenant", "downgrade", "free cash flow", "fcf",
            "capital burden", "amortis", "amortiz",
        ),
        description="Accounting for ageing assets and the cost of the debt behind them.",
        transmission="Short useful lives and heavy debt turn reported profit into a cash problem.",
        tags=("short_quality",),
    ),
    Theme(
        key="valuation_dispersion",
        label="Valuation dispersion",
        keywords=(
            "valuation", "multiple", "p/e", "forward pe", "price-to-sales",
            "price to sales", "overvalued", "undervalued", "cheap", "expensive",
            "discount", "premium", "re-rating", "rerating", "bubble",
        ),
        description="Similar businesses priced very differently.",
        transmission="A multiple gap between comparable businesses is the trade.",
        tags=("relative_value",),
    ),
    Theme(
        key="regulation",
        label="Regulation and legal",
        keywords=(
            "antitrust", "regulat", "lawsuit", "settlement", "fined", "probe",
            "investigation", "compliance", "licence", "license", "tariff",
            "export control", "sanction", "legislation", "doj", "ftc",
            # NOT a bare "sec": it matches "Security" at a word start, which
            # tagged every Social Security story as regulation.
            "sec filing", "securities and exchange",
        ),
        description="Legal and regulatory constraints that change the economics.",
        transmission="Regulatory capture or exposure can protect or destroy a margin.",
        tags=("moat", "risk"),
    ),
    Theme(
        key="mna",
        label="M&A and capital returns",
        keywords=(
            "acquisition", "acquire", "merger", "takeover", "buyout", "spin-off",
            "spinoff", "divest", "buyback", "dividend", "tender offer", "stake",
        ),
        description="Corporate action changing the share count or asset base.",
        transmission="Deal flow re-prices the assets involved.",
        tags=("catalyst",),
    ),
    Theme(
        key="guidance",
        label="Guidance and estimate revisions",
        keywords=(
            "guidance", "outlook", "forecast", "revis", "estimate", "consensus",
            "warns", "pre-announce", "preannounce", "beats", "misses",
            "earnings preview", "cuts guidance", "raises guidance", "guidance cut",
        ),
        description="Changes to what the company and analysts expect next.",
        transmission="Revisions move multiples before the earnings actually land.",
        tags=("catalyst",),
    ),
    Theme(
        key="positioning",
        label="Positioning and flows",
        keywords=(
            "short interest", "insider", "13f", "institutional", "options",
            "open interest", "squeeze", "flows", "sentiment", "upgrade",
            "downgrade", "price target",
        ),
        description="Who owns it and how it is being traded.",
        transmission="Crowded positioning makes otherwise-symmetric bets asymmetric.",
        tags=("tactical",),
    ),
)

_BY_KEY = {t.key: t for t in THEMES}

# Keyword matching is anchored at a **word start** and allows any suffix, which
# is what lets deliberate stems ("revis" -> revision/revisions, "regulat" ->
# regulation/regulatory, "delinquen" -> delinquency/delinquencies) work while
# blocking the false positives that plain substring matching produces.
#
# Plain `in` matching was tried first and was badly wrong on real headlines:
#   "nco"   matched "Income"      -> every dividend piece tagged as credit stress
#   "sec"   matched "Security"    -> every Social Security piece tagged as regulation
#   "stake" matched "Mistake"
# A leading \b fixes the first and third. The second cannot be fixed by anchoring
# -- "Security" genuinely starts with "sec" -- so ambiguous short tokens were
# replaced with specific phrases in the lexicon below.
_COMPILED: dict[str, list[tuple[str, re.Pattern[str]]]] = {}


def _pattern(keyword: str) -> re.Pattern[str]:
    # Multi-word phrases tolerate any whitespace between words.
    escaped = re.escape(keyword).replace(r"\ ", r"\s+")
    return re.compile(r"\b" + escaped, re.IGNORECASE)


def _compile_all() -> None:
    if _COMPILED:
        return
    for theme in THEMES:
        _COMPILED[theme.key] = [(kw, _pattern(kw)) for kw in theme.keywords]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def tag_text(*texts: str) -> list[str]:
    """Theme keys implied by the given text(s)."""
    _compile_all()
    blob = _normalise(" ".join(t for t in texts if t))
    hits = []
    for theme in THEMES:
        if any(pattern.search(blob) for _, pattern in _COMPILED[theme.key]):
            hits.append(theme.key)
    return hits


def match_keywords(text: str) -> dict[str, list[str]]:
    """Which phrases triggered which theme -- the audit trail for a tag."""
    _compile_all()
    blob = _normalise(text)
    out: dict[str, list[str]] = {}
    for theme in THEMES:
        found = [kw for kw, pattern in _COMPILED[theme.key] if pattern.search(blob)]
        if found:
            out[theme.key] = found
    return out


def theme_label(key: str) -> str:
    theme = _BY_KEY.get(key)
    return theme.label if theme else key


def theme_description(key: str) -> str:
    theme = _BY_KEY.get(key)
    return theme.description if theme else ""


def score_stories(items: list[dict]) -> dict:
    """Aggregate a list of news items into weighted themes.

    Returns ``{"themes": [{key, label, count, share, evidence}], "top": key}``.
    Each item should carry ``title`` and optionally ``summary``.
    """
    counts: Counter[str] = Counter()
    evidence: dict[str, list[dict]] = {}

    for item in items:
        text = f"{item.get('title','')} {item.get('summary','')}"
        for key in tag_text(text):
            counts[key] += 1
            evidence.setdefault(key, [])
            if len(evidence[key]) < 4:
                evidence[key].append(
                    {
                        "title": item.get("title"),
                        "publisher": item.get("publisher"),
                        "published": item.get("published") or item.get("created"),
                        "matched": match_keywords(text).get(key, []),
                    }
                )

    total = sum(counts.values()) or 1
    themes = [
        {
            "key": key,
            "label": theme_label(key),
            "description": theme_description(key),
            "count": count,
            "share": round(count / total, 3),
            "evidence": evidence.get(key, []),
        }
        for key, count in counts.most_common()
    ]
    return {"themes": themes, "top": themes[0]["key"] if themes else None}


def theme_pairing(theme_keys: list[str]) -> list[dict]:
    """Suggest long/short pairings implied by the live themes.

    The OMF writeup is the interesting case: the *same* macro force (AI adoption)
    is read as bullish for infrastructure and bearish for consumer lenders. This
    surfaces such two-sided readings so a candidate search can look on both sides
    of one story.
    """
    pairs = []
    keys = set(theme_keys)
    if "ai_capex" in keys and "consumer_credit" in keys:
        pairs.append(
            {
                "story": "AI adoption is bullish capex, bearish labour income",
                "long_side": "AI infrastructure and power",
                "short_side": "consumer lenders exposed to job losses",
            }
        )
    if "ai_capex" in keys and "depreciation_debt" in keys:
        pairs.append(
            {
                "story": "AI capex is real but its accounting is aggressive",
                "long_side": "asset-light AI software and data owners",
                "short_side": "debt-funded, depreciation-heavy builders",
            }
        )
    if "valuation_dispersion" in keys and "ai_monetisation" in keys:
        pairs.append(
            {
                "story": "Same AI narrative, very different multiples",
                "long_side": "cheap incumbent with distribution",
                "short_side": "expensive pure-play on the same story",
            }
        )
    return pairs
