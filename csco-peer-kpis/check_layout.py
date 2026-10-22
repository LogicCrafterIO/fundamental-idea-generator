"""Layout QA: render every figure and report pairs of overlapping text objects.

I cannot eyeball the PNGs from here, so this walks the artist tree, asks the
Agg renderer for each text object's window extent, and flags any pair that
actually intersects. Tick labels, legends, value labels and annotations are all
plain Text artists, so this catches label collisions without human eyes.

Run:  MPLCONFIGDIR=/tmp/mpl python3 csco-peer-kpis/check_layout.py
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.text import Text
import numpy as np

import build_charts as bc

MIN_AREA = 6.0  # square points; below this it is glyph-kern noise, not a collision
report: dict[str, list[str]] = {}


def texts(fig):
    out = []
    for ax in fig.get_axes():
        out += list(ax.texts)
        out.append(ax.title)
        out += [t for t in ax.get_xticklabels() + ax.get_yticklabels()]
        leg = ax.get_legend()
        if leg is not None:
            out += list(leg.get_texts())
    out += [t for t in fig.texts]
    return out


def check(fig, name):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    items = []
    for t in texts(fig):
        if not t.get_text().strip() or not t.get_visible():
            continue
        try:
            bb = t.get_window_extent(renderer=renderer)
        except Exception:  # noqa: BLE001
            continue
        items.append((t.get_text().strip()[:48], bb, t.get_fontsize()))

    hits = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]
            dx = min(a.x1, b.x1) - max(a.x0, b.x0)
            dy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if dx > 0 and dy > 0 and dx * dy > MIN_AREA:
                hits.append("  {:>5.0f}pt2  {!r}  <->  {!r}".format(dx * dy, items[i][0], items[j][0]))
    report[name] = hits
    print("{:<34} {} text objects, {} collisions".format(name, len(items), len(hits)))
    for h in hits[:12]:
        print(h)


_orig = matplotlib.figure.Figure.savefig


def savefig(self, fname, *a, **kw):
    check(self, str(fname).split("/")[-1])
    return _orig(self, fname, *a, **kw)


matplotlib.figure.Figure.savefig = savefig

if __name__ == "__main__":
    bc.dashboard()
    bc.peer_panels()
    bc.snapshot()
    bc.networking()
    total = sum(len(v) for v in report.values())
    print("\nTOTAL collisions:", total)
