"""Trend research: the three parts of a business, researched one lens at a time.

The framework
-------------
A business has three parts, and a trend acts through one of them:

``demand``   What customers are buying, and how that is changing. End-market
             growth, budget cycles, substitution, new buyers, volume versus
             price. This is the lens the parent pipeline already has
             (:mod:`fig.research` asks about end markets and stops there).
``sold``     How it is sold. Route to market, channel mix, pricing model
             (subscription, licence, usage, per-seat), procurement cycles,
             customer concentration, distributor or dealer power. A demand
             trend that never reaches the seller's channel does not reach the
             income statement.
``made``     How it is made. Inputs, supply chain, manufacturing and capacity,
             labour, logistics, the cost curve, and the regulation of
             production. This is where a demand trend gets turned into margin --
             or eaten by it.

Asking all three questions is the point. A single "industry outlook" query
returns the demand story, which is the one every sell-side note already tells;
the channel and the cost base are where a qualitative screen finds something the
consensus has not priced, because they are reported by trade press and industry
bodies rather than by the company.

Where the queries come from
---------------------------
Stage 1, **plan**: one model call, given the company's summary *and its revenue
streams*, returns queries tagged by lens and by stream. It is done by the model
because the useful question is specific -- "small business hiring" for Paychex,
"data centre power constraints" for Oracle -- and a template cannot tell those
apart. It is asked only for questions, so it needs no new facts.

Stage 2, **synthesise**: one call reads every result, tagged by lens and by the
stream it was asked about, and returns trends that carry a stance, a verbatim
quote and the quantum ratings below.

The quantum ratings
-------------------
A theme list is only useful if it is ordered, and ordering prose requires a
rubric rather than a vibe. Each trend is rated on three anchored 1-5 scales, and
each rating must state its basis in the evidence:

======================  =====================================================
``size``   1-5          How much money the trend moves across the industry:
                        5 > $100bn or most of the revenue pool, 4 $10-100bn,
                        3 $1-10bn, 2 $100m-1bn, 1 smaller or evidently niche.
``speed``  1-5          When it bites: 5 already visible in reported numbers,
                        4 within 12 months, 3 one to three years, 2 three to
                        five years, 1 beyond five years or speculative.
``impact`` 1-5          What it does to *this* company: 5 decides total revenue
                        or margin direction, 4 materially moves a major stream,
                        3 moves a minority stream, 2 second-order sentiment,
                        1 immaterial.
======================  =====================================================

The rubric is published in the prompt, so the ratings are comparable between two
names researched in different waves, and each one carries a ``*_basis`` line so a
reader can disagree with the rating without having to re-read the source. Where
the evidence states no magnitude, the instruction is to rate 2 or 3 and say so --
never to invent a market size to justify a higher number.
"""

from __future__ import annotations

import re
from datetime import date

from fig.sources import ollama

from . import grounding

# The three parts of the business, in the order they are written up. The key is
# what the model returns; the label is what a reader sees.
LENSES: tuple[dict, str] = (
    {
        "key": "demand",
        "label": "Trending demand",
        "question": "what customers buy and how that is changing",
    },
    {
        "key": "sold",
        "label": "How it's sold",
        "question": "route to market, channel, pricing model, concentration",
    },
    {
        "key": "made",
        "label": "How it's made",
        "question": "inputs, supply chain, capacity, labour, cost curve",
    },
)
LENS_KEYS = tuple(lens["key"] for lens in LENSES)
LENS_LABEL = {lens["key"]: lens["label"] for lens in LENSES}

MAX_QUERIES = 8
MAX_STREAM_QUERIES = 3
MAX_TRENDS = 12
# How many existing theme keys are offered for reuse in one synthesis prompt.
MAX_VOCABULARY = 120
MIN_TRENDS_PER_LENS = 1

# Trends whose only evidence is over a year old are kept -- the mechanism may
# still be live -- but they are marked, and the writeup prints the age beside the
# quote rather than letting a 2024 report read as a current condition.
STALE_DAYS = 365

THEME_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


