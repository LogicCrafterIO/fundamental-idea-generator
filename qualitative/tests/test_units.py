"""Offline unit tests. No network: run with ``python -m unittest`` or ``pytest``.

What is worth locking down here is everything that decides *what gets published*
and is not a model call:

* the two gates and the security-type filter that defines the universe -- the
  filter is the one place a regex can silently delete a thousand real businesses
  from the pool, and it did, twice, before the ADR rule was added;
* quote grounding, because a claim that cites a source not containing its quote
  is the failure a reader cannot detect;
* the quantum maths and the ranking, so a weight change is a visible decision
  rather than a drift in the numbers;
* the renderers, which must survive a half-researched artifact -- a ticker with no
  streams and no trends is a normal outcome on a bad search day, not a crash.

The model-dependent paths are exercised by running the tool; these tests never
touch the network.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "qualitative"))
sys.path.insert(0, str(ROOT / "src"))

from qts import grounding, themes, trends, universe, writeup  # noqa: E402


class TestTheTwoGates(unittest.TestCase):
    """Price <= $100 and market cap >= $1B are the only quantitative inputs."""

    def _row(self, symbol, name, price, cap):
        return {"symbol": symbol, "name": name, "last_sale": price, "market_cap": cap}

    def test_gates_admit_and_exclude_on_exactly_two_numbers(self):
        rows = [
            self._row("AAA", "Alpha Industries Inc. Common Stock", 99.0, 1e9),
            self._row("BBB", "Beta Corp Common Stock", 100.01, 5e9),
            self._row("CCC", "Gamma Corp Common Stock", 10.0, 0.99e9),
        ]
        kept, dropped = [], []
        for row in rows:
            price, cap = row["last_sale"], row["market_cap"]
            (kept if price <= 100.0 and cap >= 1e9 else dropped).append(row["symbol"])
        self.assertEqual(kept, ["AAA"])
        self.assertEqual(dropped, ["BBB", "CCC"])

    def test_gates_are_configurable_but_default_to_the_exercise(self):
        self.assertEqual(universe.DEFAULT_MAX_PRICE, 100.0)
        self.assertEqual(universe.DEFAULT_MIN_MARKET_CAP, 1e9)


class TestSecurityTypeFilter(unittest.TestCase):
    """Nasdaq's list carries securities, and a security is not a business."""

    def test_preferred_notes_and_warrants_are_not_businesses(self):
        for name in (
            "Huntington Bancshares Incorporated Depositary Shares, Each Representing "
            "1/4,000th Interest in a Share of 6.875% Series J Non-Cumulative Perpetual Preferred Stock",
            "AT&T Inc. 5.350% Global Notes due 2066",
            "Core Scientific, Inc. Tranche 2 Warrants",
            "Calamos Dynamic Convertible & Income Fund Common Stock",
            "Alphabet Inc. Depositary Shares representing a 1/20th Interest in a Share of "
            "Series A Mandatory Convertible Preferred Stock",
        ):
            self.assertFalse(universe.is_common_equity(name), name)

    def test_real_adrs_mlps_and_class_shares_are_businesses(self):
        for name in (
            "Mitsubishi UFJ Financial Group, Inc. Common Stock",
            # The preferred shares are inside the parenthesis and describe the ADR
            # ratio -- the descriptor is not the security.
            "Itau Unibanco Banco Holding SA American Depositary Shares (Each repstg 500 Preferred Shares)",
            "BioNTech SE American Depositary Share",
            "Shell PLC American Depositary Shares (each representing two Ordinary Shares)",
            "Energy Transfer LP Common Units",
            "Fox Corporation Class A Common Stock",
        ):
            self.assertTrue(universe.is_common_equity(name), name)

    def test_share_classes_of_one_company_collapse_to_one_key(self):
        self.assertEqual(
            universe.name_key("Alphabet Inc. Class A Common Stock"),
            universe.name_key("Alphabet Inc. Class C Capital Stock"),
        )
        self.assertNotEqual(
            universe.name_key("Bank of America Corporation Common Stock"),
            universe.name_key("Wells Fargo & Company Common Stock"),
        )


