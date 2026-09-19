"""Shared helpers: polite HTTP with on-disk caching, and money/number parsing.

Design notes
------------
Both data sources (Nasdaq's undocumented JSON API and Yahoo via yfinance) are
free but rate-limit aggressively and occasionally 5xx. Every network call in
this package goes through :func:`cached_json` so that:

* repeated runs during development cost nothing,
* a flaky upstream never kills a whole batch,
* and the exact bytes behind any number in a writeup are recoverable for audit.

Cache entries are keyed by a caller-supplied string, so two callers asking for
the same thing share one fetch.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import time
from pathlib import Path
from typing import Any, Callable

import requests

# --------------------------------------------------------------------------
# cache
# --------------------------------------------------------------------------

_CACHE_ROOT = Path(os.environ.get("FIG_CACHE_DIR", ".cache/fig"))
_DEFAULT_TTL = int(os.environ.get("FIG_CACHE_TTL", 60 * 60 * 6))  # 6h
DISABLE_CACHE = os.environ.get("FIG_NO_CACHE") == "1"

# Nasdaq in particular gets unhappy if hammered; keep a floor between calls.
_MIN_INTERVAL = float(os.environ.get("FIG_MIN_INTERVAL", 0.35))
_last_call = 0.0


def _throttle() -> None:
    global _last_call
    delta = time.monotonic() - _last_call
    if delta < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - delta)
    _last_call = time.monotonic()


def _cache_path(key: str) -> Path:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", key)[:70]
    return _CACHE_ROOT / f"{slug}.{digest}.json"


def cached_json(
    key: str,
    producer: Callable[[], Any],
    ttl: int | None = None,
    *,
    allow_cache: bool = True,
) -> Any:
    """Return ``producer()``, memoised on disk under ``key`` for ``ttl`` seconds.

    A cache hit is returned even when the entry is stale if the producer raises,
    so a transient upstream failure degrades to slightly-old data rather than a
    crash. ``None`` results are never cached (they usually mean "no data",
    which may change on the next run).
    """
    ttl = _DEFAULT_TTL if ttl is None else ttl
    path = _cache_path(key)

    fresh: Any = None
    if allow_cache and not DISABLE_CACHE and path.exists():
        try:
            blob = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            blob = None
        if isinstance(blob, dict) and "value" in blob:
            age = time.time() - blob.get("stored_at", 0)
            if age <= ttl:
                return blob["value"]
            fresh = blob["value"]  # stale, but usable as a fallback

    try:
        value = producer()
    except Exception:
        if fresh is not None:
            return fresh
        raise

    if value is not None and allow_cache and not DISABLE_CACHE:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"stored_at": time.time(), "key": key, "value": value})
            )
        except (OSError, TypeError):
            pass  # caching is best-effort; never fail the caller over it
    return value


# --------------------------------------------------------------------------
# http
# --------------------------------------------------------------------------

# Nasdaq's API rejects requests without a browser-ish UA.
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


def http_json(
    url: str,
    headers: dict[str, str] | None = None,
    *,
    retries: int = 3,
    timeout: int = 25,
) -> Any:
    """GET ``url`` and parse JSON, retrying with jittered backoff."""
    hdrs = {**DEFAULT_HEADERS, **(headers or {})}
    last_err: Exception | None = None

    for attempt in range(retries):
        _throttle()
        try:
            resp = requests.get(url, headers=hdrs, timeout=timeout, allow_redirects=True)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (403, 429) or 500 <= resp.status_code < 600:
                last_err = RuntimeError(f"HTTP {resp.status_code} for {url}")
            else:
                # 404 etc. are genuine answers, not worth retrying.
                raise RuntimeError(f"HTTP {resp.status_code} for {url}")
        except Exception as exc:  # noqa: BLE001 - retried, then re-raised
            last_err = exc
        if attempt < retries - 1:
            time.sleep((2 ** attempt) * 0.6 + random.random() * 0.4)

    raise RuntimeError(f"GET failed after {retries} attempts: {url}") from last_err


# --------------------------------------------------------------------------
# parsing helpers
# --------------------------------------------------------------------------

_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def parse_money(value: Any) -> float | None:
    """Parse the many money shapes these APIs emit.

    Handles ``"$1,234.56"``, ``"($0.86)"`` (accounting negative), ``"1.2B"``,
    ``"$5,356,707,000,000"``, ``"--"``/``""``/``"N/A"`` (-> ``None``) and bare
    numbers. Returns ``None`` when there is no number to find.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text or text.upper() in {"N/A", "NA", "--", "-", "NONE", "NULL"}:
        return None

    negative = text.startswith("(") and text.endswith(")")
    # Scale suffixes are used inconsistently across Nasdaq endpoints.
    scale = 1.0
    suffix = text.rstrip(")").strip()[-1:].upper()
    if suffix in {"K", "M", "B", "T"}:
        scale = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[suffix]

    match = _NUM_RE.search(text.replace(",", ""))
    if not match:
        return None
    number = float(match.group())
    if scale != 1.0:
        # Guard against a trailing letter being part of a junk token.
        number *= scale
    return -number if negative else number


def human_money(value: float | None, digits: int = 2) -> str:
    """Format a large number the way the reference writeups do: ``455B``, ``7.07B``."""
    if value is None:
        return "n/a"
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    for cut, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if magnitude >= cut:
            scaled = magnitude / cut
            text = f"{scaled:.{digits}f}".rstrip("0").rstrip(".")
            return f"{sign}{text}{suffix}"
    return f"{sign}{magnitude:,.{digits}f}".rstrip("0").rstrip(".")


def pct(new: float | None, old: float | None) -> float | None:
    """Percent change from ``old`` to ``new``."""
    if new is None or old in (None, 0):
        return None
    return (new - old) / abs(old) * 100.0


def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]
