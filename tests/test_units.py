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


class TestSidesAndFolders(unittest.TestCase):
    """Longs and shorts are filed apart, by the direction inside the note."""

    def test_side_folder_follows_the_direction(self):
        from fig.generate import side_folder

        self.assertEqual(side_folder("long"), "longs")
        self.assertEqual(side_folder("short"), "shorts")
        self.assertEqual(side_folder("SHORT"), "shorts")
        # An unset direction files as a long rather than crashing, and the note
        # still says what it argues.
        self.assertEqual(side_folder(None), "longs")

    def test_organize_moves_notes_and_packets_into_their_side(self):
        import json
        import tempfile
        from pathlib import Path as _Path

        from fig.generate import note_paths, organize

        with tempfile.TemporaryDirectory() as tmp:
            root = _Path(tmp)
            for ticker, direction in (("AAA", "long"), ("BBB", "short")):
                (root / f"{ticker}.json").write_text(
                    json.dumps({"ticker": ticker, "direction": direction, "reasons": ["x 1%"]})
                )
                (root / f"{ticker}.packet.json").write_text(json.dumps({"symbol": ticker}))
                (root / f"{ticker}.md").write_text(f"Ticker: {ticker}\n")
            (root / "README.md").write_text("index")

            result = organize(root)
            self.assertEqual(len(result["moved"]), 2)
            self.assertTrue((root / "longs" / "AAA.json").is_file())
            self.assertTrue((root / "longs" / "AAA.packet.json").is_file())
            self.assertTrue((root / "shorts" / "BBB.json").is_file())
            # The packet must travel with its note or the note is not auditable,
            # and the rendered note must not be left behind as a stale copy of
            # itself at the old path.
            self.assertFalse((root / "AAA.packet.json").exists())
            self.assertFalse((root / "AAA.md").exists())
            self.assertTrue((root / "longs" / "AAA.md").is_file())

            # Re-running finds nothing left to move.
            self.assertEqual(organize(root)["moved"], [])
            self.assertEqual(len(note_paths(root)), 2)

    def test_a_misfiled_note_is_corrected(self):
        import json
        import tempfile
        from pathlib import Path as _Path

        from fig.generate import organize

        with tempfile.TemporaryDirectory() as tmp:
            root = _Path(tmp)
            (root / "shorts").mkdir()
            (root / "shorts" / "AAA.json").write_text(
                json.dumps({"ticker": "AAA", "direction": "long", "reasons": ["x 1%"]})
            )
            result = organize(root)
            self.assertEqual(len(result["moved"]), 1)
            self.assertTrue((root / "longs" / "AAA.json").is_file())


class TestMoneyArgs(unittest.TestCase):
    def test_market_cap_arguments(self):
        from fig.cli import _parse_money_arg

        self.assertEqual(_parse_money_arg("1b", None), 1e9)
        self.assertEqual(_parse_money_arg("1000m", None), 1e9)
        self.assertEqual(_parse_money_arg("2e9", None), 2e9)
        self.assertEqual(_parse_money_arg("1,000,000,000", None), 1e9)
        # 0 means "no floor", not "$0", so the two ways of disabling agree.
        self.assertIsNone(_parse_money_arg("0", 2e9))
        self.assertEqual(_parse_money_arg(None, 2e9), 2e9)


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
             "reason_sources": [["S3"], ["S2"]],
             "reflection": "Credit is 14.8% mid but 10.0% if priced against me.",
             "catalyst_why": "Provisions must keep rising for the thesis to be right."},
            "short",
        )
        result = lint.lint_writeup(writeup)
        self.assertTrue(result["ok"], result["issues"])


class TestReasonSources(unittest.TestCase):
    """Every reason names the evidence behind it, and only real evidence."""

    def test_citations_resolve_to_packet_entries(self):
        from fig.generate import assemble_writeup

        writeup = assemble_writeup(
            _fake_packet(),
            {"description": "Lender",
             "reasons": ["Provisions rose 31% so losses accelerate."],
             "reason_sources": [["S1", "S3"]]},
            "short",
        )
        cited = writeup["reason_sources"][0]
        self.assertEqual([c["id"] for c in cited], ["S1", "S3"])
        # The URL and provider come from the packet, never from the model.
        self.assertTrue(all(c["provider"] for c in cited))
        self.assertNotIn("text", cited[0])

    def test_fabricated_source_id_is_dropped_not_printed(self):
        from fig.generate import assemble_writeup

        writeup = assemble_writeup(
            _fake_packet(),
            {"description": "Lender",
             "reasons": ["Provisions rose 31% so losses accelerate."],
             "reason_sources": [["S99"]]},
            "short",
        )
        self.assertEqual(writeup["reason_sources"][0], [])
        self.assertEqual(writeup["sources_unverified"], ["S99"])
        result = lint.lint_writeup(writeup)
        codes = {i["code"] for i in result["issues_detail"]}
        self.assertIn("reason_source_unknown", codes)
        self.assertIn("reason_no_source", codes)

    def test_url_written_into_a_reason_is_removed(self):
        from fig.generate import assemble_writeup

        writeup = assemble_writeup(
            _fake_packet(),
            {"description": "Lender",
             "reasons": ["Provisions rose 31% (see https://made-up.example/report) so losses accelerate."],
             "reason_sources": [["S1"]]},
            "short",
        )
        self.assertNotIn("made-up.example", writeup["reasons"][0])
        self.assertEqual(writeup["urls_redacted"], ["https://made-up.example/report"])
        codes = {i["code"] for i in lint.lint_writeup(writeup)["issues_detail"]}
        self.assertIn("reason_url_redacted", codes)

    def test_missing_citation_is_an_error_only_when_sources_were_supplied(self):
        from fig.generate import assemble_writeup

        without_catalogue = {"ticker": "T", "description": "Lender",
                             "reasons": ["Provisions rose 31% so losses accelerate.",
                                         "If charge-offs reach 10% the stock rerates lower."]}
        self.assertTrue(lint.lint_writeup(without_catalogue)["ok"])
        # The same note built from a packet that registered sources must cite one.
        assembled = assemble_writeup(
            _fake_packet(),
            {"description": "Lender",
             "reasons": ["Provisions rose 31% so losses accelerate."]},
            "short",
        )
        self.assertFalse(lint.lint_writeup(assembled)["ok"])

    def test_source_grounding_flags_a_figure_from_another_source(self):
        note = {
            "description": "Lender",
            "reasons": ["Provisions rose 31% quarter over quarter, so losses accelerate."],
            "reason_sources": [[{"id": "S1"}]],
            "sources_catalogue": [
                {"id": "S1", "kind": "consensus", "label": "estimates", "provider": "Yahoo"},
                {"id": "S3", "kind": "statements", "label": "statements", "provider": "Nasdaq"},
            ],
        }
        catalogue = note["sources_catalogue"]
        catalogue[0]["text"] = "FY consensus 1.88, 5 up and 0 down over 30 days"
        catalogue[1]["text"] = "Other Operating Items increasing 31.0%"
        report = lint.check_source_grounding(note, catalogue)
        self.assertFalse(report["ok"])
        self.assertIn("31", report["mismatches"][0])
        # Cited correctly, the same figure passes.
        note["reason_sources"] = [[{"id": "S3"}]]
        self.assertTrue(lint.check_source_grounding(note, catalogue)["ok"])

    def test_render_prints_a_source_line_under_each_reason(self):
        text = render.render_writeup(
            {
                "ticker": "BB",
                "description": "Lender",
                "reasons": ["Provisions rose 31% so losses accelerate."],
                "reason_sources": [
                    [
                        {"id": "S3", "provider": "Nasdaq company financials",
                         "url": "https://www.nasdaq.com/market-activity/stocks/bb/financials",
                         "date": "5/31/2026"}
                    ]
                ],
            }
        )
        lines = text.splitlines()
        reason_at = next(i for i, line in enumerate(lines) if line.startswith("1) "))
        self.assertTrue(lines[reason_at + 1].startswith("   Source: [S3] Nasdaq company financials"))
        self.assertIn("https://www.nasdaq.com", lines[reason_at + 1])


