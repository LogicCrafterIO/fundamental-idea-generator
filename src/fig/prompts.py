"""Prompts that enforce the house style: **simple language, as few words as possible**.

The references are the spec. Read together, they imply a strict set of rules that
this module encodes as text a model can follow, and that :mod:`fig.lint` then
*verifies* -- because "be concise" is not an instruction, it is a wish.

What the references actually do
-------------------------------
``Description`` -- one line, and it says what the business **is now**, leading
with the change where there is one::

    Formerly Databases and SaaS, Oracle is now more focused on Infrastructure
    as a Service, which of course includes data centers.        (ORCL, 20 words)

    Nonprime consumer loan lender                               (OMF, 4 words)

Four words is a complete Description. The length follows the business, not a
quota -- so the rule is "as few words as the business allows", not "about 20".

``Reasons`` -- numbered, and each one is a **claim about why the price is
wrong**, never a fact dump. Three shapes appear repeatedly:

* *comparative* -- "it's not priced like Google, which is trading at a Forward PE
  of 25 while Oracle is at a Forward PE of 17".
* *market-is-wrong* -- "The market is overpricing the effects of GPU depreciation
  and debt servicing".
* *causal chain* -- "If NCO go from 7% now to 10% in Feb or March earnings then it
  could rerate significantly to a PE of 4-5 as earnings get hit".

Every reason carries a number, a named comparison, or a mechanism. None is
generic ("strong management", "good long-term prospects").

Jargon gets a **square-bracket gloss in plain words**::

    NCO [net charge offs]
    the legislation [known as a legal company pretending to be a software company]

``Structuring`` -- the legs as a table, then a short reflection in the author's
own voice that reasons about the credit size and often asks a question. It is
allowed to be informal ("lmk if my thinking on this is wrong") and to admit
uncertainty about the *trade construction* while staying confident about the
*thesis*.

What the style forbids
----------------------
* Hedging stacks: "could potentially", "might possibly", "it seems that".
* Adverbs that add nothing: "very", "really", "quite", "significantly" (unless
  attached to a number).
* Definitions the reader already knows, and throat-clearing openers.
* Restating a number in prose that the Quants block already states.
"""

from __future__ import annotations

import json

# Jargon that should be glossed in square brackets on first use.
#
# Calibrated against the references rather than against an ideal: the ORCL note
# glosses "NCO [net charge offs]" but leaves RPO, GPU, PE and PS bare, because
# those are everyday vocabulary for the reader. So this list holds genuinely
# specialist terms only -- flagging "AI" or "PE" produced noise that would train
# the writer to ignore the check. These are warnings, not errors.
GLOSS_REQUIRED = {
    "RPO": "remaining performance obligations, i.e. contracted work not yet billed",
    "NCO": "net charge offs, i.e. loans written off as uncollectable",
    "NCOs": "net charge offs, i.e. loans written off as uncollectable",
    "NRR": "net revenue retention",
    "ARR": "annual recurring revenue",
    "TAM": "total addressable market",
    "ROIC": "return on invested capital",
    "SBC": "stock-based compensation",
    "FCF": "free cash flow",
    "DTE": "days to expiry",
    "IV": "implied volatility",
    "DSO": "days sales outstanding",
}

WORD_BUDGET = {
    "description": 30,
    "reason": 40,
    "notes": 70,
    "reasons_min": 2,
    "reasons_max": 5,
}

