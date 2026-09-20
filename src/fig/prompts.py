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
    "catalyst_why": 25,
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

Catalyst
<Supplied date line, verbatim.>
<One sentence of your own: why THAT date is the moment this thesis gets tested.
<= 25 words. Tie it to the reason -- what has to show up in that report.>

Reasons
1) <One sentence. A claim about why the price is wrong.>
2) <...>

Quants
<The supplied facts, verbatim. Do not editorialise here.>

Structuring
<Optional. The supplied legs as a table, then 1-3 sentences in the author's voice
reasoning about the size of the credit and the risk. Omit this whole section if no
legs were supplied.>

HARD RULES

1. BREVITY IS THE PRODUCT. If a word can be cut without losing meaning, cut it.
   Description <= 30 words. Each reason <= 40 words. Catalyst line <= 25 words.
   Prefer 3 reasons over 5. A shorter note that says the same thing is always
   better. Never pad.

2. PLAIN WORDS ONLY. Write so a smart person outside finance understands. Say
   "loans written off" before you say "charge-offs". No jargon as decoration.

3. GLOSS EVERY ACRONYM in square brackets, in plain words, on first use:
   "NCO [net charge offs]", "RPO [contracted work not yet billed]".
   A bracket may also carry a short aside, as in the reference:
   "the legislation [known as a legal company pretending to be a software company]".

4. EACH REASON MUST CARRY ONE OF: a number, a named comparison to another company,
   or a causal mechanism (X leads to Y leads to Z). No generic virtues. If a reason
   would apply to any company in the sector, delete it.

4a. A DISCOUNT IS NOT A THESIS. This is the easiest mistake to make and the most
   expensive. "It trades at 12x while peers trade at 20x" is an observation, not a
   reason -- premium multiples usually exist for a good reason, so a low multiple
   is not by itself a case for the stock to rerate upward. Cheap things are often
   cheap because something is wrong. If you cite a multiple, you must also say
   what the market is MISSING or what will specifically CHANGE to close the gap.
   The same applies in reverse: "expensive" is not a short thesis unless you say
   what the market is overpaying for and why that assumption breaks.

4c. NEVER CHANGE THE DIRECTION OF A TREND. The FORWARD TRENDS evidence states a
   direction; keep it exactly. If it says hiring is cooling while still growing,
   do not write "hiring accelerated". Upgrading a trend to fit your thesis is the
   single easiest way to make a note wrong while sounding well-evidenced, because
   the reader cannot tell the difference without opening the source.

4d. DO NOT READ A REVISION COUNT AS A REVISION OF THE NUMBER. "Five analysts
   raised estimates in 30 days" counts analysts moving; it does not mean the
   consensus level moved. The LEVEL READING line tells you which it is. If the
   level is unchanged, the consensus is current -- the raises were smaller than
   the rounding of the number -- so you cannot call it stale, outdated or too low
   on the strength of the count. Where the evidence gives a TRAILING CHECK, read
   it before arguing the consensus is too low: if the last four reported quarters
   already add up to it, the beat streak is IN the number.

4b. THE QUALITATIVE HALF MATTERS. Numbers describe what already happened. A strong
   reason often explains a GAP: why an obvious problem has not yet shown up in the
   reported figures, or why the reported strength cannot last. The FORWARD TRENDS
   evidence exists for exactly this -- prefer a grounded end-market trend over
   another restatement of a trailing move. Say who the customers are and what is
   happening to them.

5. NO HEDGING STACKS. Not "could potentially", "might possibly", "it seems".
   State the claim. Uncertainty belongs only in the Structuring reflection, and
   only about the trade construction.

6. QUOTE NUMBERS ON A STATED BASIS. When comparing multiples to another company,
   both must be the same basis. If the evidence gives you two forward-PE bases,
   pick one, and keep it consistent across every comparison in the note.

7. DO NOT INVENT. Every number must come from the supplied evidence. If something
   needed for a reason is missing, write the reason without it or omit the reason.
   Never estimate a figure that was not supplied.

8. THE CATALYST is the point of the note. The date is supplied -- copy it exactly,
   never restate it from memory and never round it. Your one sentence explains why
   that report is when the thesis is decided: what must show up in the numbers for
   the idea to work. Do not repeat the date's facts back; say what it will prove.

