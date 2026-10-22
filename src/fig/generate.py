"""Generate a finished idea note: packet -> prompt -> model -> lint -> note.

The division of labour is the whole design
------------------------------------------
**The model writes prose. The tool owns every number.**

That is enforced structurally, not by asking nicely in the prompt. The model
returns only ``description``, ``reasons`` and ``reflection``;
:func:`assemble_writeup` fills the Quants block and the Structuring legs from the
packet, which came from the live sources. A hallucinated price, multiple or
option premium therefore cannot reach the note, and the worst a bad generation
can do is write weak prose -- which the linter then catches.

The repair loop
---------------
The linter is fed back to the model as concrete, numbered complaints ("Reason 2
is 63 words, budget 40"), and the model revises. This works far better than
asking for brevity up front, because the model gets a measurable target instead
of an adjective. Each round is recorded so the run can be audited.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from . import (
    catalyst as catalyst_mod,
    ranking as ranking_mod,
    discover,
    lint,
    options,
    packet as packet_mod,
    prompts,
    quants,
    render,
    research as research_mod,
)
from .sources import ollama, yahoo
from .util import human_money

# Only these keys are taken from the model.
MODEL_OWNED = ("description", "reasons", "reflection")

# A URL inside reason prose. The link belongs in reason_sources, where it is
# resolved against the packet; a URL in the prose is either wasted words or an
# invention, and the tool prints neither.
_URL_RE = re.compile(r"https?://\S+")

# Public fields of a catalogue entry that a note keeps. ``text`` is the exact
# evidence a cited figure should be findable in, which is what makes the
# source-level grounding check possible -- it is kept on the packet, not in the
# note, because the note should stay readable.
# `ref` is included so a note stays readable against *its own* register: ids are
# assigned in register order, so adding evidence renumbers them, and without the ref
# a stored citation would silently point at a different source after a rebuild.
SOURCE_FIELDS = ("id", "kind", "ref", "label", "provider", "url", "date")


def public_sources(catalogue: list[dict]) -> list[dict]:
    """The catalogue as it is stored in a note: no internal evidence text."""
    return [{k: e.get(k) for k in SOURCE_FIELDS} for e in catalogue or []]


def _normalise_source_ids(raw: Any) -> list[list[str]]:
    """Read the model's citations whatever shape it returned them in.

    Models return a list of lists, a list of dicts, a dict keyed by reason number,
    or a single flat list. All four mean the same thing, and rejecting three of
    them would cost a repair round for no gain.
    """
    if not raw:
        return []
    if isinstance(raw, dict):
        # {"1": ["S3"], "2": ["S1"]} or {"reason_1": "S3"}
        pairs = sorted(
            raw.items(),
            key=lambda kv: int(re.search(r"\d+", str(kv[0])).group())
            if re.search(r"\d+", str(kv[0]))
            else 0,
        )
        return [_ids_from(value) for _, value in pairs]
    if isinstance(raw, list):
        out: list[list[str]] = []
        for item in raw:
            if isinstance(item, dict):
                merged: list[str] = []
                for key in ("ids", "sources", "source", "id", "source_id", "refs"):
                    if key in item:
                        merged.extend(_ids_from(item[key]))
                out.append(merged)
            else:
                out.append(_ids_from(item))
        return out
    return []


def _ids_from(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        out: list[str] = []
        for item in value:
            out.extend(_ids_from(item))
        return out
    text = str(value).strip()
    if not text:
        return []
    # Accept "S3", "[S3]", "S3, S7", "s3; source S7".
    found = re.findall(r"\bS\s?(\d{1,3})\b", text, re.IGNORECASE)
    if found:
        return [f"S{int(n)}" for n in found]
    return []


def resolve_reason_sources(
    model_output: dict, catalogue: list[dict], reason_count: int
) -> tuple[list[list[dict]], list[str]]:
    """Map the model's cited ids onto real catalogue entries.

    Returns ``(resolved, unknown)`` where ``resolved`` is aligned with the reasons.
    An id that is not in the catalogue is **dropped, never printed**: the note's
    promise is that a reader can open every source it names, and a fabricated id
    would break exactly that.
    """
    by_id = {e["id"].upper(): e for e in catalogue or []}
    raw = _normalise_source_ids(
        model_output.get("reason_sources")
        or model_output.get("sources")
        or model_output.get("reason_source_ids")
    )
    resolved: list[list[dict]] = []
    unknown: list[str] = []
    for index in range(reason_count):
        ids = raw[index] if index < len(raw) else []
        entries: list[dict] = []
        seen: set[str] = set()
        for source_id in ids:
            key = source_id.upper()
            if key in seen:
                continue
            seen.add(key)
            entry = by_id.get(key)
            if entry is None:
                if source_id not in unknown:
                    unknown.append(source_id)
                continue
            entries.append({k: entry.get(k) for k in SOURCE_FIELDS})
        resolved.append(entries)
    return resolved, unknown


def _redact_urls(text: str, catalogue: list[dict]) -> tuple[str, list[str]]:
    """Remove URLs from reason prose that the packet cannot vouch for.

    The model is told not to write links into a reason, and mostly it complies.
    When it does not, the link is resolved against the packet: a real one is kept
    (it is redundant but harmless) and an invented one is removed and recorded.
    Printing a fabricated URL under a real-looking claim is the one failure a
    reader cannot detect, so it cannot be left to the prompt alone.
    """
    known = {str(e.get("url")) for e in catalogue or [] if e.get("url")}
    redacted: list[str] = []

    def replace(match: re.Match[str]) -> str:
        url = match.group(0).rstrip(".,);")
        if url in known:
            return ""
        redacted.append(url)
        return ""

    cleaned = re.sub(r"\s{2,}", " ", _URL_RE.sub(replace, text)).strip()
    return cleaned, redacted


# --------------------------------------------------------------------------
# assembling the note
# --------------------------------------------------------------------------



# Words too common to signal that a reason is actually about the end market.
_TREND_STOPWORDS = {
    "their", "there", "these", "those", "which", "while", "about", "would", "could",
    "should", "being", "other", "after", "before", "still", "under", "across",
    "increasing", "increased", "growing", "growth", "demand", "rising", "higher",
    "lower", "small", "business", "businesses", "company", "companies", "market",
    "markets", "sector", "industry", "spending", "customers", "clients", "plans",
    "expected", "likely", "continue", "continues", "adding", "using", "more",
    # generic financial vocabulary -- present in almost any reason, so it cannot
    # signal that a reason is actually about the end market
    "revenue", "revenues", "earnings", "income", "profit", "profits", "margin",
    "margins", "cost", "costs", "sales", "value", "shares", "stock", "price",
    "multiple", "quarter", "quarters", "year", "years", "annual", "results",
    "performance", "operating", "expense", "expenses", "cash", "flow", "numbers",
    "figures", "reported", "reporting", "reports", "pressures", "pressure",
    "complexity", "compliance",
}


def _trend_keywords(trends: list[dict]) -> set[str]:
    """Significant words from the trend claims, for checking they were used."""
    words: set[str] = set()
    for trend in trends or []:
        text = f"{trend.get('claim','')} {trend.get('why','')}".lower()
        for word in re.findall(r"[a-z][a-z\-]{4,}", text):
            word = word.strip("-")
            if word and word not in _TREND_STOPWORDS:
                words.add(word)
    return words


def end_market_coverage(writeup: dict, trends: list[dict]) -> dict:
    """Did any reason actually use the end-market research it was given?

    Supplying end-market evidence is not the same as using it. A note can be handed
    five grounded trends and still write three reasons about trailing quarters --
    which is precisely what happened to the PAYX note the repo owner objected to:
    the words "hiring" and "employment" appeared nowhere in it, so nothing explained
    why weakness in its end markets had not reached its reported numbers.
    """
    if not trends:
        return {"available": 0, "used": [], "ok": True}

    # Words already in the company's own Description describe the company, not its
    # end market, so they cannot count as evidence about customers.
    own_business = set(
        re.findall(r"[a-z][a-z\-]{4,}", (writeup.get("description") or "").lower())
    )
    keywords = _trend_keywords(trends) - {w.strip("-") for w in own_business}
    prose = " ".join(
        [writeup.get("description") or "", *[str(r) for r in (writeup.get("reasons") or [])]]
    ).lower()
    prose = prose.replace("-", " ")

    hits = sorted(word for word in keywords if word in prose)
    return {"available": len(trends), "used": hits, "ok": bool(hits)}


def _extra_quants_lines(packet: dict, limit: int = 4) -> list[str]:
    """Terse factual lines the Quants block adds under the standard fields.

    This is what produces lines like the OMF reference's "Q2 reported increasing
    provisions". Each is mechanically derived from the statements or reported
    EPS, so it cannot be invented.

    Ordering is by importance, and ``limit`` is generous enough that the revision
    disagreement flag survives: it was previously appended last and then
    truncated away, losing the single most useful line to the least important one.
    """
    delta_lines: list[str] = []
    warning: str | None = None
    yoy_line: str | None = None

    deltas = packet.get("fundamental_deltas") or []
    conflicts = [row for row in (packet.get("yoy_deltas") or []) if row.get("conflict")]
    conflict_labels = {
        quants.canonical_label(row["label"]) for row in conflicts
    } | {row["label"] for row in conflicts}
    # Prefer credit-related moves: they are usually the thesis.
    ranked = sorted(deltas, key=lambda d: (not d.get("is_credit"), -abs(d["change_pct"])))
    for delta in ranked:
        # Suppressed where the sequential move disagrees with the year-earlier quarter:
        # the paired line below carries both halves, and this one on its own is the
        # true-but-misleading half ("net income decreasing 25% quarter over quarter"
        # about a quarter whose net income rose 41% year over year).
        if quants.canonical_label(delta["label"]) in conflict_labels:
            continue
        delta_lines.append(
            f"Last quarter {delta['label'].lower()} {delta['direction']} "
            f"{abs(delta['change_pct']):.0f}% quarter over quarter ({delta['period']})"
        )
        if len(delta_lines) >= 2:
            break

    # The pair is the fact, so it is one line: sequential first, annual second.
    for row in conflicts[:1]:
        delta_lines.insert(
            0,
            f"{row['label']} {row['qoq_pct']:+.0f}% quarter over quarter but "
            f"{row['yoy_pct']:+.0f}% year over year ({row['period']})",
        )

    yoy = packet.get("eps_yoy")
    if yoy and yoy.get("direction"):
        yoy_line = f"EPS {yoy['direction']} year over year, {yoy['year_ago']} -> {yoy['current']}"

    # A 7-day window that disagrees with the 30-day window is worth flagging: it
    # is the difference between a clean trend and a turning one.
    revisions = (packet.get("quants") or {}).get("eps_revisions") or {}
    up7, down7 = revisions.get("up_7d"), revisions.get("down_7d")
    up30, down30 = revisions.get("up_30d"), revisions.get("down_30d")
    if None not in (up7, down7, up30, down30):
        if ((up30 - down30) > 0) != ((up7 - down7) > 0) and (up7 - down7) != 0:
            warning = (
                f"Warning: revisions disagree by window, {up7:g} up / {down7:g} down over 7 days"
            )

    composed = delta_lines + ([warning] if warning else []) + ([yoy_line] if yoy_line else [])
    return composed[:limit]


def quants_block(packet: dict) -> dict:
    """Build the Quants block purely from packet data."""
    panel = packet.get("quants") or {}
    ps = panel.get("ps")
    return {
        "price": panel.get("price"),
        "market_cap": panel.get("market_cap_human"),
        "fwd_pe": round(panel["fwd_pe"], 1) if panel.get("fwd_pe") else None,
        "fwd_pe_basis": "current FY consensus",
        "ps": round(ps, 1) if ps else None,
        "eps_trend": (panel.get("eps_trend") or {}).get("text"),
        "eps_revisions": (panel.get("eps_revisions") or {}).get("text"),
        "extra": _extra_quants_lines(packet),
    }


def assemble_writeup(packet: dict, model_output: dict, direction: str) -> dict:
    """Combine model prose with tool-owned numbers.

    Raises ``ValueError`` when the model omitted a required field, rather than
    quietly emitting a note with an empty Description.

    Structuring is **optional**. The catalyst carries the idea; the legs are a
    construction detail on top of it. When no usable chain exists the note is
    still produced, without the section, and ``structure_error`` records why so
    the omission is visible rather than silent.
    """
    direction = direction.lower()
    structures = packet.get("structures") or {}
    structure = structures.get(direction)

    description = (model_output.get("description") or "").strip()
    catalogue = packet.get("sources") or packet_mod.source_catalogue(packet)

    reasons: list[str] = []
    redacted: list[str] = []
    for raw_reason in model_output.get("reasons") or []:
        text, removed = _redact_urls(str(raw_reason).strip(), catalogue)
        redacted.extend(removed)
        if text:
            reasons.append(text)

    watch: list[str] = []
    for raw_line in model_output.get("watch") or []:
        text, removed = _redact_urls(str(raw_line).strip(), catalogue)
        redacted.extend(removed)
        if text:
            watch.append(text)

    reflection = (model_output.get("reflection") or "").strip()

    # Accept the reflection nested under "structuring" too, since models vary.
    if not reflection and isinstance(model_output.get("structuring"), dict):
        reflection = (model_output["structuring"].get("reflection") or "").strip()

    missing = [name for name, value in (("description", description), ("reasons", reasons)) if not value]
    if missing:
        raise ValueError(f"model output missing: {', '.join(missing)}")

    catalyst = packet.get("catalyst") or {}
    why = (model_output.get("catalyst_why") or "").strip()
    if not why:
        # A note must never assert a catalyst without justifying it, so fall back
        # to the measured justification rather than leaving the block bare. The
        # fallback returns ONE sentence that fits the word budget: joining every
        # fact produced a 51-word line the linter rejects as an error, which no
        # repair round could clear.
        why = catalyst_mod.fallback_why(catalyst)

    # Sources are resolved against the catalogue the writer was shown. The model
    # chose which evidence supports which reason; the tool owns the id, the
    # provider, the date and the URL, so nothing in the printed citation depends
    # on the model's memory of a link.
    reason_sources, unknown_sources = resolve_reason_sources(model_output, catalogue, len(reasons))

    writeup = {
        "ticker": packet["symbol"],
        "direction": direction,
        "as_of": packet.get("as_of"),
        "description": description,
        "catalyst": {
            "date": catalyst.get("date"),
            "weekday": catalyst.get("weekday"),
            "session": catalyst.get("session"),
            "days_out": catalyst.get("days_out"),
            "basis": catalyst.get("basis"),
            "consensus": catalyst.get("consensus") or {},
            "recent_reports": catalyst.get("recent_reports") or [],
            "beat_streak": catalyst.get("beat_streak"),
            "median_gap_days": catalyst.get("median_gap_days"),
            "facts_line": catalyst.get("facts_line"),
            "why": why,
        },
        "reasons": reasons,
        "watch": watch,
        "reason_sources": reason_sources,
        "sources_catalogue": public_sources(catalogue),
        "quants": quants_block(packet),
        # The shape of the evidence, carried on the writeup so the lint pass can check
        # the comparisons the writer was given rather than re-fetching anything: which
        # lines moved in opposite directions sequentially and annually, whether a deal
        # landed in the period, and how far out the print is.
        "evidence_hints": {
            "yoy": [
                {
                    "label": row.get("label"),
                    "qoq_pct": row.get("qoq_pct"),
                    "yoy_pct": row.get("yoy_pct"),
                    "conflict": bool(row.get("conflict")),
                    "period": row.get("period"),
                }
                for row in (packet.get("yoy_deltas") or [])
            ],
            "annual": [
                {"label": row.get("label"), "change_pct": row.get("change_pct"),
                 "period": row.get("period")}
                for row in (packet.get("annual_deltas") or [])
            ],
            "deal": packet.get("deal_activity") or [],
            "catalyst_days": (packet.get("catalyst") or {}).get("days_out"),
            "bar": packet.get("consensus_bar") or {},
        },
    }

    if unknown_sources:
        # Recorded rather than printed: a reader must never be shown a source the
        # packet cannot vouch for. The lint pass turns this into a repair
        # instruction, because a dropped citation is usually the only one given.
        writeup["sources_unverified"] = unknown_sources
    if redacted:
        writeup["urls_redacted"] = redacted

    if structure and "error" not in structure and (structure.get("rows") or []):
        writeup["structuring"] = {
            "rows": structure.get("rows") or [],
            "thesis_target": _catalyst_sentence(packet, structure, direction),
            "reflection": reflection,
        }
    else:
        reason = (
            structure.get("error")
            if structure and "error" in structure
            else "no structure was requested"
        )
        writeup["structure_error"] = reason

    if packet.get("peers"):
        writeup["peers"] = packet["peers"]

    # Feeds that were down when the packet was built. Carried into the writeup so the
    # rendered note can state it: a note whose evidence came from one feed instead of
    # three is still worth publishing, but not worth publishing as though nothing was
    # missing.
    if packet.get("news_failures"):
        writeup["news_failures"] = packet["news_failures"]
    return writeup


def _catalyst_sentence(packet: dict, structure: dict, direction: str) -> str:
    """One line naming the catalyst the trade targets, from the structure."""
    catalyst = structure.get("catalyst")
    if not catalyst:
        return ""
    long_expiry = (structure.get("long_leg") or {}).get("expiry")
    verb = "gives the thesis" if direction == "long" else "gives the deterioration"
    return f"Targets the {catalyst} report, with the long leg expiring {long_expiry}, which {verb} time to show up."


# --------------------------------------------------------------------------
# generation
# --------------------------------------------------------------------------


def _messages_for(packet: dict, direction: str) -> list[dict]:
    context = packet_mod.to_prompt_context(packet)
    return [
        {"role": "system", "content": prompts.SYSTEM_PROMPT},
        {"role": "user", "content": prompts.build_user_prompt(context, direction_hint=direction)},
    ]


def _repair_messages(
    original: list[dict], model_output: dict, issues: list[str]
) -> list[dict]:
    """Ask for a revision, quoting the linter's complaints verbatim."""
    bullets = "\n".join(f"- {issue}" for issue in issues)
    return [
        *original,
        {"role": "assistant", "content": json.dumps(model_output)},
        {
            "role": "user",
            "content": (
                "A checker rejected the note for the reasons below. Fix every one of "
                "them.\n\n"
                "Most complaints are about style: for those, keep the same claims and "
                "make them shorter and plainer. Some are about the SHAPE of the "
                "argument -- a sequential move quoted without the year-over-year move, "
                "growth claimed in a period an acquisition landed in, a chain longer "
                "than the report can settle, a missing Watch block. Those need a "
                "different sentence, and for them you may use any figure already in the "
                "EVIDENCE above: the comparison the checker wants is in the packet even "
                "where your note left it out. Do not invent a fact that is not there.\n\n"
                "Where a reason is missing a source, cite the ids from the SOURCES list "
                "that support that specific reason; where a figure was rejected, cite "
                "the source that actually contains it.\n\n"
                f"{bullets}\n\n"
                "Return the corrected JSON only, in exactly the same shape: "
                '{"description": str, "catalyst_why": str (<=25 words, what the '
                'report must prove), "reasons": [str], "watch": [str], '
                '"reason_sources": [[str]], "reflection": str}. '
                "Keep catalyst_why: a revision that drops it silently erases the "
                "justification the note is required to carry."
            ),
        },
    ]