class TestStaleConsensusOnCounts(unittest.TestCase):
    """The BB error: a revision count read as a revision of the number."""

    QUANTS = {"eps_trend": "flat over the last 7 days",
              "eps_revisions": "all up, with 5 up and 0 down over last 30 days"}

    def test_bb_reason_is_caught(self):
        reason = ("Because BlackBerry beat consensus in each of the last four quarters by "
                  "36% to 186%, and five analysts raised estimates in 30 days with none "
                  "cutting, the 0.19 FY number is stale.")
        self.assertTrue(lint.is_stale_consensus_on_counts(reason, self.QUANTS))
        codes = {i["code"] for i in lint.lint_writeup(
            {"ticker": "BB", "description": "x",
             "reasons": [reason, "If the backlog converts the stock rerates to a PE of 20."],
             "quants": self.QUANTS}
        )["issues_detail"]}
        self.assertIn("reason_stale_consensus_on_counts", codes)

    def test_a_claim_about_the_level_is_not_flagged(self):
        # No revision counts: this is an argument about value, not about age.
        reason = ("Because QNX royalties convert only as cars ship, the 0.19 FY consensus "
                  "is too low by the amount already contracted.")
        self.assertFalse(lint.is_stale_consensus_on_counts(reason, self.QUANTS))

    def test_counts_without_a_staleness_claim_are_not_flagged(self):
        reason = "Five analysts raised estimates in 30 days with none cutting, so the bar is higher."
        self.assertFalse(lint.is_stale_consensus_on_counts(reason, self.QUANTS))

    def test_falling_estimates_leave_staleness_arguable(self):
        reason = "Five analysts cut estimates in 30 days and the 0.19 consensus is stale."
        quants = {"eps_trend": "slightly down over the last 7 days"}
        self.assertFalse(lint.is_stale_consensus_on_counts(reason, quants))


class TestCountsVersusLevel(unittest.TestCase):
    """The packet states which of the two moved, because prose conflates them."""

    def test_flat_level_with_rising_counts_says_the_consensus_is_current(self):
        from fig.packet import revisions_reading

        line = revisions_reading({
            "eps_trend": {"current": 0.18857, "30d_ago": 0.18857, "change_30d_pct": 0.0},
            "eps_revisions": {"up_30d": 5, "down_30d": 0},
        })
        self.assertIn("unchanged", line)
        self.assertIn("not stale", line)

    def test_a_raised_level_says_the_revisions_are_already_in_it(self):
        from fig.packet import revisions_reading

        line = revisions_reading({
            "eps_trend": {"current": 2.1, "30d_ago": 2.0, "change_30d_pct": 5.0},
            "eps_revisions": {"up_30d": 7, "down_30d": 1},
        })
        self.assertIn("raised", line)
        self.assertIn("already includes", line)

    def test_trailing_beats_that_add_up_to_the_consensus_are_called_out(self):
        from fig.packet import trailing_vs_consensus

        found = trailing_vs_consensus({
            "quants": {"eps_fy_current": 0.18857},
            "catalyst": {"recent_reports": [
                {"date": "2026-06-25", "eps_actual": 0.04, "beat": True},
                {"date": "2026-04-09", "eps_actual": 0.06, "beat": True},
                {"date": "2025-12-18", "eps_actual": 0.05, "beat": True},
                {"date": "2025-09-25", "eps_actual": 0.04, "beat": True},
            ]},
        })
        self.assertIsNotNone(found)
        self.assertAlmostEqual(found["trailing_sum"], 0.19, places=6)
        self.assertIn("already in the consensus", found["line"])

    def test_uncomparable_quarters_are_not_reported(self):
        from fig.packet import trailing_vs_consensus

        # A company whose consensus is 4x its last four quarters: no comparison.
        self.assertIsNone(trailing_vs_consensus({
            "quants": {"eps_fy_current": 8.0},
            "catalyst": {"recent_reports": [
                {"date": "2026-06-25", "eps_actual": 0.5, "beat": True},
                {"date": "2026-04-09", "eps_actual": 0.5, "beat": True},
                {"date": "2025-12-18", "eps_actual": 0.5, "beat": True},
            ]},
        }))


