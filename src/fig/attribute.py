"""Attribute existing reasons to their sources, without rewriting the reasons.

Why this exists
---------------
Sources were added to the format after the first batches had already been written.
Those notes state figures with nothing to check them against, which is precisely
the complaint the feature answers -- so leaving them alone would make the folder
inconsistent in the least defensible direction: the earliest notes least checkable.

Regenerating them would work and would cost a full generation per note. This does
the narrow job instead. The reasons are **not** rewritten -- they are the author's
claim about the company, and re-rolling the prose to attach a citation would change
the thing being cited. The model is asked one question about each existing reason:
*which of this packet's sources does it rest on?* Everything else -- the id, the
provider, the date, the URL -- comes from the packet, exactly as in generation.

Two guards, both mechanical:

* an id that is not in the packet's source register is dropped, never written;
* the result is checked with :func:`fig.lint.check_source_grounding`, so a reason
  whose figures do not appear in the source it was matched to is reported rather
  than filed as settled.

Where a note cannot be attributed honestly -- no packet beside it, or a reason that
matches nothing -- it is left uncited and listed as such. An uncited reason is a
gap a reader can see; a wrongly cited one is not.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import generate, lint, packet as packet_mod, render
from .sources import ollama

ATTRIBUTE_PROMPT = """Below are the reasons from an equity note, and the register of \
sources its evidence packet was built from.

For each reason, decide which sources that reason RESTS ON. A source belongs to a \
reason only if the reason's claim or a figure in it comes from that source. Reading \
the register is not the same as being supported by it: if a reason quotes a figure \
that appears in one entry, cite that entry and not the whole register.

Rules:
- Return one list per reason, in the same order, holding ONLY ids from the register.
- A reason built on the company's own reported figures should cite the entry those \
figures came from, not a news story that happens to mention the company.
- If a reason is genuinely supported by nothing in the register, return an empty \
list for it. An empty list is a finding; a guessed id is not.
- Do not rewrite the reasons. Do not invent ids.

Return ONLY JSON: {{"reason_sources": [["S1"], ["S4", "S7"]]}}

REASONS:
{reasons}

