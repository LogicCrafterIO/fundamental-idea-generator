"""The two outputs, rendered from the JSON artifacts.

Nothing here calls a model. Every number and every sentence in the published
markdown was written and verified during research and stored in
``qualitative/analyses/<SYM>.json``; rendering is a pure function of those files.
That separation is what lets the master theme file be rebuilt -- after a prompt
change, a new wave, or a merge fix -- without spending a single search or token,
and it means a difference between two runs of the same artifacts is a bug in the
renderer rather than a change of mind by a model.

Two documents come out:

* ``qualitative/tickers/<SYM>.md`` -- the per-ticker writeup: the detailed
  description, the exact revenue streams, then the trends found in each of the
  three parts of the business, each with its quote, its source and its rating.
* ``qualitative/themes/THEMES.md`` -- the master file: every theme, ranked, with
  the tickers it helps and the tickers it hurts.

Both print their discards. A file that shows six revenue streams and stays silent
about the four that failed grounding is a file that cannot be audited, and
grounding failures are the one thing a reader would want to know about.
"""

from __future__ import annotations

from datetime import date

from fig.util import human_money

from . import streams as streams_mod
from .trends import LENSES, LENS_LABEL

DIRECTION_MARK = {
    "tailwind": "tailwind",
    "headwind": "headwind",
    "two-sided": "two-sided",
}

# What kind of source a quote came from. Printed beside every trend so a reader
# can weigh an association survey differently from a vendor page that states a
# market size and a CAGR and nothing else.
SOURCE_TYPE_LABEL = {
    "trade": "trade press, industry body or named research house",
    "company": "company disclosure",
    "market_research": "vendor market-report page",
    "general": "general media",
}


def _stream_share(stream: dict) -> str:
    """The share of revenue, recovering it from the evidence line when unpicked.

    The model does not always take an approximate share the evidence states outright --
    "Sparkling Soft Drinks | ~50%" came back as "not disclosed" with that very line
    printed underneath it -- so the conversion is done here instead, and labelled, so
    the reader can see the figure was read off the quoted line rather than asserted.
    """
    value = stream.get("revenue_share")
    basis = stream.get("revenue_share_basis")
    recovered = None
    if value is None:
        recovered = streams_mod.share_from_quote(stream.get("quote"), stream.get("name"))
        if recovered:
            value, basis = recovered
    text = _share(value, basis)
    if recovered:
        text += ", from the evidence line"
    return text


def _stream_amount(stream: dict) -> str:
    """The disclosed amount, or a dash -- never a bare number of unknown units.

    The guard is applied here as well as at extraction, because a published figure is
    the thing a reader acts on: see :func:`qts.streams.amount_is_usable`.
    """
    amount = stream.get("amount")
    if not streams_mod.amount_is_usable(amount):
        return "—"
    return str(amount)


def _share(value, basis: str | None = None) -> str:
    if value is None:
        return "not disclosed"
    text = f"{value * 100:.0f}%"
    # A share the model worked out from two disclosed figures, or read off a
    # rounded figure, is marked -- a reader checking it against a filing will not
    # find it stated there in that form.
    if basis == "stated":
        return text
    return f"{text} ({'approx' if basis == 'approximate' else 'derived'})"


def _link(url: str | None, publisher: str | None, as_of: str | None) -> str:
    """A citation: ``[publisher, date](url)``, degrading honestly when parts are missing."""
    label = publisher or "source"
    if as_of:
        label += f", {as_of}"
    if url:
        return f"[{label}]({url})"
    return f"{label} (no link)"


def _age_note(trend: dict) -> str:
    age = trend.get("age_days")
    if age is None:
        return " date unknown"
    if age <= 60:
        return ""
    if age <= 500:
        return f" **{age // 30} months old**"
    return f" **{age // 365} years old -- historical, not a current trend**"


