# fundamental-idea-generator

Pulls current US equity fundamental news from **free** sources and turns it into
short ticker idea notes in a fixed, terse house format — the format of the two
writeups in [`references/`](references/).

The point is not the prose. It is the **distillation**: the Description, the
Catalyst and each Reason are hammered down to simple language and as few words as
possible, so the reasoning is checkable at a glance. `references/FORMAT.md` states
the rules, and `fig lint` enforces the measurable ones.

**The catalyst is the trade.** A note says exactly when the idea gets settled, and
why that report is the moment it is proved or broken. Option legs are a
second-order detail: they say how to express the idea, not what it is, so they are
optional and a note is still written when no usable chain exists.

```
Ticker: OMF

Description
Nonprime consumer loan lender                                    <- 4 words

Catalyst
2026-10-30 (Friday, before the open), 41 days out -- from the
earnings calendar, consensus EPS 1.88.                           <- measured
Credit costs must jump enough to push EPS below the 1.88
consensus, confirming the deterioration.                         <- the reasoning

Reasons
1) Nonprime consumer loans are likely to worsen as job losses increase due to AI
   Source: [S17] csoonline.com (2026-09-17) https://www.csoonline.com/...
2) If NCO [net charge offs] go from 7% now to 10% in Feb or March earnings then
   it could rerate significantly to a PE of 4-5 as earnings get hit.
   Source: [S3] Nasdaq company financials (6/30/2026) https://www.nasdaq.com/...
```

Every reason names the evidence behind it, and the note is filed under the side it
argues: `research/longs/` or `research/shorts/`.

---

## The other screener: pure qualitative themes

This repo also holds a **second, independent screener** in
[`qualitative/`](qualitative/), which asks a different question and shares only the
plumbing (Nasdaq for the listed names, yfinance for market cap, the same Ollama key
for search and generation).

It screens for a **story**, not a trade. Its only two quantitative inputs are a
**$100 share-price cap** and a **$1B market-cap floor** — no multiple, no estimate
revision, no momentum, no catalyst. For each name it extracts the **exact revenue
streams**, researches trends through the **three parts of a business** (trending
demand, how it's sold, how it's made), and aggregates those trends into **themes**
ranked by size, speed and impact, listing the tickers each theme helps and hurts.

Its two outputs are [`qualitative/themes/THEMES.md`](qualitative/themes/THEMES.md)
(the master theme file) and one writeup per ticker in
[`qualitative/tickers/`](qualitative/tickers/). See
[`qualitative/README.md`](qualitative/README.md) for the framework, the rubric and
the limits.

---

## Quickstart

```bash
python3 -m venv .venv
.venv/bin/pip install -e .

echo 'OLLAMA_API_KEY=...' > .env                # enables search + generation

.venv/bin/fig demo                             # verify the engine vs the references
.venv/bin/fig themes                           # what stories are live right now
.venv/bin/fig screen --watchlist ORCL OMF      # triage candidates, ranked
.venv/bin/fig screen --max-price 75 --min-market-cap 1b   # a tighter universe
.venv/bin/fig search "regional bank credit"    # web search via the same key
.venv/bin/fig generate OMF --directions short  # write a finished note
.venv/bin/fig lint research/shorts/omf.json    # enforce brevity/plain language
.venv/bin/fig render research/shorts/omf.json  # print in reference layout
.venv/bin/fig organize                         # file flat notes under longs/shorts
.venv/bin/fig attribute                        # backfill sources on older notes
```

`fig demo` is the regression test: it rebuilds the ORCL and OMF option legs from
live chains and fails if they no longer match the references.

---

## Every reason names its source

The note's promise is that its reasoning is checkable at a glance, and a claim with
nothing behind it cannot be checked at all. So each reason carries the evidence it
rests on, printed directly under it:

```
1) Investment banking and capital markets revenue rose 35% quarter-over-quarter
   to $2.2B in Q2, so the fee engine is already running; the stock fell only
   because asset management lost money.
   Source: [S19] seekingalpha.com (2026-06-26) https://seekingalpha.com/article/...
```

The mechanism is the same one that keeps numbers honest, applied to provenance:

- **The tool numbers the evidence.** `packet.source_catalogue` registers every block
  of evidence with an id, a provider, a date and a real URL -- the fundamentals
  (`S1`), the consensus (`S2`), the statements (`S3`), the catalyst (`S4`), each
  headline, each end-market trend, the chain. `to_prompt_context` tags every line
  with its id and prints the register at the end. The register and the prompt are
  built from one list with one limit, so the evidence the writer was shown and the
  evidence a citation can resolve against cannot drift apart; a packet carries 17-25
  feed headlines and 12-15 search results, and all of them are citable.
