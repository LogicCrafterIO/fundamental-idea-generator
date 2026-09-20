"""Revenue streams: what the company actually sells, and what each line pays.

Why this section exists at all
------------------------------
A business summary describes what a company *is*; it rarely says where the money
comes from. "Provides software and services to the healthcare industry" is
consistent with a $40bn licence business and with a $200m consulting shop. The
trend research then has nothing to attach to, because a trend acts on a revenue
stream -- on the segment that sells to a customer whose budget is moving -- not
on the company in the abstract.

So the streams are extracted first, and everything downstream hangs off them:
the trend queries are per stream, and the theme writeup says which of a company's
streams a theme touches.

Grounding, and the two paths through it
---------------------------------------
Every stream must clear one of two tests:

* its **quote** appears in the retrieved results -- typically a 10-K segment
  table, an earnings release, or a company "how we make money" page; or
* its **name** appears in the company's own business summary, which is a real
  source shipped through Yahoo.

A stream that clears neither is dropped and recorded. That asymmetry is
deliberate: segment disclosure is thin for smaller names, and requiring a search
hit would drop true streams for exactly the companies whose filings are least
indexed, while accepting the summary keeps them honest -- the company said so
itself.

Amounts and shares are quoted, never inferred. If the evidence gives no split,
the stream is published as "share not disclosed" rather than with a plausible
number, because a made-up revenue mix silently corrupts every ranking downstream.
The **only** numbers the screener itself screens on remain price and market cap;
a revenue figure appears here solely as the sourced size of a stream, which is
what makes the stream comparable with the industry trend quoted beside it.
"""

from __future__ import annotations

import re
from datetime import date

from fig.sources import ollama

from . import grounding

MAX_STREAMS = 8
# Queries per name. The fourth is the one that actually produces numbers: segment
# *tables* are what state a split, and the sites that republish them in indexable
# HTML are reached by naming the ticker and the kind of page, not by asking for the
# filing. Without it, only 23% of extracted streams carried a share or an amount --
# the filings were being outranked by "how does X make money" explainers, which
# describe the streams well and quantify none of them.
MAX_STREAM_QUERIES = 4


STREAM_PROMPT = """You are extracting the REVENUE STREAMS of one company -- where its \
money actually comes from, line by line.

The company:
  {symbol} -- {name}
  Sector: {sector} | Industry: {industry}
  Its own business summary: {summary}

Below are web results: segment tables from filings, earnings material, and company \
descriptions of how they earn money.

Return:
  "description": 2-4 sentences, at most 120 words. What this company does and how it \
earns money, precise enough that a reader knows the business better than the summary \
alone lets them. Rewrite the supplied evidence in plainer words; add NOTHING that is \
not in the evidence, and quote no number that is not in it.
  "split_basis": which dimension the stream list below is cut along -- one of \
"product_line", "revenue_type", "business_segment", "geography".
  "revenue_streams": one entry per DISTINCT way the company earns money. Cut the list \
along WHAT IS SOLD, not along where it is sold:
    - Prefer the product or service lines the company itself reports (sparkling drinks, \
water and sports drinks, juice and dairy; for a lender: net interest income, card fees, \
investment banking fees, trading). This is the split a reader can reason about demand \
against, and the one the trend research hangs on.
    - Prefer "revenue_type" where the company reports how it earns (interest, fee, \
premium, subscription, licence, service) alongside or instead of product lines -- for \
banks, insurers and utilities this is the only split that explains the economics.
    - Use "geography" ONLY when the company discloses nothing else. If both exist, the \
streams are the product/revenue-type lines and the geographic split goes in "geography".
    - Aim for 4 to 7 streams covering the whole company, not just the fastest-growing \
part.

Rules per entry:
    "name":          the stream as the company names it (<= 8 words). If the company \
does not name it, name it plainly.
    "what_it_is":    one sentence, <= 20 words: what is sold and to whom.
    "revenue_share": decimal fraction of total revenue. Use the figure the evidence \
states when it states one -- an approximate figure counts ("~50%", "about a fifth", \
"roughly 3%"), recorded as the midpoint of the range and flagged "approximate". If the \
evidence states no share but gives both this stream's revenue and the company's total \
revenue, you may compute it and flag it "derived". Set both fields to null when neither \
is available. Never estimate, never read a share off a chart.
    "revenue_share_basis": "stated" | "approximate" | "derived" | null.
    "amount":        the revenue figure for this stream exactly as the evidence \
states it, with its currency and period (e.g. "$4.2B in FY2025", "\u00a51.06tn in FY2026"). \
Only a REVENUE figure belongs here: if the evidence gives this stream's profit, assets, \
deposits, order book or transaction value instead, set "amount" to null rather than \
substituting it. Never compute the figure.
    "customer":      who pays (<= 12 words), or null.
    "quote":         a SHORT verbatim excerpt (max 25 words) copied character-for-\
character from the results below that supports this stream.
    "url":           the URL of the result the quote came from.
  "geography": the geographic mix in one sentence, if the evidence states one, else null.
  "customer_concentration": one sentence if the evidence states a concentration \
(largest customer, top-10 share, % recurring), else null.
  "notes": anything the evidence says about mix shift -- a stream growing or shrinking \
faster than the total -- else null.

HARD RULES:
- Every "quote" MUST appear word-for-word in the results below. Entries whose quote \
cannot be found are discarded automatically.
- Do not use anything you already know about this company. Only the results.
- Do not merge two streams to make a tidier list, and do not split one stream into \
sub-lines.
- If the results describe the business but disclose no split, return the streams you \
can support and leave every revenue_share and amount null. An honest list of streams \
with no numbers is worth more than a fabricated mix.

Return ONLY JSON: {{"description": "...", "split_basis": "...", \
"revenue_streams": [{{...}}], "geography": null, "customer_concentration": null, \
"notes": null}}"""


