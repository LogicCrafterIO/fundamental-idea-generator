Ticker: PDD

[news: nasdaq feed unavailable when this note was built (RuntimeError: GET failed after 3 attempts: https://api.nasdaq.com/api/news/topic/articlebysymbol?q=PDD|stocks&offset=0&limit=15) -- the reasons rest on the feeds that answered]

Description
Chinese discount e-commerce platform Pinduoduo plus Temu, its cross-border low-price marketplace.

Catalyst
2026-11-18 (Wednesday, before the open), 27 days out -- from the earnings calendar, consensus EPS 18.84.
The first full quarter of the €3 EU parcel fee must show up as lower transaction-services margin; if it doesn't, the cost thesis is wrong.

Reasons
1) China e-commerce GMV [gross merchandise value] grew 0.9% in the June 618 festival while PDD's SG&A [selling, general and administrative costs] rose 11.4% year over year against revenue up 8.1% — spending is outrunning demand.
   Source: [S20] emarketer.com (2026-06-22) https://www.emarketer.com/content/618-slowdown-clouds-outlook-china-retailers
   Source: [S3] Nasdaq company financials https://www.nasdaq.com/market-activity/stocks/pdd/financials
2) Consensus wants EPS [earnings per share] of 18.84 on 18 November after 9.51 actual in May; two of the last three reported quarters missed by 15.8% and 41.9%.
   Source: [S4] Nasdaq earnings calendar (2026-11-18) https://www.nasdaq.com/market-activity/stocks/pdd/earnings
3) Temu has paid €3 per low-value parcel into the EU since 1 July, so the September quarter carries the fee for the first time; extra customs data from 1 November lands in Q4 guidance.
   Source: [S23] taxation-customs.ec.europa.eu (2026-07-20) https://taxation-customs.ec.europa.eu/news/guidance-and-legal-text-temporary-flat-fee-low-value-imports-which-will-apply-until-1-july-2028-2026-06-08_en
   Source: [S24] fedex.com (2026-10-06) https://www.fedex.com/content/dam/fedex/us-united-states/International/FedEx_DeMinimis_Customer_Guide_US.pdf

Watch
- Revenue against the 115.64B consensus: a miss confirms the short; a print above 115.64B breaks it.
- SG&A growth versus revenue growth: still above 8.1% confirms; below it breaks.
- Transaction services revenue (54.7B, +13% year over year in Q2): deceleration confirms the EU fee bite; reacceleration breaks it.
- Q4 guidance on the 1 November EU customs-data rule: any quantified cost confirms; 'no material impact' breaks.

Quants
Price: 78.72
Market Cap: 112.05B
Fwd PE: 1.1 (current FY consensus)
P/S: 0.2
EPS Trends: flat over the last 7 days
EPS Revisions: evenly split, with 12 up and 13 down over last 30 days
Net Income +117% quarter over quarter but -12% year over year (2026-06-30)
EPS declined year over year, 11.41 -> 9.51

Structuring
Long	PUT	19-Mar-27	$ 75.00	9	$ 78.72	100	$ 4.64	$ -	$ -	$ -	$ 4,176.00
Short	PUT	20-Nov-26	$ 75.00	3	$ 78.72	100	$ 1.77	$ -	$ -	$ -	$ (531.00)
Targets the 2027-02-17 report, with the long leg expiring 2027-03-19, which gives the deterioration time to show up.
This is a debit calendar, not a credit trade: the credit ratio sits at 0.0% against a 10% floor, so nine March puts are being financed by only three November ones. Selling more of the 20 November puts would clear the floor and pay for the wait into a print 27 days out.

Evidence
End-market research, sampled 3 times because the evidence is qualitative: 2 of 3 sampled run(s) confirmed, 1 contradicted.

---
Lint: score 90/100, 0 error(s), 2 warning(s), description 11 words, catalyst 25 words, reasons [35, 28, 34]
Grounding: all 14 figures in the prose appear in the evidence.
  [warn ] Reason 1: no causal link (if/because/leads to); reads as an assertion (reason_no_mechanism)
  [warn ] Reason 2: no causal link (if/because/leads to); reads as an assertion (reason_no_mechanism)
