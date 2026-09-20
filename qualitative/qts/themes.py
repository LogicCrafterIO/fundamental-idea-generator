"""From per-name trends to ranked themes -- and why the two words are not synonyms.

Trends versus themes
--------------------
The screener uses both words, deliberately, for two different things:

**A trend** is one sourced finding about one company. "US small-business hiring
plans fell for a third month as of June 2026, which cuts the headcount that
Paychex bills per client." It belongs to a ticker, it carries one quote, and it
is written up in that ticker's file.

**A theme** is the industry force that several trends turn out to be instances
of. "Small-business hiring weakness" is a theme: it shows up in the payroll
processor as lower billings, in the staffing firm as lower placement volume, and
in the small-business lender as weaker loan demand -- the same force reaching
three income statements by different mechanisms.

So the master file is a file of **themes**, and the per-ticker files are files of
**trends**. That is the more suitable framing because the thing worth ranking is
the force -- a theme has a size, a speed and an impact that are properties of the
industry, whereas a trend's properties are properties of one company's exposure to
it. The theme is also the only object that can hold both directions at once, which
is the point of listing who is hurt and who is helped by the same story.

Merging without an embedding model
----------------------------------
Each company's trends are extracted independently, so the same force arrives under
slightly different keys (``ai-capex`` from one name, ``ai-infrastructure-capex``
from the next). Two passes reconcile them:

1. **A model pass** over the compact list of raw keys, labels and one example
   claim, which is asked only to group keys that describe the same force and to
   write the canonical label and definition. This is the pass that gets the
   judgement right -- "rate-cut-expectations" and "fed-easing-cycle" are the same
   theme, and token overlap cannot know that.
2. **A deterministic fallback** (:func:`merge_by_tokens`) used when the model is
   unavailable, and applied afterwards regardless, to catch a merge the model
   missed. It only merges keys whose token sets nearly coincide, so it cannot
   invent a grouping.

Both are validated: a key the model dropped silently is restored as its own
theme, and a key it placed in two groups is kept in the first. A merge that loses
a ticker's evidence would be invisible in the output, which is exactly the kind of
loss this pipeline is supposed to refuse.

Ranking a theme
---------------
The rank is the mean of the members' rubric ratings -- size, speed and impact on
their anchored 1-5 scales (:mod:`qts.trends`) -- weighted, then amplified by how
many researched names the theme actually reaches:

    quantum = 0.40*size + 0.30*speed + 0.30*impact     (1.0 to 5.0)
    breadth = distinct tickers with a trend on this theme
    score   = quantum * (1 + 0.10 * min(breadth - 1, 5))   (+0 to +50%)

Size is weighted highest because a theme that moves little money is not
interesting howsoever fast it moves. Breadth is a *factor* rather than a fourth
axis so that it can never outrank a genuinely larger force on its own: five
tickers sharing a small theme must not beat one ticker facing a huge one. The
breadth cap at five names stops a widely-shared triviality from running away with
the list.

Dispersion is published beside the mean: when two names rate the same theme
4 and 2 on impact, the mean of 3 hides a disagreement that a reader needs to see.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from fig.sources import ollama

from .grounding import publisher
from .trends import LENS_LABEL, LENS_KEYS

# Ranking weights. Size first, then speed and impact equally -- see the module
# docstring for why.
WEIGHT_SIZE = 0.40
WEIGHT_SPEED = 0.30
WEIGHT_IMPACT = 0.30
BREADTH_STEP = 0.10
BREADTH_CAP = 5

# Token-overlap threshold for the deterministic merge. High-ish on purpose: a wrong
# merge fuses two unrelated forces and prints one theme where there are two, which is
# worse than printing two entries a reader can see are related.
TOKEN_MERGE_THRESHOLD = 0.6


# Tokens that carry no force of their own. They are dropped before two keys are
# compared, which is what lets "credit-card-balance-growth-moderation" fuse with
# "consumer-credit-card-balance-growth-moderation" while "data-centre-power" stays
# apart from "data-centre-capex" (capex and power are both the force; "growth" is
# not). Without this list every pair of keys in a market-research corpus shares
# "growth" or "demand" and the merge becomes meaningless.
_STOP_TOKENS = {
    "and", "the", "of", "in", "for", "to", "with", "vs",
    "growth", "demand", "trend", "trends", "market", "markets", "outlook",
    "expansion", "expanding", "increase", "increasing", "rise", "rising",
    "pressure", "pressures", "shift", "shifts", "change", "changes", "changing",
    "momentum", "recovery", "recovering", "boom", "surge", "decline", "declining",
    "cost", "costs", "strong", "weak", "weakening", "stronger", "weaker",
    "accelerating", "decelerating", "moderation", "normalization", "normalisation",
    # Money words that describe the measurement rather than the force, so two
    # different inputs do not fuse through them: without these, "copper price
    # inflation" merged with "console hardware price inflation" on the strength of
    # "price" and "inflation" alone -- two unrelated forces in one theme.
    "price", "prices", "pricing", "inflation", "inflationary", "deflation",
    "volume", "volumes", "shipment", "shipments", "spending", "sales",
}

# Tokens that flip the direction of a force. They are excluded from the similarity
# test above, so two keys can look identical without them -- which is exactly how
# "non-carbonated-soft-drink-growth" nearly merged into "carbonated soft drink
# growth", two opposite forces. If one of these is what distinguishes two keys, they
# are not the same theme, whatever else they share.
_POLARITY_TOKENS = {
    "non", "no", "not", "anti", "low", "high", "less", "more", "over", "under",
    "up", "down", "compression", "deflation", "expansion", "decline", "growth",
    "rise", "fall", "falling", "rising", "rebound", "surplus", "shortage", "glut",
    "oversupply", "undersupply", "weak", "strong", "weaker", "stronger",
    "slowdown", "acceleration", "inflation", "deflation",
}


CANONICALISE_PROMPT = """Below are themes extracted independently from the trend \
research of {count} companies. Each line is: key | label | example trend | how many \
companies it was found in.

