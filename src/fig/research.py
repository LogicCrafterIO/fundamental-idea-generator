"""Forward-trend research: what is coming at a business from outside its own filings.

The gap this fills
------------------
Everything else in the packet is about the company: its filings, its consensus,
its price. That produces reasons that describe the *past* ("revenue fell 11.2%
last quarter") or restate valuation. It cannot answer the question a real idea
turns on:

    Why hasn't the obvious problem shown up in the numbers yet?

The PAYX case is the worked example. Paychex sells payroll and HR software to
small businesses. HR and software are both under visible pressure -- AI
substitution and a weak hiring market -- yet Paychex's own revenue and estimates
had not cracked. A note that only reads the filings can say "revenue fell 11.2%"
but cannot say whether that is the beginning or whether something is holding it
up. That is an end-market question, and it is answered outside the filings.

Two-stage design
----------------
Stage 1, **plan**: turn the company's own Description and business summary into
targeted forward-looking search queries. This is done by the model because the
useful questions are company-specific -- "small business hiring" is right for
Paychex, "data centre capex" is right for Oracle -- and a template cannot tell
them apart. It is given the business description and asked only for questions,
so it needs no new facts.

Stage 2, **synthesise**: read the search results and extract a few forward-trend
claims, each carrying the URL and a short verbatim quote.

Grounding is enforced, not requested
------------------------------------
Every claim's quote is checked against the actual search snippets. A claim whose
quote cannot be found is **dropped**, however plausible it reads. This matters
more here than anywhere else in the pipeline: trend claims are exactly the kind
of statement a model can produce fluently from memory, and they are the hardest
for a reader to check. Quotes are normalised for whitespace and typographic
quotes before matching, because search snippets are full of both.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any

from .sources import ollama

MAX_QUERIES = 4
MAX_CLAIMS = 5
# A trend older than this is not "forward-looking" any more. Observed in practice:
# a PAYX trend described the second half of 2025 and the writer presented it as a
# current condition nine months later. Stale evidence is worse than no evidence,
# because it reads exactly like fresh evidence.
MAX_TREND_AGE_DAYS = 180
# Snippets are long; this is what the synthesiser actually reads.
SNIPPET_CHARS = 900


PLAN_PROMPT = """You are preparing research questions about a company's END MARKETS, \
not about the company itself.

The company:
  {symbol} -- {name}
  Description: {description}
  Business summary: {summary}

Write {max_queries} web search queries that would reveal FORWARD-LOOKING pressures \
and supports on this business over the next 1-3 years. Target what is changing \
outside the company that will eventually show up in its numbers:

- the health and direction of its end markets and customer base
- substitution or disruption from technology or new competitors
- its customers' budgets, hiring, or spending trends
- structural decline or growth in the industry it sells into

Rules:
- Each query must be a realistic search string, not a question to a human.
- Include the company name and ticker in at most one query; the rest should \
target the INDUSTRY or the CUSTOMER SEGMENT, so the results are not just \
company press releases about itself.
- No queries about the share price, valuation, or analyst ratings.
- Prefer the CURRENT period: today is {today}. Add the current year where it helps
  surface recent reporting, because evidence more than {max_age_days} days old is
  discarded and evidence about last year is close to useless.

Return ONLY JSON: {{"queries": ["...", "..."]}}"""


SYNTH_PROMPT = """Below are web search results about the industry and end markets of \
{symbol} ({name}).

Extract the FORWARD-LOOKING trends that matter for this business over the next 1-3 \
years. These are trends that have NOT yet fully shown up in the company's reported \
figures -- pressures building, or supports holding current results up.

For each trend return:
  "stance":  "pressure" if the trend works AGAINST the company, "support" if it
             works FOR it. Both are valuable: a "support" often explains why a
             problem has not shown up in the reported figures YET, which is
             exactly what the writer needs to explain.
  "claim":   one sentence, plain language, <= 25 words. What is changing.
  "why":     one sentence, <= 25 words. How it eventually reaches this company's numbers.
  "quote":   a SHORT verbatim excerpt (max 25 words) copied character-for-character
             from the search results below that supports the claim.
  "url":     the URL of the result the quote came from.

HARD RULES:
- The "quote" MUST appear word-for-word in the results below. Claims whose quote
  cannot be found there will be discarded automatically, so do not paraphrase.