def _gates_line(analysis: dict) -> str:
    profile = analysis.get("profile") or {}
    price = profile.get("price")
    cap = profile.get("market_cap")
    price_text = f"${price:,.2f}" if isinstance(price, (int, float)) else "n/a"
    return (
        f"Share price {price_text} (screen: <= $100) | Market cap {human_money(cap)} "
        f"(screen: >= $1B). Those two numbers are the only quantitative inputs; "
        f"everything below is qualitative."
    )


def render_ticker(analysis: dict, theme_index: dict | None = None) -> str:
    """One ticker's writeup."""
    theme_index = theme_index or {}
    profile = analysis.get("profile") or {}
    streams = analysis.get("streams") or {}
    trends = analysis.get("trends") or {}
    symbol = analysis["symbol"]
    name = profile.get("name") or symbol

    out: list[str] = [f"# {symbol} — {name}", ""]
    out.append(f"*{_gates_line(analysis)}*")
    out.append("")

    facts = []
    if profile.get("sector") or profile.get("industry"):
        facts.append(f"**Sector / industry:** {profile.get('sector') or 'n/a'} / {profile.get('industry') or 'n/a'}")
    if profile.get("employees"):
        facts.append(f"**Employees:** {profile['employees']:,}")
    if profile.get("country"):
        facts.append(f"**Country:** {profile['country']}")
    if profile.get("website"):
        facts.append(f"**Website:** {profile['website']}")
    facts.append(f"**Researched:** {analysis.get('researched_on') or date.today().isoformat()} | "
                 f"**search results read:** {trends.get('results_count', 0)} | "
                 f"**lenses covered:** {', '.join(LENS_LABEL[k] for k, v in (trends.get('coverage') or {}).items() if v) or 'none'}")
    out.extend(facts)
    out.append("")

    conflicts = profile.get("gate_conflicts") or []
    if conflicts:
        out.append(f"> **Gate conflict:** yfinance and Nasdaq disagree — {'; '.join(conflicts)}. "
                   f"The name is kept and the disagreement is shown rather than resolved silently.")
        out.append("")

    # ---- description -----------------------------------------------------
    out.append("## Description")
    out.append("")
    description = streams.get("description") or profile.get("summary")
    if description:
        out.append(description)
    else:
        out.append("_No description could be grounded for this name._")
    if streams.get("description") and profile.get("summary") and streams["description"].strip() != profile["summary"].strip():
        out.append("")
        out.append(f"<details><summary>Company's own summary (yfinance)</summary>")
        out.append("")
        out.append(profile["summary"])
        out.append("")
        out.append("</details>")
    out.append("")

    # ---- revenue streams -------------------------------------------------
    out.append("## Revenue streams")
    out.append("")
    if streams.get("streams"):
        basis_note = {
            "product_line": "cut along the product and service lines the company reports",
            "revenue_type": "cut along how the company earns money (interest, fee, premium, subscription)",
            "business_segment": "cut along the company's reported business segments",
            "geography": "cut along geography, because that is the only split the company discloses",
        }.get(streams.get("split_basis") or "", "")
        if basis_note:
            out.append(f"*Streams are {basis_note}.*")
            out.append("")
        out.append("| # | Stream | What it is | Share of revenue | Amount as disclosed | Who pays |")
        out.append("|---|---|---|---|---|---|")
        for index, stream in enumerate(streams["streams"], start=1):
            out.append(
                f"| {index} | **{stream['name']}** | {stream.get('what_it_is') or '—'} | "
                f"{_stream_share(stream)} | "
                f"{_stream_amount(stream)} | {stream.get('customer') or '—'} |"
            )
        out.append("")
        out.append("**Evidence for the split**, one quote per source: each entry lists the streams it supports.")
        out.append("")
        # Four geographic segments usually come off one page of one filing, so
        # printing the identical quote four times would bury the four different
        # streams it supports.
        grouped: dict[tuple, list[dict]] = {}
        for stream in streams["streams"]:
            if not stream.get("quote"):
                continue
            grouped.setdefault((stream["quote"], stream.get("url")), []).append(stream)
        for (quote, url), group in grouped.items():
            names = ", ".join(s["name"] for s in group)
            note = " *(from the company's own business summary)*" if group[0].get("grounded_by") == "business_summary" else ""
            out.append(
                f"- **{names}**  \n  > \"{quote}\" — "
                f"{_link(url, group[0].get('publisher'), group[0].get('as_of'))}{note}"
            )
        if streams.get("geography"):
            out.append("")
            out.append(f"**Geographic mix:** {streams['geography']}")
        if streams.get("customer_concentration"):
            out.append("")
            out.append(f"**Customer concentration:** {streams['customer_concentration']}")
    else:
        out.append("_No revenue stream could be grounded from the retrieved sources._")
    if streams.get("notes"):
        out.append("")
        out.append(f"**Mix shift:** {streams['notes']}")
    out.append("")

    # ---- trends by part of the business ---------------------------------
    out.append("## Trends")
    out.append("")
    by_lens: dict[str, list[dict]] = {lens["key"]: [] for lens in LENSES}
    for trend in trends.get("trends") or []:
        by_lens.setdefault(trend["lens"], []).append(trend)

    for lens in LENSES:
        found = by_lens.get(lens["key"], [])
        out.append(f"### {lens['label']}")
        out.append("")
        out.append(f"*{lens['question'].capitalize()}.*")
        out.append("")
        if not found:
            out.append("_No grounded trend was found for this part of the business in the retrieved sources._")
            out.append("")
            continue
        for trend in found:
            out.append(f"- **{trend['claim']}**  \n"
                       f"  *Direction:* {DIRECTION_MARK.get(trend['direction'], trend['direction'])} for {symbol} | "
                       f"*Stream:* {trend.get('stream') or 'the business overall'}")
            if trend.get("why"):
                out.append(f"  *How it reaches the numbers:* {trend['why']}")
            out.append(
                f"  *Quantum:* size **{trend['size']}** ({trend.get('size_basis') or 'basis not stated'}), "
                f"speed **{trend['speed']}** ({trend.get('speed_basis') or 'basis not stated'}), "
                f"impact **{trend['impact']}** ({trend.get('impact_basis') or 'basis not stated'})"
            )
            out.append(
                f"  *Theme:* {trend.get('theme_label') or trend['theme_key']} (`{trend['theme_key']}`) | "
                f"*Source type:* {SOURCE_TYPE_LABEL.get(trend.get('source_type'), 'general')}"
            )
            if trend.get("quote"):
                out.append(
                    f"  > \"{trend['quote']}\" — {_link(trend.get('url'), trend.get('publisher'), trend.get('as_of'))}"
                    f"{_age_note(trend)}"
                )
            if trend.get("stream_note"):
                out.append(f"  *Note:* {trend['stream_note']}")
            out.append("")

    # ---- themes affecting this ticker -----------------------------------
    entries = theme_index.get(symbol) or []
    out.append("## Themes affecting this ticker")
    out.append("")
    if entries:
        out.append("| Theme | Rank | Parts | Direction for " + symbol + " | Impact |")
        out.append("|---|---|---|---|---|")
        for entry in entries:
            theme = entry["theme"]
            out.append(
                f"| **{theme['label']}** (`{theme['key']}`) | #{theme['rank']} | "
                f"{', '.join(theme['part_labels'])} | {entry['side']} | {entry.get('impact') or '—'} |"
            )
        out.append("")
        for entry in entries:
            theme = entry["theme"]
            out.append(f"- **{theme['label']}** — {theme['definition'] or 'no definition recorded'}")
            out.append(f"  {entry['side']} for {symbol}: {entry.get('why') or entry.get('claim') or ''}")
    else:
        out.append("_No theme was built from this name's trends._")
    out.append("")

    # ---- discards --------------------------------------------------------
    dropped_streams = streams.get("dropped") or []
    dropped_trends = trends.get("dropped") or []
    if dropped_streams or dropped_trends:
        out.append("## Retrieved but discarded")
        out.append("")
        out.append("Claims that failed grounding are shown here rather than quietly dropped: "
                   "each one is a claim a model produced whose quote could not be found in the source it named.")
        out.append("")
        for item in dropped_streams:
            out.append(f"- revenue stream **{item.get('name')}** — dropped: {item.get('drop_reason')}")
        for item in dropped_trends:
            out.append(f"- trend \"{(item.get('claim') or '')[:110]}\" — dropped: {item.get('drop_reason')}")
        out.append("")

    # ---- sources ---------------------------------------------------------
    sources = _sources_for(analysis)
    if sources:
        out.append("## Sources")
        out.append("")
        for url, label in sources:
            out.append(f"- {label} <{url}>")
        out.append("")

    out.append("---")
    out.append("")
    out.append("*Method: universe from Nasdaq's listed names gated on price <= $100 and "
               "market cap >= $1B; description and market cap from yfinance; revenue streams and "
               "trends from web/industry search, every quote verified against the retrieved text. "
               "Generated by `qts` in `qualitative/`.*")
    out.append("")
    return "\n".join(out)


