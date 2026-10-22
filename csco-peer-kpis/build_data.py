"""Assemble the KPI tables behind the charts.

Two views, because they answer different questions:

``kpis_annual.csv``
    Each company's own reported fiscal year. Best for "how has this trended",
    worst for "who is winning right now" -- Cisco and Palo Alto close in July,
    HPE closes in October, Arista and Fortinet close in December, so the latest
    plotted year is not the same 12 months for everybody.

``kpis_ttm.csv``
    Trailing twelve months through each company's most recent reported quarter
    (all of them land on Jun/Jul 2026), with growth measured TTM-over-prior-TTM.
    This is the like-for-like comparison.

Sources
-------
* CSCO FY2021-FY2026: Cisco's own Q4 earnings 8-Ks on EDGAR (see
  ``fetch_csco_nongaap.py``) -- primary, and it carries the GAAP->non-GAAP bridge.
* Peers: Yahoo Finance annual/quarterly statements via yfinance. Cross-checked
  against Cisco's FY2026 press release, which the pipeline reproduces to the
  dollar (revenue 63,325 / gross profit 40,860 / R&D 9,563 / operating income
  15,368 / net income 13,267).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

PEERS = ["ANET", "HPE", "PANW", "FTNT"]
ALL_TICKERS = ["CSCO", *PEERS, "NOK", "ERIC", "FFIV"]

LABEL = {
    "CSCO": "Cisco",
    "ANET": "Arista Networks",
    "HPE": "Hewlett Packard Enterprise",
    "PANW": "Palo Alto Networks",
    "FTNT": "Fortinet",
    "FFIV": "F5",
    "NOK": "Nokia",
    "ERIC": "Ericsson",
}

# Cisco restated FY2025 in the FY2026 release: a $355m legal/indemnification
# charge moved out of "interest and other" into cost of sales. We use the
# restated basis so the FY2024-FY2026 line is continuous. Non-GAAP is unaffected.
CSCO_FY2025_RESTATED = {"gaap_gross_profit": 36790.0, "gaap_op_income": 11760.0}


def csco_annual() -> pd.DataFrame:
    raw = json.loads((DATA / "csco_nongaap.json").read_text())
    rows = []
    for fy_label, d in sorted(raw.items()):
        fy = int(fy_label[2:])
        d = {**d, **CSCO_FY2025_RESTATED} if fy == 2025 else d
        rev = d["gaap_revenue"]
        rows.append(
            {
                "ticker": "CSCO",
                "company": LABEL["CSCO"],
                "fy": fy,
                "fy_end": pd.Timestamp(f"{fy}-07-31"),
                "revenue": rev,
                "gross_profit": d.get("gaap_gross_profit"),
                "operating_income": d.get("gaap_op_income"),
                "net_income": d.get("gaap_net_income"),
                "rnd": d.get("rnd"),
                "eps_diluted": d.get("eps_gaap"),
                "cfo": d.get("cfo"),
                "capex": d.get("capex"),
                "fcf": d.get("fcf"),
                # Cisco-only, from its published GAAP->non-GAAP bridge
                "non_gaap_op_income": d.get("non_gaap_op_income"),
                "non_gaap_gross_profit": d.get("non_gaap_gross_profit"),
                "non_gaap_gross_margin_pct": d.get("non_gaap_gross_margin_pct"),
                "adj_cogs": d.get("adj_cogs"),
                "adj_opex": d.get("adj_opex"),
                "source": d.get("url", ""),
            }
        )
    return pd.DataFrame(rows)


def peers_annual() -> pd.DataFrame:
    df = pd.read_csv(DATA / "fundamentals.csv")
    df = df[df.ticker.isin(PEERS)].copy()
    df["fy_end"] = pd.to_datetime(df["fy_end"])
    keep = [
        "ticker", "company", "fy", "fy_end", "revenue", "gross_profit",
        "operating_income", "net_income", "rnd", "eps_diluted", "cfo", "capex", "fcf",
    ]
    df = df[keep]
    # yfinance reports these in raw dollars; the Cisco EDGAR series is in millions.
    money = ["revenue", "gross_profit", "operating_income", "net_income",
             "rnd", "cfo", "capex", "fcf"]
    df[money] = df[money] / 1e6
    for c in ("non_gaap_op_income", "non_gaap_gross_profit", "non_gaap_gross_margin_pct"):
        df[c] = pd.NA
    df["source"] = "Yahoo Finance (annual statements, via yfinance)"
    return df[df.revenue.notna()]


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Margins, growth and intensity ratios (all in percent)."""
    df = df.sort_values(["ticker", "fy"]).copy()
    df["gross_margin"] = 100 * df.gross_profit / df.revenue
    df["op_margin_gaap"] = 100 * df.operating_income / df.revenue
    df["op_margin_non_gaap"] = 100 * df.non_gaap_op_income / df.revenue
    df["net_margin"] = 100 * df.net_income / df.revenue
    df["fcf_margin"] = 100 * df.fcf / df.revenue
    df["rnd_pct"] = 100 * df.rnd / df.revenue
    df["rev_growth"] = 100 * df.groupby("ticker").revenue.pct_change()
    df["eps_growth"] = 100 * df.groupby("ticker").eps_diluted.pct_change()
    return df


