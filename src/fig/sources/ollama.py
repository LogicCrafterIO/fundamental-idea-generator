"""Ollama Cloud: web search *and* LLM generation, from the same key.

Two capabilities, one endpoint family and one credential:

* ``POST /api/web_search``  -- live web/news search returning title, url and a
  content snippet. This is the *search* half and it materially upgrades the news
  layer: yfinance and Nasdaq give syndicated finance-feed headlines, whereas web
  search reaches the primary reporting behind them (it surfaced an FT story on
  Oracle's $18bn of data-centre debt that never appeared in either feed).
* ``POST /v1/chat/completions`` -- OpenAI-compatible chat, used for the
  distillation step.

Why this lives in ``sources``
-----------------------------
Search is an evidence source, so it belongs beside the other sources, and the
packet treats it exactly like a feed. Chat is consumed by :mod:`fig.generate`.

Credentials
-----------
Reads ``OLLAMA_API_KEY`` from the environment, falling back to a ``.env`` file at
the repo root. The key is never logged: errors report the status code, not the
request. ``list_models`` is provided so a run can fail early and loudly on a bad
key rather than half way through a batch.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

API_BASE = os.environ.get("OLLAMA_HOST", "https://ollama.com").rstrip("/")
CHAT_URL = f"{API_BASE}/v1/chat/completions"
SEARCH_URL = f"{API_BASE}/api/web_search"
MODELS_URL = f"{API_BASE}/v1/models"

# The qualitative work -- planning end-market queries, synthesising trends, and
# writing the note -- is latency-bound and benefits far more from speed than from
# the largest available model. Overridable per call with --model or globally with
# FIG_MODEL.
DEFAULT_MODEL = os.environ.get("FIG_MODEL", "deepseek-v4.1-flash")

_env_cache: dict[str, str] | None = None


def _load_env() -> dict[str, str]:
    """Parse the repo ``.env`` (no python-dotenv dependency; it is one format)."""
    global _env_cache
    if _env_cache is not None:
        return _env_cache

    values: dict[str, str] = {}
    # Walk up from this file so the package works when installed (editable or not).
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if candidate.is_file():
            try:
                for raw in candidate.read_text().splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    values[key.strip()] = value.strip().strip("'\"")
            except OSError:
                pass
            break
    _env_cache = values
    return values


def api_key() -> str | None:
    """The Ollama key, from the environment first, then ``.env``."""
    from_env = os.environ.get("OLLAMA_API_KEY")
    if from_env:
        return from_env.strip()
    return _load_env().get("OLLAMA_API_KEY")


def has_key() -> bool:
    return bool(api_key())


def _headers() -> dict[str, str]:
    key = api_key()
    if not key:
        raise RuntimeError(
            "OLLAMA_API_KEY is not set. Put it in the environment or in .env at the repo root."
        )
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        # Ollama cloud sits behind Cloudflare, which rejects unknown agents.
        "User-Agent": "fundamental-idea-generator/0.1",
    }


def _post(url: str, payload: dict, *, timeout: int = 180, retries: int = 3) -> Any:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.post(url, headers=_headers(), json=payload, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            # 401/403 are terminal: the key is wrong, retrying will not help.
            if resp.status_code in (401, 403):
                raise RuntimeError(
                    f"Ollama rejected the key (HTTP {resp.status_code}). "
                    "Check OLLAMA_API_KEY."
                )
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                last = RuntimeError(f"HTTP {resp.status_code} from {url}")
            else:
                raise RuntimeError(f"HTTP {resp.status_code} from {url}: {resp.text[:200]}")
        except Exception as exc:  # noqa: BLE001 - retried, then re-raised
            last = exc
        if attempt < retries - 1:
            time.sleep((2 ** attempt) * 1.5)
    raise RuntimeError(f"POST failed after {retries} attempts: {url}") from last


# --------------------------------------------------------------------------
# search
# --------------------------------------------------------------------------


def web_search(query: str, max_results: int = 6, *, timeout: int = 60) -> list[dict]:
    """Search the web. Returns ``[{title, url, content, source}]``.

    ``content`` is a substantial snippet -- often several hundred words of the
    actual article -- which is what makes this usable as evidence rather than
    just a headline list.
    """
    payload: dict[str, Any] = {"query": query}
    if max_results:
        payload["max_results"] = max_results

    data = _post(SEARCH_URL, payload, timeout=timeout)
    results = (data or {}).get("results") or []
    out = []
    for row in results:
        out.append(
            {
                "title": (row.get("title") or "").strip(),
                "url": row.get("url"),
                "content": (row.get("content") or "").strip(),
                "publisher": _publisher_from_url(row.get("url")),
                "source": "ollama_search",
                "query": query,
            }
        )
    return [r for r in out if r["title"]]


def _publisher_from_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        host = url.split("//", 1)[-1].split("/", 1)[0]
    except (IndexError, AttributeError):
        return None
    return host[4:] if host.startswith("www.") else host


def search_stories(
    symbol: str,
    company_name: str | None = None,
    *,
    extra_queries: list[str] | None = None,
    per_query: int = 5,
) -> list[dict]:
    """Search for fundamental stories about one company.

    Query design matters more than volume. Three angles cover the ground without
    drowning the writer in repetition:

    * ``news``      -- what happened recently
    * ``guidance``  -- what management and analysts now expect
    * ``thesis``    -- bears and bulls, which is where non-consensus material lives

    The last is deliberate: the reference notes are non-consensus, so the
    evidence has to include the argument against the crowd.
    """
    label = f"{company_name} ({symbol})" if company_name else symbol
    queries = [
        f"{label} stock news earnings guidance",
        f"{label} analyst estimates revision outlook",
        f"{label} bull bear case risks",
    ]
    if extra_queries:
        queries.extend(extra_queries)

    items: list[dict] = []
    for query in queries:
        try:
            items.extend(web_search(query, max_results=per_query))
        except Exception as exc:  # search is additive; never fail the packet over it
            items.append(
                {
                    "title": "",
                    "url": None,
                    "content": "",
                    "source": "ollama_search",
                    "error": f"{type(exc).__name__}: {exc}",
                    "query": query,
                }
            )
    return [i for i in items if i.get("title")]


# --------------------------------------------------------------------------
# chat
# --------------------------------------------------------------------------


def list_models(*, timeout: int = 30) -> list[str]:
    """Available models. Use this to fail fast on a bad key."""
    resp = requests.get(MODELS_URL, headers=_headers(), timeout=timeout)
    resp.raise_for_status()
    return sorted(m["id"] for m in (resp.json().get("data") or []))


def chat(
    messages: list[dict],
    *,
    model: str = DEFAULT_MODEL,
    json_mode: bool = True,
    temperature: float = 0.2,
    max_tokens: int | None = None,
    timeout: int = 300,
) -> dict:
    """One chat completion.

    Returns ``{text, model, usage, elapsed, finish_reason}``. ``json_mode`` asks
    the server to constrain output to a JSON object, which is what makes the
    writeup schema reliable rather than a parsing lottery.
    """
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if max_tokens:
        payload["max_tokens"] = max_tokens

    started = time.monotonic()
    data = _post(CHAT_URL, payload, timeout=timeout)
    elapsed = time.monotonic() - started

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"no choices in response: {json.dumps(data)[:300]}")
    message = choices[0].get("message") or {}

    return {
        "text": message.get("content") or "",
        "model": data.get("model") or model,
        "usage": data.get("usage") or {},
        "finish_reason": choices[0].get("finish_reason"),
        "elapsed": round(elapsed, 2),
    }


def parse_json_object(text: str) -> dict:
    """Extract a JSON object from a model response.

    JSON mode makes valid JSON the common case, but models still occasionally
    wrap it in fences or add a sentence before it. Try strict parsing first, then
    fall back to the outermost brace pair, so a good answer is not thrown away
    over formatting.
    """
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("```")[1] if len(text.split("```")) > 1 else text
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"model did not return parseable JSON: {exc}") from exc
    raise RuntimeError("model did not return a JSON object")
