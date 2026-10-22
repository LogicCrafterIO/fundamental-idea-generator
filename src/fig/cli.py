"""Command line interface.

    fig themes                      what stories are live in the market right now
    fig screen                      triage a candidate universe, ranked
    fig packet ORCL --peers GOOG,SNOW
    fig prompt ORCL --peers GOOG,SNOW --direction long
    fig structure ORCL --direction long
    fig lint ideas/orcl.json
    fig render ideas/orcl.json
    fig demo                        reproducibility check against the references
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import discover, lint, options, packet, quants, render, themes, variants as variants_mod
from .sources import nasdaq
from .util import human_money


# --------------------------------------------------------------------------
# formatting helpers
# --------------------------------------------------------------------------


def _table(headers: list[str], rows: list[list[str]], widths: list[int] | None = None) -> str:
    widths = widths or [
        max(len(str(h)), *(len(str(r[i])) for r in rows)) if rows else len(h)
        for i, h in enumerate(headers)
    ]
    out = ["  ".join(str(h).ljust(w) for h, w in zip(headers, widths)).rstrip()]
    out.append("  ".join("-" * w for w in widths))
    for row in rows:
        out.append("  ".join(str(c).ljust(w) for c, w in zip(row, widths)).rstrip())
    return "\n".join(out)


def _write(path: str | None, text: str) -> None:
    if path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        print(f"wrote {target}", file=sys.stderr)
    else:
        print(text)


def _variant_list(value: str | None) -> list[str]:
    """Expand ``--variants`` into the variants this run publishes, in order.

    ``both`` is the default for a ``--screen`` run: the two screens read the same
    pool, share the expensive half (screening), and differ only in how the rows are
    ranked, so running one and then the other is nearly free. ``revisions`` first so
    the order matches :data:`fig.discover.SCORING_MODES` and the primary folder is
    the one the tool has been publishing.
    """
    choice = (value or "both").strip().lower()
    if choice == "both":
        return list(variants_mod.VARIANTS)
    if choice not in variants_mod.VARIANTS:
        raise SystemExit(
            f"unknown --variants {value!r}; expected one of both, "
            + ", ".join(variants_mod.VARIANTS)
        )
    return [choice]


def _parse_money_arg(value: str | None, default: float | None) -> float | None:
    """Parse a money argument: ``1b``, ``1000m``, ``2.5e9``, ``75000000``, ``0``.

    A plain number is dollars, and a bare ``0`` means "no floor" rather than
    "$0" so the two ways of disabling a rule behave the same.
    """
    if value is None:
        return default
    text = str(value).strip().lower().replace("_", "").replace(",", "")
    if not text:
        return default
    scale = 1.0
    if text.endswith("k"):
        scale, text = 1e3, text[:-1]
    elif text.endswith("m"):
        scale, text = 1e6, text[:-1]
    elif text.endswith("b"):
        scale, text = 1e9, text[:-1]
    elif text.endswith("t"):
        scale, text = 1e12, text[:-1]
    try:
        number = float(text) * scale
    except ValueError:
        raise SystemExit(f"could not read a dollar amount from {value!r} (try 1b, 1000m, 75000000)")
    return None if number <= 0 else number


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------


def cmd_themes(args) -> int:
    """Live market themes, from market-wide news plus any watched names."""
    items = nasdaq.market_news(limit=args.limit)
    for symbol in args.watchlist or []:
        items.extend(nasdaq.news_for_symbol(symbol, limit=10))

    story = themes.score_stories(items)
    print(f"Scanned {len(items)} headlines\n")
    if not story["themes"]:
        print("No themes matched the lexicon.")
        return 0

    for theme in story["themes"]:
        print(f"{theme['label']}  ({theme['count']} stories, {theme['share']*100:.0f}%)")
        print(f"    {theme['description']}")
        for ev in theme["evidence"][:3]:
            print(f"    - {ev['title']}")
            if ev.get("matched"):
                print(f"      matched: {', '.join(ev['matched'][:5])}")
        print()

    pairings = themes.theme_pairing([t["key"] for t in story["themes"]])
    if pairings:
        print("Two-sided readings (same story, opposite trades)")
        for pair in pairings:
            print(f"  {pair['story']}")
            print(f"    long : {pair['long_side']}")
            print(f"    short: {pair['short_side']}")
    return 0


def cmd_screen(args) -> int:
    max_price = _parse_money_arg(getattr(args, "max_price", None), discover.DEFAULT_MAX_PRICE)
    min_market_cap = _parse_money_arg(
        getattr(args, "min_market_cap", None), discover.DEFAULT_MIN_MARKET_CAP
    )
    result = discover.scan(
        watchlist=[s.strip().upper() for s in (args.watchlist or [])],
        limit=args.limit,
        top=args.top,
        earnings_days=args.earnings_days,
        include_screener=not args.no_screener,
        max_price=max_price,
        min_market_cap=min_market_cap if min_market_cap is not None else 0.0,
        mode=getattr(args, "scoring", discover.DEFAULT_SCORING) or discover.DEFAULT_SCORING,
    )
    cap_text = f"${max_price:,.0f}" if max_price is not None else "none"
    print(
        f"rules: share price under {cap_text}, market cap at least "
        f"{human_money(min_market_cap) if min_market_cap else 'none'}, "
        f"earnings within {args.earnings_days}d, screener "
        f"{'on' if not args.no_screener else 'off'}, "
        f"scoring {getattr(args, 'scoring', discover.DEFAULT_SCORING) or discover.DEFAULT_SCORING}\n"
    )
    print(
        f"pool {result['pool_size']} names -> screened {result['screened']} -> "
        f"ranked {len(result['ranked'])}\n"
    )
    if not result["ranked"]:
        print("Nothing cleared the score floor. Lower --min-score or widen the pool.")
        return 0

    rows = []
    for r in result["ranked"]:
        rows.append(
            [
                r["symbol"],
                r.get("direction_hint", ""),
                f"{r.get('score', 0):.0f}",
                f"{r.get('fwd_pe') or '-'}",
                f"{r.get('ps') or '-'}",
                f"{(r.get('price_change_30d') or 0):+.0f}%",
                f"{r.get('revisions_net_30d') or 0:+g}",
                str(r.get("next_earnings") or "-"),
                ",".join(r.get("themes") or [])[:26],
            ]
        )
    print(
        _table(
            ["TICKER", "SIDE", "SCORE", "FWD_PE", "P/S", "30D", "REV_NET", "EARNINGS", "THEMES"],
            rows,
        )
    )
    if result["gated"]:
        # Counted by reason, because "how many names the cap removed" is the number
        # that explains the size of the batch -- listing six tickers does not.
        reasons: dict[str, int] = {}
        for row in result["gated"]:
            key = re.sub(r"\$[\d,.]+", "$X", str(row.get("gated") or "other"))
            reasons[key] = reasons.get(key, 0) + 1
        print(f"\nGated out ({len(result['gated'])}):")
        for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
            print(f"  {count:4}  {reason}")
    print("\nScore components for the top name:")
    top = result["ranked"][0]
    for key, value in (top.get("score_components") or {}).items():
        print(f"  {key:14} {value}")
    print(f"\nNext: fig prompt {top['symbol']} --direction {top.get('direction_hint','long')}")
    return 0


def _split_symbols(value: str | None) -> list[str]:
    """Parse a comma-separated ticker list.

    ``--peers`` arrives as a string, so it must be split before iterating:
    iterating the raw value yields characters, which silently produced peers
    named "G", "O", "O", "G", "," ...
    """
    if not value:
        return []
    return [token.strip().upper() for token in str(value).split(",") if token.strip()]


def cmd_packet(args) -> int:
    result = packet.build_packet(
        args.symbol,
        peers=_split_symbols(args.peers),
        catalyst_index=args.catalyst_index,
    )
    if args.json:
        _write(args.out, json.dumps(result, indent=2, default=str))
    else:
        _write(args.out, packet.to_prompt_context(result))
    return 0


def cmd_prompt(args) -> int:
    from . import prompts

    result = packet.build_packet(
        args.symbol,
        peers=_split_symbols(args.peers),
        catalyst_index=args.catalyst_index,
    )
    context = packet.to_prompt_context(result)
    text = (
        "=== SYSTEM ===\n"
        + prompts.SYSTEM_PROMPT
        + "\n\n=== USER ===\n"
        + prompts.build_user_prompt(context, direction_hint=args.direction)
    )
    _write(args.out, text)
    return 0


def cmd_structure(args) -> int:
    structure = options.build_structure(
        args.symbol,
        args.direction,
        catalyst_index=args.catalyst_index,
        capital=args.capital,
        credit_target=args.credit_target,
    )
    print(f"{structure.symbol} {structure.direction.upper()}  price {structure.price}")
    print(f"catalyst {structure.catalyst}")
    print()
    print(render.render_structure_table(structure.rows()))
    print()
    print(f"credit ratio  mid {structure.credit_ratio_mid*100:.2f}%  "
          f"conservative {structure.credit_ratio_conservative*100:.2f}%  "
          f"(floor {options.CREDIT_FLOOR*100:.0f}%)")
    print(f"long paid ${structure.long_total:,.0f}  short collected ${structure.short_total:,.0f}  "
          f"net debit ${structure.net_debit:,.0f}")
    print(f"{options.suggest_short_adjustment(structure)}")
    for note in structure.notes:
        print(f"note: {note}")

    print("\nCredit ladder (conservative basis is the one that matters)")
    for row in options.credit_ladder(structure):
        flag = "ok" if row["passes_floor"] else "  "
        print(
            f"  shorts {row['short_qty']:>2}  mid {row['credit_ratio_mid']*100:5.2f}%  "
            f"cons {row['credit_ratio_conservative']*100:5.2f}%  {flag}  "
            f"cash ${row['cash_collected']:,.0f}"
        )
    return 0


def cmd_lint(args) -> int:
    if args.path == "-":
        payload = json.load(sys.stdin)
    else:
        payload = json.loads(Path(args.path).read_text())
    writeups = payload if isinstance(payload, list) else [payload]

    if len(writeups) == 1:
        result = lint.lint_writeup(writeups[0])
        print(f"score {result['score']}/100  errors {result['errors']}  warnings {result['warnings']}")
        print(
            f"description {result['stats']['description_words']} words, "
            f"reasons {result['stats']['reason_words']}, "
            f"notes {result['stats']['notes_words']}"
        )
        if not result["issues"]:
            print("clean")
        for issue in result["issues"]:
            print(f"  {issue}")
        return 0 if result["ok"] else 1

    summary = lint.lint_batch(writeups)
    for result in summary["results"]:
        status = "PASS" if result["ok"] else "FAIL"
        print(f"{status} {result['ticker']}  score {result['score']}")
        for issue in result["issues"]:
            print(f"    {issue}")
    print(f"\n{summary['passed']} passed, {summary['failed']} failed, mean {summary['mean_score']}")
    return 0 if summary["failed"] == 0 else 1


def cmd_render(args) -> int:
    payload = json.loads(Path(args.path).read_text())
    writeups = payload if isinstance(payload, list) else [payload]
    chunks = [render.render_writeup(w, include_lint=args.lint) for w in writeups]
    _write(args.out, "\n\n---\n\n".join(chunks))
    return 0


def cmd_quants(args) -> int:
    panel = quants.quants_panel(args.symbol)
    for line in quants.quants_lines(panel):
        print(line)
    print(
        f"\n(next-FY basis fwd PE {panel['fwd_pe_1y']}; "
        f"yahoo forwardPE {panel['fwd_pe_yahoo']}; trailing {panel['trailing_pe']})"
    )
    deltas = quants.fundamental_deltas(args.symbol)
    if deltas:
        print("\nStatement moves")
        for d in deltas:
            print(f"  {d['label']}: {d['direction']} {abs(d['change_pct']):.1f}% ({d['prior_period']} -> {d['period']})")

    # Printed here because this command is where a person checks a figure by hand, and
    # a sequential move without its year-earlier comparison is the reading error this
    # tool has actually made.
    rows = quants.yoy_deltas(args.symbol)
    if rows:
        print("\nSequential vs same quarter a year ago")
        for d in rows:
            conflict = "  <- opposite directions" if d.get("conflict") else ""
            print(
                f"  {d['label']}: {human_money(d.get('current'))} ({d['period']}) "
                f"{d['qoq_pct']:+.1f}% QoQ vs {human_money(d.get('year_ago'))} "
                f"({d.get('year_ago_period')}) {d['yoy_pct']:+.1f}% YoY{conflict}"
            )

    annual = quants.annual_deltas(args.symbol)
    if annual:
        print("\nFiscal year vs prior year")
        for d in annual:
            print(
                f"  {d['label']}: {human_money(d.get('prior'))} -> "
                f"{human_money(d.get('current'))} ({d['change_pct']:+.1f}%)"
            )

    deals = quants.deal_activity(args.symbol)
    if deals:
        print("\nAcquisition footprint")
        for d in deals:
            print(
                f"  {d['label']}: {human_money(d.get('prior'))} -> "
                f"{human_money(d.get('current'))} ({d['prior_period']} to {d['period']}, "
                f"{d['basis']}, {d['change_pct']:+.1f}%)"
                + ("  [goodwill: confirms a deal]" if d.get("confirmed") else "  [suggestive]")
            )

    panel_next = panel.get("next_earnings") or {}
    bar = quants.consensus_bar(panel)
    if bar:
        bits = []
        if bar.get("eps_avg") is not None:
            bits.append(f"EPS {bar['eps_avg']}")
        if bar.get("revenue_avg") is not None:
            bits.append(f"revenue {human_money(bar['revenue_avg'])}")
        print(f"\nConsensus bar ({bar.get('date')}): " + ", ".join(bits))

    yoy = quants.eps_yoy(args.symbol)
    if yoy:
        print(f"\nEPS yoy: {yoy['direction']} ({yoy['year_ago']} -> {yoy['current']})")
    return 0


def cmd_search(args) -> int:
    """Web search via the Ollama key -- usable on its own, not just internally."""
    from .sources import ollama

    if not ollama.has_key():
        print("OLLAMA_API_KEY not set (env or .env).", file=sys.stderr)
        return 1

    if args.models:
        for name in ollama.list_models():
            print(name)
        return 0

    for result in ollama.web_search(args.query, max_results=args.limit):
        print(f"- {result['title']}")
        if result.get("publisher"):
            print(f"  {result['publisher']}")
        if result.get("url"):
            print(f"  {result['url']}")
        snippet = (result.get("content") or "").strip().replace("\n", " ")
        if snippet and args.snippets:
            print(f"  {snippet[:400]}")
        print()
    return 0


def cmd_generate(args) -> int:
    from . import generate

    # args.symbols is already a list from nargs="*" -- it must NOT go through
    # _split_symbols, which stringifies and would yield "['ORCL']".
    from . import discover

    symbols = [s.strip().upper() for s in (args.symbols or []) if s.strip()]
    if not symbols:
        symbols = [s.strip().upper() for s in (args.watchlist or []) if s.strip()]

    # The cap is on by default: ideas are capped so a position fits the capital
    # unit. --max-price 0 means "no cap" for an exploratory scan.
    raw_cap = getattr(args, "max_price", None)
    if raw_cap is None:
        max_price = discover.DEFAULT_MAX_PRICE
    elif raw_cap <= 0:
        max_price = None
    else:
        max_price = raw_cap

    # --screen N closes a loop that was left open: the screener produced ranked
    # candidates that nothing ever generated from, so its survivors sat un-written
    # unless someone retyped the tickers by hand.
    hint: dict[str, str] = {}
    screen_n = int(getattr(args, "screen", 0) or 0)
    planned: dict | None = None
    work: list[dict] = []

    if screen_n:
        min_market_cap = _parse_money_arg(
            getattr(args, "min_market_cap", None), discover.DEFAULT_MIN_MARKET_CAP
        )
        variants = _variant_list(getattr(args, "variants", "both"))

        # One screening pass, however many variants are published. The screen is the
        # expensive half (several network calls per name); rescoring rows already in
        # hand is arithmetic, so the second variant costs no network time at all.
        outcome = discover.scan(
            top=screen_n,
            limit=int(getattr(args, "screen_limit", 60) or 60),
            max_price=max_price,
            min_market_cap=min_market_cap if min_market_cap is not None else 0.0,
            require_structure=bool(getattr(args, "strict", False)),
            require_positive_pe=bool(getattr(args, "strict", False)),
            mode=variants[0],
        )

        picks: dict[str, list[dict]] = {}
        for variant in variants:
            picks[variant] = discover.rank_candidates(
                discover.rescore(outcome["all_rows"], mode=variant),
                top=screen_n,
                require_structure=bool(getattr(args, "strict", False)),
                require_positive_pe=bool(getattr(args, "strict", False)),
                max_price=max_price,
            )

        print(
            f"screener: {outcome['pool_size']} in pool, {outcome['screened']} screened "
            f"-> {sum(len(v) for v in picks.values())} pick(s) across "
            f"{len(variants)} screen(s)"
        )
        print(
            f"  rules: share price under "
            f"{f'${max_price:,.0f}' if max_price is not None else 'none'}, "
            f"market cap at least "
            f"{human_money(min_market_cap) if min_market_cap else 'none'}"
        )
        for variant in variants:
            print(
                f"\n  {variant} ({variants_mod.VARIANT_TITLES.get(variant, variant)}):"
            )
            for row in picks[variant]:
                print(
                    f"    {row['symbol']:6} {row.get('direction_hint','?'):5} "
                    f"score {row['score']:5.1f}"
                    + (f"  caveats: {'; '.join(row['caveats'])}" if row.get("caveats") else "")
                )

        planned = variants_mod.plan(picks)
        if len(variants) > 1:
            for line in variants_mod.describe(planned):
                print(line)
            for clash in planned["disagreements"]:
                sides = ", ".join(f"{v}={d}" for d, v in sorted(clash["directions"].items()))
                print(f"  disagreement: {clash['symbol']} ({sides}) -- both notes written")
        work = planned["work"]
        for item in work:
            hint[item["symbol"]] = item["direction"]

    # Typed tickers: one note each, no screening, so no variants to plan -- the
    # direction comes from --directions or defaults to long.
    if not work:
        if not symbols:
            print("give one or more tickers, or --screen N", file=sys.stderr)
            return 1

        # --directions is a comma-separated string; directions are lowercase.
        if getattr(args, "directions", None):
            directions = [d.strip().lower() for d in args.directions.split(",") if d.strip()]
        else:
            directions = ["long"]
        if not directions:
            directions = ["long"]
        work = [
            {
                "symbol": symbol,
                "direction": directions[i] if i < len(directions) else directions[-1],
                "variants": [],
                "scores": {},
            }
            for i, symbol in enumerate(symbols)
        ]

    results = []
    failures = []
    excluded = []
    by_target: dict[Path, list[dict]] = {}

    def targets_for(item: dict) -> list[Path]:
        """Which folders this note is published into.

        A two-variant run publishes into ``<out>/<variant>/``; a single-variant run
        keeps writing straight into ``--out``, which is the layout every note in the
        repo's history already has.
        """
        if item.get("variants") and len((planned or {}).get("variants") or []) > 1:
            return [Path(args.out) / variants_mod.folder_name(v) for v in item["variants"]]
        return [Path(args.out)]

    # Tickers are independent, and generation is almost entirely network wait, so
    # a batch runs concurrently. This is the single biggest speed win available:
    # 9 tickers at ~1.5 min each is 13 min serially and ~2 min at 8 jobs.
    jobs = max(1, min(int(getattr(args, "jobs", 1) or 1), len(work)))

    def run(item: dict) -> tuple[dict, object]:
        try:
            return item, generate.generate_idea(
                item["symbol"],
                direction=item["direction"],
                peers=_split_symbols(args.peers),
                model=args.model,
                use_search=not args.no_search,
                catalyst_index=args.catalyst_index,
                credit_target=args.credit_target,
                repairs=args.repairs,
                structure_legs=not getattr(args, "no_legs", False),
                samples=getattr(args, "samples", 1),
                max_price=max_price,
                verbose=jobs == 1,
            )
        except generate.PriceCapError as exc:
            return item, exc
        except Exception as exc:  # noqa: BLE001 - reported per symbol, batch continues
            return item, exc

    if jobs == 1:
        outcomes = [run(item) for item in work]
    else:
        print(f"\ngenerating {len(work)} note(s) with {jobs} parallel jobs")
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            outcomes = list(pool.map(run, work))

    for item, outcome in outcomes:
        symbol = item["symbol"]
        if isinstance(outcome, generate.PriceCapError):
            print(f"[{symbol}] SKIPPED: {outcome}")
            excluded.append((symbol, str(outcome)))
            continue
        if isinstance(outcome, Exception):
            print(f"[{symbol}] FAILED: {type(outcome).__name__}: {outcome}", file=sys.stderr)
            failures.append((symbol, str(outcome)))
            continue

        # Written into every folder this note belongs to. When both screens pick the
        # same name on the same side there is one generation and two copies, which is
        # the whole saving: a second generation would spend tokens to reproduce text
        # that could differ between the folders.
        note_path = ""
        score = 0
        for target in targets_for(item):
            paths = generate.save_idea(outcome, target)
            by_target.setdefault(target, []).append(outcome)
            note_path = note_path or paths["note"]
            score = paths["score"]
        results.append(outcome)
        print(
            f"[{symbol}] {note_path}  score {score}/100"
            f"{'' if note_path else ''}"
            f"{'' if not item.get('variants') or len(item['variants']) < 2 else ' (copied to both)'}"
        )

    if results or excluded:
        if not by_target:
            by_target[Path(args.out)] = list(results)
        scored_disagreements = (planned or {}).get("disagreements") or []
        for target, target_results in by_target.items():
            generate.write_excluded(excluded, target)
            # Rebuilt from every note on disk rather than written from this batch
            # alone: a batch that wrote its own index would silently drop every note
            # from the runs before it. The rebuild re-lints and re-grounds each note,
            # so the index is an audit of the whole folder, not a report on one batch.
            #
            # The rules this batch ran under are recorded beside the notes, so a later
            # rebuild states the cap the folder was actually built under rather than
            # the tool's default.
            generate.record_settings(
                target,
                tickers=[r["writeup"]["ticker"] for r in target_results],
                max_price=max_price,
                min_market_cap=(
                    _parse_money_arg(getattr(args, "min_market_cap", None), None)
                    if getattr(args, "min_market_cap", None)
                    else None
                ),
            )
            scoring = target.name if target.name in variants_mod.VARIANTS else None
            rebuilt = generate.rebuild_index(
                target,
                scoring=scoring,
                disagreements=scored_disagreements if len(variants_mod.VARIANTS) else None,
            )
            print(f"\nindex: {rebuilt['index']} ({rebuilt['notes']} note(s))")
    if failures:
        print(f"\n{len(failures)} failed:", file=sys.stderr)
        for symbol, error in failures:
            print(f"  {symbol}: {error}", file=sys.stderr)
    return 1 if failures and not results else 0



def cmd_rank(args) -> int:
    """Print the ranking for a folder of notes, with counts."""
    import json as _json

    from . import generate, ranking

    results = generate.rebuild_index(args.out)["results"]
    entries = ranking.rank_ideas(results)
    counts = ranking.summarise(entries)

    print(
        f"{counts['ideas']} idea(s): {counts['longs']} long, {counts['shorts']} short"
        f"  |  mean conviction {counts['mean_conviction']}"
    )
    print(
        f"{counts['well_evidenced']} confirmed by end-market evidence, "
        f"{counts['evidence_against']} contradicted"
    )
    print()
    print(f"{'#':>2}  {'ticker':7} {'side':5} {'conv':>5} {'evidence':16} {'catalyst':10} {'lint':>5}  description")
    for entry in entries:
        when = entry["catalyst_date"] or "-"
        if entry["catalyst_days"] is not None:
            when += f" {entry['catalyst_days']}d"
        description = (entry["description"] or "")[:46]
        print(
            f"{entry['rank']:>2}  {entry['ticker']:7} {entry['direction']:5} "
            f"{entry['conviction']:>5} {entry['evidence_label']:16} {when:10} "
            f"{entry['score']:>5}  {description}"
        )
    print()
    print("conviction is a reading order, not a prediction: src/fig/ranking.py")
    return 0


def cmd_index(args) -> int:
    """Rebuild the research index from the notes on disk."""
    from . import generate

    summary = generate.rebuild_index(args.out)
    print(f"{summary['notes']} note(s), mean score {summary['mean_score']} -> {summary['index']}")
    return 0


def cmd_organize(args) -> int:
    """File every note under its own side's folder."""
    from . import generate

    result = generate.organize(args.out, dry_run=args.dry_run)
    for source, destination in result["moved"]:
        print(f"{'would move' if args.dry_run else 'moved'} {source} -> {destination}")
    if not result["moved"]:
        print(f"{result['unchanged']} note(s) already filed under their side")
    elif result["unchanged"]:
        print(f"{result['unchanged']} note(s) already filed under their side")
    if result["moved"] and not args.dry_run:
        print("\nrun `fig index` to rewrite the index links into the folders")
    return 0