CURRENCY_MARKERS = (
    "$", "\u00a5", "\u20ac", "\u00a3", "\u20b9", "usd", "jpy", "eur", "gbp", "cny", "rmb",
    "krw", "cad", "aud", "chf", "sek", "nok", "dkk", "brl", "mxn", "inr", "try", "zar",
)


def amount_is_usable(amount) -> bool:
    """Is this an amount a reader can use, or a bare number of unknown units?

    The guard exists because of one real output: a segment "revenue" of
    ``1.06T (FY2026)`` for a Japanese bank whose segments are reported in yen while its
    market cap is quoted in dollars. The number may well have been the segment's
    *assets* rather than its revenue, and either way a figure with no currency is not
    something a reader can compare with anything -- so it is rejected.

    Two tests, both mechanical: it must contain a digit, and it must name a currency.
    Anything else is withheld and kept in the artifact as ``amount_raw`` for audit.
    """
    if amount is None:
        return False
    text = str(amount)
    if not any(character.isdigit() for character in text):
        return False
    lowered = text.lower()
    return any(marker in lowered for marker in CURRENCY_MARKERS)


def plan_queries(name: str, symbol: str, sector: str | None, industry: str | None) -> list[str]:
    """Deterministic revenue-breakdown queries.

    These are templated rather than model-planned on purpose: the shape of the
    question does not vary by company ("what are the segments and what did each
    earn"), unlike the end-market questions in :mod:`qts.trends`, which do. One
    fewer model call per name, and a query set that is identical across a batch,
    so a missing stream is a source problem and not a prompt lottery.
    """
    year = date.today().year
    label = f"{name} ({symbol})" if name and name.upper() != symbol else symbol
    subject = industry or sector or "business"
    return [
        f"{label} revenue by segment product line breakdown annual report 10-K",
        f"{name} how it makes money revenue streams {subject} {year}",
        f"{label} segment revenue percentage of total latest quarter results",
        # The share-carrying query: names the ticker and the page type, which is how
        # a segment table in indexable HTML gets found.
        f"{symbol} stock revenue by segment breakdown percentage of total revenue",
    ][:MAX_STREAM_QUERIES]


SHARE_PERCENT_RE = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d+)?)\s*%")
APPROXIMATE_MARKERS = ("~", "about", "around", "roughly", "nearly", "approximately", "circa", "c.")
# Wording that means the percentage is a *rate of change*, not a share of revenue.
# Without this guard "Revenue grew 6.8% in the quarter on sparkling soft drinks volume"
# was read as sparkling drinks being 6.8% of revenue -- a wrong number presented as a
# stated one, which is the failure this whole pipeline exists to prevent.
CHANGE_CUES = re.compile(
    r"\b(grew|grow\w*|rose|ris\w+|fell|fall\w*|increas\w+|decreas\w+|higher|lower|"
    r"yoy|year-over-year|cagr|gain\w*|declin\w+|expand\w*|contract\w*|up|down)\b"
)
# A share printed as a share is short: a table row, a bullet, a percentage beside the
# stream's name. Anything longer is prose, and percentages in prose are growth rates.
MAX_SHARE_QUOTE_CHARS = 60


def share_from_quote(quote: str | None, name: str) -> tuple[float, str] | None:
    """Recover a revenue share the model had in front of it but did not record.

    A real failure, seen on the first published batch: the evidence line for Coca-Cola's
    segments reads ``Sparkling Soft Drinks | ~50%``, the quote is printed in the writeup
    directly under a table cell saying "not disclosed", and the reader is left to do the
    conversion the tool should have done. The prompt permits an approximate figure; the
    model simply did not always take it.

    So the share is recovered mechanically, under guards that keep it from inventing
    anything: the quote must **name the stream**, it must be short and read like a line
    from a table rather than a sentence, it must contain **exactly one** percentage, and
    it must not contain wording that marks that percentage as a rate of change. Returns
    ``(fraction, basis)`` or ``None``.
    """
    if not quote or not name:
        return None
    text = str(quote)
    if len(text) > MAX_SHARE_QUOTE_CHARS:
        return None
    lowered = grounding.normalise(text)
    if CHANGE_CUES.search(lowered):
        return None
    words = [w for w in re.findall(r"[a-z]{4,}", str(name).lower())]
    if not words:
        return None
    # The stream has to be what the line is about: named at its head, or in a table row.
    head = lowered[:45]
    if not (any(word in head for word in words) or "|" in text):
        return None
    found = SHARE_PERCENT_RE.findall(text)
    if len(found) != 1:
        return None
    value = float(found[0])
    if not (0 < value <= 100):
        return None
    basis = "approximate" if any(marker in lowered for marker in APPROXIMATE_MARKERS) else "stated"
    return round(value / 100.0, 4), basis


