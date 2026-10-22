"""Render the CSCO-vs-peers KPI charts.

Four figures:
  01_csco_kpi_dashboard.png   Cisco alone, FY2021-FY2026, GAAP vs non-GAAP
  02_peer_comparison.png      Small multiples: Cisco vs Arista/HPE/Palo Alto/Fortinet
  03_latest_ttm_snapshot.png  Period-aligned snapshot, TTM through Jun/Jul 2026
  04_networking_segment.png   Like-for-like: networking revenue only

Reads only the CSVs written by build_data.py, so it needs neither yfinance nor the
network. Layout is done with explicit margins rather than constrained_layout, so
the header and footnote sit at fixed positions and cannot collide with the axes.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

HERE = Path(__file__).resolve().parent
DATA, OUT = HERE / "data", HERE / "charts"
OUT.mkdir(exist_ok=True)

CSCO = "#0b5cad"
PEERS = {"ANET": "#e8710a", "HPE": "#019c7a", "PANW": "#7b4dbb", "FTNT": "#c8102e"}
ORDER = ["CSCO", "ANET", "HPE", "PANW", "FTNT"]
GREY = "#8a8f98"
INK = "#20242b"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": "#c9ced6",
    "axes.labelcolor": INK,
    "text.color": INK,
    "axes.titlesize": 11.5,
    "axes.titleweight": "bold",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})

ann = pd.read_csv(DATA / "kpis_annual.csv")
ttm = pd.read_csv(DATA / "kpis_ttm.csv")
seg = pd.read_csv(DATA / "segments.csv")

# Verified in Cisco's FY2024 10-K revenue note: the current "Networking" definition,
# restated back through FY2022. The as-reported series is not continuous (see README).
CSCO_NET = {2022: 29265.0, 2023: 34570.0, 2024: 29229.0, 2025: 28304.0, 2026: 34668.0}
# HPE Networking, restated basis: FY25 Q4 plus FY26 Q1-Q3 = four quarters to 31-Jul-2026
HPE_NET_TTM = 2722 + 2706 + 2690 + 2893


def frame(fig, title, subtitle, footnote, top=0.855, bottom=0.105,
          left=0.052, right=0.957, hspace=0.42, wspace=0.30):
    """Fixed-margin canvas: header at the top, source note along the bottom."""
    fig.subplots_adjust(top=top, bottom=bottom, left=left, right=right,
                        hspace=hspace, wspace=wspace)
    fig.text(0.008, 0.985, title, fontsize=16, fontweight="bold", va="top", ha="left")
    fig.text(0.008, 0.945, subtitle, fontsize=9.2, color=GREY, va="top", ha="left")
    fig.text(0.008, 0.012, footnote, fontsize=7.2, color=GREY, va="bottom", ha="left")


def arrays(df):
    """Numeric column -> numpy array, so no pandas object ever reaches matplotlib."""
    num = df.select_dtypes(include=[np.number])
    return {k: num[k].to_numpy(dtype=float) for k in num.columns}


def tidy(ax, grid="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis=grid, color="#e8ebef", lw=0.9, zorder=0)
    ax.set_axisbelow(True)
    if grid == "x":
        ax.grid(axis="y", visible=False)


def twin(ax):
    """A right-hand axis that inherits the clean styling."""
    a = ax.twinx()
    a.spines["top"].set_visible(False)
    a.spines["right"].set_color("#c9ced6")
    a.grid(False)
    return a


def money(ax, suffix="B"):
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "${:,.0f}{}".format(v, suffix)))


def pct(ax):
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "{:.0f}%".format(v)))


def series(ticker, col, fy_min=None):
    d = ann[ann.ticker == ticker].sort_values("fy")
    if fy_min:
        d = d[d.fy >= fy_min]
    return d.fy.to_numpy(dtype=float), d[col].to_numpy(dtype=float)


# --------------------------------------------------------------------- figure 1

def dashboard():
    c = ann[ann.ticker == "CSCO"].sort_values("fy")
    r = arrays(c)
    fy = r["fy"]
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 9.0))
    frame(
        fig,
        "Cisco (CSCO) — key financial KPIs, fiscal 2021-2026",
        "Fiscal years end late July.  FY27 guidance: revenue $72.2-73.4B (+14-16%), non-GAAP EPS $5.05-5.11.",
        "Source: Cisco quarterly and annual earnings releases (SEC 8-K EX-99.1 / 10-K), FY2021-FY2026.  "
        "Non-GAAP figures are Cisco's own published GAAP-to-non-GAAP bridge, read from each year's Q4 release.\n"
        "Charts: csco-peer-kpis/build_charts.py",
    )

    # --- revenue + growth
    ax = axes[0][0]
    ax.bar(fy, r["revenue"] / 1000, color=CSCO, width=0.62, zorder=3)
    for x, v in zip(fy, r["revenue"] / 1000):
        ax.text(x, v + 1.2, "{:.1f}".format(v), ha="center", fontsize=8.6, color=INK)
    ax.set_title("Revenue ($B, bars) and growth (line)")
    ax.set_ylim(0, 80)
    money(ax)
    tidy(ax)
    a = twin(ax)
    g = r["rev_growth"]
    a.plot(fy[1:], g[1:], color="#d1495b", marker="o", ms=4.6, lw=1.9, zorder=4)
    for x, v in zip(fy[1:], g[1:]):
        a.annotate("{:+.1f}%".format(v), (x, v), textcoords="offset points", xytext=(0, 9),
                   ha="center", fontsize=8, color="#d1495b")
    a.set_ylim(-12, 30)
    a.set_yticks([-10, -5, 0, 5, 10, 15])
    pct(a)
    a.text(2023, 26.5, "YoY %", color="#d1495b", fontsize=8.6, ha="center", fontweight="bold")

    # --- gross margin
    ax = axes[0][1]
    ax.plot(fy, r["gross_margin"], color=CSCO, marker="o", ms=5, lw=2.2, label="GAAP", zorder=4)
    ax.plot(fy, r["non_gaap_gross_margin_pct"], color="#7fb0e0", marker="s", ms=4.4, lw=2,
            ls="--", label="non-GAAP", zorder=4)
    ax.set_title("Gross margin")
    ax.set_ylim(56, 72)
    ax.set_xlim(2020.6, 2026.4)
    ax.set_yticks([58, 60, 62, 64, 66, 68, 70])
    pct(ax)
    tidy(ax)
    ax.legend(frameon=False, fontsize=8.6, loc="lower left")
    ax.annotate("non-GAAP slips 180bp in FY26\nas AI hardware mixes in",
                (2020.7, 71.7), fontsize=8, color=GREY, va="top", ha="left")

    # --- operating margin
    ax = axes[0][2]
    ax.fill_between(fy, r["op_margin_gaap"], r["op_margin_non_gaap"], color=CSCO, alpha=0.08)
    ax.plot(fy, r["op_margin_non_gaap"], color=CSCO, marker="o", ms=5, lw=2.4,
            label="non-GAAP", zorder=4)
    ax.plot(fy, r["op_margin_gaap"], color="#9aa4b0", marker="o", ms=4.6, lw=2.1,
            ls="--", label="GAAP", zorder=4)
    ax.set_title("Operating margin")
    ax.set_ylim(15, 41)
    ax.set_xlim(2020.6, 2026.4)
    ax.set_yticks([15, 20, 25, 30, 35, 40])
    pct(ax)
    tidy(ax)
    ax.legend(frameon=False, fontsize=8.6, loc="lower left")
    ax.annotate("~10.5pt gap = Splunk amortisation,\nrestructuring and stock comp",
                (2023.4, 28.4), fontsize=8, color=GREY, ha="center")
    ax.annotate("{:.1f}%".format(r["op_margin_non_gaap"][-1]),
                (2025.9, r["op_margin_non_gaap"][-1]), textcoords="offset points",
                xytext=(-2, 11), ha="right", fontsize=8.8, color=CSCO, fontweight="bold")

    # --- net income + EPS
    ax = axes[1][0]
    ax.bar(fy, r["net_income"] / 1000, color="#c3d4e8", width=0.62, zorder=3)
    ax.set_title("Net income ($B, bars) and GAAP EPS ($, line)")
    ax.set_ylim(0, 19.5)
    money(ax)
    tidy(ax)
    for x, v in zip(fy, r["net_income"] / 1000):
        ax.text(x, v - 1.6, "{:.1f}".format(v), ha="center", fontsize=8.6, color="#3d4a5a",
                zorder=5)
    a = twin(ax)
    a.plot(fy, r["eps_diluted"], color=CSCO, marker="o", ms=4.8, lw=2.2, zorder=6)
    a.set_ylim(0, 5.4)
    a.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "${:.1f}".format(v)))
    for x, v in zip(fy, r["eps_diluted"]):
        a.annotate("${:.2f}".format(v), (x, v), textcoords="offset points", xytext=(0, 9),
                   ha="center", fontsize=8, color=CSCO)
    a.text(2021, 4.95, "GAAP EPS", color=CSCO, fontsize=8.6, ha="center", fontweight="bold")

    # --- free cash flow
    ax = axes[1][1]
    ax.bar(fy, r["fcf"] / 1000, color="#8fb8a8", width=0.62, zorder=3)
    for x, v, m in zip(fy, r["fcf"] / 1000, r["fcf_margin"]):
        ax.text(x, v + 0.35, "{:.1f}\n{:.0f}%".format(v, m), ha="center", fontsize=8, color=INK)
    ax.set_title("Free cash flow ($B, bars) and FCF margin")
    ax.set_ylim(0, 24)
    money(ax)
    tidy(ax)
    ax.axhline(r["fcf"].mean() / 1000, color=GREY, ls=":", lw=1.3, zorder=2)
    ax.text(2020.85, 22.6, "6-yr average ${:.1f}B".format(r["fcf"].mean() / 1000),
            fontsize=8, color=GREY, va="center")

    # --- R&D
    ax = axes[1][2]
    ax.bar(fy, r["rnd"] / 1000, color="#b7a6cf", width=0.62, zorder=3)
    ax.set_title("R&D expense ($B, bars) and % of revenue (line)")
    ax.set_ylim(0, 12)
    money(ax)
    tidy(ax)
    for x, v in zip(fy, r["rnd"] / 1000):
        ax.text(x, v + 0.2, "{:.1f}".format(v), ha="center", fontsize=8.4, color="#5c6672")
    a = twin(ax)
    a.plot(fy, r["rnd_pct"], color="#6a4c93", marker="o", ms=4.8, lw=2.1, zorder=4)
    a.set_ylim(10, 20)
    a.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "{:.0f}%".format(v)))
    for x, v in zip(fy, r["rnd_pct"]):
        a.annotate("{:.1f}%".format(v), (x, v), textcoords="offset points", xytext=(0, 7),
                   ha="center", fontsize=8, color="#6a4c93")
    a.text(2021, 19.3, "% of revenue", color="#6a4c93", fontsize=8.6, ha="center",
           fontweight="bold")

    fig.savefig(OUT / "01_csco_kpi_dashboard.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------- figure 2

def peer_panels():
    fy_min = 2023
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.8))
    frame(
        fig,
        "Cisco vs networking / security peers — fiscal 2023 to 2026",
        "Each company on its own fiscal year (CSCO and PANW end July, HPE October, ANET and FTNT December).",
        "Peer data: Yahoo Finance annual statements via yfinance (validated against Cisco's FY2026 press release "
        "to the dollar), FY2023-FY2026.\nGAAP basis throughout: Cisco's own GAAP/non-GAAP gap is ~10.5pt versus "
        "roughly 1-6pt for these peers, so this view understates Cisco's cash profitability relative to them.",
        top=0.845,
    )

    panels = [
        ("rev_growth", "Revenue growth (YoY)", (-14, 44)),
        ("gross_margin", "Gross margin", (24, 88)),
        ("op_margin_gaap", "Operating margin (GAAP)", (-8, 50)),
        ("fcf_margin", "Free cash flow margin", (0, 62)),
        ("rnd_pct", "R&D as % of revenue", (4, 27)),
    ]
    handles = None
    for ax, (col, title, ylim) in zip(axes.ravel(), panels):
        for t in ORDER:
            x, y = series(t, col, fy_min)
            keep = ~np.isnan(y)
            x, y = x[keep], y[keep]
            if not len(x):
                continue
            ax.plot(x, y, marker="o", ms=4.2, lw=2.9 if t == "CSCO" else 1.7,
                    color=CSCO if t == "CSCO" else PEERS[t],
                    zorder=5 if t == "CSCO" else 3, label=t)
            if t == "CSCO":
                for xx, yy in zip(x, y):
                    ax.annotate("{:.1f}".format(yy), (xx, yy), textcoords="offset points",
                                xytext=(0, 8), ha="center", fontsize=7.8, color=CSCO,
                                fontweight="bold")
        if handles is None:
            handles = ax.get_legend_handles_labels()[0]
        ax.set_title(title)
        ax.set_ylim(*ylim)
        ax.set_xlim(2022.7, 2026.55)
        ax.set_xticks([2023, 2024, 2025, 2026])
        pct(ax)
        tidy(ax)

    ax = axes[1][2]
    for t in ORDER:
        x, y = series(t, "revenue", fy_min)
        if not len(x):
            continue
        idx = 100 * y / y[0]
        col = CSCO if t == "CSCO" else PEERS[t]
        ax.plot(x, idx, marker="o", ms=4.2, lw=2.9 if t == "CSCO" else 1.7, color=col,
                zorder=5 if t == "CSCO" else 3, label=t)
        ax.annotate("{:.0f}".format(idx[-1]), (x[-1], idx[-1]), textcoords="offset points",
                    xytext=(7, -3), fontsize=8.2, color=col)
    ax.set_title("Revenue indexed to FY2023 = 100")
    ax.set_ylim(60, 215)
    ax.set_xlim(2022.75, 2026.95)
    ax.set_xticks([2023, 2024, 2025, 2026])
    tidy(ax)

    fig.legend(handles, ORDER, loc="upper left", bbox_to_anchor=(0.008, 0.918),
               ncol=5, frameon=False, fontsize=9.5)
    fig.savefig(OUT / "02_peer_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------- figure 3

def snapshot():
    d = ttm[(ttm.currency == "USD") & ttm.ticker.isin(ORDER)]
    d = d.set_index("ticker").loc[ORDER].reset_index()
    short = {"CSCO": "Cisco", "ANET": "Arista Networks", "HPE": "HPE",
             "PANW": "Palo Alto", "FTNT": "Fortinet"}
    names = [short[t] for t in d.ticker]
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.6))
    frame(
        fig,
        "Latest twelve months, period-aligned — all windows end Jun-Jul 2026",
        "Cisco has just closed FY2026 while Arista and Fortinet are mid-year, so fiscal years are not comparable. "
        "Everything here is TTM through each company's last reported quarter.",
        "Source: Yahoo Finance quarterly statements via yfinance; Cisco's TTM reconciles to its FY2026 as-reported "
        "figures.  Nokia and Ericsson excluded (they report in EUR and SEK).\n"
        "Growth is the most recent reported quarter versus the same quarter a year earlier.",
        left=0.075, wspace=0.42,
    )

    specs = [
        ("revenue", "Revenue ($B, TTM)", 1 / 1000, lambda v: "{:.1f}".format(v), False),
        ("rev_growth_q", "Revenue growth (latest quarter, YoY)", 1, lambda v: "{:+.1f}%".format(v), True),
        ("gross_margin", "Gross margin (TTM)", 1, lambda v: "{:.1f}%".format(v), True),
        ("op_margin_gaap", "Operating margin, GAAP (TTM)", 1, lambda v: "{:.1f}%".format(v), True),
        ("fcf_margin", "Free cash flow margin (TTM)", 1, lambda v: "{:.1f}%".format(v), True),
        ("rnd_pct", "R&D as % of revenue (TTM)", 1, lambda v: "{:.1f}%".format(v), True),
    ]
    ypos = list(range(len(names)))[::-1]
    for ax, (col, title, scale, fmt, as_pct) in zip(axes.ravel(), specs):
        vals = d[col].to_numpy(dtype=float) * scale
        colors = [CSCO if t == "CSCO" else "#b9bec6" for t in d.ticker]
        ax.barh(ypos, vals, color=colors, height=0.62, zorder=3)
        ax.set_yticks(ypos)
        ax.set_yticklabels(names, fontsize=9.2)
        ax.set_title(title)
        for yy, v in zip(ypos, vals):
            ax.text(v + vals.max() * 0.025, yy, fmt(v), va="center", ha="left",
                    fontsize=8.9, color=INK)
        ax.set_xlim(0, vals.max() * 1.28)
        if as_pct:
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: "{:.0f}%".format(v)))
        tidy(ax, grid="x")

    fig.savefig(OUT / "03_latest_ttm_snapshot.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------- figure 4

def networking():
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.9),
                             gridspec_kw={"width_ratios": [1.75, 1]})
    frame(
        fig,
        "The like-for-like cut: networking revenue only",
        "Cisco's total revenue is only ~72% networking product. Its series here is on the current \"Networking\" "
        "definition, restated back to FY2022 in the FY2024 10-K.",
        "Sources: Cisco FY2024 10-K revenue note and FY2026 Q4 press release; HPE Q4-FY25 and Q1-Q3 FY26 earnings "
        "releases (shown as reported, see note); Arista 10-Ks.\n"
        "HPE's Networking segment is broader than Cisco's Networking product category, which excludes attached "
        "services. HPE FY25 includes ~1 month of Juniper (deal closed 2 Jul 2025); the TTM bar uses the "
        "restated, net-of-intersegment basis.",
        top=0.80, bottom=0.155, right=0.965, wspace=0.22,
    )

    ax = axes[0]
    cx = np.array(sorted(CSCO_NET), dtype=float)
    cy = np.array([CSCO_NET[k] for k in sorted(CSCO_NET)], dtype=float) / 1000
    ax.plot(cx, cy, color=CSCO, marker="o", ms=7, lw=3.2, label="Cisco Networking", zorder=5)
    for x, v in zip(cx, cy):
        ax.annotate("{:.1f}".format(v), (x, v), textcoords="offset points", xytext=(0, 11),
                    ha="center", fontsize=9, color=CSCO, fontweight="bold")

    # annual rows only -- "FY2026 Q1" also starts with "FY20", so match FYnnnn exactly
    hp = seg[(seg.ticker == "HPE") & seg.fy_label.str.match(r"^FY\d{4}$")]
    hx = hp.fy_end.str[:4].astype(int).to_numpy(dtype=float)
    hy = hp.segment_revenue_musd.to_numpy(dtype=float) / 1000
    ax.plot(hx, hy, color=PEERS["HPE"], marker="s", ms=6, lw=2.6,
            label="HPE Networking (Intelligent Edge)", zorder=4)
    for x, v in zip(hx, hy):
        ax.annotate("{:.1f}".format(v), (x, v), textcoords="offset points", xytext=(0, -16),
                    ha="center", fontsize=8.6, color=PEERS["HPE"])

    an = seg[seg.ticker == "ANET"]
    axx = an.fy_end.str[:4].astype(int).to_numpy(dtype=float)
    ay = an.segment_revenue_musd.to_numpy(dtype=float) / 1000
    ax.plot(axx, ay, color=PEERS["ANET"], marker="^", ms=6.5, lw=2.6,
            label="Arista Networks (total company)", zorder=4)
    for x, v in zip(axx, ay):
        ax.annotate("{:.1f}".format(v), (x, v), textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=8.6, color=PEERS["ANET"])

    ax.set_title("Annual networking revenue ($B) — as reported, fiscal years differ")
    ax.set_ylim(0, 41)
    ax.set_xlim(2020.6, 2026.6)
    ax.set_xticks(range(2021, 2027))
    money(ax)
    tidy(ax)
    ax.annotate("HPE FY25 contains ~1 month of Juniper\n(deal closed 2 Jul 2025)", (2020.8, 15.5),
                fontsize=8.2, color=PEERS["HPE"])
    ax.annotate("Cisco FY23 was the post-COVID backlog peak;\nnetworking then fell 15% in FY24",
                (2023, 34.57), textcoords="offset points", xytext=(-8, 20), fontsize=8.2,
                color=GREY, ha="right")

    ax = axes[1]
    labels = ["Cisco\nNetworking\n(FY26)", "HPE\nNetworking\n(TTM Jul-26)",
              "Arista\n(total,\nTTM Jun-26)"]
    vals = [34668 / 1000, HPE_NET_TTM / 1000,
            float(ttm.loc[ttm.ticker == "ANET", "revenue"].iloc[0]) / 1000]
    colors = [CSCO, PEERS["HPE"], PEERS["ANET"]]
    bars = ax.bar(labels, vals, color=colors, width=0.6, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.9, "${:.1f}B".format(v), ha="center",
                fontsize=11.5, fontweight="bold", color=INK)
    ax.set_title("Latest twelve months, aligned to Jun-Jul 2026 ($B)")
    ax.set_ylim(0, 45)
    money(ax)
    tidy(ax)
    ax.annotate("Cisco's networking franchise is still ~3x its\nnearest pure-play rival — but Arista grew 38%\n"
                "last quarter against Cisco networking's 22%.",
                (0.03, 0.97), xycoords="axes fraction", va="top", fontsize=8.6, color=GREY)

    fig.legend(axes[0].get_legend_handles_labels()[0],
               ["Cisco Networking", "HPE Networking (Intelligent Edge)",
                "Arista Networks (total company)"],
               loc="upper left", bbox_to_anchor=(0.008, 0.895), ncol=3, frameon=False,
               fontsize=9.5)
    fig.savefig(OUT / "04_networking_segment.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    dashboard()
    peer_panels()
    snapshot()
    networking()
    print("wrote:")
    for p in sorted(OUT.glob("*.png")):
        print("  ", p)