SOURCE REGISTER:
{catalogue}"""


def _catalogue_lines(catalogue: list[dict]) -> str:
    lines = []
    for entry in catalogue:
        bits = [entry.get("id") or "?", f"{entry.get('provider') or '?'}:"]
        bits.append(str(entry.get("label") or ""))
        if entry.get("date"):
            bits.append(f"({entry['date']})")
        text = str(entry.get("text") or "").strip()
        lines.append("  " + " ".join(bits) + (f"\n      evidence text: {text[:500]}" if text else ""))
    return "\n".join(lines)


def _parse_citations(text: str) -> dict:
    """Read the answer as citation lists, whatever shape it arrived in.

    The task asks for ``{"reason_sources": [[...]]}``, and models also return a bare
    array, a fenced block, or a sentence before the JSON. All of those mean the same
    thing, and rejecting them would spend a retry on formatting while the answer was
    already correct -- which is how one note in the first backfill run took five
    minutes instead of forty seconds.
    """
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        cleaned = parts[1] if len(parts) > 1 else cleaned
        if cleaned.lstrip().startswith("json"):
            cleaned = cleaned.lstrip()[4:]
        cleaned = cleaned.strip()

    parsed: Any = None
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        for opener, closer in (("{", "}"), ("[", "]")):
            start, end = cleaned.find(opener), cleaned.rfind(closer)
            if start != -1 and end > start:
                try:
                    parsed = json.loads(cleaned[start : end + 1])
                    break
                except json.JSONDecodeError:
                    continue

    if isinstance(parsed, list):
        # A bare array of citation lists IS the answer; resolve_reason_sources also
        # accepts a list of objects that each carry a source key.
        return {"reason_sources": parsed}
    if isinstance(parsed, dict):
        return parsed
    raise RuntimeError("model did not return the citations as JSON")


def attribute_note(
    data: dict, packet: dict, *, model: str | None = None, verbose: bool = True
) -> dict:
    """Attach ``reason_sources`` to one already-written note.

    Returns ``{"reason_sources", "unknown", "source_grounding", "catalogue_size"}``.
    """
    reasons = [str(r) for r in (data.get("reasons") or [])]
    catalogue = packet.get("sources") or packet_mod.source_catalogue(packet)
    if not reasons or not catalogue:
        return {"reason_sources": [], "unknown": [], "catalogue_size": len(catalogue)}

    prompt = ATTRIBUTE_PROMPT.format(
        reasons="\n".join(f"{i}) {r}" for i, r in enumerate(reasons, start=1)),
        catalogue=_catalogue_lines(catalogue),
    )
    attempts = 3
    raw: dict = {}
    for attempt in range(attempts):
        messages = [{"role": "user", "content": prompt}]
        if attempt:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        'Return the JSON object only, no prose: '
                        '{"reason_sources": [["S1"], ["S4", "S7"]]}'
                    ),
                }
            )
        reply = ollama.chat(messages, model=model or ollama.DEFAULT_MODEL)
        try:
            raw = _parse_citations(reply["text"])
            break
        except RuntimeError:
            if verbose:
                print(f"    unparseable citations, retrying ({attempt + 2}/{attempts})")
    resolved, unknown = generate.resolve_reason_sources(raw, catalogue, len(reasons))

    probe = {**data, "reason_sources": resolved}
    grounding = lint.check_source_grounding(probe, catalogue)
    return {
        "reason_sources": resolved,
        "unknown": unknown,
        "source_grounding": grounding,
        "catalogue_size": len(catalogue),
    }


def attribute_folder(
    out_dir: str | Path = "research",
    *,
    model: str | None = None,
    limit: int | None = None,
    verbose: bool = True,
) -> dict:
    """Backfill sources for every note in a folder that lacks them.

    The note's own ``.packet.json`` is the evidence, so nothing is re-researched and
    no number moves. Notes already carrying citations are skipped, which makes the
    command safe to re-run.
    """
    out = Path(out_dir)
    attributed: list[dict] = []
    skipped: list[tuple[str, str]] = []

    for path in generate.note_paths(out):
        data = generate.load_note(path)
        if not data or not data.get("reasons"):
            continue
        ticker = data["ticker"]
        if limit is not None and len(attributed) >= limit:
            break
        if data.get("reason_sources") and data.get("sources_catalogue"):
            skipped.append((ticker, "already cited"))
            continue

        packet_path = path.with_name(f"{ticker}.packet.json")
        if not packet_path.is_file():
            skipped.append((ticker, "no packet beside it"))
            continue
        packet = json.loads(packet_path.read_text())

        if verbose:
            print(f"  [{ticker}] attributing {len(data['reasons'])} reason(s)")
        result = attribute_note(data, packet, model=model, verbose=verbose)

        data["reason_sources"] = result["reason_sources"]
        # The register is written into the note as well, so a reader of the note
        # alone can see what each id refers to -- and so `fig lint` can check the
        # citations without needing the packet.
        data["sources_catalogue"] = generate.public_sources(
            packet.get("sources") or packet_mod.source_catalogue(packet)
        )
        if result["unknown"]:
            data["sources_unverified"] = result["unknown"]
        path.write_text(json.dumps(data, indent=2) + "\n")
        # Re-render the note with the citation lines. Prose is untouched. The
        # grounding verdict is recomputed against the packet and printed in the note,
        # so a backfilled note states its own support exactly as a freshly generated
        # one does -- and this is where a figure that is in the packet but nowhere
        # near the source it cites becomes visible to the reader.
        path.with_suffix(".md").write_text(
            render.render_writeup(
                data,
                include_lint=True,
                grounding=lint.check_grounding(data, packet_mod.to_prompt_context(packet)),
                source_grounding=result["source_grounding"],
            )
        )

        cited = sum(len(s or []) for s in result["reason_sources"])
        attributed.append(
            {
                "ticker": ticker,
                "path": str(path),
                "reasons": len(data["reasons"]),
                "citations": cited,
                "uncited_reasons": [
                    i + 1 for i, s in enumerate(result["reason_sources"]) if not s
                ],
                "unknown_ids": result["unknown"],
                "source_grounding": result["source_grounding"],
            }
        )
    return {"attributed": attributed, "skipped": skipped}
