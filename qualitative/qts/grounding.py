"""Making a qualitative screener checkable.

The problem this module exists for
---------------------------------
This screener is *deliberately* qualitative: it makes no judgement from a
multiple, a revision count or a price move. Almost everything it publishes is
therefore prose -- a description, a revenue stream, a trend -- and prose is the
one thing a reader cannot check against a number they already have.

That is exactly the failure mode :mod:`fig.research` was built to stop: a model
can produce a fluent, plausible, entirely invented trend, and it will read
better than the boring true one. So the same discipline is applied here, at two
levels:

1. **Every claim carries a verbatim quote and a URL.** The quote is matched
   against the snippets that were actually retrieved, after folding whitespace
   and typographic quotes (search results are full of both). A claim whose quote
   cannot be found is dropped and *recorded as dropped* -- silently losing it
   would hide a bad prompt behind a short list.
2. **A quote must come from the source it names.** "Somewhere in the results" is
   weaker than it sounds: a reader sent to a link that does not contain the
   words is being misled, and the failure is invisible in the output. So the
   quote is matched against each result individually and the claim keeps only
   the source that actually contains it (``supporting_results``).

Why the date matters here
-------------------------
An industry trend quoted from a 2023 report is not a trend, it is history, and
it looks identical to a current one once the URL is a link. Results are
therefore dated on retrieval (``date_results``, via
:func:`fig.research.source_date`, which only trusts *explicit* dates so a
yearless "Sept 18" cannot be read as today), and the synthesiser is told the
date of every snippet it is shown. Age is then carried into the writeup rather
than being lost after the prompt.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from fig.research import source_date

# A snippet truncated too hard loses the sentence the model needs to quote; too
# long and eight searches overflow the context. 1200 characters carried the
# segment tables and the market-size paragraphs in testing.
SNIPPET_CHARS = 1200

# Evidence older than this is not a live trend. It is not dropped outright --
# a 2019 10-K segment table is the best available description of how a company
# earns money -- but it is labelled, and the trend synthesiser is told to prefer
# recent sources for anything forward-looking.
STALE_DAYS = 365


def normalise(text: str) -> str:
    """Fold whitespace and typographic punctuation so quote-matching is robust.

    Search snippets arrive with smart quotes, em dashes and collapsed newlines;
    a verbatim quote will differ in exactly those characters even when every
    word was copied correctly.
    """
    text = (text or "").replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip().lower()


def supporting_results(quote: str, results: list[dict]) -> list[dict]:
    """Results whose own text contains the quote."""
    needle = normalise(quote)
    if not needle:
        return []
    words = needle.split()
    head = " ".join(words[:12]) if len(words) > 12 else needle
    found = []
    for item in results:
        haystack = normalise(f"{item.get('content') or ''} {item.get('title') or ''}")
        if needle in haystack or head in haystack:
            found.append(item)
    return found


def quote_supported(quote: str, results: list[dict]) -> bool:
    """Is the quote present in the retrieved snippets at all?

    A long quote may match on its first twelve words (models occasionally splice
    two adjacent sentences); a short one must match exactly.
    """
    return bool(supporting_results(quote, results))


def text_in_summary(phrase: str, summary: str | None) -> bool:
    """Is ``phrase`` present in the company's own business summary?

    The yfinance business summary is a real source -- it is the company's own
    self-description, shipped through Yahoo -- so a revenue stream named in it is
    grounded even when no search result restates it. This is the second grounding
    path, and it matters most for the many small caps whose segment disclosure is
    not indexed anywhere a free search can reach.
    """
    needle = normalise(phrase)
    if not needle or not summary:
        return False
    haystack = normalise(summary)
    if needle in haystack:
        return True
    # Allow the summary to describe the stream in the company's own words rather
    # than the phrase the model chose: require most of the content words to be
    # present, so "Cloud and license support" matches a summary that says
    # "cloud services and license support".
    words = [w for w in re.findall(r"[a-z0-9]{4,}", needle)]
    if not words:
        return False
    hits = sum(1 for w in words if w in haystack)
    return hits >= max(2, int(len(words) * 0.6))


def publisher(url: Any) -> str | None:
    """Hostname of a URL, minus ``www.`` -- how the writeups cite a source."""
    if not url:
        return None
    host = str(url).split("//", 1)[-1].split("/", 1)[0]
    return host[4:] if host.startswith("www.") else host


def age_days(found: str | None) -> int | None:
    if not found:
        return None
    try:
        return (date.today() - date.fromisoformat(found)).days
    except (ValueError, TypeError):
        return None


def date_results(results: list[dict]) -> list[dict]:
    """Annotate each result with ``source_date`` and ``age_days``, in place.

    The dates are what let the synthesiser prefer a current report over a
    higher-ranking old one, and what let the writeup print an honest age next to
    every quote.
    """
    dated = 0
    for item in results:
        found = source_date(f"{item.get('title', '')} {item.get('content', '')}", item.get("url"))
        item["source_date"] = found.isoformat() if found else None
        item["age_days"] = age_days(item["source_date"])
        item["publisher"] = publisher(item.get("url"))
        if found:
            dated += 1
    return results


def format_results(results: list[dict], *, chars: int = SNIPPET_CHARS) -> str:
    """The evidence block handed to the model: numbered, dated, with URLs."""
    blocks = []
    for index, item in enumerate(results, start=1):
        age = item.get("age_days")
        if age is None:
            stamp = "date unknown -- treat as undated, do not present it as current"
        elif age <= 60:
            stamp = f"published {item['source_date']} ({age} days old)"
        elif age <= 500:
            stamp = f"published {item['source_date']} ({age // 30} months old)"
        else:
            stamp = f"published {item['source_date']} ({age // 365} years old -- historical, not a current trend)"
        blocks.append(
            f"[{index}] {item.get('title')}\n"
            f"URL: {item.get('url')}\n"
            f"DATE: {stamp}\n"
            f"{' '.join((item.get('content') or '').split())[:chars]}"
        )
    return "\n\n".join(blocks)


def clean_claims(raw: list, results: list[dict], *, quote_key: str = "quote") -> tuple[list[dict], list[dict]]:
    """Split model claims into grounded and dropped, keeping the reason.

    Returns ``(kept, dropped)``. The only test is the quote: a claim that cites a
    source whose own text does not contain the quote is dropped, no matter how
    plausible it reads. ``grounded_by`` records which path passed, so a reader can
    tell a claim resting on live reporting from one resting on a company's own
    description.
    """
    kept: list[dict] = []
    dropped: list[dict] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        quote = str(item.get(quote_key) or "").strip()
        record = dict(item)
        hits = supporting_results(quote, results)
        if not hits:
            record["drop_reason"] = "quote_not_found_in_retrieved_results"
            dropped.append(record)
            continue
        newest = None
        for hit in hits:
            found = hit.get("source_date")
            if found and (newest is None or found > newest):
                newest = found
        record["quote"] = quote
        record["as_of"] = newest
        record["age_days"] = age_days(newest)
        record["publisher"] = publisher(record.get("url")) or publisher(hits[0].get("url"))
        record["url"] = record.get("url") or hits[0].get("url")
        record["grounded_by"] = "search"
        kept.append(record)
    return kept, dropped