class TestBatchSelection(unittest.TestCase):
    """The batch is an ordering, never a score."""

    def setUp(self):
        self.pool = [
            {"symbol": "SMALL", "name": "Small Co", "market_cap": 1e9},
            {"symbol": "BIG", "name": "Big Co", "market_cap": 5e11},
            {"symbol": "MID", "name": "Mid Co", "market_cap": 5e10},
        ]

    def test_cap_order_is_largest_first(self):
        picked = universe.select(self.pool, limit=2, order="cap")
        self.assertEqual([r["symbol"] for r in picked], ["BIG", "MID"])

    def test_start_skips_so_a_later_wave_does_not_redo_the_first(self):
        picked = universe.select(self.pool, limit=2, order="cap", start=2)
        self.assertEqual([r["symbol"] for r in picked], ["SMALL"])

    def test_random_order_is_seeded_and_reproducible(self):
        one = universe.select(self.pool, limit=3, order="random", seed=7)
        two = universe.select(self.pool, limit=3, order="random", seed=7)
        self.assertEqual([r["symbol"] for r in one], [r["symbol"] for r in two])


class TestGrounding(unittest.TestCase):
    """A quote must exist in the results, and in the source it names."""

    def setUp(self):
        self.results = [
            {
                "title": "Small business hiring cools",
                "url": "https://example.com/a",
                "content": "Hiring plans fell for a third month, the NFIB survey said.",
                "source_date": "2026-07-01",
                "age_days": 80,
                "publisher": "example.com",
            },
            {
                "title": "Unrelated",
                "url": "https://example.com/b",
                "content": "Something else entirely about weather.",
                "source_date": "2026-01-01",
                "age_days": 260,
                "publisher": "example.com",
            },
        ]

    def test_a_verbatim_quote_is_supported(self):
        self.assertTrue(grounding.quote_supported("Hiring plans fell for a third month", self.results))

    def test_a_paraphrase_is_not_supported(self):
        self.assertFalse(grounding.quote_supported("Hiring plans declined for a third month", self.results))

    def test_typographic_punctuation_does_not_break_a_match(self):
        results = [{"title": "t", "url": "u", "content": "The company\u2019s \u201cAI\u201d spend rose."}]
        self.assertTrue(grounding.quote_supported("The company's \"AI\" spend rose.", results))

    def test_supporting_results_name_the_source_that_contains_the_quote(self):
        hits = grounding.supporting_results("Something else entirely", self.results)
        self.assertEqual([h["url"] for h in hits], ["https://example.com/b"])

    def test_clean_claims_drops_unsupported_and_records_why(self):
        kept, dropped = grounding.clean_claims(
            [
                {"claim": "ok", "quote": "Hiring plans fell for a third month", "url": "https://example.com/a"},
                {"claim": "invented", "quote": "Hiring collapsed by 40%", "url": "https://example.com/a"},
            ],
            self.results,
        )
        self.assertEqual([k["claim"] for k in kept], ["ok"])
        self.assertEqual(dropped[0]["claim"], "invented")
        self.assertEqual(dropped[0]["drop_reason"], "quote_not_found_in_retrieved_results")
        self.assertEqual(kept[0]["grounded_by"], "search")

    def test_a_stream_named_only_in_the_business_summary_is_still_grounded(self):
        summary = "We earn revenue from cloud services and license support, and from hardware."
        self.assertTrue(grounding.text_in_summary("Cloud and license support", summary))
        self.assertFalse(grounding.text_in_summary("Advertising", summary))