**Several of these keys are the SAME industry force written differently, and finding \
them is the entire task.** They were coined one company at a time, so a force shared by \
six banks arrives six times under six names. Expect the same deposit-funding pressure \
twice, the same investment-banking fee recovery three times, the same rate path, the \
same tariff, the same AI capital cycle, the same drug patent cliff.

Return ONLY THE GROUPS OF TWO OR MORE KEYS THAT DESCRIBE THE SAME FORCE. A key you do \
not mention stands alone as its own theme -- so a list of every key is a failed answer, \
and so is an empty list. Most of these keys share a force with at least one other.

  "merges": [{{"key": canonical kebab-case slug for the group, "label": plain-English \
title (<= 8 words), "definition": one sentence (<= 25 words) true for every company the \
theme touches, "members": [the EXACT input keys in this group]}}]

HARD RULES:
- Every key named in a group must be copied exactly from the list below. Do not invent
  keys, and do not list a key in more than one group.
- Merge keys that describe the same force even when the wording differs and even when
  they are measured in different places: "deposit-competition-and-funding-costs" and
  "deposit-funding-cost-pressure" are one theme; "wealth-advisory-fee-inflation" and
  "wealth-management-fee-inflation" are one theme.
- A force and its consequence are still two themes: keep "small-business-hiring-weakness"
  apart from "payroll-software-substitution". Keep two different inputs apart:
  "copper-price-inflation" is not "electronic-component-inventory-shortage".
- Opposites never merge: a rise is not a fall, a shortage is not a glut.
- Geography alone does not separate a force: a US and a European version of one global
  trend belong in one group unless the evidence really is region-specific.
- Prefer the key carried by the most companies as the group's canonical key. Never put a
  ticker in a key, and never name a company in a definition.

INPUT KEYS:
{keys}

Return ONLY JSON: {{"merges": [{{...}}]}}"""


# Asked of the *groups* rather than the raw keys. A second pass over the group
# representatives catches what the first pass could not, because two keys naming one force
# are sometimes lexically unrelated ("fed-easing-cycle" and "rate-cut-expectations"), and
# only become comparable once each is a labelled, defined theme. It also costs almost
# nothing: there are far fewer groups than keys.
REGION_PROMPT = """Below are themes built from the trend research of {count} companies. \
Each line is: key | label | definition | how many companies it was found in.

Some of these themes are the same industry force described in different words, or the \
same force seen from two different industries. Merge the ones that are genuinely the same.