class TestRegisterStability(unittest.TestCase):
    """Ids are positional, so a note must be checked against the register it cited.

    Widening how many headlines are citable shifts every id after them. Checking a
    stored note against a freshly built register therefore resolves its citations to
    the wrong sources -- in this repo it reported six misfiled citations that were
    artefacts of the rebuild. `register_for` resolves against the note's own register,
    with the text coming from the packet by ``ref``.
    """

    PACKET = {
        "symbol": "ZZ",
        "quants": {"price": 10.0, "market_cap": 1e9, "fwd_pe": 10.0},
        "profile": {"name": "ZZ Corp", "summary": "does things"},
        "news": [
            {
                "title": f"feed {i}",
                "url": f"https://f{i}.com/a",
                "source": "yfinance",
                "publisher": f"f{i}.com",
                "summary": f"feed text {i}",
            }
            for i in range(3)
        ]
        + [
            {
                "title": "web item",
                "url": "https://w.com/a",
                "source": "ollama_search",
                "publisher": "w.com",
                "summary": "the delinquency rate hit 22% in the quarter",
            }
        ],
    }

    def _note_citing_web_item(self):
        from fig import generate, packet as packet_mod

        small = packet_mod.source_catalogue(self.PACKET, max_news=1)
        web_id = next(e["id"] for e in small if e["ref"] == "web:0")
        note = {
            "description": "Lender",
            "reasons": ["Delinquency hit 22%, the worst since 2020."],
            "reason_sources": [[{"id": web_id}]],
            "sources_catalogue": generate.public_sources(small),
        }
        return note, web_id

    def test_a_rebuilt_register_would_misfile_the_citation(self):
        from fig import packet as packet_mod

        note, web_id = self._note_citing_web_item()
        rebuilt = packet_mod.source_catalogue(self.PACKET, max_news=10)
        self.assertNotEqual(
            next(e["ref"] for e in rebuilt if e["id"] == web_id),
            "web:0",
            "the fixture no longer reproduces the id shift this class exists for",
        )
        # The figure is in the packet and cited correctly, and the rebuilt register
        # still reports it as misfiled -- which is why the rebuild must not be used.
        self.assertFalse(lint.check_source_grounding(note, rebuilt)["ok"])

    def test_the_stored_register_resolves_it_correctly(self):
        from fig import generate

        note, web_id = self._note_citing_web_item()
        report = lint.check_source_grounding(note, generate.register_for(note, self.PACKET))
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["checked"], 1, report)

    def test_a_note_without_a_stored_register_uses_the_packet(self):
        from fig import generate, packet as packet_mod

        packet = {**self.PACKET, "sources": packet_mod.source_catalogue(self.PACKET)}
        note = {"description": "Lender", "reasons": ["Delinquency hit 22%."], "reason_sources": [[]]}
        self.assertEqual(generate.register_for(note, packet), packet["sources"])


class TestRunSettings(unittest.TestCase):
    """A folder can hold notes from runs under different caps.

    The index states which cap produced which notes, and it is rebuilt from the notes
    alone -- so the rules have to be on disk beside them. Stating one default for the
    whole folder is a false claim about how most of these names were chosen.
    """

    def test_the_index_states_the_cap_each_batch_ran_under(self):
        import tempfile

        from fig import generate

        with tempfile.TemporaryDirectory() as tmp:
            generate.record_settings(
                tmp, tickers=["AAA", "BBB"], max_price=75.0, min_market_cap=1e9
            )
            generate.record_settings(tmp, tickers=["CCC"], max_price=150.0, min_market_cap=2e9)
            rows = generate._read_settings(tmp)
            self.assertEqual(len(rows), 2)

            results = [
                {"writeup": {"ticker": t, "direction": "long"}, "lint": {"score": 90}}
                for t in ("AAA", "BBB", "CCC")
            ]
            text = generate.write_index(results, tmp, settings=rows)
            self.assertIn("2 note(s) under a **$75** share price", text)
            self.assertIn("1 note(s) under a **$150** share price", text)

    def test_a_note_from_no_recorded_run_is_not_attributed_to_one(self):
        import tempfile

        from fig import generate

        with tempfile.TemporaryDirectory() as tmp:
            results = [
                {"writeup": {"ticker": "ZZZ", "direction": "long"}, "lint": {"score": 90}}
            ]
            text = generate.write_index(
                results,
                tmp,
                settings=[{"tickers": ["AAA"], "max_price": 75.0, "min_market_cap": 1e9}],
            )
            # No record names this note, so the index must not claim the recorded
            # cap produced it -- it says it does not know, and names the defaults.
            self.assertIn("No run record for these 1 note(s)", text)
            self.assertIn("$150 and $2.0B", text)


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

    def test_digits_inside_dates_and_urls_cannot_ground_a_figure(self):
        # The BB regression, exactly: a reason claimed "25.38% a year" growth. The
        # packet has no such figure -- the only 25 in it was the day of the month in
        # "Jun 25, 2026" and a digit run in a link, and either was enough to make an
        # invented figure look sourced.
        evidence = (
            "Release Date Jun 25, 2026\n"
            "  BlackBerry (BB) Q2 2026 Earnings  https://247wallst.com/companies/bb/181253/earnings\n"
            "  [3] 2025-09-25 headline text\n"
        )
        report = lint.check_grounding(
            self._note(["UEM demand grows 25.38% a year through 2031."]), evidence
        )
        self.assertFalse(report["grounded"], report)
        self.assertIn("25.38", " ".join(report["unsupported"]))

    def test_a_year_is_not_a_figure_in_either_direction(self):
        # The three-digit head of a four-digit year used to be harvested as a number
        # ("202" from "2026"), which matched unrelated prose years both ways.
        report = lint.check_grounding(
            self._note(["The 2027 print is the one that matters."]), "Fiscal 2026 outlook"
        )
        self.assertTrue(report["grounded"], report)
        self.assertEqual(report["checked"], 0, report)

    def test_a_date_written_in_words_still_grounds_its_own_date(self):
        # The exclusions must not go so far that a real date stops being supported.
        report = lint.check_grounding(
            self._note(["Reports 2026-10-30, and the consensus is 1.88."]), self.EVIDENCE
        )
        self.assertTrue(report["grounded"], report)