JSON_NUDGE = (
    "Return the JSON object only. No prose, no explanation, no markdown fences."
)


def _chat_json(symbol: str, messages: list[dict], *, model: str, say, attempts: int = 3) -> tuple[dict, dict]:
    """One completion that must yield a JSON object, retrying if it does not.

    JSON mode makes this rare but not impossible: a run failed on PAYX with "model
    did not return a JSON object" (an empty or non-conforming reply). That is a
    transient upstream wobble, not a reason to lose the ticker from a batch, so it
    is retried with an explicit nudge before the symbol is given up on.
    """
    last_error: Exception | None = None
    for attempt in range(attempts):
        payload = messages if attempt == 0 else [*messages, {"role": "user", "content": JSON_NUDGE}]
        reply = ollama.chat(payload, model=model)
        try:
            return ollama.parse_json_object(reply["text"]), reply
        except RuntimeError as exc:
            last_error = exc
            if attempt < attempts - 1:
                say(f"[{symbol}] unparseable JSON, retrying ({attempt + 2}/{attempts})")
    raise RuntimeError(f"model did not return parseable JSON after {attempts} attempts") from last_error


class PriceCapError(ValueError):
    """Raised when a ticker trades at or above the share-price cap."""


def generate_idea(
    symbol: str,
    *,
    direction: str = "long",
    peers: list[str] | None = None,
    model: str | None = None,
    use_search: bool = True,
    catalyst_index: int = 0,
    credit_target: float = options.DEFAULT_CREDIT_TARGET,
    repairs: int = 2,
    structure_legs: bool = True,
    samples: int = 1,
    max_price: float | None = discover.DEFAULT_MAX_PRICE,
    verbose: bool = True,
) -> dict:
    """Generate one note. Returns ``{writeup, packet, lint, attempts, model}``.

    Never raises on a lint failure: a note that still has errors is returned with
    its lint result so a batch run can report and continue.
    """
    model = model or ollama.DEFAULT_MODEL

    def say(message: str) -> None:
        if verbose:
            print(message, flush=True)

    # The price cap is checked before any work is done, so a batch rejects an
    # over-cap ticker immediately instead of after a minute of research.
    if max_price is not None:
        try:
            price = yahoo.valuation(symbol).get("price")
        except Exception:
            price = None
        if price is not None and price >= max_price:
            raise PriceCapError(
                f"{symbol} trades at ${price:,.2f}, at or above the ${max_price:,.0f} "
                f"share-price cap. Raise it with --max-price to research this name."
            )

    say(f"[{symbol}] building evidence packet (search={use_search and ollama.has_key()})")
    pack = packet_mod.build_packet(
        symbol, peers=peers, include_web=use_search, catalyst_index=catalyst_index
    )

    # Rebuild the target structure at the requested credit target, since
    # build_packet uses its own default.
    # Structuring is optional: if no usable chain exists the note is still worth
    # writing, because the catalyst and the reasons carry the idea. The failure is
    # recorded so the omission is visible.
    if not structure_legs:
        # Structuring is a second-order detail on top of the idea, and the chain
        # fetch is the slowest part of packet building. The omission is recorded
        # through the same path a failed chain takes, so the note says so in
        # render rather than looking like a chain that happened to be missing.
        say(f"[{symbol}] structuring skipped (--no-legs) -- writing the note without legs")
        pack.setdefault("structures", {})[direction] = {
            "error": "structuring skipped (--no-legs)"
        }
    else:
        try:
            structure = options.build_structure(
                symbol, direction, catalyst_index=catalyst_index, credit_target=credit_target
            )
            pack.setdefault("structures", {})[direction] = {
                **structure.as_dict(),
                "advice": options.suggest_short_adjustment(structure),
                "credit_ladder": options.credit_ladder(structure),
            }
        except Exception as exc:
            say(f"[{symbol}] no {direction} structure ({type(exc).__name__}: {exc}) -- writing the note without legs")
            pack.setdefault("structures", {})[direction] = {
                "error": f"{type(exc).__name__}: {exc}"
            }

    samples = max(1, int(samples))

    # Each sample is a full independent run: its own trend research, so the
    # qualitative evidence differs, and its own writing. The verdict is then
    # assessed across samples rather than asserted once -- which is the honest
    # treatment of evidence that is genuinely run-dependent.
    per_sample: list[dict] = []
    best: dict | None = None
    # Trends are kept per sample as well as in the packet: only one sample's set can
    # survive into the saved packet, and the notes of the other samples quote the
    # others. Without this, a saved note can cite evidence that no longer exists
    # anywhere -- which is what happened to BB's second reason.
    sample_trends: list[dict] = []

    for sample_index in range(samples):
        if samples > 1:
            say(f"[{symbol}] sample {sample_index + 1}/{samples}")

        # Sample 0 reuses the packet's research; later samples re-run it. Without
        # this, sampling would vary only the writing while the evidence stayed
        # fixed, and the verdict could never disagree with itself -- which is the
        # whole reason for sampling qualitative evidence.
        if sample_index > 0 and use_search and ollama.has_key():
            fresh = research_mod.forward_trends(
                symbol,
                ((pack.get("profile") or {}).get("name")),
                None,
                ((pack.get("profile") or {}).get("summary")),
            )
            if fresh.get("trends"):
                pack["forward_trends"] = fresh
            else:
                say(f"[{symbol}] sample {sample_index + 1}: no fresh trends found, reusing the first set")

        # The source register numbers the evidence, so it is rebuilt whenever that
        # evidence changes. Leaving the first sample's register in place while the
        # trends behind it were replaced would resolve a citation to a *different*
        # trend's URL -- a wrong source that reads exactly like a right one, which is
        # the failure this mechanism exists to prevent.
        pack["sources"] = packet_mod.source_catalogue(pack)
        sample_trends.append(pack["forward_trends"])

        trends = (pack.get("forward_trends") or {}).get("trends") or []
        verdict = research_mod.evidence_verdict(trends, direction)

        messages = _messages_for(pack, direction)
        attempts: list[dict] = []
        model_output: dict = {}
        writeup: dict = {}
        result: dict = {}
        last_why: str = ""

        for round_index in range(repairs + 1):
            model_output, reply = _chat_json(symbol, messages, model=model, say=say)

            if (model_output.get("catalyst_why") or "").strip():
                last_why = model_output["catalyst_why"].strip()
            elif round_index and last_why:
                # A revision can still drop catalyst_why even though the required
                # shape asks for it. Carrying the earlier line forward is better
                # than replacing a written justification with the measured fallback.
                model_output["catalyst_why"] = last_why

            writeup = assemble_writeup(pack, model_output, direction)
            result = lint.lint_writeup(writeup)
            grounding = lint.check_grounding(writeup, packet_mod.to_prompt_context(pack))
            result["grounding"] = grounding

            # Weaker than it sounds on its own: a figure can be in the packet and
            # still be absent from the source this reason sends the reader to.
            source_grounding = lint.check_source_grounding(writeup, pack.get("sources") or [])
            result["source_grounding"] = source_grounding
            if source_grounding["mismatches"]:
                result["issues"] = result["issues"] + [
                    f"[warn ] Reason prose: figure(s) not in the cited source "
                    f"({'; '.join(source_grounding['mismatches'][:3])}) (source_grounding)"
                ]
                result["warnings"] += 1

            coverage = end_market_coverage(writeup, trends)
            result["end_market"] = coverage
            if not coverage["ok"]:
                # An error, not a warning: the writer was handed end-market evidence
                # and wrote about trailing quarters instead, which is the gap this
                # feature exists to close. The repair loop then has to use it.
                result["errors"] += 1
                result["issues"] = result["issues"] + [
                    f"[error] no reason uses the end-market research supplied "
                    f"({coverage['available']} trends): say what is happening to the "
                    f"customers, or why the pressure has not shown up yet (end_market_unused)"
                ]
            if grounding["unsupported"]:
                result["issues"] = result["issues"] + [
                    f"[warn ] Reason prose: unsupported figure(s) {', '.join(grounding['unsupported'])} "
                    f"not found in the evidence (grounding)"
                ]
                result["warnings"] += 1

            attempts.append(
                {
                    "round": round_index,
                    "elapsed": reply["elapsed"],
                    "usage": reply.get("usage"),
                    "errors": result["errors"],
                    "warnings": result["warnings"],
                    "score": result["score"],
                    "issues": result["issues"],
                    "unsupported_figures": grounding["unsupported"],
                }
            )
            say(
                f"[{symbol}] round {round_index}: score {result['score']} "
                f"({result['errors']} errors, {result['warnings']} warnings) in {reply['elapsed']}s"
                + (
                    f" -- unsupported figures: {', '.join(grounding['unsupported'])}"
                    if grounding["unsupported"]
                    else f" -- {grounding['checked']} figures all grounded"
                )
            )

            if result["ok"]:
                break
            if round_index < repairs:
                say(f"[{symbol}] repairing {result['errors']} error(s)")
                messages = _repair_messages(messages, model_output, result["issues"])

        sample = {
            "sample": sample_index,
            "rounds": attempts,
            "score": result["score"],
            "errors": result["errors"],
            "warnings": result["warnings"],
            "ok": result["ok"],
            "verdict": verdict["verdict"],
            "supportive": verdict["supportive"],
            "adverse": verdict["adverse"],
            "trends_available": len(trends),
            "trends_used": (result.get("end_market") or {}).get("used") or [],
            # Which register this sample's citations were resolved against. Small,
            # and the only record of how a citation was interpreted if a sample's
            # evidence is ever questioned.
            "source_ids": [e["id"] for e in (pack.get("sources") or [])],
            "writeup": writeup,
        }
        per_sample.append(sample)

        # Best = zero errors first, then score. A sample that failed lint should
        # never be the one that gets saved.
        if best is None or (
            (sample["ok"], sample["score"]) > (best["ok"], best["score"])
        ):
            best = sample

    assert best is not None

    # The packet saved beside the note must be the packet the note was written
    # from. Sampling replaces the trends in place, so without this the saved
    # evidence is whichever sample ran last while the note may be an earlier one --
    # which silently detaches the note from its own evidence, and (before the
    # register was rebuilt per sample) could point a citation at the wrong source.
    pack["forward_trends"] = sample_trends[best["sample"]]
    pack["sources"] = packet_mod.source_catalogue(pack)
    pack["trailing_vs_consensus"] = packet_mod.trailing_vs_consensus(pack)
    if len(sample_trends) > 1:
        # All samples' research is kept, because the sampling is a real part of how
        # the note was judged and the sets genuinely differ.
        pack["forward_trends_samples"] = sample_trends

    # The saved note is the best sample; its lint/grounding detail is re-derived
    # from the note itself so what is stored is what the note actually scores now.
    writeup = best["writeup"]
    trends = (pack.get("forward_trends") or {}).get("trends") or []
    result = lint.lint_writeup(writeup)
    result["grounding"] = lint.check_grounding(writeup, packet_mod.to_prompt_context(pack))
    result["source_grounding"] = lint.check_source_grounding(writeup, pack.get("sources") or [])
    result["end_market"] = end_market_coverage(writeup, trends)

    verdicts = [s["verdict"] for s in per_sample]
    tally = {
        "samples": samples,
        "verdicts": verdicts,
        "confirmed": verdicts.count("confirms"),
        "contradicted": verdicts.count("contradicts"),
        "mixed": verdicts.count("mixed") + verdicts.count("no-evidence"),
        "majority": max(set(verdicts), key=verdicts.count) if verdicts else "no-evidence",
        "agreement": round(verdicts.count(max(set(verdicts), key=verdicts.count)) / len(verdicts), 2)
        if verdicts
        else 0.0,
    }
    if samples > 1:
        say(
            f"[{symbol}] verdict across {samples} samples: {tally['majority']} "
            f"({tally['confirmed']} confirms, {tally['contradicted']} contradicts, "
            f"{tally['mixed']} mixed)"
        )

    return {
        "writeup": writeup,
        "packet": pack,
        "lint": result,
        "attempts": [round_ for sample in per_sample for round_ in sample["rounds"]],
        "samples": per_sample,
        "verdict": tally,
        "model": model,
        "search_used": bool(use_search and ollama.has_key()),
    }