Return ONLY the groups of two or more themes that are the same force. A theme you do not \
mention stands alone -- so a list of everything is a failed answer, and so is an empty \
list if any pair below really does describe one force.

  "merges": [{{"key": canonical kebab-case slug, "label": plain-English title \
(<= 8 words), "definition": one sentence (<= 25 words), "members": [the EXACT input keys]}}]

HARD RULES:
- Every key named must be copied exactly from the list. Never list a key twice.
- Same force, not a related force: a driver and its consequence stay separate, and two
  different inputs stay separate. Opposites never merge.
- A region-specific theme stays separate from a global one unless the evidence covers both.

INPUT THEMES:
{keys}

Return ONLY JSON: {{"merges": [{{...}}]}}"""


def _quantum(trends: list[dict]) -> dict:
    """Mean rubric ratings across a theme's member trends, with the dispersion."""
    if not trends:
        return {"size": 0.0, "speed": 0.0, "impact": 0.0, "quantum": 0.0, "spread": 0.0}
    sizes = [t.get("size") or 3 for t in trends]
    speeds = [t.get("speed") or 3 for t in trends]
    impacts = [t.get("impact") or 3 for t in trends]
    size = sum(sizes) / len(sizes)
    speed = sum(speeds) / len(speeds)
    impact = sum(impacts) / len(impacts)
    quantum = WEIGHT_SIZE * size + WEIGHT_SPEED * speed + WEIGHT_IMPACT * impact
    # Dispersion across members, so a theme rated 5 and 1 does not read like a
    # settled 3.
    spread = round((max(sizes) - min(sizes) + max(speeds) - min(speeds) + max(impacts) - min(impacts)) / 3.0, 2)
    return {
        "size": round(size, 2),
        "speed": round(speed, 2),
        "impact": round(impact, 2),
        "quantum": round(quantum, 2),
        "spread": spread,
    }


def merge_by_tokens(groups: list[list[str]]) -> list[list[str]]:
    """Deterministic merge of near-identical keys *within* each group.

    Two keys merge when their significant tokens overlap by at least
    ``TOKEN_MERGE_THRESHOLD`` of the smaller set. It never merges across groups, so
    it cannot undo the model's judgement that two forces are distinct.
    """
    out: list[list[str]] = []
    for group in groups:
        merged: list[list[str]] = []
        for key in group:
            placed = False
            for bucket in merged:
                if _near_identical(key, bucket[0]):
                    bucket.append(key)
                    placed = True
                    break
            if not placed:
                merged.append([key])
        out.extend(merged)
    return out


def _significant(key: str) -> set[str]:
    """The tokens of a key that carry force, with generic wording dropped."""
    tokens = set(key.split("-"))
    return tokens - _STOP_TOKENS or tokens


def _near_identical(one: str, other: str) -> bool:
    """Do two keys name the same force closely enough to merge mechanically?

    Three tests, in order: at least two significant tokens in common, enough overlap
    relative to the shorter key, and nothing in the difference that flips direction.
    The third test is what keeps opposites apart once the generic wording has been
    stripped -- see ``_POLARITY_TOKENS``.
    """
    left, right = _significant(one), _significant(other)
    shared = left & right
    if len(shared) < 2:
        return False
    if (left ^ right) & _POLARITY_TOKENS:
        return False
    return len(shared) / min(len(left), len(right)) >= TOKEN_MERGE_THRESHOLD


def merge_groups_by_representative(
    groups: list[list[str]], weights: dict[str, int] | None = None
) -> list[list[str]]:
    """Merge whole groups whose representative keys nearly coincide.

    This is the safety net, and it exists because of a failure that actually
    happened: the grouping model returned 232 groups of one, so the merge produced
    208 themes from 220 trends and the six banks in the batch never shared a theme.
    A model that answers "one group per key" is a valid answer to the schema and a
    useless answer to the question, so the deterministic pass does not depend on it.

    Groups are compared by their representative key -- the member key carried by the
    most trends -- in descending evidence order, so the biggest group absorbs the
    smaller ones and the canonical key stays the best-evidenced one.
    """
    weights = weights or {}
    ordered = sorted(groups, key=lambda g: -sum(weights.get(k, 1) for k in g))
    clusters: list[tuple[str, list[str]]] = []
    for group in ordered:
        rep = max(group, key=lambda k: (weights.get(k, 1), len(k)))
        for index, (cluster_rep, members) in enumerate(clusters):
            if _near_identical(rep, cluster_rep):
                members.extend(group)
                clusters[index] = (cluster_rep, members)
                break
        else:
            clusters.append((rep, list(group)))
    return [members for _, members in clusters]