class TestSourceGrounding(unittest.TestCase):
    """A citation is worth nothing if the figure is not in the source it names."""

    CATALOGUE = [
        {"id": "S1", "kind": "fundamentals", "text": "Price 60.81 Market Cap 7.0B"},
        {"id": "S4", "kind": "catalyst", "text": "NEXT EARNINGS 2026-10-30 consensus EPS 1.87559"},
        {"id": "S7", "kind": "news", "text": "Subprime auto loan delinquency rate hit 6.8%"},
    ]

    def _note(self, reason, cited):
        return {
            "description": "Lender",
            "reasons": [reason],
            "reason_sources": [[{"id": c} for c in cited]],
        }

    def test_figure_in_the_cited_source_passes(self):
        report = lint.check_source_grounding(
            self._note("Delinquency hit 6.8%, the worst in decades.", ["S7"]), self.CATALOGUE
        )
        self.assertTrue(report["ok"], report)

    def test_figure_in_the_packet_but_another_source_is_named(self):
        # Cited to the fundamentals block, but 6.8% lives in the headline.
        report = lint.check_source_grounding(
            self._note("Delinquency hit 6.8%, the worst in decades.", ["S1"]), self.CATALOGUE
        )
        self.assertFalse(report["ok"], report)
        self.assertIn("S7", report["mismatches"][0])
        self.assertIn("S1", report["mismatches"][0])

    def test_figure_that_is_nowhere_is_left_to_check_grounding(self):
        # Deliberately silent here: a derived figure has no home source, and naming
        # every one of them would bury the miscitations this check exists to find.
        report = lint.check_source_grounding(
            self._note("The 12.4% target implies a rerating.", ["S1"]), self.CATALOGUE
        )
        self.assertTrue(report["ok"], report)

    def test_counts_and_years_are_not_checked_against_a_source(self):
        report = lint.check_source_grounding(
            self._note("Four quarters into 2027, the 30-day revision window is flat.", ["S1"]),
            self.CATALOGUE,
        )
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["checked"], 0, report)

    def test_an_uncited_reason_is_not_reported_here(self):
        # Missing citations are a lint error; this check is about wrong ones.
        note = self._note("Delinquency hit 6.8%.", [])
        report = lint.check_source_grounding(note, self.CATALOGUE)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["checked"], 0, report)


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


class TestCatalystFallback(unittest.TestCase):
    """The measured fallback has to satisfy the note's own linter.

    Regression, found on ORCL: the fallback joined *every* justification fact into
    one line, which is 51 words against a 25-word budget. The breach is an error,
    and the repair round could never clear it because the revision's required shape
    omitted ``catalyst_why`` and so erased the writer's own sentence on every retry.
    """

    def _catalyst(self, **over):
        base = {
            "date": "2026-12-10",
            "basis": "scheduled",
            "same_slot_last_year": True,
            "median_gap_days": 91,
            "beat_streak": 4,
        }
        base.update(over)
        return base

    def test_the_old_join_really_did_blow_the_budget(self):
        """Keep the bug's signature honest: this is what ORCL shipped with."""
        from fig import catalyst as catalyst_mod
        from fig.prompts import WORD_BUDGET

        joined = "; ".join(catalyst_mod.justification_facts(self._catalyst()))
        self.assertEqual(lint.word_count(joined), 51)
        self.assertGreater(lint.word_count(joined), WORD_BUDGET["catalyst_why"])

    def test_fallback_fits_the_budget_when_every_fact_fires(self):
        from fig import catalyst as catalyst_mod
        from fig.prompts import WORD_BUDGET

        why = catalyst_mod.fallback_why(self._catalyst())
        self.assertLessEqual(lint.word_count(why), WORD_BUDGET["catalyst_why"], why)

    def test_fallback_is_one_clean_sentence(self):
        from fig import catalyst as catalyst_mod

        why = catalyst_mod.fallback_why(self._catalyst())
        self.assertEqual(why.count("."), 1, why)
        self.assertNotIn(".;", why)
        self.assertNotIn("; ", why)

    def test_fallback_prefers_the_beat_record(self):
        """The fact naming the bar the print must clear, not the one dating it."""
        from fig import catalyst as catalyst_mod

        why = catalyst_mod.fallback_why(self._catalyst())
        self.assertIn("Beat consensus", why)
        self.assertIn("moves the stock", why)

    def test_fallback_truncates_rather_than_exceeding_the_budget(self):
        from fig import catalyst as catalyst_mod

        why = catalyst_mod.fallback_why(self._catalyst(beat_streak=1234), max_words=5)
        self.assertLessEqual(lint.word_count(why), 5, why)

    def test_fallback_is_empty_without_a_catalyst(self):
        from fig import catalyst as catalyst_mod

        self.assertEqual(catalyst_mod.fallback_why({}), "")

    def test_a_note_with_no_written_why_still_lints_clean(self):
        """No catalyst_why from the model: the fallback must still be acceptable."""
        from fig.generate import assemble_writeup

        writeup = assemble_writeup(
            _fake_packet(),
            {
                "description": "Nonprime consumer loan lender",
                "reasons": ["Provisions rose 31% quarter over quarter, so losses accelerate."],
            },
            "short",
        )
        joined = " ".join(lint.lint_writeup(writeup)["issues"])
        self.assertNotIn("catalyst_no_justification", joined)
        self.assertNotIn("catalyst_why_too_long", joined)

    def test_repair_round_is_asked_to_keep_catalyst_why(self):
        """The shape that erased it is the half of the bug that made it permanent."""
        from fig.generate import _repair_messages

        messages = _repair_messages([], {"description": "x"}, ["[error] something"])
        self.assertIn("catalyst_why", messages[-1]["content"])


class TestNoLegs(unittest.TestCase):
    """`--no-legs` skips structuring without making the note look broken."""

    def test_parser_accepts_no_legs(self):
        from fig.cli import build_parser

        self.assertTrue(build_parser().parse_args(["generate", "ORCL", "--no-legs"]).no_legs)
        self.assertFalse(build_parser().parse_args(["generate", "ORCL"]).no_legs)

    def test_a_skipped_structure_says_so_in_the_note(self):
        from fig.generate import assemble_writeup

        packet = _fake_packet()
        packet["structures"] = {"short": {"error": "structuring skipped (--no-legs)"}}
        writeup = assemble_writeup(
            packet,
            {
                "description": "Nonprime consumer loan lender",
                "reasons": ["Provisions rose 31% quarter over quarter, so losses accelerate."],
            },
            "short",
        )
        self.assertNotIn("structuring", writeup)
        self.assertEqual(writeup["structure_error"], "structuring skipped (--no-legs)")
        self.assertIn(
            "[no option structure: structuring skipped (--no-legs)]",
            render.render_writeup(writeup),
        )