SYSTEM_PROMPT = """You write short equity idea notes for a trader who already knows \
the market. You are not writing research for a client. You are writing the two or \
three sentences that would make someone act.

THE FORMAT, EXACTLY:

Ticker: <SYMBOL>

Description
<One line. What the business is NOW. If it has changed, lead with the change.
As few words as the business allows. "Nonprime consumer loan lender" is a complete,
correct Description. Never pad it to look substantial.>

Reasons
1) <One sentence. A claim about why the price is wrong.>
2) <...>

Quants
<The supplied facts, verbatim. Do not editorialise here.>

Structuring
<The supplied legs as a table, then 1-3 sentences in the author's voice reasoning
about the size of the credit and the risk.>

HARD RULES

1. BREVITY IS THE PRODUCT. If a word can be cut without losing meaning, cut it.
   Description <= 30 words. Each reason <= 40 words. Prefer 3 reasons over 5.
   A shorter note that says the same thing is always better. Never pad.

2. PLAIN WORDS ONLY. Write so a smart person outside finance understands. Say
   "loans written off" before you say "charge-offs". No jargon as decoration.

3. GLOSS EVERY ACRONYM in square brackets, in plain words, on first use:
   "NCO [net charge offs]", "RPO [contracted work not yet billed]".
   A bracket may also carry a short aside, as in the reference:
   "the legislation [known as a legal company pretending to be a software company]".

4. EACH REASON MUST CARRY ONE OF: a number, a named comparison to another company,
   or a causal mechanism (X leads to Y leads to Z). No generic virtues. If a reason
   would apply to any company in the sector, delete it.

5. NO HEDGING STACKS. Not "could potentially", "might possibly", "it seems".
   State the claim. Uncertainty belongs only in the Structuring reflection, and
   only about the trade construction.

6. QUOTE NUMBERS ON A STATED BASIS. When comparing multiples to another company,
   both must be the same basis. If the evidence gives you two forward-PE bases,
   pick one, and keep it consistent across every comparison in the note.

7. DO NOT INVENT. Every number must come from the supplied evidence. If something
   needed for a reason is missing, write the reason without it or omit the reason.
   Never estimate a figure that was not supplied.

8. The Structuring reflection is the only place for voice. One or two sentences:
   whether the credit is fat enough, how many more shorts could be sold, what the
   floor test says. It may end with a question. Keep it short.

Return ONLY JSON matching the requested schema. No markdown fences, no commentary."""


def format_spec() -> str:
    """The style rules as plain text, for embedding in any prompt or doc."""
    return SYSTEM_PROMPT


def build_user_prompt(packet_context: str, *, direction_hint: str | None = None) -> str:
    """The per-idea prompt: raw evidence plus the output contract."""
    hint = ""
    if direction_hint:
        hint = (
            f"\nThe structure supplied is a {direction_hint.upper()} idea. Write the note "
            f"for that direction; do not write about the other side.\n"
        )

    schema = {
        "ticker": "SYMBOL",
        "direction": "long | short",
        "description": "one line, plain words, as short as the business allows",
        "reasons": ["one sentence each, each carrying a number, a comparison, or a mechanism"],
        "quants": {
            "price": "number or null",
            "market_cap": "string as supplied, e.g. 7.07B",
            "fwd_pe": "number from evidence",
            "fwd_pe_basis": "which basis you used",
            "eps_trend": "the supplied EPS trends wording",
            "eps_revisions": "the supplied EPS revisions wording",
            "extra": ["optional extra factual lines such as quarter-over-quarter moves"],
        },
        "structuring": {
            "legs": "copy the supplied structure legs exactly as given",
            "reflection": "1-3 short sentences in the author's voice about credit size and risk",
        },
    }

    return f"""Write one idea note from the evidence below.

{hint}
=== EVIDENCE ===
{packet_context}
=== END EVIDENCE ===

Distil it. Most of the evidence above should NOT appear in the note -- your job is
to find the one or two things that make the price wrong, and say them briefly.

Reminders: Description <= 30 words and says what the business is now. Each reason
<= 40 words, one sentence, carrying a number, a named comparison, or a mechanism.
Gloss every acronym in square brackets. No hedging. No invented numbers.

Return ONLY this JSON:

{json.dumps(schema, indent=2)}"""


def build_triage_prompt(candidates: list[dict]) -> str:
    """Ask which candidates are worth a full note at all.

    Cheaper than writing notes for everything, and it is where a bad candidate
    should die.
    """
    lines = [
        "You are triaging candidate equities for idea notes.",
        "An idea is only worth writing if there is a specific, checkable reason the",
        "price is wrong -- a valuation gap, a revision trend, a credit cycle, a",
        "catalyst. Rank the candidates and reject the ones with no edge.",
        "",
    ]
    for c in candidates:
        lines.append(
            f"- {c.get('symbol')} ({c.get('name')}): price {c.get('price')}, "
            f"fwdPE {c.get('fwd_pe')}, P/S {c.get('ps')}, "
            f"EPS trend {c.get('eps_trend')}, revisions {c.get('eps_revisions')}, "
            f"next earnings {c.get('next_earnings')}, "
            f"themes {', '.join(c.get('themes') or []) or 'none'}"
        )
    lines.append("")
    lines.append(
        "Return JSON: {\"ranked\": [{\"symbol\": str, \"direction\": \"long|short\", "
        "\"conviction\": 1-5, \"one_line_reason\": str, \"reject\": bool, "
        "\"reject_reason\": str|null}]}"
    )
    return "\n".join(lines)