- **The model cites ids, never links.** It returns `reason_sources`, aligned to the
  reasons. Provider, date and URL are resolved from the packet, so **a URL that the
  evidence does not contain cannot reach a note**: an unknown id is dropped and
  recorded, and a URL written into the prose is removed and recorded. That is the
  one failure a reader cannot detect -- a fabricated link under a real-looking
  claim -- so it is not left to the prompt.
- **A reason with no source is an error**, so the repair loop has to fix it.
- **A figure must be found in the source it cites** (`lint.check_source_grounding`).
  "In the packet somewhere" is weaker than it sounds once a reason names its
  evidence: the reader sent to `S7` has to find the number in `S7`. The check reports
  only figures that are **in the packet but in a different source**, and names that
  source -- `Reason 3: "3.8%" is cited to S2 but appears in S4, S18`. A figure in no
  source at all is left to `check_grounding`, because a derived figure has no home
  and reporting those would bury the miscitations. Warning, not error: a reason may
  lean on a source for its claim and not for its figure.
- **A figure has to be earned.** `check_grounding` harvested numbers from dates and
  URLs, so a bare `25` inside `Jun 25, 2026` or in a link's path could vouch for a
  `25.38%` that the packet never contained -- which is exactly how the invented
  figure in the BB note below passed the check for a week. Dates, URLs and the
  three-digit heads of four-digit years are now excluded, and rounding tolerance runs
  one way only: a note may round 43.2 down to "43", but "6.8" is not grounded by an
  unrelated 7.0 market cap.