def cmd_attribute(args) -> int:
    """Backfill the sources behind each reason, for notes written before sources."""
    from . import attribute

    summary = attribute.attribute_folder(args.out, model=args.model, limit=args.limit)
    print()
    for row in summary["attributed"]:
        status = f"{row['citations']} citation(s)"
        if row["uncited_reasons"]:
            status += f", reason(s) {row['uncited_reasons']} left uncited"
        if row["unknown_ids"]:
            status += f", dropped unknown id(s) {row['unknown_ids']}"
        ground = row["source_grounding"]
        if ground and ground.get("mismatches"):
            status += f", {len(ground['mismatches'])} figure(s) outside the cited source"
        print(f"  {row['ticker']:6} {status}")
    if summary["skipped"]:
        print("\nskipped:")
        for ticker, why in summary["skipped"]:
            print(f"  {ticker:6} {why}")
    print(f"\n{len(summary['attributed'])} note(s) attributed")
    return 0


def cmd_demo(args) -> int:
    """Verify the engine still reproduces the two reference structures.

    This is the regression test for the whole structuring model: if the leg
    selection or credit math drifts, this fails.
    """
    cases = [
        ("ORCL", "long", 0, "2026-10-16", 155.0, "2026-12-18", 155.0),
        ("OMF", "short", 1, "2026-10-16", 57.5, "2027-02-19", 57.5),
    ]
    failures = 0
    for symbol, direction, catalyst_index, short_exp, short_k, long_exp, long_k in cases:
        try:
            structure = options.build_structure(symbol, direction, catalyst_index=catalyst_index)
        except Exception as exc:
            print(f"FAIL {symbol}: {type(exc).__name__}: {exc}")
            failures += 1
            continue

        checks = [
            ("short expiry", structure.short_leg["expiry"], short_exp),
            ("short strike", structure.short_leg["strike"], short_k),
            ("long expiry", structure.long_leg["expiry"], long_exp),
            ("long strike", structure.long_leg["strike"], long_k),
        ]
        bad = [(n, got, want) for n, got, want in checks if got != want]
        if bad:
            failures += 1
            print(f"FAIL {symbol} {direction}")
            for name, got, want in bad:
                print(f"     {name}: got {got}, reference {want}")
        else:
            print(
                f"PASS {symbol} {direction}: short {short_exp} K{short_k:g}, "
                f"long {long_exp} K{long_k:g} -- matches reference"
            )
        print(
            f"     credit mid {structure.credit_ratio_mid*100:.1f}% / "
            f"conservative {structure.credit_ratio_conservative*100:.1f}%, "
            f"net debit ${structure.net_debit:,.0f}"
        )
    return 1 if failures else 0