class TestSelectionPhrase(unittest.TestCase):
    """The index's selection sentence has to read as English in every combination.

    Regression: the no-floor case interpolated the number 1 and rendered
    "under a $150 share price and a no 1 floor floor".
    """

    def test_no_floor_disabled_reads_correctly(self):
        from fig.generate import _selection_phrase

        phrase = _selection_phrase(150.0, None, 3)
        self.assertEqual(
            phrase, "3 note(s) under a **$150** share price and **no market-cap floor**"
        )
        self.assertNotIn("no 1", phrase)
        self.assertNotIn("floor floor", phrase)

    def test_a_real_floor_is_named(self):
        from fig.generate import _selection_phrase

        self.assertEqual(
            _selection_phrase(150.0, 2e9, 3),
            "3 note(s) under a **$150** share price and a **$2.0B** floor",
        )

    def test_disabled_cap_reads_correctly(self):
        from fig.generate import _selection_phrase

        phrase = _selection_phrase(None, 2e9, 1)
        self.assertNotIn("no cap** share", phrase)
        self.assertIn("**no share-price cap**", phrase)


class TestRevisionScore(unittest.TestCase):
    """The screen ranks on the consensus revision, and price does not enter.

    Regression for the change that removed the revision-versus-price divergence:
    identical revision moves used to score ~30 points apart depending only on the
    direction of the price move, and 24 of 50 names in a real screen sat in the
    collapsed "aligned" branch.
    """

    def _row(self, **over):
        base = {
            "revisions_net_30d": None,
            "price_change_30d": None,
            "price_change_90d": None,
            "news_specific": 0,
            "structure_available": False,
        }
        base.update(over)
        return base

    def test_price_direction_no_longer_changes_anything(self):
        from fig import discover

        # Same revisions, opposite tapes: the old code scored these ~30 apart.
        falling = discover._score(self._row(revisions_net_30d=4, price_change_30d=-10))
        rising = discover._score(self._row(revisions_net_30d=4, price_change_30d=+10))
        self.assertEqual(falling[0], rising[0])
        self.assertEqual(falling[1], rising[1])
        self.assertEqual(falling[2], rising[2])

    def test_the_old_alignment_penalty_is_gone(self):
        """A name whose estimates and price agree now ties a dislocation of the same size."""
        from fig import discover

        aligned_short = discover._score(
            self._row(revisions_net_30d=-6, price_change_30d=-5)   # BABA's real shape
        )
        divergent_short = discover._score(
            self._row(revisions_net_30d=-6, price_change_30d=+15)  # same revisions, dislocation
        )
        self.assertEqual(aligned_short[1], divergent_short[1])
        self.assertEqual(aligned_short[2]["revisions"], 40.0)

    def test_side_comes_from_the_revision_sign(self):
        from fig import discover

        self.assertEqual(discover._score(self._row(revisions_net_30d=4))[0], "long")
        self.assertEqual(discover._score(self._row(revisions_net_30d=-4))[0], "short")
        # Flat estimates carry no side, so the long fallback stands.
        self.assertEqual(discover._score(self._row(revisions_net_30d=0))[0], "long")

    def test_no_price_component_remains(self):
        from fig import discover

        components = discover._score(
            self._row(revisions_net_30d=-3, price_change_30d=+9, price_change_90d=+55)
        )[2]
        self.assertIn("revisions", components)
        self.assertNotIn("divergence", components)
        # extended_move was pure price and is gone with it, however stretched the 90d.
        self.assertNotIn("extended_move", components)

    def test_magnitude_scales_then_saturates(self):
        from fig import discover

        for net, expected in ((1, 8.0), (3, 24.0), (5, 40.0), (22, 40.0)):
            got = discover._score(self._row(revisions_net_30d=net))[2]["revisions"]
            self.assertEqual(got, expected, f"net {net}")
            # The sign must not matter to the magnitude, only to the side.
            self.assertEqual(
                discover._score(self._row(revisions_net_30d=-net))[2]["revisions"], expected
            )

    def test_missing_revisions_scores_nothing_on_price(self):
        from fig import discover

        direction, score, components = discover._score(self._row(price_change_30d=-25))
        self.assertEqual(direction, "long")
        self.assertEqual(components.get("revisions"), 0.0)
        self.assertEqual(score, 0.0)


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


class TestTrendRecency(unittest.TestCase):
    """Stale evidence reads exactly like fresh evidence, so it is dropped."""

    def test_explicit_dates_only(self):
        from fig import research

        # packet._date_from_text assumes the current year for yearless forms, which
        # would make an old article look current. Not acceptable for dating.
        self.assertIsNone(research.source_date("Sept 18 (Reuters) - hiring slowed"))
        self.assertEqual(
            research.source_date("Sept 18, 2026 | 8:03 AM"), __import__("datetime").date(2026, 9, 18)
        )

    def test_month_year_is_enough(self):
        import datetime as dt

        from fig import research

        # The form stale evidence usually arrives in, and the one first missed.
        self.assertEqual(research.source_date("In December 2025, hiring slowed"), dt.date(2025, 12, 1))
        self.assertEqual(
            research.source_date("as of March 2026 profitability weakened"), dt.date(2026, 3, 1)
        )

    def test_url_date_is_preferred(self):
        import datetime as dt

        from fig import research

        self.assertEqual(
            research.source_date("body mentions 2024-01-02", "https://x.com/2026/09/18/a"),
            dt.date(2026, 9, 18),
        )

    def test_future_dates_are_not_publication_dates(self):
        from fig import research

        self.assertIsNone(research.source_date("guidance for 2028"))

    def test_age_threshold_is_under_a_year(self):
        from fig import research

        self.assertLessEqual(research.MAX_TREND_AGE_DAYS, 180)


