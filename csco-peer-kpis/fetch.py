"""Pull annual fundamentals for Cisco and its networking/security peer set.

Everything comes from yfinance (Yahoo Finance annual statements). Fiscal years
are kept as reported -- the companies do NOT share a fiscal calendar:

    CSCO  July    (FY2026 ended 2026-07-31)
    PANW  July    (FY2026 ended 2026-07-31)
    HPE   October (FY2025 ended 2025-10-31)
    ANET  December
    FTNT  December
    NOK   December
    ERIC  December
    FFIV  September
    JNPR  December (delisted -- acquired by HPE, 2025-07-02)

Output: data/fundamentals.csv (long form) + data/fundamentals.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent

TICKERS = {
    "CSCO": ("Cisco", "Jul"),
    "ANET": ("Arista Networks", "Dec"),
    "HPE": ("Hewlett Packard Enterprise", "Oct"),
    "PANW": ("Palo Alto Networks", "Jul"),
    "FTNT": ("Fortinet", "Dec"),
    "FFIV": ("F5", "Sep"),
    "NOK": ("Nokia", "Dec"),
    "ERIC": ("Ericsson", "Dec"),
    "JNPR": ("Juniper Networks", "Dec"),
}

# yfinance row labels we care about -> our column name.
INC = {
    "Total Revenue": "revenue",
    "Cost Of Revenue": "cogs",
    "Gross Profit": "gross_profit",
    "Research And Development": "rnd",
    "Selling General And Administration": "sga",
    "Operating Income": "operating_income_yahoo",
    "Total Operating Income As Reported": "operating_income",
    "Net Income": "net_income",
    "Net Income Common Stockholders": "net_income_common",
    "Diluted EPS": "eps_diluted",
    "Diluted Average Shares": "shares_diluted",
}
CF = {
    "Operating Cash Flow": "cfo",
    "Capital Expenditure": "capex",
    "Free Cash Flow": "fcf",
    "Repurchase Of Capital Stock": "buybacks",
    "Cash Dividends Paid": "dividends",
}


def _row(df: pd.DataFrame, label: str) -> pd.Series | None:
    if df is None or df.empty or label not in df.index:
        return None
    return df.loc[label]


def pull(ticker: str) -> pd.DataFrame:
    tk = yf.Ticker(ticker)
    try:
        inc, cf = tk.income_stmt, tk.cashflow
    except Exception as exc:  # noqa: BLE001
        print(f"  !! {ticker}: {type(exc).__name__}: {exc}")
        return pd.DataFrame()

    rows: dict[str, pd.Series] = {}
    for label, name in INC.items():
        s = _row(inc, label)
        if s is not None:
            rows[name] = s
    for label, name in CF.items():
        s = _row(cf, label)
        if s is not None:
            rows[name] = s

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df.index)
    df.index.name = "fy_end"
    df = df.sort_index()
    return df


def main() -> None:
    frames = []
    for ticker, (name, fy_end_month) in TICKERS.items():
        print(f"pulling {ticker} ...")
        df = pull(ticker)
        if df.empty:
            print(f"  -- no data for {ticker}")
            continue
        df = df.reset_index()
        df.insert(0, "ticker", ticker)
        df.insert(1, "company", name)
        df.insert(2, "fy_end_month", fy_end_month)
        frames.append(df)

    allrows = pd.concat(frames, ignore_index=True)
    allrows["fy"] = allrows["fy_end"].dt.year
    allrows["fy_label"] = (
        allrows["fy_end"].dt.year.astype(str) + "-" + allrows["fy_end"].dt.strftime("%m")
    )
    out_csv = HERE / "data" / "fundamentals.csv"
    allrows.to_csv(out_csv, index=False)
    (HERE / "data" / "fundamentals.json").write_text(
        allrows.to_json(orient="records", date_format="iso", indent=1)
    )
    print(f"\nwrote {out_csv}  ({len(allrows)} rows)")
    print(allrows.groupby("ticker")["fy_label"].agg(["count", "min", "max"]))


if __name__ == "__main__":
    main()
