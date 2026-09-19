"""Offline unit tests. No network: run with ``python -m unittest`` or ``pytest``.

These lock in the reverse-engineered maths and the wording generators. The
network-dependent check that the *live* chains still produce the reference legs
lives in ``fig demo``.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fig import lint, options, render  # noqa: E402
from fig.options import CONTRACT, Structure  # noqa: E402
from fig.themes import match_keywords, tag_text  # noqa: E402
from fig.util import human_money, parse_money  # noqa: E402
from fig.quants import describe_revisions, describe_trend  # noqa: E402


class TestParsing(unittest.TestCase):
    def test_parse_money_shapes(self):
        cases = [
            ("$1,234.56", 1234.56),
            ("($0.86)", -0.86),          # accounting negative
            ("$5,356,707,000,000", 5356707000000.0),
            ("--", None),
            ("", None),
            ("N/A", None),
            (7.5, 7.5),
            ("$ 147.61", 147.61),
        ]
        for raw, want in cases:
            with self.subTest(raw=raw):
                self.assertEqual(parse_money(raw), want)

    def test_human_money(self):
        self.assertEqual(human_money(455_000_000_000), "455B")
        self.assertEqual(human_money(7_070_000_000), "7.07B")
        self.assertEqual(human_money(446_333_681_664), "446.33B")


class TestWording(unittest.TestCase):
    def test_describe_trend_bands(self):
        # A 0.1% drift is noise and must read as flat.
        self.assertEqual(describe_trend(0.1), "flat over the last 7 days")
        self.assertEqual(describe_trend(-0.5), "slightly down over the last 7 days")
        self.assertEqual(describe_trend(2.0), "up over the last 7 days")
        self.assertEqual(describe_trend(-5.0), "sharply down over the last 7 days")
        self.assertEqual(describe_trend(None), "no revision history")

    def test_describe_revisions_always_states_counts(self):
        self.assertEqual(
            describe_revisions(4, 0), "all up, with 4 up and 0 down over last 30 days"
        )
        self.assertEqual(
            describe_revisions(6, 8), "tilted lower, with 6 up and 8 down over last 30 days"
        )
        self.assertEqual(
            describe_revisions(5, 5), "evenly split, with 5 up and 5 down over last 30 days"
        )
        self.assertEqual(describe_revisions(0, 0), "no revisions over last 30 days")


class TestThemes(unittest.TestCase):
    def test_no_substring_false_positives(self):
        # These three all broke a naive `keyword in text` implementation.
        self.assertNotIn("consumer_credit", tag_text("Passive Income From Dividends"))
        self.assertNotIn("regulation", tag_text("Social Security Changes for Retirees"))
        self.assertNotIn("mna", tag_text("The 1 Mistake Many Investors Make"))

    def test_true_positives(self):
        self.assertIn("consumer_credit", tag_text("Net charge-offs rose as provisions increased"))
        self.assertIn("ai_capex", tag_text("Data center capex drives GPU demand"))
        self.assertIn("guidance", tag_text("Company cuts guidance for the quarter"))

    def test_match_keywords_is_auditable(self):
        matched = match_keywords("net charge-offs rose")
        self.assertIn("consumer_credit", matched)
        self.assertIn("net charge-off", matched["consumer_credit"])


def _structure(long_premium: float, long_qty: int, short_premium: float, short_qty: int,
               long_bid=None, short_bid=None) -> Structure:
    """Build a Structure with synthetic legs, bypassing the network."""
    return Structure(
        symbol="TEST",
        direction="long",
        option_type="CALL",
        price=100.0,
        long_leg={"expiry": "2026-12-18", "strike": 105.0, "premium": long_premium,
                  "qty": long_qty, "bid": long_bid, "ask": long_premium},
        short_leg={"expiry": "2026-10-16", "strike": 105.0, "premium": short_premium,
                   "qty": short_qty, "bid": short_bid, "ask": short_premium},
    )


class TestCreditMath(unittest.TestCase):
    """The credit-ratio definition is the load-bearing reverse-engineered rule.

    It is the definition that makes both references' prose true:
      OMF  "very slightly above the 10% floor"  -> 10.16%
      ORCL "even if I halved it, it would be 13%" -> 27.6% / 2 = 13.8%
    """

    def test_omf_reference_credit_ratio(self):
        s = _structure(3.20, 14, 0.65, 7)
        self.assertAlmostEqual(s.credit_ratio_mid, 0.10156, places=4)
        self.assertGreater(s.credit_ratio_mid, options.CREDIT_FLOOR)

    def test_orcl_reference_credit_ratio_and_halving(self):
        s = _structure(15.55, 3, 6.44, 2)
        self.assertAlmostEqual(s.credit_ratio_mid, 0.27614, places=4)
        self.assertAlmostEqual(s.credit_ratio_mid / 2, 0.13807, places=4)  # "13%"

    def test_totals_match_reference_dollars(self):
        s = _structure(15.55, 3, 6.44, 2)
        self.assertAlmostEqual(s.long_total, 4665.0, places=2)
        self.assertAlmostEqual(s.short_total, 1288.0, places=2)
        self.assertAlmostEqual(s.net_debit, 3377.0, places=2)

    def test_conservative_basis_is_stricter_than_mid(self):
        # Long at ask above premium, short at bid below premium.
        s = _structure(3.48, 12, 0.77, 7, long_bid=2.95, short_bid=0.60)
        s.long_leg["ask"] = 4.0
        self.assertLess(s.credit_ratio_conservative, s.credit_ratio_mid)
        self.assertFalse(s.passes_floor())  # 8.75% at mid-ish pricing

    def test_solve_short_qty_reaches_target(self):
        # ORCL's target: 3 longs, aiming near 25% -> 2 shorts.
        self.assertEqual(options.solve_short_qty(15.55, 6.44, 3, target_ratio=0.25), 2)
        # Never more shorts than longs by default, even when the maths says so:
        # ideal here is 3 * 0.9 * 5.0 / 0.5 = 27, capped to the 3 longs.
        self.assertEqual(options.solve_short_qty(5.0, 0.5, 3, target_ratio=0.9), 3)

    def test_never_returns_zero_credit_when_one_lot_is_expensive(self):
        # AZO-like: a single contract, and an ideal short qty of 0.4 which used to
        # round to 0 and emit a structure with no credit at all.
        self.assertEqual(options.solve_short_qty(132.75, 40.0, 1, target_ratio=0.12), 1)

    def test_zero_when_no_short_premium_or_no_long(self):
        self.assertEqual(options.solve_short_qty(10.0, 0.0, 3, target_ratio=0.12), 0)
        self.assertEqual(options.solve_short_qty(10.0, 1.0, 0, target_ratio=0.12), 0)


class TestMonthlies(unittest.TestCase):
    def test_reference_expiries_are_monthlies(self):
        for expiry in ("2026-10-16", "2026-11-20", "2026-12-18", "2027-02-19"):
            with self.subTest(expiry=expiry):
                self.assertTrue(options.is_monthly_expiry(expiry))

    def test_weeklies_are_not_monthlies(self):
        for expiry in ("2026-10-02", "2026-10-09", "2026-10-23"):
            with self.subTest(expiry=expiry):
                self.assertFalse(options.is_monthly_expiry(expiry))


class TestRender(unittest.TestCase):
    def test_table_matches_reference_layout(self):
        s = _structure(15.55, 3, 6.44, 2)
        s.price = 150.0
        table = render.render_structure_table(s.rows())
        lines = table.split("\n")
        self.assertEqual(
            lines[0],
            "Long\tCALL\t18-Dec-26\t$ 105.00\t3\t$ 150.00\t100\t$ 15.55\t$ -\t$ -\t$ -\t$ 4,665.00",
        )
        # Credit received is negative and parenthesised; premium paid positive.
        self.assertIn("$ (1,288.00)", lines[1])

    def test_negative_money_is_parenthesised(self):
        self.assertEqual(render._money(-1288.0), "$ (1,288.00)")
        self.assertEqual(render._money(4665.0), "$ 4,665.00")


class TestLint(unittest.TestCase):
    def _good(self) -> dict:
        return {
            "ticker": "TEST",
            "description": "Nonprime consumer loan lender",
            "reasons": [
                "Provisions rose 31% quarter over quarter, so losses are accelerating.",
                "If charge-offs reach 10% the stock rerates to a PE of 4-5.",
            ],
            "structuring": {"reflection": "Credit clears the floor."},
        }

    def test_clean_note_passes(self):
        result = lint.lint_writeup(self._good())
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], 0)
        self.assertGreaterEqual(result["score"], 90)

    def test_long_description_fails(self):
        note = self._good()
        note["description"] = "word " * 40
        result = lint.lint_writeup(note)
        self.assertFalse(result["ok"])
        self.assertTrue(any("description_too_long" in i for i in result["issues"]))

    def test_long_reason_fails(self):
        note = self._good()
        note["reasons"] = ["word " * 50, "Provisions rose 31% so losses accelerate."]
        result = lint.lint_writeup(note)
        self.assertFalse(result["ok"])
        self.assertTrue(any("reason_too_long" in i for i in result["issues"]))

    def test_hedging_fails(self):
        note = self._good()
        note["reasons"] = ["Earnings could potentially fall 20% if credit turns."]
        result = lint.lint_writeup(note)
        self.assertTrue(any("hedging" in i for i in result["issues"]))

    def test_reference_style_reason_without_number_only_warns(self):
        # ORCL's own reason 2 has no number and no named comparison. Requiring one
        # would reject a verbatim reference reason, so this must not be an error.
        note = self._good()
        note["reasons"] = [
            "The market is overpricing the effects of GPU depreciation and debt servicing.",
            "Provisions rose 31% quarter over quarter, so losses are accelerating.",
        ]
        result = lint.lint_writeup(note)
        self.assertTrue(result["ok"], result["issues"])
        self.assertTrue(any("reason_no_anchor" in i for i in result["issues"]))

    def test_filler_is_word_matched_not_substring(self):
        # "very" must not match inside "recovery the" -- a real false positive
        # that reported an empty intensifier in a clean note.
        note = self._good()
        note["reasons"] = ["Net income rose 46% so the recovery the market doubted is real."]
        self.assertFalse(any("filler" in i for i in lint.lint_writeup(note)["issues"]))

        note["reasons"] = ["Net income rose 46% and it is a very real recovery for the franchise."]
        self.assertTrue(any("filler" in i for i in lint.lint_writeup(note)["issues"]))

    def test_unglossed_acronym_warns_but_glossed_is_clean(self):
        note = self._good()
        note["reasons"] = ["If NCO reach 10% the stock rerates to a PE of 4-5."]
        self.assertTrue(any("unglossed_acronym" in i for i in lint.lint_writeup(note)["issues"]))

        note["reasons"] = ["If NCO [net charge offs] reach 10% the stock rerates sharply."]
        self.assertFalse(any("unglossed_acronym" in i for i in lint.lint_writeup(note)["issues"]))


class TestNewsRelevance(unittest.TestCase):
    """Research houses appear in headlines as the *analyst*, not the subject.

    Jefferies (JEF) is itself a broker, so name matching alone scored its own
    coverage of McDonald's and Adobe as company-specific JEF news.
    """

    def _rel(self, title, name="Jefferies Financial Group Inc."):
        from fig.packet import _relevance

        return _relevance("JEF", {"title": title}, name)

    def test_analyst_role_is_demoted(self):
        self.assertEqual(self._rel("McDonald's target falls to $325, but Jefferies keeps faith"), 1)
        self.assertEqual(self._rel("Why Jefferies Is Bullish on Formula One Stock Now"), 1)
        self.assertEqual(self._rel("Jefferies favors senior housing in coverage launch"), 1)

    def test_subject_role_stays_high(self):
        self.assertEqual(self._rel("Jefferies posts Q3 profit jump on advisory fees"), 3)


class TestOllamaParsing(unittest.TestCase):
    """JSON mode makes valid JSON the common case, not the only case."""

    def test_parse_json_object_variants(self):
        from fig.sources.ollama import parse_json_object

        self.assertEqual(parse_json_object('{"a": 1}'), {"a": 1})
        self.assertEqual(parse_json_object('```json\n{"a": 2}\n```'), {"a": 2})
        self.assertEqual(parse_json_object('Here you go:\n{"a": 3}\nDone.'), {"a": 3})

    def test_parse_json_object_rejects_non_object(self):
        from fig.sources.ollama import parse_json_object

        with self.assertRaises(RuntimeError):
            parse_json_object("I cannot help with that.")


class TestDateRecovery(unittest.TestCase):
    def test_date_from_snippet(self):
        from fig.packet import _date_from_text

        self.assertEqual(_date_from_text("Sept 18 (Reuters) - About $18 billion"), "2026-09-18")
        self.assertEqual(_date_from_text("19 September 2026 | 8:03 AM"), "2026-09-19")
        self.assertEqual(_date_from_text("filed 2026-09-18 by the company"), "2026-09-18")
        self.assertIsNone(_date_from_text("no date here at all"))


def _fake_packet() -> dict:
    return {
        "symbol": "TEST",
        "as_of": "2026-09-19",
        "quants": {
            "price": 100.0,
            "market_cap_human": "10B",
            "fwd_pe": 12.34,
            "ps": 2.567,
            "eps_trend": {"text": "flat over the last 7 days"},
            "eps_revisions": {"text": "tilted lower, with 6 up and 8 down over last 30 days",
                              "up_7d": 3, "down_7d": 1, "up_30d": 6, "down_30d": 8},
        },
        "fundamental_deltas": [
            {"label": "Other Operating Items", "change_pct": 31.0, "direction": "increasing",
             "period": "6/30/2026", "is_credit": True},
            {"label": "Net Income", "change_pct": -32.7, "direction": "decreasing",
             "period": "6/30/2026", "is_credit": False},
        ],
        "eps_yoy": {"direction": "declined", "year_ago": 1.45, "current": 1.31},
        "catalyst": {
            "date": "2026-10-30",
            "weekday": "Friday",
            "session": "before the open",
            "days_out": 41,
            "basis": "scheduled",
            "consensus": {"eps_avg": 1.88},
            "recent_reports": [
                {"date": "2026-07-29", "eps_estimate": 1.26, "eps_actual": 1.31,
                 "surprise_pct": 3.92, "beat": True}
            ],
            "beat_streak": 4,
            "median_gap_days": 91,
            "facts_line": ("2026-10-30 (Friday, before the open), 41 days out "
                           "-- from the earnings calendar, consensus EPS 1.88."),
        },
        "structures": {
            "short": {
                "rows": [
                    {"side": "Long", "type": "PUT", "expiry": "19-Feb-27", "strike": 57.5, "qty": 12,
                     "underlying": 60.81, "multiplier": 100, "price": 3.48, "total": 4176.0},
                    {"side": "Short", "type": "PUT", "expiry": "16-Oct-26", "strike": 57.5, "qty": 8,
                     "underlying": 60.81, "multiplier": 100, "price": 0.77, "total": -616.0},
                ],
                "catalyst": "2027-01-29",
                "long_leg": {"expiry": "2027-02-19"},
                "credit_ratio_mid": 0.1475,
                "credit_ratio_conservative": 0.10,
            }
        },
    }


class TestAssembleWriteup(unittest.TestCase):
    """The safety invariant: the model writes prose, the tool owns the numbers."""

    def test_model_cannot_inject_numbers(self):
        from fig.generate import assemble_writeup

        # A model that hallucinates prices, multiples and option premiums.
        model_output = {
            "description": "Nonprime consumer loan lender",
            "reasons": ["Provisions rose 31% quarter over quarter, so losses are accelerating."],
            "reflection": "Credit clears the floor.",
            "quants": {"price": 999.99, "fwd_pe": 99.9, "market_cap": "999B", "ps": 99.9},
            "structuring": {"rows": [{"side": "Long", "strike": 1.0, "price": 9999.0}]},
        }
        writeup = assemble_writeup(_fake_packet(), model_output, "short")

        # Prose is the model's.
        self.assertEqual(writeup["description"], "Nonprime consumer loan lender")
        # Numbers are the packet's, not the model's.
        self.assertEqual(writeup["quants"]["price"], 100.0)
        self.assertEqual(writeup["quants"]["fwd_pe"], 12.3)
        self.assertEqual(writeup["quants"]["market_cap"], "10B")
        self.assertEqual(writeup["quants"]["ps"], 2.6)
        # Legs are the tool's, and the hallucinated row is gone.
        self.assertEqual(len(writeup["structuring"]["rows"]), 2)
        self.assertEqual(writeup["structuring"]["rows"][0]["price"], 3.48)

    def test_credit_delta_is_preferred_first(self):
        from fig.generate import _extra_quants_lines

        lines = _extra_quants_lines(_fake_packet())
        self.assertTrue(lines[0].startswith("Last quarter other operating items"), lines)
        self.assertTrue(any("year over year" in line for line in lines))

    def test_window_disagreement_is_flagged(self):
        from fig.generate import _extra_quants_lines

        lines = _extra_quants_lines(_fake_packet())
        self.assertTrue(any("disagree by window" in line for line in lines), lines)

    def test_missing_description_raises(self):
        from fig.generate import assemble_writeup

        with self.assertRaises(ValueError):
            assemble_writeup(_fake_packet(), {"reasons": ["a 31% move"]}, "short")

    def test_missing_structure_still_produces_a_note(self):
        """Structuring is optional: the catalyst carries the idea, legs do not."""
        from fig.generate import assemble_writeup

        writeup = assemble_writeup(
            _fake_packet(),
            {"description": "Lender", "reasons": ["Provisions rose 31% so losses accelerate."],
             "catalyst_why": "Provisions must keep rising for the thesis to hold."},
            "long",  # no long structure exists in the fake packet
        )
        self.assertNotIn("structuring", writeup)
        # The omission is recorded, not silent.
        self.assertIn("structure_error", writeup)
        self.assertEqual(writeup["catalyst"]["date"], "2026-10-30")

    def test_catalyst_why_falls_back_to_measured_justification(self):
        """A note must never assert a catalyst without justifying it."""
        from fig.generate import assemble_writeup

        writeup = assemble_writeup(
            _fake_packet(),
            {"description": "Lender", "reasons": ["Provisions rose 31% so losses accelerate."]},
            "short",
        )
        self.assertTrue(writeup["catalyst"]["why"], "catalyst justification must not be empty")

    def test_catalyst_is_copied_from_the_packet_not_the_model(self):
        from fig.generate import assemble_writeup

        writeup = assemble_writeup(
            _fake_packet(),
            {"description": "Lender", "reasons": ["Provisions rose 31% so losses accelerate."],
             "catalyst_why": "Credit must crack in the report.",
             "catalyst": {"date": "2099-01-01", "facts_line": "2099-01-01 (made up)"}},
            "short",
        )
        self.assertEqual(writeup["catalyst"]["date"], "2026-10-30")
        self.assertIn("2026-10-30", writeup["catalyst"]["facts_line"])

    def test_nested_reflection_is_accepted(self):
        from fig.generate import assemble_writeup

        writeup = assemble_writeup(
            _fake_packet(),
            {"description": "Lender", "reasons": ["Provisions rose 31% so losses accelerate."],
             "catalyst_why": "Provisions must keep rising for this to work.",
             "structuring": {"reflection": "Credit is 10.0% against me."}},
            "short",
        )
        self.assertEqual(writeup["structuring"]["reflection"], "Credit is 10.0% against me.")

    def test_assembled_note_passes_lint(self):
        from fig.generate import assemble_writeup

        writeup = assemble_writeup(
            _fake_packet(),
            {"description": "Nonprime consumer loan lender",
             "reasons": ["Provisions rose 31% quarter over quarter, so losses are accelerating.",
                         "If charge-offs reach 10% the stock rerates lower."],
             "reflection": "Credit is 14.8% mid but 10.0% if priced against me.",
             "catalyst_why": "Provisions must keep rising for the thesis to be right."},
            "short",
        )
        result = lint.lint_writeup(writeup)
        self.assertTrue(result["ok"], result["issues"])


class TestGrounding(unittest.TestCase):
    """Reason prose is the only place a model could smuggle in an invented figure."""

    EVIDENCE = (
        "QUANTS\n  Price: 60.81\n  Market Cap: 7.0B\n  EPS revisions: 6 up / 8 down (30d)\n"
        "STATEMENT MOVES\n  Net Income: decreasing 32.7%\n  Other Operating Items: increasing 31.0%\n"
        "NEXT EARNINGS: 2026-10-30  consensus EPS 1.87559\n"
        "  Subprime auto loan delinquency rate hit 6.8% at the start of 2026\n"
        "  fwdPE(current FY) 8.57  fwdPE(next FY) 7.08\n"
    )

    def _note(self, reasons):
        return {"description": "Lender", "reasons": reasons}

    def test_grounded_figures_pass(self):
        note = self._note(["Net income fell 32.7% while provisions rose 31%, so credit is worsening."])
        report = lint.check_grounding(note, self.EVIDENCE)
        self.assertTrue(report["grounded"], report)
        self.assertEqual(report["unsupported"], [])

    def test_rounded_figure_counts_as_grounded(self):
        # The note may write 8.6 where the packet says 8.57.
        report = lint.check_grounding(self._note(["It trades at 8.6x earnings."]), self.EVIDENCE)
        self.assertTrue(report["grounded"], report)

    def test_search_sourced_figure_is_grounded(self):
        report = lint.check_grounding(
            self._note(["Delinquency hit 6.8%, the worst in decades."]), self.EVIDENCE
        )
        self.assertTrue(report["grounded"], report)

    def test_invented_figure_is_flagged(self):
        report = lint.check_grounding(
            self._note(["Provisions rose 47.3% quarter over quarter."]), self.EVIDENCE
        )
        self.assertFalse(report["grounded"])
        self.assertIn("47.3", " ".join(report["unsupported"]))

    def test_small_counts_and_years_are_ignored(self):
        report = lint.check_grounding(
            self._note(["Two bad quarters in 2027 could cut the dividend 5 times."]), self.EVIDENCE
        )
        self.assertTrue(report["grounded"], report)


class TestCatalystLint(unittest.TestCase):
    def _note(self, **catalyst):
        base = {
            "date": "2026-10-30",
            "facts_line": "2026-10-30 (Friday, before the open), 41 days out.",
            "why": "Provisions must keep rising for the thesis to hold.",
        }
        base.update(catalyst)
        return {
            "ticker": "TST",
            "description": "Nonprime consumer loan lender",
            "catalyst": base,
            "reasons": ["Provisions rose 31% quarter over quarter, so losses accelerate.",
                        "Charge-offs at 10% would cut earnings enough to force a rerate."],
        }

    def test_valid_catalyst_passes(self):
        result = lint.lint_writeup(self._note())
        self.assertTrue(result["ok"], result["issues"])

    def test_missing_justification_is_an_error(self):
        result = lint.lint_writeup(self._note(why=""))
        self.assertFalse(result["ok"])
        self.assertIn("catalyst_no_justification", " ".join(result["issues"]))

    def test_overlong_justification_is_an_error(self):
        result = lint.lint_writeup(self._note(why=" ".join(["word"] * 40)))
        self.assertIn("catalyst_why_too_long", " ".join(result["issues"]))

    def test_date_must_appear_in_the_stated_facts(self):
        result = lint.lint_writeup(
            self._note(facts_line="late January, roughly 41 days out, before the open")
        )
        self.assertIn("catalyst_date_mismatch", " ".join(result["issues"]))

    def test_missing_catalyst_is_a_warning_not_a_blocker(self):
        result = lint.lint_writeup({
            "ticker": "TST",
            "description": "Nonprime consumer loan lender",
            "reasons": ["Provisions rose 31% quarter over quarter, so losses accelerate.",
                        "Charge-offs at 10% would cut earnings enough to force a rerate."],
        })
        self.assertIn("catalyst_missing", " ".join(result["issues"]))
        # No legs is acceptable now, so the note can still be ok.
        self.assertTrue(result["ok"], result["issues"])


class TestValuationBias(unittest.TestCase):
    """A discount is not a thesis; premium multiples usually exist for a reason."""

    def test_pure_discount_reason_is_flagged(self):
        self.assertTrue(
            lint.is_valuation_only("At 12.3x next-year earnings the stock prices in no growth.")
        )
        self.assertTrue(
            lint.is_valuation_only("It trades at 11.8x forward earnings, a discount to peers.")
        )

    def test_multiple_with_a_stated_mispricing_passes(self):
        # Names what the market is missing -> a thesis, not an observation.
        self.assertFalse(
            lint.is_valuation_only(
                "At 12.3x the market is missing that revenue grew 31%, so the multiple is too low."
            )
        )

    def test_multiple_with_a_mechanism_passes(self):
        self.assertFalse(
            lint.is_valuation_only(
                "It trades at 19.5x because margins are high, which forces a de-rating when "
                "costs rise."
            )
        )

    def test_mechanism_reason_is_not_flagged(self):
        self.assertFalse(
            lint.is_valuation_only("Revenue fell 11.2% quarter over quarter as clients cut headcount.")
        )

    def test_cheap_plus_falling_estimates_is_not_a_long_bonus(self):
        from fig import discover

        base = {
            "revisions_net_30d": -2, "price_change_30d": 4.0, "price_change_90d": None,
            "news_specific": 0, "structure_available": False,
        }
        cheap = discover._score({**base, "fwd_pe": 6.0, "ps": 1.0})
        pricey = discover._score({**base, "fwd_pe": 40.0, "ps": 1.0})
        # Cheap-and-falling must not outrank expensive-and-falling on valuation alone.
        self.assertNotIn("valuation", cheap[2])
        self.assertLessEqual(cheap[2].get("valuation_fragility", 0), pricey[2].get("valuation_fragility", 0))

    def test_rising_estimates_gets_no_valuation_bonus(self):
        from fig import discover

        scored = discover._score({
            "revisions_net_30d": 3, "price_change_30d": -6.0, "price_change_90d": None,
            "news_specific": 0, "structure_available": False, "fwd_pe": 5.0, "ps": 0.5,
        })
        self.assertNotIn("valuation_fragility", scored[2])


class TestValuationRuleCalibration(unittest.TestCase):
    """Calibrated against an independent audit of all nine generated notes."""

    def test_juxtaposition_form_is_the_fallacy(self):
        # "Fundamentals improved yet it trades at 16.9x" has not explained why the
        # market pays only 16.9x -- it restates the screen signal as a conclusion.
        self.assertTrue(
            lint.is_valuation_only(
                "Net income rose 32%, yet the stock trades at 16.9x next-year earnings.", "long"
            )
        )

    def test_price_discount_is_covered_not_just_multiples(self):
        self.assertTrue(
            lint.is_valuation_only(
                "Sales rose 9.9% and e-commerce grew 17.9%, yet shares sit 18% below May peak.",
                "long",
            )
        )

    def test_weak_conjunction_is_not_a_mechanism(self):
        # "so" used to count as causation, which excused this exact reason.
        self.assertTrue(
            lint.is_valuation_only(
                "next-FY consensus forward PE is 39.51, below the current 43.54, so the "
                "market is paying less for next year's earnings.",
                "long",
            )
        )

    def test_causal_chain_survives_the_tightening(self):
        # "force a rerate" is a consequence of a mechanism, not valuation vocabulary.
        self.assertFalse(
            lint.is_valuation_only(
                "Charge-offs at 10% would cut earnings enough to force a rerate.", "long"
            )
        )

    def test_short_theses_are_exempt(self):
        self.assertFalse(
            lint.is_valuation_only(
                "Revenue fell 11.2% while it still trades at 19.5x forward earnings.", "short"
            )
        )

    def test_reference_orcl_reason_1_passes(self):
        # The owner's own spec must not be rejected by the linter.
        self.assertFalse(
            lint.is_valuation_only(
                "It's unclear if the valuation is pricing in a declining enterprise Saas, "
                "because it's not priced like Google, which is trading at a Forward PE of "
                "25 while Oracle is at a Forward PE of 17.",
                "long",
            )
        )

    def test_pe_rollforward_is_caught_separately(self):
        # True of any company with any growth, so it distinguishes nothing.
        self.assertTrue(
            lint.is_pe_rollforward(
                "next-FY consensus forward PE is 39.51, below the current 43.54"
            )
        )
        self.assertFalse(
            lint.is_pe_rollforward("Revenue fell 11.2% quarter over quarter.")
        )

    def test_valuation_only_is_an_error_so_the_repair_loop_fixes_it(self):
        note = {
            "ticker": "TST",
            "direction": "long",
            "description": "Retailer of consumer goods",
            "catalyst": {"date": "2026-10-30", "facts_line": "2026-10-30, 41 days out.",
                         "why": "Margins must recover for this to work."},
            "reasons": ["It trades at 12x, a discount to peers trading at 20x.",
                        "It trades at 12x versus the group at 20x on every metric."],
        }
        result = lint.lint_writeup(note)
        self.assertFalse(result["ok"])
        self.assertIn("reason_valuation_only", " ".join(result["issues"]))


class TestTrendGrounding(unittest.TestCase):
    """A trend claim survives only if its quote is really in the retrieved text."""

    RESULTS = [
        {"title": "Subprime Auto Loans Hit Worst Delinquency in 32 Years",
         "url": "https://example.com/a",
         "content": "Key Points The subprime auto loan delinquency rate hit 6.8% at the "
                    "start of 2026."},
        {"title": "Small business hiring cools",
         "url": "https://example.com/b",
         "content": "Hiring cooled to its slowest pace of the streak as gains held "
                    "across every region."},
    ]

    def test_supported_quote_is_kept(self):
        from fig import research

        self.assertTrue(
            research._quote_is_supported("hiring cooled to its slowest pace of the streak", self.RESULTS)
        )

    def test_paraphrase_is_rejected(self):
        from fig import research

        self.assertFalse(
            research._quote_is_supported(
                "hiring accelerated sharply across all regions and company sizes", self.RESULTS
            )
        )

    def test_smart_quotes_and_whitespace_are_normalised(self):
        from fig import research

        self.assertTrue(
            research._quote_is_supported(
                "delinquency rate hit 6.8%   at the start of 2026", self.RESULTS
            )
        )

    def test_invented_claim_about_a_real_source_is_rejected(self):
        from fig import research

        self.assertFalse(
            research._quote_is_supported(
                "the delinquency rate fell to 2.1% as consumers repaired their balance sheets",
                self.RESULTS,
            )
        )


class TestReferencesPresent(unittest.TestCase):
    def test_reference_notes_exist_and_keep_key_figures(self):
        root = Path(__file__).resolve().parents[1] / "references"
        for name, needle in (
            ("orcl.md", "Forward PE of 17"),
            ("omf.md", "Nonprime consumer loan lender"),
        ):
            with self.subTest(reference=name):
                text = (root / name).read_text()
                self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