# --------------------------------------------------------------------------
# saving
# --------------------------------------------------------------------------


def side_folder(direction: str | None) -> str:
    """The folder a note belongs in, by side.

    Longs and shorts are different trades with different failure modes -- a long
    breaks when the thesis is late, a short breaks when it is early and the borrow
    is expensive -- so reading them in one flat list mixes two kinds of risk. The
    folder is derived from the note's own direction, so a note cannot end up filed
    against the side it argues.
    """
    return "shorts" if (direction or "").lower().startswith("short") else "longs"


def save_idea(result: dict, out_dir: str | Path = "research") -> dict:
    """Write the note, its JSON and the raw packet into the side's folder.

    The packet is kept because it is the audit trail: every number in the note can
    be traced back to the evidence that produced it, and now every *source* cited
    in a reason can be traced to the same place.
    """
    out = Path(out_dir)
    writeup = result["writeup"]
    symbol = writeup["ticker"]
    folder = side_folder(writeup.get("direction"))
    out = out / folder
    out.mkdir(parents=True, exist_ok=True)
    result["folder"] = folder

    idea_path = out / f"{symbol}.json"

    # Store how the note was made alongside it, so the index can be rebuilt from
    # the files alone (see fig index) without regenerating anything.
    persisted = {
        **writeup,
        "generation": {
            "model": result.get("model"),
            "search_used": result.get("search_used"),
            "rounds": [
                {
                    "round": a["round"],
                    "score": a["score"],
                    "errors": a["errors"],
                    "warnings": a["warnings"],
                    "unsupported_figures": a.get("unsupported_figures", []),
                }
                for a in (result.get("attempts") or [])
            ],
            "grounding": (result.get("lint") or {}).get("grounding"),
            "source_grounding": (result.get("lint") or {}).get("source_grounding"),
            # The sampled verdict is persisted because it is the only input to the
            # ranking that comes from a view on the company rather than on the note.
            "verdict": result.get("verdict"),
            "samples": [
                {
                    "sample": sample["sample"],
                    "score": sample["score"],
                    "verdict": sample["verdict"],
                    "supportive": sample["supportive"],
                    "adverse": sample["adverse"],
                    "trends_available": sample["trends_available"],
                    "trends_used": sample["trends_used"],
                }
                for sample in (result.get("samples") or [])
            ],
        },
    }
    idea_path.write_text(json.dumps(persisted, indent=2) + "\n")

    note = render.render_writeup(
        writeup,
        include_lint=True,
        grounding=(result.get("lint") or {}).get("grounding"),
        source_grounding=(result.get("lint") or {}).get("source_grounding"),
    )
    header = (
        f"<!-- generated by `fig generate {symbol}` on {writeup.get('as_of')} "
        f"with {result.get('model')}. Edit {idea_path.name}, then re-run `fig render`. -->\n\n"
    )
    note_path = out / f"{symbol}.md"
    note_path.write_text(header + note)

    packet_path = out / f"{symbol}.packet.json"
    packet_path.write_text(json.dumps(result["packet"], indent=2, default=str) + "\n")

    return {
        "idea": str(idea_path),
        "note": str(note_path),
        "packet": str(packet_path),
        "folder": folder,
        "score": result["lint"]["score"],
        "ok": result["lint"]["ok"],
    }