9. The Structuring reflection is the only place for voice. One or two sentences:
   whether the credit is fat enough, how many more shorts could be sold, what the
   floor test says. It may end with a question. Keep it short. If no legs were
   supplied, omit Structuring entirely and put nothing in its place.

10. EVERY REASON NAMES ITS SOURCES. The evidence is numbered -- every block, every
   headline and every trend carries an id like [S3], and the SOURCES list at the
   end states what each one is. Return "reason_sources" as a list of lists, one
   entry per reason, holding the ids of the evidence that specific reason rests
   on. Cite the source that actually supports THAT reason, not the whole list.
   Never write a URL or a bare id into the reason prose itself: it costs words and
   an uncited id is dropped. A reason with no source is rejected.

11. A FIGURE MUST BE IN THE SOURCE YOU CITE. If a reason quotes a number that
   appears in one source, cite that one. Citing a headline for a figure that comes
   from the statements is the same class of error as inventing the figure, because
   the reader who checks it will not find it.

12. A SEQUENTIAL MOVE IS NOT A TREND. The QUARTER block gives every line's
   quarter-over-quarter move AND its move against the same quarter a year earlier.
   If you quote one, quote the other in the same sentence. When the two point in
   opposite directions the sequential move is seasonality or a deal, not
   deterioration -- and the note must say what the annual comparison shows. A note
   once reported "revenue down 11.2% sequentially" about Paychex's May quarter,
   which grew 12.5% year over year: every figure in it was sourced and the
   conclusion was backwards. If you cannot state both, drop the move.

13. AN ACQUISITION IS NOT ORGANIC GROWTH. When the DEAL ACTIVITY block appears, a
   deal closed in that period, so reported growth inside it is partly bought.
   Never attribute acquired revenue to end-market demand: name the deal and say
   which part of the growth it explains, or argue from a line the deal cannot
   flatter (margins, client counts, interest on client funds, the year-earlier
   comparison). Treat the deal year as the base case, not as evidence of momentum.

14. ONE LINK FROM MECHANISM TO CATALYST. A reason's chain must reach the catalyst
   date in one or two steps, and every step must be evidence supplied above. No
   speculative multi-year chains ("AI agents will eventually mean far fewer small
   companies"): a payoff years away cannot decide a dated report, and a long chain
   cannot be checked. If the chain is longer than two links, cut it or drop it.

15. ONE METRIC PER CLAIM. Two survey questions are two metrics even when they share
   a theme: "job openings fell to 29%" and "51% report few or no qualified workers"
   are separate NFIB questions and do not describe one trend. When the evidence
   holds several readings of the same driver, use the LATEST and say what changed
   from the earlier one -- never pick the reading that fits and leave the newer one
   out. If a driver reversed in the newest reading, that reversal is the fact.

16. SAY WHAT WOULD PROVE YOU WRONG. When the catalyst is near, the Watch block names
   2-4 variables that decide the idea at that report, each with the reading that
   confirms the thesis and the reading that breaks it. Use the variables with the
   most information value -- organic versus acquired growth, revenue excluding the
   acquisition, client or volume counts, the rate-linked line, guidance, margin.
   A Watch line is not a restatement of a reason and not a hedge: it is what the
   reader should check first, and it must be checkable against the report itself.

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
        "catalyst_why": "<=25 words: what the report must show for this thesis to work",
        "reasons": ["one sentence each, each carrying a number, a comparison, or a mechanism"],
        "watch": [
            "2-4 lines, one per variable, each <= 25 words: name the variable, the "
            "reading that confirms and the reading that breaks the thesis (rule 16). "
            "Required when the catalyst is within 21 days; omit the key entirely if "
            "there is no dated catalyst."
        ],
        "reason_sources": [
            ["S3", "S7"],
            ["S1"],
            "one inner list per reason, in the same order, holding the ids of the "
            "evidence that reason rests on (rule 10). No URLs, no prose.",
        ],
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
            "reflection": "1-3 short sentences in the author's voice about credit size and risk; omit if no legs were supplied",
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
Gloss every acronym in square brackets. No hedging. No invented numbers. Every
reason cites the ids of the evidence behind it in "reason_sources", aligned to the
reasons list -- cite what supports that reason, and put no URLs in the prose.
Before you answer, check the QUARTER block: every sequential move you use needs the
year-over-year move beside it, and every growth claim in a DEAL ACTIVITY period
needs the acquisition named.

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