`fig attribute` backfills this onto notes written before the format had it. The
reasons are **not** rewritten -- re-rolling the prose to attach a citation would
change the thing being cited -- so it asks one question per existing reason (which
of this packet's sources does it rest on?) and verifies the answer. Notes it cannot
attribute honestly are listed as left uncited rather than given a plausible source.

### A revision count is not a revision of the number

The format's most expensive reading error, found in its own BB note:

> "five analysts raised estimates in 30 days with none cutting, the 0.19 FY number is stale"

Those are the same fact read twice. Five analysts raising means 0.19 is the number
they raised *to*, which makes it the freshest estimate there is. The packet agreed
with the opposite conclusion: the FY level was 0.18857 thirty days earlier and
0.18857 on the day, so the raises were smaller than the rounding of the level --
nothing had moved. And the beat streak cited alongside it was already *in* the
number: the last four quarters' actuals (0.04 + 0.06 + 0.05 + 0.04) sum to 0.19,
against a 0.18857 consensus.

Two facts are now stated in the evidence rather than left to be inferred:

- **`LEVEL READING`** sits under the quants: how many analysts moved, and whether
  the *level* moved. Where the level is unchanged and the counts are up, it says
  outright that the consensus is current rather than stale.
- **`TRAILING CHECK`** compares the last four reported quarters against the
  current-FY consensus whenever the two are comparable, and says when the streak is
  already in the number.

And `fig lint` errors on the conjunction -- a staleness claim plus revision-count
evidence plus a level that did not fall (`reason_stale_consensus_on_counts`). Each
half alone is legitimate, so only the conjunction fires; BB's reason 3 is the only
reason in the committed batch it flags, and it is now visible as an error in the
index rather than reading as evidence.

### What pointing the checks at the existing notes found

`fig attribute` was run over the thirteen committed notes, then `fig index` re-linted
and re-grounded every one of them against the evidence on disk. Both checks found real
defects, which is the point of running them:

| note | finding | what it means |
|---|---|---|
| BB | reason 2 cites nothing, and its `25.38%` is unsupported | the figure is not in the packet at all -- the note asserts a UEM growth rate its own evidence never contained |
| ORCL | reasons 1 and 2 cite nothing; `209` unsupported | the $664B backlog is in a headline, but the $209B year-over-year rise the reason leans on is not |
| C | reason 3 cites nothing; `127` unsupported | "127 banks exited emerging-market correspondent relationships" has no home in the evidence |
| FUL | reason 3 cites nothing | the reason stands on the packet's statements without saying so |
| CSX, OMF | two figures each cited to a source that does not contain them | `3.8%` cited to the consensus but present in the catalyst; `6.8%` cited to a headline but present in the catalyst |
| MRK, JEF, MNST | one each | `128` cited to a headline but present in the catalyst, and so on -- the citations are real and point at the wrong entry |

Eight misfiled citations, three figures with no support anywhere in the packet, and
five reasons with no citation at all, across thirteen notes -- which is roughly what
careful hand-checking finds, and is the reason these run on every rebuild rather than
once. The counts are printed in `research/README.md`, and each note's own footer says
what its numbers rest on.

The BB case is worth naming because it is the same failure as the staleness claim
above, in a different disguise: an assertion that reads as evidence. It also exposed
the defect underneath it -- the note quotes research from a *different sample run*
than the one whose packet was saved beside it, and until the register was rebuilt per
sample, a citation from one sample could resolve to another sample's URL. The saved
packet is now the one the chosen note was written from, and every sample's research is
kept.

The notes are left as they are: the errors are the honest state of those notes, and
the index and each note's footer now say so. Fixing them means rewriting the thesis,
which is a generation decision rather than a linting one -- `fig generate BB` will
produce a fresh note with the repaired evidence in hand.

### A sequential move is not a trend, and a deal is not organic growth

The PAYX short note is the case that produced the next four checks. Its second reason:

> "The May quarter showed revenue down 11.2% and net income down 24.9% sequentially,
> while the stock trades at 19.5x forward earnings -- the market is pricing a recovery
> the latest numbers do not show."

Every figure was correct, every figure was sourced, and the conclusion was backwards.
The same quarter grew **12.5% in revenue and 41.5% in net income** year over year. A
payroll processor's fiscal year ends in May, so the February quarter is the seasonal
peak and the decline into May is the calendar. Worse, the note's whole frame -- that
weak small-business hiring must show up as weak Paychex revenue -- ignored that
**Paycor** had just added most of the year's growth: FY26 revenue grew 16.9% while net
income grew 6.2%, because the deal lifted selling, general and administrative costs
27.6% and interest expense 155.7%.

Four defects, four fixes, each of which is evidence the writer is now shown and a
check that fires when the note ignores it:

| defect | evidence added | check |
|---|---|---|
| a sequential fall read as deterioration | `QUARTER: SEQUENTIAL vs SAME QUARTER A YEAR AGO`, one line per statement line, plus `ANNUAL` for the fiscal year; the Quants panel leads with the pair where the two disagree | `reason_sequential_without_year` (**error**): a sequential move quoted without the year-earlier comparison, when the two point opposite ways |
| acquired growth treated as demand | `DEAL ACTIVITY`, derived from a goodwill or intangibles step change on the balance sheet -- not from the writer remembering the deal | `reason_ignores_deal` (**error**): a deal landed in the period and no reason names one |
| a long chain that no single report can settle | nothing: the fix is to cut the chain | `reason_long_horizon` and `reason_chain_too_long` (warnings) |
| two survey questions presented as one trend, and the older reading used | `Superseded readings`, from the packet's own dated readings of the same driver | reported in the note's footer when a later reading from the same provider reverses the cited one |

The note that came back is a different argument for the same idea, built on the
figures the first one did not have:

> 1) FY2026 revenue grew 16.9% but net income only 6.2%, because the Paycor deal lifted
> SG&A [selling, general and administrative costs] 27.6% and interest expense 155.7%
> -- growth that costs more than it earns.
> 2) Small-business hiring cooled in August 2026 to the slowest pace of a seven-month
> growth streak, from 38,200 jobs added in July, because payroll revenue tracks client
> headcount -- and Paycor's bought revenue hides that.

The `Watch` block is the other half of the same lesson. The critique that prompted all
of this ended with a ranked list of what to check at the print; that list is now a
required section of the note whenever the catalyst is within 21 days, with the reading
that confirms and the reading that breaks:

```
Watch
- Organic revenue excluding Paycor: confirms if it grows below the 16.9% FY rate; breaks if it reaccelerates.
- Client worksite employees and PEO [professional employer organisation] headcount: confirms if growth slows from the July pace; breaks if it reaccelerates.
- FY27 EPS guidance: confirms if below the 5.96 consensus; breaks if above.
```

Section 3d-3g of `references/FORMAT.md` carries the rules, the evidence blocks and the
reason each one exists.

---

## Generating notes (`fig generate`)

One key drives both halves of the job — **search for evidence, and the model for
prose**:

```bash
.venv/bin/fig generate COST JEF ORCL OMF GIS PAYX --directions long,long,long,short,short,short
```

Output lands in `research/` under the side the note argues -- `research/longs/` or
`research/shorts/` -- as a `.md` note in reference layout, its `.json` source, and a
`.packet.json` holding every piece of evidence used, plus an index at
`research/README.md` with a table per side. The folder is derived from the note's own
`direction`, so a note cannot be filed against the side it argues; `fig organize`
files notes written before the folders existed and corrects any misfiled one.

### The safety property: the model writes prose, the tool owns every number