def note_paths(out_dir: str | Path = "research") -> list[Path]:
    """Every note JSON under ``out_dir``, in side folders or the flat legacy layout.

    Both are read, because the folders were introduced after the first batches were
    written: a rebase of the layout must not lose the notes that predate it. Files
    that are not notes are skipped by name rather than by guessing at their shape --
    ``excluded.json`` is a list and lives in the same folder.
    """
    out = Path(out_dir)
    skip = {"excluded.json"}
    found: list[Path] = []

    def collect(folder: Path) -> None:
        for path in sorted(folder.glob("*.json")):
            if path.name.endswith(".packet.json") or path.name in skip:
                continue
            found.append(path)

    collect(out)
    for side in (out / "longs", out / "shorts"):
        if side.is_dir():
            collect(side)
    return found


def load_note(path: Path) -> dict | None:
    """A note file as a dict, or ``None`` if it is not a note."""
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) and data.get("ticker") else None


def organize(out_dir: str | Path = "research", *, dry_run: bool = False) -> dict:
    """Move flat notes into their side's folder, and say what moved.

    A note carries its own direction, so the destination is read from the file
    rather than guessed from its contents or its name. Notes already in a side
    folder are moved only if the folder disagrees with the direction inside them --
    a misfiled note is worse than a flat one.
    """
    out = Path(out_dir)
    moved: list[tuple[str, str]] = []
    unchanged = 0

    for path in note_paths(out):
        data = load_note(path)
        if data is None:
            continue
        ticker = data["ticker"]

        # The packet moves with its note: a note without its evidence is not
        # auditable, which is the whole reason the packet is written.
        stem = path.name[: -len(".json")]
        is_packet = stem.endswith(".packet")
        if is_packet:
            continue
        # The note's siblings travel with it: the packet, because a note without
        # its evidence is not auditable, and the rendered markdown, because an
        # orphaned .md at the old path is worse than no file at all -- it is the
        # stale version of a note that has moved.
        siblings = [path]
        packet = path.with_name(f"{ticker}.packet.json")
        if packet.is_file():
            siblings.append(packet)
        rendered = path.with_suffix(".md")
        if rendered.is_file():
            siblings.append(rendered)

        target_dir = out / side_folder(data.get("direction"))
        if path.parent == target_dir:
            unchanged += 1
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        if dry_run:
            moved.append((str(path), str(target_dir / path.name)))
            continue
        for source in siblings:
            destination = target_dir / source.name
            if destination.exists():
                destination.unlink()
            source.rename(destination)
        moved.append((str(path), str(target_dir / path.name)))

    return {"moved": moved, "unchanged": unchanged, "dry_run": dry_run}