PLAN_PROMPT = """You are preparing research questions about the three parts of one \
business: its DEMAND, HOW IT IS SOLD, and HOW IT IS MADE.

The company:
  {symbol} -- {name}
  Sector: {sector} | Industry: {industry}
  Business summary: {summary}
  Revenue streams (extracted from filings and company disclosure):
{streams}

Write {max_queries} web search queries that would surface TRENDS in those three \
parts over the next one to three years, for THIS company and the industries it \
sells into. Each query is tagged with the part it targets:

- "demand": end-market demand, customer budgets, volumes, substitution, new buyers.
- "sold": how the product reaches the customer -- channel and distributor shifts,
  pricing model changes, procurement, customer concentration, competitive bidding.
- "made": inputs and supply chain, manufacturing capacity, labour, logistics,
  input costs, the regulation of production.

Rules:
- At least two queries per part. Every query must be a realistic search string,
  not a question to a human.
- Target INDUSTRY RESEARCH, TRADE PRESS AND INDUSTRY BODIES where possible: ask for
  market reports, association data, trade publications, and the customer segment --
  not company press releases about itself. Include the company name in at most two
  queries; the rest must stand on the industry alone.
- Where the query concerns one revenue stream, name it in "stream"; otherwise set
  "stream" to null. Cover the streams that carry the most revenue.
- NO queries about the share price, valuation, analyst ratings, or earnings dates.
- Prefer the CURRENT period: today is {today}. Add the current year where it helps
  surface recent reporting -- evidence more than a year old is flagged as history.
- Prefer questions whose answers change what the company earns or what it costs,
  over general commentary about an industry.

Return ONLY JSON: {{"queries": [{{"q": "...", "lens": "demand|sold|made", \
"stream": "stream name or null"}}]}}"""


SYNTH_PROMPT = """Below are web results about the demand, the channel and the cost \
base of {symbol} ({name}), its revenue streams, and the industries it sells into.

Extract the TRENDS that matter to this business's economics over the next one to \
three years. A trend must act through one of the three parts:

  "demand" -- what customers buy and how that is changing
  "sold"   -- how it reaches the customer: channel, pricing model, procurement,
              concentration, competition for the same wallet
  "made"   -- inputs, supply chain, capacity, labour, logistics, cost curve

For each trend return:
  "lens":      "demand" | "sold" | "made"
  "stream":    the revenue stream it acts on, copied from the list below, or
               "the business overall". Never invent a stream.
  "claim":     one sentence, plain language, <= 25 words. What is changing, and
               STATE THE PERIOD the evidence covers ("in the first half of 2026",
               "as of June 2026"). Older evidence must never be presented as current.
  "direction": "tailwind" if it helps THIS company's revenue or margin, "headwind"
               if it hurts, "two-sided" if the same force cuts both ways.
  "why":       one sentence, <= 25 words. The mechanism by which it reaches this
               company's income statement.
  "quote":     a SHORT verbatim excerpt (max 25 words) copied character-for-character
               from the results below that supports the claim.
  "url":       the URL of the result the quote came from.
  "source_type": what kind of source the quote came from:
               "trade"           trade press, an industry body, an association survey,
                                 a regulator, or a named market-research house
               "company"         the company's own disclosure or press release
               "market_research" a vendor market-report summary page whose only content
                                 is a market size and a CAGR forecast
               "general"         general news media
               Choose honestly: a reader discounts a vendor forecast differently from an
               association survey, and the tag is how they can tell.
  "size":      1-5. How much money the trend moves across the industry:
               5 = over $100bn, or most of the industry's revenue pool
               4 = $10-100bn, or a large minority of the pool
               3 = $1-10bn
               2 = $100m-1bn, a niche line
               1 = smaller than that, or evidently niche
  "size_basis": <= 15 words. The magnitude the evidence states, or "no magnitude in
               evidence". NEVER invent a market size to justify a rating: if the
               evidence gives none, rate 2 or 3 and say so.
  "speed":     1-5. When it bites:
               5 = already visible in reported numbers for the current year
               4 = shows up within 12 months
               3 = one to three years
               2 = three to five years
               1 = beyond five years, or speculative
  "speed_basis": <= 15 words. The period or adoption evidence that justifies it.
  "impact":    1-5. What it does to THIS company:
               5 = decides the direction of total revenue or margin
               4 = materially moves a major revenue stream
               3 = moves a material but minority stream
               2 = second-order, mostly narrative or sentiment
               1 = immaterial to the numbers
  "impact_basis": <= 15 words. Which stream it reaches and how much of it.
  "theme_key": a canonical kebab-case slug for the underlying theme, at the level
               of an industry force and NOT of this company. It must be reusable by
               another company in the same industry: "ai-data-centre-capex",
               "small-business-hiring-weakness", "insurance-loss-cost-inflation".
               Do NOT include the ticker, and do not coin a key for a fact about
               this company alone.
               IF THE EXISTING THEME KEYS BELOW ALREADY NAME THIS FORCE, REUSE THAT KEY
               EXACTLY AS WRITTEN -- character for character, including its spelling.
               Coin a new key only when none of them fits. This is how the same force
               found by two companies ends up as one theme instead of two.
  "theme_label": a plain-English title for that theme, <= 8 words.
  "theme_definition": one sentence, <= 25 words: what the theme is, in words that
               work for any company it touches.

HARD RULES:
- Every "quote" MUST appear word-for-word in the results below. A trend whose quote
  cannot be found there is discarded automatically, so do not paraphrase.
- Do not use anything you already know. Only the results.
- Prefer PRIMARY and TRADE sources when the results offer them: an industry body or
  association survey, a regulator, trade press, or the company's own disclosure beats
  a vendor market-report page that states only a market size and a growth rate. Use
  such a page when it is the best available, and tag it "market_research" so the
  reader can weigh it accordingly.
- Cover all three parts. If the results genuinely say nothing about one part, return
  nothing for it rather than inventing a trend to fill the section.
- Prefer specific, checkable statements (numbers, named segments, named policies,
  named customers) over generalities like "uncertainty remains".
- If the results contain evidence pointing BOTH ways on the same issue, return both
  as separate trends with opposite directions -- the disagreement is the finding.
- Strongly prefer the most recent evidence. If only older evidence exists, say the
  period in the claim so the reader can see it is not current.
- Return at most {max_trends} trends. Fewer, better-supported trends beat a long list.
- Do not pad the list with the same force restated per region: if one theme arrives
  five times for five geographies, return it once, with the widest evidence, and put
  the regional detail in the claim.

Return ONLY JSON: {{"trends": [{{...}}]}}

EXISTING THEME KEYS (reuse one of these when it names the same force; coin a new key
only when none of them fits):
{vocabulary}

REVENUE STREAMS:
{streams}

SEARCH RESULTS:
{results}"""


