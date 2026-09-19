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

from . import (
    catalyst as catalyst_mod,
    ranking as ranking_mod,
    discover,
    lint,
    options,
    packet as packet_mod,
    prompts,
    render,
    research as research_mod,
)
from .sources import ollama, yahoo

# Only these keys are taken from the model.
MODEL_OWNED = ("description", "reasons", "reflection")


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
    # Prefer credit-related moves: they are usually the thesis.
    ranked = sorted(deltas, key=lambda d: (not d.get("is_credit"), -abs(d["change_pct"])))
    for delta in ranked[:2]:
        delta_lines.append(
            f"Last quarter {delta['label'].lower()} {delta['direction']} "
            f"{abs(delta['change_pct']):.0f}% quarter over quarter ({delta['period']})"
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
    reasons = [str(r).strip() for r in (model_output.get("reasons") or []) if str(r).strip()]
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
        # to the measured justification rather than leaving the block bare.
        why = "; ".join(catalyst_mod.justification_facts(catalyst)) or ""

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
        "quants": quants_block(packet),
    }

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
                "A style checker rejected the note for the reasons below. Fix every "
                "one of them. Keep the same claims and the same evidence -- only make "
                "them shorter and plainer. Do not add new facts.\n\n"
                f"{bullets}\n\n"
                "Return the corrected JSON only, in exactly the same shape: "
                '{"description": str, "reasons": [str], "reflection": str}'
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

        trends = (pack.get("forward_trends") or {}).get("trends") or []
        verdict = research_mod.evidence_verdict(trends, direction)

        messages = _messages_for(pack, direction)
        attempts: list[dict] = []
        model_output: dict = {}
        writeup: dict = {}
        result: dict = {}

        for round_index in range(repairs + 1):
            model_output, reply = _chat_json(symbol, messages, model=model, say=say)

            writeup = assemble_writeup(pack, model_output, direction)
            result = lint.lint_writeup(writeup)
            grounding = lint.check_grounding(writeup, packet_mod.to_prompt_context(pack))
            result["grounding"] = grounding

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

    # The saved note is the best sample; its lint/grounding detail is re-derived
    # from the note itself so what is stored is what the note actually scores now.
    writeup = best["writeup"]
    trends = (pack.get("forward_trends") or {}).get("trends") or []
    result = lint.lint_writeup(writeup)
    result["grounding"] = lint.check_grounding(writeup, packet_mod.to_prompt_context(pack))
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