This is the core design decision, and it is enforced structurally rather than
requested in the prompt. The model returns only `description`, `reasons`,
`reason_sources` and `reflection`; `generate.assemble_writeup` then fills the Quants
block, the option legs and every citation from the packet, which came from live
sources. A hallucinated price, multiple, premium **or URL** therefore cannot reach a
note — the worst a bad generation can do is write weak prose, which the linter then
catches.

Because reason prose is the one remaining place a figure could be smuggled in
from the model's memory, `fig lint` also **grounds** the numbers: every figure
written in the Description and Reasons is checked against the evidence text, and
anything unsupported is reported in the note footer. On the committed batch all
63 figures across 8 notes traced back to the packet. A second check goes further
and asks whether the figure is in the *source that reason cites* — being in the
packet somewhere is not the same as being in the page the reader is sent to.

### The catalyst is dated and justified

Every note carries an exact earnings date and the reasoning for it. Line 1 is
**measured**, never written by the model:

```
2026-10-30 (Friday, before the open), 41 days out -- from the earnings calendar, consensus EPS 1.88.
```

That line distinguishes a **scheduled** date (published in the earnings calendar)
from an **estimated** one (projected from the company's own reporting gap, and
labelled as approximate), names the session, and gives the consensus for that
report. `fig lint` errors if the date in the note does not appear in that line,
because a restated or rounded earnings date is the most damaging error a note can
carry.

Line 2 is the writer's, ≤ 25 words: what must show up in that report for the
thesis to be right. The facts supplied to support it are what make a date
credible — the company's cadence (`median gap 91 days`), whether it reported in
the same slot last year, and its record against consensus. That last one is a real
caution on a short: **OMF has beaten consensus in each of the last four reports**,
so the bar is already high and a miss is what moves the stock.

### A discount is not a thesis

The single most expensive reasoning error in this format, and the one the ORCL
reference itself risks: "it trades at 12x while peers are at 20x" is an
observation, not an argument. Premium multiples usually exist for a good reason,
so cheapness is not by itself a case for an upward rerating -- cheap things are
frequently cheap because something is wrong.

Three things now push against it:

1. **The screen no longer rewards cheapness.** It used to add a flat bonus for a
   low forward PE, which biased the whole ranking toward discounted names looking
   to rerate. A multiple now only *amplifies* a signal that already exists, and
   the tilt depends on which way estimates are going: falling-and-cheap is fragile
   (the discount is deserved), falling-and-expensive is vulnerable. Rising
   estimates earn no valuation bonus at all.
2. **The prompt says so explicitly** (rule 4a): citing a multiple obliges you to
   say what the market is *missing* or what will specifically *change*.
3. **The linter enforces it.** `reason_valuation_only` is an **error**, so the
   repair loop has to rewrite it. The juxtaposition form counts -- "net income
   rose 32% yet it trades at 16.9x" has not explained why the market pays only
   16.9x. Short theses are exempt (a high multiple on deteriorating numbers is a
   standard short argument), and ORCL's own reference reason 1 passes on its
   "because", so the rule flags the bare form rather than rejecting the spec.

Calibration was verified against an independent audit of all nine notes: the rule
and the audit agreed on exactly the same seven reasons. Fixing it required two
corrections -- `"so"` had been counted as a causal mechanism (which excused "next-FY
PE is 39.5, so the market is paying less for next year's earnings"), and price
discounts were not covered at all, only multiples.

### End-market research, and why a problem has not shown up yet

Filings and consensus describe what already happened. They cannot answer the
question a real idea turns on: **why hasn't the obvious problem shown up in the
numbers yet?** Paychex sells payroll and HR to small businesses, both under
visible pressure, and its estimates had not cracked.

`fig.research` closes that gap in two stages: it plans search queries from the
company's own Description (the useful questions are company-specific), runs them
against the industry and customer segment rather than the company's own press
releases, then extracts trend claims that are **kept only if a verbatim quote is
found in the retrieved text**. Unsupported claims are dropped however plausible
they read -- trend claims are exactly the kind of statement a model produces
fluently from memory.

Each trend is tagged `pressure` or `support`. Supports matter as much as
pressures, because a support is usually the reason a problem has not appeared yet.
A note is required to use them: if trends were supplied and no reason refers to
the end market, that is an **error** and the writer has to try again. The check
ignores words already in the company's own Description, so "payroll" for Paychex
cannot count as evidence about its customers.

### Model and speed

The default model is **`deepseek-v4.1-flash`** (`FIG_MODEL`, or `--model` per call).
The qualitative work here -- planning end-market queries, synthesising trends,
writing the note -- is latency-bound, and flash writes a round in ~19s against the
pro model's 26-38s, with no observed loss in note quality.

Two other levers matter more than the model:

- **`--jobs N` generates N tickers concurrently.** Generation is almost entirely
  network wait, so this is close to linear: 4 tickers take ~2 minutes in parallel
  versus ~6.5 serially.
- **`tools/funnel.py`** shows where names are lost before any model call happens,
  which is usually the real answer to "why so few ideas?".

Screening is cheap and model-free by design: `screen_symbol` pulls only light facts
(no option chains), so dozens of names can be triaged before paying for a full
packet on the survivors.

### The share-price cap, and the pool floor

Ideas are capped at **$150 per share**, enforced in the screen and again before any
research is done (`--max-price`, or `0` to disable). The reason is arithmetic
rather than taste: the reference structures size a position from a ~$4,500 capital
unit against 100-share contracts, so the cap is what makes a normal position fit.

It is not a judgement on expensive companies. AZO at ~$2,855 needed $13,275 for a
single option contract -- three times the unit -- and COST at $895 needed $3,785.
Rejected names are listed in the index with the price that excluded them, so the
policy's effect stays visible instead of silently shrinking the universe.

The cap is available on `fig screen`, not only on `fig generate`, together with the
pool's market-cap floor (`--min-market-cap`, accepting `1b`/`1000m`/`2e9`, default
`2b`, `0` to disable). The two rules jointly decide the size of the universe and
therefore the runtime:

