# Reference writeup — OMF (short)

Supplied verbatim by the repo owner as a target example of the format. Do not
edit: this is the spec. See [`FORMAT.md`](FORMAT.md) for the rules distilled from
this and the ORCL note, and `fig demo` for the reproducibility check that
reconstructs its option legs from live data.

Data vintage: written from the 2026-09-18 close — 60.94 is that day's
`regularMarketPreviousClose`, which is how the quoted price was pinned to a date.

---

Ticker: OMF

Description
Nonprime consumer loan lender

Reasons
1) Nonprime consumer loans are likely to worsen as job losses increase due to AI
2) If NCO [net charge offs] go from 7% now to 10% in Feb or March earnings then it could rerate significantly to a PE of 4-5 as earnings get hit.  

Quants: 
Price: 60.94 USD
Market Cap: 7.07B
Fwd PE: 7.7
EPS trends: slightly down over the last 7 days
EPS revisions: Split equally, with 5 up and 10 down over last 30 days
Q2 reported increasing provisions and managed receivables => more loans made
Q2 reported Consumer loan Net charge-offs increasing => More losses 
Q2 EPS declined year-over-year.

Structuring
A 40% downside is possible if we target earnings in late January, allowing two quarters for the worsening consumer debt story to play out, resulting in a $36 price target.
Long	PUT	19-Feb-27	$ 57.50	14	$ 60.94	100	$ 3.20	$ -	$ -	$ -	$ 4,480.00
Short	PUT	16-Oct-26	$ 57.50	7	$ 60.94	100	$ 0.65	$ -	$ -	$ -	$ (455.00)
The credit received is very slightly above the 10% floor for credits, but I could sell 1 or 2 more to increase that. Given the time factor more puts could be sold as well, but lmk if my thinking on this is wrong.
