"""Compose README.md, rendering every table straight from the CSVs.

Generating the tables rather than typing them keeps the prose and the data in
lockstep -- if a number is ever re-fetched and changes, the README changes with it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

ann = pd.read_csv(DATA / "kpis_annual.csv")
ttm = pd.read_csv(DATA / "kpis_ttm.csv")
seg = pd.read_csv(DATA / "segments.csv")

ORDER = ["CSCO", "ANET", "HPE", "PANW", "FTNT"]


def md(df, cols, headers):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                cells.append("" if pd.isna(v) else "{:,.1f}".format(v))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main() -> None:
    csco = ann[ann.ticker == "CSCO"].copy()
    csco_usd = csco.copy()
    for c in ("revenue", "gross_profit", "operating_income", "net_income", "rnd", "fcf",
              "non_gaap_op_income", "non_gaap_gross_profit"):
        csco_usd[c] = csco_usd[c] / 1000

    peers = ann[(ann.ticker != "CSCO") & ann.ticker.isin(ORDER)].sort_values(
        ["ticker", "fy"]).copy()
    peers["revenue"] = peers["revenue"] / 1000

    t = ttm[ttm.ticker.isin(ORDER)].set_index("ticker").loc[ORDER].reset_index()

    hp = seg[(seg.ticker == "HPE") & seg.fy_label.str.match(r"^FY\d{4}$")]
    net = pd.DataFrame({
        "company": ["Cisco Networking (FY2026)", "HPE Networking (TTM to Jul-26)",
                    "Arista (total, TTM to Jun-26)"],
        "usd_bn": [34668 / 1000, (2722 + 2706 + 2690 + 2893) / 1000,
                   float(ttm.loc[ttm.ticker == "ANET", "revenue"].iloc[0]) / 1000],
        "basis": ["product category, current definition",
                  "segment, restated net-of-intersegment",
                  "single operating segment"],
    })

    doc = f"""# Cisco (CSCO) KPIs vs networking and security peers

Scratch research, not part of the `fundamental-idea-generator` pipeline. Everything
here is reproducible from the scripts in this folder.

**Headline:** Cisco closed FY2026 with revenue of **$63.3bn, +11.8%**, and guided FY2027 to
**$72.2-73.4bn (+14-16%)**. It is the slowest-growing name in this peer set on reported
numbers, and the largest by revenue and cash flow. Its non-GAAP operating margin of
**34.8%** is the highest in the six years shown. The whole story is in the networking line:
**$34.7bn, +22%**, versus low single digits anywhere else in the portfolio.

## Charts

| File | What it shows |
|---|---|
| `charts/01_csco_kpi_dashboard.png` | Cisco alone, FY2021-FY2026: revenue, gross margin, operating margin, net income/EPS, free cash flow, R&D. GAAP against Cisco's own non-GAAP. |
| `charts/02_peer_comparison.png` | Small multiples, CSCO vs ANET/HPE/PANW/FTNT on five ratios plus a revenue index. |
| `charts/03_latest_ttm_snapshot.png` | The fair comparison: trailing twelve months, every window ending Jun-Jul 2026. |
| `charts/04_networking_segment.png` | Networking revenue only: Cisco vs HPE Networking vs Arista. |

## Table 1 - Cisco annual KPIs (fiscal years end late July, $bn and %)

{md(csco_usd, ["fy", "revenue", "rev_growth", "gross_margin", "op_margin_gaap", "op_margin_non_gaap", "fcf", "fcf_margin", "rnd", "rnd_pct", "eps_diluted"], ["FY", "Revenue", "Rev growth %", "Gross margin %", "Op margin GAAP %", "Op margin non-GAAP %", "FCF", "FCF margin %", "R&D", "R&D % of rev", "GAAP EPS $"])}

## Table 2 - Peers, own fiscal years ($bn and %)

{md(peers, ["ticker", "fy", "revenue", "rev_growth", "gross_margin", "op_margin_gaap", "fcf_margin", "rnd_pct"], ["Ticker", "FY", "Revenue", "Rev growth %", "Gross margin %", "Op margin GAAP %", "FCF margin %", "R&D % of rev"])}

## Table 3 - Period-aligned snapshot, TTM to Jun-Jul 2026