class TestStreamExtraction(unittest.TestCase):
    """Shares are quoted or derived, never estimated."""

    def test_stream_queries_target_the_segment_split(self):
        queries = __import__("qts.streams", fromlist=["streams"]).plan_queries(
            "Coca-Cola", "KO", "Consumer Defensive", "Beverages"
        )
        self.assertTrue(any("segment" in q.lower() for q in queries))
        self.assertTrue(all("KO" in q or "Coca-Cola" in q for q in queries))

    def test_a_share_is_recovered_from_the_evidence_line_but_not_a_growth_rate(self):
        """The real pair: a segment table row versus a growth rate in a sentence."""
        streams = __import__("qts.streams", fromlist=["streams"])
        self.assertEqual(
            streams.share_from_quote("Sparkling Soft Drinks | ~50%", "Sparkling Soft Drinks"),
            (0.5, "approximate"),
        )
        self.assertEqual(
            streams.share_from_quote("Energy 4% of net operating revenue", "Energy"), (0.04, "stated")
        )
        self.assertIsNone(
            streams.share_from_quote(
                "Revenue grew 6.8% in the quarter on sparkling soft drinks volume",
                "Sparkling Soft Drinks",
            )
        )
        self.assertIsNone(
            streams.share_from_quote("Net interest income rose 5% as trading fell", "Net interest income")
        )
        # A percentage with no stream in it is not that stream's share.
        self.assertIsNone(streams.share_from_quote("~50%", "Sparkling Soft Drinks"))

    def test_an_amount_without_a_currency_is_withheld(self):
        """The real case: a bank segment "revenue" of 1.06T that was probably assets."""
        streams = __import__("qts.streams", fromlist=["streams"])
        self.assertFalse(streams.amount_is_usable("1.06T (FY2026)"))
        self.assertFalse(streams.amount_is_usable("segment total"))
        self.assertFalse(streams.amount_is_usable(None))
        self.assertTrue(streams.amount_is_usable("$4.2B in FY2025"))
        self.assertTrue(streams.amount_is_usable("\u00a51.06tn in FY2026"))
        self.assertTrue(streams.amount_is_usable("EUR 12.5 billion"))


class TestTrendVerification(unittest.TestCase):
    """The three-part framework must not lose a trend to a field the model fumbled."""

    def setUp(self):
        self.results = [
            {
                "title": "Channel shift",
                "url": "https://example.com/c",
                "content": "Distributors now provide inventory management and route planning.",
                "source_date": "2026-06-26",
                "age_days": 85,
                "publisher": "example.com",
            }
        ]
        self.streams = [{"name": "North America"}, {"name": "Bottling Investments"}]

    def test_ratings_are_clamped_to_the_scale(self):
        self.assertEqual(trends._rating(9), 5)
        self.assertEqual(trends._rating(0), 1)
        self.assertEqual(trends._rating("nonsense"), 3)

    def test_direction_synonyms_normalise(self):
        self.assertEqual(trends._direction("positive"), "tailwind")
        self.assertEqual(trends._direction("pressure"), "headwind")
        self.assertEqual(trends._direction("sideways"), "two-sided")

    def test_an_invented_stream_is_reset_rather_than_dropped(self):
        kept, dropped = trends._verify(
            [
                {
                    "lens": "sold",
                    "stream": "Imaginary Division",
                    "claim": "Distributors are taking on more services.",
                    "quote": "Distributors now provide inventory management and route planning.",
                    "url": "https://example.com/c",
                    "theme_key": "channel-shift",
                    "direction": "tailwind",
                    "size": 3,
                    "speed": 3,
                    "impact": 2,
                }
            ],
            self.results,
            self.streams,
        )
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["stream"], "the business overall")
        self.assertIn("stream_note", kept[0])
        self.assertEqual(dropped, [])

    def test_an_ungrounded_trend_is_dropped_with_its_reason(self):
        kept, dropped = trends._verify(
            [
                {
                    "lens": "demand",
                    "claim": "Demand is exploding.",
                    "quote": "Demand is exploding by 50% a year.",
                    "url": "https://example.com/c",
                    "theme_key": "demand-boom",
                }
            ],
            self.results,
            self.streams,
        )
        self.assertEqual(kept, [])
        self.assertEqual(dropped[0]["drop_reason"], "quote_not_found_in_retrieved_results")

    def test_an_unlabelled_trend_is_dropped_because_the_framework_needs_the_lens(self):
        kept, dropped = trends._verify(
            [{"lens": "", "claim": "x", "quote": "Distributors now provide inventory management", "theme_key": "k"}],
            self.results,
            self.streams,
        )
        self.assertEqual(kept, [])
        self.assertIn("unknown lens", dropped[0]["drop_reason"])

    def test_source_type_defaults_to_the_vaguest_honest_label(self):
        self.assertEqual(trends._source_type("trade"), "trade")
        self.assertEqual(trends._source_type("Market-Research"), "market_research")
        self.assertEqual(trends._source_type(""), "general")

    def test_synthesis_prompt_offers_existing_keys_for_reuse(self):
        """Without this, every ticker coins its own synonym for a shared force."""
        block = trends.format_vocabulary([{"key": "ai-data-centre-capex", "label": "AI data centre capex"}])
        self.assertIn("ai-data-centre-capex -- AI data centre capex", block)
        self.assertIn("(none yet", trends.format_vocabulary([]))
        self.assertIn("REUSE THAT KEY", trends.SYNTH_PROMPT)

    def test_vocabulary_is_capped_and_ordered_by_how_many_companies_use_a_key(self):
        analyses = [
            {"symbol": "AAA", "trends": {"trends": [{"theme_key": "shared"}, {"theme_key": "aa-only"}]}},
            {"symbol": "BBB", "trends": {"trends": [{"theme_key": "shared"}]}},
        ]
        vocab = __import__("qts.analysis", fromlist=["analysis"]).theme_vocabulary(analyses)
        self.assertEqual(vocab[0]["key"], "shared")
        self.assertEqual(vocab[0]["companies"], 2)
        self.assertEqual([v["key"] for v in vocab], ["shared", "aa-only"])


