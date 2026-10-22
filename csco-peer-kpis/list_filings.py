"""List SEC filings of interest (8-K / 10-K / 10-Q) for Cisco and HPE."""
from __future__ import annotations

import json
import sys

SUBS = {
    "CSCO": "/tmp/csco_sub.json",
    "HPE": "/tmp/hpe_sub.json",
}


def main() -> None:
    want_forms = {"8-K", "10-K", "10-Q", "8-K/A", "10-K/A"}
    tick = sys.argv[1] if len(sys.argv) > 1 else "CSCO"
    since = sys.argv[2] if len(sys.argv) > 2 else "2021-01-01"
    d = json.load(open(SUBS[tick]))
    r = d["filings"]["recent"]
    rows = list(zip(r["form"], r["filingDate"], r["reportDate"], r["accessionNumber"], r["primaryDocument"], r["items"]))
    rows = [x for x in rows if x[0] in want_forms and x[1] >= since]
    rows.sort(key=lambda x: x[1])
    for form, fdate, rdate, acc, doc, items in rows:
        print(f"{fdate}  {form:6s} rpt={rdate:10s} {acc}  {doc}  {items}")


if __name__ == "__main__":
    main()