```bash
.venv/bin/fig screen --max-price 75 --min-market-cap 1b --limit 250 --top 60
```

The floor is a *pool* filter rather than a ranking input -- a name below it is never
added, so it cannot appear as "gated" either -- and it exists to keep the option
requirement satisfiable, because microcaps rarely have listed strikes worth trading.
Unlike generation, screening is model-free: a screen run costs time and no quota.
Measured numbers are in "what a run costs" below.

### What a run costs

The pipeline is deliberately split into a cheap model-free half and an expensive
model-bound one, so the two costs are separable.

| stage | cost | measured |
|---|---|---|
| pool + triage (`fig screen`) | time only | **~5-7s per name** screened serially: 144 names in 728s, 149 names in 1030s |
| packet build (per name) | time only | ~2 min: 1 profile + 1 quants panel + news + 4 searches + chains |
| generation (per name) | API calls | ~19s per round, 3-7 rounds, plus 1 plan + 1 synthesis chat call and 4 searches per sample |
| whole batch | — | 8 tickers at `--jobs 8 --samples 3`: **9.6 min wall** (packets built 01:03:39, notes saved 01:13:18) |

So the dominant term is not the model but **how many names get screened and how many
samples each survivor gets**. The screen is model-free and cached on disk for 6h, so
a repeat run inside that window is roughly three times faster.

#### The $75 / $1B universe, measured

```bash
.venv/bin/fig screen --max-price 75 --min-market-cap 1b --limit 250 --top 80
# pool 149 names -> screened 149 -> ranked 29        (17m10s, cold cache)
# gated out: 113 at or above the $75 cap, 5 below the triage score floor
```

Against the $150 run on the same universe -- 144 names, 83 price-capped, 53 passed,
728s -- the tighter cap does two things and only one of them is obvious:

- **It rejects more names, not fewer.** 113 of 149 are at or above $75, so the cap
  removes ~30 ideas the $150 cap admits (including half the top ten: COST, AZO, MU,
  ASML, META and most of the semis are nowhere near $75).
- **It barely grows the pool.** Lowering the floor from $2B to $1B added 5 names
  (144 -> 149), because the Nasdaq screener returns the most active 60 per exchange
  and those are large caps already. The floor binds on the *earnings calendar*, which
  is where the mid-caps (CNXC, MLKN, ANAB, IDT, TBN, WOR) came from.

Budget **~17 min** for the screen and **~10-12 min** to generate the top 8-10 of the
29 survivors at `--jobs 8 --samples 3`, so **~25-30 min end to end** on a cold cache
and ~15 min warm. The model spend scales with survivors generated, not with the
universe screened, which is what makes a wide net affordable: screening 149 names
costs no quota at all.

Note the direction hint is not a recommendation: this screen returns 29 names across
both sides (MNST, CSX, BB, FUL long; CNXC, WOR, VZ, GIS short), and the end-market
sampling later contradicted the screener's own top-ranked name.

### Ranking, and what it is not

`fig rank` orders a folder by **conviction**, built from stated components: catalyst
proximity (0.20), 7-day/30-day estimate-revision agreement (0.20), current lint
score (0.10), grounding (0.10), and the sampled end-market verdict (0.40). See
`src/fig/ranking.py` for the definitions and the two cautions worth more than the
weights themselves:

