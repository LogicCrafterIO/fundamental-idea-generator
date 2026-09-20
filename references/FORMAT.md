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

Catalyst
<the exact earnings date, where it came from, then one line on why that date decides the thesis>

Reasons
1) <one sentence: why the price is wrong>
   Source: [S3] <provider> (<date>) <url>          <- see §3b
2) ...

Watch
- <variable>: <reading that confirms>; <reading that breaks it>   <- see §3e

Quants
<the numbers, uneditorialised>

Structuring
<the option legs, then 1–3 sentences of reflection. OPTIONAL>
```

The first four sections never reorder, and Watch follows the reasons it tests.
**Structuring is optional**: in the two references the trade construction matters
because it says how to express the idea, but the idea itself is the Description, the
Catalyst and the Reasons. A note with no usable option chain is still a note;
`fig generate` writes it and states the omission rather than failing.

---

## 1a. Catalyst

The single most important line after the Description, because it says *when the
idea gets settled*. The reference states it inside its Structuring block:

> "A 40% downside is possible if we target earnings in late January, allowing two
> quarters for the worsening consumer debt story to play out, resulting in a $36
> price target."

That sentence does three jobs: **the date**, **the mechanism** (credit needs two
quarters to deteriorate), and **the payoff** ($36). Only the date is a fact; the
other two are the writer's reasoning. So the section splits exactly that way:

```
Catalyst
2026-10-30 (Friday, before the open), 41 days out -- from the earnings calendar, consensus EPS 1.88.
Credit costs must jump enough to push EPS below the 1.88 consensus, confirming the deterioration.
```

* **Line 1 is measured, never written by the model.** Date, weekday, session
  (before the open / after the close), days remaining, whether the date is
  *scheduled* (published in the earnings calendar) or *estimated* (projected from
  the company's own reporting gap — and said so), and the consensus for that
  report. `fig lint` errors if the stated date does not appear in that line,
  because a restated or rounded earnings date is the most damaging error a note
  can carry.
* **Line 2 is the writer's.** What must show up in that report for the thesis to
  be right. ≤ 25 words, and it must not simply restate the date's facts.

Supporting facts are supplied to the writer, since they are what make a date
credible: the company's cadence (median gap between reports), whether it reported
in the same calendar slot a year ago, and its recent record against consensus —
OMF, for instance, has **beaten consensus in each of the last four reports**, so
"the bar is already high and a miss is what moves the stock" is a real caution on
a short thesis, and it is stated.

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

## 3a. A discount is not a thesis

Enforced by `fig lint` as an **error**, and by the screener. The rule:

> Premium multiples usually exist for a good reason. A stock trading at a discount
> is not automatically a long, and an expensive stock is not automatically a
> short. If a Reason cites a multiple, it must also say what the market is
> **missing** or what will specifically **change**.

The ORCL reference is the cautionary case, and the origin of this rule. Its
reason 1 -- *"it's not priced like Google, which is trading at a Forward PE of 25
while Oracle is at a Forward PE of 17"* -- is a discount observation, and §5 shows
the comparison mixes bases and actually inverts like-for-like. Its reason 2 is the
better shape: a mechanism with the multiple left out entirely.

Three forms, worst to best:

| form | example | verdict |
|---|---|---|
| bare level | "It trades at 12x, a discount to peers at 20x." | **error** |
| juxtaposition | "Revenue rose 31% yet it trades at 12.3x." | **error** -- this has not explained why the market pays only 12.3x |
| mechanism, multiple as consequence | "At 10.76x, below its 13.16x current-year, **because the market is missing** that expanding fee pools will lift revenue." | passes |

A forward-PE roll-forward is a special case worth naming: "next-FY 39.5 is below
this year's 43.5" is true of **every** company with any earnings growth, so it
distinguishes nothing. It reads like a finding and is not one.

Short theses are exempt. A high multiple on a business whose numbers are
deteriorating is a standard short argument, not this fallacy -- see the GIS and
OMF notes, where the multiple is evaluated *against* a named change.

## 3b. Every reason names its source

A reason the reader cannot check is a reason the reader has to take on trust, and
this format exists to be checkable at a glance. So each reason carries the evidence
it rests on, printed directly beneath it:

```
3) Because QNX royalties are contracted before the cars ship, the 0.19 FY
   consensus already reflects the last four quarters' actuals.
   Source: [S3] Nasdaq company financials (5/31/2026) https://www.nasdaq.com/market-activity/stocks/bb/financials
