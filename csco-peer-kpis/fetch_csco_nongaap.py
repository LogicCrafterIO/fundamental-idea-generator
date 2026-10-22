"""Pull Cisco's own GAAP / non-GAAP figures from its Q4 earnings 8-Ks (FY2021-FY2026).

Why: Cisco's *GAAP* operating margin is depressed by Splunk-related intangible
amortization and restructuring, so a GAAP-only 5-year line overstates how much the
underlying business moved. Cisco publishes a GAAP->non-GAAP bridge in every Q4
press release (EX-99.1 of the earnings 8-K), so the bridge is primary-sourced.

Method (avoids relying on any vendor's adjusted numbers):
    non-GAAP operating income = GAAP operating income          (income statement,
                                                               fiscal-year column)
                              + total adj. to GAAP cost of sales   (raises gross profit)
                              + total adj. to GAAP operating expenses

Column identification: Cisco's tables carry a "Three Months Ended ... Fiscal Year
Ended" header with 4 date columns [Q4 cur, Q4 prior, FY cur, FY prior]. Values sit
in "$"-prefixed groups, so the current fiscal-year value is group index (ncols-2).

SEC requires a declared User-Agent; see https://www.sec.gov/os/webmaster-faq#developers
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = "fundamental-idea-generator research (contact: johncheongzhanhao@example.com)"
CIK = 858877  # Cisco Systems

DATE_RE = re.compile(r"^[A-Z][a-z]+ \d{1,2},\s?\d{4}$")
NUM_RE = re.compile(r"^\(?-?[\d,]+\.?\d*\)?$")


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
        return r.read().decode("utf-8", "ignore")


def tables(hdoc: str) -> list[list[list[str]]]:
    out = []
    for tbl in re.findall(r"<table[^>]*>(.*?)</table>", hdoc, flags=re.S | re.I):
        rows = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, flags=re.S | re.I):
            cells = [
                re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", c))).strip()
                for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S | re.I)
            ]
            cells = [c for c in cells if c]
            if cells:
                rows.append(cells)
        if rows:
            out.append(rows)
    return out


def values(row: list[str]) -> list[float]:
    """Numeric cells of a money row, left to right.

    Works whether or not Cisco wrapped each figure in its own ``$`` cell, because
    the ``$`` and ``%`` cells simply fail to match :data:`NUM_RE` and drop out.
    Only used on periods-across tables (see :func:`header_ncols`), which have no
    Y/Y column to contaminate the sequence.
    """
    vals = []
    for c in row[1:]:
        c = c.replace(" ", "")
        if not NUM_RE.match(c):
            continue
        neg = c.startswith("(")
        try:
            vals.append(-float(c.strip("()").replace(",", "")) if neg else float(c.replace(",", "")))
        except ValueError:
            pass
    return vals


def header_ncols(rows: list[list[str]]) -> int:
    """Number of dated columns in the table header (4 = Q4 cur/prior + FY cur/prior)."""
    return max((sum(1 for c in r if DATE_RE.match(c)) for r in rows[:4]), default=0)


def find_row(rows: list[list[str]], needle: str) -> list[str] | None:
    """Exact (case/space-insensitive) label match, then a startswith fallback.

    Exact-first matters: the cash-flow statement has a *header sentence*
    "Adjustments to reconcile net income to net cash provided by operating
    activities:" that contains the very label we are looking for.
    """
    n = needle.lower()
    for r in rows:
        if r and r[0].strip().lower() == n:
            return r
    for r in rows:
        if r and r[0].strip().lower().startswith(n):
            return r
    return None


def parse_fy(hdoc: str) -> dict[str, float] | None:
    """Read the fiscal-year column of every periods-across table in the release."""
    out: dict[str, float] = {}
    for rows in tables(hdoc):
        ncols = header_ncols(rows)
        if ncols < 2:
            continue  # summary tables (one period, metrics across) -- handled below
        idx = ncols - 2  # [Q4 cur, Q4 prior, FY cur, FY prior]
        header = " ".join(" ".join(r) for r in rows[:2]).lower()
        if ncols == 2 and "fiscal year" not in header:
            continue  # a Q4-only two-column table

        for label, key in (
            ("Total revenue", "gaap_revenue"),
            ("Gross margin", "gaap_gross_profit"),
            ("Operating income", "gaap_op_income"),
            ("Diluted", "eps_gaap"),
            ("Net income", "gaap_net_income"),
            ("Net cash provided by operating activities", "cfo"),
            ("Acquisition of property and equipment", "capex"),
            ("Research and development", "rnd"),
            ("Total adjustments to GAAP cost of sales", "adj_cogs"),
            ("Total adjustments to GAAP operating expenses", "adj_opex"),
        ):
            if key in out:
                continue
            r = find_row(rows, label)
            if r:
                v = values(r)
                if len(v) > idx:
                    out[key] = v[idx]

    if "gaap_op_income" not in out or "gaap_revenue" not in out:
        return None

    rev = out["gaap_revenue"]
    if "adj_cogs" in out:
        # adjustments to cost of sales raise gross profit
        out["non_gaap_gross_profit"] = out["gaap_gross_profit"] + out["adj_cogs"]
        out["non_gaap_gross_margin_pct"] = 100 * out["non_gaap_gross_profit"] / rev

    if "cfo" in out:
        out["fcf"] = out["cfo"] - abs(out.get("capex", 0.0))

    oi = out["gaap_op_income"]
    if "gaap_gross_profit" in out:
        out["gaap_gross_margin_pct"] = 100 * out["gaap_gross_profit"] / rev
    if "adj_cogs" in out and "adj_opex" in out:
        out["non_gaap_op_income"] = oi + out["adj_cogs"] + out["adj_opex"]
        out["non_gaap_op_margin_pct"] = 100 * out["non_gaap_op_income"] / rev
    out["gaap_op_margin_pct"] = 100 * oi / rev
    return out


def q4_8k(fy: int) -> tuple[str, str] | None:
    """Q4 earnings 8-K of fiscal `fy` -- item 2.02, filed in mid-August."""
    data = json.loads(get(f"https://data.sec.gov/submissions/CIK{CIK:010d}.json"))
    r = data["filings"]["recent"]
    for form, date, acc, items in zip(
        r["form"], r["filingDate"], r["accessionNumber"], r["items"]
    ):
        if form == "8-K" and date.startswith(f"{fy}-08") and "2.02" in (items or ""):
            return acc.replace("-", ""), date
    return None


def ex99(acc: str) -> str:
    idx = json.loads(get(f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc}/index.json"))
    names = [i["name"] for i in idx["directory"]["item"]]
    hits = [n for n in names if re.search(r"ex.*99", n, re.I) and n.endswith((".htm", ".html"))]
    if not hits:
        raise FileNotFoundError(f"no EX-99.1 in {acc}: {names}")
    return get(f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc}/{hits[0]}")


def main() -> None:
    out: dict[str, dict[str, float | str]] = {}
    for fy in range(2021, 2027):
        hit = q4_8k(fy)
        if not hit:
            print(f"FY{fy}: no Q4 8-K found")
            continue
        acc, date = hit
        try:
            d = parse_fy(ex99(acc))
        except Exception as exc:  # noqa: BLE001
            print(f"FY{fy}: {type(exc).__name__}: {exc}")
            continue
        if not d:
            print(f"FY{fy}: parse found no income statement")
            continue
        d["filing_date"] = date
        d["url"] = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc}/"
        out[f"FY{fy}"] = d
        print(
            f"FY{fy} ({date})  rev={d.get('gaap_revenue')}  GAAP OI={d.get('gaap_op_income')} "
            f"({d.get('gaap_op_margin_pct'):.1f}%)  non-GAAP OI={d.get('non_gaap_op_income')} "
            f"({d.get('non_gaap_op_margin_pct'):.1f}%)"
        )
        time.sleep(1)

    (HERE / "data" / "csco_nongaap.json").write_text(json.dumps(out, indent=1))
    print("\nwrote data/csco_nongaap.json")


if __name__ == "__main__":
    main()