def _sources_for(analysis: dict) -> list[tuple[str, str]]:
    seen: dict[str, str] = {}
    streams = analysis.get("streams") or {}
    for stream in streams.get("streams") or []:
        if stream.get("url"):
            seen.setdefault(stream["url"], f"{stream.get('publisher') or 'source'} ({stream.get('as_of') or 'date unknown'})")
    for trend in (analysis.get("trends") or {}).get("trends") or []:
        if trend.get("url"):
            seen.setdefault(trend["url"], f"{trend.get('publisher') or 'source'} ({trend.get('as_of') or 'date unknown'})")
    return list(seen.items())


def theme_impact_index(themes: list[dict]) -> dict[str, list[dict]]:
    """``{symbol: [{theme, side, why, impact}]}``, sorted by theme rank.

    The per-ticker file needs to name the themes that touch it, and the side it is
    on for each. Built from the same objects the master file prints, so the two
    documents cannot disagree about who is helped and who is hurt.
    """
    index: dict[str, list[dict]] = {}
    for theme in themes:
        for side, bucket in (("positive", theme["positive"]), ("negative", theme["negative"]), ("mixed", theme["mixed"])):
            for member in bucket:
                index.setdefault(member["symbol"], []).append(
                    {
                        "theme": theme,
                        "side": {"positive": "helps it", "negative": "hurts it", "mixed": "two-sided or unclear"}[side],
                        "why": member.get("why"),
                        "claim": member.get("claim"),
                        "impact": member.get("impact"),
                        "lens": member.get("lens"),
                    }
                )
    for entries in index.values():
        entries.sort(key=lambda e: e["theme"]["rank"])
    return index