class TestEvidenceVerdict(unittest.TestCase):
    """The verdict is sampled because the qualitative evidence varies by run."""

    def test_pressures_support_a_short(self):
        from fig import research

        trends = [{"stance": "pressure"}, {"stance": "pressure"}, {"stance": "support"}]
        result = research.evidence_verdict(trends, "short")
        self.assertEqual(result["verdict"], "confirms")
        self.assertEqual((result["supportive"], result["adverse"]), (2, 1))

    def test_the_same_evidence_contradicts_a_long(self):
        from fig import research

        trends = [{"stance": "pressure"}, {"stance": "pressure"}, {"stance": "support"}]
        self.assertEqual(research.evidence_verdict(trends, "long")["verdict"], "contradicts")

    def test_balanced_evidence_is_mixed(self):
        from fig import research

        trends = [{"stance": "pressure"}, {"stance": "support"}]
        self.assertEqual(research.evidence_verdict(trends, "short")["verdict"], "mixed")

    def test_no_stances_is_reported_not_guessed(self):
        from fig import research

        self.assertEqual(
            research.evidence_verdict([{"claim": "x"}], "long")["verdict"], "no-evidence"
        )


class TestPriceCap(unittest.TestCase):
    def test_default_cap_is_150(self):
        from fig import discover

        self.assertEqual(discover.DEFAULT_MAX_PRICE, 150.0)

    def test_gate_rejects_at_or_above_the_cap(self):
        from fig import discover

        rows = [
            {"symbol": "CHEAP", "price": 149.99, "score": 50, "has_options": True,
             "structure_available": True, "fwd_pe": 10.0},
            {"symbol": "EDGE", "price": 150.0, "score": 99, "has_options": True,
             "structure_available": True, "fwd_pe": 10.0},
            {"symbol": "PRICEY", "price": 2855.31, "score": 99, "has_options": True,
             "structure_available": True, "fwd_pe": 10.0},
        ]
        kept = discover.rank_candidates(rows, min_score=0)
        names = [row["symbol"] for row in kept]
        self.assertIn("CHEAP", names)
        self.assertNotIn("PRICEY", names)
        # At the cap is out: the rule is "under 150". AZO's single contract cost
        # $13,275 against a ~$4,500 unit, which is what the cap prevents.
        self.assertNotIn("EDGE", names)

    def test_cap_can_be_disabled(self):
        from fig import discover

        rows = [{"symbol": "PRICEY", "price": 2855.31, "score": 99, "has_options": True,
                 "structure_available": True, "fwd_pe": 10.0}]
        kept = discover.rank_candidates(rows, min_score=0, max_price=None)
        self.assertEqual([row["symbol"] for row in kept], ["PRICEY"])

    def test_loss_making_is_no_longer_filtered(self):
        """The owner's instruction: keep loss-making names.

        A negative forward PE means "Fwd PE" is not a valuation signal. It does not
        mean the idea is meaningless, and gating on it deleted real candidates.
        """
        from fig import discover

        rows = [{"symbol": "LOSER", "price": 20.0, "score": 60, "has_options": True,
                 "structure_available": True, "fwd_pe": -4.0}]
        kept = discover.rank_candidates(rows, min_score=0)
        self.assertEqual([row["symbol"] for row in kept], ["LOSER"])
        # Still recorded, so the note can state it.
        self.assertIn("loss-making (fwd PE not meaningful)", kept[0]["caveats"])

    def test_missing_option_chain_is_no_longer_filtered(self):
        """These facts come from free endpoints, and a bad response is
        indistinguishable from a genuine absence."""
        from fig import discover

        rows = [
            {"symbol": "NOCHAIN", "price": 20.0, "score": 60, "has_options": False,
             "structure_available": False, "fwd_pe": 12.0},
            {"symbol": "NOPAIR", "price": 20.0, "score": 60, "has_options": True,
             "structure_available": False, "fwd_pe": 12.0},
        ]
        kept = discover.rank_candidates(rows, min_score=0)
        self.assertEqual({row["symbol"] for row in kept}, {"NOCHAIN", "NOPAIR"})
        self.assertEqual(kept[0]["caveats"], ["no listed options reported"])
        self.assertEqual(kept[1]["caveats"], ["no usable expiry pair for the next 3 catalysts"])

    def test_strict_mode_still_available(self):
        from fig import discover

        rows = [{"symbol": "LOSER", "price": 20.0, "score": 60, "has_options": True,
                 "structure_available": True, "fwd_pe": -4.0}]
        kept = discover.rank_candidates(rows, min_score=0, require_positive_pe=True)
        self.assertEqual(kept, [])

    def test_only_the_price_cap_gates_by_default(self):
        import inspect

        from fig import discover

        defaults = inspect.signature(discover.rank_candidates).parameters
        self.assertFalse(defaults["require_structure"].default)
        self.assertFalse(defaults["require_positive_pe"].default)
        self.assertEqual(defaults["max_price"].default, discover.DEFAULT_MAX_PRICE)


