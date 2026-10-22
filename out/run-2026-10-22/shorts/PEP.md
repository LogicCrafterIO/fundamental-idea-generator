Ticker: PEP

[news: nasdaq feed unavailable when this note was built (RuntimeError: GET failed after 3 attempts: https://api.nasdaq.com/api/news/topic/articlebysymbol?q=PEP|stocks&offset=0&limit=15) -- the reasons rest on the feeds that answered]

Description
Global snacks and soft-drink maker; North America food and beverage is both the profit centre and the laggard.

Catalyst
2027-02-02 (Tuesday, before the open), 103 days out -- from the earnings calendar, consensus EPS 2.24.
Q4 must show North America volumes growing and the 2.5-3.5% earnings guidance held; another cut proves the recovery slipped again.

Reasons
1) The estimate level is still falling, not stabilising: 15 of 16 analysts cut in 30 days and FY [full year] consensus EPS [earnings per share] fell 1.91% to 8.395, after the October guidance cut.
   Source: [S2] Yahoo Finance (via yfinance) (2026-10-22) https://finance.yahoo.com/quote/PEP/analysis/
   Source: [S12] openbookanalytics.com (2026-10-09) https://www.openbookanalytics.com/news/insights/pepsico-pep-stock-analysis-latest-results-earnings-share-price-2026
2) The beat streak is already in the number: the last four quarters' EPS [earnings per share] actuals total 8.41 against 8.395 consensus, so Q4 needs a beat just to hold the level.
   Source: [S3] Nasdaq company financials https://www.nasdaq.com/market-activity/stocks/pep/financials
   Source: [S4] Nasdaq earnings calendar (2027-02-02) https://www.nasdaq.com/market-activity/stocks/pep/earnings
3) At 16.05x forward earnings for 2% core earnings growth, the price assumes a North America recovery the company just pushed out, while 41% of c-store [convenience store] retailers report customers cutting spend per visit.
   Source: [S1] Yahoo Finance (via yfinance) (2026-10-22) https://finance.yahoo.com/quote/PEP/key-statistics/
   Source: [S18] investor.pepsico.com (2026-10-08) https://investor.pepsico.com/docs/pepsico-5v9wci20/media/Files/investors/q3-2026-earnings-release.pdf
   Source: [S23] cstoredecisions.com (2026-09-01) https://cstoredecisions.com/foodservice-faces-rising-labor-food-costs-as-retailers-prioritize-staffing/
   Source: [S10] streetinsider.com (2026-10-08) https://www.streetinsider.com/Reuters/PepsiCo+slashes+forecast%2C+deepens+cost+cuts+as+N.America+recovery+drags/27163141.html

Watch
- Organic revenue growth: 3.1% or better with North America positive confirms the recovery; below 3% or another North America decline breaks it.
- Full-year earnings guidance: held at 2.5-3.5% growth confirms; a second cut inside four months breaks the thesis.
- Q4 EPS against the 2.24 consensus: a beat with guidance held confirms; a miss ends the beat streak the multiple rests on.

Quants
Price: 134.7
Market Cap: 183.56B
Fwd PE: 16.1 (current FY consensus)
P/S: 1.9
EPS Trends: flat over the last 7 days
EPS Revisions: tilted lower, with 1 up and 15 down over last 30 days
EPS increased year over year, 2.29 -> 2.34

Structuring
Long	PUT	19-Mar-27	$ 130.00	7	$ 134.70	100	$ 5.81	$ -	$ -	$ -	$ 4,067.00
Short	PUT	20-Nov-26	$ 130.00	4	$ 134.70	100	$ 1.33	$ -	$ -	$ -	$ (532.00)
Targets the 2027-02-02 report, with the long leg expiring 2027-03-19, which gives the deterioration time to show up.
The short leg expires 2026-11-20, ten weeks before the print, so the position pays for its protection and collects nothing into the catalyst. At a 0.0% conservative credit ratio against a 10% floor this is a debit spread, not premium sold -- size it as a directional put and treat the 130 strike as the line where the thesis is already working.

Evidence
End-market research, sampled 3 times because the evidence is qualitative: 3 of 3 sampled run(s) confirmed.

---
Lint: score 90/100, 0 error(s), 2 warning(s), description 18 words, catalyst 20 words, reasons [34, 32, 34]
Grounding: all 15 figures in the prose appear in the evidence.
Source grounding: 2 figure(s) are in the packet but not in the source cited for them -- Reason 2: "8.41" is cited to S3, S4 but appears in S2; Reason 2: "8.395" is cited to S3, S4 but appears in S2
  [warn ] Reason 1: no causal link (if/because/leads to); reads as an assertion (reason_no_mechanism)
  [warn ] Reason 2: no causal link (if/because/leads to); reads as an assertion (reason_no_mechanism)
