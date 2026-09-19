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