def plan_queries(
    symbol: str,
    name: str,
    *,
    summary: str | None,
    sector: str | None,
    industry: str | None,
    streams: list[dict] | None = None,
    model: str | None = None,
    max_queries: int = MAX_QUERIES,
) -> list[dict]:
    """Model-planned queries, tagged by lens and stream.

    Falls back to a deterministic set when the model is unavailable or returns
    nothing usable, so a run always has queries to run -- the fallback is
    deliberately industry-level, which is what "no model" costs.
    """
    streams = streams or []
    stream_list = "\n".join(f"    - {s['name']}: {s.get('what_it_is') or ''}" for s in streams) or "    (none extracted)"
    label = name or symbol
    subject = industry or sector or "the industry"
    fallback = [
        {"q": f"{subject} market outlook demand trends {date.today().year}", "lens": "demand", "stream": None},
        {"q": f"{subject} industry report growth forecast {date.today().year}", "lens": "demand", "stream": None},
        {"q": f"{subject} distribution channel shift pricing model {date.today().year}", "lens": "sold", "stream": None},
        {"q": f"{subject} distributors dealers procurement trends {date.today().year}", "lens": "sold", "stream": None},
        {"q": f"{subject} supply chain input costs outlook {date.today().year}", "lens": "made", "stream": None},
        {"q": f"{subject} manufacturing capacity labour costs {date.today().year}", "lens": "made", "stream": None},
        {"q": f"{label} demand outlook customer budgets latest", "lens": "demand", "stream": None},
    ]

    if not ollama.has_key():
        return fallback[:max_queries]

    prompt = PLAN_PROMPT.format(
        symbol=symbol,
        name=label,
        sector=sector or "unknown",
        industry=industry or "unknown",
        summary=(summary or "not supplied")[:2000],
        streams=stream_list,
        max_queries=max_queries,
        today=date.today().isoformat(),
    )
    try:
        reply = ollama.chat([{"role": "user", "content": prompt}], model=model or ollama.DEFAULT_MODEL)
        data = ollama.parse_json_object(reply["text"])
        planned = data.get("queries") or []
    except Exception:
        planned = []

    cleaned: list[dict] = []
    seen: set[str] = set()
    for item in planned:
        if isinstance(item, str):
            item = {"q": item}
        if not isinstance(item, dict):
            continue
        query = str(item.get("q") or item.get("query") or "").strip()
        lens = str(item.get("lens") or "").strip().lower()
        if not query or lens not in LENS_KEYS:
            continue
        key = query.lower()
        if key in seen:
            continue
        seen.add(key)
        stream = item.get("stream")
        cleaned.append(
            {
                "q": query,
                "lens": lens,
                "stream": str(stream).strip() if stream and str(stream).strip() else None,
            }
        )
        if len(cleaned) >= max_queries:
            break

    # The model's plan is kept only if it covers every part; otherwise the
    # deterministic set is used, because a plan with no "made" queries would
    # silently delete a third of the framework from the writeup.
    covered = {item["lens"] for item in cleaned}
    if len(cleaned) < 4 or covered != set(LENS_KEYS):
        return fallback[:max_queries]
    return cleaned


