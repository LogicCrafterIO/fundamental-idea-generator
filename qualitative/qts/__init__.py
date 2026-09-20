"""qts -- a purely qualitative theme screener.

The screen is two numbers: share price <= $100 and market cap >= $1B. Everything
else this package publishes -- what the business does, where its revenue comes
from, what is happening to its demand, its channel and its cost base, and the
themes that several tickers turn out to share -- is qualitative, sourced and
ranked on stated rubrics rather than on multiples.

Read the modules in this order to follow the pipeline:

    universe.py   the two gates, over Nasdaq's listed names
    profile.py    yfinance: the description and the two numbers
    streams.py    the exact revenue streams, grounded
    trends.py     the three parts of a business, researched one lens at a time
    themes.py     trends -> canonical themes, ranked by quantum and breadth
    writeup.py    the two outputs, rendered from stored artifacts
    analysis.py   running the batch and keeping every artifact
"""

__all__ = ["universe", "profile", "streams", "trends", "themes", "writeup", "analysis", "grounding"]
