"""Running one screen twice, and paying for the overlap once.

What this module decides
------------------------
The two scoring modes in :mod:`fig.discover` rank *the same screened rows*. So a
run that publishes both needs exactly one screening pass and, for the naming, one
generation per distinct ``(ticker, direction)`` -- not one per folder. That is the
whole job here: turn each variant's ranked picks into

* a de-duplicated list of work, and
* a map from that work to the folders it has to be written into.

The cases, and why each is what it is
-------------------------------------
**Overlap, same side.** The same name is picked long by both screens. One note is
generated and copied into both folders. A note is a function of the packet and the
direction, and both are identical here, so a second generation would spend tokens
to produce a second copy of the same text -- and could produce a *different* text
on a sampled run, which is worse than wasteful: two folders would show two
different writeups of one idea with no way to tell that from a real disagreement.

**Overlap, opposite sides.** One screen says long, the other short. These are two
different notes by construction -- the direction drives the catalyst argument, the
watch lines and the option structure -- so both are generated, and the ticker is
reported as a **disagreement**. It is not an error to be resolved: a revision-only
screen can rank a name long while the divergence screen reads the same estimates
against a falling tape as a short, and which one is right is the reader's question,
not the planner's.

**No overlap.** The usual case. One note, one folder.

Both sides of a disagreement are surfaced, never silently reconciled: an index that
listed the two folders without mentioning that they contradict each other on a
ticker would be the one output of this pipeline a careful reader could still be
misled by.
"""

from __future__ import annotations

from .discover import DEFAULT_SCORING, SCORING_MODES

# The variants a run can publish. Names match :data:`fig.discover.SCORING_MODES`
# because a variant *is* a scoring mode; this alias exists for the output side of
# the pipeline, where "variant" is the clearer word.
VARIANTS = SCORING_MODES
DEFAULT_VARIANT = DEFAULT_SCORING

# What each variant is, in one clause, for the index that has to say which folder
# a reader is holding. Kept here rather than in the renderer so the two screens'
# descriptions cannot drift from the modes they describe.
VARIANT_TITLES = {
    "revisions": "consensus revision only",
    "divergence": "revision versus price",
}


def folder_name(variant: str) -> str:
    """The subfolder a variant publishes into."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}; expected one of {VARIANTS}")
    return variant


def plan(picks: dict[str, list[dict]]) -> dict:
    """Turn each variant's ranked rows into one work list plus its destinations.

    ``picks`` maps a variant name to the rows the screen ranked for it (each row
    carrying ``symbol`` and ``direction_hint``). Returns::

        {
          "work": [{"symbol", "direction", "variants": [..], "scores": {..}}],
          "membership": {variant: [symbol, ...]},        # what that folder publishes
          "disagreements": [{"symbol", "long": variant, "short": variant}],
        }

    ``scores`` keeps each variant's number for the ticker so the index can show why
    the two folders' orders differ, including for a name both screens picked.
    """
    order = [v for v in VARIANTS if v in picks]
    for variant in picks:
        if variant not in VARIANTS:
            raise ValueError(f"unknown variant {variant!r}; expected one of {VARIANTS}")

    # (symbol, direction) -> the work item, so the second variant's sighting of the
    # same name on the same side lands on the existing item instead of a new one.
    by_key: dict[tuple[str, str], dict] = {}
    work: list[dict] = []
    membership: dict[str, list[str]] = {variant: [] for variant in order}
    seen_direction: dict[str, dict[str, str]] = {}

    for variant in order:
        for row in picks.get(variant) or []:
            symbol = str(row.get("symbol") or "").upper()
            direction = str(row.get("direction_hint") or "long").lower()
            if not symbol:
                continue
            if symbol not in membership[variant]:
                membership[variant].append(symbol)

            seen_direction.setdefault(symbol, {}).setdefault(direction, variant)

            key = (symbol, direction)
            item = by_key.get(key)
            if item is None:
                item = {
                    "symbol": symbol,
                    "direction": direction,
                    "variants": [],
                    "scores": {},
                }
                by_key[key] = item
                work.append(item)
            if variant not in item["variants"]:
                item["variants"].append(variant)
            item["scores"][variant] = row.get("score")

    disagreements = [
        {
            "symbol": symbol,
            "directions": dict(directions),
            "variants": sorted({v for v in directions.values()}),
        }
        for symbol, directions in seen_direction.items()
        if len(directions) > 1
    ]
    disagreements.sort(key=lambda d: d["symbol"])

    return {
        "work": work,
        "membership": membership,
        "disagreements": disagreements,
        "variants": order,
    }


def describe(planned: dict) -> list[str]:
    """Human lines for a run: what each folder publishes, and what the overlap saved."""
    lines: list[str] = []
    for variant in planned.get("variants") or []:
        picked = planned["membership"].get(variant) or []
        lines.append(f"  {variant:10} {VARIANT_TITLES.get(variant, variant)}: {len(picked)} name(s)")
    unique = len(planned.get("work") or [])
    total = sum(len(v) for v in (planned.get("membership") or {}).values())
    if total > unique:
        lines.append(f"  {total - unique} note(s) shared between folders, generated once")
    return lines