class TestThemeMaths(unittest.TestCase):
    """The ranking is arithmetic on stated ratings plus a capped breadth factor."""

    def test_quantum_weights_size_highest(self):
        big = themes._quantum([{"size": 5, "speed": 1, "impact": 1}])
        fast = themes._quantum([{"size": 1, "speed": 5, "impact": 1}])
        self.assertGreater(big["quantum"], fast["quantum"])

    def test_breadth_amplifies_but_is_capped(self):
        narrow = themes._assemble("k", ["k"], [self._trend("AAA", "k")], {"label": "K"})
        wide = themes._assemble(
            "k", ["k"], [self._trend(f"S{i}", "k") for i in range(12)], {"label": "K"}
        )
        self.assertEqual(narrow["breadth_factor"], 1.0)
        self.assertEqual(wide["breadth"], 12)
        self.assertEqual(wide["breadth_factor"], 1.5)  # capped at BREADTH_CAP=5
        self.assertGreater(wide["score"], narrow["score"])

    def test_one_large_theme_outranks_a_shared_small_one(self):
        """The reason breadth is a factor and not a fourth axis."""
        huge = themes._assemble(
            "huge", ["huge"], [self._trend("AAA", "huge", size=5, speed=5, impact=5)], {"label": "Huge"}
        )
        trivial = themes._assemble(
            "small",
            ["small"],
            [self._trend(f"S{i}", "small", size=1, speed=1, impact=1) for i in range(6)],
            {"label": "Small"},
        )
        self.assertGreater(huge["score"], trivial["score"])

    def test_a_name_on_both_sides_is_mixed_not_double_counted(self):
        theme = themes._assemble(
            "k",
            ["k"],
            [self._trend("AAA", "k", direction="tailwind"), self._trend("AAA", "k", direction="headwind")],
            {"label": "K"},
        )
        self.assertEqual(theme["sides"], {"positive": 0, "negative": 0, "mixed": 1})
        self.assertEqual(theme["breadth"], 1)

    def test_a_name_contributing_two_trends_is_listed_once_with_the_stronger_one(self):
        """Two angles on one force is a finding; printing the ticker twice is a bug."""
        theme = themes._assemble(
            "k",
            ["k"],
            [
                self._trend("AAA", "k", impact=2, direction="tailwind"),
                self._trend("AAA", "k", impact=5, direction="tailwind"),
            ],
            {"label": "K"},
        )
        self.assertEqual(len(theme["positive"]), 1)
        self.assertEqual(theme["positive"][0]["impact"], 5)
        self.assertEqual(theme["positive"][0]["trends_on_theme"], 2)
        self.assertEqual(theme["breadth"], 1)

    def test_token_merge_unites_near_identical_keys_only(self):
        groups = themes.merge_by_tokens([["ai-capex", "ai-infrastructure-capex", "data-centre-power"]])
        self.assertEqual(groups, [["ai-capex", "ai-infrastructure-capex"], ["data-centre-power"]])

    def test_generic_wording_does_not_carry_a_merge(self):
        """"growth" and "market" are not the force -- "copper" and "console" are."""
        self.assertFalse(themes._near_identical("copper-price-inflation", "console-hardware-price-inflation"))
        self.assertTrue(themes._near_identical("orphan-drug-growth", "orphan-drug-market-growth"))

    def test_opposites_do_not_merge(self):
        """The failure this guard exists for: non-carbonated is not carbonated."""
        self.assertFalse(
            themes._near_identical("non-carbonated-soft-drink-growth", "carbonated-soft-drink-market-growth")
        )
        self.assertFalse(
            themes._near_identical("asset-management-fee-compression", "wealth-management-fee-inflation")
        )

    def test_the_deterministic_pass_fires_even_when_the_model_returns_singletons(self):
        """A model that answers "one group per key" must not leave 200 themes behind."""
        groups = [[key] for key in ("deposit-competition-and-funding-costs", "deposit-funding-cost-pressure", "copper-price-inflation")]
        merged = themes.merge_groups_by_representative(groups)
        self.assertEqual(len(merged), 2)
        self.assertIn(
            sorted(["deposit-competition-and-funding-costs", "deposit-funding-cost-pressure"]),
            sorted([sorted(g) for g in merged]),
        )

    def test_ranks_are_dense_and_ordered_by_score(self):
        built = themes.build([self._analysis("AAA"), self._analysis("BBB")], canonicalise=False)
        scores = [t["score"] for t in built["themes"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual([t["rank"] for t in built["themes"]], list(range(1, len(scores) + 1)))

    def test_two_tickers_sharing_a_force_produce_one_theme_with_both_sides(self):
        built = themes.build(
            [self._analysis("AAA", direction="tailwind"), self._analysis("BBB", direction="headwind")],
            canonicalise=False,
        )
        theme = built["themes"][0]
        self.assertEqual(theme["breadth"], 2)
        self.assertEqual([m["symbol"] for m in theme["positive"]], ["AAA"])
        self.assertEqual([m["symbol"] for m in theme["negative"]], ["BBB"])
        self.assertEqual(theme["net"], "two-sided")

    # -- fixtures ---------------------------------------------------------
    def _trend(self, symbol, key, *, size=3, speed=3, impact=3, direction="tailwind"):  # noqa: D401
        return {
            "symbol": symbol,
            "lens": "demand",
            "stream": "the business overall",
            "claim": f"{symbol} claim",
            "why": "why",
            "quote": "q",
            "url": f"https://example.com/{symbol}",
            "publisher": "example.com",
            "direction": direction,
            "size": size,
            "speed": speed,
            "impact": impact,
            "theme_key": key,
            "theme_label": key.replace("-", " ").title(),
            "theme_definition": "definition",
        }

    def _analysis(self, symbol, *, direction="tailwind"):
        return {
            "symbol": symbol,
            "profile": {"name": f"{symbol} Inc", "price": 50.0, "market_cap": 2e9},
            "streams": {"streams": [], "description": "does things"},
            "trends": {
                "trends": [
                    self._trend(symbol, "shared-force", direction=direction),
                    self._trend(symbol, f"{symbol.lower()}-only", direction=direction),
                ]
            },
        }


class TestRendering(unittest.TestCase):
    """Rendering is a pure function of the artifacts, including when they are thin."""

    def _analysis(self, **overrides):
        base = {
            "symbol": "TEST",
            "researched_on": "2026-09-20",
            "profile": {
                "name": "Test Industries Inc.",
                "price": 42.5,
                "market_cap": 3.1e9,
                "sector": "Industrials",
                "industry": "Specialty Machinery",
                "employees": 12000,
                "country": "United States",
                "website": "https://example.com",
                "summary": "Test Industries makes widgets and sells them to distributors.",
                "gate_conflicts": [],
            },
            "streams": {
                "description": "Makes widgets and sells them to distributors.",
                "split_basis": "product_line",
                "streams": [
                    {
                        "name": "Widgets",
                        "what_it_is": "Sells widgets to industrial distributors.",
                        "revenue_share": 0.6,
                        "revenue_share_basis": "stated",
                        "amount": "$600M in FY2025",
                        "customer": "industrial distributors",
                        "quote": "Widgets were 60% of revenue",
                        "url": "https://example.com/w",
                        "publisher": "example.com",
                        "as_of": "2026-06-01",
                        "grounded_by": "search",
                    },
                    {
                        "name": "Service",
                        "what_it_is": "Maintains installed widgets.",
                        "revenue_share": 0.4,
                        "revenue_share_basis": "derived",
                        "amount": None,
                        "customer": "end users",
                        "quote": "Widgets were 60% of revenue",
                        "url": "https://example.com/w",
                        "publisher": "example.com",
                        "as_of": "2026-06-01",
                        "grounded_by": "search",
                    },
                ],
                "dropped": [{"name": "Mystery", "drop_reason": "not in retrieved results and not in the business summary"}],
                "customer_concentration": "Top ten distributors are 45% of revenue.",
                "notes": None,
                "geography": "Two thirds of revenue is North America.",
                "results_count": 12,
            },
            "trends": {
                "trends": [
                    {
                        "lens": "sold",
                        "lens_label": "How it's sold",
                        "stream": "Widgets",
                        "claim": "Distributors are consolidating as of 2026.",
                        "direction": "headwind",
                        "why": "Fewer buyers means less pricing power.",
                        "quote": "Distributor consolidation accelerated in 2026",
                        "url": "https://example.com/d",
                        "publisher": "example.com",
                        "source_type": "trade",
                        "as_of": "2026-06-26",
                        "age_days": 80,
                        "stale": False,
                        "size": 4,
                        "size_basis": "$10bn channel",
                        "speed": 4,
                        "speed_basis": "already visible",
                        "impact": 3,
                        "impact_basis": "one stream",
                        "theme_key": "distributor-consolidation",
                        "theme_label": "Distributor consolidation",
                        "theme_definition": "Buyers merging into fewer, larger accounts.",
                    }
                ],
                "dropped": [],
                "coverage": {"demand": 0, "sold": 1, "made": 0},
                "results_count": 30,
                "queries": [],
            },
            "errors": [],
        }
        base.update(overrides)
        return base

    def test_ticker_writeup_prints_streams_trends_and_the_two_numbers(self):
        text = writeup.render_ticker(self._analysis())
        self.assertIn("# TEST — Test Industries Inc.", text)
        self.assertIn("Share price $42.50", text)
        self.assertIn("Market cap 3.1B", text)
        self.assertIn("## Revenue streams", text)
        self.assertIn("| 1 | **Widgets**", text)
        self.assertIn("60%", text)
        self.assertIn("40% (derived)", text)
        self.assertIn("### How it's sold", text)
        self.assertIn("trade press, industry body or named research house", text)
        self.assertIn("## Retrieved but discarded", text)
        self.assertIn("Mystery", text)

    def test_one_quote_is_printed_once_even_when_it_grounds_two_streams(self):
        text = writeup.render_ticker(self._analysis())
        self.assertEqual(text.count("Widgets were 60% of revenue"), 1)
        self.assertIn("**Widgets, Service**", text)

    def test_a_part_with_no_grounded_trend_says_so_rather_than_going_blank(self):
        text = writeup.render_ticker(self._analysis())
        self.assertEqual(
            text.count("_No grounded trend was found for this part of the business in the retrieved sources._"),
            2,  # demand and made produced nothing; sold produced one trend
        )

    def test_a_bare_artifact_still_renders(self):
        bare = self._analysis(
            profile={"name": "Bare Co", "price": None, "market_cap": None, "summary": "A company."},
            streams={"streams": [], "dropped": []},
            trends={"trends": [], "dropped": [], "coverage": {}, "results_count": 0},
        )
        text = writeup.render_ticker(bare)
        self.assertIn("_No revenue stream could be grounded", text)
        self.assertIn("Bare Co", text)
        self.assertIn("n/a", text)

    def test_master_file_lists_both_sides_and_the_ticker_index(self):
        analyses = [self._analysis()]
        built = themes.build(analyses, canonicalise=False)
        index = writeup.theme_impact_index(built["themes"])
        master = writeup.render_master(built, analyses=analyses, gates={"max_price": 100.0, "min_market_cap": 1e9})
        self.assertIn("# Themes", master)
        self.assertIn("<= $100", master)
        self.assertIn("Negatively affected (1):", master)
        self.assertIn("**TEST**", master)
        self.assertIn("[writeup](../tickers/TEST.md)", master)
        self.assertIn("## Ranked themes", master)
        self.assertIn("`distributor-consolidation`", master)
        self.assertEqual(index["TEST"][0]["side"], "hurts it")

    def test_an_empty_theme_file_says_so(self):
        master = writeup.render_master({"themes": [], "tickers": [], "trend_count": 0, "merged": 0}, analyses=[])
        self.assertIn("_No themes: no trends survived grounding._", master)


if __name__ == "__main__":
    unittest.main()