- Do not use anything you already know. Only what is in the results.
- Do not write about the share price, valuation, or analyst price targets.
- Prefer specific, checkable statements (numbers, named segments, named policies)
  over generalities like "uncertainty remains".
- If the results do not support a trend, return fewer trends. Returning an empty
  list is better than inventing one.
- If the results contain evidence pointing BOTH ways on the same issue, return both
  as separate trends with opposite stances.
- STATE THE PERIOD the evidence covers, inside the claim ("in the first half of
  2026", "as of June 2026"). Never present an older period as though it were
  current: an item dated 2025 describing 2025 conditions is not forward-looking
  for a report due later in 2026.
- Strongly prefer the most recent evidence. If only older evidence is available for
  a trend, say so in the claim rather than implying it is current. Do not silently pick one side: a source
  saying hiring is cooling and another saying it is accelerating are both findings,
  and the disagreement is itself informative.

Return ONLY JSON: {{"trends": [{{"claim": "...", "why": "...", "quote": "...", "url": "..."}}]}}

SEARCH RESULTS:
{results}"""


# Explicit dates only. packet._date_from_text also matches yearless forms like
# "Sept 18" and assumes the current year -- fine for ordering headlines, actively
# harmful here, because it would make a stale article look current.
_EXPLICIT_PATTERNS = (
    re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b"),
    re.compile(
        r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+(20\d{2})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(20\d{2})\b",
        re.IGNORECASE,
    ),
    # Month-and-year only ("in December 2025", "as of March 2026"). This form is
    # how stale evidence usually presents itself, so missing it was the bug.
    re.compile(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(20\d{2})\b",
        re.IGNORECASE,
    ),
)
_URL_DATE_RE = re.compile(r"/(20\d{2})[/-](\d{1,2})(?:[/-](\d{1,2}))?[/-]")
_MONTHS = {
    m: i
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
        start=1,
    )
}


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        parsed = date(year, month, day)
    except ValueError:
        return None
    # A date in the future is a mention, not a publication date.
    return parsed if parsed <= date.today() else None


def source_date(text: str, url: str | None = None) -> date | None:
    """Newest explicit publication date recoverable from a result, or None.

    A URL path date (`/2026/09/18/`) is trusted first: it is machine-generated
    and cannot be a stray mention in the body. Otherwise the newest explicit date
    in the text is used, which for a dated news page is its publication date.
    """
    if url:
        match = _URL_DATE_RE.search(str(url))
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            day = int(match.group(3)) if match.group(3) else 1
            found = _safe_date(year, month, day)
            if found:
                return found

    candidates: list[date] = []
    for index, pattern in enumerate(_EXPLICIT_PATTERNS):
        for match in pattern.finditer(text or ""):
            if index == 0:
                found = _safe_date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            elif index == 1:
                month = _MONTHS.get(match.group(2)[:3].lower())
                found = _safe_date(int(match.group(3)), month, int(match.group(1))) if month else None
            elif index == 2:
                month = _MONTHS.get(match.group(1)[:3].lower())
                found = _safe_date(int(match.group(3)), month, int(match.group(2))) if month else None
            else:
                month = _MONTHS.get(match.group(1)[:3].lower())
                found = _safe_date(int(match.group(2)), month, 1) if month else None
            if found:
                candidates.append(found)
    return max(candidates) if candidates else None


def _age_days(found: date | None) -> int | None:
    return (date.today() - found).days if found else None


def _normalise(text: str) -> str:
    """Fold whitespace and typographic quotes so quote-matching is robust.

    Search snippets arrive with smart quotes, em dashes and collapsed newlines;
    a verbatim quote from the model will differ in those characters even when it
    copied the words correctly.
    """
    text = (text or "").replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def plan_queries(
    symbol: str,
    company_name: str | None,
    description: str | None,
    summary: str | None,
    *,
    model: str | None = None,
    max_queries: int = MAX_QUERIES,
) -> list[str]:
    """Company-specific forward-looking search queries.

    Falls back to sector-level templates when the model is unavailable or returns
    nothing usable, so the caller always gets queries to run.
    """
    name = company_name or symbol
    fallback = [
        f"{name} industry outlook {date.today().year} demand trends",
        f"{name} competitors disruption market share {date.today().year}",
        f"{name} customers spending hiring trends latest",
    ]
    if not ollama.has_key():
        return fallback[:max_queries]

    prompt = PLAN_PROMPT.format(
        symbol=symbol,
        name=name,
        description=(description or "not supplied")[:400],
        summary=(summary or "not supplied")[:1200],
        max_queries=max_queries,
        today=date.today().isoformat(),
        max_age_days=MAX_TREND_AGE_DAYS,
    )
    try:
        reply = ollama.chat(
            [{"role": "user", "content": prompt}], model=model or ollama.DEFAULT_MODEL
        )
        data = ollama.parse_json_object(reply["text"])
        queries = [str(q).strip() for q in (data.get("queries") or []) if str(q).strip()]
    except Exception:
        queries = []

    # De-duplicate while keeping order, and cap.
    seen: set[str] = set()
    cleaned: list[str] = []
    for query in queries:
        key = query.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(query)
    return cleaned[:max_queries] or fallback[:max_queries]


def _format_results(results: list[dict]) -> str:
    blocks = []
    for index, item in enumerate(results, start=1):
        age = item.get("age_days")
        if age is None:
            stamp = "date unknown"
        elif age <= 45:
            stamp = f"published {item['source_date']} ({age} days old)"
        else:
            stamp = f"published {item['source_date']} ({age // 30} months old)"
        blocks.append(
            f"[{index}] {item.get('title')}\n"
            f"URL: {item.get('url')}\n"
            f"DATE: {stamp}\n"
            f"{(item.get('content') or '')[:SNIPPET_CHARS]}"
        )
    return "\n\n".join(blocks)


def _supporting_results(quote: str, results: list[dict]) -> list[dict]:
    """Results whose text actually contains the quote."""
    needle = _normalise(quote)
    if not needle:
        return []
    words = needle.split()
    head = " ".join(words[:12]) if len(words) > 12 else needle
    supporting = []
    for item in results:
        haystack = _normalise(f"{item.get('content') or ''} {item.get('title') or ''}")
        if needle in haystack or head in haystack:
            supporting.append(item)
    return supporting


def _quote_is_supported(quote: str, results: list[dict]) -> bool:
    """Is the quote actually present in the retrieved snippets?

    A long quote is allowed a partial match on its first clause, because models
    sometimes splice two adjacent sentences; a short quote must match exactly.
    """
    needle = _normalise(quote)
    if not needle:
        return False
    haystack = _normalise(" ".join((r.get("content") or "") + " " + (r.get("title") or "") for r in results))
    if needle in haystack:
        return True

    words = needle.split()
    if len(words) > 12:
        head = " ".join(words[:12])
        if head in haystack:
            return True
    return False


def forward_trends(
    symbol: str,
    company_name: str | None = None,
    description: str | None = None,
    summary: str | None = None,
    *,
    model: str | None = None,
    queries: list[str] | None = None,
    per_query: int = 5,
) -> dict:
    """Plan, search, synthesise, and verify forward-looking end-market trends.

    Returns ``{"queries", "results_count", "trends", "dropped"}``. ``dropped``
    records claims discarded for unsupported quotes, so the discard rate is
    visible rather than silent.
    """
    if not ollama.has_key():
        return {"queries": [], "results_count": 0, "trends": [], "dropped": [], "skipped": "no API key"}

    name = company_name or symbol
    planned = queries or plan_queries(
        symbol, company_name, description, summary, model=model
    )

    results: list[dict] = []
    for query in planned:
        try:
            results.extend(ollama.web_search(query, max_results=per_query))
        except Exception:
            continue

    if not results:
        return {
            "queries": planned,
            "results_count": 0,
            "trends": [],
            "dropped": [],
            "skipped": "no search results",
        }

    # Date every result, then hand the dates to the synthesiser so it can prefer
    # recent sources rather than trusting whatever ranked highest.
    dated = 0
    for item in results:
        found = source_date(
            f"{item.get('title','')} {item.get('content','')}", item.get("url")
        )
        item["source_date"] = found.isoformat() if found else None
        item["age_days"] = _age_days(found)
        if found:
            dated += 1

    prompt = SYNTH_PROMPT.format(
        symbol=symbol, name=name, results=_format_results(results)
    )
    try:
        reply = ollama.chat(
            [{"role": "user", "content": prompt}], model=model or ollama.DEFAULT_MODEL
        )
        raw = ollama.parse_json_object(reply["text"]).get("trends") or []
    except Exception as exc:
        return {
            "queries": planned,
            "results_count": len(results),
            "trends": [],
            "dropped": [],
            "skipped": f"{type(exc).__name__}: {exc}",
        }

    kept: list[dict] = []
    dropped: list[dict] = []
    for item in raw[: MAX_CLAIMS * 2]:
        if not isinstance(item, dict):
            continue
        claim = str(item.get("claim") or "").strip()
        quote = str(item.get("quote") or "").strip()
        if not claim:
            continue
        stance = str(item.get("stance") or "").strip().lower()
        record = {
            "claim": claim,
            "stance": stance if stance in ("pressure", "support") else "unspecified",
            "why": str(item.get("why") or "").strip(),
            "quote": quote,
            "url": item.get("url"),
            "publisher": _publisher(item.get("url")),
        }
        supporting = _supporting_results(quote, results)
        newest = None
        for item in supporting:
            found = item.get("source_date")
            if found and (newest is None or found > newest):
                newest = found
        record["as_of"] = newest
        record["age_days"] = _age_days(date.fromisoformat(newest)) if newest else None
        record["undated"] = newest is None

        if not _quote_is_supported(quote, results):
            # Unsupported: the claim may be fluent and plausible and still not be
            # in the evidence, which is precisely why it is dropped.
            record["drop_reason"] = "quote_not_found_in_results"
            dropped.append(record)
        elif record["age_days"] is not None and record["age_days"] > MAX_TREND_AGE_DAYS:
            # Stale evidence reads exactly like fresh evidence, so it is worse than
            # no evidence. Dropped rather than shown with a caveat the writer may
            # ignore.
            record["drop_reason"] = f"stale ({record['age_days']} days old)"
            dropped.append(record)
        else:
            kept.append(record)
        if len(kept) >= MAX_CLAIMS:
            break

    return {
        "queries": planned,
        "results_count": len(results),
        "results_dated": dated,
        "trends": kept,
        "dropped": dropped,
        "stale_dropped": sum(
            1 for d in dropped if str(d.get("drop_reason", "")).startswith("stale")
        ),
        "max_age_days": MAX_TREND_AGE_DAYS,
    }


def _publisher(url: Any) -> str | None:
    if not url:
        return None
    try:
        host = str(url).split("//", 1)[-1].split("/", 1)[0]
    except (IndexError, AttributeError):
        return None
    return host[4:] if host.startswith("www.") else host


def evidence_verdict(trends: list[dict], direction: str) -> dict:
    """Does the end-market evidence point with the idea or against it?

    Deliberately mechanical, because the whole point of sampling is that the
    qualitative evidence varies between runs. For a SHORT, end-market *pressures*
    support the thesis and *supports* argue against it; for a LONG the reverse.
    Running the research several times and counting these verdicts turns the
    non-determinism into a confidence measure rather than a defect to be papered
    over: "confirmed in 3 of 3 samples" carries information that one run cannot.
    """
    supportive = adverse = 0
    for trend in trends or []:
        stance = (trend.get("stance") or "unspecified").lower()
        if stance == "unspecified":
            continue
        bearish = stance == "pressure"
        with_idea = bearish if direction.lower() == "short" else not bearish
        if with_idea:
            supportive += 1
        else:
            adverse += 1

    if not supportive and not adverse:
        verdict = "no-evidence"
    elif supportive > adverse:
        verdict = "confirms"
    elif adverse > supportive:
        verdict = "contradicts"
    else:
        verdict = "mixed"
    return {"verdict": verdict, "supportive": supportive, "adverse": adverse}


def trends_for_prompt(research: dict) -> list[str]:
    """Compact lines for the evidence block."""
    lines = []
    for trend in research.get("trends") or []:
        stance = trend.get("stance")
        tag = f"[{stance}] " if stance and stance != "unspecified" else ""
        when = trend.get("as_of")
        if when:
            age = trend.get("age_days") or 0
            tag += f"[{when}{'' if age <= 45 else f', {age // 30}mo old'}] "
        elif trend.get("undated"):
            tag += "[date unknown] "
        line = f"  - {tag}{trend['claim']}"
        if trend.get("why"):
            line += f" (reaches the company because: {trend['why']})"
        if trend.get("publisher"):
            line += f" [{trend['publisher']}]"
        lines.append(line)
    return lines