def stream_queries(
    streams: list[dict],
    *,
    industry: str | None,
    sector: str | None,
    max_queries: int = MAX_STREAM_QUERIES,
) -> list[dict]:
    """One deterministic demand query per major revenue stream.

    The plan's queries are industry-level; these make sure each big stream is
    asked about by name, which is what lets the synthesiser attach a trend to a
    specific stream instead of to "the business overall".
    """
    subject = industry or sector or "industry"
    ordered = sorted(
        streams or [],
        key=lambda s: (s.get("revenue_share") is None, -(s.get("revenue_share") or 0)),
    )
    out = []
    for stream in ordered[:max_queries]:
        out.append(
            {
                "q": f"{stream['name']} {subject} market growth demand outlook {date.today().year}",
                "lens": "demand",
                "stream": stream["name"],
            }
        )
    return out


def research(
    symbol: str,
    name: str,
    *,
    summary: str | None,
    sector: str | None = None,
    industry: str | None = None,
    streams: list[dict] | None = None,
    model: str | None = None,
    per_query: int = 5,
    queries: list[dict] | None = None,
    vocabulary: list[dict] | None = None,
) -> dict:
    """Plan, search across all three lenses, synthesise, verify.

    ``vocabulary`` is the theme keys already coined by earlier companies, offered to the
    synthesiser to reuse. Without it every company invents its own key for a force it
    shares with five others -- measured on the first batch, only 17% of trends sat in a
    theme reaching more than one company, which defeats the point of a theme file. It is
    passed in rather than fetched here so the caller owns the accumulation and can seed
    it from the artifacts already on disk.

    Returns ``{"queries", "results_count", "trends", "dropped", "by_lens",
    "coverage"}``. ``coverage`` names the lenses that produced nothing, which is
    what the writeup turns into "no grounded trend found for this part" instead of
    an empty heading.
    """
    streams = streams or []
    planned = queries or (
        plan_queries(
            symbol,
            name,
            summary=summary,
            sector=sector,
            industry=industry,
            streams=streams,
            model=model,
        )
        + stream_queries(streams, industry=industry, sector=sector)
    )

    results: list[dict] = []
    searched: list[dict] = []
    for item in planned:
        try:
            found = ollama.web_search(item["q"], max_results=per_query)
        except Exception:
            continue
        for row in found:
            row["lens"] = item["lens"]
            row["stream"] = item.get("stream")
            row["query"] = item["q"]
        results.extend(found)
        searched.append({"query": item["q"], "lens": item["lens"], "stream": item.get("stream"), "results": len(found)})

    grounding.date_results(results)
    outcome = {
        "queries": planned,
        "searched": searched,
        "results": results,
        "results_count": len(results),
        "trends": [],
        "dropped": [],
        "by_lens": {},
        "coverage": {},
    }
    if not results:
        outcome["skipped"] = "no search results"
        outcome["coverage"] = {key: 0 for key in LENS_KEYS}
        return outcome

    stream_list = "\n".join(
        f"    - {s['name']} ({s.get('revenue_share') or 'share not disclosed'})" for s in streams
    ) or "    (none extracted -- use \"the business overall\")"

    prompt = SYNTH_PROMPT.format(
        symbol=symbol,
        name=name or symbol,
        max_trends=MAX_TRENDS,
        streams=stream_list,
        vocabulary=format_vocabulary(vocabulary),
        results=grounding.format_results(results),
    )
    try:
        reply = ollama.chat(
            [{"role": "user", "content": prompt}], model=model or ollama.DEFAULT_MODEL
        )
        raw = ollama.parse_json_object(reply["text"]).get("trends") or []
    except Exception as exc:
        outcome["skipped"] = f"{type(exc).__name__}: {exc}"
        outcome["coverage"] = {key: 0 for key in LENS_KEYS}
        return outcome

    trends, dropped = _verify(raw, results, streams)
    outcome["trends"] = trends
    outcome["dropped"] = dropped
    outcome["by_lens"] = {
        key: sum(1 for t in trends if t["lens"] == key) for key in LENS_KEYS
    }
    outcome["coverage"] = outcome["by_lens"]
    outcome["stale_dropped"] = sum(
        1 for t in trends if (t.get("age_days") or 0) > STALE_DAYS
    )
    return outcome