def register_for(data: dict, packet: dict) -> list[dict]:
    """The register a note's ids were assigned against, with text from the packet.

    A note stores the register it cited. That register is not the one a newer build
    would produce -- ids are positional, and a packet with more headlines numbers its
    sources differently -- so checking stored citations against a rebuilt register
    would resolve every one of them to the wrong source and report misfires that are
    artefacts of the rebuild. Entries are matched by ``ref``, which is stable against
    the packet, and by url and label for registers written before ref was stored.
    """
    stored = data.get("sources_catalogue") or []
    rebuilt = packet.get("sources") or packet_mod.source_catalogue(packet)
    if not stored:
        return rebuilt
    by_ref = {e.get("ref"): e for e in rebuilt if e.get("ref")}
    by_url = {e.get("url"): e for e in rebuilt if e.get("url")}
    by_label = {e.get("label"): e for e in rebuilt if e.get("label")}
    merged: list[dict] = []
    for entry in stored:
        # Label before url: two end-market trends can share a publisher url, and the
        # label carries the claim, which is what tells them apart.
        source = (
            by_ref.get(entry.get("ref"))
            or by_label.get(entry.get("label"))
            or by_url.get(entry.get("url"))
            or {}
        )
        merged.append({**entry, "text": source.get("text") or ""})
    return merged