```

The rules, all enforced (`fig lint`, `fig generate`):

- **The writer cites ids, never URLs.** The packet numbers every piece of evidence
  (`S1`, `S2`, ...) and prints the register. An id resolves against that register,
  so a source the packet cannot vouch for is *dropped* rather than printed -- which
  is the difference between a citation and a plausible-looking link.
- **The tool owns the metadata.** Provider, date and URL come from the packet. The
  model chooses *which* evidence supports *which* reason; nothing else about the
  citation passes through it.
- **A reason with no source is an error**, whenever the packet registered any. If
  the tool supplied no sources it has no standing to demand them, which is why the
  offline fixtures and the pre-source notes are unaffected.
- **A URL in the reason prose is an error.** It spends the 40-word budget on a link
  that belongs in the source line, and it is the one place a fabricated URL can
  look like evidence. Any URL the packet does not contain is removed on the way in
  and recorded.
- **A figure must be in the source it cites.** A warning, not an error -- a reason
  may legitimately lean on a source for its claim and not for its number -- but it
  never passes silently. "In the packet somewhere" is weaker than it sounds: the
  reader being sent to `S7` has to find the figure in `S7`. The check reports only a
  figure that is in the packet but under a **different** id, and names that id, so
  what it prints is a miscitation rather than a rounding artefact.
- **A figure has to be earned.** Digits inside a date or a URL are not evidence that
  a number is supported ("25" from `Jun 25, 2026` should not vouch for `25.38%`), and
  rounding is allowed only in the writer's direction: a note may round 43.2 to "43",
  but a note that writes "6.8" is not grounded by an unrelated 7.0.

The note's footer states both verdicts, so a reader does not have to run anything:

```
Grounding: all 12 figures in the prose appear in the evidence.
Source grounding: 2 figure(s) are in the packet but not in the source cited for
them -- Reason 2: "8%" is cited to S19 but appears in S10, S17; ...
```

## 3c. A revision count is not a revision of the number

The most expensive reading error this format has actually produced, from the BB
note:

> "five analysts raised estimates in 30 days with none cutting, the 0.19 FY number
> is stale"

The two halves are the same fact read twice. If five analysts raised, then 0.19 is
the number they raised **to** -- which makes it the freshest estimate available, not
a stale one. The packet agreed: the FY level was 0.18857 thirty days earlier and
0.18857 on the day, so the raises were smaller than the rounding of the level and
nothing had moved.

Two mechanical defences, because the prose failure is predictable:

1. **`LEVEL READING`** is stated in the evidence next to the counts: how many
   analysts moved, and whether the *level* moved. Where the level is unchanged and
   the counts are up, the line says outright that the consensus is current.
2. **`TRAILING CHECK`** compares the last four reported quarters' EPS with the
   current-FY consensus, when the two are comparable. On BB they were equal --
   0.04 + 0.06 + 0.05 + 0.04 = 0.19 against a 0.18857 consensus -- so the beat
   streak was already *in* the number, and citing it as evidence that the number is
   wrong inverts what it shows.

`fig lint` errors on the conjunction: a staleness claim (`stale`, `out of date`,
`too low`, `hasn't caught up`) plus revision-count evidence plus a level that did
not fall. Each half alone is legitimate -- "the consensus is too low" is an ordinary
long argument and "5 up and 0 down" is an ordinary fact -- so only the conjunction
is flagged, and short theses are unaffected.

---

## 3d. A sequential move is not a trend

The note that prompted this section said Paychex's May 2026 quarter showed revenue
down 11.2% and net income down 24.9% "sequentially", and concluded the market was
pricing a recovery the numbers did not show. Every figure was right and every figure
was sourced. The same quarter grew **12.5% in revenue and 41.5% in net income** year
over year.

A payroll processor's fiscal year ends in May: the February quarter is the seasonal
peak (year-end tax filing), so a decline into the May quarter is the calendar, not a
business. And the sequential comparison cannot see a mid-year acquisition, a rate move
or a divestiture at all. The rule is therefore not "never quote a sequential move" --
it is that the pair is the fact:

```
QUARTER: SEQUENTIAL vs SAME QUARTER A YEAR AGO                       [S3] [S2]
  Total Revenue: 1.61B in 2026-05-31 (-11.2% QoQ) vs 1.43B in 2025-05-31 (+12.5% YoY)
  Net Income: 420.6M in 2026-05-31 (-24.9% QoQ) vs 297.2M in 2025-05-31 (+41.5% YoY)
  ...
  NOTE: Total Revenue, Net Income, Operating Income move in opposite directions
  sequentially and on the year. A sequential move is NOT a trend here -- quote the
  year-over-year comparison with it, and do not present the sequential fall as
  deterioration.
```

Three mechanical defences, again because the prose failure is predictable:

1. **`QUARTER: SEQUENTIAL vs SAME QUARTER A YEAR AGO`** puts both comparisons on one
   line per statement line, so the writer cannot see one without the other. The Nasdaq
   tables stop at four quarters and cannot support this; the year-earlier column comes
   from the yfinance statement series (`fig.quants.yoy_deltas`).