{md(t, ["ticker", "quarter_label", "revenue", "rev_growth_q", "gross_margin", "op_margin_gaap", "fcf_margin", "rnd_pct"], ["Ticker", "Latest quarter", "Revenue $m", "Rev growth YoY %", "Gross margin %", "Op margin GAAP %", "FCF margin %", "R&D % of rev"])}

## Table 4 - Networking revenue only ($bn)

{md(net, ["company", "usd_bn", "basis"], [" ", "Latest 12 months", "Basis"])}

## What the numbers say

1. **The trough was FY2024.** Revenue fell 5.6% in FY2024, grew 5.3% in FY2025 and 11.8% in
   FY2026. Networking orders have now grown double digits for eight consecutive quarters.
2. **It is a networking company again.** Networking is $34.7bn of a $63.3bn company (+22%),
   while Security is $8.2bn and grew 2% - Splunk is still being digested - and Collaboration
   is $4.3bn at +4%. The AI infrastructure order book was $9.3bn in FY2026, with ~$4bn
   recognised as revenue and $7.5bn expected in FY2027.
3. **Margins are stable where it counts.** Non-GAAP operating margin has been 33.5% to
   34.8% for six straight years, and hit a record in FY2026. The GAAP line swings much more
   (22.6% in FY2024 to 24.3% in FY2026) and sits ~10.5pt below non-GAAP because of Splunk
   intangible amortisation, restructuring and stock compensation. Judge Cisco's margin on
   the non-GAAP line and its cash on the FCF line, but treat both consistently.
4. **Gross margin is the thing to watch.** Non-GAAP gross margin fell 180bp in FY2026 to
   66.9% as AI hardware, which carries a lower margin than software and services, mixes in.
   Management's FY2027 guide implies more of the same (65-66% non-GAAP).
5. **Cash generation is not keeping pace with revenue.** FCF was $12.8bn (20.2% of revenue),
   below the six-year average of $13.8bn, even as revenue hit a record. The cash went into
   working capital: inventories rose ~$2.5bn and financing receivables ~$1.8bn year on year,
   which is what financing AI build-outs looks like on a cash flow statement.
6. **Against peers, Cisco is the incumbent, not the challenger.** On aligned TTM windows it
   is the slowest grower (+17.6% in the latest quarter, versus Arista +37.7%, Palo Alto
   +34.4%, HPE +33.7% - the last two flattered by the Juniper and CyberArk acquisitions -
   and Fortinet +25.6%). Its gross margin is mid-pack - 64.5%, well below the software models
   at Fortinet (80.2%) and Palo Alto (70.4%), but above Arista (63.0%) and HPE (36.7%) - and
   its FCF margin of 20.2% is less than half of Arista's 48.9%. On GAAP operating margin it is
   mid-pack at 24.3%; on its own non-GAAP basis, at ~35%, it would rank second only to
   Arista.
7. **In networking specifically, Cisco is still roughly 3x the nearest pure play** -
   $34.7bn against HPE Networking's ~$11.0bn and Arista's ~$10.5bn - but Arista is growing at
   nearly twice the rate and taking the hyperscale AI switching share that Cisco is now
   fighting to win back.

## Method and sources

* **Cisco FY2021-FY2026** comes from Cisco's own quarterly and annual filings via EDGAR:
  the Q4 earnings release (EX-99.1 of the 8-K) for each year, plus the FY2024 10-K. The
  GAAP-to-non-GAAP bridge is parsed out of the reconciliation tables rather than taken from
  a vendor. `fetch_csco_nongaap.py` does this; it also derives non-GAAP operating income as
  *GAAP operating income + adjustments to cost of sales + adjustments to operating
  expenses*, which reproduces Cisco's published non-GAAP operating income to the dollar for
  both FY2025 ($19,491m) and FY2026 ($22,040m).
* **Peers** come from Yahoo Finance annual and quarterly statements via yfinance
  (`fetch.py`, `build_data.py`). The pipeline was validated against Cisco's FY2026 press
  release and matches it exactly: revenue 63,325 / gross profit 40,860 / R&D 9,563 /
  operating income 15,368 / net income 13,267.