- **A high lint score is not evidence of a good thesis.** Lint measures form, and
  the two highest-scoring notes this repo has produced were the two judged weakest
  on reasoning. Form is cheap to satisfy.
- **The evidence component is the only one carrying a view on the company**, and it
  is a *sampled* view. A note confirmed in 1 of 3 runs is genuinely less settled
  than one confirmed in 3 of 3, and the score says so rather than hiding it.

### Sampling the verdict, on purpose

The owner's instruction: search is *not* reproducible, and that is correct rather
than a defect -- the reasons are qualitative, and the verdict should be assessed
non-deterministically.

So `--samples N` runs N fully independent generations per ticker. **Each sample
re-runs the end-market research**, not just the writing, because otherwise the
evidence would be fixed and the verdict could never disagree with itself, which is
the entire reason for sampling. `research.evidence_verdict` then counts, mechanically,
whether the end-market evidence points with the idea or against it -- pressures
support a short, supports support a long -- and the batch reports it as
"confirmed 2/3". Disagreement between samples is a finding, not noise to be averaged
away.

### Recency: stale research is dropped, not caveated

Trends are dated from an explicit publication date in the URL path or the text, and
anything older than **180 days is discarded**. This fixes a real bug: a PAYX trend
described the second half of 2025 and the writer presented it as a current condition
nine months later. Stale evidence is worse than no evidence, precisely because it
reads exactly like fresh evidence.

Only *explicit* dates are accepted. The yearless form the news reader uses ("Sept 18")
assumes the current year, which would make an old article look new -- acceptable for
ordering headlines, actively harmful for dating evidence.

Filtering alone only sorts whatever the engine ranked, so the query planner is also
told today's date and to prefer the current period, and the synthesiser must state
the period the evidence covers and must not pass an older period off as current.

### Structuring is optional

The legs are the most expensive part of a note to get right (listed chain, common
strike, two standard monthlies straddling the catalyst, credit over the 10% floor)
and the least important part of the idea. When no chain works, the note is still
written and `fig render` prints one bracketed line naming the reason:

```
[no option structure: no usable catalyst for SNX]
```

### The repair loop

The linter's complaints are fed back to the model as concrete, numbered
instructions ("Reason 2 is 63 words, budget 40"), which works far better than
asking for brevity up front — the model gets a measurable target instead of an
adjective. Each round is recorded in the run log and the index.

```
[OMF] round 0: score 95 (0 errors, 1 warnings) in 9.9s -- 9 figures all grounded
```

### Prose is still optional

`fig prompt` prints the packet and instructions without calling anything, so a
note can be written by hand or by any other model and then scored with `fig lint`.
`fig generate` is a convenience over the same schema, not a requirement.

---

## How to pull the data (what actually works, and what doesn't)

Both free sources were probed before any code was written. Findings:

| need | source | verdict |
|---|---|---|
| valuation, consensus trend/revisions, option chains | **yfinance** | best single dependency; handles Yahoo's cookie+crumb handshake |
| universe, earnings calendar, market news | **Nasdaq public API** | open, no key, no crumb |
| current reporting behind the headlines | **Ollama `api/web_search`** | needs a key; returns title + url + long snippet, which makes it usable as *evidence* rather than just a headline list |
| distillation into prose | **Ollama `v1/chat/completions`** | same key; OpenAI-compatible with a JSON mode |
| Yahoo `quoteSummary` / `v7/quote` directly | — | **401 `Invalid Crumb`** unauthenticated — use yfinance, which manages the crumb |
| Nasdaq `analyst/{sym}/eps` | — | 404; the endpoint is `analyst/{sym}/earnings-forecast` |

Three gotchas cost real debugging time and are encoded in the code:

1. **Yahoo needs a crumb.** `query1.finance.yahoo.com/v10/finance/quoteSummary/...`
   returns `401 Invalid Crumb` with no cookie. yfinance is the practical
   workaround rather than reimplementing the handshake.
2. **Nasdaq's `frequency` parameter is inverted.** `frequency=1` returns *annual*
   columns and `frequency=2` returns *quarterly* ones. See
   `fig.sources.nasdaq.financials`.
3. **Nasdaq news is topic-scoped, not symbol-scoped.** `articlebysymbol?q=ORCL`
   returns market roundups that merely mention the ticker, so headlines are
   scored for relevance (0–3) rather than trusted, and Yahoo's per-symbol feed is
   merged in for genuine coverage.

### Why web search is worth a key

The two free feeds give syndicated headlines. They do not reach primary reporting,
and they carry no macro datapoints about a company's *end market*. Search does.
It put these into the evidence packet, and they became real reasons:

| what search added | where it landed |
|---|---|
| "Subprime auto loan delinquency hit 6.8% at the start of 2026", worst in 32 years | OMF short, reason 2 |
| Oracle's ~$18bn New Mexico data-centre loans quoted at 89–91c, plus a rebuttal that the debt is not Oracle's | ORCL long, the debt-servicing debate |
| Mondelez raising 2026 organic growth while General Mills exits yogurt | GIS short, reason 3 |

Search is **off during screening** (`collect_news(include_web=False)`) because
screening calls it once per candidate and three searches per name across a
universe is slow; packet building turns it on.

### Division of labour

`fig.sources.nasdaq` is the **discovery** half — what is happening, and what is
about to happen (the earnings calendar defines the catalyst window a trade must
cover). `fig.sources.yahoo` is the **fundamentals** half — every number the
writeups quote, including the option chain. Every call is cached on disk
(`.cache/fig/`) with a TTL, so re-runs are free and a flaky upstream degrades to
slightly-stale data instead of a crash.

---

## Pipeline

```
universe()          Nasdaq earnings calendar + screener + watchlist
      |             -> candidates, each tagged with why it surfaced
      v
screen_symbol()     yfinance quants, consensus revisions, 30/90d price move,
      |             news themes, and whether an option structure is even possible
      v
rank_candidates()   revision score -> direction hint (long/short)
      |             $150 price cap is the only gate still on by default
      v
build_packet()      full evidence bundle: profile, quants, statement deltas,
      |             EPS YoY, headlines, live themes, peers, structures
      |             + source_catalogue(): every source numbered, with its URL
      v
to_prompt_context() + prompts.py     <- the distillation instructions,
      |                                 evidence tagged with its source ids
      +--> fig prompt    -> a model or a human writes the prose
      |
      v
writeup JSON  ->  lint.py  ->  render.py  ->  reference-layout note
                    |                            (reasons, each with its Source line)
                    +--> generate.py drives this loop end to end:
                         ollama.chat -> assemble (tool owns numbers AND citations)
                         -> lint -> feed complaints back -> revise
                    |
                    +--> save_idea() -> research/longs/ | research/shorts/
```

### The core screen: the consensus EPS revision

The primary signal is the **consensus EPS revision**: the size of the net revision
sets the rank, and its sign sets the side.

- **ORCL** — revisions *up* (4 up, 0 down over 30d) → **long**
- **OMF** — revisions *tilted lower* (6 up, 8 down), thesis expects worsening
  charge-offs → **short**

It is measurable from free data and it yields a *direction* rather than just a
ranking. It is a triage filter, not an answer: `score_components` is returned for
every candidate so a rank can be argued with.

**This used to be a divergence against price**, so that improving estimates into a
falling tape outscored estimates and price agreeing. It was removed because the
price leg was doing much of the ranking rather than the revisions: two names with
identical revision moves scored ~30 points apart depending only on the direction of
the tape, and **24 of 50 names in a real screen sat in the collapsed "aligned"
branch** — including 16 of the 19 shorts, which were "estimates falling *with* the
price", i.e. trend-following rather than a dislocation.

The cost of that removal is worth stating plainly: **a revision-following rank is
closer to consensus than a gap was.** The non-consensus character of an idea now has
to come from the reasons, not from the screen — which the format already demands,
since a reason that merely restates the screen signal as a conclusion is rejected
(see "a discount is not a thesis" above).

Neither signal licenses the reading that produced the BB note's worst reason: "5 up
and 0 down" is a count of analysts moving, not a move in the consensus *level*, and
the packet states which of the two happened. See "a revision count is not a
revision of the number" above.

### The story layer

Neither reference is a reaction to one headline — ORCL is an AI-infrastructure
thesis, OMF a consumer-credit one. So `fig/themes.py` tags headlines against a
curated lexicon and aggregates them into live themes, and can surface *two-sided*
readings of one story (AI adoption is bullish infra capex and bearish labour
income). Tagging is keyword-based on purpose: free, offline, deterministic and
auditable. `tag_text()` is the single seam where an embedding or LLM classifier
would slot in.

Matching is **word-start anchored with suffix allowed**, so deliberate stems
(`revis` → revision/revisions) work while substring false positives do not. Plain
substring matching was tried first and was badly wrong on real headlines: `nco`
matched "I**nco**me" (every dividend story tagged as credit stress), `sec` matched
"**Sec**urity" (every Social Security story tagged as regulation), `stake` matched
"Mi**stake**".

### Structuring