class TestRanking(unittest.TestCase):
    """Conviction orders reading; it is not a prediction."""

    def _result(self, ticker, direction, score, days_out, quants, verdict):
        return {
            "writeup": {
                "ticker": ticker,
                "direction": direction,
                "description": "d",
                "catalyst": {"date": "2026-10-01", "days_out": days_out},
                "quants": quants,
                "generation": {"grounding": {"grounded": True}, "verdict": verdict},
            },
            "lint": {"score": score},
        }

    def test_ordering_is_by_conviction_descending(self):
        from fig import ranking

        agreed = {"eps_revisions_up_7d": 3, "eps_revisions_down_7d": 0,
                  "eps_revisions_up_30d": 8, "eps_revisions_down_30d": 1}
        split = {"eps_revisions_up_7d": 1, "eps_revisions_down_7d": 3,
                 "eps_revisions_up_30d": 8, "eps_revisions_down_30d": 1}
        strong = {"samples": 3, "confirmed": 3, "contradicted": 0}
        weak = {"samples": 3, "confirmed": 0, "contradicted": 3}

        entries = ranking.rank_ideas([
            self._result("WEAK", "long", 90, 100, split, weak),
            self._result("STRONG", "short", 90, 5, agreed, strong),
        ])
        self.assertEqual([e["ticker"] for e in entries], ["STRONG", "WEAK"])
        self.assertEqual(entries[0]["rank"], 1)
        self.assertGreater(entries[0]["conviction"], entries[1]["conviction"])

    def test_a_distant_catalyst_scores_lower_than_a_near_one(self):
        from fig import ranking

        agreed = {"eps_revisions_up_7d": 3, "eps_revisions_down_7d": 0,
                  "eps_revisions_up_30d": 8, "eps_revisions_down_30d": 1}
        verdict = {"samples": 3, "confirmed": 3, "contradicted": 0}
        near = ranking.rank_ideas([self._result("NEAR", "long", 90, 5, agreed, verdict)])[0]
        far = ranking.rank_ideas([self._result("FAR", "long", 90, 300, agreed, verdict)])[0]
        self.assertGreater(near["components"]["catalyst_proximity"],
                           far["components"]["catalyst_proximity"])

    def test_counts_split_long_and_short(self):
        from fig import ranking

        quants = {"eps_revisions_up_7d": 1, "eps_revisions_down_7d": 1,
                  "eps_revisions_up_30d": 2, "eps_revisions_down_30d": 2}
        verdict = {"samples": 2, "confirmed": 1, "contradicted": 0}
        entries = ranking.rank_ideas([
            self._result("A", "long", 90, 5, quants, verdict),
            self._result("B", "long", 90, 5, quants, verdict),
            self._result("C", "short", 90, 5, quants, verdict),
        ])
        counts = ranking.summarise(entries)
        self.assertEqual((counts["ideas"], counts["longs"], counts["shorts"]), (3, 2, 1))

    def test_evidence_component_uses_the_sample_share(self):
        from fig import ranking

        quants = {"eps_revisions_up_7d": 1, "eps_revisions_down_7d": 1,
                  "eps_revisions_up_30d": 2, "eps_revisions_down_30d": 2}
        entries = ranking.rank_ideas([
            self._result("A", "long", 90, 5, quants, {"samples": 4, "confirmed": 3, "contradicted": 0}),
            self._result("B", "long", 90, 5, quants, {"samples": 4, "confirmed": 0, "contradicted": 4}),
        ])
        by_ticker = {e["ticker"]: e for e in entries}
        self.assertGreater(by_ticker["A"]["components"]["evidence"],
                           by_ticker["B"]["components"]["evidence"])

    def test_weights_sum_to_one(self):
        from fig import ranking

        self.assertAlmostEqual(sum(ranking.WEIGHTS.values()), 1.0)


class TestEvidenceShapeChecks(unittest.TestCase):
    """The checks that exist because a true, well-sourced note was still wrong.

    Each fixture is the shape of a real failure, not a hypothetical: the PAYX note
    that reported a sequential revenue fall as deterioration, and the lead reason
    built on the older reading of a survey the packet had already superseded.
    """

    # The real comparison for Paychex's May 2026 quarter: revenue fell 11.2% from the
    # February quarter and grew 12.5% against the year-earlier quarter.
    YOY = [
        {"label": "Total Revenue", "qoq_pct": -11.2, "yoy_pct": 12.5,
         "conflict": True, "period": "2026-05-31"},
        {"label": "Net Income", "qoq_pct": -24.9, "yoy_pct": 41.5,
         "conflict": True, "period": "2026-05-31"},
        {"label": "Interest Expense", "qoq_pct": -5.0, "yoy_pct": 1.6,
         "conflict": False, "period": "2026-05-31"},
    ]

    def test_sequential_move_without_the_year_is_flagged(self):
        reason = (
            "The May quarter showed revenue down 11.2% and net income down 24.9% "
            "sequentially, while the stock trades at 19.5x forward earnings."
        )
        found = lint.sequential_without_year(reason, {"yoy": self.YOY})
        self.assertTrue(found["conflict"])
        self.assertEqual(found["label"], "Total Revenue")

    def test_pairing_the_two_comparisons_passes(self):
        reason = (
            "Revenue fell 11.2% quarter over quarter but rose 12.5% year over year, "
            "so the sequential move is the calendar, not the business."
        )
        self.assertIsNone(lint.sequential_without_year(reason, {"yoy": self.YOY}))

    def test_a_non_conflicting_sequential_move_is_only_a_warning(self):
        reason = "Interest expense rose 4% sequentially and the trend is intact."
        found = lint.sequential_without_year(reason, {"yoy": self.YOY})
        self.assertIsNotNone(found)
        self.assertFalse(found["conflict"])

    def test_ignores_deal_fires_when_growth_is_called_organic(self):
        hints = {"deal": [{"label": "Goodwill", "period": "2025-05-31",
                           "change_pct": 139.8, "confirmed": True}]}
        found = lint.ignores_deal(
            ["Revenue grew 16.9% and will keep growing."], hints
        )
        self.assertTrue(found["confirmed"])

    def test_only_a_goodwill_step_is_treated_as_proof(self):
        """An intangibles step is suggestive, so it warns rather than errors."""
        confirmed = lint.ignores_deal(
            ["Revenue grew."], {"deal": [{"label": "Goodwill", "confirmed": True}]}
        )
        suspected = lint.ignores_deal(
            ["Revenue grew."], {"deal": [{"label": "Other Intangible Assets", "confirmed": False}]}
        )
        self.assertTrue(confirmed["confirmed"])
        self.assertFalse(suspected["confirmed"])

    def test_ignores_deal_clears_when_the_acquisition_is_named(self):
        hints = {"deal": [{"label": "Other Intangible Assets", "change_pct": 901.2}]}
        self.assertIsNone(
            lint.ignores_deal(["The Paycor acquisition supplies most of the growth."], hints)
        )
        self.assertIsNone(
            lint.ignores_deal(["Growth is Paycor synergies, not new clients."], hints)
        )

    def test_long_horizon_payoff_is_flagged(self):
        found = lint.speculative_reason(
            "AI agents will eventually replace payroll staff, which leads to fewer "
            "small companies and lower revenue over time."
        )
        self.assertIsNotNone(found)

    def test_watch_is_required_when_the_print_is_close(self):
        problems = lint.watch_problems([], {"catalyst_days": 3})
        self.assertEqual(problems[0][1], "watch_missing")
        self.assertEqual(problems[0][0], "error")

    def test_watch_is_optional_with_no_dated_catalyst(self):
        self.assertEqual(lint.watch_problems([], {"catalyst_days": None}), [])

    def test_watch_line_needs_both_readings(self):
        vague = lint.watch_problems(
            ["Client counts matter for the payroll thesis."], {"catalyst_days": 3}
        )
        self.assertIn("watch_no_test", [code for _, code, _ in vague])
        paired = lint.watch_problems(
            ["Client counts: flat or falling confirms the thesis; rising breaks it."],
            {"catalyst_days": 3},
        )
        self.assertNotIn("watch_no_test", [code for _, code, _ in paired])

    def test_superseded_reading_is_caught(self):
        """The May job-openings reading, with June's opposite reading uncited."""
        catalogue = [
            {
                "id": "S1", "kind": "research", "provider": "nfib.com", "date": "2026-06-01",
                "label": "nfib.com: In May 2026, small-business job openings fell to 29%",
                "text": (
                    "In May 2026, small-business job openings fell to 29%, the lowest "
                    "since May 2020. Fewer job openings mean slower payroll headcount "
                    "growth for Paychex."
                ),
            },
            {
                "id": "S2", "kind": "research", "provider": "nfib.com", "date": "2026-07-01",
                "label": "nfib.com: In June 2026, 51% of small businesses reported few or no qualified workers",
                "text": (
                    "In June 2026, 51% of small businesses reported few or no qualified "
                    "workers, highest since September 2024. Hiring difficulty can limit "
                    "headcount growth for Paychex."
                ),
            },
        ]
        writeup = {
            "reasons": ["Job openings fell to 29%, the lowest since May 2020."],
            "reason_sources": [[catalogue[0]]],
        }
        findings = lint.superseded_readings(writeup, catalogue)
        self.assertEqual(len(findings), 1)
        self.assertIn("S2", findings[0])

    def test_unrelated_later_article_is_not_a_superseded_reading(self):
        catalogue = [
            {
                "id": "S1", "kind": "research", "provider": "nfib.com", "date": "2026-06-01",
                "label": "nfib.com: job openings fell to 29%",
                "text": "In May 2026, small-business job openings fell to 29%, the lowest "
                        "since May 2020. Fewer job openings mean slower payroll growth.",
            },
            {
                "id": "S2", "kind": "research", "provider": "nfib.com", "date": "2026-07-01",
                "label": "nfib.com: capital spending plans rose",
                "text": "In June 2026, capital spending plans rose to 24%, the highest "
                        "since 2022. Stronger investment supports equipment demand.",
            },
        ]
        writeup = {
            "reasons": ["Job openings fell to 29%."],
            "reason_sources": [[catalogue[0]]],
        }
        self.assertEqual(lint.superseded_readings(writeup, catalogue), [])

    def test_canonical_label_matches_the_two_sources(self):
        from fig.quants import canonical_label

        self.assertEqual(
            canonical_label("Earnings Before Interest and Tax"), "EBIT"
        )
        # The alias must not rewrite a label it has no mapping for.
        self.assertEqual(canonical_label("Total Revenue"), "Total Revenue")

    def test_year_ago_column_is_found_by_gap_not_offset(self):
        from fig.quants import _year_ago_index

        self.assertEqual(
            _year_ago_index(["2026-05-31", "2026-02-28", "2025-11-30", "2025-08-31", "2025-05-31"]),
            4,
        )
        # A series with no year-earlier column must return None, not the last column.
        self.assertIsNone(_year_ago_index(["2026-05-31", "2026-02-28", "2025-11-30"]))


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


