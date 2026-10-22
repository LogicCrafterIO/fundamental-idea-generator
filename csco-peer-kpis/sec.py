"""Small SEC fetch + HTML-table-parse toolkit (1 req/sec, declared UA, disk cache)."""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.request

UA = "fundamental-idea-generator research (contact: johncheongzhanhao@example.com)"
CACHE = "/tmp/seccache"
os.makedirs(CACHE, exist_ok=True)
_last = [0.0]


def get(url: str, force: bool = False) -> str:
    key = hashlib.sha1(url.encode()).hexdigest()
    path = os.path.join(CACHE, key + ".txt")
    meta = os.path.join(CACHE, key + ".url")
    if os.path.exists(path) and not force:
        return open(path, encoding="utf-8", errors="replace").read()
    dt = time.time() - _last[0]
    if dt < 1.05:
        time.sleep(1.05 - dt)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            import gzip

            raw = gzip.decompress(raw)
    _last[0] = time.time()
    txt = raw.decode("utf-8", errors="replace")
    open(path, "w", encoding="utf-8").write(txt)
    open(meta, "w", encoding="utf-8").write(url)
    return txt


def acc_nodash(acc: str) -> str:
    return acc.replace("-", "")


def filing_dir(cik: str, acc: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash(acc)}"


def index(cik: str, acc: str) -> dict:
    return json.loads(get(filing_dir(cik, acc) + "/index.json"))


def exhibit_url(cik: str, acc: str, pattern: str = r"ex.?99", form_hint: str = "8-K") -> list[tuple[str, str]]:
    """Return [(name, url)] of filing files whose name matches pattern."""
    idx = index(cik, acc)
    out = []
    for it in idx["directory"]["item"]:
        nm = it["name"]
        if re.search(pattern, nm, re.I) and nm.lower().endswith((".htm", ".html", ".txt")):
            out.append((nm, f"https://www.sec.gov{it['pathToFolder']}/{nm}" if "pathToFolder" in it else f"{filing_dir(cik, acc)}/{nm}"))
    return out


def strip_tags(s: str) -> str:
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"</(p|div|tr|td|th|li|h\d)>", " | ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"(\s*\|\s*)+", " | ", s)
    return s.strip()


def tables(hdoc: str) -> list[list[list[str]]]:
    """Parse HTML into list of tables; each table is list of rows of cell strings."""
    out = []
    for tm in re.finditer(r"<table\b.*?</table>", hdoc, flags=re.S | re.I):
        tbl = []
        for rm in re.finditer(r"<tr\b.*?</tr>", tm.group(0), flags=re.S | re.I):
            cells = []
            for cm in re.finditer(r"<t[hd]\b.*?</t[hd]>", rm.group(0), flags=re.S | re.I):
                cells.append(strip_tags(cm.group(0)).strip(" |").strip())
            if any(c for c in cells):
                tbl.append(cells)
        if tbl:
            out.append(tbl)
    return out


def text_lines(doc: str) -> list[str]:
    """Flatten any document (html or plain text exhibit) into lines."""
    if re.search(r"<\s*(html|table|div|p)\b", doc, re.I):
        t = strip_tags(doc)
    else:
        t = doc
    t = html.unescape(t).replace("\xa0", " ")
    lines = []
    for ln in re.split(r"\n|\|\s*\|", t):
        ln = re.sub(r"\s+", " ", ln).strip(" |").strip()
        if ln:
            lines.append(ln)
    return lines


def grep_tables(tbls, *needles, ci=True) -> list[list[list[str]]]:
    res = []
    for t in tbls:
        blob = " ".join(" ".join(r) for r in t)
        if ci:
            blob = blob.lower()
        if all((n.lower() if ci else n) in blob for n in needles):
            res.append(t)
    return res


def show(tbl) -> None:
    for r in tbl:
        print(" | ".join(r))


def show_all(tbls) -> None:
    for i, t in enumerate(tbls):
        print(f"----- table {i} ({len(t)} rows) -----")
        show(t)


if __name__ == "__main__":
    print(get(sys.argv[1]))
