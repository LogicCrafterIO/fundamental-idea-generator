"""Command line: ``qualitative/qs <command>``.

    qs screen                     the gated universe (price <= $100, cap >= $1B)
    qs screen --limit 20          the next batch it would research
    qs research --limit 20        research the batch: streams + three-lens trends
    qs research --tickers ORCL,PAYX --force
    qs themes                     rebuild THEMES.md from the artifacts on disk
    qs show PAYX                  print one writeup
    qs models                     list available models

Every command takes ``--root`` for where artifacts and markdown live; it defaults
to this folder (``qualitative/``), which is what keeps the screener's outputs
separate from the parent pipeline's ``research/`` notes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fig.sources import ollama
from fig.util import human_money

from . import analysis as analysis_mod
from . import themes as themes_mod
from . import universe as universe_mod
from . import writeup

QUALITATIVE_ROOT = Path(__file__).resolve().parents[1]


def _log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _parse_money_arg(value: str | None, default: float | None) -> float | None:
    """Parse ``1b``, ``1000m``, ``2.5e9``, ``75000000``; a bare ``0`` means "no gate"."""
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
        raise SystemExit(f"could not read a dollar amount from {value!r} (try 100, 1b, 1000m)")
    return None if number <= 0 else number


def cmd_screen(args) -> int:
    max_price = _parse_money_arg(getattr(args, "max_price", None), universe_mod.DEFAULT_MAX_PRICE)
    min_cap = _parse_money_arg(getattr(args, "min_market_cap", None), universe_mod.DEFAULT_MIN_MARKET_CAP)
    result = universe_mod.universe(max_price=max_price, min_market_cap=min_cap)

    print(universe_mod.describe(result))
    print()
    batch = universe_mod.select(result["rows"], limit=args.limit, order=args.order, seed=args.seed, start=args.start)
    print(f"Next batch ({len(batch)} of {result['count']}, ordered by {args.order}):")
    print()
    print(f"{'#':>3}  {'TICKER':<7} {'EXCH':<7} {'PRICE':>9} {'MARKET CAP':>11}  NAME")
    for index, row in enumerate(batch, start=1):
        print(
            f"{index:>3}  {row['symbol']:<7} {(row.get('exchange') or ''):<7} "
            f"{row.get('price') or 0:>9,.2f} {human_money(row.get('market_cap')):>11}  {(row.get('name') or '')[:52]}"
        )

    path = universe_mod.run_path(args.root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "gates": result["gates"],
                "count": result["count"],
                "by_exchange": result["by_exchange"],
                "excluded": result["excluded"],
                "duplicates": result["duplicates"],
                "batch": [row["symbol"] for row in batch],
                "rows": result["rows"],
            },
            indent=2,
        )
    )
    _log(f"wrote {path}")
    return 0


def cmd_research(args) -> int:
    root = args.root
    max_price = _parse_money_arg(getattr(args, "max_price", None), universe_mod.DEFAULT_MAX_PRICE)
    min_cap = _parse_money_arg(getattr(args, "min_market_cap", None), universe_mod.DEFAULT_MIN_MARKET_CAP)
    gates = {"max_price": max_price, "min_market_cap": min_cap}

    if args.tickers:
        wanted = [s.strip().upper() for s in args.tickers.replace(",", " ").split() if s.strip()]
        result = universe_mod.universe(max_price=max_price, min_market_cap=min_cap)
        listed = {row["symbol"]: row for row in result["rows"]}
        targets = []
        for symbol in wanted:
            row = listed.get(symbol)
            if not row:
                if not args.force:
                    # Said out loud rather than skipped quietly: a name omitted
                    # from the batch must be visible as a gate decision.
                    _log(f"{symbol}: does not pass the screen (price <= {max_price}, cap >= {human_money(min_cap)}); "
                         f"use --force to research it anyway")
                    continue
                row = {"symbol": symbol, "name": None}
                _log(f"{symbol}: researched under --force, outside the gates")
            targets.append(row)
    else:
        result = universe_mod.universe(max_price=max_price, min_market_cap=min_cap)
        targets = universe_mod.select(result["rows"], limit=args.limit, order=args.order, seed=args.seed, start=args.start)
        _log(universe_mod.describe(result))

    if not targets:
        print("nothing to research", file=sys.stderr)
        return 1

    outcome = analysis_mod.run(
        root,
        targets,
        model=args.model,
        workers=args.workers,
        refresh=args.refresh,
        per_query=args.per_query,
        gates=gates,
        log=_log,
    )

    analyses = analysis_mod.load_all(root)
    written = analysis_mod.write_ticker_files(root, analyses)
    _log(f"wrote {len(written)} ticker writeup(s) to {analysis_mod.tickers_dir(root)}")
    built = themes_mod.build(analyses, model=args.model, canonicalise=not args.no_canonicalise)
    master = writeup.render_master(built, analyses=analyses, gates=gates, model=args.model)
    master_path = analysis_mod.themes_dir(root) / "THEMES.md"
    master_path.write_text(master)
    _log(f"wrote {master_path} ({len(built['themes'])} themes from {len(analyses)} companies)")

    if outcome["failures"]:
        print("\nfailures:", file=sys.stderr)
        for failure in outcome["failures"]:
            print(f"  {failure['symbol']}: {failure['error']}", file=sys.stderr)
    return 0


def cmd_themes(args) -> int:
    root = args.root
    analyses = analysis_mod.load_all(root)
    if not analyses:
        print("no analyses on disk yet -- run: qs research", file=sys.stderr)
        return 1
    # The gates printed in the master file are the ones the batch was researched
    # under, read back from the artifacts, so a later run with different flags cannot
    # silently relabel an existing batch.
    gates = next((a.get("gates") for a in analyses if a.get("gates")), {}) or {}
    built = themes_mod.build(analyses, model=args.model, canonicalise=not args.no_canonicalise)
    index = writeup.theme_impact_index(built["themes"])
    analysis_mod.write_ticker_files(root, analyses, index)
    master = writeup.render_master(built, analyses=analyses, gates=gates, model=args.model)
    path = analysis_mod.themes_dir(root) / "THEMES.md"
    path.write_text(master)
    _log(f"wrote {path}")

    print(f"{len(built['themes'])} themes from {len(analyses)} companies "
          f"({built['trend_count']} trends, {built['merged']} duplicate keys merged)\n")
    print(f"{'#':>3}  {'SIZE':>4} {'SPD':>4} {'IMP':>4} {'QUANT':>5} {'REACH':>5} {'SCORE':>5}  THEME")
    for theme in built["themes"][: args.top]:
        q = theme["quantum"]
        print(
            f"{theme['rank']:>3}  {q['size']:>4.1f} {q['speed']:>4.1f} {q['impact']:>4.1f} "
            f"{q['quantum']:>5.2f} {theme['breadth']:>5} {theme['score']:>5.2f}  {theme['label']} "
            f"[+{theme['sides']['positive']}/-{theme['sides']['negative']}/±{theme['sides']['mixed']}]"
        )
    return 0


def cmd_show(args) -> int:
    path = analysis_mod.tickers_dir(args.root) / f"{args.symbol.upper()}.md"
    if not path.exists():
        print(f"no writeup for {args.symbol.upper()} (run: qs research --tickers {args.symbol.upper()})", file=sys.stderr)
        return 1
    print(path.read_text())
    return 0


def cmd_artifact(args) -> int:
    artifact = analysis_mod.load_analysis(args.root, args.symbol)
    if not artifact:
        print(f"no artifact for {args.symbol.upper()}", file=sys.stderr)
        return 1
    print(json.dumps(artifact, indent=2)[: args.chars] if args.chars else json.dumps(artifact, indent=2))
    return 0


def cmd_models(args) -> int:
    for model in ollama.list_models():
        print(model)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qs", description="Qualitative theme screener")
    parser.add_argument("--root", type=Path, default=QUALITATIVE_ROOT,
                        help="where analyses/ tickers/ themes/ live (default: qualitative/)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("screen", help="the gated universe: price and market cap only")
    p.add_argument("--max-price", dest="max_price", default=None, help="share price cap (default 100)")
    p.add_argument("--min-market-cap", dest="min_market_cap", default=None, help="market cap floor (default 1b)")
    p.add_argument("--limit", type=int, default=20, help="how many to show as the next batch")
    p.add_argument("--order", choices=["cap", "name", "random"], default="cap")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--start", type=int, default=0, help="skip into the ordered pool (later waves)")
    p.set_defaults(func=cmd_screen)

    p = sub.add_parser("research", help="research a batch: streams and three-lens trends")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--order", choices=["cap", "name", "random"], default="cap")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--tickers", default="", help="explicit symbols, comma or space separated")
    p.add_argument("--force", action="store_true", help="research names that fail the gates")
    p.add_argument("--max-price", dest="max_price", default=None)
    p.add_argument("--min-market-cap", dest="min_market_cap", default=None)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--per-query", type=int, default=5)
    p.add_argument("--model", default=None)
    p.add_argument("--refresh", action="store_true", help="ignore existing artifacts")
    p.add_argument("--no-canonicalise", action="store_true", help="skip the theme-merging model pass")
    p.set_defaults(func=cmd_research)

    p = sub.add_parser("themes", help="rebuild THEMES.md from the artifacts on disk")
    p.add_argument("--model", default=None)
    p.add_argument("--top", type=int, default=30)
    p.add_argument("--no-canonicalise", action="store_true")
    p.set_defaults(func=cmd_themes)

    p = sub.add_parser("show", help="print one ticker writeup")
    p.add_argument("symbol")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("artifact", help="print the stored research artifact for one ticker")
    p.add_argument("symbol")
    p.add_argument("--chars", type=int, default=0)
    p.set_defaults(func=cmd_artifact)

    p = sub.add_parser("models", help="list available models")
    p.set_defaults(func=cmd_models)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
