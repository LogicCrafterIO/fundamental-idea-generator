"""Extract HPE segment tables (Intelligent Edge / Networking) from 10-K and 10-Q filings."""
from __future__ import annotations

import sys
import sec

CIK = "0001645590"
DOCS = {
    "FY2021 10-K": "0001645590-21-000068",
    "FY2022 10-K": "0001645590-22-000071",
    "FY2023 10-K": "0001645590-23-000117",
    "FY2024 10-K": "0001645590-24-000139",
    "FY2025 10-K": "0001645590-25-000130",
    "FY2026Q1 10-Q": "0001645590-26-000032",
    "FY2026Q2 10-Q": "0001645590-26-000055",
    "FY2026Q3 10-Q": "0001645590-26-000080",
}
PRIMARY = {
    "FY2021 10-K": "hpe-20211031.htm",
    "FY2022 10-K": "hpe-20221031.htm",
    "FY2023 10-K": "hpe-20231031.htm",
    "FY2024 10-K": "hpe-20241031.htm",
    "FY2025 10-K": "hpe-20251031.htm",
    "FY2026Q1 10-Q": "hpe-20260131.htm",
    "FY2026Q2 10-Q": "hpe-20260430.htm",
    "FY2026Q3 10-Q": "hpe-20260731.htm",
}


def main() -> None:
    which = sys.argv[1:] or list(DOCS)
    for label in which:
        acc = DOCS[label]
        url = f"{sec.filing_dir(CIK, acc)}/{PRIMARY[label]}"
        print("=" * 110)
        print(f"### {label}  {acc}\n    {url}")
        doc = sec.get(url)
        print(f"    ({len(doc):,} chars)")
        tbls = sec.tables(doc)
        for t in tbls:
            blob = " ".join(" ".join(r) for r in t).lower()
            if ("intelligent edge" in blob or "networking" in blob) and len(t) <= 40:
                sec.show(t)
                print("    ---")


if __name__ == "__main__":
    main()