def rebuild_index(
    out_dir: str | Path = "research",
    *,
    scoring: str | None = None,
    disagreements: list[dict] | None = None,
) -> dict:
    """Rebuild the index from the notes on disk.

    Everything needed is inside each ``.json``: the writeup itself plus the
    ``generation`` block recording model, rounds and scores. Notes are re-linted
    rather than trusted, so the index reflects the current linter -- which means
    ``fig index`` also doubles as "did my rules change under these notes?".

    ``scoring`` names the screen this folder is one of (see
    :data:`fig.discover.SCORING_MODES`) and ``disagreements`` carries the tickers the
    two screens split on, so a two-variant run produces two indexes that say what
    each one ranked by and, where it applies, that the other folder contradicts it.
    """
    out = Path(out_dir)
    results = []
    for path in note_paths(out):
        data = load_note(path)
        if not data or not data.get("reasons"):
            continue

        generation = data.get("generation") or {}
        result = lint.lint_writeup(data)

        # Re-run the grounding checks against the packet sitting beside the note.
        # This is stronger than trusting the figure recorded at generation time:
        # it re-verifies the claims against the evidence on disk, so an index
        # rebuild is a genuine audit rather than a restatement.
        grounding = generation.get("grounding")
        packet_path = path.with_name(f"{data['ticker']}.packet.json")
        if packet_path.is_file():
            try:
                stored_packet = json.loads(packet_path.read_text())
                grounding = lint.check_grounding(
                    data, packet_mod.to_prompt_context(stored_packet)
                )
                result["source_grounding"] = lint.check_source_grounding(
                    data, register_for(data, stored_packet)
                )
            except (OSError, json.JSONDecodeError):
                pass
        if grounding:
            result["grounding"] = grounding

        # Rewrite the note from the stored writeup so layout and metadata blocks
        # (the catalyst line, the cited sources, the sampled Evidence block)
        # reflect the current renderer. The model's prose is stored verbatim, so
        # this changes presentation only -- it never rewrites the reasoning.
        try:
            path.with_suffix(".md").write_text(
                render.render_writeup(
                    data,
                    include_lint=True,
                    grounding=grounding,
                    source_grounding=result.get("source_grounding"),
                )
            )
        except OSError:
            pass

        results.append(
            {
                "writeup": data,
                "lint": result,
                "model": generation.get("model"),
                "search_used": generation.get("search_used"),
                "attempts": generation.get("rounds") or [],
                "generation": generation,
                # Where the note lives, so the index can link into the side folder.
                "folder": "" if path.parent == out else path.parent.name,
            }
        )

    if results:
        write_index(
            results,
            out,
            excluded=_read_excluded(out),
            settings=_read_settings(out),
            scoring=scoring,
            disagreements=disagreements,
        )
    return {
        "index": str(out / "README.md"),
        "notes": len(results),
        "mean_score": round(sum(r["lint"]["score"] for r in results) / len(results), 1)
        if results
        else 0,
        "results": results,
    }


def excluded_path(out_dir: str | Path = "research") -> Path:
    return Path(out_dir) / "excluded.json"


def settings_path(out_dir: str | Path = "research") -> Path:
    return Path(out_dir) / "settings.json"


