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
from datetime import date
from pathlib import Path

from . import catalyst as catalyst_mod, lint, options, packet as packet_mod, prompts, render
from .sources import ollama

# Only these keys are taken from the model.
MODEL_OWNED = ("description", "reasons", "reflection")


# --------------------------------------------------------------------------
# assembling the note
# --------------------------------------------------------------------------


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

    return {
        "writeup": writeup,
        "packet": pack,
        "lint": result,
        "attempts": attempts,
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

        results.append(
            {
                "writeup": data,
                "lint": result,
                "model": generation.get("model"),
                "search_used": generation.get("search_used"),
                "attempts": generation.get("rounds") or [],
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
    }


def _clip(text: str, width: int = 68) -> str:
    """Truncate on a word boundary so the index never shows a severed word."""
    text = (text or "").strip()
    if len(text) <= width:
        return text
    cut = text[:width].rsplit(" ", 1)[0].rstrip(",;:")
    return f"{cut}..."


def write_index(results: list[dict], out_dir: str | Path = "research") -> str:
    """A scannable index of a batch, with provenance and lint scores."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Generated research",
        "",
        f"{len(results)} note(s), mean lint score "
        f"{round(sum(r['lint']['score'] for r in results) / len(results), 1) if results else 0}/100.",
        "",
        "Regenerated by any `fig generate` batch, or rebuilt from the notes on disk "
        "with `fig index`. Every note is re-linted as it is indexed, so the scores "
        "here reflect the current linter rather than the state at generation time.",
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
