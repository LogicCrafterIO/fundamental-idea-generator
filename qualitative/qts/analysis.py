"""Running the research, one company at a time, and keeping every artifact.

The artifact is the unit of work
--------------------------------
Each company's research is written to ``qualitative/analyses/<SYM>.json`` the
moment it finishes, and a re-run reads that file instead of the network. Three
things follow, and all three matter for a qualitative screen specifically:

* **A wave is resumable.** Twenty companies is roughly twenty minutes of search
  and generation; a crash at company nineteen must not cost the first eighteen.
* **The master theme file is additive.** ``qs themes`` aggregates every artifact
  on disk, so a second wave of twenty more names *deepens* the theme file -- more
  tickers on each side of a theme, more merging -- instead of replacing it.
* **The published markdown is reproducible.** Rendering reads only artifacts. A
  prompt change can therefore be judged on the artifacts it produced, and a
  renderer change can be judged without re-spending a single search.

What is deliberately *not* stored: the retrieved snippets. They are large, they
are not needed to render, and keeping them would make the artifact a second cache
with its own staleness problem. What is stored is a compact index of every result
the model was shown -- title, URL, publisher, date -- so the evidence trail stays
auditable after the fact.

Partial failure is expected, not exceptional
-------------------------------------------
Free search endpoints fail, models return malformed JSON, a company discloses no
segments. Every one of those is recorded per stage in ``errors`` and the artifact
is still written with whatever was found. A run that produces eleven of twelve
sections and says which one is missing is more useful than one that raises, and
far more useful than one that fills the gap with plausible prose.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import date
from pathlib import Path

from fig.sources import ollama

from . import profile as profile_mod
from . import streams as streams_mod
from . import trends as trends_mod
from . import writeup


def analyses_dir(root: Path) -> Path:
    path = root / "analyses"
    path.mkdir(parents=True, exist_ok=True)
    return path


def tickers_dir(root: Path) -> Path:
    path = root / "tickers"
    path.mkdir(parents=True, exist_ok=True)
    return path


def themes_dir(root: Path) -> Path:
    path = root / "themes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def artifact_path(root: Path, symbol: str) -> Path:
    return analyses_dir(root) / f"{symbol.upper()}.json"


def _compact(results: list[dict]) -> list[dict]:
    """The evidence index: who said what, where, and when -- not the text."""
    return [
        {
            "title": item.get("title"),
            "url": item.get("url"),
            "publisher": item.get("publisher"),
            "source_date": item.get("source_date"),
            "age_days": item.get("age_days"),
            "lens": item.get("lens"),
            "stream": item.get("stream"),
            "query": item.get("query"),
        }
        for item in results or []
    ]


def analyse_one(
    symbol: str,
    *,
    listed: dict | None = None,
    model: str | None = None,
    per_query: int = 5,
    gates: dict | None = None,
    vocabulary: list[dict] | None = None,
) -> dict:
    """Full research pass for one symbol: profile, streams, then three-lens trends.

    ``gates`` is the screen the name was admitted under, recorded in the artifact so
    that the two numbers the published master file states are the ones the batch was
    actually built with -- rather than whatever a later render happens to default to.
    ``vocabulary`` is the theme keys already coined elsewhere, so this company reuses
    them instead of inventing a synonym; see :func:`theme_vocabulary`.
    """
    symbol = symbol.upper()
    errors: list[str] = []
    artifact: dict = {
        "symbol": symbol,
        "researched_on": date.today().isoformat(),
        "model": model or ollama.DEFAULT_MODEL,
        "gates": gates or {},
        "profile": {},
        "streams": {},
        "trends": {},
        "errors": errors,
    }

    try:
        profile = profile_mod.fetch(symbol, listed=listed)
    except Exception as exc:
        errors.append(f"profile: {type(exc).__name__}: {exc}")
        return artifact
    artifact["profile"] = profile

    name = profile.get("name") or symbol
    summary = profile.get("summary")

    try:
        stream_data = streams_mod.extract(
            symbol,
            name,
            summary=summary,
            sector=profile.get("sector"),
            industry=profile.get("industry"),
            model=model,
            per_query=per_query,
        )
    except Exception as exc:
        errors.append(f"streams: {type(exc).__name__}: {exc}")
        stream_data = {
            "queries": streams_mod.plan_queries(name, symbol, profile.get("sector"), profile.get("industry")),
            "streams": [],
            "dropped": [],
            "results_count": 0,
        }
    artifact["streams"] = {**stream_data, "results": _compact(stream_data.get("results"))}

    try:
        trend_data = trends_mod.research(
            symbol,
            name,
            summary=summary,
            sector=profile.get("sector"),
            industry=profile.get("industry"),
            streams=stream_data.get("streams") or [],
            model=model,
            per_query=per_query,
            vocabulary=vocabulary,
        )
    except Exception as exc:
        errors.append(f"trends: {type(exc).__name__}: {exc}")
        trend_data = {"queries": [], "trends": [], "dropped": [], "results_count": 0, "coverage": {}}
    artifact["trends"] = {**trend_data, "results": _compact(trend_data.get("results"))}

    return artifact


def load_analysis(root: Path, symbol: str) -> dict | None:
    path = artifact_path(root, symbol)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def save_analysis(root: Path, artifact: dict) -> Path:
    path = artifact_path(root, artifact["symbol"])
    path.write_text(json.dumps(artifact, indent=2, sort_keys=False))
    return path


def load_all(root: Path) -> list[dict]:
    """Every artifact on disk, newest research date first."""
    out = []
    for path in sorted(analyses_dir(root).glob("*.json")):
        try:
            blob = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if blob.get("symbol"):
            out.append(blob)
    out.sort(key=lambda a: (a.get("researched_on") or "", a["symbol"]))
    return out


def theme_vocabulary(analyses: list[dict], *, limit: int = 120) -> list[dict]:
    """The theme keys already in use, most-used first, for reuse by later companies.

    Seeded from every artifact on disk and grown as a batch progresses, so a wave
    converges on one set of keys instead of coining a synonym per ticker. The count
    behind each key is how many companies already use it, which is what makes the
    most-shared keys the ones offered first.
    """
    counts: dict[str, dict] = {}
    for artifact in analyses:
        for trend in (artifact.get("trends") or {}).get("trends") or []:
            key = trend.get("theme_key")
            if not key:
                continue
            entry = counts.setdefault(
                key,
                {"key": key, "label": trend.get("theme_label") or key, "companies": set()},
            )
            entry["companies"].add(artifact.get("symbol"))
    ordered = sorted(counts.values(), key=lambda e: (-len(e["companies"]), e["key"]))
    return [
        {"key": e["key"], "label": e["label"], "companies": len(e["companies"])}
        for e in ordered[:limit]
    ]


def run(
    root: Path,
    targets: list[dict],
    *,
    model: str | None = None,
    workers: int = 4,
    refresh: bool = False,
    per_query: int = 5,
    gates: dict | None = None,
    log=None,
) -> dict:
    """Research a batch, reusing artifacts unless ``refresh``.

    ``targets`` are pool rows (``symbol`` plus the Nasdaq row it came from).
    Companies are researched concurrently because the work is latency-bound: each
    one waits on a search or a generation, not on a CPU.
    """
    log = log or (lambda message: None)
    todo = []
    reused = 0
    for row in targets:
        symbol = row["symbol"]
        if not refresh and load_analysis(root, symbol):
            reused += 1
            continue
        todo.append(row)

    log(f"researching {len(todo)} name(s), reusing {reused} artifact(s)")
    done: list[dict] = []
    failures: list[dict] = []

    if not todo:
        return {"researched": [], "failures": [], "reused": reused}

    # The shared vocabulary, seeded from the artifacts on disk that are *not* part of
    # this batch, then grown as this batch's companies finish. Excluding the batch's own
    # artifacts matters: seeding from the run being replaced would let each ticker
    # rediscover its own previous keys, which looks like convergence while changing
    # nothing. Held under a lock because the workers read and write it concurrently, and
    # a torn read would offer the synthesiser a partial key list -- worse than none,
    # since it would look authoritative.
    lock = Lock()
    in_batch = {row["symbol"] for row in targets}
    vocabulary: dict[str, dict] = {
        item["key"]: {"key": item["key"], "label": item["label"], "companies": item["companies"]}
        for item in theme_vocabulary([a for a in load_all(root) if a["symbol"] not in in_batch])
    }

    def snapshot() -> list[dict]:
        with lock:
            items = sorted(vocabulary.values(), key=lambda e: (-e["companies"], e["key"]))
            return [dict(item) for item in items[:120]]

    def absorb(artifact: dict) -> None:
        with lock:
            for trend in (artifact.get("trends") or {}).get("trends") or []:
                key = trend.get("theme_key")
                if not key:
                    continue
                entry = vocabulary.setdefault(
                    key, {"key": key, "label": trend.get("theme_label") or key, "companies": 0}
                )
                entry["companies"] = (entry.get("companies") or 0) + 1

    def work(row: dict) -> dict:
        return analyse_one(
            row["symbol"],
            listed=row,
            model=model,
            per_query=per_query,
            gates=gates,
            vocabulary=snapshot(),
        )

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(work, row): row for row in todo}
        for future in as_completed(futures):
            row = futures[future]
            try:
                artifact = future.result()
            except Exception as exc:  # defensive: analyse_one already catches
                failures.append({"symbol": row["symbol"], "error": f"{type(exc).__name__}: {exc}"})
                continue
            save_analysis(root, artifact)
            absorb(artifact)
            done.append(artifact)
            log(
                f"  {artifact['symbol']}: {len((artifact.get('streams') or {}).get('streams') or [])} streams, "
                f"{len((artifact.get('trends') or {}).get('trends') or [])} trends"
                + (f", errors: {len(artifact.get('errors') or [])}" if artifact.get("errors") else "")
            )

    return {"researched": done, "failures": failures, "reused": reused}


def write_ticker_files(root: Path, analyses: list[dict], theme_index: dict | None = None) -> list[Path]:
    written = []
    for analysis in analyses:
        path = tickers_dir(root) / f"{analysis['symbol']}.md"
        path.write_text(writeup.render_ticker(analysis, theme_index))
        written.append(path)
    return written
