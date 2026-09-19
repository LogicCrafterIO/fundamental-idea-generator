# The format, distilled

Every rule below was reverse-engineered from [`orcl.md`](orcl.md) and
[`omf.md`](omf.md), then verified against live data. Anything marked
**verified** is checked by `fig demo` or reproduced by the code paths named.

The single overriding requirement: **the reasoning must be short and simple.**
The two references are 20 words of Description and 2–5 one-sentence reasons. That
is the product, not a summary of it.

---

## 1. Anatomy

```
Ticker: <SYMBOL>

Description
<one line: what the business is now>

Reasons
1) <one sentence: why the price is wrong>
2) ...

Quants
<the numbers, uneditorialised>

Structuring
<the option legs, then 1–3 sentences of reflection>
```

Sections never reorder, and no section is ever dropped.

---

## 2. Description

One line. It says what the business **is now**; where that has changed, the
change leads.

| | words | note |
|---|---|---|
| ORCL | 20 | "Formerly Databases and SaaS, Oracle is now more focused on Infrastructure as a Service, which of course includes data centers." |
| OMF | 4 | "Nonprime consumer loan lender" |

Four words is a complete Description. The length follows the business — so the
rule is **as few words as the business allows**, not a word quota. Never pad it
to look substantial. Budget: ≤ 30 words (enforced by `fig lint`).

## 3. Reasons

Numbered, each **one sentence** and each a *claim about mispricing* — never a
fact dump. Three shapes recur:

1. **Comparative** — a multiple set against a named peer.
   > "it's not priced like Google, which is trading at a Forward PE of 25 while Oracle is at a Forward PE of 17"
2. **Market-is-wrong** — the consensus is mispricing a specific mechanism.
   > "The market is overpricing the effects of GPU depreciation and debt servicing"
3. **Causal chain** — X leads to Y leads to a re-rating, with thresholds.
   > "If NCO [net charge offs] go from 7% now to 10% in Feb or March earnings then it could rerate significantly to a PE of 4-5"

Every reason carries **a number, a named comparison, or a mechanism**. A reason
that would apply to any company in the sector is deleted. Budget: ≤ 40 words,
2–5 reasons (both enforced by `fig lint`).

## 4. Jargon gets a bracket gloss

Plain words first, or in brackets immediately after the term:

```
NCO [net charge offs]
the legislation [known as a legal company pretending to be a software company]
SNOW [which has the software and data but not the infra and is trading at 20x PS]
```

The bracket may define a term *or* carry a short aside explaining relevance.
`fig lint` flags unglossed acronyms from the list in `fig/prompts.py`
(`GLOSS_REQUIRED`).

## 5. Quants

Raw numbers, no adjectives. Order: price, market cap, forward PE, EPS trends,
EPS revisions, then optional quarter-specific facts.

```
Price: 60.94 USD
Market Cap: 7.07B
Fwd PE: 7.7
EPS trends: slightly down over the last 7 days
EPS revisions: Split equally, with 5 up and 10 down over last 30 days
Q2 reported increasing provisions and managed receivables => more loans made
```

Two lines are *generated prose*, produced by `fig.quants.describe_trend()` and
`describe_revisions()` from the underlying consensus numbers so the wording can
never contradict the data. The `Q2 reported ...` lines are pulled from the
quarterly statements by `fig.quants.fundamental_deltas()`.

> **Note on "Split equally, with 5 up and 10 down".** 5 up and 10 down is not
> even, so the adjective and the counts disagree. The generator emits an accurate
> tilt word (`tilted lower`, `evenly split`, `tilted higher`, `all up`,
> `all down`) and always prints the raw counts, since the counts are checkable
> and the adjective is not.

### Forward PE is ambiguous — always state the basis

The references quote a single unlabelled `Fwd PE`, and it cannot be reproduced to
the decimal from free data because the basis is unstated. Live ORCL has three
defensible values:

| basis | value | source |
|---|---|---|
| current FY consensus EPS (8.14) | **18.13** | `price / eps_trend['0y'].current` |
| next FY consensus EPS (10.99) | **13.43** | yfinance `info['forwardPE']` |
| Nasdaq FY-May-2027 consensus (6.65) | 22.20 | `api.nasdaq.com analyst/earnings-forecast` |

The ORCL reference's 17.7 at price 150 implies current-FY EPS of ~8.47, so it is
the **current-FY** basis. The OMF reference's 7.7 implies EPS ~7.9, which matches
neither free basis today (current-FY 7.09 → 8.57; next-FY 8.59 → 7.08) — most
likely consensus drift since the note was written.

**Practice:** `fig` reports `fwd_pe` (current FY, the default) and `fwd_pe_1y`,
and any peer comparison must use one basis consistently. `fig prompt` instructs
the writer to state the basis.

### The ORCL note's peer comparison mixes bases

Worth knowing, because it changes the conclusion. Live values on 2026-09-19:

| | current-FY PE | next-FY PE | P/S |
|---|---|---|---|
| ORCL | 18.13 | 13.43 | 6.2 |
| GOOG | 16.72 | 23.21 | 9.4 |
| SNOW | 149.9 | 110.3 | 21.6 |

The ORCL note claims "it's not priced like Google, which is trading at a Forward
PE of 25 while Oracle is at a Forward PE of 17". Its GOOG figure matches GOOG's
**next-FY** basis (23.21) while its ORCL figure matches ORCL's **current-FY** basis
(18.13). Mixed bases make the comparison unreliable — and on a like-for-like
current-FY basis it actually *inverts*: ORCL at 18.13 is slightly more expensive
than GOOG at 16.72. Only on the next-FY basis is ORCL genuinely the cheaper name
(13.43 vs 23.21).

The same note's P/S comparison, by contrast, checks out cleanly: SNOW 21.6x vs
ORCL 6.2x against the stated "20x ... about 7x". So the fix is narrow — when a
reason sets two multiples against each other, quote both from the same row.

## 6. Structuring

The legs go in a **tab-separated** table (a broker ticket paste, not markdown):

```
Long	CALL	18-Dec-26	$ 155.00	3	$ 150.00	100	$ 15.55	$ -	$ -	$ -	$ 4,665.00
Short	CALL	16-Oct-26	$ 155.00	2	$ 150.00	100	$ 6.44	$ -	$ -	$ -	$ (1,288.00)
```

Columns: side · type · expiry (`DD-Mon-YY`) · strike · qty · underlying ·
multiplier · option price · three unused cash columns · total. Negatives are
parenthesised; the premium paid is positive, the credit received negative.

Then 1–3 sentences of reflection **in the author's voice**, reasoning about the
size of the credit. It may be informal and may ask a question:

> "Fairly fat credit, even if I halved it, it would be 13%. I also find it a bit hard to find non-consensus longs, stuff is getting stupid expensive imo."

> "The credit received is very slightly above the 10% floor for credits, but I could sell 1 or 2 more to increase that. ... lmk if my thinking on this is wrong."

Uncertainty is allowed **here only**, and only about the trade construction —
the thesis itself stays confident.

---

## 7. Structure construction rules (**verified**)

All four legs of both references are reproduced from live chains by
`fig.options.build_structure()`; `fig demo` asserts it.

1. **Shape** — buy one far-dated leg, sell a nearer-dated leg at the *same*
   strike. Long idea → calls, short idea → puts.
2. **The short leg expires before the catalyst.** ORCL short 16-Oct-26 vs next
   earnings 11-Dec-26; OMF short 16-Oct-26 vs 30-Oct-26. The short decays without
   event risk.
3. **The long leg expires after the catalyst.** ORCL long 18-Dec-26 sits just past
   the 11-Dec-26 report; OMF long 19-Feb-27 sits past the late-Jan-27 report.
   `--catalyst-index 1` selects the *second* upcoming report, which is what the
   OMF note means by "allowing two quarters for the worsening consumer debt story
   to play out".
4. **Expiries are standard monthlies** — the third Friday of the month. Oct 16,
   Nov 20, Dec 18 and Feb 19 are each a third Friday. Weeklies are listed but
   skipped for liquidity.
5. **Strike = nearest common OTM strike to ~4% out of the money**, and it must be
   listed in *both* expiries. OMF's 60 strike exists in the Oct-26 chain but not
   the Feb-27 chain, which is why 57.5 was used.
6. **Size ≈ $4,500 of long premium** — `long_qty = capital ÷ (premium × 100)`.
   ORCL 3 × 15.55 × 100 = $4,665; OMF 14 × 3.20 × 100 = $4,480.
7. **Credit ratio**, the definition that makes both notes' prose work:
   ```
   credit ratio = short premium collected ÷ long premium paid
   ```
   - OMF: 0.65 × 7 ÷ (3.20 × 14) = **10.16%** → "very slightly above the 10% floor"
   - ORCL: 6.44 × 2 ÷ (15.55 × 3) = **27.6%** → halved is 13.8% → "even if I halved it, it would be 13%"
8. **Floor = 10%**, and short quantity is solved to a target above it.

### The floor is a mid-price number

Worth knowing: the 10% floor holds at **mid prices only**. Priced against you
(long at ask, short at bid), the OMF note's 7 shorts give **8.75%**, and it needs
8 shorts to clear 10%. `fig structure` prints both the mid and conservative
ratios and a full credit ladder, because the honest number is the conservative
one.

---

## 8. Voice

- Short, direct, first person where it helps ("I find it a bit hard to find
  non-consensus longs").
- Confident on the thesis, candid about the trade.
- No hedging stacks ("could potentially", "might possibly").
- No empty intensifiers ("very", "really").
- No definitions the reader already knows, and no throat-clearing openers.

`fig lint` enforces the measurable parts and scores 0–100.
