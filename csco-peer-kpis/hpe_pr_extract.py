"""Extract HPE quarterly earnings press-release segment tables (EX-99.1 / EX-99.2)."""
from __future__ import annotations

import sys
import sec

CIK = "0001645590"
PRS = {
    "FY2021 Q4": ("0001645590-21-000063", "ex-991x10312021x8kng.htm"),
    "FY2022 Q4": ("0001645590-22-000067", "ex-991x10312022x8kng.htm"),
    "FY2023 Q4": ("0001645590-23-000105", "ex-991x11282023x8k.htm"),
    "FY2024 Q4": ("0001645590-24-000132", "ex-991x1252024x8k.htm"),
    "FY2025 Q4": ("0001645590-25-000126", "ex-991x1242025x8k.htm"),
    "FY2026 Q1": ("0001645590-26-000028", "ex-991x392026x8k.htm"),
    "FY2026 Q2": ("0001645590-26-000052", "ex-991x612026x8k.htm"),
    "FY2026 Q3": ("0001645590-26-000078", "ex-991x922026x8k.htm"),
}


def main() -> None:
    which = sys.argv[1:] or list(PRS)
    for label in which:
        acc, doc = PRS[label]
        url = f"{sec.filing_dir(CIK, acc)}/{doc}"
        print("=" * 110)
        print(f"### {label}  {acc}\n    {url}")
        h = sec.get(url)
        tbls = sec.tables(h)
        for t in tbls:
            blob = " ".join(" ".join(r) for r in t).lower()
            if ("intelligent edge" in blob or "networking" in blob) and len(t) <= 30:
                sec.show(t)
                print("    ---")


if __name__ == "__main__":
    main()
