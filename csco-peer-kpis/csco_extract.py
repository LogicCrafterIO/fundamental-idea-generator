"""Extract Cisco's product-category revenue table from each FY Q4 earnings press release (EX-99.1)."""
from __future__ import annotations

import re
import sec

CIK = "0000858877"
ACC = {
    "FY2021": "0001193125-21-250360",  # 8-K filed 2021-08-18
    "FY2022": "0001193125-22-223250",  # 8-K filed 2022-08-17
    "FY2023": "0001193125-23-214316",  # 8-K filed 2023-08-16
    "FY2024": "0001193125-24-200636",  # 8-K filed 2024-08-14
    "FY2025": "0001193125-25-179820",  # 8-K filed 2025-08-13
    "FY2026": "0000858877-26-000106",  # 8-K filed 2026-08-12
}

LABEL_HINTS = ("Networking", "Secure, Agile Networks", "Infrastructure Platforms", "Total Product")


def ex99(cik: str, acc: str) -> tuple[str, str]:
    cands = sec.exhibit_url(cik, acc, r"(ex.?99|exhibit99)", "8-K")
    for nm, u in cands:
        if "index" in nm.lower():
            continue
        return nm, u
    raise SystemExit(f"no EX-99.1 found for {acc}: {cands}")


def main() -> None:
    for fy, acc in ACC.items():
        nm, url = ex99(CIK, acc)
        doc = sec.get(url)
        tbls = sec.tables(doc)
        print("=" * 100)
        print(f"### {fy}  8-K {acc}  exhibit {nm}")
        print(f"    {url}")
        hits = []
        for t in tbls:
            blob = " ".join(" ".join(r) for r in t)
            if any(h.lower() in blob.lower() for h in LABEL_HINTS) and re.search(r"\d{1,3},\d{3}", blob):
                hits.append(t)
        for t in hits:
            sec.show(t)
            print("    ---")


if __name__ == "__main__":
    main()
