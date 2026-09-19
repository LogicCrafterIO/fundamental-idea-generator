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
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import discover, lint, options, packet, quants, render, themes
from .sources import nasdaq


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
    result = discover.scan(
        watchlist=[s.strip().upper() for s in (args.watchlist or [])],
        limit=args.limit,
        top=args.top,
        earnings_days=args.earnings_days,
        include_screener=not args.no_screener,
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
        print(f"\nGated out ({len(result['gated'])}):")
        for row in result["gated"][:6]:
            print(f"  {row['symbol']:<6} {row.get('gated')}")
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
    symbols = [s.strip().upper() for s in (args.symbols or []) if s.strip()]
    if not symbols:
        symbols = [s.strip().upper() for s in (args.watchlist or []) if s.strip()]
    if not symbols:
        print("give one or more tickers", file=sys.stderr)
        return 1

    # --directions is a comma-separated string; directions are lowercase.
    directions = [d.strip().lower() for d in (args.directions or "long").split(",") if d.strip()]
    if not directions:
        directions = ["long"]
    results = []
    failures = []
    excluded = []

    # The cap is on by default: ideas are capped so a position fits the capital
    # unit. --max-price 0 means "no cap" for an exploratory scan.
    from . import discover as _discover

    raw_cap = getattr(args, "max_price", None)
    if raw_cap is None:
        max_price = _discover.DEFAULT_MAX_PRICE
    elif raw_cap <= 0:
        max_price = None
    else:
        max_price = raw_cap

    # Tickers are independent, and generation is almost entirely network wait, so
    # a batch runs concurrently. This is the single biggest speed win available:
    # 9 tickers at ~1.5 min each is 13 min serially and ~2 min at 8 jobs.
    jobs = max(1, min(int(getattr(args, "jobs", 1) or 1), len(symbols)))

    def work(item: tuple[int, str]) -> tuple[str, object]:
        index, symbol = item
        direction = directions[index] if index < len(directions) else directions[-1]
        try:
            return symbol, generate.generate_idea(
                symbol,
                direction=direction,
                peers=_split_symbols(args.peers),
                model=args.model,
                use_search=not args.no_search,
                catalyst_index=args.catalyst_index,
                credit_target=args.credit_target,
                repairs=args.repairs,
                samples=getattr(args, "samples", 1),
                max_price=max_price,
                verbose=jobs == 1,
            )
        except generate.PriceCapError as exc:
            return symbol, exc
        except Exception as exc:  # noqa: BLE001 - reported per symbol, batch continues
            return symbol, exc

    indexed = list(enumerate(symbols))
    if jobs == 1:
        outcomes = [work(item) for item in indexed]
    else:
        print(f"generating {len(symbols)} ticker(s) with {jobs} parallel jobs")
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            outcomes = [
                outcome
                for outcome in pool.map(work, indexed)
            ]

    for symbol, outcome in outcomes:
        if isinstance(outcome, generate.PriceCapError):
            print(f"[{symbol}] SKIPPED: {outcome}")
            excluded.append((symbol, str(outcome)))
            continue
        if isinstance(outcome, Exception):
            print(f"[{symbol}] FAILED: {type(outcome).__name__}: {outcome}", file=sys.stderr)
            failures.append((symbol, str(outcome)))
            continue
        paths = generate.save_idea(outcome, args.out)
        results.append(outcome)
        print(
            f"[{symbol}] {paths['note']}  score {paths['score']}/100"
            f"{'' if paths['ok'] else '  (still has lint errors)'}"
        )

    if results or excluded:
        generate.write_index(results, args.out, excluded=excluded, max_price=max_price)
        print(f"\nindex: {args.out}/README.md")
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
    p.add_argument("--no-screener", action="store_true")
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
    p.add_argument("--directions", default="long", help="comma-separated, aligned to tickers")
    p.add_argument("--peers", default="")
    p.add_argument("--model", default=None, help="model id, e.g. deepseek-v4-pro:0813")
    p.add_argument("--out", default="research")
    p.add_argument("--no-search", action="store_true", help="skip web-search evidence")
    p.add_argument("--catalyst-index", type=int, default=0)
    p.add_argument("--credit-target", type=float, default=options.DEFAULT_CREDIT_TARGET)
    p.add_argument("--repairs", type=int, default=2, help="lint-driven revision rounds")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("rank", help="rank a folder of generated ideas")
    p.add_argument("--out", default="research")
    p.set_defaults(func=cmd_rank)

    p = sub.add_parser("index", help="rebuild the research index from the notes on disk")
    p.add_argument("--out", default="research")
    p.set_defaults(func=cmd_index)

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