def format_vocabulary(vocabulary: list[dict] | None, *, limit: int = MAX_VOCABULARY) -> str:
    """The reuse list handed to the synthesiser: ``key -- label``, most-used first.

    Capped, because the list is prompt budget: past a hundred-odd keys the marginal one
    is a force from an unrelated industry that this company will never touch, and it
    costs context that the evidence needs.
    """
    items = (vocabulary or [])[:limit]
    if not items:
        return "    (none yet -- you are the first company researched, so coin the keys)"
    return "\n".join(f"    {item['key']} -- {item.get('label') or ''}" for item in items)


def _rating(value, default: int = 3) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(1, min(5, number))


def _verify(raw: list, results: list[dict], streams: list[dict]) -> tuple[list[dict], list[dict]]:
    """Ground each trend, repair its fields, and keep the dropped ones visible.

    The repair is deliberately conservative: an unparsable rating becomes 3 (the
    middle of the scale, which is the honest answer for "not stated") rather than
    being dropped, but a trend with no lens is dropped -- an unlabelled trend
    cannot be placed in the three-part framework, which is the framework's whole
    claim. A ``stream`` the model invented is reset to "the business overall"
    rather than dropped, since the trend is still real and only its attachment was
    wrong.
    """
    valid_streams = {s["name"].lower() for s in streams}
    kept, dropped = [], []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        claim = str(item.get("claim") or "").strip()
        lens = str(item.get("lens") or "").strip().lower()
        if not claim:
            continue
        if lens not in LENS_KEYS:
            dropped.append({"claim": claim, "drop_reason": f"unknown lens {lens!r}"})
            continue

        record = {
            "lens": lens,
            "stream": str(item.get("stream") or "").strip() or "the business overall",
            "claim": claim,
            "direction": _direction(item.get("direction")),
            "why": str(item.get("why") or "").strip(),
            "quote": str(item.get("quote") or "").strip(),
            "url": item.get("url"),
            "source_type": _source_type(item.get("source_type")),
            "size": _rating(item.get("size")),
            "size_basis": str(item.get("size_basis") or "").strip(),
            "speed": _rating(item.get("speed")),
            "speed_basis": str(item.get("speed_basis") or "").strip(),
            "impact": _rating(item.get("impact")),
            "impact_basis": str(item.get("impact_basis") or "").strip(),
            "theme_key": slugify(item.get("theme_key")),
            "theme_label": str(item.get("theme_label") or "").strip(),
            "theme_definition": str(item.get("theme_definition") or "").strip(),
        }
        if record["stream"].lower() not in valid_streams and record["stream"] != "the business overall":
            record["stream_note"] = "attached stream was not one of the extracted streams"
            record["stream"] = "the business overall"
        if not record["theme_key"]:
            dropped.append({**record, "drop_reason": "no usable theme key"})
            continue

        hits = grounding.supporting_results(record["quote"], results)
        if not hits:
            dropped.append({**record, "drop_reason": "quote_not_found_in_retrieved_results"})
            continue

        newest = None
        for hit in hits:
            found = hit.get("source_date")
            if found and (newest is None or found > newest):
                newest = found
        record["as_of"] = newest
        record["age_days"] = grounding.age_days(newest)
        record["stale"] = bool(record["age_days"] and record["age_days"] > STALE_DAYS)
        record["publisher"] = grounding.publisher(record.get("url")) or hits[0].get("publisher")
        record["url"] = record.get("url") or hits[0].get("url")
        record["lens_label"] = LENS_LABEL[lens]
        record["theme_label"] = record["theme_label"] or record["theme_key"].replace("-", " ")
        kept.append(record)
        if len(kept) >= MAX_TRENDS:
            break
    return kept, dropped


def _direction(value) -> str:
    text = str(value or "").strip().lower()
    if text in ("tailwind", "headwind", "two-sided"):
        return text
    if text in ("positive", "support", "upside", "beneficiary"):
        return "tailwind"
    if text in ("negative", "pressure", "downside", "victim"):
        return "headwind"
    return "two-sided"


SOURCE_TYPES = ("trade", "company", "market_research", "general")


def _source_type(value) -> str:
    """Normalise the source tag, defaulting to the vaguest honest label.

    An unlabelled source becomes ``general`` rather than ``trade``: the tag exists
    so a reader can discount a vendor forecast page, and defaulting to the more
    credible label would defeat it.
    """
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return text if text in SOURCE_TYPES else "general"


def slugify(value) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text if THEME_KEY_RE.match(text) else ""
