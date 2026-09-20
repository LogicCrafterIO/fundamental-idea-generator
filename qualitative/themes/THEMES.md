# Themes

*Every theme found by the qualitative screener, ranked. Generated 2026-09-20.*

Built from **20 researched companies** (APH, BAC, BBVA, BHP, BUD, KO, MUFG, NEE, NFLX, NVO, PFE, SAN, SHEL, SONY, T, TTE, UBER, UBS, VZ, WFC) and **233 grounded trends**, which collapsed into **175 themes** (15 duplicate keys merged).

## How this file is built

**The screen.** Nasdaq's listed names, gated on share price <= $100 and market cap >= 1.0B. Those two numbers are the *only* quantitative inputs: there is no multiple, no estimate revision, no price momentum and no earnings date anywhere in this screener, and the batch a company lands in is an ordering by market cap for research coverage, not a ranking of the business.

**Trend versus theme.** A *trend* is one sourced finding about one company; a *theme* is the industry force that several trends turn out to be instances of. The per-ticker files in `../tickers/` hold trends; this file holds themes.

**Three parts of a business.** Every theme is researched through the part of the business it acts on, and the theme records which parts produced it: *Trending demand* (what customers buy), *How it's sold* (channel, pricing model, procurement, concentration) and *How it's made* (inputs, supply chain, capacity, labour, cost curve). A theme found through more than one part is the more systemic for it.

**Evidence.** Every trend carries a verbatim quote from a retrieved source, checked word-for-word against the text that was retrieved, and dated. Claims whose quote could not be found are not published — they are listed as discarded in the ticker file they came from.