def _merge_groups_from_reply(data: dict, known: set[str], used: set[str]) -> list[list[str]]:
    """Read a merges-only reply into groups of keys, dropping anything unknown.

    The reply lists only groups of two or more, so a key it does not mention simply
    stands alone -- which is what makes the output small enough for one call to cover
    a whole batch of tickers. Two guards: a key listed twice (in two groups) is kept
    in the first, because a duplicated member would double-count its evidence in the
    ranking, and a key the model invented is dropped rather than trusted.
    """
    groups: list[list[str]] = []
    for merge in data.get("merges") or []:
        if not isinstance(merge, dict):
            continue
        members = []
        for raw in merge.get("members") or []:
            key = str(raw).strip().lower()
            if key in known and key not in used:
                members.append(key)
                used.add(key)
        if len(members) >= 2:
            groups.append(members)
        elif members:
            # A "merge" of one is not a merge; releasing the key lets it be
            # considered again by a later pass instead of pinning it alone.
            used.discard(members[0])
    return groups


def _call(prompt: str, *, model: str | None) -> dict:
    try:
        reply = ollama.chat(
            [{"role": "user", "content": prompt}], model=model or ollama.DEFAULT_MODEL
        )
        return ollama.parse_json_object(reply["text"])
    except Exception:
        return {}


def _model_groups(keys: list[dict], *, model: str | None = None) -> list[list[str]]:
    """Group raw theme keys with two model passes. Returns groups of keys.

    Why the reply holds only merges
    -------------------------------
    The obvious design -- ask for every group, one entry per key -- does not work at
    this size, and the failure is quiet: asked to place the 232 keys one 20-company
    batch produces, the model returns a handful of merges and leaves the rest as
    singletons. That is a valid answer to the schema and a useless answer to the
    question, and it is what the first version of this function did, leaving 200
    themes where the deliverable promises shared ones. Asking instead for *only the
    groups of two or more* makes the output roughly a third the size, so one call can
    cover every key and the model spends its budget on the judgement that matters.

    Why there is a second pass
    --------------------------
    Two keys naming one force are sometimes lexically unrelated -- "fed-easing-cycle"
    from one name, "rate-cut-expectations" from another -- and the first pass sees them
    as two lines in a list of 232. Once each is a labelled, defined theme, they are
    comparable, so the second pass runs over the *groups* rather than the keys. It is
    cheap: there are far fewer groups than keys.
    """
    if not keys or not ollama.has_key():
        return []

    company_count = len({s for item in keys for s in item.get("symbols") or []}) or len(keys)

    def key_lines(items: list[dict]) -> str:
        return "\n".join(
            f"{item['key']} | {item.get('label') or ''} | {(item.get('example') or '')[:90]} | {item.get('count') or 1}"
            for item in items
        )

    # Pass 1: the keys themselves.
    known = {item["key"] for item in keys}
    used: set[str] = set()
    groups = _merge_groups_from_reply(
        _call(CANONICALISE_PROMPT.format(count=company_count, keys=key_lines(keys)), model=model),
        known,
        used,
    )

    # Everything not merged stands alone, then the standalone themes and the merged
    # ones are both passed to pass 2 as groups.
    singletons = [[item["key"]] for item in keys if item["key"] not in used]
    groups.extend(singletons)
    if len(groups) < 4:
        return groups

    # Pass 2: the groups, by representative key. The representative is the key of the
    # group's largest member, so a theme is named after what it is mostly about.
    weights = {item["key"]: item.get("count") or 1 for item in keys}
    labels = {item["key"]: item.get("label") or item["key"] for item in keys}
    definitions = {item["key"]: item.get("definition") or "" for item in keys}
    reps = [max(group, key=lambda k: (weights.get(k, 1), len(k))) for group in groups]
    rep_lines = "\n".join(
        f"{rep} | {labels.get(rep, rep)} | {definitions.get(rep, '')} | {weights.get(rep, 1)}"
        for rep in reps
    )
    known_reps = set(reps)
    used_reps: set[str] = set()
    extra = _merge_groups_from_reply(
        _call(REGION_PROMPT.format(count=company_count, keys=rep_lines), model=model),
        known_reps,
        used_reps,
    )

    # Fold pass-2 merges back onto the groups they name: a merge of representatives is
    # a merge of the groups those representatives stand for.
    by_rep = {rep: group for rep, group in zip(reps, groups)}
    folded: list[list[str]] = []
    absorbed: set[str] = set()
    for merge in extra:
        members: list[str] = []
        for rep in merge:
            members.extend(by_rep.get(rep, [rep]))
            absorbed.add(rep)
        if len(members) >= 2:
            folded.append(members)
    for rep, group in zip(reps, groups):
        if rep not in absorbed:
            folded.append(group)
    return folded