`fig/options.py` encodes the construction rules reverse-engineered from the
references and verified against live chains — monthly (3rd-Friday) expiries, short
leg expiring *before* the catalyst, long leg *after* it, strike at the nearest
common OTM strike to ~4%, ~$4,500 of long premium, and a **10% credit floor** where

```
credit ratio = short premium collected / long premium paid
```

Both reference structures are reproduced exactly. See `references/FORMAT.md` §7.

---

## Commands

| command | purpose |
|---|---|
| `fig themes` | live themes from market-wide news |
| `fig screen` | triage a universe; ranked with direction hints (`--max-price`, `--min-market-cap`) |
| `fig packet SYM` | evidence packet (text, or `--json`) |
| `fig prompt SYM` | packet + distillation instructions, ready for a model |
| `fig structure SYM --direction long\|short` | build and stress the spread |
| `fig quants SYM` | the Quants block plus statement deltas |
| `fig lint FILE` | check a writeup against the house style, its citations included |
| `fig render FILE` | print a writeup in reference layout |
| `fig search Q` | web search via the Ollama key (`--models` lists models) |
| `fig generate SYM...` | build packet, search, write, lint, revise, save under `longs/`\|`shorts/` |
| `fig organize` | file flat notes under their side's folder (`--dry-run` to preview) |
| `fig attribute` | backfill the sources behind each reason on notes written before sources |
| `fig index` | rebuild the index from the notes on disk, re-linting them |
| `fig rank` | rank a folder of notes by conviction, per side |
| `fig demo` | assert the engine still reproduces the references |

---

## Where the prose comes from

The repo generates **evidence and constraints**, not prose. `fig prompt` emits a
packet plus the house-style instructions; the writeup JSON is produced by whatever
model you point at it (or written by hand), then `fig lint` scores it and
`fig render` prints it.

That split is deliberate: the packet/lint/render loop is deterministic and
testable, and the one non-deterministic step is isolated and checkable. Wiring a
provider is a small adapter — send `fig prompt`'s output, receive the JSON in
`prompts.build_user_prompt`'s schema.

## Worked examples

`ideas/` holds three generated notes: `orcl.json` and `omf.json` regenerate the
two reference trades from **today's** live data (useful for checking the loop
end-to-end), and `jef.json` is a fresh name the screener surfaced on its own.
`ideas/README.md` is the generated index. Editing the JSON and re-running
`fig render` is the intended workflow.

`research/` holds the working batch, filed as `research/longs/` and
`research/shorts/` with `research/README.md` indexing both sides. The `.md` is the
note; the `.json` is what you edit; the `.packet.json` is the evidence, including
the source register every citation in the note resolves against. The notes written
before the format had sources were backfilled with `fig attribute` rather than
regenerated, so their prose is the original and only their citations are new.

## Caveats

- Both upstreams are **free and undocumented**, and can change without notice.
  Parsers return `None` rather than raising, and disk caching absorbs rate limits.
- Nasdaq reports statement figures in **thousands** — compare ratios, not levels.
- `fig demo` depends on the reference expiries still being listed; it will start
  failing once Oct-26 rolls off, which is expected. Re-point it at fresh
  references rather than deleting it.
- Statement-delta labels come from Nasdaq's own naming (`Other Operating Items` is
  a bucket, sometimes the provisions line) — treat them as a pointer to the filing,
  not as a final label.
- **Research houses look like their own news.** Jefferies (JEF) is a broker, so
  name matching scored "McDonald's target falls to $325, but Jefferies keeps
  faith" as company-specific JEF coverage — as were *all* of its top headlines.
  `packet._relevance` now detects the analyst role and demotes those to a mention.
  The same trap applies to any sell-side or ratings-issuing name.
- **Fwd PE for a loss-maker is meaningless.** Negative multiples are gated out of
  the screen rather than ranked, since a negative PE sorts as "cheapest" and would
  float distressed names to the top.


## Tests

```bash
.venv/bin/python -m unittest discover -s tests   # offline: parsing, maths, lint, render
.venv/bin/fig demo                               # online: reproduces the reference legs

# the qualitative screener's own offline suite (gates, grounding, quantum, rendering)
PYTHONPATH=qualitative .venv/bin/python -m unittest discover -s qualitative/tests
```

The offline suite locks in the reverse-engineered maths (the credit-ratio
definition and both references' dollar totals), the wording generators, the
word-boundary matching rules, and the lint budgets. It also locks in the two failure
modes found in production and described above: a fabricated source id is dropped
rather than printed, a URL written into a reason is removed, a figure outside the
source it cites is reported, and the BB counts-versus-level reason is caught -- while
the four reasons next to it that only *look* similar are not. `fig demo` covers the
part that depends on live chains.
