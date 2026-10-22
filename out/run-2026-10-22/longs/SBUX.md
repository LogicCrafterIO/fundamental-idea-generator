Ticker: SBUX

[news: nasdaq feed unavailable when this note was built (RuntimeError: GET failed after 3 attempts: https://api.nasdaq.com/api/news/topic/articlebysymbol?q=SBUX|stocks&offset=0&limit=15) -- the reasons rest on the feeds that answered]

Description
Coffee chain running company-operated and licensed stores in North America and abroad, plus packaged coffee sold through grocery.

Catalyst
2026-10-29 (Thursday, after the close), 7 days out -- from the earnings calendar, consensus EPS 0.71.
Q4 must show a third straight quarter of margin expansion and positive US traffic, or the 38x multiple has nothing behind it.

Reasons
1) Profit, not sales, is the engine: Q3 operating income rose 33.9% to 1.2B while revenue fell 1.4% to 9.32B, because China now runs licensed [partner-operated] and its sales left the top line.
   Source: [S3] Nasdaq company financials https://www.nasdaq.com/market-activity/stocks/sbux/financials
   Source: [S19] investor.starbucks.com (2026-06-28) https://investor.starbucks.com/news/financial-releases/news-details/2026/Starbucks-Reports-Q3-Fiscal-Year-2026-Results/default.aspx
2) US comparable sales rose 7.9% on both transactions and ticket, North America company-operated comps 8.1%, while US coffee shop visits grew 4.1% in H1 2026 against dining traffic down 0.4%.
   Source: [S13] s203.q4cdn.com https://s203.q4cdn.com/326826266/files/doc_financials/2026/q3/Q3-FY26-Earnings-at-a-Glance.pdf
   Source: [S8] thesischeck.io (2026-09-29) https://thesischeck.io/teardown/sbux-traffic-margin-turnaround-2026-09
   Source: [S22] placer.ai (2026-07-16) https://www.placer.ai/anchor/articles/placer-top-5-cities-for-coffee-lovers
3) Industry profit is forecast to fall on soaring operating costs and Starbucks still flags coffee and tariffs, yet gross profit rose 6.5% to 2.3B — store efficiency is absorbing it.
   Source: [S24] ibisworld.com (2026-06-01) https://www.ibisworld.com/united-states/industry/coffee-snack-shops/1973/
   Source: [S8] thesischeck.io (2026-09-29) https://thesischeck.io/teardown/sbux-traffic-margin-turnaround-2026-09
   Source: [S3] Nasdaq company financials https://www.nasdaq.com/market-activity/stocks/sbux/financials

Watch
- US comparable sales: confirm at or above Q3's 7.9% with transactions positive; breaks if traffic turns negative.
- Operating margin: confirm a third straight quarter of expansion; breaks if gross margin contracts on coffee and tariff costs.
- FY27 guidance: confirm above FY26's 2.61 consensus; breaks if the initial range is flat or below.
- North America revenue: confirm growth; breaks if the consolidated 1.4% year-over-year decline widens.

Quants
Price: 99.08
Market Cap: 112.95B
Fwd PE: 38.0 (current FY consensus)
P/S: 2.9
EPS Trends: slightly up over the last 7 days
EPS Revisions: all up, with 4 up and 0 down over last 30 days
EPS increased year over year, 0.5 -> 0.85

Structuring
Long	CALL	19-Feb-27	$ 105.00	10	$ 99.08	100	$ 4.50	$ -	$ -	$ -	$ 4,500.00
Short	CALL	20-Nov-26	$ 105.00	4	$ 99.08	100	$ 1.48	$ -	$ -	$ -	$ (592.00)
Targets the 2027-01-29 report, with the long leg expiring 2027-02-19, which gives the thesis time to show up.
The November 105 short caps the payoff at 105 exactly as the print lands, so $4.5 of premium buys about $6 of room. The credit ratio is 0.0%, below the floor — there is nothing sold against the long to soften a miss.

Evidence
End-market research, sampled 3 times because the evidence is qualitative: 0 of 3 sampled run(s) confirmed, 3 contradicted.

---
Lint: score 85/100, 0 error(s), 3 warning(s), description 18 words, catalyst 22 words, reasons [32, 30, 29]
Grounding: all 13 figures in the prose appear in the evidence.
  [warn ] Reason 2: no causal link (if/because/leads to); reads as an assertion (reason_no_mechanism)
  [warn ] Reason 3: no causal link (if/because/leads to); reads as an assertion (reason_no_mechanism)
  [warn ] Reasons: intangibles stepped +65% in 2025-09-30, which usually means a deal closed in that period, so reported growth there is bought rather than organic -- name the acquisition and what it contributes, or argue from a line it cannot flatter (reason_deal_unattributed)