def extract(
    symbol: str,
    name: str,
    *,
    summary: str | None,
    sector: str | None = None,
    industry: str | None = None,
    model: str | None = None,
    per_query: int = 5,
) -> dict:
    """Search for the split, then synthesise and verify the streams.

    Returns ``{"queries", "results_count", "streams", "dropped", "description",
    ...}``. ``dropped`` is published, not swallowed: a name that returns six
    streams of which four failed grounding is a name whose evidence was thin, and
    the writeup says so.
    """
    queries = plan_queries(name, symbol, sector, industry)
    results: list[dict] = []
    for query in queries:
        try:
            results.extend(ollama.web_search(query, max_results=per_query))
        except Exception:
            continue
    grounding.date_results(results)

    outcome = {
        "queries": queries,
        "results": results,
        "results_count": len(results),
        "streams": [],
        "dropped": [],
        "description": None,
        "customer_concentration": None,
        "notes": None,
    }
    if not results:
        outcome["skipped"] = "no search results"
        return outcome

    prompt = STREAM_PROMPT.format(
        symbol=symbol,
        name=name,
        sector=sector or "unknown",
        industry=industry or "unknown",
        summary=(summary or "not supplied")[:2500],
    )
    # The snippets are appended after the instructions so the instruction block
    # stays at the head of the context, where it is least likely to be lost.
    prompt += "\n\nSEARCH RESULTS:\n" + grounding.format_results(results)

    try:
        reply = ollama.chat(
            [{"role": "user", "content": prompt}], model=model or ollama.DEFAULT_MODEL
        )
        data = ollama.parse_json_object(reply["text"])
    except Exception as exc:
        outcome["skipped"] = f"{type(exc).__name__}: {exc}"
        return outcome

    outcome["description"] = (data.get("description") or "").strip() or None
    outcome["split_basis"] = str(data.get("split_basis") or "").strip().lower() or None
    outcome["customer_concentration"] = data.get("customer_concentration")
    outcome["geography"] = data.get("geography")
    outcome["notes"] = data.get("notes")

    kept, dropped = [], []
    for item in (data.get("revenue_streams") or [])[: MAX_STREAMS * 2]:
        if not isinstance(item, dict):
            continue
        stream_name = str(item.get("name") or "").strip()
        if not stream_name:
            continue
        quote = str(item.get("quote") or "").strip()
        hits = grounding.supporting_results(quote, results)
        if hits:
            grounded_by = "search"
            source = hits[0]
        elif grounding.text_in_summary(stream_name, summary) or grounding.text_in_summary(
            f"{stream_name} {item.get('what_it_is') or ''}", summary
        ):
            # Named in the company's own summary: a real source, even with no
            # indexed segment table.
            grounded_by = "business_summary"
            source = {"url": None, "publisher": "yfinance business summary", "source_date": None}
        else:
            dropped.append(
                {
                    "name": stream_name,
                    "quote": quote,
                    "drop_reason": "not in retrieved results and not in the business summary",
                }
            )
            continue

        share = item.get("revenue_share")
        try:
            share = round(float(share), 4) if share is not None else None
        except (TypeError, ValueError):
            share = None
        if share is not None and not (0 < share <= 1):
            share = None
        basis = str(item.get("revenue_share_basis") or "").strip().lower()
        if share is None:
            basis = None
        elif basis not in ("stated", "approximate", "derived"):
            # An unlabelled share is treated as derived: of the two possible
            # errors, printing arithmetic (or a rough reading) as though the
            # company stated it is the one that misleads a reader who checks.
            basis = "derived"

        if share is None:
            # Recover what the evidence line already stated, rather than printing
            # "not disclosed" under a quote that discloses it.
            recovered = share_from_quote(quote, stream_name)
            if recovered:
                share, basis = recovered

        amount = item.get("amount")
        amount_raw = amount if not amount_is_usable(amount) else None
        if amount_raw is not None:
            amount = None

        kept.append(
            {
                "name": stream_name,
                "what_it_is": (item.get("what_it_is") or "").strip(),
                "revenue_share": share,
                "revenue_share_basis": basis,
                "amount": amount,
                "amount_raw": amount_raw,
                "customer": item.get("customer"),
                "quote": quote,
                "url": item.get("url") or source.get("url"),
                "publisher": grounding.publisher(item.get("url")) or source.get("publisher"),
                "as_of": source.get("source_date"),
                "grounded_by": grounded_by,
            }
        )
        if len(kept) >= MAX_STREAMS:
            break

    outcome["streams"] = kept
    outcome["dropped"] = dropped
    return outcome