class TestNewsFeedOutage(unittest.TestCase):
    """A dead free feed must not cost the note -- and must not vanish either.

    Nasdaq's news endpoint returned 403 across a whole run (six of ten names), and
    ``collect_news`` used to raise, so each of those notes was dropped entirely.
    One endpoint's condition says nothing about the company, so the note is now
    built from the feeds that answered and the outage is recorded on the packet.
    """

    _ITEM = {
        "title": "Test Co raises guidance",
        "url": "https://example.com/test-co-guidance",
        "publisher": "example.com",
        "summary": "Test Co raised full-year guidance.",
    }

    def _collect(self, *, nasdaq_dies: bool = True, yahoo_dies: bool = False):
        from unittest.mock import patch

        from fig import packet

        def yahoo_news(symbol, limit=12):
            if yahoo_dies:
                raise RuntimeError("HTTP 403 for https://yahoo/news")
            return [self._ITEM]

        def nasdaq_news(symbol, limit=15):
            if nasdaq_dies:
                raise RuntimeError("GET failed after 3 attempts: nasdaq articlebysymbol")
            return [self._ITEM]

        with (
            patch.object(packet.yahoo, "profile", lambda s: {"name": "Test Co"}),
            patch.object(packet.yahoo, "news", yahoo_news),
            patch.object(packet.nasdaq, "news_for_symbol", nasdaq_news),
        ):
            return packet.collect_news("TEST")

    def test_a_dead_feed_is_recorded_and_the_surviving_feed_is_kept(self):
        items, failures = self._collect()

        self.assertEqual([f["source"] for f in failures], ["nasdaq"])
        self.assertIn("articlebysymbol", failures[0]["error"])
        self.assertTrue(items, "the note must still carry the yahoo coverage")
        self.assertEqual(items[0]["title"], self._ITEM["title"])

    def test_both_feeds_down_still_returns_rather_than_raising(self):
        items, failures = self._collect(yahoo_dies=True)

        self.assertEqual(items, [])
        self.assertEqual([f["source"] for f in failures], ["yahoo", "nasdaq"])

    def test_healthy_feeds_record_no_failure(self):
        items, failures = self._collect(nasdaq_dies=False)

        self.assertEqual(failures, [])
        self.assertTrue(items)

    def test_the_outage_is_printed_in_the_note(self):
        text = render.render_writeup(
            {
                "ticker": "TEST",
                "description": "Test Co.",
                "news_failures": [{"source": "nasdaq", "error": "RuntimeError: HTTP 403"}],
            }
        )

        self.assertIn("nasdaq feed unavailable when this note was built", text)
        self.assertIn("HTTP 403", text)

    def test_a_healthy_note_prints_no_outage_line(self):
        text = render.render_writeup({"ticker": "TEST", "description": "Test Co."})

        self.assertNotIn("feed unavailable", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
