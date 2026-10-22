# A purely qualitative theme screener

A second screener, separate from the parent pipeline in [`../src/fig/`](../src/fig/),
that answers a different question:

> **What is happening to these businesses, and which tickers does the same force
> help and hurt?**

The parent tool screens for a *trade*: it ranks the consensus EPS revision, dates a
catalyst, and writes a terse note. This
one screens for a *story*. It has no view on valuation, no estimate revisions, no
catalyst, and no option leg. It builds a list of tickers, finds out what each one
sells, researches the trends acting on each part of the business, and then
aggregates those trends into ranked **themes** shared across tickers.

```
$ qualitative/qs screen --limit 20        # the gated universe
$ qualitative/qs research --limit 20      # description + revenue streams + trends
$ qualitative/qs themes                   # rebuild the master theme file
$ qualitative/qs show KO                  # one writeup
```

Outputs land in this folder:

| Path | What it is |
|---|---|
| [`themes/THEMES.md`](themes/THEMES.md) | **The master file.** Every theme, ranked, with the tickers it helps and the tickers it hurts. |
| [`tickers/`](tickers/) | One writeup per ticker: description, revenue streams, trends by part of the business, themes affecting it. |
| [`analyses/`](analyses/) | The research artifacts the two documents are rendered from. |
| [`runs/`](runs/) | Universe snapshots, so a batch can be reproduced. |

---

## The only two numbers

The screen is two quantitative inputs, and nothing else:

| Gate | Default | Why |
|---|---|---|
| Share price | `<= $100` | Position arithmetic: option contracts come in 100-share lots, so a high-priced underlying breaks a normal capital unit. The parent screener applies the same rule at $150. |
| Market cap | `>= $1B` | Coverage: industry reports, trade press and segment disclosure exist for billion-dollar businesses. Below that, a screen that only reads qualitative sources mostly returns silence, and silence is indistinguishable from "no trend found". |

There is **no** multiple, estimate revision, price momentum, earnings date or
quality score anywhere in the pipeline, and no ranking of businesses. The batch is
ordered by market cap purely so consecutive waves start with the names that have
the most research coverage — that is an ordering, not a judgement, and
`--order name` / `--order random --seed 7` produce equally valid batches.

Two consequences worth stating plainly:

* **A revenue figure appears in the output, but is not a screen input.** A stream's
  size is quoted from segment disclosure because "the exact revenue streams" needs
  it, and it is what makes a stream comparable to the industry trend printed next
  to it. It never enters a gate or a rank.
* **The universe is businesses, not securities.** Nasdaq's listed names include
  preferred issues, notes, warrants and closed-end funds, which pass both gates
  comfortably (Huntington Bancshares alone contributes four preferred lines). Those
  rows are removed by security *type* — a definition of the universe, not a
  judgement about a company — and the count removed is reported on every run.
  Real ADRs, MLPs and class shares are kept: see `qts/universe.py` for why the
  difference is a parenthesis.

As of 2026-09-20 the gates admit **1,876 businesses** (NASDAQ 799, NYSE 1,056,
AMEX 21) out of ~7,600 listed rows. One run researches a batch of them; the tool is
resumable and the theme file is additive, so a second wave deepens the first.

---

## Trend or theme?

Both words are used, for different objects, and the distinction is the design:

| | What it is | Where it lives |
|---|---|---|
| **Trend** | One sourced finding about **one company**. "US small-business hiring plans fell for a third month as of June 2026, which cuts the headcount Paychex bills per client." | The ticker file, under the part of the business it acts on. |
| **Theme** | The industry force that several trends turn out to be instances of. "Small-business hiring weakness" reaches a payroll processor through billings, a staffing firm through placements, a lender through loan demand. | `themes/THEMES.md`, ranked. |

**Themes** is therefore the right name for the master file: the rankable object is
the *force*, whose size, speed and impact are properties of the industry, while a
trend's properties are properties of one company's exposure to it. A theme is also
the only object that can hold both directions at once — which is exactly what
"list the tickers positively and negatively affected" requires.

### How one force becomes one theme

Each company is researched on its own, so the same force arrives under a different
key from each of them (`deposit-funding-cost-pressure` from one bank,
`deposit-competition-and-funding-costs` from the next). Three mechanisms turn those
keys into shared themes, and the first is the one that matters most:

1. **Convergence during research.** Every ticker's synthesis prompt is handed the
   theme keys already coined by companies researched before it, with the instruction
   to reuse one exactly when it names the same force. The vocabulary is seeded from
   the artifacts on disk that are *not* in the current batch — seeding it from the run
   being replaced would let each company rediscover its own previous keys, which looks
   like convergence while changing nothing. Later companies in a wave therefore adopt
   earlier companies' keys, and a second wave inherits the first wave's vocabulary.
2. **A model merge pass, in two stages.** Stage one groups the raw keys; stage two
   runs over the resulting *themes* rather than the keys, which is what catches the
   pairs that are semantically identical and lexically unrelated
   (`fed-easing-cycle` and `rate-cut-expectations` only look comparable once each is a
   labelled, defined theme). Both stages return **only the groups of two or more** —
   every key not mentioned stands alone. That detail is not cosmetic: asking instead
   for a group per key produced 200 themes from 220 trends, and the failure was quiet,
   because "one group per key" is a valid answer to the schema and a useless answer to
   the question.
3. **A deterministic safety net.** Near-identical keys merge mechanically when they
   share at least two *significant* tokens — generic wording like "growth", "market",
   "price" and "inflation" is stripped first, and a token that flips direction
   (`non`, `low`, `shortage`, `compression`) blocks the merge outright. That guard
   exists because without it `non-carbonated-soft-drink-growth` merged into
   `carbonated-soft-drink-market-growth`: two opposite forces in one theme.

Every merge prints its aliases in `THEMES.md` (`merged from: …`), so a wrong one is
visible rather than buried. A key can never be lost by any of the three: a key the
model omits is restored as its own theme, and a key it places twice is kept in the
first group.

---

## The three parts of a business

Every theme is researched through the part of the business it acts on, and the
theme records which parts produced it. This is the user-facing framework, and each
lens gets its own search queries and its own section in the ticker file:

| Part | The question | What lands here |
|---|---|---|
| **Trending demand** | What customers are buying, and how that is changing | End-market growth, budget cycles, substitution, new buyers, volume versus price |
| **How it's sold** | How the product reaches the customer | Channel and distributor shifts, pricing model (subscription, licence, usage, per-seat), procurement cycles, customer concentration |
| **How it's made** | What it costs to produce and deliver | Inputs and supply chain, manufacturing and capacity, labour, logistics, the cost curve, regulation of production |

Asking all three is the point. A single "industry outlook" query returns the demand
story — which is the one every sell-side note already tells. The channel and the
cost base are where a qualitative screen finds something the consensus has not
priced, because they are reported by trade press and industry bodies rather than by
the company.

A theme found through two or three parts is the more systemic for it, and
`THEMES.md` prints `Parts 2/3` beside every entry.

---

## What comes out, and how it is ranked

Each trend carries a stance, a verbatim quote with its URL and date, the revenue
stream it acts on, and three anchored 1–5 ratings — each with a **stated basis**:

| Axis | 1 | 3 | 5 |
|---|---|---|---|
| **size** — money moved across the industry | small or niche | $1–10bn | over $100bn or most of the revenue pool |
| **speed** — when it bites | beyond five years | one to three years | already visible in reported numbers |
| **impact** — what it does to *this* company | immaterial | moves a minority stream | decides total revenue or margin direction |

A theme's quantum is the mean of its members' ratings, weighted
`0.40*size + 0.30*speed + 0.30*impact`, then amplified by how many researched names
it reaches:

```
score = quantum * (1 + 0.10 * min(breadth - 1, 5))     # +0% to +50%
```

Size is weighted highest because a theme that moves little money is not interesting
however fast it moves. Breadth is a *factor*, not a fourth axis, so a widely-shared
small theme cannot outrank a large one — five names sharing a triviality must not
beat one name facing a huge force. Rating **dispersion** is printed beside every
mean, because a theme rated 5 by one company and 1 by another averages to a
settled-looking 3.

Each theme then lists its sides: **positively affected**, **negatively affected**,
and **two-sided or unclear** (a company appears on one side only, and lands in the
two-sided column when the same force reaches it both ways). The ticker's own writeup
prints the same sides from the same objects, so the two documents cannot disagree.

---

## Grounding is enforced, not requested

The screener publishes prose, and prose is the one thing a reader cannot check
against a number they already have. So every claim carries evidence, and the
evidence is verified mechanically:

* **Revenue streams** clear one of two tests: the quote appears in the retrieved
  results (a segment table, an earnings release, the company's own segments page),
  or the stream is named in the company's own business summary shipped through
  yfinance. A stream that clears neither is dropped **and listed as dropped**.
* **Trends** must carry a quote that appears word-for-word in the text that was
  retrieved, after folding whitespace and typographic quotes. The quote must be in
  the source it *names*, not merely somewhere in the results — a reader sent to a
  link that does not contain the words is being misled, and the failure is invisible
  in the output. Unsupported claims are dropped with their reason, printed in
  `## Retrieved but discarded`.
* **Every source is dated** on retrieval, with explicit dates only, so a yearless
  "Sept 18" cannot read as today. Evidence older than a year is printed with its age
  as history rather than presented as a current trend.
* **Every source is tagged** by kind — trade press / industry body / named research
  house, company disclosure, vendor market-report page, general media. A vendor page
  that states a market size and a CAGR is usable and is labelled as such, so a
  reader can weigh it against an association survey.
* **Shares are labelled**: `stated`, `approx` (the evidence said "~50%") or
  `derived` (computed from two disclosed figures). A number that is not stated
  anywhere in that form is never presented as though it were.

---

## Layout

```
qualitative/
  qs                     launcher (sets PYTHONPATH, uses the repo venv)
  qts/
    universe.py          the two gates over Nasdaq's listed names
    profile.py           yfinance: description, market cap, price
    streams.py           the exact revenue streams, grounded
    trends.py            the three parts of a business, one lens at a time
    themes.py            trends -> canonical themes, ranked by quantum and breadth
    writeup.py           the two markdown documents, rendered from artifacts
    analysis.py          running a batch and keeping every artifact
    grounding.py         quote verification, dating, source labelling
    cli.py               the qs commands
  tests/test_units.py    42 offline tests: gates, grounding, quantum, rendering
  run_*.sh               the two runs that produced the committed outputs
```

Everything shares the parent pipeline's plumbing: `fig.sources.nasdaq` for the
listed names, `fig.sources.yahoo` (yfinance) for the description and the two
numbers, `fig.sources.ollama` for search and generation, `fig.util.cached_json`
for on-disk caching and `fig.research.source_date` for dating evidence.

Rendering touches no network and no model. `qs themes` rebuilds `THEMES.md` from
the artifacts on disk, so a prompt or merge fix costs nothing to re-apply, a
renderer change is testable offline, and a second wave of tickers *adds* to the
existing theme file rather than replacing it.

```bash
# run the offline tests
PYTHONPATH=qualitative .venv/bin/python -m unittest discover -s qualitative/tests
```

---

## Limits, stated rather than hidden

* **Coverage is the researched batch.** A theme naming three companies was found in
  three companies; it is not a claim that only three are exposed. Every run prints
  the batch it covers.
* **Key convergence depends on research order.** Because the reuse list is whatever
  vocabulary exists when a company is researched, companies in flight together at the
  start of a wave coin their own keys and later ones converge on them. That is a real
  dependency, and it is why the theme file is rebuilt from artifacts rather than
  re-researched: the keys a wave settled on stay stable afterwards.
* **Theme merging is judgement.** One model pass groups the keys, a second reviews the
  groups, and a deterministic token pass catches what both missed. All three are
  validated so a key can never fall out of the file, and every merge prints its
  aliases.
* **The quantum ratings are model judgement on a published rubric**, not measured
  data. The rubric and each rating's stated basis exist so a reader can disagree with
  a number rather than having to trust it.
* **Free sources stay thin for small caps.** A stream named only in the business
  summary is grounded but unquantified, and the writeup says so instead of
  inventing a mix. In the committed 20-name batch, 46 of 85 streams carried a share
  or an amount; the rest are printed as *not disclosed* rather than estimated.
* **Themes are as granular as their evidence.** The committed batch produced 175
  themes from 233 trends, and 80 of those trends (34%) sit in a theme that reaches
  more than one company. Much of the rest is honestly single-company: a global
  games market shift found through Sony is a theme, but only Sony among the twenty
  names is exposed to it. Ten themes reach three or more names, and those are the
  ones at the top of the ranking.
* **A trend is not a forecast.** The screener reports what industry sources say is
  changing; it does not model what it means for a share price, and it makes no
  attempt to time anything.