def render_master(
    built: dict,
    *,
    analyses: list[dict],
    gates: dict | None = None,
    model: str | None = None,
    generated: date | None = None,
) -> str:
    """The master theme file: ranked themes, both sides, and the ticker index."""
    gates = gates or {}
    themes = built.get("themes") or []
    day = (generated or date.today()).isoformat()
    price = gates.get("max_price")
    cap = gates.get("min_market_cap")
    price_text = "no cap" if price is None else f"<= ${price:,.0f}"
    cap_text = "no floor" if cap is None else f">= {human_money(cap)}"

    out: list[str] = ["# Themes", ""]
    out.append(f"*Every theme found by the qualitative screener, ranked. Generated {day}.*")
    out.append("")
    out.append(
        f"Built from **{len(built.get('tickers') or [])} researched companies** "
        f"({', '.join(built.get('tickers') or []) or 'none'}) and "
        f"**{built.get('trend_count', 0)} grounded trends**, which collapsed into "
        f"**{len(themes)} themes** ({built.get('merged', 0)} duplicate keys merged)."
    )
    out.append("")
    out.append("## How this file is built")
    out.append("")
    out.append(f"**The screen.** Nasdaq's listed names, gated on share price {price_text} and "
               f"market cap {cap_text}. Those two numbers are the *only* quantitative inputs: there is no "
               f"multiple, no estimate revision, no price momentum and no earnings date anywhere in this "
               f"screener, and the batch a company lands in is an ordering by market cap for research "
               f"coverage, not a ranking of the business.")
    out.append("")
    out.append("**Trend versus theme.** A *trend* is one sourced finding about one company; a *theme* is "
               "the industry force that several trends turn out to be instances of. The per-ticker files in "
               "`../tickers/` hold trends; this file holds themes.")
    out.append("")
    out.append("**Three parts of a business.** Every theme is researched through the part of the business it "
               "acts on, and the theme records which parts produced it: *Trending demand* (what customers buy), "
               "*How it's sold* (channel, pricing model, procurement, concentration) and *How it's made* "
               "(inputs, supply chain, capacity, labour, cost curve). A theme found through more than one part "
               "is the more systemic for it.")
    out.append("")
    out.append("**Evidence.** Every trend carries a verbatim quote from a retrieved source, checked "
               "word-for-word against the text that was retrieved, and dated. Claims whose quote could not be "
               "found are not published — they are listed as discarded in the ticker file they came from.")
    out.append("")
    out.append("**Quantum.** Each trend is rated 1-5 on three anchored scales — **size** (how much money the "
               "trend moves across the industry), **speed** (when it bites: 5 = already visible in reported "
               "numbers, 1 = beyond five years) and **impact** (what it does to that company's revenue or "
               "margin) — each with a stated basis. A theme's quantum is the mean of its members' ratings, "
               "weighted `0.40*size + 0.30*speed + 0.30*impact`, then amplified by how many researched names "
               "it reaches:")
    out.append("")
    out.append("```")
    out.append("score = quantum * (1 + 0.10 * min(breadth - 1, 5))      # breadth = distinct tickers reached")
    out.append("```")
    out.append("")
    out.append("Size is weighted highest because a theme that moves little money is not interesting however "
               "fast it moves. Breadth is a *factor*, capped at +50%, so that a widely-shared small theme "
               "cannot outrank a large one — five names sharing a triviality must not beat one name facing a "
               "huge force. Dispersion is printed beside the mean, because a theme rated 5 by one company and "
               "1 by another averages to a settled-looking 3.")
    out.append("")
    out.append("**Who is affected.** For each theme the tickers are split by the direction the force takes for "
               "that company: *positively affected* (tailwind), *negatively affected* (headwind), and "
               "*two-sided or unclear*. A company appears on one side only, and appears under *two-sided* when "
               "the same force reaches it both ways. Sides are drawn from the researched batch alone: a theme "
               "that names three companies is a theme found in three companies, not a claim that only three "
               "companies are exposed.")
    out.append("")

    if not themes:
        out.append("_No themes: no trends survived grounding._")
        return "\n".join(out)

    out.append("## Ranked themes")
    out.append("")
    out.append("| # | Theme | Parts | Size | Speed | Impact | Quantum | Reaches | Score | Net |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for theme in themes:
        q = theme["quantum"]
        out.append(
            f"| {theme['rank']} | **{theme['label']}** | {len(theme['parts'])}/3 | {q['size']:.1f} | "
            f"{q['speed']:.1f} | {q['impact']:.1f} | {q['quantum']:.2f} | {theme['breadth']} | "
            f"**{theme['score']:.2f}** | {theme['net']} |"
        )
    out.append("")
    out.append("`Reaches` counts the researched tickers with a trend on the theme; `Parts` is how many of the "
               "three parts of a business the theme was found through.")
    out.append("")

    for theme in themes:
        q = theme["quantum"]
        out.append(f"### {theme['rank']}. {theme['label']}")
        out.append("")
        out.append(f"`{theme['key']}`" + (f" — merged from: {', '.join('`' + a + '`' for a in theme['aliases'])}" if theme["aliases"] else ""))
        out.append("")
        if theme.get("definition"):
            out.append(f"**What it is.** {theme['definition']}")
            out.append("")
        out.append(f"**Found through:** {', '.join(theme['part_labels'])}" +
                   (f" | **Revenue streams touched:** {', '.join(theme['streams'])}" if theme["streams"] else ""))
        out.append("")
        out.append(
            f"**Quantum.** size **{q['size']:.1f}**, speed **{q['speed']:.1f}**, impact **{q['impact']:.1f}** "
            f"→ quantum **{q['quantum']:.2f}** × breadth factor **{theme['breadth_factor']:.2f}** = "
            f"**{theme['score']:.2f}**  \n"
            f"({theme['trend_count']} trends from {theme['breadth']} companies, {theme['evidence_count']} sources, "
            f"rating dispersion {q['spread']:.2f}"
            + (f"; sources: {', '.join(f'{SOURCE_TYPE_LABEL.get(k, k)} x{v}' for k, v in sorted((theme.get('source_mix') or {}).items(), key=lambda kv: -kv[1]))}" if theme.get("source_mix") else "")
            + ")"
        )
        out.append("")
        for title, bucket, marker in (
            ("Positively affected", theme["positive"], "+"),
            ("Negatively affected", theme["negative"], "-"),
            ("Two-sided or unclear", theme["mixed"], "±"),
        ):
            if not bucket:
                continue
            out.append(f"**{title} ({len(bucket)}):**")
            out.append("")
            for member in bucket:
                why = member.get("why") or member.get("claim") or ""
                out.append(
                    f"- `{marker}` **{member['symbol']}** ({member.get('company') or ''}) — {why} "
                    f"*(impact {member.get('impact')}, found through {LENS_LABEL.get(member.get('lens'), member.get('lens'))}"
                    + (f", stream: {member['stream']}" if member.get("stream") and member["stream"] != "the business overall" else "")
                    + ")*"
                )
            out.append("")
        out.append("**Evidence:**")
        out.append("")
        for member in theme["members"]:
            if not member.get("quote"):
                continue
            out.append(
                f"- \"{member['quote']}\" — {_link(member.get('url'), member.get('publisher'), member.get('as_of'))}"
                f" — **{member['symbol']}**, {LENS_LABEL.get(member.get('lens'), member.get('lens')).lower()}"
                + (f" of {member['stream']}" if member.get("stream") and member["stream"] != "the business overall" else "")
                + f" *({SOURCE_TYPE_LABEL.get(member.get('source_type'), 'general media')})*"
            )
        out.append("")

    # ---- ticker index ----------------------------------------------------
    index = theme_impact_index(themes)
    out.append("## Ticker index")
    out.append("")
    out.append("| Ticker | Helped by | Hurt by | Two-sided | Writeup |")
    out.append("|---|---|---|---|---|")
    for symbol in sorted(index):
        entries = index[symbol]
        helps = [f"{e['theme']['label']} (#{e['theme']['rank']})" for e in entries if e["side"] == "helps it"]
        hurts = [f"{e['theme']['label']} (#{e['theme']['rank']})" for e in entries if e["side"] == "hurts it"]
        mixed = [f"{e['theme']['label']} (#{e['theme']['rank']})" for e in entries if e["side"].startswith("two")]
        out.append(
            f"| **{symbol}** | {'; '.join(helps) or '—'} | {'; '.join(hurts) or '—'} | "
            f"{'; '.join(mixed) or '—'} | [writeup](../tickers/{symbol}.md) |"
        )
    out.append("")
    out.append("---")
    out.append("")
    out.append(f"*Generated by `qts` from {len(analyses)} analysis artifacts"
               + (f" using `{model}`" if model else "")
               + ". Rebuild with `qualitative/qs themes` — rendering reads the artifacts only, so it costs "
                 "no searches and no tokens.*")
    out.append("")
    return "\n".join(out)