def item_count(items: list[dict]) -> int:
    """How many companies contributed to the raw theme list."""
    return len({t for item in items for t in item.get("symbols", [])}) or len(items)


def collect(analyses: list[dict]) -> list[dict]:
    """Every trend from every analysis, tagged with the ticker it came from.

    The artifact stores the trend stage as a dict (queries, results index, trends,
    dropped), so the list is one level down -- and reading it a level too high
    yields the stage's own keys, which iterate as strings.
    """
    out = []
    for analysis in analyses:
        symbol = analysis["symbol"]
        company = (analysis.get("profile") or {}).get("name")
        for trend in (analysis.get("trends") or {}).get("trends") or []:
            out.append({**trend, "symbol": symbol, "company": company})
    return out


def build(
    analyses: list[dict],
    *,
    model: str | None = None,
    canonicalise: bool = True,
) -> dict:
    """Aggregate analyses into ranked themes.

    ``analyses`` is the list of per-ticker research artifacts written by
    :mod:`qts.analysis`, so the master file can be rebuilt from disk without
    re-running any research -- which is what makes a second wave additive.
    """
    trends = collect(analyses)
    by_key: dict[str, list[dict]] = defaultdict(list)
    for trend in trends:
        by_key[trend["theme_key"]].append(trend)

    raw = [
        {
            "key": key,
            "label": Counter(t.get("theme_label") for t in items).most_common(1)[0][0] or key,
            "definition": Counter(t.get("theme_definition") for t in items if t.get("theme_definition")).most_common(1)[0][0]
            if any(t.get("theme_definition") for t in items)
            else "",
            "example": (items[0].get("claim") or ""),
            "count": len({t["symbol"] for t in items}),
            "symbols": sorted({t["symbol"] for t in items}),
        }
        for key, items in by_key.items()
    ]
    raw.sort(key=lambda item: (-item["count"], item["key"]))

    groups: list[list[str]] = []
    if canonicalise:
        groups = _model_groups(raw, model=model)
    if not groups:
        groups = [[item["key"]] for item in raw]
    groups = merge_by_tokens(groups)
    # The safety net runs whatever the model did, including when it grouped
    # everything into singletons: see merge_groups_by_representative.
    weights = {key: len(items) for key, items in by_key.items()}
    groups = merge_groups_by_representative(groups, weights)
    # Order groups by the evidence they carry, so the canonical key of the
    # biggest group is the one the theme is named after.
    groups.sort(key=lambda g: -sum(len(by_key[k]) for k in g))

    lookup = {item["key"]: item for item in raw}
    themes = []
    for group in groups:
        members = [t for key in group for t in by_key.get(key, [])]
        if not members:
            continue
        canonical = max(group, key=lambda k: len(by_key.get(k, [])))
        info = lookup[canonical]
        themes.append(_assemble(canonical, group, members, info))

    assign_ranks(themes)
    return {
        "themes": themes,
        "raw_theme_count": len(raw),
        "raw_keys": raw,
        "groups": groups,
        "trend_count": len(trends),
        "tickers": sorted({a["symbol"] for a in analyses}),
        "merged": len(raw) - len(themes),
    }


def _stronger(current: dict | None, candidate: dict) -> dict:
    """Keep the entry that matters most for one symbol under one theme.

    A ticker can contribute two trends to a theme -- both merged into the same force
    from different angles, which is a finding rather than a bug -- but it must appear
    on exactly one side, listed once. The stronger of the two is kept (most impact,
    then most size), and the count is recorded so the merge stays visible.
    """
    if current is None:
        return {**candidate, "trends_on_theme": 1}
    key = lambda e: (e.get("impact") or 0, e.get("size") or 0)
    best = candidate if key(candidate) > key(current) else current
    return {**best, "trends_on_theme": (current.get("trends_on_theme") or 1) + 1}