# --------------------------------------------------------------------------- TTM

# "Total Operating Income As Reported" is GAAP as reported; Yahoo's plain
# "Operating Income" is a slightly different construct (verified: it puts CSCO
# FY2026 at 16,061 vs the 15,368 Cisco actually reported).
TTM_INC = {"Total Revenue": "revenue", "Gross Profit": "gross_profit",
           "Operating Income": "operating_income",
           "Research And Development": "rnd"}

# Nokia reports in EUR, Ericsson in SEK -- their levels are not comparable to the
# USD names, though their margins are.
CURRENCY = {"NOK": "EUR", "ERIC": "SEK"}
TTM_CF = {"Operating Cash Flow": "cfo", "Capital Expenditure": "capex"}


def ttm() -> pd.DataFrame:
    """Trailing-twelve-month levels plus latest-quarter YoY growth.

    Yahoo only serves 5-7 quarters, which is enough for a 4-quarter TTM level but
    not for a prior-year TTM. So growth is measured on the single most recent
    reported quarter versus the same quarter a year earlier -- an aligned window
    across companies, and the number each management team actually guides on.
    """
    rows = []
    for t in ALL_TICKERS:
        tk = yf.Ticker(t)
        try:
            qi, qc = tk.quarterly_income_stmt, tk.quarterly_cashflow
        except Exception as exc:  # noqa: BLE001
            print(f"  !! {t}: {exc}")
            continue
        if qi is None or qi.empty or len(qi.columns) < 5:
            print(f"  -- {t}: only {0 if qi is None else len(qi.columns)} quarters")
            continue

        def val(src, label, i):
            if src is None or label not in src.index:
                return None
            s = src.loc[label]
            v = s.iloc[i] if i < len(s) else None
            return None if v is None or pd.isna(v) else float(v)

        def ttm_sum(src, label):
            if src is None or label not in src.index:
                return None
            s = src.loc[label].iloc[:4].dropna()
            return float(s.sum()) if len(s) == 4 else None

        rec: dict[str, object] = {
            "ticker": t, "company": LABEL[t], "currency": CURRENCY.get(t, "USD"),
        }
        rec["ttm_end"] = pd.to_datetime(qi.columns[0])
        for label, key in TTM_INC.items():
            rec[key] = ttm_sum(qi, label) / 1e6
            rec[key + "_q"] = (val(qi, label, 0) or 0) / 1e6
            rec[key + "_q_prior"] = (val(qi, label, 4) or 0) / 1e6
        for label, key in TTM_CF.items():
            rec[key] = ttm_sum(qc, label) / 1e6
        rec["quarter_label"] = pd.to_datetime(qi.columns[0]).strftime("%b %Y")
        rows.append(rec)

    df = pd.DataFrame(rows)
    df = df[df.revenue.notna()].copy()

    # Where a company's TTM window *is* its fiscal year (Cisco and Palo Alto both
    # close in July), prefer the as-reported annual figures so the two tables in
    # this analysis cannot disagree with each other.
    ann = pd.read_csv(DATA / "kpis_annual.csv", parse_dates=["fy_end"])
    ann = ann.set_index(["ticker", "fy_end"])
    for i, r in df.iterrows():
        key = (r.ticker, r.ttm_end)
        if key in ann.index:
            a = ann.loc[key]
            for c in ("revenue", "gross_profit", "operating_income", "rnd"):
                df.at[i, c] = float(a[c])
    df["fcf"] = df.cfo - df.capex.abs()
    df["rev_growth_q"] = 100 * (df.revenue_q / df.revenue_q_prior - 1)
    df["gross_margin"] = 100 * df.gross_profit / df.revenue
    df["op_margin_gaap"] = 100 * df.operating_income / df.revenue
    df["fcf_margin"] = 100 * df.fcf / df.revenue
    df["rnd_pct"] = 100 * df.rnd / df.revenue
    return df


def main() -> None:
    annual = add_derived(pd.concat([csco_annual(), peers_annual()], ignore_index=True))
    annual.to_csv(DATA / "kpis_annual.csv", index=False)
    print("=== annual (USD millions unless %) ===")
    cols = ["ticker", "fy", "revenue", "rev_growth", "gross_margin", "op_margin_gaap",
            "op_margin_non_gaap", "fcf_margin", "rnd_pct", "eps_diluted"]
    print(annual[cols].round(1).to_string(index=False))

    t = ttm()
    t.to_csv(DATA / "kpis_ttm.csv", index=False)
    print("\n=== TTM through latest reported quarter ===")
    cols = ["ticker", "ttm_end", "quarter_label", "revenue", "rev_growth_q",
            "gross_margin", "op_margin_gaap", "fcf_margin", "rnd_pct"]
    print(t[cols].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