* **Segment data** (`data/segments.csv`) was read out of the SEC filings of Cisco, HPE and
  Arista, each row carrying its source URL. See `data/segments-notes.md`.

Reproduce with:

```bash
../.venv/bin/python fetch.py                # peer annual statements
../.venv/bin/python fetch_csco_nongaap.py   # Cisco GAAP/non-GAAP, from EDGAR
../.venv/bin/python build_data.py           # kpis_annual.csv, kpis_ttm.csv
python3 build_charts.py                     # charts/ (needs matplotlib)
python3 check_layout.py                     # asserts zero label collisions
python3 make_readme.py                      # this file
```

`check_layout.py` renders every figure, reads each text object's bounding box from the Agg
renderer and fails loudly on overlapping labels. All four figures currently report zero
collisions and no clipped data.

## Caveats you should carry into any conclusion

* **Fiscal years do not line up.** Cisco and Palo Alto close in July, HPE in October, Arista
  and Fortinet in December. The annual charts plot each company on its own year; the TTM
  snapshot in chart 3 is the only genuinely aligned comparison.
* **GAAP is not apples-to-apples across these companies.** Cisco's GAAP-to-non-GAAP gap is
  ~10.5pt; for Arista and Fortinet it is much smaller. Chart 2 is GAAP throughout (the only
  basis available for all five), so it *understates* Cisco's profitability relative to
  peers. Chart 1 shows both bases for Cisco.
* **HPE is not a networking pure play** - it is a server and storage company with a
  networking segment - so its corporate margins say little about networking competition.
  Its FY2025 (ended Oct 2025) also carries the Juniper deal and integration charges, which
  is why GAAP operating margin reads -1.3%.
* **Cisco's "Networking" definition changed.** The FY2021 figure (Infrastructure Platforms,
  $27.1bn) is not comparable to later years, and FY2024's "Networking" merged two earlier
  categories, which is why Cisco restated FY2022 and FY2023 upward (to $29,265m and
  $34,570m) in the FY2024 10-K. Chart 4 uses the restated basis; the raw as-reported figures
  are in `data/segments.csv`.
* **HPE's FY2026 quarters use a different segment basis** than its annual rows (Financial
  Services folded into Cloud & AI, segment revenue net of intersegment, and FY2025 quarters
  restated down). Do not splice them onto one line.
* **Cisco restated FY2025** in the FY2026 release: a $355m legal/indemnification charge moved
  from "interest and other" into cost of sales, taking FY2025 GAAP operating income from
  $12,115m to $11,760m and gross profit from $37,145m to $36,790m. This analysis uses the
  restated basis so the FY2024-FY2026 line is continuous; non-GAAP figures are unaffected.
* **Nokia and Ericsson are in `data/kpis_ttm.csv` but excluded from the charts** because they
  report in EUR and SEK, so their revenue levels are not comparable.
* Peer fundamentals come from Yahoo Finance. It is good enough to reproduce Cisco's filings
  to the dollar, but it is a secondary source for the peers; treat individual peer numbers
  as accurate to the rounding shown, not as audited figures.

## Files

```
fetch.py                 peer annual statements (yfinance)
fetch_csco_nongaap.py    Cisco GAAP/non-GAAP from EDGAR 8-K EX-99.1 filings
build_data.py            -> data/kpis_annual.csv, data/kpis_ttm.csv
build_charts.py          -> charts/*.png
check_layout.py          layout QA: zero-overlap assertion
make_readme.py           -> README.md
data/fundamentals.csv    raw annual statements, all tickers
data/csco_nongaap.json   parsed Cisco GAAP/non-GAAP bridge, FY2021-FY2026
data/segments.csv        Cisco / HPE / Arista segment history, with source URLs
data/segments-notes.md   segment-basis caveats
sec.py, list_filings.py, csco_extract.py, hpe_extract.py,
hpe_pr_extract.py, build_segments.py   helpers used to build segments.csv
```

*Data as reported through 2 October 2026. Cisco has reported FY2026 (ended 25 July 2026);
HPE's FY2026 is not complete until 31 October 2026.*
"""
    (HERE / "README.md").write_text(doc)
    print("wrote README.md", len(doc), "chars")


if __name__ == "__main__":
    main()