2. **`ANNUAL`** gives the fiscal-year comparison, which is the one a deal, a rate move
   or a calendar cannot flatter on its own. Paychex FY26 revenue: 5.57B to 6.51B, +16.9%.
3. **The Quants panel leads with the pair** where the two disagree: `Total Revenue -11%
   quarter over quarter but +12% year over year (2026-05-31)`. The half-line it
   replaces -- "net income decreasing 25% quarter over quarter" -- is suppressed,
   because on its own it is true and misleading.

`fig lint` errors on `reason_sequential_without_year`: a reason that quotes a
sequential move for a line whose year-earlier comparison moves the other way, without
stating the annual figure. Where the two agree the sequential move is only flagged as
`reason_sequential_unpaired`, a warning.

---

## 3e. Watch: what would prove the note wrong

A reason says why the price is wrong. Watch says which numbers at the catalyst decide
whether that is true, and it is required when the print is within 21 days
(`WATCH_REQUIRED_WITHIN_DAYS`), because that is when a reader can act on it:

```
Watch
- Organic revenue excluding Paycor: confirms if it grows below the 16.9% FY rate; breaks if it reaccelerates.
- Client worksite employees and PEO [professional employer organisation] headcount: confirms if growth slows from the July pace; breaks if it reaccelerates.
- FY27 EPS guidance: confirms if below the 5.96 consensus; breaks if above.
- Interest expense: confirms if it keeps rising above the 155.7% FY pace; breaks if it flattens.
```

2-4 lines, each one a *variable* plus both readings, ranked by information value.
The useful order is: organic versus acquired growth, revenue excluding the
acquisition, client or volume counts, revenue per client, the rate-linked line, the
guidance range, the post-deal margin, and only then the end-market commentary. A line
that restates a reason is not a test; a line with only one reading is not a test
either (`watch_no_test`). A note with no dated catalyst omits the section entirely.

The section is checked, not trusted: `watch_missing` is an error when the catalyst is
close, `watch_too_long` and `watch_count` are warnings, and the figures in it are
grounded like any other prose.

---

## 3f. An acquisition is not organic growth

Reported growth in a period a deal landed in is partly bought, and a thesis that
treats it as demand is measuring the wrong thing. Paycor supplied roughly 12% of
Paychex's FY26 revenue growth; a note arguing "declining small-business hiring means
declining Paychex revenue" was arguing from a number that mostly reflected an
acquisition.

The evidence does not depend on the writer remembering the deal. `DEAL ACTIVITY` is
derived from the balance sheet, where a step change in goodwill or intangibles is the
footprint of an acquisition:

```
DEAL ACTIVITY (an acquisition landed in these periods)                       [S4]
  Other Intangible Assets: 194.5M -> 1.95B (2024-05-31 to 2025-05-31, fiscal year, +901.2%)
  Any growth in the periods at or after 2025-05-31 includes acquired revenue, so it is
  NOT organic growth. If a reason argues from growth, say how much of it is acquired;
  if it argues from a decline, check whether the deal year flatters the comparison.
```

`fig lint` errors on `reason_ignores_deal` when the balance sheet shows a deal and no
reason mentions one. The detector reads both the annual and the quarterly series
(`fig.quants.deal_activity`), and only steps within the most recent periods count, so
an acquisition from years ago is not raised as today's news.

---

## 3g. One metric per claim, and the latest reading of it

Two survey questions are two metrics even when they share a theme. The PAYX note's
lead reason joined "job openings fell to 29%, the lowest since May 2020" (the NFIB
May *job openings* question) to "51% report few or no qualified workers" (the NFIB
June *qualified workers* question) as if they were one trend. Both figures were
correctly cited. The packet also held a July reading in the opposite direction
(employment plans up 9 points to a net 20%), and a June reading of hiring difficulty
at its highest since 2024 -- neither appeared.

So `fig lint` (via `check_source_grounding`) reports
**`Superseded readings`**: a reason that rests on a dated reading of a recurring
series, when the packet holds a later reading from the same provider whose direction
is the opposite. The pair must be about the *same subject* -- wording overlap of at
least 25% on content words -- so two unrelated articles from one site are not treated
as one series. The direction is read from the claim's first sentence rather than the
whole entry, because the second sentence is a note-style gloss written in the
direction of the thesis and counting it turns a reversal into a tie.

---

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

**This whole section is optional.** It is the most expensive part of a note to get
right — it needs a listed chain, a common strike, two standard monthly expiries
straddling the catalyst, and a credit ratio over the 10% floor — and it is the
least important part of the idea. When it cannot be built, `fig render` prints a
single bracketed line naming the reason (for example
`[no option structure: no usable catalyst for SNX]`) so the gap is visible and
the note still stands on its Catalyst and Reasons.

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