def record_settings(
    out_dir: str | Path,
    *,
    tickers: list[str],
    max_price: float | None,
    min_market_cap: float | None,
) -> None:
    """Record the rules a batch was selected under, beside its notes.

    A folder can hold notes from runs under different caps, and `fig index` rebuilds
    from the notes alone -- which cannot tell a $75 run from a $150 one. Without this
    the index states the tool's default, which is a claim about how the notes were
    chosen that is simply false for most of this folder. Batches are recorded as a
    list, keyed by the tickers each one produced, so the rebuild can attribute every
    note on disk to the run that made it.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = [
        row
        for row in _read_settings(out)
        if not (set(row.get("tickers") or []) & set(tickers))
    ]
    rows.append(
        {
            "date": date.today().isoformat(),
            "tickers": sorted(tickers),
            "max_price": max_price,
            "min_market_cap": min_market_cap,
        }
    )
    settings_path(out).write_text(json.dumps(rows, indent=2) + "\n")


def _read_settings(out_dir: str | Path = "research") -> list[dict]:
    path = settings_path(out_dir)
    if not path.is_file():
        return []
    try:
        rows = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def write_excluded(excluded: list[tuple[str, str]], out_dir: str | Path = "research") -> None:
    """Persist the names the price cap rejected, so the index can always state them.

    Without this the "excluded by the cap" section exists only in the index that a
    generate run happens to write, and the next `fig index` -- which rebuilds from
    the notes on disk -- would silently drop it. The names a rule *removed* are part
    of how a batch was selected, so they belong on disk next to the notes.
    """
    if not excluded:
        return
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # Merged, not replaced: exclusions accumulate across batches, and a later batch
    # that rejected nothing must not erase the record of what an earlier one removed.
    merged = {symbol: reason for symbol, reason in _read_excluded(out)}
    merged.update({symbol: reason for symbol, reason in excluded})
    excluded_path(out).write_text(
        json.dumps(
            [{"symbol": symbol, "reason": reason} for symbol, reason in sorted(merged.items())],
            indent=2,
        )
        + "\n"
    )


def _read_excluded(out_dir: str | Path = "research") -> list[tuple[str, str]]:
    path = excluded_path(out_dir)
    if not path.is_file():
        return []
    try:
        rows = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    return [(r.get("symbol", "?"), r.get("reason", "")) for r in rows if r.get("symbol")]


def _clip(text: str, width: int = 68) -> str:
    """Truncate on a word boundary so the index never shows a severed word."""
    text = (text or "").strip()
    if len(text) <= width:
        return text
    cut = text[:width].rsplit(" ", 1)[0].rstrip(",;:")
    return f"{cut}..."


def _note_link(result: dict, suffix: str = "md") -> str:
    """Relative link to a note from the index at the top of ``out_dir``."""
    ticker = result["writeup"]["ticker"]
    folder = result.get("folder") or ""
    return f"{folder}/{ticker}.{suffix}" if folder else f"{ticker}.{suffix}"


def _side_section(
    lines: list[str],
    title: str,
    entries: list[dict],
    results_by_ticker: dict[str, dict],
) -> None:
    """One side's table, ranked, with the reason each name is on the list."""
    lines += [
        f"### {title}",
        "",
        "| # | ticker | conviction | evidence | catalyst | rev agree | lint | fwd PE | description |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    if not entries:
        lines.append("| - | _none in this batch_ | | | | | | | |")
        lines.append("")
        return
    for position, entry in enumerate(entries, start=1):
        result = results_by_ticker.get(entry["ticker"]) or {}
        components = entry["components"]
        when = entry["catalyst_date"] or "-"
        if entry["catalyst_days"] is not None:
            when += f" ({entry['catalyst_days']}d)"
        link = _note_link(result) if result else f"{entry['ticker']}.md"
        lines.append(
            f"| {position} | **{entry['ticker']}** | {entry['conviction']} | "
            f"{entry['evidence_label']} | {when} | {components['revision_agreement']:.1f} | "
            f"{entry['score']}/100 | {entry['fwd_pe']} | "
            f"[{_clip(entry['description'], 60)}]({link}) |"
        )
    lines.append("")


def _selection_phrase(cap: float | None, mcap: float | None, count: int) -> str:
    """How one run's selection rules read in the index.

    Built here rather than inline because the disabled cases have to read as English:
    the previous version interpolated the *number* 1 into the no-floor case and
    produced "under a $150 share price and a no 1 floor floor".
    """
    cap_text = f"a **${cap:,.0f}** share price" if cap is not None else "**no share-price cap**"
    floor_text = (
        f"a **${human_money(mcap)}** floor" if mcap else "**no market-cap floor**"
    )
    return f"{count} note(s) under {cap_text} and {floor_text}"


def _selection_groups(
    on_disk: set[str], recorded: list[dict]
) -> tuple[list[tuple[float | None, float | None, int]], int]:
    """Group the notes on disk by the selection rules that produced them.

    Returns ``(groups, unrecorded)``: one ``(cap, floor, count)`` per distinct rule
    set, in the order the run records first mention it, and how many notes on disk
    no record accounts for.

    Grouping is by the *rules*, not by the run that recorded them. A batch resumed
    after an outage writes a second settings row carrying the same cap and floor,
    and treating rows as groups rendered the same sentence twice -- "4 note(s) under
    a $150 share price ...; 6 note(s) under a $150 share price ...". Tickers are
    gathered per rule so a name appearing in two rows is still counted once.
    """
    by_rules: dict[tuple[float | None, float | None], set[str]] = {}
    attributed: set[str] = set()
    for row in recorded:
        members = on_disk & set(row.get("tickers") or [])
        if not members:
            continue
        by_rules.setdefault((row.get("max_price"), row.get("min_market_cap")), set()).update(
            members
        )
        attributed |= members
    groups = [(cap, floor, len(names)) for (cap, floor), names in by_rules.items()]
    return groups, len(on_disk - attributed)


def _scoring_lines(scoring: str | None, disagreements: list[dict] | None) -> list[str]:
    """What ranked this folder, and where the companion folder contradicts it.

    A two-variant run publishes siblings that can rank the same name on opposite
    sides. That fact belongs in both indexes: a reader holding one folder has no way
    to discover the other's disagreement, and of everything this pipeline prints,
    a genuine contradiction between two of its own screens is the thing most likely
    to be mistaken for agreement by omission.
    """
    from . import variants as variants_mod  # local: only the index needs the titles

    lines: list[str] = []
    if scoring:
        title = variants_mod.VARIANT_TITLES.get(scoring, scoring)
        if scoring == "divergence":
            what = (
                "A name scores high here when the consensus revision and the 30-day "
                "price move point opposite ways -- improving estimates into a falling "
                "tape, or deteriorating estimates into a rising one -- and collapses "
                "to at most 12 when the two agree. That selects for a name the crowd "
                "has taken the other side of, at the cost that the price leg supplies "
                "much of the order."
            )
        else:
            what = (
                "The consensus revision alone sets this order: its size is the score "
                "and its sign is the side. The price move is shown on the screen table "
                "as context and does not enter the score, which makes the ranking "
                "closer to consensus than a revision-versus-price gap was -- the "
                "non-consensus argument has to come from the reasons."
            )
        others = [v for v in variants_mod.VARIANTS if v != scoring]
        lines.append("### Ranking signal")
        lines.append("")
        lines.append(f"This folder was ranked by **{title}** (`--variants {scoring}`). {what}")
        if others:
            links = ", ".join(f"[`{v}/`](../{v}/)" for v in others)
            lines.append(
                f"The same screen ran under {links} beside this folder -- the same "
                f"screened rows, one different term -- so the two orderings can be "
                f"compared on identical evidence."
            )
        lines.append("")

    if disagreements:
        lines.append("### Screen disagreements")
        lines.append("")
        lines.append(
            "These tickers were picked by both screens on **opposite sides**. Both "
            "notes were written, one per folder, because a long and a short differ "
            "in the catalyst argument, the watch lines and the structure -- they are "
            "not two copies of one idea. Which screen is right is a judgement about "
            "the company, and the disagreement is reported rather than reconciled."
        )
        lines.append("")
        for clash in disagreements:
            sides = ", ".join(
                f"**{variant}** says {direction}"
                for direction, variant in sorted(clash.get("directions", {}).items())
            )
            lines.append(f"- **{clash.get('symbol')}** -- {sides}.")
        lines.append("")

    return lines


def write_index(
    results: list[dict],
    out_dir: str | Path = "research",
    *,
    excluded: list[tuple[str, str]] | None = None,
    settings: list[dict] | None = None,
    scoring: str | None = None,
    disagreements: list[dict] | None = None,
) -> str:
    """A scannable index of a batch, with the two sides apart and provenance kept.

    The batch is split by side rather than left in one ranked list, because a long
    and a short are not two points on one scale: they break for opposite reasons,
    and a reader deciding what to look at first is choosing which side to read.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    entries = ranking_mod.rank_ideas(results)
    counts = ranking_mod.summarise(entries)
    results_by_ticker = {r["writeup"]["ticker"]: r for r in results}
    longs = [e for e in entries if e["direction"] == "long"]
    shorts = [e for e in entries if e["direction"] == "short"]
    other = [e for e in entries if e["direction"] not in ("long", "short")]

    scored = [e for e in entries]
    # Coverage is counted per reason, not per note: "this note has citations" is true
    # of a note where one of three reasons is unsourced, and the per-reason count is
    # the one a reader is entitled to see.
    uncited = [
        (r["writeup"]["ticker"], index + 1)
        for r in results
        for index, sources in enumerate(r["writeup"].get("reason_sources") or [])
        if not sources
    ]
    full = sum(
        1
        for r in results
        if (r["writeup"].get("reason_sources") or [])
        and all(r["writeup"]["reason_sources"])
    )
    cited = sum(1 for r in results if (r["writeup"].get("reason_sources") or []))

    # The cap each note was selected under, from the run records beside the notes.
    # Stating one default for a folder built under several caps would be a false
    # claim about how most of these names were chosen.
    on_disk = {r["writeup"]["ticker"] for r in results}
    recorded = settings if settings is not None else _read_settings(out)
    groups, unrecorded = _selection_groups(on_disk, recorded)

    defaults_text = (
        f"${discover.DEFAULT_MAX_PRICE:,.0f} and "
        f"${human_money(discover.DEFAULT_MIN_MARKET_CAP)}"
    )

    def _rules_sentence() -> str:
        parts = []
        for cap, mcap, count in groups:
            parts.append(_selection_phrase(cap, mcap, count))
        if not parts:
            # Nothing on disk says how these were chosen. Naming the defaults is still
            # better than silence, but it is labelled as the default rather than as a
            # record, so it does not read as a fact about the selection.
            return (
                f"No run record for these {len(on_disk)} note(s): they were generated "
                f"before the rules were recorded on disk, when the tool's defaults were "
                f"{defaults_text}."
            )
        sentence = "Selected by `fig screen`: " + "; ".join(parts) + "."
        if unrecorded:
            sentence += (
                f" The other {unrecorded} note(s) predate the run record; the tool's "
                f"defaults at the time were {defaults_text}."
            )
        return sentence
    lines = [
        "# Generated research",
        "",
        f"**{counts['ideas']} idea(s): {counts['longs']} long "
        f"([`longs/`](longs/)), {counts['shorts']} short ([`shorts/`](shorts/))** "
        f"(mean lint score "
        f"{round(sum(r['lint']['score'] for r in results) / len(results), 1) if results else 0}/100, "
        f"mean conviction {counts['mean_conviction']}).",
        "",
        f"{counts['well_evidenced']} of {counts['ideas']} are confirmed by their "
        f"end-market evidence in a majority of {counts['samples']} sampled run(s); "
        f"{counts['evidence_against']} are contradicted by it. "
        "The verdict is sampled rather than asserted because the evidence is "
        "qualitative and genuinely varies between runs.",
        "",
        f"{full} of {len(results)} note(s) cite a source for every reason, printed "
        f"under the reason it supports. {len(uncited)} reason(s) across "
        f"{len({t for t, _ in uncited})} note(s) carry none"
        + (
            " ("
            + ", ".join(f"{t} reason {i}" for t, i in uncited)
            + ") and are listed as errors."
            if uncited
            else "."
        )
        + " Every source is an id resolved against that note's `.packet.json`, so the "
        "links are the evidence's own rather than the writer's -- a citation the "
        "packet cannot vouch for is dropped instead of printed.",
        "",
        "### How these were selected",
        "",
        _rules_sentence()
        + " The share-price cap is a tradeability rule, so a position fits the "
        "~$4,500 capital unit, and the floor keeps the option requirement "
        "satisfiable. Loss-making companies and names "
        "with no usable option chain are **not** filtered: those facts come from free "
        "endpoints, where a bad response is indistinguishable from a genuine absence, "
        "and structuring is optional downstream anyway. They are recorded as caveats "
        "on the note instead (`--strict` restores the old filters).",
        "",
        "Regenerated by any `fig generate` batch, or rebuilt from the notes on disk "
        "with `fig index`. Every note is re-linted as it is indexed, so the scores "
        "here reflect the current linter rather than the state at generation time.",
        "",
        *_scoring_lines(scoring, disagreements),
        "## Ranking",
        "",
        "Ordered by conviction, within each side. **This is not a prediction and not "
        "a recommendation.** It says where to start reading, using facts about each "
        "note rather than a view on the company: catalyst proximity (0.20), "
        "estimate-revision agreement across the 7- and 30-day windows (0.20), "
        "current lint score (0.10), whether every figure is grounded (0.10), and the "
        "sampled end-market verdict (0.40). A high lint score is NOT evidence of a "
        "good thesis -- it measures form, and the two highest-scoring notes in this "
        "repo's history were the two judged weakest on reasoning. See "
        "`src/fig/ranking.py`.",
        "",
    ]

    _side_section(lines, f"Longs ({counts['longs']})", longs, results_by_ticker)
    _side_section(lines, f"Shorts ({counts['shorts']})", shorts, results_by_ticker)
    if other:
        _side_section(lines, f"Unclassified ({len(other)})", other, results_by_ticker)

    if excluded:
        lines += [
            "## Excluded by the share-price cap",
            "",
            "Ideas are capped by share price so a position fits the "
            "~$4,500 capital unit. These were researched by the screen and rejected on "
            f"price alone -- the cap is a tradeability rule, not a judgement on them:",
            "",
        ]
        for symbol, reason in excluded:
            lines.append(f"- **{symbol}** -- {reason}")
        lines.append("")

    lines += [
        "## All notes",
        "",
        "| ticker | side | folder | catalyst | score | fwd PE | mkt cap | sources | description | files |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for result in results:
        writeup = result["writeup"]
        quants = writeup.get("quants") or {}
        symbol = writeup["ticker"]
        catalyst = writeup.get("catalyst") or {}
        when = catalyst.get("date") or "-"
        if catalyst.get("date") and catalyst.get("days_out") is not None:
            when = f"{catalyst['date']} ({catalyst['days_out']}d)"
        cited = sum(len(s or []) for s in (writeup.get("reason_sources") or []))
        lines.append(
            f"| **{symbol}** | {writeup.get('direction','').upper()} | "
            f"{result.get('folder') or '-'} | {when} | "
            f"{result['lint']['score']}/100 | {quants.get('fwd_pe','-')} | "
            f"{quants.get('market_cap','-')} | {cited} | "
            f"{_clip(writeup.get('description'))} | "
            f"[{symbol}.md]({_note_link(result)}) · "
            f"[json]({_note_link(result, 'json')}) |"
        )

    lines += ["", "## Run details", ""]
    for result in results:
        writeup = result["writeup"]
        symbol = writeup["ticker"]
        rounds = result.get("attempts") or []
        grounding = (result.get("lint") or {}).get("grounding") or {}
        if grounding:
            grounded = (
                f"{grounding['checked']} figures all traced to the packet"
                if grounding.get("grounded")
                else f"unsupported: {', '.join(grounding.get('unsupported') or [])}"
            )
        else:
            grounded = "not checked"
        source_ground = (result.get("lint") or {}).get("source_grounding") or {}
        if source_ground:
            source_note = (
                f"{source_ground['checked']} figure(s) checked against the cited source"
                if source_ground.get("ok")
                else f"figures outside the cited source: {'; '.join(source_ground.get('mismatches') or [])}"
            )
        else:
            source_note = "not checked"
        legs = "legs" if (writeup.get("structuring") or {}).get("rows") else "no legs"
        cited = sum(len(s or []) for s in (writeup.get("reason_sources") or []))
        lines.append(
            f"- **{symbol}** — {result.get('folder') or 'flat'}/, model "
            f"`{result.get('model') or 'n/a'}`, {legs}, "
            f"search {'on' if result.get('search_used') else 'off'}, "
            f"{len(rounds)} round(s), scores {[r['score'] for r in rounds]}, "
            f"{cited} source citation(s), "
            f"grounding: {grounded}, source grounding: {source_note}"
        )
    lines.append("")
    lines.append(
        "Each note has a `.packet.json` beside it holding the exact evidence used "
        "(price, consensus, statements, headlines, search results, option chain), so "
        "any figure can be traced to its source -- and every source named in a reason "
        "is an entry in that packet's own source register."
    )
    text = "\n".join(lines) + "\n"
    (out / "README.md").write_text(text)
    return text
