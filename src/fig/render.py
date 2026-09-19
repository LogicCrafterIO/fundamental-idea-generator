"""Render a writeup into the reference layout.

The output target is the plain-text shape of the two reference notes, including
the tab-separated Structuring table, which is pasted from a broker ticket rather
than a markdown table::

    Long	CALL	18-Dec-26	$ 155.00	3	$ 150.00	100	$ 15.55	$ -	$ -	$ -	$ 4,665.00
    Short	CALL	16-Oct-26	$ 155.00	2	$ 150.00	100	$ 6.44	$ -	$ -	$ -	$ (1,288.00)

Columns: side, type, expiry, strike, quantity, underlying price, multiplier,
option price, three unused cash columns, total. Negative money is parenthesised,
and the premium paid is positive while the credit received is negative.
"""

from __future__ import annotations

from .lint import lint_writeup


def _money(value: float | None, *, paren_negative: bool = True) -> str:
    """``1288.0`` -> ``"$ (1,288.00)"``; ``4665.0`` -> ``"$ 4,665.00"``."""
    if value is None:
        return "$ -"
    if value < 0 and paren_negative:
        return f"$ ({abs(value):,.2f})"
    return f"$ {value:,.2f}"


def render_structure_table(rows: list[dict]) -> str:
    """Tab-separated legs, in reference column order."""
    lines = []
    for row in rows:
        lines.append(
            "\t".join(
                [
                    str(row["side"]),
                    str(row["type"]),
                    str(row["expiry"]),
                    _money(row["strike"]),
                    str(row["qty"]),
                    _money(row["underlying"]),
                    str(row["multiplier"]),
                    _money(row["price"]),
                    "$ -",
                    "$ -",
                    "$ -",
                    _money(row["total"]),
                ]
            )
        )
    return "\n".join(lines)


def render_writeup(writeup: dict, *, include_lint: bool = False) -> str:
    """Full note in reference layout.

    ``writeup`` shape::

        {"ticker", "description", "reasons": [...],
         "quants": {"price","market_cap","fwd_pe","eps_trend","eps_revisions","extra":[...]},
         "structuring": {"rows": [...], "reflection": "..."}}
    """
    out: list[str] = [f"Ticker: {writeup.get('ticker','')}", ""]

    out.append("Description")
    out.append((writeup.get("description") or "").strip())
    out.append("")

    # The catalyst sits directly under the Description: it is the line that says
    # when the idea gets settled, so it should be read before the reasons.
    catalyst = writeup.get("catalyst") or {}
    if catalyst.get("date") or catalyst.get("facts_line"):
        out.append("Catalyst")
        if catalyst.get("facts_line"):
            out.append(str(catalyst["facts_line"]).strip())
        if catalyst.get("why"):
            out.append(str(catalyst["why"]).strip())
        out.append("")

    out.append("Reasons")
    for index, reason in enumerate(writeup.get("reasons") or [], start=1):
        out.append(f"{index}) {str(reason).strip()}")
    out.append("")

    quants = writeup.get("quants") or {}
    out.append("Quants")
    price = quants.get("price")
    if price is not None:
        out.append(f"Price: {price:g}" if isinstance(price, (int, float)) else f"Price: {price}")
    if quants.get("market_cap"):
        out.append(f"Market Cap: {quants['market_cap']}")
    if quants.get("fwd_pe") is not None:
        basis = quants.get("fwd_pe_basis")
        suffix = f" ({basis})" if basis else ""
        out.append(f"Fwd PE: {quants['fwd_pe']}{suffix}")
    if quants.get("ps") is not None:
        out.append(f"P/S: {quants['ps']}")
    if quants.get("eps_trend"):
        out.append(f"EPS Trends: {quants['eps_trend']}")
    if quants.get("eps_revisions"):
        out.append(f"EPS Revisions: {quants['eps_revisions']}")
    for extra in quants.get("extra") or []:
        out.append(str(extra))
    out.append("")

    structuring = writeup.get("structuring") or {}
    if structuring and (structuring.get("rows") or structuring.get("reflection")):
        out.append("Structuring")
        rows = structuring.get("rows") or []
        if rows:
            out.append(render_structure_table(rows))
        if structuring.get("thesis_target"):
            out.append(str(structuring["thesis_target"]))
        if structuring.get("reflection"):
            out.append(str(structuring["reflection"]).strip())
    elif writeup.get("structure_error"):
        # Structuring is optional, but its absence is stated rather than hidden.
        out.append(f"[no option structure: {writeup['structure_error']}]")

    # The sampled verdict belongs in the note, not only in the index JSON: a reader
    # of the .md should be able to see that a thesis was contradicted by its own
    # end-market evidence in 2 of 3 runs without opening a second file.
    generation = writeup.get("generation") or {}
    verdict = generation.get("verdict") or {}
    if verdict.get("samples"):
        out.append("")
        out.append("Evidence")
        confirmed = verdict.get("confirmed") or 0
        contradicted = verdict.get("contradicted") or 0
        mixed = verdict.get("mixed") or 0
        parts = [f"{confirmed} of {verdict['samples']} sampled run(s) confirmed"]
        if contradicted:
            parts.append(f"{contradicted} contradicted")
        if mixed:
            parts.append(f"{mixed} mixed or no evidence")
        out.append(
            f"End-market research, sampled {verdict['samples']} times because the "
            f"evidence is qualitative: " + ", ".join(parts) + "."
        )

    text = "\n".join(out).rstrip() + "\n"
    if include_lint:
        result = lint_writeup(writeup)
        text += "\n" + _render_lint(result)
    return text


def _render_lint(result: dict) -> str:
    lines = [
        "---",
        f"Lint: score {result['score']}/100, {result['errors']} error(s), "
        f"{result['warnings']} warning(s), "
        f"description {result['stats']['description_words']} words, "
        f"catalyst {result['stats'].get('catalyst_why_words', 0)} words, "
        f"reasons {result['stats']['reason_words']}",
    ]
    grounding = result.get("grounding")
    if grounding:
        if grounding["unsupported"]:
            lines.append(
                f"Grounding: {len(grounding['unsupported'])} figure(s) in the prose were "
                f"not found in the evidence -- check before trusting: "
                f"{', '.join(grounding['unsupported'])}"
            )
        else:
            lines.append(
                f"Grounding: all {grounding['checked']} figures in the prose appear in the evidence."
            )
    for issue in result["issues"]:
        lines.append(f"  {issue}")
    return "\n".join(lines)


def render_index(writeups: list[dict]) -> str:
    """A one-line-per-idea index, for scanning a batch."""
    lines = ["# Idea index", ""]
    for w in writeups:
        direction = (w.get("direction") or "").upper()
        ticker = w.get("ticker", "")
        quants = w.get("quants") or {}
        result = lint_writeup(w)
        lines.append(
            f"- **{ticker}** ({direction}) — {quants.get('fwd_pe', 'n/a')} fwd PE, "
            f"{quants.get('market_cap', 'n/a')} — lint {result['score']}/100 — "
            f"{(w.get('description') or '')[:80]}"
        )
    return "\n".join(lines) + "\n"