**Quantum.** Each trend is rated 1-5 on three anchored scales — **size** (how much money the trend moves across the industry), **speed** (when it bites: 5 = already visible in reported numbers, 1 = beyond five years) and **impact** (what it does to that company's revenue or margin) — each with a stated basis. A theme's quantum is the mean of its members' ratings, weighted `0.40*size + 0.30*speed + 0.30*impact`, then amplified by how many researched names it reaches:

```
score = quantum * (1 + 0.10 * min(breadth - 1, 5))      # breadth = distinct tickers reached
```

Size is weighted highest because a theme that moves little money is not interesting however fast it moves. Breadth is a *factor*, capped at +50%, so that a widely-shared small theme cannot outrank a large one — five names sharing a triviality must not beat one name facing a huge force. Dispersion is printed beside the mean, because a theme rated 5 by one company and 1 by another averages to a settled-looking 3.

**Who is affected.** For each theme the tickers are split by the direction the force takes for that company: *positively affected* (tailwind), *negatively affected* (headwind), and *two-sided or unclear*. A company appears on one side only, and appears under *two-sided* when the same force reaches it both ways. Sides are drawn from the researched batch alone: a theme that names three companies is a theme found in three companies, not a claim that only three companies are exposed.

## Ranked themes

| # | Theme | Parts | Size | Speed | Impact | Quantum | Reaches | Score | Net |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Deposit and loan growth** | 1/3 | 3.8 | 4.5 | 4.5 | 4.20 | 4 | **5.46** | tailwind |
| 2 | **Oil demand decline in 2026** | 1/3 | 5.0 | 5.0 | 4.5 | 4.85 | 2 | **5.33** | headwind |
| 3 | **Commercial credit demand** | 1/3 | 4.0 | 4.5 | 3.8 | 4.08 | 4 | **5.30** | mostly tailwind |
| 4 | **Japan interest rate normalisation** | 2/3 | 4.5 | 5.0 | 4.5 | 4.65 | 2 | **5.12** | two-sided |
| 5 | **China steel demand weakness** | 1/3 | 5.0 | 5.0 | 5.0 | 5.00 | 1 | **5.00** | headwind |
| 6 | **Global games market growth** | 1/3 | 5.0 | 5.0 | 5.0 | 5.00 | 1 | **5.00** | tailwind |
| 7 | **Global LNG demand growth** | 1/3 | 5.0 | 5.0 | 5.0 | 5.00 | 1 | **5.00** | tailwind |
| 8 | **GLP-1 competitive share shift** | 1/3 | 5.0 | 5.0 | 5.0 | 5.00 | 1 | **5.00** | headwind |
| 9 | **GLP-1 obesity demand growth** | 1/3 | 5.0 | 5.0 | 5.0 | 5.00 | 1 | **5.00** | tailwind |
| 10 | **GLP-1 payer formulary churn** | 1/3 | 5.0 | 5.0 | 5.0 | 5.00 | 1 | **5.00** | unclear |
| 11 | **Wireless service price competition** | 1/3 | 5.0 | 5.0 | 5.0 | 5.00 | 1 | **5.00** | headwind |
| 12 | **AI data centre capex** | 1/3 | 4.3 | 3.7 | 4.3 | 4.13 | 3 | **4.96** | tailwind |
| 13 | **Investment banking fee rebound** | 2/3 | 4.0 | 4.3 | 4.0 | 4.10 | 3 | **4.92** | tailwind |
| 14 | **Oil and gas cash windfall** | 1/3 | 4.0 | 5.0 | 4.5 | 4.45 | 2 | **4.90** | tailwind |
| 15 | **Forex market volume growth** | 2/3 | 5.0 | 4.5 | 3.5 | 4.40 | 2 | **4.84** | tailwind |
| 16 | **Oil demand rebound in 2027** | 1/3 | 5.0 | 3.5 | 4.5 | 4.40 | 2 | **4.84** | tailwind |
| 17 | **Foundry capacity tightness and price hikes** | 1/3 | 4.5 | 5.0 | 3.5 | 4.35 | 2 | **4.79** | headwind |
| 18 | **Nonbank competition in banking** | 1/3 | 3.8 | 3.8 | 3.5 | 3.67 | 4 | **4.77** | headwind |
| 19 | **Middle East supply shock raises feedstock costs** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 2 | **4.73** | headwind |
| 20 | **Health-driven beverage reformulation** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 2 | **4.73** | tailwind |
| 21 | **Copper market balance** | 2/3 | 5.0 | 4.0 | 5.0 | 4.70 | 1 | **4.70** | unclear |
| 22 | **Beer volume decline offset by premium mix** | 1/3 | 5.0 | 5.0 | 4.0 | 4.70 | 1 | **4.70** | unclear |
| 23 | **Clean energy tax credit deadlines** | 1/3 | 5.0 | 5.0 | 4.0 | 4.70 | 1 | **4.70** | unclear |
| 24 | **Consumer tech demand flatness** | 1/3 | 5.0 | 5.0 | 4.0 | 4.70 | 1 | **4.70** | headwind |
| 25 | **Household credit demand weakness** | 1/3 | 5.0 | 5.0 | 4.0 | 4.70 | 1 | **4.70** | headwind |
| 26 | **Japan NISA asset management inflows** | 1/3 | 5.0 | 5.0 | 4.0 | 4.70 | 1 | **4.70** | tailwind |
| 27 | **M&A volume rebound** | 1/3 | 5.0 | 5.0 | 4.0 | 4.70 | 1 | **4.70** | tailwind |
| 28 | **Sales and trading revenue boom** | 1/3 | 5.0 | 5.0 | 4.0 | 4.70 | 1 | **4.70** | tailwind |
| 29 | **Solar supply chain oversupply** | 1/3 | 5.0 | 5.0 | 4.0 | 4.70 | 1 | **4.70** | tailwind |
| 30 | **SVOD market saturation** | 1/3 | 5.0 | 5.0 | 4.0 | 4.70 | 1 | **4.70** | headwind |
| 31 | **Banking technology spending cycle** | 1/3 | 3.7 | 4.7 | 3.3 | 3.87 | 3 | **4.64** | headwind |
| 32 | **Content spend inflation** | 1/3 | 4.0 | 5.0 | 5.0 | 4.60 | 1 | **4.60** | headwind |
| 33 | **Subscription streaming spend growth** | 1/3 | 4.0 | 5.0 | 5.0 | 4.60 | 1 | **4.60** | tailwind |
| 34 | **Wireless promotional intensity** | 1/3 | 4.0 | 5.0 | 5.0 | 4.60 | 1 | **4.60** | headwind |
| 35 | **Deposit competition raises funding costs** | 2/3 | 4.0 | 4.5 | 4.0 | 4.15 | 2 | **4.57** | headwind |
| 36 | **Net interest margin compression** | 1/3 | 3.0 | 4.3 | 4.3 | 3.80 | 3 | **4.56** | headwind |
| 37 | **China iron ore pricing power** | 2/3 | 5.0 | 4.0 | 4.5 | 4.55 | 1 | **4.55** | unclear |
| 38 | **Beverage packaging input inflation** | 1/3 | 3.5 | 5.0 | 4.0 | 4.10 | 2 | **4.51** | headwind |
| 39 | **Refining and chemical margin recovery** | 1/3 | 3.5 | 5.0 | 4.0 | 4.10 | 2 | **4.51** | tailwind |
| 40 | **CIB wallet sponsor migration** | 1/3 | 5.0 | 3.0 | 4.0 | 4.10 | 2 | **4.51** | unclear |
| 41 | **Consumer electronics tariff nearshoring** | 2/3 | 4.5 | 5.0 | 4.0 | 4.50 | 1 | **4.50** | unclear |
| 42 | **Equity market rally lifts AUM** | 1/3 | 4.0 | 4.3 | 3.7 | 4.00 | 2 | **4.40** | tailwind |
| 43 | **AI telecom procurement savings** | 1/3 | 5.0 | 4.0 | 4.0 | 4.40 | 1 | **4.40** | tailwind |
| 44 | **Credit card balance growth moderation** | 1/3 | 5.0 | 4.0 | 4.0 | 4.40 | 1 | **4.40** | headwind |
| 45 | **Global steel demand growth** | 1/3 | 5.0 | 4.0 | 4.0 | 4.40 | 1 | **4.40** | tailwind |
| 46 | **IRA Medicare drug price negotiation** | 1/3 | 5.0 | 4.0 | 4.0 | 4.40 | 1 | **4.40** | headwind |
| 47 | **LNG supply wave 2026-2027** | 1/3 | 5.0 | 4.0 | 4.0 | 4.40 | 1 | **4.40** | unclear |
| 48 | **Non-carbonated beverage shift** | 1/3 | 5.0 | 4.0 | 4.0 | 4.40 | 1 | **4.40** | tailwind |
| 49 | **Ride-hailing demand growth** | 1/3 | 5.0 | 3.0 | 5.0 | 4.40 | 1 | **4.40** | tailwind |
| 50 | **Streaming subscriber growth** | 1/3 | 5.0 | 3.0 | 5.0 | 4.40 | 1 | **4.40** | tailwind |
| 51 | **Wireless spectrum capacity shortfall** | 1/3 | 5.0 | 4.0 | 4.0 | 4.40 | 1 | **4.40** | headwind |
| 52 | **Agentic AI banking productivity** | 1/3 | 3.3 | 3.7 | 4.0 | 3.63 | 3 | **4.36** | tailwind |
| 53 | **Gulf energy shock metals costs** | 1/3 | 3.5 | 4.5 | 4.0 | 3.95 | 2 | **4.35** | headwind |
| 54 | **India met coal import growth** | 2/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | tailwind |
| 55 | **Oral GLP-1 competition** | 2/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | unclear |
| 56 | **Adult pneumococcal vaccine demand** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | tailwind |
| 57 | **Asian LNG demand decline** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | headwind |
| 58 | **Connector pricing upcycle** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | tailwind |
| 59 | **Connector raw material cost inflation** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | headwind |
| 60 | **Copper concentrate TC/RC collapse** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | tailwind |
| 61 | **CTV ad spend growth** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | tailwind |
| 62 | **CTV upfront decline** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | headwind |
| 63 | **Delivery platform commission pressure** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | unclear |
| 64 | **Freight broker margin compression** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | headwind |
| 65 | **Gig insurance costs decline** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | tailwind |
| 66 | **PC and console market maturity** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | headwind |
| 67 | **Recorded music streaming growth** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | tailwind |
| 68 | **Refinery throughput disruption** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | headwind |
| 69 | **Smartphone upgrade cycle extension** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | headwind |
| 70 | **US beer demand expansion** | 1/3 | 4.0 | 5.0 | 4.0 | 4.30 | 1 | **4.30** | tailwind |
| 71 | **Financial services distribution shift** | 2/3 | 3.7 | 3.7 | 3.3 | 3.57 | 3 | **4.28** | two-sided |
| 72 | **Converged connectivity demand** | 1/3 | 3.0 | 5.0 | 5.0 | 4.20 | 1 | **4.20** | tailwind |
| 73 | **Utility rate base growth** | 1/3 | 3.0 | 5.0 | 5.0 | 4.20 | 1 | **4.20** | tailwind |
| 74 | **Global beverage alcohol volume decline** | 1/3 | 4.0 | 5.0 | 3.5 | 4.15 | 1 | **4.15** | unclear |
| 75 | **Electronic component supply tightness** | 1/3 | 3.0 | 5.0 | 3.5 | 3.75 | 2 | **4.12** | headwind |
| 76 | **Online food delivery growth** | 2/3 | 5.0 | 3.0 | 4.0 | 4.10 | 1 | **4.10** | unclear |
| 77 | **Basel III capital relief** | 1/3 | 5.0 | 3.0 | 4.0 | 4.10 | 1 | **4.10** | tailwind |
| 78 | **Communications hardware component demand** | 1/3 | 5.0 | 3.0 | 4.0 | 4.10 | 1 | **4.10** | tailwind |
| 79 | **Copper demand growth** | 1/3 | 5.0 | 3.0 | 4.0 | 4.10 | 1 | **4.10** | tailwind |
| 80 | **Cross-border wealth booking shift** | 1/3 | 5.0 | 3.0 | 4.0 | 4.10 | 1 | **4.10** | unclear |
| 81 | **Enterprise telecom services growth** | 1/3 | 5.0 | 3.0 | 4.0 | 4.10 | 1 | **4.10** | tailwind |
| 82 | **Global medicine demand growth** | 1/3 | 5.0 | 3.0 | 4.0 | 4.10 | 1 | **4.10** | tailwind |
| 83 | **Japan silver economy wealth transfer** | 1/3 | 5.0 | 3.0 | 4.0 | 4.10 | 1 | **4.10** | tailwind |
| 84 | **Music fan economy expansion** | 1/3 | 5.0 | 3.0 | 4.0 | 4.10 | 1 | **4.10** | tailwind |
| 85 | **Oncology market growth** | 1/3 | 5.0 | 3.0 | 4.0 | 4.10 | 1 | **4.10** | tailwind |
| 86 | **Syndicated loan market growth** | 1/3 | 5.0 | 3.0 | 4.0 | 4.10 | 1 | **4.10** | tailwind |
| 87 | **Beverage system capacity investment** | 1/3 | 3.5 | 4.5 | 3.0 | 3.65 | 2 | **4.02** | tailwind |
| 88 | **AI rack copper-optics architecture** | 1/3 | 4.0 | 4.0 | 4.0 | 4.00 | 1 | **4.00** | tailwind |
| 89 | **Asset management fee compression** | 1/3 | 4.0 | 4.0 | 4.0 | 4.00 | 1 | **4.00** | headwind |
| 90 | **Beer wholesale channel pressure** | 1/3 | 4.0 | 5.0 | 3.0 | 4.00 | 1 | **4.00** | headwind |
| 91 | **Copper by-product credit cost relief** | 1/3 | 4.0 | 4.0 | 4.0 | 4.00 | 1 | **4.00** | tailwind |
| 92 | **Data centre construction delays** | 1/3 | 4.0 | 4.0 | 4.0 | 4.00 | 1 | **4.00** | headwind |
| 93 | **Equity capital markets rebound** | 1/3 | 4.0 | 5.0 | 3.0 | 4.00 | 1 | **4.00** | tailwind |
| 94 | **Functional beverage demand growth** | 1/3 | 4.0 | 4.0 | 4.0 | 4.00 | 1 | **4.00** | tailwind |
| 95 | **GLP-1 adherence and price sensitivity** | 1/3 | 4.0 | 4.0 | 4.0 | 4.00 | 1 | **4.00** | headwind |
| 96 | **GLP-1 expanded indications** | 1/3 | 4.0 | 4.0 | 4.0 | 4.00 | 1 | **4.00** | tailwind |
| 97 | **GLP-1 Medicare coverage expansion** | 1/3 | 4.0 | 4.0 | 4.0 | 4.00 | 1 | **4.00** | unclear |
| 98 | **Japan inbound investment growth sectors** | 1/3 | 4.0 | 4.0 | 4.0 | 4.00 | 1 | **4.00** | tailwind |
| 99 | **Oil and gas labour cost pressure** | 1/3 | 4.0 | 4.0 | 4.0 | 4.00 | 1 | **4.00** | headwind |
| 100 | **Short-form drama competition** | 1/3 | 4.0 | 5.0 | 3.0 | 4.00 | 1 | **4.00** | headwind |
| 101 | **Commercial lending standards tightening** | 1/3 | 3.0 | 4.5 | 3.5 | 3.60 | 2 | **3.96** | headwind |
| 102 | **EV charging changes forecourt economics** | 2/3 | 3.0 | 4.5 | 3.5 | 3.60 | 2 | **3.96** | unclear |
| 103 | **Carbonated soft drink per-capita decline** | 1/3 | 3.0 | 5.0 | 4.0 | 3.90 | 1 | **3.90** | headwind |
| 104 | **COVID product demand decline** | 1/3 | 3.0 | 5.0 | 4.0 | 3.90 | 1 | **3.90** | headwind |
| 105 | **Fiber buildout acceleration** | 1/3 | 3.0 | 5.0 | 4.0 | 3.90 | 1 | **3.90** | unclear |
| 106 | **LNG trading gains from volatility** | 1/3 | 3.0 | 5.0 | 4.0 | 3.90 | 1 | **3.90** | tailwind |
| 107 | **Non-COVID innovative drug growth** | 1/3 | 3.0 | 5.0 | 4.0 | 3.90 | 1 | **3.90** | tailwind |
| 108 | **Optical fiber price inflation** | 1/3 | 3.0 | 5.0 | 4.0 | 3.90 | 1 | **3.90** | headwind |
| 109 | **Streaming price increases** | 1/3 | 3.0 | 5.0 | 4.0 | 3.90 | 1 | **3.90** | tailwind |
| 110 | **Telecom ARPU rises but core prices flat** | 1/3 | 3.0 | 5.0 | 4.0 | 3.90 | 1 | **3.90** | unclear |
| 111 | **Transformer supply shortage** | 1/3 | 3.0 | 5.0 | 4.0 | 3.90 | 1 | **3.90** | headwind |
| 112 | **Utility large-load tariffs** | 1/3 | 3.0 | 5.0 | 4.0 | 3.90 | 1 | **3.90** | tailwind |
| 113 | **AI disruption in banking** | 2/3 | 3.0 | 3.0 | 3.7 | 3.20 | 3 | **3.84** | headwind |
| 114 | **Clean energy development backlog** | 2/3 | 3.5 | 4.0 | 4.0 | 3.80 | 1 | **3.80** | tailwind |
| 115 | **Rare disease drug demand growth** | 1/3 | 5.0 | 3.0 | 3.0 | 3.80 | 1 | **3.80** | tailwind |
| 116 | **Auto finance market growth** | 1/3 | 4.0 | 3.0 | 4.0 | 3.70 | 1 | **3.70** | tailwind |
| 117 | **BNPL consumer credit growth** | 1/3 | 4.0 | 4.0 | 3.0 | 3.70 | 1 | **3.70** | unclear |
| 118 | **Oncology loss-of-exclusivity risk** | 1/3 | 4.0 | 3.0 | 4.0 | 3.70 | 1 | **3.70** | headwind |
| 119 | **Streaming industry consolidation** | 1/3 | 4.0 | 3.0 | 4.0 | 3.70 | 1 | **3.70** | headwind |
| 120 | **Wireless infrastructure labour shortage** | 1/3 | 4.0 | 4.0 | 3.0 | 3.70 | 1 | **3.70** | headwind |
| 121 | **Connector supply chain nearshoring and tariffs** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 2 | **3.63** | headwind |
| 122 | **Fuel retail volume softness** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 2 | **3.63** | headwind |
| 123 | **AI backplane supplier concentration** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | tailwind |
| 124 | **Asset-light beverage franchising** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | tailwind |
| 125 | **Card interchange fee caps** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | headwind |
| 126 | **Coffee and tea commodity inflation** | 1/3 | 3.0 | 5.0 | 3.0 | 3.60 | 1 | **3.60** | headwind |
| 127 | **Commercial loan demand strength** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | tailwind |
| 128 | **Consumer credit origination rebound** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | tailwind |
| 129 | **Freight rate inflation** | 1/3 | 3.0 | 5.0 | 3.0 | 3.60 | 1 | **3.60** | headwind |
| 130 | **Insulin tender pricing pressure** | 1/3 | 3.0 | 5.0 | 3.0 | 3.60 | 1 | **3.60** | headwind |
| 131 | **Japan life insurance channel shift** | 1/3 | 3.0 | 5.0 | 3.0 | 3.60 | 1 | **3.60** | tailwind |
| 132 | **Japan ultrawealthy wealth management** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | unclear |
| 133 | **LNG contract flexibility shift** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | unclear |
| 134 | **Middle market earnings resilience** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | tailwind |
| 135 | **Oncology payer access controls** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | headwind |
| 136 | **Postpaid convergence pressures margins** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | headwind |
| 137 | **Private-label beverage competition** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | headwind |
| 138 | **QSR dispensed beverage expansion** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | tailwind |
| 139 | **Smartphone demand weakens on memory costs** | 1/3 | 3.0 | 5.0 | 3.0 | 3.60 | 1 | **3.60** | headwind |
| 140 | **Smartphone promotion intensity rises** | 1/3 | 3.0 | 5.0 | 3.0 | 3.60 | 1 | **3.60** | unclear |
| 141 | **Smartphone replacement cycles lengthen** | 1/3 | 3.0 | 5.0 | 3.0 | 3.60 | 1 | **3.60** | headwind |
| 142 | **Specialty pharmacy margin compression** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | headwind |
| 143 | **Streaming bundling return** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | unclear |
| 144 | **Streaming engagement decline** | 1/3 | 3.0 | 4.0 | 4.0 | 3.60 | 1 | **3.60** | headwind |
| 145 | **Broadband permitting reform** | 1/3 | 3.5 | 3.0 | 3.0 | 3.20 | 2 | **3.52** | tailwind |
| 146 | **SMB banking switching intent** | 1/3 | 3.0 | 3.5 | 3.0 | 3.15 | 2 | **3.47** | two-sided |
| 147 | **Automotive connector electrification demand** | 1/3 | 4.0 | 3.0 | 3.0 | 3.40 | 1 | **3.40** | tailwind |
| 148 | **Insulin access gap in LMICs** | 1/3 | 4.0 | 3.0 | 3.0 | 3.40 | 1 | **3.40** | tailwind |
| 149 | **Private 5G enterprise adoption** | 1/3 | 4.0 | 3.0 | 3.0 | 3.40 | 1 | **3.40** | tailwind |
| 150 | **Aerospace and defense connector demand** | 1/3 | 3.0 | 3.0 | 4.0 | 3.30 | 1 | **3.30** | tailwind |
| 151 | **AI infrastructure financing demand** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 1 | **3.30** | tailwind |
| 152 | **API supply chain diversification** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 1 | **3.30** | unclear |
| 153 | **Branch network strategy shift** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 1 | **3.30** | unclear |
| 154 | **CIB revenue momentum slowdown** | 1/3 | 3.0 | 3.0 | 4.0 | 3.30 | 1 | **3.30** | headwind |
| 155 | **GLP-1 manufacturing capacity expansion** | 1/3 | 3.0 | 3.0 | 4.0 | 3.30 | 1 | **3.30** | tailwind |
| 156 | **Government rideshare procurement expands** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 1 | **3.30** | tailwind |
| 157 | **Natural gas price volatility** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 1 | **3.30** | unclear |
| 158 | **Production spend decline** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 1 | **3.30** | tailwind |
| 159 | **Retail deposit acquisition costs rise** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 1 | **3.30** | headwind |
| 160 | **Smartphone OEM financing disintermediation** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 1 | **3.30** | unclear |
| 161 | **Stablecoin disruption in banking** | 1/3 | 3.0 | 3.0 | 3.0 | 3.00 | 2 | **3.30** | headwind |
| 162 | **White-label foodservice beverages** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 1 | **3.30** | tailwind |
| 163 | **Wireless retail channel control** | 1/3 | 3.0 | 4.0 | 3.0 | 3.30 | 1 | **3.30** | headwind |
| 164 | **Physical game media decline** | 1/3 | 2.0 | 5.0 | 3.0 | 3.20 | 1 | **3.20** | unclear |
| 165 | **Beer distributor portfolio diversification** | 1/3 | 3.0 | 3.0 | 3.0 | 3.00 | 1 | **3.00** | headwind |
| 166 | **Consumer electronics D2C shift** | 1/3 | 3.0 | 3.0 | 3.0 | 3.00 | 1 | **3.00** | unclear |
| 167 | **Digital freight brokerage growth** | 1/3 | 3.0 | 3.0 | 3.0 | 3.00 | 1 | **3.00** | tailwind |
| 168 | **Flanker brands become growth engines** | 1/3 | 3.0 | 3.0 | 3.0 | 3.00 | 1 | **3.00** | tailwind |
| 169 | **Harsh environment connector qualification barriers** | 1/3 | 3.0 | 3.0 | 3.0 | 3.00 | 1 | **3.00** | tailwind |
| 170 | **Industrial automation sensor connector demand** | 1/3 | 3.0 | 3.0 | 3.0 | 3.00 | 1 | **3.00** | tailwind |
| 171 | **Insulin API and biosimilar supply** | 1/3 | 3.0 | 3.0 | 3.0 | 3.00 | 1 | **3.00** | unclear |
| 172 | **Pole attachment deployment delays** | 1/3 | 3.0 | 3.0 | 3.0 | 3.00 | 1 | **3.00** | headwind |
| 173 | **Retail vertical integration** | 1/3 | 3.0 | 3.0 | 3.0 | 3.00 | 1 | **3.00** | headwind |
| 174 | **LNG buyers shift to term contracts** | 1/3 | 2.0 | 4.0 | 3.0 | 2.90 | 1 | **2.90** | tailwind |
| 175 | **Mortgage servicing cost inflation** | 1/3 | 2.0 | 4.0 | 3.0 | 2.90 | 1 | **2.90** | headwind |

`Reaches` counts the researched tickers with a trend on the theme; `Parts` is how many of the three parts of a business the theme was found through.

### 1. Deposit and loan growth

`deposit-and-loan-growth` — merged from: `us-banking-deposit-and-loan-growth`

**What it is.** Bank deposits and loans are growing, supporting net interest income.

**Found through:** Trending demand | **Revenue streams touched:** Net interest income

**Quantum.** size **3.8**, speed **4.5**, impact **4.5** → quantum **4.20** × breadth factor **1.30** = **5.46**  
(4 trends from 4 companies, 3 sources, rating dispersion 1.67; sources: trade press, industry body or named research house x3, company disclosure x1)

**Positively affected (4):**

- `+` **BAC** (Bank of America Corporation) — Deposit and loan growth expand the balance sheet and support net interest income. *(impact 4, found through Trending demand)*
- `+` **BBVA** (Banco Bilbao Vizcaya Argentaria, S.A.) — Higher loan and deposit volumes expand BBVA Mexico's net interest income base. *(impact 4, found through Trending demand, stream: Net interest income)*
- `+` **SAN** (Banco Santander, S.A.) — Customer growth expands deposits, loans, and fee income across the group. *(impact 5, found through Trending demand)*
- `+` **WFC** (Wells Fargo & Company) — Deposit and loan growth support balance sheet expansion and net interest income across the bank. *(impact 5, found through Trending demand)*

**Evidence:**

- "Domestic deposits increased for the eighth consecutive quarter and loan growth was strong." — [fdic.gov, 2026-08-25](https://www.fdic.gov/fdic-quarterly-banking-profile-second-quarter-2026.pdf) — **BAC**, trending demand *(trade press, industry body or named research house)*
- "In June 2026, bank deposits and lending in Mexico showed greater momentum, driven by time deposits and consumer credit." — [bbvaresearch.com, 2026-08-21](https://www.bbvaresearch.com/en/publicaciones/mexico-monthly-report-on-banking-and-the-financial-system-august-2026/) — **BBVA**, trending demand of Net interest income *(trade press, industry body or named research house)*
- "growing its customer base from 180 million at the end of 2025 to more than 210 million by 2028" — [santander.com, 2026-05-05](https://www.santander.com/content/dam/santander-com/en/documentos/investor-day/2026/id-2026-press-release-on-the-presentation-of-strategic-plans-and-targets-at-the-investor-day-and-the-shareholder-remuneration-policy-en.pdf) — **SAN**, trending demand *(company disclosure)*
- "Domestic deposits increased for the eighth consecutive quarter and loan growth was strong." — [fdic.gov, 2026-08-25](https://www.fdic.gov/fdic-quarterly-banking-profile-second-quarter-2026.pdf) — **WFC**, trending demand *(trade press, industry body or named research house)*

### 2. Oil demand decline in 2026

`oil-demand-decline-2026`

**What it is.** Global oil consumption is contracting in 2026 due to high prices and supply disruptions.

**Found through:** Trending demand | **Revenue streams touched:** Upstream

**Quantum.** size **5.0**, speed **5.0**, impact **4.5** → quantum **4.85** × breadth factor **1.10** = **5.33**  
(2 trends from 2 companies, 1 sources, rating dispersion 0.33; sources: trade press, industry body or named research house x2)

**Negatively affected (2):**

- `-` **SHEL** (Shell plc) — Lower oil demand pressures crude prices and Upstream revenues. *(impact 5, found through Trending demand, stream: Upstream)*
- `-` **TTE** (TotalEnergies SE) — Lower oil demand reduces E&P volumes and realized prices, pressuring TotalEnergies' upstream revenue. *(impact 4, found through Trending demand)*

**Evidence:**

- "World oil demand is forecast to decline by 2.5 mb/d in 2026" — [iea.org, 2026-09-11](https://www.iea.org/reports/oil-market-report-september-2026) — **SHEL**, trending demand of Upstream *(trade press, industry body or named research house)*
- "World oil demand is forecast to decline by 2.5 mb/d in 2026" — [iea.org, 2026-09-11](https://www.iea.org/reports/oil-market-report-september-2026) — **TTE**, trending demand *(trade press, industry body or named research house)*

### 3. Commercial credit demand

`commercial-credit-demand`

**What it is.** Demand for commercial and industrial loans from large and middle-market firms is strengthening.

**Found through:** Trending demand | **Revenue streams touched:** Corporate & Investment Banking, Net interest income

**Quantum.** size **4.0**, speed **4.5**, impact **3.8** → quantum **4.08** × breadth factor **1.30** = **5.30**  
(4 trends from 4 companies, 4 sources, rating dispersion 1.67; sources: trade press, industry body or named research house x3, vendor market-report page x1)

**Positively affected (2):**

- `+` **BAC** (Bank of America Corporation) — Stronger commercial loan demand supports loan growth and net interest income at large banks. *(impact 4, found through Trending demand)*
- `+` **UBS** (UBS Group AG) — Growing corporate credit demand supports loan balances and fee income. *(impact 3, found through Trending demand)*

**Negatively affected (1):**

- `-` **BBVA** (Banco Bilbao Vizcaya Argentaria, S.A.) — Slower loan growth limits BBVA Mexico's interest-earning asset expansion. *(impact 4, found through Trending demand, stream: Net interest income)*

**Two-sided or unclear (1):**

- `±` **SAN** (Banco Santander, S.A.) — Higher enterprise loan demand supports CIB lending volumes, but tighter standards may constrain approvals and margins. *(impact 4, found through Trending demand, stream: Corporate & Investment Banking)*

**Evidence:**

- "banks reported stronger demand for C&I loans from large and middle-market firms and basically unchanged demand for C&I loans from small firms on net." — [federalreserve.gov, 2026-08-03](https://www.federalreserve.gov/data/documents/sloos-202607.pdf) — **BAC**, trending demand *(trade press, industry body or named research house)*
- "In April 2026, the outstanding credit to the non-financial private sector continued to slow, reaching 1.3% in real annual terms" — [bbvaresearch.com, 2026-06-19](https://www.bbvaresearch.com/en/publicaciones/mexico-monthly-report-on-banking-and-the-financial-system-june-2026/) — **BBVA**, trending demand of Net interest income *(trade press, industry body or named research house)*
- "Demand for loans increased slightly" — [ecb.europa.eu, 2026-07-15](https://www.ecb.europa.eu/stats/ecb_surveys/bank_lending_survey/pdf/ecb.blssurvey2026q2~baa6b60429.en.pdf) — **SAN**, trending demand of Corporate & Investment Banking *(trade press, industry body or named research house)*
- "The Corporate Banking Market valued at $738.6 Billion in 2026 is projected to expand to $1,335.21 Billion by 2035" — [markwideresearch.com, 2026-05-01](https://markwideresearch.com/corporate-banking-market) — **UBS**, trending demand *(vendor market-report page)*

### 4. Japan interest rate normalisation

`japan-interest-rate-normalisation` — merged from: `utility-interest-rate-headwind`

**What it is.** Bank of Japan policy rate increases that lift Japanese banks' net interest income and profitability.

**Found through:** How it's sold, How it's made

**Quantum.** size **4.5**, speed **5.0**, impact **4.5** → quantum **4.65** × breadth factor **1.10** = **5.12**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.67; sources: general media x1, trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Higher rates lift net interest income across lending and deposit franchises. *(impact 5, found through How it's sold)*

**Negatively affected (1):**

- `-` **NEE** (NextEra Energy, Inc.) — Higher rates raise NEE's financing costs and pressure valuation. *(impact 4, found through How it's made)*

**Evidence:**

- "the country’s banking sector is set to continue receiving a significant earnings tailwind for the current financial year." — [internationalbanker.com, 2026-08-03](https://internationalbanker.com/banking/interest-rate-normalisation-is-driving-record-japanese-banking-profitability/) — **MUFG**, how it's sold *(general media)*
- "pushing the 10-year Treasury yield above 4.3%, creating a headwind for the group." — [gabelli.com, 2026-09-01](https://gabelli.com/research/utilities-u-s-outlook/) — **NEE**, how it's made *(trade press, industry body or named research house)*

### 5. China steel demand weakness

`china-steel-demand-weakness`

**What it is.** China's property construction slump offsetting manufacturing steel demand, weighing on iron ore.

**Found through:** Trending demand

**Quantum.** size **5.0**, speed **5.0**, impact **5.0** → quantum **5.00** × breadth factor **1.00** = **5.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **BHP** (BHP Group Limited) — China is a major iron ore buyer; weaker steel demand pressures BHP's iron ore prices. *(impact 5, found through Trending demand)*

**Evidence:**

- "China's steel demand to drop slightly in 2026 as construction slump may neutralize gains from manufacturing" — [steelorbis.com, 2026-07-28](https://www.steelorbis.com/steel-news/latest-news/chinas-steel-demand-to-drop-slightly-in-2026-as-construction-slump-may-neutralize-gains-from-manufacturing-1467349.htm) — **BHP**, trending demand *(trade press, industry body or named research house)*

### 6. Global games market growth

`global-games-market-growth`

**What it is.** Worldwide consumer spending on video games expands across platforms and regions.

**Found through:** Trending demand | **Revenue streams touched:** Game & Network Services

**Quantum.** size **5.0**, speed **5.0**, impact **5.0** → quantum **5.00** × breadth factor **1.00** = **5.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **SONY** (Sony Group Corporation) — Higher industry spending lifts Sony's PlayStation software, services, and subscription revenue. *(impact 5, found through Trending demand, stream: Game & Network Services)*

**Evidence:**

- "The global games market is forecast to generate $213.9 billion in 2026, an increase of 6.1% year over year." — [newzoo.com](https://newzoo.com/articles/executive-summary-ggmr-2026-free-edition) — **SONY**, trending demand of Game & Network Services *(trade press, industry body or named research house)*

### 7. Global LNG demand growth

`global-lng-demand-growth`

**What it is.** Worldwide LNG trade is expanding as gas demand and energy security needs rise.

**Found through:** Trending demand | **Revenue streams touched:** Integrated Gas

**Quantum.** size **5.0**, speed **5.0**, impact **5.0** → quantum **5.00** × breadth factor **1.00** = **5.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **SHEL** (Shell plc) — Growing LNG demand supports Shell's Integrated Gas volumes and long-term sales. *(impact 5, found through Trending demand, stream: Integrated Gas)*

**Evidence:**

- "The global liquefied natural gas (LNG) trade reached a record of 437 million tonnes in 2025, with a 6.3% increase" — [igu.org, 2026-07-07](https://www.igu.org/press-releases/world-lng-report-2026) — **SHEL**, trending demand of Integrated Gas *(trade press, industry body or named research house)*

### 8. GLP-1 competitive share shift

`glp1-competitive-share-shift`

**What it is.** Competition between GLP-1 leaders is shifting market share and pricing power.

**Found through:** How it's sold

**Quantum.** size **5.0**, speed **5.0**, impact **5.0** → quantum **5.00** × breadth factor **1.00** = **5.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **NVO** (Novo Nordisk A/S) — Lilly's share gains reduce Novo's pricing power and GLP-1 revenue growth. *(impact 5, found through How it's sold)*

**Evidence:**

- "Eli Lilly captured 61.8% of combined next-generation incretin revenue from the two GLP-1 leaders in Q2 2026, up from 36.0% in 2024" — [axis-intelligence.com, 2026-09-15](https://axis-intelligence.com/glp-1-market-statistics/) — **NVO**, how it's sold *(trade press, industry body or named research house)*

### 9. GLP-1 obesity demand growth

`glp1-obesity-demand-growth`

**What it is.** Rising global demand for obesity pharmacotherapy expands the market for GLP-1 medicines.

**Found through:** Trending demand

**Quantum.** size **5.0**, speed **5.0**, impact **5.0** → quantum **5.00** × breadth factor **1.00** = **5.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **NVO** (Novo Nordisk A/S) — Expanding obesity drug demand lifts Wegovy and Novo's GLP-1 franchise revenue. *(impact 5, found through Trending demand)*

**Evidence:**

- "forecast to rise to $92 billion in 2026, before reaching between $105 billion and $200 billion by 2027 and beyond" — [iqvia.com, 2026-04-01](https://www.iqvia.com/locations/emea/blogs/2026/04/the-outlook-for-obesity-from-2026-to-2030) — **NVO**, trending demand *(trade press, industry body or named research house)*

### 10. GLP-1 payer formulary churn

`glp1-payer-formulary-churn`

**What it is.** Pharmacy benefit managers frequently change GLP-1 coverage, preferred status, and exclusions, altering access.

**Found through:** How it's sold

**Quantum.** size **5.0**, speed **5.0**, impact **5.0** → quantum **5.00** × breadth factor **1.00** = **5.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **NVO** (Novo Nordisk A/S) — Formulary placement controls patient access and net pricing for Wegovy. *(impact 5, found through How it's sold)*

**Evidence:**

- "designated semaglutide (Wegovy) as the preferred GLP-1 for obesity treatment" — [pharmadossier.com, 2026-06-06](https://pharmadossier.com/blog/cvs-caremark-glp1-coverage-formulary-2026) — **NVO**, how it's sold *(trade press, industry body or named research house)*

### 11. Wireless service price competition

`wireless-service-price-competition`

**What it is.** Intensifying competition among wireless carriers constrains pricing power even as data usage grows.

**Found through:** Trending demand

**Quantum.** size **5.0**, speed **5.0**, impact **5.0** → quantum **5.00** × breadth factor **1.00** = **5.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **VZ** (Verizon Communications Inc.) — Constrains service pricing and revenue per user, pressuring Verizon's mobility and broadband service margins. *(impact 5, found through Trending demand)*

**Evidence:**

- "competition intensifying across both premium and value segments" — [script.ibisworld.com, 2026-05-01](https://script.ibisworld.com/united-states/industry/wireless-telecommunications-carriers/1267/) — **VZ**, trending demand *(trade press, industry body or named research house)*

### 12. AI data centre capex

`ai-data-centre-capex`

**What it is.** Sustained investment in AI data centres increases demand for high-speed interconnect and connector content.

**Found through:** Trending demand | **Revenue streams touched:** FPL, Global Corporate & Investment Banking

**Quantum.** size **4.3**, speed **3.7**, impact **4.3** → quantum **4.13** × breadth factor **1.20** = **4.96**  
(3 trends from 3 companies, 3 sources, rating dispersion 1.00; sources: trade press, industry body or named research house x2, vendor market-report page x1)

**Positively affected (3):**

- `+` **APH** (Amphenol Corporation) — More AI racks and interfaces per rack raise connector content and revenue in Communications Solutions. *(impact 4, found through Trending demand)*
- `+` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Financing, advisory and markets activity around data centre build-out lifts CIB revenue. *(impact 4, found through Trending demand, stream: Global Corporate & Investment Banking)*
- `+` **NEE** (NextEra Energy, Inc.) — Drives FPL capital investment and rate base growth as large loads connect. *(impact 5, found through Trending demand, stream: FPL)*

**Evidence:**

- "projected to grow from US$ 1874 million in 2025 to US$ 10670 million by 2032, at a CAGR of 28.6%" — [qyresearch.com, 2026-03-10](https://www.qyresearch.com/reports/6126665/ai-data-center-connectors) — **APH**, trending demand *(vendor market-report page)*
- "The sector is experiencing an infrastructure investment supercycle requiring up to $3 trillion by 2030." — [jll.com, 2026-01-01](https://www.jll.com/content/dam/jllcom/en/global/documents/reports/research-reports/26-research-global-data-center-outlook-new.pdf) — **MUFG**, trending demand of Global Corporate & Investment Banking *(trade press, industry body or named research house)*
- "data center and other large-load demand at its Florida subsidiary, Florida Power & Light (FPL), to 8GW by 2032" — [datacenterdynamics.com, 2026-07-28](https://www.datacenterdynamics.com/en/news/nextera-raises-data-center-forecast-to-8gw-by-2032-at-florida-subsidiary-fpl/) — **NEE**, trending demand of FPL *(trade press, industry body or named research house)*

### 13. Investment banking fee rebound

`investment-banking-fee-rebound`

**What it is.** Global investment banking fees are rising on stronger M&A, equity, and debt capital markets activity.

**Found through:** Trending demand, How it's sold | **Revenue streams touched:** Corporate & Investment Banking

**Quantum.** size **4.0**, speed **4.3**, impact **4.0** → quantum **4.10** × breadth factor **1.20** = **4.92**  
(3 trends from 3 companies, 3 sources, rating dispersion 1.00; sources: general media x2, trade press, industry body or named research house x1)

**Positively affected (3):**

- `+` **BAC** (Bank of America Corporation) — Higher industry fee pools lift investment banking fee revenue for large banks. *(impact 4, found through Trending demand)*
- `+` **SAN** (Banco Santander, S.A.) — Higher advisory and underwriting activity lifts CIB fee income. *(impact 4, found through How it's sold, stream: Corporate & Investment Banking)*
- `+` **UBS** (UBS Group AG) — Higher advisory and underwriting fees lift Investment Bank revenue. *(impact 4, found through Trending demand)*

**Evidence:**

- "Fees are up almost 20% year-on-year (YoY) to USD 48bn" — [ionanalytics.com, 2026-06-01](https://ionanalytics.com/insights/mergermarket/global-ib-fees-hit-five-year-record-despite-geopolitical-conflicts-revenue-report/) — **BAC**, trending demand *(trade press, industry body or named research house)*
- "Investment banking and capital markets advisory enter 2026 with renewed momentum after several years of uneven activity across M&A, IPOs, leveraged finance, and debt issuance." — [advisoryranking.com, 2026-01-01](https://advisoryranking.com/news/2026/01/202601288644) — **SAN**, how it's sold of Corporate & Investment Banking *(general media)*
- "Investment banking fees rise at top US banks, lift profits" — [reuters.com, 2026-04-15](https://www.reuters.com/legal/transactional/wall-street-still-betting-2026-deal-boom-middle-east-unrest-adds-caution-2026-04-15/) — **UBS**, trending demand *(general media)*

### 14. Oil and gas cash windfall

`oil-gas-cash-windfall-high-prices`

**What it is.** High oil prices generate large upstream cash flows even as investment stays disciplined.

**Found through:** How it's sold | **Revenue streams touched:** Upstream

**Quantum.** size **4.0**, speed **5.0**, impact **4.5** → quantum **4.45** × breadth factor **1.10** = **4.90**  
(2 trends from 2 companies, 2 sources, rating dispersion 1.00; sources: trade press, industry body or named research house x2)

**Positively affected (2):**

- `+` **SHEL** (Shell plc) — High oil prices lift Upstream cash flow and returns. *(impact 5, found through How it's sold, stream: Upstream)*
- `+` **TTE** (TotalEnergies SE) — Higher crude prices lift E&P revenue and refining margins, boosting TotalEnergies' cash flow. *(impact 4, found through How it's sold)*

**Evidence:**

- "global upstream sector could accumulate a cash windfall of US$495 billion this year" — [woodmac.com, 2026-07-28](https://www.woodmac.com/press-releases/wood-mackenzie-mid-year-outlook-oil-and-gas-industry-cash-rich-but-capital-cautious-as-nearly-half-a-trillion-dollar-windfall-fails-to-trigger-a-spending-surge/) — **SHEL**, how it's sold of Upstream *(trade press, industry body or named research house)*
- "marks the beginning of a prolonged period of elevated prices" — [nacsmagazine.com, 2026-06-01](https://nacsmagazine.com/issues/june-2026/what-to-expect-in-fueling-and-charging-in-the-year-ahead) — **TTE**, how it's sold *(trade press, industry body or named research house)*

### 15. Forex market volume growth

`forex-market-volume-growth`

**What it is.** Foreign exchange trading volumes grow, supporting bank trading revenue.

**Found through:** Trending demand, How it's sold | **Revenue streams touched:** Global Markets, Net trading income

**Quantum.** size **5.0**, speed **4.5**, impact **3.5** → quantum **4.40** × breadth factor **1.10** = **4.84**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.67; sources: trade press, industry body or named research house x1, general media x1)

**Positively affected (2):**

- `+` **BBVA** (Banco Bilbao Vizcaya Argentaria, S.A.) — Higher FX volumes increase client flow and trading income for BBVA's markets business. *(impact 3, found through How it's sold, stream: Net trading income)*
- `+` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Higher FX volumes lift trading and market-making revenue for Global Markets. *(impact 4, found through Trending demand, stream: Global Markets)*

**Evidence:**

- "daily trading volumes reaching USD 9.6 trillion in 2025" — [greyspark.com, 2026-05-26](https://www.greyspark.com/report/buyers-guide-institutional-fx-trading-solutions-2026/) — **BBVA**, how it's sold of Net trading income *(trade press, industry body or named research house)*
- "Global forex daily turnover in 2026 reaches an estimated $7.5 trillion" — [track360.io, 2026-05-13](https://track360.io/blog/forex-market-size-2026-annual-breakdown) — **MUFG**, trending demand of Global Markets *(general media)*

### 16. Oil demand rebound in 2027

`oil-demand-rebound-2027`

**What it is.** Global oil demand is expected to recover in 2027 as trade flows normalise and prices ease.

**Found through:** Trending demand | **Revenue streams touched:** Upstream

**Quantum.** size **5.0**, speed **3.5**, impact **4.5** → quantum **4.40** × breadth factor **1.10** = **4.84**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.67; sources: trade press, industry body or named research house x2)

**Positively affected (2):**

- `+` **SHEL** (Shell plc) — Rebounding demand supports higher crude prices and Upstream volumes. *(impact 5, found through Trending demand, stream: Upstream)*
- `+` **TTE** (TotalEnergies SE) — Rebounding demand supports E&P volumes and prices from 2027, improving upstream revenue. *(impact 4, found through Trending demand)*

**Evidence:**

- "Global oil demand is projected to expand by 2.4 mb/d in 2027." — [iea.org, 2026-08-12](https://www.iea.org/reports/oil-market-report-august-2026) — **SHEL**, trending demand of Upstream *(trade press, industry body or named research house)*
- "forecasts for 2027 converge on a recovery of approximately 1.9–2.0 mb/d" — [ief.org, 2026-07-14](https://www.ief.org/news/comparative-analysis-of-monthly-reports-on-the-oil-market-77) — **TTE**, trending demand *(trade press, industry body or named research house)*

### 17. Foundry capacity tightness and price hikes

`foundry-capacity-tightness-price-hikes` — merged from: `truckload-capacity-tightness`

**What it is.** AI demand fills leading-edge foundry capacity, raising wafer prices for chip buyers.

**Found through:** How it's made | **Revenue streams touched:** Game & Network Services

**Quantum.** size **4.5**, speed **5.0**, impact **3.5** → quantum **4.35** × breadth factor **1.10** = **4.79**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.67; sources: trade press, industry body or named research house x2)

**Negatively affected (2):**

- `-` **SONY** (Sony Group Corporation) — Tight foundry capacity and higher wafer prices raise Sony's chip procurement costs. *(impact 3, found through How it's made, stream: Game & Network Services)*
- `-` **UBER** (Uber Technologies, Inc.) — Higher carrier spot rates raise Uber Freight purchased transportation costs and squeeze margins. *(impact 4, found through How it's made)*

**Evidence:**

- "TSMC’s 5nm/4nm and below capacity could be fully booked for the remainder of 2026. In addition, TSMC has raised its prices at 5nm/4nm and below." — [marklapedus.substack.com, 2026-03-20](https://marklapedus.substack.com/p/foundry-outlook-tight-capacity-price) — **SONY**, how it's made of Game & Network Services *(trade press, industry body or named research house)*
- "dry van, reefer, and flatbed spot rates, excluding fuel, were 41% to 47% higher year over year in July" — [actresearch.net, 2026-08-28](https://www.actresearch.net/resources/blog/trucking-industry-forecast-for-2026) — **UBER**, how it's made *(trade press, industry body or named research house)*

### 18. Nonbank competition in banking

`nonbank-competition-in-banking`

**What it is.** Nonbank financial firms compete with banks for loans, deposits, and payments.

**Found through:** How it's sold | **Revenue streams touched:** Payments, Retail & Digital Service Business Group

**Quantum.** size **3.8**, speed **3.8**, impact **3.5** → quantum **3.67** × breadth factor **1.30** = **4.77**  
(4 trends from 4 companies, 2 sources, rating dispersion 1.00; sources: trade press, industry body or named research house x4)

**Negatively affected (4):**

- `-` **BBVA** (Banco Bilbao Vizcaya Argentaria, S.A.) — Nonbanks compete for loans, deposits, and payments, pressuring BBVA's spread and fee income. *(impact 4, found through How it's sold)*
- `-` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Nonbank entrants compete for payments and deposits, pressuring retail banking fees and margins. *(impact 3, found through How it's sold, stream: Retail & Digital Service Business Group)*
- `-` **SAN** (Banco Santander, S.A.) — Merchant migration to PayTechs erodes bank payment acquiring volumes and fee income. *(impact 3, found through How it's sold, stream: Payments)*
- `-` **UBS** (UBS Group AG) — Nonbank rivals take lending and payment share, reducing bank revenue and margins. *(impact 4, found through How it's sold)*

**Evidence:**

- "Banks could be forced to defend margins, diversify fee income, and prepare for increased competition from nonbank entities." — [deloitte.com, 2026-07-01](https://www.deloitte.com/us/en/insights/industry/financial-services/financial-services-industry-outlooks/banking-industry-outlook.html) — **BBVA**, how it's sold *(trade press, industry body or named research house)*
- "Banks could be forced to defend margins, diversify fee income, and prepare for increased competition from nonbank entities." — [deloitte.com, 2026-07-01](https://www.deloitte.com/us/en/insights/industry/financial-services/financial-services-industry-outlooks/banking-industry-outlook.html) — **MUFG**, how it's sold of Retail & Digital Service Business Group *(trade press, industry body or named research house)*
- "Banks face fallout as 40% of small and mid-sized merchant businesses eye shift to PayTechs" — [capgemini.com, 2025-09-01](https://www.capgemini.com/in-en/wp-content/uploads/sites/18/2025/09/09_25_-Capgemini_World-Payments-Report-2026_EN.pdf) — **SAN**, how it's sold of Payments *(trade press, industry body or named research house)*
- "Banks could be forced to defend margins, diversify fee income, and prepare for increased competition from nonbank entities." — [deloitte.com, 2026-07-01](https://www.deloitte.com/us/en/insights/industry/financial-services/financial-services-industry-outlooks/banking-industry-outlook.html) — **UBS**, how it's sold *(trade press, industry body or named research house)*

### 19. Middle East supply shock raises feedstock costs

`middle-east-supply-shock-feedstock-costs` — merged from: `middle-east-conflict-lng-supply-disruption`

**What it is.** Middle East disruptions elevate and volatilise oil and chemical feedstock prices.

**Found through:** How it's made | **Revenue streams touched:** Chemicals and Products, Integrated Gas

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.10** = **4.73**  
(4 trends from 2 companies, 4 sources, rating dispersion 1.33; sources: trade press, industry body or named research house x3, company disclosure x1)

**Negatively affected (1):**

- `-` **SHEL** (Shell plc) — Lower Qatari volumes reduce Integrated Gas production and earnings. *(impact 5, found through How it's made, stream: Integrated Gas)*

**Two-sided or unclear (1):**

- `±` **TTE** (TotalEnergies SE) — Higher LNG prices lift trading and upstream margins, but demand destruction cuts volumes. *(impact 4, found through How it's made)*

**Evidence:**

- "Prolonged disruption keeps oil and feedstock prices elevated and volatile." — [icis.com, 2026-04-01](https://www.icis.com/explore/resources/hormuz-risk-navigating-chemical-supply-shock/) — **SHEL**, how it's made of Chemicals and Products *(trade press, industry body or named research house)*
- "abrupt price surges across polypropylene (PP), polyvinyl chloride (PVC), and benzene" — [beroeinc.com, 2026-03-23](https://www.beroeinc.com/category-focus/how-geopolitical-shock-and-supply-discipline-are-reshaping-petrochemical-procurement-in-2026/) — **TTE**, how it's made *(trade press, industry body or named research house)*
- "production is expected between 610 and 650 kboe/d versus 909 kboe/d in Q1 2026, reflecting the impact of the Middle East conflict on Qatari volumes" — [stocktitan.net, 2026-07-30](https://www.stocktitan.net/sec-filings/SHEL/6-k-shell-plc-current-report-foreign-issuer-fe4eee4bcd50.html) — **SHEL**, how it's made of Integrated Gas *(company disclosure)*
- "the conflict, which has removed roughly 20% of global LNG supply for six months and counting" — [energyintel.com, 2026-09-17](https://www.energyintel.com/000001a0-a93a-dc4a-a1fb-edfb972f0000) — **TTE**, how it's made *(trade press, industry body or named research house)*

### 20. Health-driven beverage reformulation

`health-wellness-beverage-reformulation`

**What it is.** Consumers shift to healthier beverage formulations, including no- and low-alcohol options.

**Found through:** Trending demand | **Revenue streams touched:** Beer Business, Sparkling Soft Drinks

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.10** = **4.73**  
(2 trends from 2 companies, 2 sources, rating dispersion 1.33; sources: company disclosure x1, vendor market-report page x1)

**Positively affected (1):**

- `+` **BUD** (Anheuser-Busch InBev SA/NV) — No-alcohol beer lifts revenue per hectoliter and offsets declining alcohol volumes. *(impact 3, found through Trending demand, stream: Beer Business)*

**Two-sided or unclear (1):**

- `±` **KO** (The Coca-Cola Company) — Shifts mix within Sparkling Soft Drinks; KO's zero-sugar portfolio can offset core sugar volume decline. *(impact 5, found through Trending demand, stream: Sparkling Soft Drinks)*

**Evidence:**

- "27% increase in revenue of no-alcohol beer" — [businesswire.com, 2026-05-05](https://www.businesswire.com/news/home/20260504526109/en/AB-InBev-Reports-First-Quarter-2026-Results) — **BUD**, trending demand of Beer Business *(company disclosure)*
- "Demand for zero-sugar and diet carbonated soft drink formulations is increasing owing to rising consumer awareness of obesity and metabolic health risks" — [emergenresearch.com, 2026-07-14](https://www.emergenresearch.com/industry-report/carbonated-soft-drinks-market) — **KO**, trending demand of Sparkling Soft Drinks *(vendor market-report page)*

### 21. Copper market balance

`copper-market-balance`

**What it is.** The gap between refined copper supply and demand that sets prices and producer margins.

**Found through:** Trending demand, How it's made

**Quantum.** size **5.0**, speed **4.0**, impact **5.0** → quantum **4.70** × breadth factor **1.00** = **4.70**  
(2 trends from 1 companies, 2 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1, general media x1)

**Two-sided or unclear (1):**

- `±` **BHP** (BHP Group Limited) — A looser copper balance pressures prices, reducing BHP's copper revenue. *(impact 5, found through Trending demand)*

**Evidence:**

- "We model a structural refined-copper deficit widening through 2026 as grid and EV demand outpaces new supply." — [montriam.com, 2026-07-28](https://www.montriam.com/en-gb/insights/copper-price-outlook-2026-pro) — **BHP**, how it's made *(trade press, industry body or named research house)*
- "By April, that number had swung to a projected surplus of about 96,000 tonnes." — [grumarket.com, 2026-09-11](https://grumarket.com/articles/copper-futures-price-prediction-5/) — **BHP**, trending demand *(general media)*

### 22. Beer volume decline offset by premium mix

`beer-volume-decline-premium-mix`

**What it is.** Global beer volumes fall while premium and no-alcohol products lift value per serving.

**Found through:** Trending demand | **Revenue streams touched:** Beer Business

**Quantum.** size **5.0**, speed **5.0**, impact **4.0** → quantum **4.70** × breadth factor **1.00** = **4.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **BUD** (Anheuser-Busch InBev SA/NV) — Volume decline pressures beer revenue, while premium mix lifts revenue per hectoliter. *(impact 4, found through Trending demand, stream: Beer Business)*

**Evidence:**

- "total beer volumes (in the world’s leading 21 markets/T21) fell by -1%, but value* grew slightly" — [theiwsr.com](https://www.theiwsr.com/insight/under-pressure-but-not-out-of-options-beer-in-2026/) — **BUD**, trending demand of Beer Business *(trade press, industry body or named research house)*

### 23. Clean energy tax credit deadlines

`clean-energy-tax-credit-deadlines`

**What it is.** US clean energy tax credits now have construction and operation deadlines that reshape project timing.

**Found through:** How it's sold | **Revenue streams touched:** NEER

**Quantum.** size **5.0**, speed **5.0**, impact **4.0** → quantum **4.70** × breadth factor **1.00** = **4.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Two-sided or unclear (1):**

- `±` **NEE** (NextEra Energy, Inc.) — Pulls forward wind/solar projects but threatens post-2027 pipeline; storage/nuclear favored. *(impact 4, found through How it's sold, stream: NEER)*

**Evidence:**

- "projects generally needed to begin construction by July 4, 2026, or reach commercial operation by the end of 2027" — [kurums.com, 2026-08-26](https://kurums.com/us-renewable-energy-strategy/) — **NEE**, how it's sold of NEER *(general media)*

### 24. Consumer tech demand flatness

`consumer-tech-demand-flatness`

**What it is.** Global consumer technology spending stalls after prior growth, with regional divergence.

**Found through:** Trending demand | **Revenue streams touched:** Entertainment Technology & Services

**Quantum.** size **5.0**, speed **5.0**, impact **4.0** → quantum **4.70** × breadth factor **1.00** = **4.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **SONY** (Sony Group Corporation) — Flat consumer electronics demand pressures Sony's TV, audio, and camera sales. *(impact 4, found through Trending demand, stream: Entertainment Technology & Services)*

**Evidence:**

- "For 2026, the global picture will flatten, with NIQ estimating -0.4% year-over-year growth." — [nielseniq.com, 2026-03-01](https://nielseniq.com/global/en/insights/analysis/2026/consumer-tech-market-growth-estimate-2026/) — **SONY**, trending demand of Entertainment Technology & Services *(trade press, industry body or named research house)*

### 25. Household credit demand weakness

`household-credit-demand-weakness`

**What it is.** Declining household demand for mortgages and consumer credit across banking markets.

**Found through:** Trending demand | **Revenue streams touched:** Retail & Commercial Banking

**Quantum.** size **5.0**, speed **5.0**, impact **4.0** → quantum **4.70** × breadth factor **1.00** = **4.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **SAN** (Banco Santander, S.A.) — Weaker household borrowing reduces retail and consumer loan volumes and net interest income. *(impact 4, found through Trending demand, stream: Retail & Commercial Banking)*

**Evidence:**

- "Demand for housing loans contracted markedly" — [ecb.europa.eu, 2026-07-15](https://www.ecb.europa.eu/stats/ecb_surveys/bank_lending_survey/pdf/ecb.blssurvey2026q2~baa6b60429.en.pdf) — **SAN**, trending demand of Retail & Commercial Banking *(trade press, industry body or named research house)*

### 26. Japan NISA asset management inflows

`japan-nisa-asset-management-inflows`

**What it is.** Retail investment inflows into Japanese funds driven by tax-exempt NISA savings accounts.

**Found through:** Trending demand | **Revenue streams touched:** Asset Management/Investor Services

**Quantum.** size **5.0**, speed **5.0**, impact **4.0** → quantum **4.70** × breadth factor **1.00** = **4.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Higher fund inflows and AUM lift management fees for MUFG's asset management arm. *(impact 4, found through Trending demand, stream: Asset Management/Investor Services)*

**Evidence:**

- "publicly offered open-ended equity investment trusts experienced monthly net inflows exceeding 1 trillion yen for 10 consecutive months leading up to June 2026." — [fintechobserver.com, 2026-09-14](https://www.fintechobserver.com/morningstar-japan-asset-management-digest-2026/) — **MUFG**, trending demand of Asset Management/Investor Services *(trade press, industry body or named research house)*

### 27. M&A volume rebound

`m-and-a-volume-rebound`

**What it is.** Global mergers and acquisitions activity is rebounding strongly, boosting investment banking fees.

**Found through:** Trending demand | **Revenue streams touched:** Corporate and Investment Banking

**Quantum.** size **5.0**, speed **5.0**, impact **4.0** → quantum **4.70** × breadth factor **1.00** = **4.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **WFC** (Wells Fargo & Company) — Higher M&A volumes boost advisory and capital markets fee revenue in Corporate and Investment Banking. *(impact 4, found through Trending demand, stream: Corporate and Investment Banking)*

**Evidence:**

- "Global M&A volumes rose 48% YoY" — [goldmansachs.com, 2026-07-22](https://www.goldmansachs.com/what-we-do/investment-banking/insights/articles/global-ma-in-2h-2026) — **WFC**, trending demand of Corporate and Investment Banking *(trade press, industry body or named research house)*

### 28. Sales and trading revenue boom

`sales-and-trading-revenue-boom`

**What it is.** Global markets revenues are hitting records on elevated volatility and client activity.

**Found through:** Trending demand

**Quantum.** size **5.0**, speed **5.0**, impact **4.0** → quantum **4.70** × breadth factor **1.00** = **4.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **BAC** (Bank of America Corporation) — Record global markets revenues directly lift sales and trading income. *(impact 4, found through Trending demand)*

**Evidence:**

- "Banks are projected to generate a record US$169bn of global markets revenues in the first half" — [ifre.com, 2026-07-17](https://www.ifre.com/topic-codes/2455134/equities-blowout-to-deliver-record-revenue-haul-for-bank-traders) — **BAC**, trending demand *(trade press, industry body or named research house)*

### 29. Solar supply chain oversupply

`solar-supply-chain-oversupply`

**What it is.** Global solar manufacturing capacity exceeds demand, keeping module and polysilicon prices low.

**Found through:** How it's made | **Revenue streams touched:** NEER

**Quantum.** size **5.0**, speed **5.0**, impact **4.0** → quantum **4.70** × breadth factor **1.00** = **4.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Positively affected (1):**

- `+` **NEE** (NextEra Energy, Inc.) — Lower module and polysilicon costs improve NEER project economics. *(impact 4, found through How it's made, stream: NEER)*

**Evidence:**

- "Solar supply chain trends in 2026 show module prices stabilizing at $0.10–$0.15/W, polysilicon at $8–$12/kg" — [surgepv.com, 2026-05-25](https://www.surgepv.com/blog/solar-supply-chain-trends-2026) — **NEE**, how it's made of NEER *(general media)*

### 30. SVOD market saturation

`svod-market-saturation`

**What it is.** U.S. subscription video market reaching high household penetration, limiting new subscriber growth.

**Found through:** Trending demand | **Revenue streams touched:** Monthly memberships

**Quantum.** size **5.0**, speed **5.0**, impact **4.0** → quantum **4.70** × breadth factor **1.00** = **4.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **NFLX** (Netflix, Inc.) — Saturated U.S. market means growth must come from pricing or international, not new households. *(impact 4, found through Trending demand, stream: Monthly memberships)*

**Evidence:**

- "the SVOD market as a whole has achieved a 91% penetration rate among U.S. households" — [parksassociates.com, 2026-01-19](https://www.parksassociates.com/index.php/blogs/in-the-news/home-entertainment-forecast-2026-streaming-flexes-its-muscle-transactional-a-critical-revenue-bridge) — **NFLX**, trending demand of Monthly memberships *(trade press, industry body or named research house)*

### 31. Banking technology spending cycle

`banking-technology-spending-cycle`

**What it is.** Banks increase technology spending on digital transformation and AI.

**Found through:** How it's made

**Quantum.** size **3.7**, speed **4.7**, impact **3.3** → quantum **3.87** × breadth factor **1.20** = **4.64**  
(3 trends from 3 companies, 3 sources, rating dispersion 1.00; sources: trade press, industry body or named research house x3)

**Negatively affected (2):**

- `-` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Rising technology spend raises operating costs and competes with other investment capacity. *(impact 3, found through How it's made)*
- `-` **UBS** (UBS Group AG) — Rising technology and operating costs pressure Investment Bank margins. *(impact 4, found through How it's made)*

**Two-sided or unclear (1):**

- `±` **BBVA** (Banco Bilbao Vizcaya Argentaria, S.A.) — Higher technology spend raises BBVA's cost base while potentially improving efficiency and distribution. *(impact 3, found through How it's made)*

**Evidence:**

- "digital transformation remains the top focus" — [digitalbankingreport.com, 2026-01-01](https://www.digitalbankingreport.com/trends/2026-retail-banking-trends-and-priorities/) — **BBVA**, how it's made *(trade press, industry body or named research house)*
- "major-bank technology wallets up ~16% since Jun’24 and +7.8% YoY in Jun’26 despite macro uncertainty." — [investmentguruindia.com, 2026-09-10](https://investmentguruindia.com/editorial/uploads/news-pdf/9449adb3_research-report.pdf) — **MUFG**, how it's made *(trade press, industry body or named research house)*
- "Corporate and investment bank operating costs have climbed almost 25% since 2019, driven largely by rapidly increasing technology spending" — [greenwich.com, 2026-08-25](https://www.greenwich.com/press-release/bank-operating-costs-rise-amid-surge-tech-spending) — **UBS**, how it's made *(trade press, industry body or named research house)*

### 32. Content spend inflation

`content-spend-inflation`

**What it is.** Rising content spending by streaming platforms increasing the cost base.

**Found through:** How it's made

**Quantum.** size **4.0**, speed **5.0**, impact **5.0** → quantum **4.60** × breadth factor **1.00** = **4.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **NFLX** (Netflix, Inc.) — Content is Netflix's largest cost, so higher spending pressures margins unless offset by revenue. *(impact 5, found through How it's made)*

**Evidence:**

- "Netflix is eyeing $20 billion in content cash spending in 2026, up 10%" — [variety.com, 2026-03-27](https://variety.com/2026/biz/news/why-netflix-hiked-prices-explained-chart-1236701365/) — **NFLX**, how it's made *(trade press, industry body or named research house)*

### 33. Subscription streaming spend growth

`subscription-streaming-spend-growth`

**What it is.** Consumer spending on subscription streaming services continues to rise.

**Found through:** Trending demand | **Revenue streams touched:** Monthly memberships

**Quantum.** size **4.0**, speed **5.0**, impact **5.0** → quantum **4.60** × breadth factor **1.00** = **4.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **NFLX** (Netflix, Inc.) — Higher streaming spend lifts the subscription revenue pool Netflix sells into. *(impact 5, found through Trending demand, stream: Monthly memberships)*

**Evidence:**

- "The 2026 first half increase was fueled by a 15.1 percent rise in aggregated subscription streaming spending" — [degonline.org, 2026-08-01](https://www.degonline.org/wp-content/uploads/2026/08/f2_DEGMidYear2026_covernote-grid_8.12.26.pdf) — **NFLX**, trending demand of Monthly memberships *(trade press, industry body or named research house)*

### 34. Wireless promotional intensity

`wireless-promotional-intensity`

**What it is.** Carriers compete with aggressive device subsidies and promotions, compressing postpaid margins.

**Found through:** How it's sold

**Quantum.** size **4.0**, speed **5.0**, impact **5.0** → quantum **4.60** × breadth factor **1.00** = **4.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **VZ** (Verizon Communications Inc.) — Higher subsidies and promotions raise customer acquisition costs and reduce service margins. *(impact 5, found through How it's sold)*

**Evidence:**

- "Mobile service promotions remain at all-time highs with lots of parity" — [counterpointresearch.com, 2026-02-25](https://counterpointresearch.com/en/reports/state-of-us-postpaid-2026-the-year-of-convergence-and-shrinking-margins-for-us-postpaid-mnos) — **VZ**, how it's sold *(trade press, industry body or named research house)*

### 35. Deposit competition raises funding costs

`deposit-competition-funding-costs`

**What it is.** Banks compete for deposits, raising funding costs and pressuring net interest margins.

**Found through:** How it's sold, How it's made

**Quantum.** size **4.0**, speed **4.5**, impact **4.0** → quantum **4.15** × breadth factor **1.10** = **4.57**  
(2 trends from 2 companies, 2 sources, rating dispersion 1.00; sources: trade press, industry body or named research house x2)

**Negatively affected (2):**

- `-` **BAC** (Bank of America Corporation) — Intense deposit competition raises funding costs and compresses net interest margin. *(impact 4, found through How it's sold)*
- `-` **SAN** (Banco Santander, S.A.) — Higher funding costs compress net interest margins and profitability. *(impact 4, found through How it's made)*

**Evidence:**

- "As deposit competition intensifies and liquidity management grows more complex" — [aba.com, 2026-03-19](https://www.aba.com/training-events/online-training/the-2026-deposit-playbook) — **BAC**, how it's sold *(trade press, industry body or named research house)*
- "Banks’ access to funding deteriorated for retail funding, debt securities and money markets" — [ecb.europa.eu, 2026-07-15](https://www.ecb.europa.eu/stats/ecb_surveys/bank_lending_survey/pdf/ecb.blssurvey2026q2~baa6b60429.en.pdf) — **SAN**, how it's made *(trade press, industry body or named research house)*

### 36. Net interest margin compression

`net-interest-margin-compression`

**What it is.** Falling rates and loan repricing compress bank net interest margins.

**Found through:** How it's made | **Revenue streams touched:** Net interest income

**Quantum.** size **3.0**, speed **4.3**, impact **4.3** → quantum **3.80** × breadth factor **1.20** = **4.56**  
(3 trends from 3 companies, 2 sources, rating dispersion 1.00; sources: trade press, industry body or named research house x3)

**Negatively affected (3):**

- `-` **BBVA** (Banco Bilbao Vizcaya Argentaria, S.A.) — Narrower spreads directly reduce BBVA's largest revenue stream, net interest income. *(impact 5, found through How it's made, stream: Net interest income)*
- `-` **UBS** (UBS Group AG) — Margin pressure reduces net interest income from Swiss lending and deposits. *(impact 3, found through How it's made)*
- `-` **WFC** (Wells Fargo & Company) — Narrower net interest margin reduces net interest income, a core driver of total revenue. *(impact 5, found through How it's made)*

**Evidence:**

- "continued repricing of loans and other earning assets is likely to increase pressure on spread income" — [simon-kucher.com, 2026-07-31](https://www.simon-kucher.com/en/insights/building-stronger-non-interest-revenue-engine-commercial-banking) — **BBVA**, how it's made of Net interest income *(trade press, industry body or named research house)*
- "With margins still under pressure, expectations for interest operations remain cautious." — [swissbanking.ch, 2026-08-01](https://www.swissbanking.ch/_Resources/Persistent/3/1/e/8/31e89d93c48aa685e9f31a7329e66055953e1df2/Swiss-Banking-Outlook_2026_EN.pdf) — **UBS**, how it's made *(trade press, industry body or named research house)*
- "less room to further reduce funding costs, while continued repricing of loans and other earning assets is likely to increase pressure on spread income" — [simon-kucher.com, 2026-07-31](https://www.simon-kucher.com/en/insights/building-stronger-non-interest-revenue-engine-commercial-banking) — **WFC**, how it's made *(trade press, industry body or named research house)*

### 37. China iron ore pricing power

`china-iron-ore-pricing-power` — merged from: `iron-ore-supply-growth`

**What it is.** China's centralized buyer and RMB indexes reshaping iron ore contract pricing and miner bargaining power.

**Found through:** How it's sold, How it's made

**Quantum.** size **5.0**, speed **4.0**, impact **4.5** → quantum **4.55** × breadth factor **1.00** = **4.55**  
(2 trends from 1 companies, 2 sources, rating dispersion 1.00; sources: trade press, industry body or named research house x2)

**Two-sided or unclear (1):**

- `±` **BHP** (BHP Group Limited) — Ending the dispute restores sales, but Chinese index pricing may reduce BHP's pricing power. *(impact 5, found through How it's sold)*

**Evidence:**

- "BHP and China Mineral Resources Group (CMRG) have finally reached an agreement on their annual long-term iron ore contract." — [miningcomm.com, 2026-04-29](https://miningcomm.com/bhp-and-cmrg-finalize-annual-iron-ore-long-term-contract/) — **BHP**, how it's sold *(trade press, industry body or named research house)*
- "~70 Mt of new seaborne capacity in 2026 — Simandou first among them — bends the multi-year price curve lower." — [events.metal.com, 2026-07-06](https://events.metal.com/ai-stack/reports/ironore_en.html) — **BHP**, how it's made *(trade press, industry body or named research house)*

### 38. Beverage packaging input inflation

`beverage-packaging-input-inflation`

**What it is.** Costs for glass, aluminum, and paper packaging rise, squeezing beverage margins.

**Found through:** How it's made | **Revenue streams touched:** Beer Business

**Quantum.** size **3.5**, speed **5.0**, impact **4.0** → quantum **4.10** × breadth factor **1.10** = **4.51**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.33; sources: general media x2)

**Negatively affected (2):**

- `-` **BUD** (Anheuser-Busch InBev SA/NV) — Higher packaging costs raise AB InBev's cost of goods sold and pressure beer margins. *(impact 4, found through How it's made, stream: Beer Business)*
- `-` **KO** (The Coca-Cola Company) — Higher packaging input costs squeeze bottler margins and may pass through to KO's system economics. *(impact 4, found through How it's made)*

**Evidence:**

- "Aluminum cans jumped 10.8% year-over-year through April 2026, the steepest YoY move of any packaging substrate." — [eightx.co, 2026-08-01](https://eightx.co/blog/packaging-cost-squeeze-2026) — **BUD**, how it's made of Beer Business *(general media)*
- "bottlers would have greater impact if higher aluminum and pet prices sustain" — [newsquawk.com, 2026-04-28](https://www.newsquawk.com/headlines/coca-cola-ko-cfo-says-bottlers-would-have-greater-impact-if-higher-aluminum-and-pet-prices-sustain-on-aluminum-can-shortage-in-india-says-have-had-some-disruption-in-can-supply-and-our-cross-enterprise-procurement-team) — **KO**, how it's made *(general media)*

### 39. Refining and chemical margin recovery

`refining-and-chemical-margin-recovery`

**What it is.** Refining and chemicals margins are recovering from prior lows, improving downstream earnings.

**Found through:** How it's sold | **Revenue streams touched:** Chemicals and Products

**Quantum.** size **3.5**, speed **5.0**, impact **4.0** → quantum **4.10** × breadth factor **1.10** = **4.51**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.33; sources: company disclosure x1, trade press, industry body or named research house x1)

**Positively affected (2):**

- `+` **SHEL** (Shell plc) — Higher refining and chemicals margins lift Chemicals and Products earnings. *(impact 4, found through How it's sold, stream: Chemicals and Products)*
- `+` **TTE** (TotalEnergies SE) — High cracks lift TTE's refining and chemicals segment margins. *(impact 4, found through How it's sold)*

**Evidence:**

- "indicative refining margin of about $20/bbl versus $17/bbl in Q1 2026 and an indicative chemicals margin of about $240/tonne versus $139/tonne" — [stocktitan.net, 2026-07-30](https://www.stocktitan.net/sec-filings/SHEL/6-k-shell-plc-current-report-foreign-issuer-fe4eee4bcd50.html) — **SHEL**, how it's sold of Chemicals and Products *(company disclosure)*
- "Refining margins remain at historically high levels, supported by record middle distillate cracks." — [iea.blob.core.windows.net, 2026-09-01](https://iea.blob.core.windows.net/assets/2b89a47b-34a2-40e0-90ff-68f7ccd80715/-13MAY2026__OilMarketReport_publicversion.pdf) — **TTE**, how it's sold *(trade press, industry body or named research house)*

### 40. CIB wallet sponsor migration

`cib-wallet-sponsor-migration`

**What it is.** Corporate and investment banking revenue shifting toward sponsors and portfolio companies.

**Found through:** How it's sold | **Revenue streams touched:** Corporate & Investment Banking, Global Corporate & Investment Banking

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.10** = **4.51**  
(2 trends from 2 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x2)

**Two-sided or unclear (2):**

- `±` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Wallet growth helps revenue, but sponsor migration and fee decline pressure traditional CIB margins. *(impact 4, found through How it's sold, stream: Global Corporate & Investment Banking)*
- `±` **SAN** (Banco Santander, S.A.) — Santander must capture sponsor-led fee pools to offset declining traditional CIB fees. *(impact 4, found through How it's sold, stream: Corporate & Investment Banking)*

**Evidence:**

- "revenues migrating toward sponsors and their portfolio companies while traditional corporate and institutional fees decline." — [bcg.com, 2025-10-14](https://www.bcg.com/publications/2025/driving-growth-in-corporate-and-investment-banking) — **MUFG**, how it's sold of Global Corporate & Investment Banking *(trade press, industry body or named research house)*
- "revenues migrating toward sponsors and their portfolio companies while traditional corporate and institutional fees decline" — [bcg.com, 2025-10-14](https://www.bcg.com/publications/2025/driving-growth-in-corporate-and-investment-banking) — **SAN**, how it's sold of Corporate & Investment Banking *(trade press, industry body or named research house)*

### 41. Consumer electronics tariff nearshoring

`consumer-electronics-tariff-nearshoring` — merged from: `consumer-electronics-demand-growth`

**What it is.** Tariffs push console and electronics production from China to Vietnam and other locations.

**Found through:** Trending demand, How it's made | **Revenue streams touched:** Entertainment Technology & Services, Game & Network Services

**Quantum.** size **4.5**, speed **5.0**, impact **4.0** → quantum **4.50** × breadth factor **1.00** = **4.50**  
(2 trends from 1 companies, 2 sources, rating dispersion 0.33; sources: general media x1, vendor market-report page x1)

**Two-sided or unclear (1):**

- `±` **SONY** (Sony Group Corporation) — Tariff avoidance lowers landed costs but relocation and Vietnam tariffs add expense. *(impact 4, found through How it's made, stream: Game & Network Services)*

**Evidence:**

- "China’s share of US console imports dropped from 86% in 2024 to less than 5% in 2025. Vietnam captured 75% of the market." — [exnihilomagazine.com, 2026-03-03](https://exnihilomagazine.com/slug-vietnam-manufacturing-surge-electronics-tariffs/) — **SONY**, how it's made of Game & Network Services *(general media)*
- "demand for consumer electronics is estimated to grow to USD 740 billion in 2026" — [factmr.com, 2026-03-12](https://www.factmr.com/report/consumer-electronics-market) — **SONY**, trending demand of Entertainment Technology & Services *(vendor market-report page)*

### 42. Equity market rally lifts AUM

`equity-market-rally-aum`

**What it is.** Rising financial markets and wealth growth increase assets under management and wealth-management revenue.

**Found through:** Trending demand

**Quantum.** size **4.0**, speed **4.3**, impact **3.7** → quantum **4.00** × breadth factor **1.10** = **4.40**  
(3 trends from 2 companies, 3 sources, rating dispersion 1.33; sources: trade press, industry body or named research house x1, company disclosure x1, vendor market-report page x1)

**Positively affected (2):**

- `+` **BAC** (Bank of America Corporation) — Rising equity markets increase assets under management and asset management fee revenue. *(impact 3, found through Trending demand)*
- `+` **UBS** (UBS Group AG) — Higher client assets increase fee-based revenue and net new money for wealth management. *(impact 4, found through Trending demand)*

**Evidence:**

- "The S&P 500 ended 2Q26 at 7,49.36 (+14.9% Q/Q, +20.9% Y/Y)" — [sifma.org, 2026-04-01](https://www.sifma.org/wp-content/uploads/2026/04/SIFMA-Research-Quarterly-Equity-and-Related-2Q26.pdf) — **BAC**, trending demand *(trade press, industry body or named research house)*
- "In 2025, global personal wealth rose by 10.8% in USD terms" — [ubs.com, 2026-06-30](https://www.ubs.com/global/en/media/display-page-ndp/en-20260630-gwr-2026.html) — **UBS**, trending demand *(company disclosure)*
- "lower interest rates and steady, but subdued, economic growth globally in the next 12-18 months will support growth in assets under management (AUM) and revenue." — [moodys.com, 2025-11-12](https://www.moodys.com/web/en/us/insights/credit-risk/outlooks/asset-management-2026.html) — **UBS**, trending demand *(vendor market-report page)*

### 43. AI telecom procurement savings

`telecom-ai-procurement-cost-savings`

**What it is.** AI spend intelligence tools reduce telecom operators' external procurement costs.

**Found through:** How it's made

**Quantum.** size **5.0**, speed **4.0**, impact **4.0** → quantum **4.40** × breadth factor **1.00** = **4.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Positively affected (1):**

- `+` **VZ** (Verizon Communications Inc.) — Cuts external spend, which is up to 40% of telecom revenue, improving Verizon's margins. *(impact 4, found through How it's made)*

**Evidence:**

- "AI-powered spend intelligence platforms deliver 95%+ visibility and 5–15% cost reductions within 90 days" — [suplari.com, 2026-07-28](https://suplari.com/blog/state-of-telecoms-procurement) — **VZ**, how it's made *(general media)*

### 44. Credit card balance growth moderation

`credit-card-balance-growth-moderation`

**What it is.** Credit card balances are growing more slowly as lenders tighten underwriting and consumers manage debt.

**Found through:** Trending demand | **Revenue streams touched:** Consumer Banking and Lending

**Quantum.** size **5.0**, speed **4.0**, impact **4.0** → quantum **4.40** × breadth factor **1.00** = **4.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **WFC** (Wells Fargo & Company) — Slower card balance growth limits interest and fee revenue growth in Consumer Banking and Lending. *(impact 4, found through Trending demand, stream: Consumer Banking and Lending)*

**Evidence:**

- "credit card balances to grow 2.3% year over year (YoY)—the smallest annual increase since 2013" — [newsroom.transunion.com, 2025-12-01](https://newsroom.transunion.com/2026-consumer-credit-forecast/) — **WFC**, trending demand of Consumer Banking and Lending *(trade press, industry body or named research house)*

### 45. Global steel demand growth

`global-steel-demand-growth`

**What it is.** Steel consumption growth that drives demand for iron ore and metallurgical coal.

**Found through:** Trending demand

**Quantum.** size **5.0**, speed **4.0**, impact **4.0** → quantum **4.40** × breadth factor **1.00** = **4.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **BHP** (BHP Group Limited) — Steelmakers buy iron ore; higher steel output lifts BHP's iron ore volumes and prices. *(impact 4, found through Trending demand)*

**Evidence:**

- "worldsteel forecasts that global demand will grow by 0.3% in 2026 to reach 1,724 Mt, followed by an accelerated growth of 2.2% in 2027" — [worldsteel.org, 2026-04-14](https://worldsteel.org/media/press-releases/2026/worldsteel-short-range-outlook-april-2026/) — **BHP**, trending demand *(trade press, industry body or named research house)*

### 46. IRA Medicare drug price negotiation

`ira-medicare-drug-price-negotiation`

**What it is.** Medicare drug price negotiation sets maximum fair prices and compresses pharma revenue.

**Found through:** How it's sold

**Quantum.** size **5.0**, speed **4.0**, impact **4.0** → quantum **4.40** × breadth factor **1.00** = **4.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **PFE** (Pfizer Inc.) — Government-negotiated prices reduce revenue and margins on affected drugs. *(impact 4, found through How it's sold)*

**Evidence:**

- "IRA MFP is three rounds deep: Round 1 live Jan 2026, Round 2 (15 drugs, $41B spend, semaglutide -71%) effective Jan 2027" — [rxalmanac.com, 2026-05-25](https://rxalmanac.com/articles/ira-mfp-impact-pharma-services-vendors/) — **PFE**, how it's sold *(trade press, industry body or named research house)*

### 47. LNG supply wave 2026-2027

`lng-supply-wave-2026-2027`

**What it is.** A large wave of new liquefaction capacity expands global LNG supply and pressures prices.

**Found through:** How it's made

**Quantum.** size **5.0**, speed **4.0**, impact **4.0** → quantum **4.40** × breadth factor **1.00** = **4.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **TTE** (TotalEnergies SE) — New supply pressures LNG prices but lowers feedstock costs for TTE's offtake and trading. *(impact 4, found through How it's made)*

**Evidence:**

- "to a notional 610 million tonnes per year by end 2027" — [deluair.com, 2026-04-26](https://deluair.com/consultancy/insights/lng-global-glut-2026) — **TTE**, how it's made *(trade press, industry body or named research house)*

### 48. Non-carbonated beverage shift

`non-carbonated-beverage-shift`

**What it is.** Consumers move from carbonated sugary drinks to still, hydrating, and functional non-carbonated beverages.

**Found through:** Trending demand | **Revenue streams touched:** Water, Sports, Coffee & Tea

**Quantum.** size **5.0**, speed **4.0**, impact **4.0** → quantum **4.40** × breadth factor **1.00** = **4.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **KO** (The Coca-Cola Company) — Lifts KO's non-carbonated portfolio, offsetting slower carbonated volume growth. *(impact 4, found through Trending demand, stream: Water, Sports, Coffee & Tea)*

**Evidence:**

- "growing at a CAGR of 6.4% from 2026 to 2033" — [grandviewresearch.com, 2025-10-01](https://www.grandviewresearch.com/industry-analysis/non-carbonated-soft-drinks-market-report) — **KO**, trending demand of Water, Sports, Coffee & Tea *(vendor market-report page)*

### 49. Ride-hailing demand growth

`ride-hailing-demand-growth`

**What it is.** Global demand for app-based ride-hailing expands, lifting trip volumes and platform revenue.

**Found through:** Trending demand

**Quantum.** size **5.0**, speed **3.0**, impact **5.0** → quantum **4.40** × breadth factor **1.00** = **4.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **UBER** (Uber Technologies, Inc.) — Expanding ride-hailing demand lifts Uber Mobility bookings and revenue over the forecast period. *(impact 5, found through Trending demand)*

**Evidence:**

- "Market Size (2031) | USD 513.77 Billion" — [mordorintelligence.com, 2026-08-12](https://www.mordorintelligence.com/industry-reports/ride-hailing-market) — **UBER**, trending demand *(vendor market-report page)*

### 50. Streaming subscriber growth

`streaming-subscriber-growth`

**What it is.** Global subscription streaming subscriber growth as platforms scale and consolidate.

**Found through:** Trending demand | **Revenue streams touched:** Monthly memberships

**Quantum.** size **5.0**, speed **3.0**, impact **5.0** → quantum **4.40** × breadth factor **1.00** = **4.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **NFLX** (Netflix, Inc.) — More subscribers directly increase monthly membership revenue, the largest revenue stream. *(impact 5, found through Trending demand, stream: Monthly memberships)*

**Evidence:**

- "increasing its subscriber base from 325.3 million in 2025 to 396.2 million by 2031" — [telecomlead.com, 2026-06-13](https://telecomlead.com/broadcasting/netflix-to-reach-396-2-mn-subscribers-by-2031-as-jiohotstar-disney-and-hbo-max-paramount-drive-streaming-market-growth-126250) — **NFLX**, trending demand of Monthly memberships *(trade press, industry body or named research house)*

### 51. Wireless spectrum capacity shortfall

`wireless-spectrum-capacity-shortfall`

**What it is.** US wireless networks face mid-band spectrum shortages that constrain capacity and require new investment.

**Found through:** How it's made

**Quantum.** size **5.0**, speed **4.0**, impact **4.0** → quantum **4.40** × breadth factor **1.00** = **4.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **VZ** (Verizon Communications Inc.) — Requires additional spectrum and network capex, raising Verizon's cost base and risking service quality. *(impact 4, found through How it's made)*

**Evidence:**

- "by 2027, networks will be unable to meet nearly a quarter of traffic demand in high-traffic areas during peak hours" — [api.ctia.org, 2025-03-01](https://api.ctia.org/wp-content/uploads/2025/03/Looming-Spectrum-Crisis-Accenture.pdf) — **VZ**, how it's made *(trade press, industry body or named research house)*

### 52. Agentic AI banking productivity

`agentic-ai-banking-productivity`

**What it is.** AI agents cutting banking operating costs and lifting fee income across retail and wealth.

**Found through:** How it's made

**Quantum.** size **3.3**, speed **3.7**, impact **4.0** → quantum **3.63** × breadth factor **1.20** = **4.36**  
(3 trends from 3 companies, 3 sources, rating dispersion 1.00; sources: trade press, industry body or named research house x3)

**Positively affected (3):**

- `+` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Lower operating costs and higher fee income improve margins across retail and wealth streams. *(impact 4, found through How it's made)*
- `+` **SAN** (Banco Santander, S.A.) — AI-driven productivity lowers operating costs and improves efficiency ratio. *(impact 4, found through How it's made)*
- `+` **UBS** (UBS Group AG) — Higher advisor productivity and lower costs expand wealth management margins. *(impact 4, found through How it's made)*

**Evidence:**

- "agentic AI is delivering more than 50% productivity gains in retail lending and boosting fee income by more than 30% in wealth management." — [bcg.com, 2026-06-08](https://www.bcg.com/publications/2026/future-of-finance-2026-time-to-shift-gears) — **MUFG**, how it's made *(trade press, industry body or named research house)*
- "AI can unlock meaningful productivity gains while laggards face a widening cost disadvantage." — [strategyand.pwc.com, 2026-07-06](https://www.strategyand.pwc.com/de/en/industries/financial-services/retail-banking-monitor.html) — **SAN**, how it's made *(trade press, industry body or named research house)*
- "AI, which is poised to improve conversion rates by 10-25%, unlock 25-30% additional capacity in planning and servicing" — [fintechnews.ch, 2026-07-07](https://fintechnews.ch/roboadvisor_onlinewealth/top-findings-ubs-global-wealth-report-2026/84524/) — **UBS**, how it's made *(trade press, industry body or named research house)*

### 53. Gulf energy shock metals costs

`gulf-energy-shock-metals-costs`

**What it is.** Middle East energy disruption raising fuel, power and currency costs across mining and metals.

**Found through:** How it's made | **Revenue streams touched:** Beer Business

**Quantum.** size **3.5**, speed **4.5**, impact **4.0** → quantum **3.95** × breadth factor **1.10** = **4.35**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.67; sources: trade press, industry body or named research house x1, general media x1)

**Negatively affected (2):**

- `-` **BHP** (BHP Group Limited) — Higher input and currency costs compress margins on BHP's copper output. *(impact 4, found through How it's made)*
- `-` **BUD** (Anheuser-Busch InBev SA/NV) — Higher aluminum costs raise can prices and AB InBev's packaging cost base. *(impact 4, found through How it's made, stream: Beer Business)*

**Evidence:**

- "Copper faces a broad-based increase in commodity cost pressure rather than a single-point shock." — [crugroup.com, 2026-03-24](https://www.crugroup.com/en/communities/thought-leadership/2026/gulf-energy-shock-fuels-broader-cost-pressures-for-metals/) — **BHP**, how it's made *(trade press, industry body or named research house)*
- "Aluminum on the London Metal Exchange has surged more than 13% since the U.S.-Israeli strikes on Iran on Feb. 28." — [cnbc.com, 2026-05-05](https://www.cnbc.com/2026/05/05/aluminum-prices-hormuz-ford-molson-coors.html) — **BUD**, how it's made of Beer Business *(general media)*

### 54. India met coal import growth

`india-met-coal-import-growth` — merged from: `met-coal-price-rally`

**What it is.** India's rising steel production driving metallurgical coal imports and seaborne demand.

**Found through:** Trending demand, How it's sold

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(2 trends from 1 companies, 2 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x2)

**Positively affected (1):**

- `+` **BHP** (BHP Group Limited) — Higher Indian met coal imports lift seaborne demand and prices for BHP's coal. *(impact 4, found through Trending demand)*

**Evidence:**

- "India's imports of metallurgical coal (including coking coal and pulverised coal injection) are projected to rise 9% y-o-y to 83 million tonnes (mnt) in FY'26" — [mysteel.net, 2026-03-29](https://www.mysteel.net/news/5117586-indias-met-coal-imports-expected-to-rise-9-y-o-y-in-fy26-on-steel-production-growth) — **BHP**, trending demand *(trade press, industry body or named research house)*
- "Queensland PLV FOB prices rising from around US$230/t to a two-year high of US$265/t by month-end" — [woodmac.com, 2026-08-31](https://www.woodmac.com/reports/coal-metallurgical-coal-markets-the-fortnight-flash-150499674/) — **BHP**, how it's sold *(trade press, industry body or named research house)*

### 55. Oral GLP-1 competition

`oral-glp1-competition` — merged from: `oral-glp1-delivery-shift`

**What it is.** Multiple oral GLP-1 launches compete for new obesity patients and market share.

**Found through:** Trending demand, How it's sold

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(2 trends from 1 companies, 2 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x2)

**Two-sided or unclear (1):**

- `±` **NVO** (Novo Nordisk A/S) — Oral pill expands access but cannibalizes injectable and invites new competition. *(impact 4, found through Trending demand)*

**Evidence:**

- "Foundayo captured more than 30% of new patients in the U.S. market for oral obesity treatments" — [fiercepharma.com](https://www.fiercepharma.com/pharma/oral-glp-1-tracker-launch-trajectories-lilly-foundayo-novo-wegovy-pill) — **NVO**, how it's sold *(trade press, industry body or named research house)*
- "the pill delivers a disproportionate share of forward growth" — [pharmaceutical-technology.com, 2026-03-12](https://www.pharmaceutical-technology.com/analyst-comment/wegovy-portfolio-growth-pill/) — **NVO**, trending demand *(trade press, industry body or named research house)*

### 56. Adult pneumococcal vaccine demand

`adult-pneumococcal-vaccine-demand`

**What it is.** Sustained adult pneumococcal vaccination is driving vaccine market growth and leadership shifts.

**Found through:** Trending demand | **Revenue streams touched:** Primary Care

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **PFE** (Pfizer Inc.) — Higher Prevnar demand lifts Primary Care vaccine revenue and market share. *(impact 4, found through Trending demand, stream: Primary Care)*

**Evidence:**

- "sustained adult pneumococcal vaccination demand" — [chemlifeintel.com, 2026-06-26](https://chemlifeintel.com/intelligence/pfizer-prevnar-overtakes-merck-gardasil-global-vaccine-market-leadership) — **PFE**, trending demand of Primary Care *(trade press, industry body or named research house)*

### 57. Asian LNG demand decline

`asian-lng-demand-decline`

**What it is.** Asian LNG demand falls as high prices and supply disruptions cut consumption.

**Found through:** Trending demand

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Negatively affected (1):**

- `-` **TTE** (TotalEnergies SE) — Lower Asian offtake volumes reduce Integrated LNG sales and trading opportunities. *(impact 4, found through Trending demand)*

**Evidence:**

- "Analysts estimate Asian LNG demand will fall 3% to 10% from 2025 levels in 2026" — [reuters.com, 2026-09-17](https://www.reuters.com/business/energy/asian-lng-demand-set-fall-second-year-war-shrinks-supply-2026-09-17/) — **TTE**, trending demand *(general media)*

### 58. Connector pricing upcycle

`connector-pricing-upcycle`

**What it is.** Connector suppliers are raising prices as demand and lead times tighten across the electronics channel.

**Found through:** How it's sold

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **APH** (Amphenol Corporation) — Price increases lift revenue and margin across connector product lines. *(impact 4, found through How it's sold)*

**Evidence:**

- "TE/Amphenol leading second round of channel price increase YTD (+7-8% effective 3/2)" — [tti.com](https://www.tti.com/content/ttiinc/en/resources/marketeye/categories/supply-chain/me-reed-20260310.html) — **APH**, how it's sold *(trade press, industry body or named research house)*

### 59. Connector raw material cost inflation

`connector-raw-material-cost-inflation`

**What it is.** Rising copper, gold and silver prices raise input costs for connector manufacturers.

**Found through:** How it's made

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **APH** (Amphenol Corporation) — Higher metal input costs squeeze gross margin unless passed through in pricing. *(impact 4, found through How it's made)*

**Evidence:**

- "gold prices passed $5,000 per ounce, silver prices passed $100 an ounce, and copper reached $13,300 per ton" — [connectorsupplier.com, 2026-03-03](https://connectorsupplier.com/high-materials-costs-squeeze-connector-manufacturers/) — **APH**, how it's made *(trade press, industry body or named research house)*

### 60. Copper concentrate TC/RC collapse

`copper-concentrate-tcrc-collapse`

**What it is.** Treatment and refining charges for copper concentrate falling to zero or negative, shifting bargaining power to miners.

**Found through:** How it's sold

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **BHP** (BHP Group Limited) — Negative TC/RCs mean smelters pay miners, lifting BHP's concentrate sales realisations. *(impact 4, found through How it's sold)*

**Evidence:**

- "Spot treatment and refining charges (TC/RCs) for copper concentrate have fallen deep into negative territory" — [lmeinsight.com, 2026-06-25](https://www.lmeinsight.com/coppers-benchmark-is-breaking-down-and-a-replacement-is-already-emerging/) — **BHP**, how it's sold *(trade press, industry body or named research house)*

### 61. CTV ad spend growth

`ctv-ad-spend-growth`

**What it is.** Connected TV advertising spend growing as budgets shift from linear television.

**Found through:** How it's sold | **Revenue streams touched:** Advertising

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **NFLX** (Netflix, Inc.) — More CTV ad dollars expand demand for Netflix's ad inventory and pricing. *(impact 4, found through How it's sold, stream: Advertising)*

**Evidence:**

- "Connected TV ad spend surpassed $46 billion in total upfront commitments across major streaming platforms this cycle" — [ad-times.com, 2026-09-05](https://ad-times.com/ctv-ad-spend-hits-46b-as-upfront-deals-reshape-buyer-power/) — **NFLX**, how it's sold of Advertising *(trade press, industry body or named research house)*

### 62. CTV upfront decline

`ctv-upfront-decline`

**What it is.** Connected TV upfront advertising commitments and pricing declining after years of growth.

**Found through:** How it's sold | **Revenue streams touched:** Advertising

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **NFLX** (Netflix, Inc.) — Falling upfront commitments and CPMs pressure Netflix's advertising revenue growth. *(impact 4, found through How it's sold, stream: Advertising)*

**Evidence:**

- "total CTV upfront commitments for the 2026–2027 broadcast year came in roughly 11 percent below the prior cycle" — [ad-times.com, 2026-07-07](https://ad-times.com/ctvs-upfront-collapse-is-exposing-streamings-ad-math-problem/) — **NFLX**, how it's sold of Advertising *(trade press, industry body or named research house)*

### 63. Delivery platform commission pressure

`delivery-platform-commission-pressure`

**What it is.** Restaurants face high delivery app commissions, pushing some toward direct ordering.

**Found through:** How it's sold

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Two-sided or unclear (1):**

- `±` **UBER** (Uber Technologies, Inc.) — High take rates lift Delivery revenue but risk merchant churn to direct ordering channels. *(impact 4, found through How it's sold)*

**Evidence:**

- "Uber Eats charges 20%, 25%, or 30% for delivery and 7% for pickup." — [directorders.com, 2026-08-18](https://www.directorders.com/blog/delivery-app-commission-rates-2026) — **UBER**, how it's sold *(general media)*

### 64. Freight broker margin compression

`freight-broker-margin-compression`

**What it is.** Rising carrier costs outpace customer pricing, squeezing freight brokerage gross margins.

**Found through:** How it's made

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Negatively affected (1):**

- `-` **UBER** (Uber Technologies, Inc.) — Rising carrier costs outpace customer pricing, compressing Uber Freight gross margin. *(impact 4, found through How it's made)*

**Evidence:**

- "revenue increased 49% and loads increased 19%, but purchased transportation expense increased 54% and gross margin fell from 15.5% to 12.5%" — [arktms.com, 2026-07-16](https://arktms.com/blog/freight-broker-margin-compression-purchased-transportation-costs-2026) — **UBER**, how it's made *(general media)*

### 65. Gig insurance costs decline

`gig-platform-insurance-cost-decline`

**What it is.** Insurance expense per gig trip falls, lowering a major platform cost layer.

**Found through:** How it's made

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **UBER** (Uber Technologies, Inc.) — Lower insurance expense per ride improves Uber Mobility contribution margin. *(impact 4, found through How it's made)*

**Evidence:**

- "From Q1 2025 to Q1 2026, average insurance expense per ride fell 5.1% on Uber rides" — [thecurbivore.com, 2026-07-23](https://www.thecurbivore.com/p/gig-platforms-gain-as-insurance-costs) — **UBER**, how it's made *(trade press, industry body or named research house)*

### 66. PC and console market maturity

`pc-console-market-maturity`

**What it is.** PC and console gaming growth slows as hardware cycles stretch and players become more selective.

**Found through:** Trending demand | **Revenue streams touched:** Game & Network Services

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **SONY** (Sony Group Corporation) — Slower PC/console growth pressures Sony's console hardware and game software revenue. *(impact 4, found through Trending demand, stream: Game & Network Services)*

**Evidence:**

- "The PC and console market is not in decline, but it is no longer the growth engine it once was." — [investgame.net, 2026-03-01](https://investgame.net/wp-content/uploads/2026/03/2026-03-12-newzoo_2026_pc_and_console_gaming_report_wp.pdf) — **SONY**, trending demand of Game & Network Services *(trade press, industry body or named research house)*

### 67. Recorded music streaming growth

`recorded-music-streaming-growth`

**What it is.** Paid streaming subscriptions drive global recorded music revenue growth.

**Found through:** Trending demand | **Revenue streams touched:** Music

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **SONY** (Sony Group Corporation) — Higher streaming and subscription revenue lifts Sony Music's recorded music income. *(impact 4, found through Trending demand, stream: Music)*

**Evidence:**

- "Global recorded music revenues grew 6.4% and reached US$31.7 billion in 2025" — [ifpi.org, 2026-03-01](https://www.ifpi.org/global-music-report-2026-global-recorded-music-revenues-grow-6-4-as-record-companies-drive-innovation/) — **SONY**, trending demand of Music *(trade press, industry body or named research house)*

### 68. Refinery throughput disruption

`refinery-throughput-disruption`

**What it is.** Global refinery crude throughput falls due to supply disruptions and feedstock shortages.

**Found through:** How it's made

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **TTE** (TotalEnergies SE) — Lower throughput reduces volumes even as high margins partially offset the impact. *(impact 4, found through How it's made)*

**Evidence:**

- "Refinery crude throughputs are forecast to plunge by 4.5 mb/d in 2Q26" — [iea.blob.core.windows.net, 2026-09-01](https://iea.blob.core.windows.net/assets/2b89a47b-34a2-40e0-90ff-68f7ccd80715/-13MAY2026__OilMarketReport_publicversion.pdf) — **TTE**, how it's made *(trade press, industry body or named research house)*

### 69. Smartphone upgrade cycle extension

`smartphone-upgrade-cycle-extension`

**What it is.** Consumers hold smartphones longer, reducing device upgrade volumes across carriers and OEMs.

**Found through:** Trending demand

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **VZ** (Verizon Communications Inc.) — Longer replacement cycles reduce device upgrade volumes, pressuring Verizon's wireless equipment revenue. *(impact 4, found through Trending demand)*

**Evidence:**

- "Smartphone replacement cycles are extending to four years, with this trend expected to continue through 2026 and 2027" — [counterpointresearch.com, 2026-08-13](https://counterpointresearch.com/q1-2026-report.pdf/reports/memory-crisis-pushes-global-smartphone%20replacement-cycles-toward-4-years) — **VZ**, trending demand *(trade press, industry body or named research house)*

### 70. US beer demand expansion

`us-beer-demand-expansion`

**What it is.** US beer distributor purchasing rises above expansion threshold, signaling demand recovery.

**Found through:** How it's sold | **Revenue streams touched:** Beer Business

**Quantum.** size **4.0**, speed **5.0**, impact **4.0** → quantum **4.30** × breadth factor **1.00** = **4.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **BUD** (Anheuser-Busch InBev SA/NV) — Stronger distributor purchasing supports AB InBev's US beer volumes and channel sell-through. *(impact 4, found through How it's sold, stream: Beer Business)*

**Evidence:**

- "The July reading of 51 marks the fifth consecutive reading at or above 50" — [nbwa.org, 2026-07-30](https://nbwa.org/press-release/beer-industry-maintains-expansionary-footing/) — **BUD**, how it's sold of Beer Business *(trade press, industry body or named research house)*

### 71. Financial services distribution shift

`financial-services-distribution-shift` — merged from: `financial-services-tech-spending-growth`

**What it is.** Changing distribution channels and client expectations in wealth and insurance markets.

**Found through:** How it's sold, How it's made | **Revenue streams touched:** Wealth Management & Insurance

**Quantum.** size **3.7**, speed **3.7**, impact **3.3** → quantum **3.57** × breadth factor **1.20** = **4.28**  
(3 trends from 3 companies, 3 sources, rating dispersion 1.67; sources: trade press, industry body or named research house x3)

**Positively affected (1):**

- `+` **SAN** (Banco Santander, S.A.) — Holistic planning demand supports wealth management and insurance fee income. *(impact 3, found through How it's sold, stream: Wealth Management & Insurance)*

**Negatively affected (1):**

- `-` **BAC** (Bank of America Corporation) — Higher technology spending raises operating costs across the bank. *(impact 3, found through How it's made)*

**Two-sided or unclear (1):**

- `±` **UBS** (UBS Group AG) — UBS can leverage wealth distribution but must invest in systems to compete. *(impact 4, found through How it's sold)*

**Evidence:**

- "growing demand for holistic planning" — [limra.com](https://www.limra.com/en/newsroom/industry-trends/2026/limra-six-forces-reshaping-financial-services-distribution/) — **SAN**, how it's sold of Wealth Management & Insurance *(trade press, industry body or named research house)*
- "distribution has replaced investment performance as the primary competitive advantage" — [bcg.com, 2026-04-28](https://www.bcg.com/publications/2026/distribution-is-the-new-source-of-advantage) — **UBS**, how it's sold *(trade press, industry body or named research house)*
- "US financial services tech budgets, including staff costs, to reach $495 billion in 2026" — [forrester.com, 2026-02-10](https://www.forrester.com/report/us-tech-forecast-2026-what-it-means-for-financial-services/RES191756) — **BAC**, how it's made *(trade press, industry body or named research house)*

### 72. Converged connectivity demand

`converged-connectivity-demand`

**What it is.** Customers bundle fiber, fixed wireless, and postpaid wireless into single accounts, driving net adds and reducing churn.

**Found through:** Trending demand

**Quantum.** size **3.0**, speed **5.0**, impact **5.0** → quantum **4.20** × breadth factor **1.00** = **4.20**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: company disclosure x1)

**Positively affected (1):**

- `+` **T** (AT&T Inc.) — More converged subscribers lift service revenue and reduce churn. *(impact 5, found through Trending demand)*

**Evidence:**

- "AT&T adds more than 1 million Advanced Connectivity customers, driven by year-over-year increases in net adds across fiber, fixed wireless, and postpaid phone subscribers" — [newswire.telecomramblings.com, 2026-07-01](https://newswire.telecomramblings.com/2026/07/att-delivers-strong-second-quarter-results-as-investment-led-strategy-gains-momentum/) — **T**, trending demand *(company disclosure)*

### 73. Utility rate base growth

`utility-rate-base-growth`

**What it is.** Regulated utilities seek rate increases to fund capital investment and grow revenue.

**Found through:** How it's sold | **Revenue streams touched:** FPL

**Quantum.** size **3.0**, speed **5.0**, impact **5.0** → quantum **4.20** × breadth factor **1.00** = **4.20**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Positively affected (1):**

- `+` **NEE** (NextEra Energy, Inc.) — Approved rate increases raise FPL revenue and return on equity. *(impact 5, found through How it's sold, stream: FPL)*

**Evidence:**

- "FPL has requested an increase in its retail rates and charges to generate $1.55 billion in additional gross annual revenue, effective January 1, 2026." — [psc.state.fl.us, 2026-01-01](https://www.psc.state.fl.us/library/filings/2025/02690-2025/02690-2025.pdf) — **NEE**, how it's sold of FPL *(general media)*

### 74. Global beverage alcohol volume decline

`global-beverage-alcohol-volume-decline` — merged from: `rtd-beverage-alcohol-growth`

**What it is.** Global alcohol consumption volumes fall for years before recovering, shifting demand across regions.

**Found through:** Trending demand | **Revenue streams touched:** Non-beer Business

**Quantum.** size **4.0**, speed **5.0**, impact **3.5** → quantum **4.15** × breadth factor **1.00** = **4.15**  
(2 trends from 1 companies, 2 sources, rating dispersion 1.00; sources: trade press, industry body or named research house x2)

**Two-sided or unclear (1):**

- `±` **BUD** (Anheuser-Busch InBev SA/NV) — RTD growth lifts AB InBev's Beyond Beer and non-beer revenue stream. *(impact 3, found through Trending demand, stream: Non-beer Business)*

**Evidence:**

- "IWSR forecasts global beverage alcohol consumption volume to decline for a further six years before resuming growth in 2031." — [theiwsr.com, 2026-06-11](https://www.theiwsr.com/insight/press-release/global-beverage-alcohol-to-drop-further-before-recovering/) — **BUD**, trending demand *(trade press, industry body or named research house)*
- "total RTD volumes were up by 3% in 2025" — [thespiritsbusiness.com, 2026-06-01](https://www.thespiritsbusiness.com/2026/06/rtds-overtake-vodka-in-global-value/) — **BUD**, trending demand of Non-beer Business *(trade press, industry body or named research house)*

### 75. Electronic component supply tightness

`electronic-component-supply-tightness`

**What it is.** Tight supply and long lead times for electronic components raise costs and support pricing.

**Found through:** How it's made | **Revenue streams touched:** Game & Network Services

**Quantum.** size **3.0**, speed **5.0**, impact **3.5** → quantum **3.75** × breadth factor **1.10** = **4.12**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.33; sources: trade press, industry body or named research house x1, general media x1)

**Negatively affected (1):**

- `-` **SONY** (Sony Group Corporation) — Higher memory costs raise PlayStation console production costs and may force price increases. *(impact 4, found through How it's made, stream: Game & Network Services)*

**Two-sided or unclear (1):**

- `±` **APH** (Amphenol Corporation) — Tighter component supply can constrain production while supporting higher connector prices. *(impact 3, found through How it's made)*

**Evidence:**

- "Passives supply continue to tighten, most notably in Capacitors, lead times extending to 52w in some cases, price increases coming." — [tti.com, 2026-05-01](https://www.tti.com/content/ttiinc/en/resources/marketeye/categories/supply-chain/me-reed-20260602.html) — **APH**, how it's made *(trade press, industry body or named research house)*
- "Memory chip prices doubled in the first quarter alone from the previous quarter and are forecast to climb up to 63% in the current quarter" — [economictimes.indiatimes.com, 2026-08-07](https://economictimes.indiatimes.com/tech/artificial-intelligence/sony-nintendo-grapple-with-memory-price-surge-as-ai-boom-constrains-supply/articleshow/130962612.cms) — **SONY**, how it's made of Game & Network Services *(general media)*

### 76. Online food delivery growth

`online-food-delivery-growth` — merged from: `online-grocery-delivery-growth`, `online-delivery-competition`

**What it is.** Consumers keep shifting meal ordering online, expanding delivery platform order volumes.

**Found through:** Trending demand, How it's sold

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.00** = **4.10**  
(3 trends from 1 companies, 2 sources, rating dispersion 0.00; sources: vendor market-report page x3)

**Two-sided or unclear (1):**

- `±` **UBER** (Uber Technologies, Inc.) — More platforms and retailers compete for the same delivery wallet, pressuring Uber Eats share and fees. *(impact 4, found through How it's sold)*

**Evidence:**

- "Revenue in the Online Food Delivery market is projected to reach US$1.51tn in 2026." — [statista.com, 2026-06-01](https://www.statista.com/outlook/emo/online-food-delivery/worldwide/) — **UBER**, trending demand *(vendor market-report page)*
- "The Grocery Delivery market is expected to show a revenue growth of 9.8% in 2027." — [statista.com, 2026-06-01](https://www.statista.com/outlook/emo/online-food-delivery/worldwide/) — **UBER**, trending demand *(vendor market-report page)*
- "Online Food & Grocery Delivery Market to See Rise in Competition" — [htfmarketintelligence.com, 2026-02-09](https://www.htfmarketintelligence.com/report/global-online-food-grocery-delivery-market) — **UBER**, how it's sold *(vendor market-report page)*

### 77. Basel III capital relief

`basel-iii-capital-relief`

**What it is.** Revised bank capital rules reduce regulatory capital burdens, freeing capacity for lending and trading.

**Found through:** How it's made

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.00** = **4.10**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **UBS** (UBS Group AG) — Lower capital requirements free balance sheet capacity for trading and lending. *(impact 4, found through How it's made)*

**Evidence:**

- "Agencies’ Capital Proposals Seek to Reduce Regulatory Burden and Extend Capital Relief to the Banking Industry at Large" — [arnoldporter.com, 2026-03-01](https://www.arnoldporter.com/en/perspectives/advisories/2026/03/agencies-capital-proposals-seek-to-reduce-regulatory-burden) — **UBS**, how it's made *(trade press, industry body or named research house)*

### 78. Communications hardware component demand

`communications-hardware-component-demand`

**What it is.** Growth in communications infrastructure and networking increases demand for electronic components.

**Found through:** Trending demand

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.00** = **4.10**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **APH** (Amphenol Corporation) — Broad communications infrastructure spending lifts Communications Solutions revenue. *(impact 4, found through Trending demand)*

**Evidence:**

- "valued at US$ 162770 million in 2025 and is anticipated to reach US$ 234310 million by 2032" — [reports.valuates.com, 2026-02-04](https://reports.valuates.com/market-reports/QYRE-Auto-29H18413/global-electronic-components-for-communications) — **APH**, trending demand *(vendor market-report page)*

### 79. Copper demand growth

`copper-demand-growth`

**What it is.** Rising grid, EV and data-centre copper consumption expanding the refined copper market.

**Found through:** Trending demand

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.00** = **4.10**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **BHP** (BHP Group Limited) — Copper is 49.4% of revenue, so higher end-use demand supports prices and volumes. *(impact 4, found through Trending demand)*

**Evidence:**

- "The global copper market is estimated at USD 265.08 billion in 2026 and is forecast to expand at a CAGR of 6.8%" — [factmr.com, 2026-05-25](https://www.factmr.com/report/copper-market) — **BHP**, trending demand *(vendor market-report page)*

### 80. Cross-border wealth booking shift

`cross-border-wealth-booking-center-shift`

**What it is.** Cross-border wealth flows are shifting between booking centers, changing where wealth managers capture assets.

**Found through:** Trending demand

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.00** = **4.10**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **UBS** (UBS Group AG) — Shift in booking centers changes where UBS captures cross-border wealth flows. *(impact 4, found through Trending demand)*

**Evidence:**

- "Cross-border wealth reached $15.6 trillion in 2025, with the top ten booking centers accounting for more than 90% of new flows." — [bcg.com, 2026-05-27](https://www.bcg.com/publications/2026/global-wealth-growth-in-an-era-of-reordering) — **UBS**, trending demand *(trade press, industry body or named research house)*

### 81. Enterprise telecom services growth

`enterprise-telecom-services-growth`

**What it is.** Enterprise spending on managed network and connectivity services grows as businesses modernize communications infrastructure.

**Found through:** Trending demand

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.00** = **4.10**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **T** (AT&T Inc.) — AT&T Business sells managed and connectivity services into this growing enterprise pool. *(impact 4, found through Trending demand)*

**Evidence:**

- "Projected Size of 579.27 Billion USD by 2032 with a CAGR of 6.01%" — [pmarketresearch.com, 2026-06-22](https://pmarketresearch.com/it/telecom-enterprise-services-market/) — **T**, trending demand *(vendor market-report page)*

### 82. Global medicine demand growth

`global-medicine-demand-growth`

**What it is.** Global demand for medicines continues to grow at mid-single-digit rates through 2030.

**Found through:** Trending demand

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.00** = **4.10**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **PFE** (Pfizer Inc.) — A growing global medicine market expands the revenue pool Pfizer sells into. *(impact 4, found through Trending demand)*

**Evidence:**

- "The global medicine market is projected to grow at a 5% to 8% compound annual growth rate (CAGR) through 2030, reaching approximately $2.6 trillion." — [iqvia.com, 2026-03-01](https://www.iqvia.com/blogs/2026/03/iqvia-institutes-2026-forecast-global-medicine-use-stays-strong-despite-headwinds) — **PFE**, trending demand *(trade press, industry body or named research house)*

### 83. Japan silver economy wealth transfer

`japan-silver-economy-wealth-transfer`

**What it is.** Aging Japanese households shifting trillions from cash deposits into investments and inheritance.

**Found through:** Trending demand | **Revenue streams touched:** Asset Management/Investor Services

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.00** = **4.10**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Shift from cash deposits to investments expands addressable AUM and wealth fees. *(impact 4, found through Trending demand, stream: Asset Management/Investor Services)*

**Evidence:**

- "Individuals over 60 are estimated to hold more than 60% of the country's household financial assets" — [legal500.com, 2026-09-18](https://www.legal500.com/intelligence/japan/wealth-management/japan's-silver-economy-why-trust-banks-and-distributors-hold-the-key) — **MUFG**, trending demand of Asset Management/Investor Services *(trade press, industry body or named research house)*

### 84. Music fan economy expansion

`music-fan-economy-expansion`

**What it is.** Labels diversify beyond streaming into merchandise, live, and expanded rights.

**Found through:** Trending demand | **Revenue streams touched:** Music

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.00** = **4.10**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **SONY** (Sony Group Corporation) — Expanded rights and fan economy add higher-margin revenue for Sony Music. *(impact 4, found through Trending demand, stream: Music)*

**Evidence:**

- "Global recorded music retail revenues will grow by 62.9%, from $74.3 billion in 2025 to $121.1 billion by 2033" — [midiaresearch.com, 2026-08-13](https://www.midiaresearch.com/blog/global-recorded-music-retail-revenues-to-reach-1211-billion-by-2033) — **SONY**, trending demand of Music *(trade press, industry body or named research house)*

### 85. Oncology market growth

`oncology-market-growth`

**What it is.** Oncology remains the largest and fastest-growing pharmaceutical therapeutic area.

**Found through:** Trending demand | **Revenue streams touched:** Oncology

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.00** = **4.10**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **PFE** (Pfizer Inc.) — A larger oncology market supports Pfizer's Oncology revenue stream. *(impact 4, found through Trending demand, stream: Oncology)*

**Evidence:**

- "Oncology remains the largest therapeutic area by global market size" — [iqvia.com, 2026-07-01](https://www.iqvia.com/locations/emea/blogs/2026/07/oncology-innovation-2026-and-beyond) — **PFE**, trending demand of Oncology *(trade press, industry body or named research house)*

### 86. Syndicated loan market growth

`syndicated-loan-market-growth`

**What it is.** Expanding global syndicated loan issuance and outstandings.

**Found through:** Trending demand | **Revenue streams touched:** Global Corporate & Investment Banking

**Quantum.** size **5.0**, speed **3.0**, impact **4.0** → quantum **4.10** × breadth factor **1.00** = **4.10**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Larger syndicated loan market expands underwriting and lending fees for CIB. *(impact 4, found through Trending demand, stream: Global Corporate & Investment Banking)*

**Evidence:**

- "Market Size (2026) | USD 7.5 Trillion" — [mordorintelligence.com, 2026-09-06](https://www.mordorintelligence.com/industry-reports/syndicated-loans-market) — **MUFG**, trending demand of Global Corporate & Investment Banking *(vendor market-report page)*

### 87. Beverage system capacity investment

`beverage-system-capex`

**What it is.** Beverage makers invest in production and packaging assets to secure supply and cut costs.

**Found through:** How it's made | **Revenue streams touched:** Beer Business

**Quantum.** size **3.5**, speed **4.5**, impact **3.0** → quantum **3.65** × breadth factor **1.10** = **4.02**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.67; sources: trade press, industry body or named research house x2)

**Positively affected (2):**

- `+` **BUD** (Anheuser-Busch InBev SA/NV) — Full ownership of can plants improves cost efficiency and supply security for US beer. *(impact 3, found through How it's made, stream: Beer Business)*
- `+` **KO** (The Coca-Cola Company) — Expands US capacity and distribution, supporting volume growth but adding system capital intensity. *(impact 3, found through How it's made)*

**Evidence:**

- "AB InBev has announced the reacquisition of the remaining 49.9% minority stake in its U.S. metal container plant operations" — [inside.beer](https://www.inside.beer/news/detail/usa-ab-inbev-reclaims-us-packaging-assets-in-usd-3-billion-deal) — **BUD**, how it's made of Beer Business *(trade press, industry body or named research house)*
- "The Coca-Cola system plans to invest USD$10 billion in US infrastructure between 2026 and 2030" — [foodbeverage-outlook.com, 2026-09-16](https://www.foodbeverage-outlook.com/beverage-production/coca-cola-plans-usd10-billion-us-investment-as-economic-contribution-reaches-usd85-billion) — **KO**, how it's made *(trade press, industry body or named research house)*

### 88. AI rack copper-optics architecture

`ai-rack-copper-optics-architecture`

**What it is.** AI rack designs mix copper and optical links, determining connector content and technology mix.

**Found through:** Trending demand

**Quantum.** size **4.0**, speed **4.0**, impact **4.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **APH** (Amphenol Corporation) — Copper intra-rack dominance protects connector content in Communications Solutions. *(impact 4, found through Trending demand)*

**Evidence:**

- "hybrid copper/optics architectures persisting through at least next two AI rack generations, implying limited risk to copper content through CY28/29" — [tti.com, 2026-05-01](https://www.tti.com/content/ttiinc/en/resources/marketeye/categories/supply-chain/me-reed-20260602.html) — **APH**, trending demand *(trade press, industry body or named research house)*

### 89. Asset management fee compression

`asset-management-fee-compression`

**What it is.** Falling fees and rising costs compress margins across the asset management industry.

**Found through:** How it's sold

**Quantum.** size **4.0**, speed **4.0**, impact **4.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **UBS** (UBS Group AG) — Fee compression and rising costs squeeze Asset Management operating margins. *(impact 4, found through How it's sold)*

**Evidence:**

- "Fees are falling, costs are rising, and margins have not moved in 15 years." — [bcg.com, 2026-04-28](https://www.bcg.com/publications/2026/an-imperative-for-growth-and-the-new-economics-of-asset-management) — **UBS**, how it's sold *(trade press, industry body or named research house)*

### 90. Beer wholesale channel pressure

`beer-wholesale-channel-pressure`

**What it is.** Beer wholesalers face soft volumes, rising costs, and competition from other beverages.

**Found through:** How it's sold | **Revenue streams touched:** Beer Business

**Quantum.** size **4.0**, speed **5.0**, impact **3.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **BUD** (Anheuser-Busch InBev SA/NV) — Weak wholesaler economics can slow distribution and pressure AB InBev's US beer volumes. *(impact 3, found through How it's sold, stream: Beer Business)*

**Evidence:**

- "Revenue has been climbing at a CAGR of just 0.3% over the past five years, expanding 0.9% in 2026 to total $92.0 billion." — [ibisworld.com, 2026-05-01](https://www.ibisworld.com/united-states/industry/beer-wholesaling/991/) — **BUD**, how it's sold of Beer Business *(trade press, industry body or named research house)*

### 91. Copper by-product credit cost relief

`copper-byproduct-credit-cost-relief`

**What it is.** Precious-metal by-products lowering copper miners' net cash costs and cushioning input inflation.

**Found through:** How it's made

**Quantum.** size **4.0**, speed **4.0**, impact **4.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **BHP** (BHP Group Limited) — Lower net cash costs expand margins on BHP's copper production. *(impact 4, found through How it's made)*

**Evidence:**

- "Surging gold and silver by-product credits are set to pull global copper C1 plus sustaining costs lower in 2026" — [woodmac.com, 2026-06-29](https://www.woodmac.com/reports/metals-global-copper-mine-cost-summary-15725731/) — **BHP**, how it's made *(trade press, industry body or named research house)*

### 92. Data centre construction delays

`data-centre-construction-delays`

**What it is.** Data centre projects face delays and cancellations, slowing power demand growth.

**Found through:** Trending demand

**Quantum.** size **4.0**, speed **4.0**, impact **4.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **NEE** (NextEra Energy, Inc.) — Delays push out FPL large-load revenue and NEER offtake opportunities. *(impact 4, found through Trending demand)*

**Evidence:**

- "Only about 50-60% of data center capacity scheduled for the next one to two years is expected to come online on time" — [goldmansachs.com, 2026-05-20](https://www.goldmansachs.com/insights/articles/us-data-center-power-demand-projected-to-double-by-2027) — **NEE**, trending demand *(trade press, industry body or named research house)*

### 93. Equity capital markets rebound

`equity-capital-markets-rebound`

**What it is.** Equity underwriting fees are rising as IPO and follow-on activity revives.

**Found through:** Trending demand

**Quantum.** size **4.0**, speed **5.0**, impact **3.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Positively affected (1):**

- `+` **BAC** (Bank of America Corporation) — Revived equity issuance increases equity underwriting fees for investment banks. *(impact 3, found through Trending demand)*

**Evidence:**

- "equity fees jumped 60% to US$13.5 billion, amid a revival in initial public offerings" — [investmentexecutive.com, 2026-07-06](https://www.investmentexecutive.com/news/research-and-markets/first-half-delivers-fee-feast-for-investment-banks/) — **BAC**, trending demand *(general media)*

### 94. Functional beverage demand growth

`functional-beverage-demand`

**What it is.** Consumers increasingly buy drinks with functional health benefits, expanding beverage categories beyond refreshment.

**Found through:** Trending demand | **Revenue streams touched:** Water, Sports, Coffee & Tea

**Quantum.** size **4.0**, speed **4.0**, impact **4.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **KO** (The Coca-Cola Company) — Functional demand lifts KO's water, sports, coffee/tea and energy lines, supporting price/mix. *(impact 4, found through Trending demand, stream: Water, Sports, Coffee & Tea)*

**Evidence:**

- "Rising consumer preference for functional and health-oriented drinks across demographics is accelerating category diversification." — [morganreedinsights.com, 2026-06-01](https://www.morganreedinsights.com/us-non-alcoholic-beverages-market/) — **KO**, trending demand of Water, Sports, Coffee & Tea *(vendor market-report page)*

### 95. GLP-1 adherence and price sensitivity

`glp1-adherence-price-sensitivity`

**What it is.** Patient cost exposure and adherence friction limit sustained GLP-1 utilization and revenue.

**Found through:** Trending demand

**Quantum.** size **4.0**, speed **4.0**, impact **4.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **NVO** (Novo Nordisk A/S) — Poor adherence and payer friction reduce persistent refills and net revenue. *(impact 4, found through Trending demand)*

**Evidence:**

- "hitting a wall of attrition fueled by systemic hurdles and behavioral friction" — [cd103-www.iqvia.com, 2025-11-01](https://cd103-www.iqvia.com/locations/united-states/blogs/2025/11/patient-behavior-how-does-price-sensitivity-and-adherence-shape-the-glp-1-market) — **NVO**, trending demand *(trade press, industry body or named research house)*

### 96. GLP-1 expanded indications

`glp1-expanded-indications`

**What it is.** GLP-1 medicines gain use beyond diabetes, including obesity and cardiovascular risk reduction.

**Found through:** Trending demand

**Quantum.** size **4.0**, speed **4.0**, impact **4.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **NVO** (Novo Nordisk A/S) — Expanded indications broaden Ozempic's eligible patient population and payer coverage. *(impact 4, found through Trending demand)*

**Evidence:**

- "GLP-1 medicines are now used for more than diabetes treatment" — [biospace.com, 2026-09-08](https://www.biospace.com/press-releases/glp-1-drugs-market-ozempic-wegovy-and-mounjaro-fda-and-industry-insights-from-precedence-research) — **NVO**, trending demand *(vendor market-report page)*

### 97. GLP-1 Medicare coverage expansion

`glp1-medicare-coverage-expansion`

**What it is.** Medicare is adding limited GLP-1 obesity coverage and negotiated pricing, expanding access but pressuring prices.

**Found through:** How it's sold

**Quantum.** size **4.0**, speed **4.0**, impact **4.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **NVO** (Novo Nordisk A/S) — Broader Medicare access adds volume but negotiated prices may lower net revenue. *(impact 4, found through How it's sold)*

**Evidence:**

- "Medicare’s negotiated price for certain GLP-1 products beginning in 2027" — [kff.org, 2026-01-30](https://www.kff.org/medicare/recent-trends-in-glp-1-use-and-spending-in-medicare/) — **NVO**, how it's sold *(trade press, industry body or named research house)*

### 98. Japan inbound investment growth sectors

`japan-inbound-investment-growth-sectors`

**What it is.** Foreign investment into Japanese data centres, AI, chips and defence sectors.

**Found through:** Trending demand | **Revenue streams touched:** Japanese Corporate & Investment Banking Business Group

**Quantum.** size **4.0**, speed **4.0**, impact **4.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Positively affected (1):**

- `+` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Inbound deals and financing in growth sectors lift Japanese CIB advisory and lending revenue. *(impact 4, found through Trending demand, stream: Japanese Corporate & Investment Banking Business Group)*

**Evidence:**

- "There are opportunities in growth areas such as data centres as well as the strategic sectors promoted by Prime Minister Takaichi, which include AI, chips and defence" — [dealstreetasia.com, 2026-09-16](https://www.dealstreetasia.com/stories/mizuho-securities-banks-on-japan-inbound-investments-to-drive-revenue-growth-495273) — **MUFG**, trending demand of Japanese Corporate & Investment Banking Business Group *(general media)*

### 99. Oil and gas labour cost pressure

`oil-gas-labour-cost-and-skills-gap`

**What it is.** An aging workforce and high turnover raise labour costs across oil and gas operations.

**Found through:** How it's made | **Revenue streams touched:** Upstream

**Quantum.** size **4.0**, speed **4.0**, impact **4.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Negatively affected (1):**

- `-` **SHEL** (Shell plc) — Rising labour costs and turnover inflate Upstream operating expenses. *(impact 4, found through How it's made, stream: Upstream)*

**Evidence:**

- "Labor accounts for 25 to 40 percent of total upstream operating expenditures" — [stealthagents.com, 2026-06-18](https://stealthagents.com/research/oil-and-gas-industry-staffing-costs-2026) — **SHEL**, how it's made of Upstream *(general media)*

### 100. Short-form drama competition

`short-form-drama-competition`

**What it is.** Short-form, often AI-made, drama formats competing for viewer attention and subscription spending.

**Found through:** Trending demand | **Revenue streams touched:** Monthly memberships

**Quantum.** size **4.0**, speed **5.0**, impact **3.0** → quantum **4.00** × breadth factor **1.00** = **4.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Negatively affected (1):**

- `-` **NFLX** (Netflix, Inc.) — Short dramas compete for the same viewer attention, potentially reducing time spent on Netflix. *(impact 3, found through Trending demand, stream: Monthly memberships)*

**Evidence:**

- "Global in-app revenue from short-form dramas will more than double in a single year, rising to $7.8 billion" — [en.sedaily.com, 2026-09-13](https://en.sedaily.com/society/2026/09/13/ai-made-short-dramas-emerge-as-threat-to-netflix) — **NFLX**, trending demand of Monthly memberships *(general media)*

### 101. Commercial lending standards tightening

`commercial-lending-standards-tightening`

**What it is.** Banks tighten credit standards for commercial loans, restraining loan supply and volume.

**Found through:** Trending demand | **Revenue streams touched:** Commercial Banking, Net interest income

**Quantum.** size **3.0**, speed **4.5**, impact **3.5** → quantum **3.60** × breadth factor **1.10** = **3.96**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.67; sources: trade press, industry body or named research house x2)

**Negatively affected (2):**

- `-` **BBVA** (Banco Bilbao Vizcaya Argentaria, S.A.) — Tighter credit standards restrain loan supply and volume growth in BBVA's European markets. *(impact 3, found through Trending demand, stream: Net interest income)*
- `-` **WFC** (Wells Fargo & Company) — Tighter standards can slow commercial loan growth and related fee income at WFC's Commercial Banking unit. *(impact 4, found through Trending demand, stream: Commercial Banking)*

**Evidence:**

- "euro area banks reported a moderate net tightening of credit standards for loans or credit lines to firms (net percentage of banks of 7%" — [ecb.europa.eu, 2026-07-15](https://www.ecb.europa.eu/stats/ecb_surveys/bank_lending_survey/html/ecb.blssurvey2026q2~baa6b60429.et.html) — **BBVA**, trending demand of Net interest income *(trade press, industry body or named research house)*
- "tighter lending standards for commercial and industrial (C&I) loans to firms of all sizes" — [federalreserve.gov, 2026-02-02](https://www.federalreserve.gov/data/sloos/sloos-202601.htm) — **WFC**, trending demand of Commercial Banking *(trade press, industry body or named research house)*

### 102. EV charging changes forecourt economics

`ev-charging-forecourt-dwell-time`

**What it is.** Longer EV charging stops shift convenience retail from quick fuel transactions to longer visits.

**Found through:** Trending demand, How it's sold | **Revenue streams touched:** Marketing

**Quantum.** size **3.0**, speed **4.5**, impact **3.5** → quantum **3.60** × breadth factor **1.10** = **3.96**  
(2 trends from 2 companies, 1 sources, rating dispersion 0.67; sources: trade press, industry body or named research house x2)

**Two-sided or unclear (2):**

- `±` **SHEL** (Shell plc) — Longer EV stops can lift convenience sales but displace faster fuel transactions. *(impact 4, found through How it's sold, stream: Marketing)*
- `±` **TTE** (TotalEnergies SE) — Longer dwell time can lift convenience sales but requires new forecourt investment. *(impact 3, found through Trending demand)*

**Evidence:**

- "EV charging sessions typically last around 30 minutes." — [nacsmagazine.com, 2026-08-01](https://nacsmagazine.com/issues/august-2026/catering-to-ev-drivers) — **SHEL**, how it's sold of Marketing *(trade press, industry body or named research house)*
- "EV charging sessions typically last around 30 minutes" — [nacsmagazine.com, 2026-08-01](https://nacsmagazine.com/issues/august-2026/catering-to-ev-drivers) — **TTE**, trending demand *(trade press, industry body or named research house)*

### 103. Carbonated soft drink per-capita decline

`csd-per-capita-decline`

**What it is.** Per-person consumption of sugary carbonated drinks falls in mature markets, pressuring volume.

**Found through:** Trending demand | **Revenue streams touched:** Sparkling Soft Drinks

**Quantum.** size **3.0**, speed **5.0**, impact **4.0** → quantum **3.90** × breadth factor **1.00** = **3.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Negatively affected (1):**

- `-` **KO** (The Coca-Cola Company) — Limits US volume growth in KO's largest CSD market, forcing reliance on price/mix. *(impact 4, found through Trending demand, stream: Sparkling Soft Drinks)*

**Evidence:**

- "per capita consumption has declined by roughly 10–15%" — [indexbox.io, 2026-08-19](https://www.indexbox.io/store/united-states-soda-pop-market-analysis-forecast-size-trends-and-insights/) — **KO**, trending demand of Sparkling Soft Drinks *(vendor market-report page)*

### 104. COVID product demand decline

`covid-product-demand-decline`

**What it is.** Demand for COVID-19 vaccines and antivirals is falling as pandemic-era purchasing fades.

**Found through:** Trending demand | **Revenue streams touched:** Primary Care

**Quantum.** size **3.0**, speed **5.0**, impact **4.0** → quantum **3.90** × breadth factor **1.00** = **3.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Negatively affected (1):**

- `-` **PFE** (Pfizer Inc.) — Lower COVID product revenue directly reduces Primary Care sales and total company revenue. *(impact 4, found through Trending demand, stream: Primary Care)*

**Evidence:**

- "Growth in Eliquis, Padcev, the Vyndaqel family and Lorbrena offset steep declines in COVID-19 products." — [finance.yahoo.com, 2026-08-04](https://finance.yahoo.com/healthcare/articles/pfe-q2-earnings-top-2026-154400421.html) — **PFE**, trending demand of Primary Care *(general media)*

### 105. Fiber buildout acceleration

`fiber-buildout-acceleration`

**What it is.** Operators accelerate fiber network construction to expand broadband coverage and service revenue.

**Found through:** How it's made

**Quantum.** size **3.0**, speed **5.0**, impact **4.0** → quantum **3.90** × breadth factor **1.00** = **3.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **T** (AT&T Inc.) — Faster fiber build expands service footprint but raises near-term capital and labor costs. *(impact 4, found through How it's made)*

**Evidence:**

- "AT&T will raise its fiber run-rate to 4 million locations in 2026, and expand that to 5 million locations annually through the end of the decade." — [lightreading.com, 2026-01-28](https://www.lightreading.com/broadband/at-t-ramping-up-fiber-buildout-pace-as-it-closes-in-on-lumen) — **T**, how it's made *(trade press, industry body or named research house)*

### 106. LNG trading gains from volatility

`lng-trading-optimisation-volatility`

**What it is.** Price volatility and supply disruption create trading and optimisation opportunities for LNG portfolio players.

**Found through:** How it's sold | **Revenue streams touched:** Integrated Gas

**Quantum.** size **3.0**, speed **5.0**, impact **4.0** → quantum **3.90** × breadth factor **1.00** = **3.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: company disclosure x1)

**Positively affected (1):**

- `+` **SHEL** (Shell plc) — Volatile LNG markets boost trading and optimisation margins. *(impact 4, found through How it's sold, stream: Integrated Gas)*

**Evidence:**

- "Trading & Optimisation is expected to be significantly higher than Q1 2026" — [stocktitan.net, 2026-07-30](https://www.stocktitan.net/sec-filings/SHEL/6-k-shell-plc-current-report-foreign-issuer-fe4eee4bcd50.html) — **SHEL**, how it's sold of Integrated Gas *(company disclosure)*

### 107. Non-COVID innovative drug growth

`non-covid-innovative-drug-growth`

**What it is.** Sales of non-COVID innovative medicines are growing and offsetting pandemic product declines.

**Found through:** Trending demand

**Quantum.** size **3.0**, speed **5.0**, impact **4.0** → quantum **3.90** × breadth factor **1.00** = **3.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Positively affected (1):**

- `+` **PFE** (Pfizer Inc.) — These non-COVID drugs support total revenue and offset declining COVID product sales. *(impact 4, found through Trending demand)*

**Evidence:**

- "Growth in Eliquis, Padcev, the Vyndaqel family and Lorbrena offset steep declines in COVID-19 products." — [finance.yahoo.com, 2026-08-04](https://finance.yahoo.com/healthcare/articles/pfe-q2-earnings-top-2026-154400421.html) — **PFE**, trending demand *(general media)*

### 108. Optical fiber price inflation

`optical-fiber-price-inflation`

**What it is.** Tight preform supply and strong broadband/AI demand drive sharp increases in optical fiber prices.

**Found through:** How it's made

**Quantum.** size **3.0**, speed **5.0**, impact **4.0** → quantum **3.90** × breadth factor **1.00** = **3.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **T** (AT&T Inc.) — Higher fiber input costs raise AT&T's network buildout and maintenance expenses. *(impact 4, found through How it's made)*

**Evidence:**

- "Chinese G.562.D bare fibre prices surged by more than 80% between November 2025 and January 2026" — [crugroup.com, 2026-02-26](https://www.crugroup.com/en/communities/thought-leadership/2026/optical-fibre-prices-rise-as-preform-availability-tightens/) — **T**, how it's made *(trade press, industry body or named research house)*

### 109. Streaming price increases

`streaming-price-increases`

**What it is.** Streaming services raising retail prices to lift average revenue per user.

**Found through:** How it's sold | **Revenue streams touched:** Monthly memberships

**Quantum.** size **3.0**, speed **5.0**, impact **4.0** → quantum **3.90** × breadth factor **1.00** = **3.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **NFLX** (Netflix, Inc.) — Higher prices lift average revenue per user, directly boosting membership revenue. *(impact 4, found through How it's sold, stream: Monthly memberships)*

**Evidence:**

- "is rising by $2, from $17.99 to $19.99/month" — [variety.com, 2026-03-27](https://variety.com/2026/biz/news/why-netflix-hiked-prices-explained-chart-1236701365/) — **NFLX**, how it's sold of Monthly memberships *(trade press, industry body or named research house)*

### 110. Telecom ARPU rises but core prices flat

`telecom-arpu-affordability-paradox`

**What it is.** Reported wireless ARPU climbs while underlying connectivity prices stay flat, constraining service revenue growth.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **5.0**, impact **4.0** → quantum **3.90** × breadth factor **1.00** = **3.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **T** (AT&T Inc.) — Flat core prices limit service revenue growth even as reported ARPU rises from bundled perks. *(impact 4, found through How it's sold)*

**Evidence:**

- "Blended across AT&T, T-Mobile and Verizon, postpaid phone ARPU rose from $53.22 in the second half of 2022 to $56.37 in early 2026, a roughly 6% rise." — [lightreading.com, 2026-06-04](https://www.lightreading.com/oss-bss-cx/the-affordability-paradox-telecom-claims-less-of-the-wallet-even-as-arpu-climbs) — **T**, how it's sold *(trade press, industry body or named research house)*

### 111. Transformer supply shortage

`transformer-supply-shortage`

**What it is.** Power transformer shortages and long lead times constrain grid and generation projects.

**Found through:** How it's made

**Quantum.** size **3.0**, speed **5.0**, impact **4.0** → quantum **3.90** × breadth factor **1.00** = **3.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **NEE** (NextEra Energy, Inc.) — Long lead times delay FPL and NEER capital projects and raise equipment costs. *(impact 4, found through How it's made)*

**Evidence:**

- "Power transformer and GSUs are seeing sustained lead times of 2 to 3 years." — [powermag.com, 2026-01-01](https://www.powermag.com/wp-content/uploads/2026/01/making-the-connection-executive-summary-september-2025.pdf) — **NEE**, how it's made *(trade press, industry body or named research house)*

### 112. Utility large-load tariffs

`utility-large-load-tariffs`

**What it is.** Regulated utilities create special tariffs to serve data centres and other large loads.

**Found through:** How it's sold | **Revenue streams touched:** FPL

**Quantum.** size **3.0**, speed **5.0**, impact **4.0** → quantum **3.90** × breadth factor **1.00** = **3.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **NEE** (NextEra Energy, Inc.) — Enables FPL to contract with large loads, supporting revenue and capital recovery. *(impact 4, found through How it's sold, stream: FPL)*

**Evidence:**

- "FPL's tariff was approved in November of last year and took effect on January 1, 2026." — [datacenterdynamics.com, 2026-07-28](https://www.datacenterdynamics.com/en/news/nextera-raises-data-center-forecast-to-8gw-by-2032-at-florida-subsidiary-fpl/) — **NEE**, how it's sold of FPL *(trade press, industry body or named research house)*

### 113. AI disruption in banking

`ai-disruption-banking-models`

**What it is.** AI is expected to significantly disrupt banking business and operating models, driving tech investment.

**Found through:** How it's sold, How it's made | **Revenue streams touched:** Retail & Commercial Banking

**Quantum.** size **3.0**, speed **3.0**, impact **3.7** → quantum **3.20** × breadth factor **1.20** = **3.84**  
(3 trends from 3 companies, 3 sources, rating dispersion 0.33; sources: trade press, industry body or named research house x2, general media x1)

**Negatively affected (2):**

- `-` **BBVA** (Banco Bilbao Vizcaya Argentaria, S.A.) — Loss of customer ownership can reduce cross-sell and fee income across BBVA. *(impact 4, found through How it's sold)*
- `-` **SAN** (Banco Santander, S.A.) — Loss of customer interface reduces retail cross-sell and fee income opportunities. *(impact 4, found through How it's sold, stream: Retail & Commercial Banking)*

**Two-sided or unclear (1):**

- `±` **BAC** (Bank of America Corporation) — AI may cut costs but requires investment and could disrupt existing revenue models. *(impact 3, found through How it's made)*

**Evidence:**

- "80% of banking executives now expect AI to significantly disrupt their business and operating models in the next three-five years" — [kpmg.com, 2026-06-17](https://kpmg.com/us/en/media/news/2026-banking-technology-survey.html) — **BAC**, how it's made *(trade press, industry body or named research house)*
- "warns that a new generation of fintechs, AI-driven disintermediation, and shifting customer trust threaten banks' control of client relationships." — [theledgerreview.com, 2026-09-05](https://theledgerreview.com/the-review/global-banking-2026-precision-speed-customer-relevance) — **BBVA**, how it's sold *(general media)*
- "Agentic AI increases the risk that banks lose the primary interface for saving, investing, and borrowing to third-party platforms" — [strategyand.pwc.com, 2026-07-06](https://www.strategyand.pwc.com/de/en/industries/financial-services/retail-banking-monitor.html) — **SAN**, how it's sold of Retail & Commercial Banking *(trade press, industry body or named research house)*

### 114. Clean energy development backlog

`clean-energy-development-backlog` — merged from: `clean-energy-ppa-price-inflation`

**What it is.** Renewables and storage developers are building large backlogs of contracted projects.

**Found through:** Trending demand, How it's sold | **Revenue streams touched:** NEER

**Quantum.** size **3.5**, speed **4.0**, impact **4.0** → quantum **3.80** × breadth factor **1.00** = **3.80**  
(2 trends from 1 companies, 2 sources, rating dispersion 0.33; sources: company disclosure x1, general media x1)

**Positively affected (1):**

- `+` **NEE** (NextEra Energy, Inc.) — Backlog converts into future NEER revenue as projects are built. *(impact 4, found through Trending demand, stream: NEER)*

**Evidence:**

- "NextEra Energy Resources has a strong quarter for new renewables and storage origination, adding 3.6 gigawatts to its backlog" — [last10k.com, 2026-07-24](https://last10k.com/sec-filings/37634/0000753308-26-000060.htm) — **NEE**, trending demand of NEER *(company disclosure)*
- "Average solar PPA prices in North America in Q4 2025 rose by 9% on the year to $61.7/MWh" — [reuters.com](https://www.reuters.com/business/energy/ai-power-dash-transforms-clean-energy-offtake-market--reeii-2026-03-17/) — **NEE**, how it's sold of NEER *(general media)*

### 115. Rare disease drug demand growth

`rare-disease-drug-demand-growth`

**What it is.** Demand for rare disease therapies is growing at double-digit rates.

**Found through:** Trending demand | **Revenue streams touched:** Specialty Care

**Quantum.** size **5.0**, speed **3.0**, impact **3.0** → quantum **3.80** × breadth factor **1.00** = **3.80**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **PFE** (Pfizer Inc.) — Growing rare disease drug demand supports Pfizer's Specialty Care revenue. *(impact 3, found through Trending demand, stream: Specialty Care)*

**Evidence:**

- "The Rare Disease Drugs Market size is anticipated to grow at a CAGR of 10.6%" — [coherentmarketinsights.com, 2026-06-05](https://www.coherentmarketinsights.com/market-insight/global-rare-disease-drugs-market-competitive-analysis-1200) — **PFE**, trending demand of Specialty Care *(vendor market-report page)*

### 116. Auto finance market growth

`auto-finance-market-growth`

**What it is.** Expansion of vehicle financing and leasing volumes across European markets.

**Found through:** Trending demand | **Revenue streams touched:** Digital Consumer Bank

**Quantum.** size **4.0**, speed **3.0**, impact **4.0** → quantum **3.70** × breadth factor **1.00** = **3.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **SAN** (Banco Santander, S.A.) — Growing auto finance volumes support Santander Consumer Finance's lending and interest income. *(impact 4, found through Trending demand, stream: Digital Consumer Bank)*

**Evidence:**

- "The Europe Auto Finance Market worth USD 124 billion in 2025 is growing at a CAGR of 6.74% to reach USD 184 billion by 2031." — [kenresearch.com, 2026-08-01](https://www.kenresearch.com/industry-reports/europe-auto-finance-market) — **SAN**, trending demand of Digital Consumer Bank *(vendor market-report page)*

### 117. BNPL consumer credit growth

`bnpl-consumer-credit-growth`

**What it is.** Growth and formal regulation of buy-now-pay-later consumer credit across markets.

**Found through:** Trending demand | **Revenue streams touched:** Digital Consumer Bank

**Quantum.** size **4.0**, speed **4.0**, impact **3.0** → quantum **3.70** × breadth factor **1.00** = **3.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Two-sided or unclear (1):**

- `±` **SAN** (Banco Santander, S.A.) — BNPL growth expands consumer credit demand, but tighter supervision may raise compliance costs and limit nonbank competition. *(impact 3, found through Trending demand, stream: Digital Consumer Bank)*

**Evidence:**

- "The BNPL payment market in Europe is expected to grow by 15.7% on annual basis to reach US$228.3 billion in 2026." — [researchandmarkets.com, 2026-07-15](https://www.researchandmarkets.com/report/europe-buy-now-pay-later-market) — **SAN**, trending demand of Digital Consumer Bank *(vendor market-report page)*

### 118. Oncology loss-of-exclusivity risk

`oncology-loss-of-exclusivity-risk`

**What it is.** Patent expiries and new modalities are intensifying competition in oncology.

**Found through:** How it's sold | **Revenue streams touched:** Oncology

**Quantum.** size **4.0**, speed **3.0**, impact **4.0** → quantum **3.70** × breadth factor **1.00** = **3.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **PFE** (Pfizer Inc.) — Loss of exclusivity and new competitors can erode Pfizer's oncology revenue. *(impact 4, found through How it's sold, stream: Oncology)*

**Evidence:**

- "Patent cliffs threaten today’s leaders, new modalities are taking share fast, and China has emerged as a serious force in development and commercialization." — [evaluate.com, 2026-07-23](https://www.evaluate.com/thought-leadership/oncology-market-forecast-next-decade/) — **PFE**, how it's sold of Oncology *(trade press, industry body or named research house)*

### 119. Streaming industry consolidation

`streaming-industry-consolidation`

**What it is.** Media consolidation creating larger streaming competitors through mergers.

**Found through:** How it's sold | **Revenue streams touched:** Monthly memberships

**Quantum.** size **4.0**, speed **3.0**, impact **4.0** → quantum **3.70** × breadth factor **1.00** = **3.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **NFLX** (Netflix, Inc.) — A larger combined rival competes for subscribers and content, pressuring Netflix's share. *(impact 4, found through How it's sold, stream: Monthly memberships)*

**Evidence:**

- "a combined HBO Max/Paramount+ platform could reach approximately 175 million subscribers globally by 2031" — [advanced-television.com, 2026-06-10](https://www.advanced-television.com/2026/06/10/forecast-netflix-to-strengthen-position-despite-industry-consolidation/) — **NFLX**, how it's sold of Monthly memberships *(trade press, industry body or named research house)*

### 120. Wireless infrastructure labour shortage

`wireless-infrastructure-labour-shortage`

**What it is.** A shrinking skilled workforce for tower and network construction raises costs and delays deployments.

**Found through:** How it's made

**Quantum.** size **4.0**, speed **4.0**, impact **3.0** → quantum **3.70** × breadth factor **1.00** = **3.70**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **VZ** (Verizon Communications Inc.) — Tighter skilled labor supply raises construction and maintenance costs for Verizon's network. *(impact 3, found through How it's made)*

**Evidence:**

- "workforce that contracted by more than 26,000 jobs in a single year" — [wirelessestimator.com, 2026-03-19](https://wirelessestimator.com/articles/2026/nearly-65b-158500-towers-and-a-shrinking-workforce-what-wias-2025-by-the-numbers-reveals/) — **VZ**, how it's made *(trade press, industry body or named research house)*

### 121. Connector supply chain nearshoring and tariffs

`connector-supply-chain-nearshoring-tariffs` — merged from: `pharma-supply-chain-cost-inflation`

**What it is.** Tariffs and trade rules push connector supply chains toward regional nearshoring.

**Found through:** How it's made

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.10** = **3.63**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.00; sources: vendor market-report page x1, trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **PFE** (Pfizer Inc.) — Higher input and logistics costs raise Pfizer's cost of goods and operating expenses. *(impact 3, found through How it's made)*

**Two-sided or unclear (1):**

- `±` **APH** (Amphenol Corporation) — Tariffs raise landed costs while nearshoring can improve regional supply resilience. *(impact 3, found through How it's made)*

**Evidence:**

- "evolving U.S. tariff policies introduce trade‑cost volatility and supply‑chain uncertainty" — [qyresearch.com, 2026-03-12](https://www.qyresearch.com/reports/6126665/ai-data-center-connectors) — **APH**, how it's made *(vendor market-report page)*
- "increases in oil and gas prices have raised manufacturing and transportation costs for pharmaceuticals." — [group.atradius.com, 2026-06-23](https://group.atradius.com/knowledge-and-research/reports/industry-trends-pharmaceuticals-june-2026) — **PFE**, how it's made *(trade press, industry body or named research house)*

### 122. Fuel retail volume softness

`fuel-retail-volume-softness`

**What it is.** Retail fuel demand is softening as prices and electric vehicles reduce volumes.

**Found through:** Trending demand | **Revenue streams touched:** Marketing

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.10** = **3.63**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.67; sources: company disclosure x1, trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **SHEL** (Shell plc) — Lower fuel volumes reduce Marketing revenue and earnings. *(impact 3, found through Trending demand, stream: Marketing)*

**Two-sided or unclear (1):**

- `±` **TTE** (TotalEnergies SE) — Stable fuel volumes support Marketing & Services cash flow while long-term decline caps growth. *(impact 3, found through Trending demand)*

**Evidence:**

- "sales volumes are expected in a slightly lower 2,550–2,650 kb/d range" — [stocktitan.net, 2026-07-30](https://www.stocktitan.net/sec-filings/SHEL/6-k-shell-plc-current-report-foreign-issuer-fe4eee4bcd50.html) — **SHEL**, trending demand of Marketing *(company disclosure)*
- "near-term demand will remain relatively sticky" — [c-storecanada.com, 2026-01-29](https://c-storecanada.com/attachments/article/644/2026%20North%20American%20Fuel%20Retail%20and%20Convenience%20Store%20Outlook.pdf) — **TTE**, trending demand *(trade press, industry body or named research house)*

### 123. AI backplane supplier concentration

`ai-backplane-supplier-concentration`

**What it is.** A small number of connector suppliers hold most AI backplane sockets, limiting second-source share.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **APH** (Amphenol Corporation) — Share concentration supports pricing and volume in Communications Solutions. *(impact 4, found through How it's sold)*

**Evidence:**

- "Amphenol likely to retain overwhelming majority of Nvidia backplane share further into 1H27. Second source initial share appears limited to 10%," — [passive-components.eu, 2026-07-01](https://passive-components.eu/july-2026-interconnect-passives-and-electromechanical-components-market-insights/) — **APH**, how it's sold *(trade press, industry body or named research house)*

### 124. Asset-light beverage franchising

`asset-light-beverage-franchising`

**What it is.** Beverage companies shift to franchise bottling to lower capital intensity and lift margins.

**Found through:** How it's made

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **KO** (The Coca-Cola Company) — Franchise-led structure lowers owned-asset risk and supports margin and cash flow. *(impact 4, found through How it's made)*

**Evidence:**

- "about 60 basis points of annual margin expansion and 93 percent cash conversion" — [supplychain360.io, 2026-02-18](https://supplychain360.io/operations/all-weather-supply-chain-brief/) — **KO**, how it's made *(trade press, industry body or named research house)*

### 125. Card interchange fee caps

`card-interchange-fee-caps`

**What it is.** Regulators cap card interchange fees, reducing issuer payment fee revenue.

**Found through:** How it's sold | **Revenue streams touched:** Fees and commissions

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Negatively affected (1):**

- `-` **BBVA** (Banco Bilbao Vizcaya Argentaria, S.A.) — Lower interchange fees reduce card payment fee revenue for BBVA Mexico. *(impact 4, found through How it's sold, stream: Fees and commissions)*

**Evidence:**

- "proposed updated regulations establishing phased caps on credit and debit card interchange fees" — [mexicobusiness.news, 2025-10-01](https://mexicobusiness.news/finance/news/banxico-cnbv-propose-phase-caps-card-interchange-fees) — **BBVA**, how it's sold of Fees and commissions *(general media)*

### 126. Coffee and tea commodity inflation

`coffee-tea-commodity-inflation`

**What it is.** Rising coffee and tea input costs squeeze margins for beverage makers.

**Found through:** How it's made | **Revenue streams touched:** Water, Sports, Coffee & Tea

**Quantum.** size **3.0**, speed **5.0**, impact **3.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **KO** (The Coca-Cola Company) — Higher tea and coffee input costs compress gross margin in that stream. *(impact 3, found through How it's made, stream: Water, Sports, Coffee & Tea)*

**Evidence:**

- "comparable gross margin still declined by around 30 basis points, mainly due to commodity pressures in tea and coffee" — [supplychain360.io, 2026-05-13](https://supplychain360.io/operations/coca-cola-all-weather-supply-chain/) — **KO**, how it's made of Water, Sports, Coffee & Tea *(trade press, industry body or named research house)*

### 127. Commercial loan demand strength

`commercial-loan-demand-strength`

**What it is.** Large and middle-market firms are seeking more commercial and industrial loans, supporting bank lending.

**Found through:** Trending demand | **Revenue streams touched:** Commercial Banking

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **WFC** (Wells Fargo & Company) — Higher commercial loan demand supports loan growth and net interest income in Commercial Banking. *(impact 4, found through Trending demand, stream: Commercial Banking)*

**Evidence:**

- "stronger demand for C&I loans to large and middle-market firms" — [federalreserve.gov, 2026-02-02](https://www.federalreserve.gov/data/sloos/sloos-202601.htm) — **WFC**, trending demand of Commercial Banking *(trade press, industry body or named research house)*

### 128. Consumer credit origination rebound

`consumer-credit-origination-rebound`

**What it is.** Mortgage and personal loan originations are rebounding, driving consumer credit expansion after prior lows.

**Found through:** Trending demand | **Revenue streams touched:** Consumer Banking and Lending

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **WFC** (Wells Fargo & Company) — Higher mortgage and personal loan originations support loan growth and fee income in Consumer Banking. *(impact 4, found through Trending demand, stream: Consumer Banking and Lending)*

**Evidence:**

- "mortgage and unsecured personal loans as the primary drivers of projected expansion." — [globenewswire.com, 2026-02-19](https://www.globenewswire.com/de/news-release/2026/02/19/3241073/0/en/TransUnion-2026-Originations-Forecast-Shows-Continued-Positive-Momentum-Amidst-Moderate-Expansion.html) — **WFC**, trending demand of Consumer Banking and Lending *(trade press, industry body or named research house)*

### 129. Freight rate inflation

`freight-rate-inflation`

**What it is.** Trucking capacity tightness raises freight rates, increasing distribution costs for shippers.

**Found through:** How it's made | **Revenue streams touched:** Beer Business

**Quantum.** size **3.0**, speed **5.0**, impact **3.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **BUD** (Anheuser-Busch InBev SA/NV) — Higher freight rates raise AB InBev's distribution costs and pressure beer margins. *(impact 3, found through How it's made, stream: Beer Business)*

**Evidence:**

- "Truckload contract rates are up 18% year over year as driver losses, diesel volatility and tighter capacity reshape the market" — [freightwaves.com, 2026-09-11](https://www.freightwaves.com/news/uber-freight-warns-tight-capacity-could-fuel-q4-freight-rate-surge) — **BUD**, how it's made of Beer Business *(trade press, industry body or named research house)*

### 130. Insulin tender pricing pressure

`insulin-tender-pricing-pressure`

**What it is.** Government tenders and discount agreements pressure insulin prices in public procurement markets.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **5.0**, impact **3.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **NVO** (Novo Nordisk A/S) — Tender-based procurement and discounts lower realized insulin prices in Europe. *(impact 3, found through How it's sold)*

**Evidence:**

- "For The Period January 1St, 2026 - December 31St, 2027" — [globaltenders.com, 2025-11-18](https://www.globaltenders.com/tender-detail/conclusion-of-a-non-exclusive-discount-agree-122505690) — **NVO**, how it's sold *(trade press, industry body or named research house)*

### 131. Japan life insurance channel shift

`japan-life-insurance-channel-shift`

**What it is.** Japanese life insurers see face-to-face sales regain share from bank channels.

**Found through:** How it's sold | **Revenue streams touched:** Financial Services

**Quantum.** size **3.0**, speed **5.0**, impact **3.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Positively affected (1):**

- `+` **SONY** (Sony Group Corporation) — Sony Life's face-to-face sales force benefits as customers seek support. *(impact 3, found through How it's sold, stream: Financial Services)*

**Evidence:**

- "2025年度は主要生保9社の営業職員が獲得した契約保険料が前の年度比25%増えた。銀行などの金融機関の窓口経由の保険料を逆転した。" — [nikkei.com](https://www.nikkei.com/article/DGKKZO96984950X10C26A6EE9000/) — **SONY**, how it's sold of Financial Services *(general media)*

### 132. Japan ultrawealthy wealth management

`japan-ultrawealthy-wealth-management`

**What it is.** Competition among Japanese banks for ultrawealthy clients as private fortunes rise.

**Found through:** How it's sold | **Revenue streams touched:** Commercial Banking & Wealth Management Business Group

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Two-sided or unclear (1):**

- `±` **MUFG** (Mitsubishi UFJ Financial Group, Inc.) — Rising private wealth lifts fee income but intensifies competition for the same wealthy clients. *(impact 4, found through How it's sold, stream: Commercial Banking & Wealth Management Business Group)*

**Evidence:**

- "Japan's biggest banks are stepping up efforts to win ultrawealthy clients, expanding dedicated teams and services as soaring stock and property prices boost private fortunes" — [asia.nikkei.com, 2026-08-17](https://asia.nikkei.com/business/markets/wealth-management/japan-s-megabanks-chase-ultrawealthy-as-fortunes-swell) — **MUFG**, how it's sold of Commercial Banking & Wealth Management Business Group *(general media)*

### 133. LNG contract flexibility shift

`lng-contract-flexibility-shift`

**What it is.** LNG buyers increasingly demand destination flexibility and shorter contracts, shifting risk to sellers.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **TTE** (TotalEnergies SE) — More flexible contracts can optimize TTE's portfolio but reduce long-term revenue visibility. *(impact 4, found through How it's sold)*

**Evidence:**

- "Supply diversification alongside contract duration and destination flexibility were already rising priorities for buyers" — [energyintel.com, 2026-09-17](https://www.energyintel.com/000001a0-a93a-dc4a-a1fb-edfb972f0000) — **TTE**, how it's sold *(trade press, industry body or named research house)*

### 134. Middle market earnings resilience

`middle-market-earnings-resilience`

**What it is.** Middle-market borrowers are confident in revenue and margin growth, supporting bank credit demand.

**Found through:** Trending demand | **Revenue streams touched:** Commercial Banking

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **WFC** (Wells Fargo & Company) — Healthier middle-market borrowers can sustain loan demand and lower credit losses for Commercial Banking. *(impact 4, found through Trending demand, stream: Commercial Banking)*

**Evidence:**

- "Most expect revenue growth in 2026, with an even stronger outlook for EBITDA growth and margin expansion." — [antares.com, 2026-06-01](https://www.antares.com/our-perspectives/market-insights/mid-year-2026-credit-market-outlook-survey/) — **WFC**, trending demand of Commercial Banking *(trade press, industry body or named research house)*

### 135. Oncology payer access controls

`oncology-payer-access-controls`

**What it is.** Payers are tightening access controls for oncology therapies to manage costs.

**Found through:** How it's sold | **Revenue streams touched:** Oncology

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **PFE** (Pfizer Inc.) — Tighter payer controls can restrict oncology drug access and pressure pricing. *(impact 4, found through How it's sold, stream: Oncology)*

**Evidence:**

- "economic pressures are reshaping oncology access across payers and providers." — [haydencg.com, 2026-03-01](https://haydencg.com/wp-content/uploads/2026/03/Hayden_Oncology-Part1.pdf) — **PFE**, how it's sold of Oncology *(trade press, industry body or named research house)*

### 136. Postpaid convergence pressures margins

`telecom-postpaid-convergence-margin-pressure`

**What it is.** Carriers bundle services and run heavy promotions, raising costs and compressing postpaid margins.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **T** (AT&T Inc.) — Promotional intensity and convergence raise acquisition and retention costs, compressing service margins. *(impact 4, found through How it's sold)*

**Evidence:**

- "Mobile service promotions remain at all-time highs with lots of parity" — [counterpointresearch.com, 2026-02-25](https://counterpointresearch.com/en/reports/state-of-us-postpaid-2026-the-year-of-convergence-and-shrinking-margins-for-us-postpaid-mnos) — **T**, how it's sold *(trade press, industry body or named research house)*

### 137. Private-label beverage competition

`private-label-beverage-competition`

**What it is.** Retailer-owned brands gain share, pressuring branded beverage pricing and volume.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Negatively affected (1):**

- `-` **KO** (The Coca-Cola Company) — Private label and health shifts can slow volume and limit price increases across KO's portfolio. *(impact 4, found through How it's sold)*

**Evidence:**

- "health pressure and private-label competition keep rising" — [soar-analysis.com, 2026-09-02](https://soar-analysis.com/blogs/company-commercial-risks/coca-colacompany) — **KO**, how it's sold *(general media)*

### 138. QSR dispensed beverage expansion

`foodservice-dispensed-beverage-expansion`

**What it is.** Restaurant chains broaden dispensed drink menus, increasing fountain beverage demand.

**Found through:** How it's sold | **Revenue streams touched:** Sparkling Soft Drinks

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **KO** (The Coca-Cola Company) — More QSR beverage launches increase concentrate and syrup sales through KO's foodservice system. *(impact 4, found through How it's sold, stream: Sparkling Soft Drinks)*

**Evidence:**

- "Sonic, McDonald’s, Chick-fil-A, and Whataburger are all expanding their assortment of refreshers, flavored sodas, lemonades, floats and craft-style beverage formats" — [restaurantdive.com, 2026-06-18](https://www.restaurantdive.com/news/qsrs-gaining-ground-in-dispensed-beverages-c-stores/822889/) — **KO**, how it's sold of Sparkling Soft Drinks *(trade press, industry body or named research house)*

### 139. Smartphone demand weakens on memory costs

`smartphone-demand-weakness-memory-costs`

**What it is.** Rising memory prices and macro pressure reduce smartphone unit sales and upgrade activity.

**Found through:** Trending demand

**Quantum.** size **3.0**, speed **5.0**, impact **3.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **T** (AT&T Inc.) — Lower device unit sales and higher component costs pressure AT&T's equipment revenue and upgrade economics. *(impact 3, found through Trending demand)*

**Evidence:**

- "US smartphone sales fell by 5% YoY in Q2 2026 as memory price hikes and other macroeconomic factors weakened consumer demand." — [counterpointresearch.com, 2026-08-12](https://counterpointresearch.com/en/insights/us-smartphone-sales-fall-5-percent-q2-2026) — **T**, trending demand *(trade press, industry body or named research house)*

### 140. Smartphone promotion intensity rises

`smartphone-promotion-intensity`

**What it is.** Carriers and retailers use frequent device promotions to acquire and retain subscribers, raising subsidy costs.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **5.0**, impact **3.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **T** (AT&T Inc.) — Promotions drive device and service acquisition but raise subsidy and retention costs. *(impact 3, found through How it's sold)*

**Evidence:**

- "In May 2026, telcos, OEMs, and retailers launched 1,094 smartphone promos (up 14% MoM)" — [verdict.co.uk, 2026-06-04](https://www.verdict.co.uk/may-2026-us-services-device-deal-engine/) — **T**, how it's sold *(trade press, industry body or named research house)*

### 141. Smartphone replacement cycles lengthen

`smartphone-replacement-cycle-lengthening`

**What it is.** Consumers hold smartphones longer, reducing annual device upgrades and carrier equipment revenue.

**Found through:** Trending demand

**Quantum.** size **3.0**, speed **5.0**, impact **3.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Negatively affected (1):**

- `-` **T** (AT&T Inc.) — Longer replacement cycles reduce device sales and upgrade-driven service plan changes. *(impact 3, found through Trending demand)*

**Evidence:**

- "On average, people replace their phone every 32 months (about 2 years and 8 months) in 2026, up from 29 months in 2025." — [einnews.com, 2026-09-15](https://www.einnews.com/pr_news/941009392/smartphone-lifespan-report-2026-americans-keep-devices-10-longer-as-new-releases-hit-2-000) — **T**, trending demand *(general media)*

### 142. Specialty pharmacy margin compression

`specialty-pharmacy-margin-compression`

**What it is.** Policy and channel changes are compressing specialty pharmacy reimbursement margins.

**Found through:** How it's sold | **Revenue streams touched:** Specialty Care

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **PFE** (Pfizer Inc.) — Compressed specialty pharmacy margins reduce net revenue for specialty drugs. *(impact 4, found through How it's sold, stream: Specialty Care)*

**Evidence:**

- "These policies promise lower patient and payer costs, but they also compress traditional buy-and-bill reimbursement processes and dispensing margins" — [rxinsider.com, 2026-05-12](https://rxinsider.com/market-buzz/specialty-pharmacy-outlook-2026/) — **PFE**, how it's sold of Specialty Care *(trade press, industry body or named research house)*

### 143. Streaming bundling return

`streaming-bundling-return`

**What it is.** Streaming services returning to bundles and cross-promotional packages to reduce churn.

**Found through:** How it's sold | **Revenue streams touched:** Monthly memberships

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Two-sided or unclear (1):**

- `±` **NFLX** (Netflix, Inc.) — Bundles can lower churn and acquisition costs but may reduce ARPU through discounts. *(impact 4, found through How it's sold, stream: Monthly memberships)*

**Evidence:**

- "Netflix and Warner Bros. Discovery finalized the terms of a cross-promotional bundling arrangement" — [usabusinesstimes.com, 2026-08-07](https://usabusinesstimes.com/hollywoods-streaming-giants-are-quietly-rebuilding-the-bundle/) — **NFLX**, how it's sold of Monthly memberships *(general media)*

### 144. Streaming engagement decline

`streaming-engagement-decline`

**What it is.** Viewer engagement with streaming services declining even as subscriber counts and profits hold.

**Found through:** Trending demand | **Revenue streams touched:** Monthly memberships

**Quantum.** size **3.0**, speed **4.0**, impact **4.0** → quantum **3.60** × breadth factor **1.00** = **3.60**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **NFLX** (Netflix, Inc.) — Weaker engagement can raise churn and reduce the lifetime value of memberships. *(impact 4, found through Trending demand, stream: Monthly memberships)*

**Evidence:**

- "Executives have flagged declining viewer engagement despite rising profits and low customer churn" — [tradevae.com, 2026-07-10](https://www.tradevae.com/news/stock-markets/netflix-probes-live-channels-and-bundles-as-management-flags-slipping-engagement/) — **NFLX**, trending demand of Monthly memberships *(trade press, industry body or named research house)*

### 145. Broadband permitting reform

`broadband-permitting-reform` — merged from: `wireless-infrastructure-permitting-reform`

**What it is.** Regulators streamline permits and fees to speed broadband network construction and lower deployment costs.

**Found through:** How it's made

**Quantum.** size **3.5**, speed **3.0**, impact **3.0** → quantum **3.20** × breadth factor **1.10** = **3.52**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.33; sources: company disclosure x1, trade press, industry body or named research house x1)

**Positively affected (2):**

- `+` **T** (AT&T Inc.) — Faster permits lower deployment costs and accelerate fiber service revenue. *(impact 3, found through How it's made)*
- `+` **VZ** (Verizon Communications Inc.) — Lower permitting costs and faster builds reduce Verizon's network deployment cost base. *(impact 3, found through How it's made)*

**Evidence:**

- "Speeding permitting timelines and reducing excessive fees will help remove unnecessary hurdles that can delay or even prevent broadband deployments." — [attconnects.com, 2026-06-25](https://www.attconnects.com/stories/att-statement-on-eliminating-barriers-to-wireline-deployment/) — **T**, how it's made *(company disclosure)*
- "Study finds FCC permitting reform could remove billions in costs burdening wireless construction" — [wirelessestimator.com, 2026-08-04](https://wirelessestimator.com/articles/2026/study-finds-fcc-permitting-reform-could-remove-billions-in-costs-burdening-wireless-construction/) — **VZ**, how it's made *(trade press, industry body or named research house)*

### 146. SMB banking switching intent

`smb-banking-switching-intent`

**What it is.** Small and medium businesses reconsider primary banking relationships, creating share-shift opportunities.

**Found through:** How it's sold | **Revenue streams touched:** Commercial Banking

**Quantum.** size **3.0**, speed **3.5**, impact **3.0** → quantum **3.15** × breadth factor **1.10** = **3.47**  
(2 trends from 2 companies, 2 sources, rating dispersion 0.33; sources: company disclosure x1, trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **BBVA** (Banco Bilbao Vizcaya Argentaria, S.A.) — Capturing SMB primary relationships lifts fee and interest revenue per customer. *(impact 3, found through How it's sold)*

**Negatively affected (1):**

- `-` **WFC** (Wells Fargo & Company) — Higher switching risk threatens deposit retention and fee revenue in Commercial Banking. *(impact 3, found through How it's sold, stream: Commercial Banking)*

**Evidence:**

- "Small business banking customers generate up to 12 times more annual revenue for financial institutions than traditional consumer customers in Europe" — [mynewsdesk.com, 2026-09-08](https://www.mynewsdesk.com/uk/visa/pressreleases/visa-study-small-business-banking-relationships-generate-up-to-12-times-more-revenue-than-consumer-relationships-in-europe-3465951) — **BBVA**, how it's sold *(company disclosure)*
- "Commercial Customers Are Preparing to Switch at Unprecedented Rates" — [csiweb.com, 2026-09-01](https://www.csiweb.com/wp-content/uploads/sites/2/2026/09/926_Datos_Comm_Bank_WP.pdf) — **WFC**, how it's sold of Commercial Banking *(trade press, industry body or named research house)*

### 147. Automotive connector electrification demand

`automotive-connector-electrification-demand`

**What it is.** Vehicle electrification and rising connector counts per vehicle increase automotive connector demand.

**Found through:** Trending demand

**Quantum.** size **4.0**, speed **3.0**, impact **3.0** → quantum **3.40** × breadth factor **1.00** = **3.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Positively affected (1):**

- `+` **APH** (Amphenol Corporation) — EVs use up to 40% more connectors, lifting Interconnect and Sensor Systems revenue. *(impact 3, found through Trending demand)*

**Evidence:**

- "The global automotive connector market is projected to reach $28.5 billion by 2028, growing at a CAGR of 7.2%." — [preciseworksplus.com, 2026-07-03](https://preciseworksplus.com/automotive-connector-mold-supply-chain-trends-2026-mexico-vs-china-what-buyers-need-to-know/) — **APH**, trending demand *(general media)*

### 148. Insulin access gap in LMICs

`insulin-access-gap-lmics`

**What it is.** Large unmet insulin demand in low- and middle-income countries represents future volume growth.

**Found through:** Trending demand

**Quantum.** size **4.0**, speed **3.0**, impact **3.0** → quantum **3.40** × breadth factor **1.00** = **3.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **NVO** (Novo Nordisk A/S) — Closing the LMIC access gap expands long-term insulin volume for Novo. *(impact 3, found through Trending demand)*

**Evidence:**

- "Only 35 million of the 93 million people who need insulin in LMICs currently receive it" — [clintonhealthaccess.org, 2025-11-01](https://www.clintonhealthaccess.org/wp-content/uploads/2025/11/Insulin-Market-Memo-Nov2025.pdf) — **NVO**, trending demand *(trade press, industry body or named research house)*

### 149. Private 5G enterprise adoption

`private-5g-enterprise-adoption`

**What it is.** Enterprises increasingly deploy private LTE/5G networks for AI, automation, and mission-critical connectivity.

**Found through:** Trending demand

**Quantum.** size **4.0**, speed **3.0**, impact **3.0** → quantum **3.40** × breadth factor **1.00** = **3.40**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **VZ** (Verizon Communications Inc.) — Expands enterprise connectivity and managed-network revenue for Verizon's other revenue stream. *(impact 3, found through Trending demand)*

**Evidence:**

- "spend on private LTE & 5G networks will reach $84.7 billion globally in 2031; up from $17.3 billion in 2026" — [juniperresearch.com, 2026-09-01](https://www.juniperresearch.com/press/private-network-spend-to-exceed-84bn/) — **VZ**, trending demand *(trade press, industry body or named research house)*

### 150. Aerospace and defense connector demand

`aerospace-defense-connector-demand`

**What it is.** Defense modernization and aircraft deliveries increase demand for rugged, high-reliability connectors.

**Found through:** Trending demand

**Quantum.** size **3.0**, speed **3.0**, impact **4.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **APH** (Amphenol Corporation) — Higher defense and aircraft connector demand lifts Harsh Environment Solutions revenue. *(impact 4, found through Trending demand)*

**Evidence:**

- "Demand for harsh-environment connectors is projected to expand at 7.2% CAGR between 2026 and 2036" — [futuremarketinsights.com, 2026-08-06](https://www.futuremarketinsights.com/reports/harsh-environment-connectors-market) — **APH**, trending demand *(vendor market-report page)*

### 151. AI infrastructure financing demand

`ai-infrastructure-financing-demand`

**What it is.** AI buildout drives demand for data center, power, and semiconductor financing.

**Found through:** Trending demand

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **BAC** (Bank of America Corporation) — AI infrastructure financing demand generates investment banking fees from debt and equity issuance. *(impact 3, found through Trending demand)*

**Evidence:**

- "AI itself reshapes capital allocation, fueling demand for data center, power, semiconductor, and digital infrastructure financing." — [bcgexpand.com, 2026-06-23](https://bcgexpand.com/q1-2026-investment-banking-trends/) — **BAC**, trending demand *(trade press, industry body or named research house)*

### 152. API supply chain diversification

`api-supply-chain-diversification`

**What it is.** Global API production is shifting away from China toward India and other suppliers.

**Found through:** How it's made

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **PFE** (Pfizer Inc.) — Diversifying API supply can raise near-term costs but reduce supply disruption risk. *(impact 3, found through How it's made)*

**Evidence:**

- "China is expected to reduce its share of global API output to around 30% from 45% in 2022" — [molekula.com, 2026-08-06](https://molekula.com/articles/china-and-india-api-manufacturing-shifts-in-2026-and-their-implications-for-western-procurement) — **PFE**, how it's made *(trade press, industry body or named research house)*

### 153. Branch network strategy shift

`branch-network-strategy-shift`

**What it is.** Banks are re-evaluating branch closures as physical locations prove valuable for relationships.

**Found through:** How it's sold | **Revenue streams touched:** Consumer Banking and Lending

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **WFC** (Wells Fargo & Company) — Branch relationships can lift deposit and wealth revenue but may raise distribution costs. *(impact 3, found through How it's sold, stream: Consumer Banking and Lending)*

**Evidence:**

- "Banks are rethinking branch consolidation as branches prove their relationship value" — [emarketer.com, 2026-06-23](https://www.emarketer.com/content/the-branch-2026) — **WFC**, how it's sold of Consumer Banking and Lending *(trade press, industry body or named research house)*

### 154. CIB revenue momentum slowdown

`cib-revenue-momentum-slowdown`

**What it is.** Corporate and investment banking revenue growth is slowing as non-bank competitors scale.

**Found through:** How it's sold | **Revenue streams touched:** Corporate and Investment Banking

**Quantum.** size **3.0**, speed **3.0**, impact **4.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **WFC** (Wells Fargo & Company) — Slower CIB revenue growth and non-bank competition pressure fees and market share. *(impact 4, found through How it's sold, stream: Corporate and Investment Banking)*

**Evidence:**

- "The industry is still on a growth trajectory, but the momentum we’ve seen in recent years is starting to level off." — [capgemini.com, 2026-03-01](https://www.capgemini.com/gb-en/wp-content/uploads/sites/5/2026/03/WCIBR_2026.pdf) — **WFC**, how it's sold of Corporate and Investment Banking *(trade press, industry body or named research house)*

### 155. GLP-1 manufacturing capacity expansion

`glp1-manufacturing-capacity-expansion`

**What it is.** Drugmakers are investing in manufacturing capacity to meet GLP-1 demand, especially oral formulations.

**Found through:** How it's made

**Quantum.** size **3.0**, speed **3.0**, impact **4.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: company disclosure x1)

**Positively affected (1):**

- `+` **NVO** (Novo Nordisk A/S) — Added capacity supports oral Wegovy supply and reduces shortage risk. *(impact 4, found through How it's made)*

**Evidence:**

- "This tabletting facility will provide significant additional manufacturing capacity for current and future Novo Nordisk GLP-1 treatments." — [globenewswire.com, 2026-03-02](https://www.globenewswire.com/news-release/2026/03/02/3247083/0/en/Novo-Nordisk-announces-more-than-400-million-euro-expansion-in-its-manufacturing-facility-in-Athlone-Ireland.html) — **NVO**, how it's made *(company disclosure)*

### 156. Government rideshare procurement expands

`government-rideshare-procurement`

**What it is.** Government agencies centralize ground transport buying into rideshare contracts, opening a public-sector channel.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **UBER** (Uber Technologies, Inc.) — Government channel expansion adds pre-negotiated rideshare demand for Uber Mobility. *(impact 3, found through How it's sold)*

**Evidence:**

- "It also broadens geographic coverage to more than 70 countries and 115,000 cities" — [ndtahq.com, 2026-03-24](https://www.ndtahq.com/gsa-onegov-rideshare-program-guide/) — **UBER**, how it's sold *(trade press, industry body or named research house)*

### 157. Natural gas price volatility

`natural-gas-price-volatility`

**What it is.** Natural gas price swings affect utility fuel costs and gas-fired generation margins.

**Found through:** How it's made

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Two-sided or unclear (1):**

- `±` **NEE** (NextEra Energy, Inc.) — Lower gas prices reduce FPL fuel costs but pressure NEER gas generation margins. *(impact 3, found through How it's made)*

**Evidence:**

- "Natural gas price at Henry Hub (dollars per million British thermal units) $3.53 $3.44 $3.31" — [eia.gov, 2026-09-01](https://www.eia.gov/outlooks/steo/archives/aug26.pdf) — **NEE**, how it's made *(general media)*

### 158. Production spend decline

`production-spend-decline`

**What it is.** Film and TV production spending declining even as project volumes rise.

**Found through:** How it's made

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **NFLX** (Netflix, Inc.) — Lower production spending can moderate content costs for streamers buying or commissioning shows. *(impact 3, found through How it's made)*

**Evidence:**

- "estimated committed production spending on those projects fell 5%" — [mande.net, 2026-08-25](https://mande.net/btl/production-is-up-spending-is-down-what-the-numbers-say-about-film-and-tv-in-2026) — **NFLX**, how it's made *(trade press, industry body or named research house)*

### 159. Retail deposit acquisition costs rise

`retail-deposit-acquisition-costs`

**What it is.** Banks face higher costs and lower conversion to acquire new retail deposits.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **BAC** (Bank of America Corporation) — Higher acquisition costs and low conversion make deposit gathering less efficient. *(impact 3, found through How it's sold)*

**Evidence:**

- "acquisition has gotten harder and more expensive – costs have doubled, and fewer than 1% of prospects bring meaningful balances." — [curinos.com, 2026-07-15](https://www.curinos.com/insights/curinos-perspective-meeting-growth-challenge-requires-precision-over-volume) — **BAC**, how it's sold *(trade press, industry body or named research house)*

### 160. Smartphone OEM financing disintermediation

`smartphone-oem-financing-disintermediation`

**What it is.** Device makers' leasing programs shift hardware financing and upgrade relationships away from carriers.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Two-sided or unclear (1):**

- `±` **VZ** (Verizon Communications Inc.) — It may boost upgrade frequency but shifts device financing and customer relationships away from carriers. *(impact 3, found through How it's sold)*

**Evidence:**

- "Recurring payment is the mechanism; a shorter replacement cycle is the outcome it’s built" — [reconanalytics.com, 2026-08-10](https://www.reconanalytics.com/the-upgrade-accelerator-inside-apples-new-klarna-lease/) — **VZ**, how it's sold *(trade press, industry body or named research house)*

### 161. Stablecoin disruption in banking

`stablecoin-disintermediation`

**What it is.** Stablecoins may disrupt bank payments and deposits, competing for customer balances.

**Found through:** How it's sold | **Revenue streams touched:** Fees and commissions

**Quantum.** size **3.0**, speed **3.0**, impact **3.0** → quantum **3.00** × breadth factor **1.10** = **3.30**  
(2 trends from 2 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x2)

**Negatively affected (2):**

- `-` **BAC** (Bank of America Corporation) — Stablecoins could disintermediate bank deposits and payment revenues. *(impact 3, found through How it's sold)*
- `-` **BBVA** (Banco Bilbao Vizcaya Argentaria, S.A.) — Stablecoin payments could bypass bank rails and erode card and payment fee income. *(impact 3, found through How it's sold, stream: Fees and commissions)*

**Evidence:**

- "What does the disruptive entrance of stablecoins mean for banks and payment firms?" — [deloitte.com, 2026-07-01](https://www.deloitte.com/us/en/insights/industry/financial-services/financial-services-industry-outlooks/banking-industry-outlook.html) — **BAC**, how it's sold *(trade press, industry body or named research house)*
- "The payments landscape also seems to be at a crossroads. Stablecoins, backed by the new Guiding and Establishing National Innovation" — [deloitte.com, 2026-07-01](https://www.deloitte.com/us/en/insights/industry/financial-services/financial-services-industry-outlooks/banking-industry-outlook.html) — **BBVA**, how it's sold of Fees and commissions *(trade press, industry body or named research house)*

### 162. White-label foodservice beverages

`white-label-foodservice-beverages`

**What it is.** Beverage makers supply unbranded drinks and equipment to restaurants seeking exclusive menus.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Positively affected (1):**

- `+` **KO** (The Coca-Cola Company) — Expands foodservice revenue via equipment and white-label supply, deepening customer lock-in. *(impact 3, found through How it's sold)*

**Evidence:**

- "A white-label lemonade already runs through more than 40,000 dispensers, some of it sold as Wendy’s Dave’s Craft Lemonade." — [businessmodelanalyst.com, 2026-08-24](https://businessmodelanalyst.com/coca-cola-white-label-freestyle-foodservice/) — **KO**, how it's sold *(general media)*

### 163. Wireless retail channel control

`wireless-retail-channel-control`

**What it is.** Third-party retail platforms control a growing share of US wireless device and service sales.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **4.0**, impact **3.0** → quantum **3.30** × breadth factor **1.00** = **3.30**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **VZ** (Verizon Communications Inc.) — Third-party retail control weakens carrier pricing and device sales influence. *(impact 3, found through How it's sold)*

**Evidence:**

- "Walmart has quietly become the single most important physical destination for wireless shopping in the United States" — [reconanalytics.com, 2025-12-01](https://www.reconanalytics.com/walmart-is-the-u-s-wireless-industrys-most-important-store-and-nobody-controls-it/) — **VZ**, how it's sold *(trade press, industry body or named research house)*

### 164. Physical game media decline

`physical-game-media-decline`

**What it is.** Consumer purchases of boxed video games shrink as digital distribution takes over.

**Found through:** Trending demand | **Revenue streams touched:** Game & Network Services

**Quantum.** size **2.0**, speed **5.0**, impact **3.0** → quantum **3.20** × breadth factor **1.00** = **3.20**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Two-sided or unclear (1):**

- `±` **SONY** (Sony Group Corporation) — Sony's disc exit cuts manufacturing costs but risks retail backlash and physical revenue. *(impact 3, found through Trending demand, stream: Game & Network Services)*

**Evidence:**

- "physical software dollar sales plunged to an all-time July low of $85 million in the US" — [sea.ign.com, 2026-09-01](https://sea.ign.com/playstation-5-3/247290/physical-video-game-dollar-sales-plunged-to-an-all-time-july-low-of-just-85-million-in-the-us) — **SONY**, trending demand of Game & Network Services *(general media)*

### 165. Beer distributor portfolio diversification

`beer-distributor-portfolio-diversification`

**What it is.** Beer distributors add non-beer products, reducing beer's share of their portfolios.

**Found through:** How it's sold | **Revenue streams touched:** Beer Business

**Quantum.** size **3.0**, speed **3.0**, impact **3.0** → quantum **3.00** × breadth factor **1.00** = **3.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **BUD** (Anheuser-Busch InBev SA/NV) — Distributors allocating less to beer can reduce shelf space and push for AB InBev. *(impact 3, found through How it's sold, stream: Beer Business)*

**Evidence:**

- "Beer Expected to be 67% of Distributors’ Portfolios in 5 Years, Down from 76% in 2025" — [brewbound.com](https://www.brewbound.com/news/nbwa-survey-beer-expected-to-be-67-of-distributors-portfolios-in-5-years-down-from-76-in-2025/) — **BUD**, how it's sold of Beer Business *(trade press, industry body or named research house)*

### 166. Consumer electronics D2C shift

`consumer-electronics-d2c-channel-shift`

**What it is.** Consumer electronics brands increasingly sell direct to consumers, bypassing traditional distribution.

**Found through:** How it's sold | **Revenue streams touched:** Entertainment Technology & Services

**Quantum.** size **3.0**, speed **3.0**, impact **3.0** → quantum **3.00** × breadth factor **1.00** = **3.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Two-sided or unclear (1):**

- `±` **SONY** (Sony Group Corporation) — Direct sales improve margin but require channel investment and disrupt retail partners. *(impact 3, found through How it's sold, stream: Entertainment Technology & Services)*

**Evidence:**

- "Brand-owned D2C channels are expanding at 9.92% CAGR, while traditional offline distribution moves at 3.42%." — [solgroup.net](https://www.solgroup.net/global-consumer-electronics-suppliers-2026/) — **SONY**, how it's sold of Entertainment Technology & Services *(general media)*

### 167. Digital freight brokerage growth

`digital-freight-brokerage-growth`

**What it is.** Freight procurement shifts to digital brokerage platforms, expanding the addressable market.

**Found through:** Trending demand

**Quantum.** size **3.0**, speed **3.0**, impact **3.0** → quantum **3.00** × breadth factor **1.00** = **3.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **UBER** (Uber Technologies, Inc.) — Digital brokerage adoption expands Uber Freight's addressable market and load volume. *(impact 3, found through Trending demand)*

**Evidence:**

- "The global digital freight brokerage market size was USD 4.90 Billion in 2025" — [emergenresearch.com, 2026-08-06](https://www.emergenresearch.com/industry-report/digital-freight-brokerage-market) — **UBER**, trending demand *(vendor market-report page)*

### 168. Flanker brands become growth engines

`telecom-flanker-brand-strategy`

**What it is.** Telecom operators use secondary brands to segment customers, reduce churn, and protect flagship pricing.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **3.0**, impact **3.0** → quantum **3.00** × breadth factor **1.00** = **3.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Positively affected (1):**

- `+` **T** (AT&T Inc.) — Secondary brands can defend share and reduce churn without discounting flagship brands. *(impact 3, found through How it's sold)*

**Evidence:**

- "will likely evolve into strategic, digital-first growth engines" — [deloitte.com, 2026-02-10](https://www.deloitte.com/global/en/insights/industry/technology/technology-media-telecom-outlooks/telecommunications-industry-outlook.html) — **T**, how it's sold *(trade press, industry body or named research house)*

### 169. Harsh environment connector qualification barriers

`harsh-environment-connector-qualification-barriers`

**What it is.** Long qualification cycles for harsh-environment connectors limit new entrants and protect incumbents.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **3.0**, impact **3.0** → quantum **3.00** × breadth factor **1.00** = **3.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **APH** (Amphenol Corporation) — High qualification barriers limit competition and support pricing in Harsh Environment Solutions. *(impact 3, found through How it's sold)*

**Evidence:**

- "extended qualification cycles (12–24 months) limiting new entrant velocity" — [indexbox.io, 2026-07-10](https://www.indexbox.io/store/world-connector-and-terminal-systems-for-harsh-environment-wiring-market-analysis-forecast-size-trends-and-insights/) — **APH**, how it's sold *(vendor market-report page)*

### 170. Industrial automation sensor connector demand

`industrial-automation-sensor-connector-demand`

**What it is.** Factory automation and IIoT deployments increase demand for sensor connectors and I/O connectivity.

**Found through:** Trending demand

**Quantum.** size **3.0**, speed **3.0**, impact **3.0** → quantum **3.00** × breadth factor **1.00** = **3.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Positively affected (1):**

- `+` **APH** (Amphenol Corporation) — Industrial automation and IIoT adoption raise sensor interconnect revenue. *(impact 3, found through Trending demand)*

**Evidence:**

- "Projected Size of 6.01 Billion USD by 2032 with a CAGR of 7.8%" — [pmarketresearch.com, 2026-06-22](https://pmarketresearch.com/it/sensor-connector-market/) — **APH**, trending demand *(vendor market-report page)*

### 171. Insulin API and biosimilar supply

`insulin-api-biosimilar-supply`

**What it is.** Insulin API demand grows with biosimilar adoption, altering supply economics and branded insulin competition.

**Found through:** How it's made

**Quantum.** size **3.0**, speed **3.0**, impact **3.0** → quantum **3.00** × breadth factor **1.00** = **3.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: vendor market-report page x1)

**Two-sided or unclear (1):**

- `±` **NVO** (Novo Nordisk A/S) — Biosimilar API demand grows, but biosimilar insulin competition pressures branded prices. *(impact 3, found through How it's made)*

**Evidence:**

- "forecast to a readjusted size of US$ 3761 million by 2031 with a CAGR of 4.1%" — [giiresearch.com, 2025-10-16](https://www.giiresearch.com/report/qyr1862283-insulin-api-global-market-share-ranking-overall.html) — **NVO**, how it's made *(vendor market-report page)*

### 172. Pole attachment deployment delays

`broadband-pole-attachment-delays`

**What it is.** Disputes over utility pole access delay broadband construction and raise deployment costs.

**Found through:** How it's made

**Quantum.** size **3.0**, speed **3.0**, impact **3.0** → quantum **3.00** × breadth factor **1.00** = **3.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **T** (AT&T Inc.) — Pole disputes delay fiber construction and raise deployment costs for AT&T. *(impact 3, found through How it's made)*

**Evidence:**

- "disputes within the industry over pole attachments pose deployment challenges." — [everycrsreport.com, 2026-06-01](https://www.everycrsreport.com/files/2026-06-16_R48992_54aed3576c43355b1293d51bc09b3b845428ac1e.pdf) — **T**, how it's made *(trade press, industry body or named research house)*

### 173. Retail vertical integration

`retail-vertical-integration`

**What it is.** Retailers bring distribution and production in-house to cut costs and control supply.

**Found through:** How it's sold

**Quantum.** size **3.0**, speed **3.0**, impact **3.0** → quantum **3.00** × breadth factor **1.00** = **3.00**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **KO** (The Coca-Cola Company) — Retailer integration can bypass suppliers, pressure margins and shelf space for KO brands. *(impact 3, found through How it's sold)*

**Evidence:**

- "more chains of all sizes are considering how various levels of vertical integration can help improve efficiency, strengthen supply chains and create a competitive advantage." — [cstoredecisions.com, 2026-08-31](https://cstoredecisions.com/retailers-turn-to-vertical-integration-to-cut-costs-strengthen-supply-chains/) — **KO**, how it's sold *(trade press, industry body or named research house)*

### 174. LNG buyers shift to term contracts

`lng-term-contracting-shift`

**What it is.** LNG buyers are moving from spot purchases to multi-year supply agreements for price and supply security.

**Found through:** How it's sold | **Revenue streams touched:** Integrated Gas

**Quantum.** size **2.0**, speed **4.0**, impact **3.0** → quantum **2.90** × breadth factor **1.00** = **2.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: general media x1)

**Positively affected (1):**

- `+` **SHEL** (Shell plc) — Long-term contracts secure predictable volumes and reduce spot price exposure. *(impact 3, found through How it's sold, stream: Integrated Gas)*

**Evidence:**

- "shift procurement away from volatile spot market towards long-term, predictable sourcing" — [theasset.com, 2026-07-07](https://www.theasset.com/article/56688/vietnam-secures-five-year-lng-supply-deal-with-shell) — **SHEL**, how it's sold of Integrated Gas *(general media)*

### 175. Mortgage servicing cost inflation

`mortgage-servicing-cost-inflation`

**What it is.** Mortgage servicing costs per loan are rising due to compliance and operational demands.

**Found through:** How it's made | **Revenue streams touched:** Consumer Banking and Lending

**Quantum.** size **2.0**, speed **4.0**, impact **3.0** → quantum **2.90** × breadth factor **1.00** = **2.90**  
(1 trends from 1 companies, 1 sources, rating dispersion 0.00; sources: trade press, industry body or named research house x1)

**Negatively affected (1):**

- `-` **WFC** (Wells Fargo & Company) — Higher servicing costs per loan compress margins on mortgage servicing in Consumer Banking. *(impact 3, found through How it's made, stream: Consumer Banking and Lending)*

**Evidence:**

- "annual direct servicing costs averaged $185 per loan in 2025, an increase from $181 per loan in 2024." — [newslink.mba.org, 2026-06-29](https://newslink.mba.org/servicing-newslink/2026/june/mba-servicing-newslink-tuesday-june-30-2026/chart-of-the-week-components-of-direct-servicing-operating-costs/) — **WFC**, how it's made of Consumer Banking and Lending *(trade press, industry body or named research house)*

## Ticker index

| Ticker | Helped by | Hurt by | Two-sided | Writeup |
|---|---|---|---|---|
| **APH** | AI data centre capex (#12); Connector pricing upcycle (#58); Communications hardware component demand (#78); AI rack copper-optics architecture (#88); AI backplane supplier concentration (#123); Automotive connector electrification demand (#147); Aerospace and defense connector demand (#150); Harsh environment connector qualification barriers (#169); Industrial automation sensor connector demand (#170) | Connector raw material cost inflation (#59) | Electronic component supply tightness (#75); Connector supply chain nearshoring and tariffs (#121) | [writeup](../tickers/APH.md) |
| **BAC** | Deposit and loan growth (#1); Commercial credit demand (#3); Investment banking fee rebound (#13); Sales and trading revenue boom (#28); Equity market rally lifts AUM (#42); Equity capital markets rebound (#93); AI infrastructure financing demand (#151) | Deposit competition raises funding costs (#35); Financial services distribution shift (#71); Retail deposit acquisition costs rise (#159); Stablecoin disruption in banking (#161) | AI disruption in banking (#113) | [writeup](../tickers/BAC.md) |
| **BBVA** | Deposit and loan growth (#1); Forex market volume growth (#15); SMB banking switching intent (#146) | Commercial credit demand (#3); Nonbank competition in banking (#18); Net interest margin compression (#36); Commercial lending standards tightening (#101); AI disruption in banking (#113); Card interchange fee caps (#125); Stablecoin disruption in banking (#161) | Banking technology spending cycle (#31) | [writeup](../tickers/BBVA.md) |
| **BHP** | Global steel demand growth (#45); India met coal import growth (#54); Copper concentrate TC/RC collapse (#60); Copper demand growth (#79); Copper by-product credit cost relief (#91) | China steel demand weakness (#5); Gulf energy shock metals costs (#53) | Copper market balance (#21); China iron ore pricing power (#37) | [writeup](../tickers/BHP.md) |
| **BUD** | Health-driven beverage reformulation (#20); US beer demand expansion (#70); Beverage system capacity investment (#87) | Beverage packaging input inflation (#38); Gulf energy shock metals costs (#53); Beer wholesale channel pressure (#90); Freight rate inflation (#129); Beer distributor portfolio diversification (#165) | Beer volume decline offset by premium mix (#22); Global beverage alcohol volume decline (#74) | [writeup](../tickers/BUD.md) |
| **KO** | Non-carbonated beverage shift (#48); Beverage system capacity investment (#87); Functional beverage demand growth (#94); Asset-light beverage franchising (#124); QSR dispensed beverage expansion (#138); White-label foodservice beverages (#162) | Beverage packaging input inflation (#38); Carbonated soft drink per-capita decline (#103); Coffee and tea commodity inflation (#126); Private-label beverage competition (#137); Retail vertical integration (#173) | Health-driven beverage reformulation (#20) | [writeup](../tickers/KO.md) |
| **MUFG** | Japan interest rate normalisation (#4); AI data centre capex (#12); Forex market volume growth (#15); Japan NISA asset management inflows (#26); Agentic AI banking productivity (#52); Japan silver economy wealth transfer (#83); Syndicated loan market growth (#86); Japan inbound investment growth sectors (#98) | Nonbank competition in banking (#18); Banking technology spending cycle (#31) | CIB wallet sponsor migration (#40); Japan ultrawealthy wealth management (#132) | [writeup](../tickers/MUFG.md) |
| **NEE** | AI data centre capex (#12); Solar supply chain oversupply (#29); Utility rate base growth (#73); Utility large-load tariffs (#112); Clean energy development backlog (#114) | Japan interest rate normalisation (#4); Data centre construction delays (#92); Transformer supply shortage (#111) | Clean energy tax credit deadlines (#23); Natural gas price volatility (#157) | [writeup](../tickers/NEE.md) |
| **NFLX** | Subscription streaming spend growth (#33); Streaming subscriber growth (#50); CTV ad spend growth (#61); Streaming price increases (#109); Production spend decline (#158) | SVOD market saturation (#30); Content spend inflation (#32); CTV upfront decline (#62); Short-form drama competition (#100); Streaming industry consolidation (#119); Streaming engagement decline (#144) | Streaming bundling return (#143) | [writeup](../tickers/NFLX.md) |
| **NVO** | GLP-1 obesity demand growth (#9); GLP-1 expanded indications (#96); Insulin access gap in LMICs (#148); GLP-1 manufacturing capacity expansion (#155) | GLP-1 competitive share shift (#8); GLP-1 adherence and price sensitivity (#95); Insulin tender pricing pressure (#130) | GLP-1 payer formulary churn (#10); Oral GLP-1 competition (#55); GLP-1 Medicare coverage expansion (#97); Insulin API and biosimilar supply (#171) | [writeup](../tickers/NVO.md) |
| **PFE** | Adult pneumococcal vaccine demand (#56); Global medicine demand growth (#82); Oncology market growth (#85); Non-COVID innovative drug growth (#107); Rare disease drug demand growth (#115) | IRA Medicare drug price negotiation (#46); COVID product demand decline (#104); Oncology loss-of-exclusivity risk (#118); Connector supply chain nearshoring and tariffs (#121); Oncology payer access controls (#135); Specialty pharmacy margin compression (#142) | API supply chain diversification (#152) | [writeup](../tickers/PFE.md) |
| **SAN** | Deposit and loan growth (#1); Investment banking fee rebound (#13); Agentic AI banking productivity (#52); Financial services distribution shift (#71); Auto finance market growth (#116) | Nonbank competition in banking (#18); Household credit demand weakness (#25); Deposit competition raises funding costs (#35); AI disruption in banking (#113) | Commercial credit demand (#3); CIB wallet sponsor migration (#40); BNPL consumer credit growth (#117) | [writeup](../tickers/SAN.md) |
| **SHEL** | Global LNG demand growth (#7); Oil and gas cash windfall (#14); Oil demand rebound in 2027 (#16); Refining and chemical margin recovery (#39); LNG trading gains from volatility (#106); LNG buyers shift to term contracts (#174) | Oil demand decline in 2026 (#2); Middle East supply shock raises feedstock costs (#19); Oil and gas labour cost pressure (#99); Fuel retail volume softness (#122) | EV charging changes forecourt economics (#102) | [writeup](../tickers/SHEL.md) |
| **SONY** | Global games market growth (#6); Recorded music streaming growth (#67); Music fan economy expansion (#84); Japan life insurance channel shift (#131) | Foundry capacity tightness and price hikes (#17); Consumer tech demand flatness (#24); PC and console market maturity (#66); Electronic component supply tightness (#75) | Consumer electronics tariff nearshoring (#41); Physical game media decline (#164); Consumer electronics D2C shift (#166) | [writeup](../tickers/SONY.md) |
| **T** | Converged connectivity demand (#72); Enterprise telecom services growth (#81); Broadband permitting reform (#145); Flanker brands become growth engines (#168) | Optical fiber price inflation (#108); Postpaid convergence pressures margins (#136); Smartphone demand weakens on memory costs (#139); Smartphone replacement cycles lengthen (#141); Pole attachment deployment delays (#172) | Fiber buildout acceleration (#105); Telecom ARPU rises but core prices flat (#110); Smartphone promotion intensity rises (#140) | [writeup](../tickers/T.md) |
| **TTE** | Oil and gas cash windfall (#14); Oil demand rebound in 2027 (#16); Refining and chemical margin recovery (#39) | Oil demand decline in 2026 (#2); Asian LNG demand decline (#57); Refinery throughput disruption (#68) | Middle East supply shock raises feedstock costs (#19); LNG supply wave 2026-2027 (#47); EV charging changes forecourt economics (#102); Fuel retail volume softness (#122); LNG contract flexibility shift (#133) | [writeup](../tickers/TTE.md) |
| **UBER** | Ride-hailing demand growth (#49); Gig insurance costs decline (#65); Government rideshare procurement expands (#156); Digital freight brokerage growth (#167) | Foundry capacity tightness and price hikes (#17); Freight broker margin compression (#64) | Delivery platform commission pressure (#63); Online food delivery growth (#76) | [writeup](../tickers/UBER.md) |
| **UBS** | Commercial credit demand (#3); Investment banking fee rebound (#13); Equity market rally lifts AUM (#42); Agentic AI banking productivity (#52); Basel III capital relief (#77) | Nonbank competition in banking (#18); Banking technology spending cycle (#31); Net interest margin compression (#36); Asset management fee compression (#89) | Financial services distribution shift (#71); Cross-border wealth booking shift (#80) | [writeup](../tickers/UBS.md) |
| **VZ** | AI telecom procurement savings (#43); Broadband permitting reform (#145); Private 5G enterprise adoption (#149) | Wireless service price competition (#11); Wireless promotional intensity (#34); Wireless spectrum capacity shortfall (#51); Smartphone upgrade cycle extension (#69); Wireless infrastructure labour shortage (#120); Wireless retail channel control (#163) | Smartphone OEM financing disintermediation (#160) | [writeup](../tickers/VZ.md) |
| **WFC** | Deposit and loan growth (#1); M&A volume rebound (#27); Commercial loan demand strength (#127); Consumer credit origination rebound (#128); Middle market earnings resilience (#134) | Net interest margin compression (#36); Credit card balance growth moderation (#44); Commercial lending standards tightening (#101); SMB banking switching intent (#146); CIB revenue momentum slowdown (#154); Mortgage servicing cost inflation (#175) | Branch network strategy shift (#153) | [writeup](../tickers/WFC.md) |

---

*Generated by `qts` from 20 analysis artifacts. Rebuild with `qualitative/qs themes` — rendering reads the artifacts only, so it costs no searches and no tokens.*