def _assemble(key: str, group: list[str], members: list[dict], info: dict) -> dict:
    """One canonical theme: its members, its sides, and its quantum.

    ``members`` keeps every trend -- each carries its own quote, and the evidence list
    should show all of it -- while the sides keep one entry per symbol, so a company
    is never printed twice on one theme.
    """
    positive: dict[str, dict] = {}
    negative: dict[str, dict] = {}
    mixed: dict[str, dict] = {}
    for trend in members:
        entry = {
            "symbol": trend["symbol"],
            "company": trend.get("company"),
            "lens": trend["lens"],
            "stream": trend.get("stream"),
            "claim": trend.get("claim"),
            "why": trend.get("why"),
            "quote": trend.get("quote"),
            "url": trend.get("url"),
            "publisher": trend.get("publisher"),
            "source_type": trend.get("source_type"),
            "as_of": trend.get("as_of"),
            "age_days": trend.get("age_days"),
            "stale": trend.get("stale"),
            "impact": trend.get("impact"),
            "size": trend.get("size"),
            "speed": trend.get("speed"),
        }
        symbol = trend["symbol"]
        direction = trend.get("direction")
        if direction == "tailwind" and symbol in negative:
            # The same force lands on both sides of one company's own numbers.
            entry["two_sided"] = True
            mixed[symbol] = _stronger(mixed.get(symbol), entry)
        elif direction == "headwind" and symbol in positive:
            entry["two_sided"] = True
            mixed[symbol] = _stronger(mixed.get(symbol), entry)
        elif direction == "tailwind":
            positive[symbol] = _stronger(positive.get(symbol), entry)
        elif direction == "headwind":
            negative[symbol] = _stronger(negative.get(symbol), entry)
        else:
            mixed[symbol] = _stronger(mixed.get(symbol), entry)

    # A name listed on both sides belongs in the mixed column, not twice.
    for symbol in list(mixed):
        positive.pop(symbol, None)
        negative.pop(symbol, None)

    quantum = _quantum(members)
    breadth = len({t["symbol"] for t in members})
    factor = 1 + BREADTH_STEP * min(max(breadth - 1, 0), BREADTH_CAP)
    evidence = {t.get("url") for t in members if t.get("url")}
    parts = [lens for lens in LENS_KEYS if any(t["lens"] == lens for t in members)]
    source_mix = Counter(t.get("source_type") or "general" for t in members)

    return {
        "key": key,
        "aliases": [k for k in group if k != key],
        "label": info.get("label") or key.replace("-", " "),
        "definition": info.get("definition") or "",
        "parts": parts,
        "part_labels": [LENS_LABEL[p] for p in parts],
        "streams": sorted({t.get("stream") for t in members if t.get("stream") and t["stream"] != "the business overall"}),
        "quantum": quantum,
        "breadth": breadth,
        "breadth_factor": round(factor, 2),
        "score": round(quantum["quantum"] * factor, 2),
        "evidence_count": len(evidence),
        "source_mix": dict(source_mix),
        "trend_count": len(members),
        "positive": [positive[s] for s in sorted(positive)],
        "negative": [negative[s] for s in sorted(negative)],
        "mixed": [mixed[s] for s in sorted(mixed)],
        "sides": {
            "positive": len(positive),
            "negative": len(negative),
            "mixed": len(mixed),
        },
        "net": _net(len(positive), len(negative)),
        "tickers": sorted({t["symbol"] for t in members}),
        "members": members,
    }


def _net(positive: int, negative: int) -> str:
    if positive and not negative:
        return "tailwind"
    if negative and not positive:
        return "headwind"
    if not positive and not negative:
        return "unclear"
    if positive >= negative * 2:
        return "mostly tailwind"
    if negative >= positive * 2:
        return "mostly headwind"
    return "two-sided"


def assign_ranks(themes: list[dict]) -> None:
    """Rank in place: score, then evidence, then label.

    Ties are broken by how much evidence a theme rests on, so two themes of equal
    quantum are ordered by the one a reader can check more of.
    """
    themes.sort(key=lambda t: (-t["score"], -t["evidence_count"], t["label"].lower()))
    for index, theme in enumerate(themes, start=1):
        theme["rank"] = index


def publisher_of(url: str | None) -> str | None:
    return publisher(url)
