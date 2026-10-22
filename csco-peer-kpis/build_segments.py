"""Build data/segments.csv from the figures verified directly against SEC filings."""
from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent

CSCO = "https://www.sec.gov/Archives/edgar/data/858877"
HPE = "https://www.sec.gov/Archives/edgar/data/1645590"
ANET = "https://www.sec.gov/Archives/edgar/data/1596532"

# company, ticker, segment, fy_label, fy_end, revenue_musd, op_income_musd, source_url
ROWS = [
    # ---------------- Cisco: main networking / product category, as reported each FY ----------
    ("Cisco", "CSCO", "Networking (as reported FY2021: Infrastructure Platforms)",
     "FY2021", "2021-07-31", "27109", "",
     f"{CSCO}/000119312521250360/d198426dex991.htm"),
    ("Cisco", "CSCO", "Networking (as reported FY2022: Secure, Agile Networks)",
     "FY2022", "2022-07-30", "23829", "",
     f"{CSCO}/000119312522223250/d391322dex991.htm"),
    ("Cisco", "CSCO", "Networking (as reported FY2023: Secure, Agile Networks)",
     "FY2023", "2023-07-29", "29105", "",
     f"{CSCO}/000119312523214316/d511414dex991.htm"),
    ("Cisco", "CSCO", "Networking",
     "FY2024", "2024-07-27", "29229", "",
     f"{CSCO}/000119312524200636/d878533dex991.htm"),
    ("Cisco", "CSCO", "Networking",
     "FY2025", "2025-07-26", "28304", "",
     f"{CSCO}/000119312525179820/d901470dex991.htm"),
    ("Cisco", "CSCO", "Networking",
     "FY2026", "2026-07-25", "34668", "",
     f"{CSCO}/000085887726000106/exhibit991pressrelease-q4f.htm"),

    # ---------------- HPE: Intelligent Edge -> Networking (total segment net revenue) ----------
    ("HPE", "HPE", "Networking (as reported FY2021: Intelligent Edge)",
     "FY2021", "2021-10-31", "3287", "500",
     f"{HPE}/000164559021000063/ex-991x10312021x8kng.htm"),
    ("HPE", "HPE", "Networking (as reported FY2022: Intelligent Edge)",
     "FY2022", "2022-10-31", "3674", "549",
     f"{HPE}/000164559022000067/ex-991x10312022x8kng.htm"),
    ("HPE", "HPE", "Networking (as reported FY2023: Intelligent Edge)",
     "FY2023", "2023-10-31", "5204", "1419",
     f"{HPE}/000164559023000105/ex-991x11282023x8k.htm"),
    ("HPE", "HPE", "Networking (as reported FY2024: Intelligent Edge)",
     "FY2024", "2024-10-31", "4532", "1115",
     f"{HPE}/000164559024000132/ex-991x1252024x8k.htm"),
    ("HPE", "HPE", "Networking (renamed from Intelligent Edge in FY2025; incl. Juniper from 2025-07-02)",
     "FY2025", "2025-10-31", "6850", "1596",
     f"{HPE}/000164559025000126/ex-991x1242025x8k.htm"),
    ("HPE", "HPE", "Networking",
     "FY2026 Q1", "2026-01-31", "2706", "640",
     f"{HPE}/000164559026000028/ex-991x392026x8k.htm"),
    ("HPE", "HPE", "Networking",
     "FY2026 Q2", "2026-04-30", "2690", "581",
     f"{HPE}/000164559026000052/ex-991x612026x8k.htm"),
    ("HPE", "HPE", "Networking",
     "FY2026 Q3", "2026-07-31", "2893", "637",
     f"{HPE}/000164559026000078/ex-991x922026x8k.htm"),

    # ---------------- Arista Networks: single operating segment --------------------------------
    ("Arista Networks", "ANET", "Total", "FY2021", "2021-12-31", "2948", "925",
     f"{ANET}/000159653222000026/anet-20211231.htm"),
    ("Arista Networks", "ANET", "Total", "FY2022", "2022-12-31", "4381", "1527",
     f"{ANET}/000159653223000016/anet-20221231.htm"),
    ("Arista Networks", "ANET", "Total", "FY2023", "2023-12-31", "5860", "2257",
     f"{ANET}/000159653224000043/anet-20231231.htm"),
    ("Arista Networks", "ANET", "Total", "FY2024", "2024-12-31", "7003", "2945",
     f"{ANET}/000159653225000028/anet-20241231.htm"),
    ("Arista Networks", "ANET", "Total", "FY2025", "2025-12-31", "9006", "3856",
     f"{ANET}/000159653226000013/anet-20251231.htm"),
]

HEADER = ["company", "ticker", "segment", "fy_label", "fy_end",
          "segment_revenue_musd", "segment_operating_income_musd", "source_url"]


def main() -> None:
    out = HERE / "data" / "segments.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(HEADER)
        w.writerows(ROWS)
    print(f"wrote {out} ({len(ROWS)} data rows)")


if __name__ == "__main__":
    main()