def save_idea(result: dict, out_dir: str | Path = "research") -> dict:
    """Write ``<ticker>.json`` and ``<ticker>.md`` plus the raw packet.

    The packet is kept because it is the audit trail: every number in the note can
    be traced back to the evidence that produced it.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    writeup = result["writeup"]
    symbol = writeup["ticker"]

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

    note = render.render_writeup(writeup, include_lint=True)
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
        "score": result["lint"]["score"],
        "ok": result["lint"]["ok"],
    }


def rebuild_index(out_dir: str | Path = "research") -> dict:
    """Rebuild the index from the notes on disk.

    Everything needed is inside each ``.json``: the writeup itself plus the
    ``generation`` block recording model, rounds and scores. Notes are re-linted
    rather than trusted, so the index reflects the current linter -- which means
    ``fig index`` also doubles as "did my rules change under these notes?".
    """
    out = Path(out_dir)
    results = []
    for path in sorted(out.glob("*.json")):
        if path.name.endswith(".packet.json"):
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not data.get("ticker") or not data.get("reasons"):
            continue

        generation = data.get("generation") or {}
        result = lint.lint_writeup(data)

        # Re-run the grounding check against the packet sitting beside the note.
        # This is stronger than trusting the figure recorded at generation time:
        # it re-verifies the claims against the evidence on disk, so an index
        # rebuild is a genuine audit rather than a restatement.
        grounding = generation.get("grounding")
        packet_path = out / f"{data['ticker']}.packet.json"
        if packet_path.is_file():
            try:
                stored_packet = json.loads(packet_path.read_text())
                grounding = lint.check_grounding(
                    data, packet_mod.to_prompt_context(stored_packet)
                )
            except (OSError, json.JSONDecodeError):
                pass
        if grounding:
            result["grounding"] = grounding

        # Rewrite the note from the stored writeup so layout and metadata blocks
        # (the catalyst line, the sampled Evidence block) reflect the current
        # renderer. The model's prose is stored verbatim, so this changes
        # presentation only -- it never rewrites the reasoning.
        try:
            (out / f"{data['ticker']}.md").write_text(
                render.render_writeup(data, include_lint=True)
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
            }
        )

    if results:
        write_index(results, out)
    return {
        "index": str(out / "README.md"),
        "notes": len(results),
        "mean_score": round(sum(r["lint"]["score"] for r in results) / len(results), 1)
        if results
        else 0,
        "results": results,
    }


def _clip(text: str, width: int = 68) -> str:
    """Truncate on a word boundary so the index never shows a severed word."""
    text = (text or "").strip()
    if len(text) <= width:
        return text
    cut = text[:width].rsplit(" ", 1)[0].rstrip(",;:")
    return f"{cut}..."


def write_index(
    results: list[dict],
    out_dir: str | Path = "research",
    *,
    excluded: list[tuple[str, str]] | None = None,
    max_price: float | None = None,
) -> str:
    """A scannable index of a batch, with provenance and lint scores."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    entries = ranking_mod.rank_ideas(results)
    counts = ranking_mod.summarise(entries)

    lines = [
        "# Generated research",
        "",
        f"**{counts['ideas']} idea(s): {counts['longs']} long, {counts['shorts']} short** "
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
        "### How these were selected",
        "",
        f"Share price must be under **${(max_price or 0):,.0f}** -- a tradeability rule, "
        "so a position fits the ~$4,500 capital unit. Loss-making companies and names "
        "with no usable option chain are **not** filtered: those facts come from free "
        "endpoints, where a bad response is indistinguishable from a genuine absence, "
        "and structuring is optional downstream anyway. They are recorded as caveats "
        "on the note instead (`--strict` restores the old filters).",
        "",
        "Regenerated by any `fig generate` batch, or rebuilt from the notes on disk "
        "with `fig index`. Every note is re-linted as it is indexed, so the scores "
        "here reflect the current linter rather than the state at generation time.",
        "",
        "## Ranking",
        "",
        "Ordered by conviction. **This is not a prediction and not a recommendation.** "
        "It says where to start reading, using facts about each note rather than a "
        "view on the company: catalyst proximity (0.20), estimate-revision agreement "
        "across the 7- and 30-day windows (0.20), current lint score (0.10), whether "
        "every figure is grounded (0.10), and the sampled end-market verdict (0.40). "
        "A high lint score is NOT evidence of a good thesis -- it measures form, and "
        "the two highest-scoring notes in this repo's history were the two judged "
        "weakest on reasoning. See `src/fig/ranking.py`.",
        "",
        "| # | ticker | side | conviction | evidence | catalyst | rev agree | lint | fwd PE | description |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for entry in entries:
        components = entry["components"]
        when = entry["catalyst_date"] or "-"
        if entry["catalyst_days"] is not None:
            when += f" ({entry['catalyst_days']}d)"
        lines.append(
            f"| {entry['rank']} | **{entry['ticker']}** | {entry['direction'].upper()} | "
            f"{entry['conviction']} | {entry['evidence_label']} | {when} | "
            f"{components['revision_agreement']:.1f} | {entry['score']}/100 | "
            f"{entry['fwd_pe']} | [{_clip(entry['description'], 60)}]({entry['ticker']}.md) |"
        )

    if excluded:
        lines += [
            "",
            "## Excluded by the share-price cap",
            "",
            f"Ideas are capped at **${max_price:,.0f} per share** so a position fits the "
            f"~$4,500 capital unit. These were researched by the screen and rejected on "
            f"price alone -- the cap is a tradeability rule, not a judgement on them:",
            "",
        ]
        for symbol, reason in excluded:
            lines.append(f"- **{symbol}** -- {reason}")
        lines.append("")

    lines += [
        "",
        "## All notes",
        "",
        "| ticker | side | catalyst | score | fwd PE | mkt cap | description | files |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for result in results:
        writeup = result["writeup"]
        quants = writeup.get("quants") or {}
        symbol = writeup["ticker"]
        catalyst = writeup.get("catalyst") or {}
        when = catalyst.get("date") or "-"
        if catalyst.get("date") and catalyst.get("days_out") is not None:
            when = f"{catalyst['date']} ({catalyst['days_out']}d)"
        lines.append(
            f"| **{symbol}** | {writeup.get('direction','').upper()} | {when} | "
            f"{result['lint']['score']}/100 | {quants.get('fwd_pe','-')} | "
            f"{quants.get('market_cap','-')} | {_clip(writeup.get('description'))} | "
            f"[{symbol}.md]({symbol}.md) |"
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
        legs = "legs" if (writeup.get("structuring") or {}).get("rows") else "no legs"
        lines.append(
            f"- **{symbol}** — model `{result.get('model') or 'n/a'}`, {legs}, "
            f"search {'on' if result.get('search_used') else 'off'}, "
            f"{len(rounds)} round(s), scores {[r['score'] for r in rounds]}, "
            f"grounding: {grounded}"
        )
    lines.append("")
    lines.append(
        "Each note has a `.packet.json` beside it holding the exact evidence used "
        "(price, consensus, statements, headlines, search results, option chain), "
        "so any figure can be traced to its source."
    )
    text = "\n".join(lines) + "\n"
    (out / "README.md").write_text(text)
    return text
