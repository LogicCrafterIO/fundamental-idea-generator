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
2) If NCO [net charge offs] go from 7% now to 10% in Feb or March earnings then
   it could rerate significantly to a PE of 4-5 as earnings get hit.
```

---

## Quickstart

```bash
python3 -m venv .venv
.venv/bin/pip install -e .

echo 'OLLAMA_API_KEY=...' > .env                # enables search + generation

.venv/bin/fig demo                             # verify the engine vs the references
.venv/bin/fig themes                           # what stories are live right now
.venv/bin/fig screen --watchlist ORCL OMF      # triage candidates, ranked
.venv/bin/fig search "regional bank credit"    # web search via the same key
.venv/bin/fig generate OMF --directions short  # write a finished note
.venv/bin/fig lint ideas/orcl.json             # enforce brevity/plain language
.venv/bin/fig render ideas/orcl.json           # print in reference layout
```

`fig demo` is the regression test: it rebuilds the ORCL and OMF option legs from
live chains and fails if they no longer match the references.

---

## Generating notes (`fig generate`)

One key drives both halves of the job — **search for evidence, and the model for
prose**:

```bash
.venv/bin/fig generate COST JEF ORCL OMF GIS PAYX --directions long,long,long,short,short,short
```

Output lands in `research/`: a `.md` note in reference layout, its `.json` source,
and a `.packet.json` holding every piece of evidence used, plus an index.

### The safety property: the model writes prose, the tool owns every number

This is the core design decision, and it is enforced structurally rather than
requested in the prompt. The model returns only `description`, `reasons` and
`reflection`; `generate.assemble_writeup` then fills the Quants block and the
option legs from the packet, which came from live sources. A hallucinated price,
multiple or premium therefore **cannot reach a note** — the worst a bad generation
can do is write weak prose, which the linter then catches.

Because reason prose is the one remaining place a figure could be smuggled in
from the model's memory, `fig lint` also **grounds** the numbers: every figure
written in the Description and Reasons is checked against the evidence text, and
anything unsupported is reported in the note footer. On the committed batch all
63 figures across 8 notes traced back to the packet.

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
rank_candidates()   divergence score -> direction hint (long/short)
      |
      v
build_packet()      full evidence bundle: profile, quants, statement deltas,
      |             EPS YoY, headlines, live themes, peers, structures
      v
to_prompt_context() + prompts.py     <- the distillation instructions
      |
      +--> fig prompt    -> a model or a human writes the prose
      |
      v
writeup JSON  ->  lint.py  ->  render.py  ->  reference-layout note
                    |
                    +--> generate.py drives this loop end to end:
                         ollama.chat -> assemble (tool owns numbers)
                         -> lint -> feed complaints back -> revise
```

### The core screen: revision-versus-price divergence

Screening on "cheap" or "expensive" alone yields consensus ideas, and the ORCL
reference explicitly rejects consensus. So the primary signal is a **divergence**
between consensus EPS revisions and price — which both references happen to be:

- **ORCL** — revisions *up* (4 up, 0 down over 30d), price down >20% → **long**
- **OMF** — revisions *tilted lower* (6 up, 8 down), thesis expects worsening
  charge-offs → **short**

It is measurable from free data, it is inherently non-consensus, and it yields a
*direction* rather than just a ranking. It is a triage filter, not an answer:
`score_components` is returned for every candidate so a rank can be argued with.

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
| `fig screen` | triage a universe; ranked with direction hints |
| `fig packet SYM` | evidence packet (text, or `--json`) |
| `fig prompt SYM` | packet + distillation instructions, ready for a model |
| `fig structure SYM --direction long\|short` | build and stress the spread |
| `fig quants SYM` | the Quants block plus statement deltas |
| `fig lint FILE` | check a writeup against the house style |
| `fig render FILE` | print a writeup in reference layout |
| `fig search Q` | web search via the Ollama key (`--models` lists models) |
| `fig generate SYM...` | build packet, search, write, lint, revise, save to `research/` |
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
```

The offline suite locks in the reverse-engineered maths (the credit-ratio
definition and both references' dollar totals), the wording generators, the
word-boundary matching rules, and the lint budgets. `fig demo` covers the part
that depends on live chains.