# --------------------------------------------------------------------------
# parser
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fig", description="Fundamental idea generator")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("themes", help="live themes from market news")
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--watchlist", nargs="*", default=[])
    p.set_defaults(func=cmd_themes)

    p = sub.add_parser("screen", help="triage a candidate universe")
    p.add_argument("--watchlist", nargs="*", default=[])
    p.add_argument("--limit", type=int, default=25, help="names to screen")
    p.add_argument("--top", type=int, default=12)
    p.add_argument("--earnings-days", type=int, default=10)
    p.add_argument(
        "--max-price",
        default=None,
        help="only names trading under this share price (default 150, the ideas "
        "cap; accepts 75 or 75.00; 0 disables)",
    )
    p.add_argument(
        "--min-market-cap",
        default=None,
        help="pool floor, accepts 1b / 1000m / 2e9 (default 2b)",
    )
    p.add_argument("--no-screener", action="store_true")
    p.add_argument(
        "--scoring",
        default="revisions",
        choices=["revisions", "divergence"],
        help="core signal to rank on: revisions (consensus EPS revision alone, the "
        "default) or divergence (revisions versus the 30-day price move)",
    )
    p.set_defaults(func=cmd_screen)

    p = sub.add_parser("packet", help="evidence packet for one name")
    p.add_argument("symbol")
    p.add_argument("--peers", default="", help="comma-separated peer tickers")
    p.add_argument("--catalyst-index", type=int, default=0)
    p.add_argument("--json", action="store_true")
    p.add_argument("--out")
    p.set_defaults(func=cmd_packet)

    p = sub.add_parser("prompt", help="the distillation prompt for one name")
    p.add_argument("symbol")
    p.add_argument("--peers", default="")
    p.add_argument("--direction", choices=["long", "short"])
    p.add_argument("--catalyst-index", type=int, default=0)
    p.add_argument("--out")
    p.set_defaults(func=cmd_prompt)

    p = sub.add_parser("structure", help="build an option structure")
    p.add_argument("symbol")
    p.add_argument("--direction", choices=["long", "short"], required=True)
    p.add_argument("--catalyst-index", type=int, default=0)
    p.add_argument("--capital", type=float, default=options.DEFAULT_CAPITAL)
    p.add_argument("--credit-target", type=float, default=options.DEFAULT_CREDIT_TARGET)
    p.set_defaults(func=cmd_structure)

    p = sub.add_parser("lint", help="check a writeup against the house style")
    p.add_argument("path")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("render", help="render a writeup in reference layout")
    p.add_argument("path")
    p.add_argument("--out")
    p.add_argument("--lint", action="store_true")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("quants", help="quants panel for one name")
    p.add_argument("symbol")
    p.set_defaults(func=cmd_quants)

    p = sub.add_parser("search", help="web search via the Ollama key")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=6)
    p.add_argument("--no-snippets", dest="snippets", action="store_false", default=True)
    p.add_argument("--models", action="store_true", help="list available models instead")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("generate", help="generate finished idea notes with the model")
    p.add_argument(
        "--screen",
        type=int,
        default=0,
        metavar="N",
        help="generate from the screener's top N survivors instead of a typed list",
    )
    p.add_argument(
        "--screen-limit",
        type=int,
        default=60,
        help="how many names the screener screens before ranking (default 60)",
    )
    p.add_argument(
        "--variants",
        default="both",
        help="which screens a --screen run publishes: both (default), revisions, or "
        "divergence. Both read the same pool, so the second costs only arithmetic, "
        "and a name both pick on the same side is generated once and copied",
    )
    p.add_argument(
        "--min-market-cap",
        default=None,
        help="pool floor for --screen, accepts 1b / 1000m / 2e9 (default 2b)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="also filter on missing option chains and loss-making (off by default: "
        "that data can be wrong)",
    )
    p.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="generate this many tickers in parallel (default 1; generation is "
        "network-bound, so 4-8 is a large speed-up on a batch)",
    )
    p.add_argument(
        "--samples",
        type=int,
        default=1,
        help="independent runs per ticker; each re-runs the end-market research, so "
        "the sampled verdict can disagree with itself (default 1)",
    )
    p.add_argument(
        "--max-price",
        type=float,
        default=None,
        help="reject tickers at or above this share price (default 150, the ideas "
        "cap, so a position fits the ~$4,500 capital unit; 0 disables the cap)",
    )
    p.add_argument("symbols", nargs="*", help="tickers to write up")
    p.add_argument("--watchlist", nargs="*", default=[])
    # default=None, not "long": a truthy default would always win the check in
    # cmd_generate and silently override the screener's own direction hints.
    p.add_argument(
        "--directions",
        default=None,
        help="comma-separated, aligned to tickers (default: the screener's hint "
        "with --screen, otherwise long)",
    )
    p.add_argument("--peers", default="")
    p.add_argument("--model", default=None, help="model id, e.g. deepseek-v4-pro:0813")
    p.add_argument("--out", default="research")
    p.add_argument("--no-search", action="store_true", help="skip web-search evidence")
    p.add_argument("--catalyst-index", type=int, default=0)
    p.add_argument("--credit-target", type=float, default=options.DEFAULT_CREDIT_TARGET)
    p.add_argument("--repairs", type=int, default=2, help="lint-driven revision rounds")
    p.add_argument(
        "--no-legs",
        action="store_true",
        help="skip option structuring; the note is written without a spread "
        "(the legs are a second-order detail and the chain fetch is the slow part)",
    )
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("rank", help="rank a folder of generated ideas")
    p.add_argument("--out", default="research")
    p.set_defaults(func=cmd_rank)

    p = sub.add_parser("index", help="rebuild the research index from the notes on disk")
    p.add_argument("--out", default="research")
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("organize", help="file notes under longs/ and shorts/ by their side")
    p.add_argument("--out", default="research")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_organize)

    p = sub.add_parser(
        "attribute",
        help="backfill the sources behind each reason for notes written before sources",
    )
    p.add_argument("--out", default="research")
    p.add_argument("--limit", type=int, default=None, help="stop after this many notes")
    p.add_argument("--model", default=None)
    p.set_defaults(func=cmd_attribute)

    p = sub.add_parser("demo", help="verify the engine reproduces the reference structures")
    p.set_defaults(func=cmd_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
