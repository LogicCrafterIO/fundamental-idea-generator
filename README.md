# fundamental-idea-generator

Pulls current US equity fundamental news from **free** sources and turns it into
short ticker idea notes in a fixed, terse house format — the format of the two
writeups in [`references/`](references/).

The point is not the prose. It is the **distillation**: the Description and each
Reason are hammered down to simple language and as few words as possible, so the
reasoning is checkable at a glance. `references/FORMAT.md` states the rules, and
`fig lint` enforces the measurable ones.

```
Ticker: OMF

Description
Nonprime consumer loan lender                                    <- 4 words

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

.venv/bin/fig demo                          # verify the engine vs the references
.venv/bin/fig themes                        # what stories are live right now
.venv/bin/fig screen --watchlist ORCL OMF   # triage candidates, ranked
.venv/bin/fig prompt ORCL --peers GOOG,SNOW --direction long
.venv/bin/fig structure ORCL --direction long
.venv/bin/fig lint ideas/orcl.json          # enforce brevity/plain language
.venv/bin/fig render ideas/orcl.json        # print in reference layout
```

`fig demo` is the regression test: it rebuilds the ORCL and OMF option legs from
live chains and fails if they no longer match the references.

---

## How to pull the data (what actually works, and what doesn't)

Both free sources were probed before any code was written. Findings:

| need | source | verdict |
|---|---|---|
| valuation, consensus trend/revisions, option chains | **yfinance** | best single dependency; handles Yahoo's cookie+crumb handshake |
| universe, earnings calendar, market news | **Nasdaq public API** | open, no key, no crumb |
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
      v
writeup JSON  ->  lint.py  ->  render.py  ->  reference-layout note
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
