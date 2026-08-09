# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static forbid-list: Demand review must follow DS muted section chrome (not primary-fixed / square)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
CSS = APP_ROOT / "public" / "css" / "demands_review.css"
FIXTURE = APP_ROOT / "public" / "js" / "demands_ui_fixtures" / "review.js"


class TestDemandsReviewChromeGate(unittest.TestCase):
	def test_css_exists(self):
		self.assertTrue(CSS.is_file(), f"missing {CSS}")
		self.assertTrue(FIXTURE.is_file(), f"missing {FIXTURE}")

	def test_must_not_reintroduce_primary_fixed_section_heads(self):
		css = CSS.read_text(encoding="utf-8")
		# Forbidden: re-pin section/table heads to legacy primary-fixed #d7e2ff.
		for needle in ("#d7e2ff", "#D7E2FF"):
			self.assertNotIn(
				needle,
				css,
				"demands_review.css must not re-pin primary-fixed #d7e2ff "
				"(DS muted heads win via kt_stitch_desk_chrome)",
			)
		navy_inset = re.search(
			r"inset\s+3px\s+0\s+0",
			css,
			flags=re.I,
		)
		self.assertIsNone(
			navy_inset,
			"demands_review.css must not re-introduce navy inset section bands",
		)

	def test_must_not_force_square_cards(self):
		css = CSS.read_text(encoding="utf-8")
		# Forbidden: square-card lock that fights DS rounded-xl / rounded-lg.
		square = re.search(
			r"\.kt-dem[^{]*rounded-xl[^{]*\{[^}]*border-radius:\s*0\s*!important",
			css,
			flags=re.S,
		)
		self.assertIsNone(
			square,
			"demands_review.css must not force border-radius: 0 on Stitch cards "
			"(DS rounded cards win)",
		)

	def test_ui06_summary_strategy_have_surface_low_bands(self):
		html = FIXTURE.read_text(encoding="utf-8")
		idx = html.find('data-testid="kt-dem-ui06-summary"')
		self.assertGreater(idx, 0)
		# Summary section must open with a direct-child surface-low band (muted DS).
		summary_slice = html[idx : idx + 800]
		self.assertIn("bg-surface-container-low", summary_slice)
		self.assertNotIn("kt-dem-ui06-inline-title", summary_slice)
		strat_idx = html.find('data-testid="kt-dem-ui06-strategy-check"')
		self.assertGreater(strat_idx, 0)
		strat_slice = html[strat_idx : strat_idx + 800]
		self.assertIn("bg-surface-container-low", strat_slice)
		self.assertNotIn("kt-dem-ui06-inline-title", strat_slice)
		rec_idx = html.find('data-testid="kt-dem-ui06-recommendation"')
		self.assertGreater(rec_idx, 0)
		rec_slice = html[rec_idx : rec_idx + 500]
		self.assertIn("bg-surface-container-low", rec_slice)
		self.assertIn("kt-dem-ui06-recommend-head", rec_slice)
		# Same band height as Summary — px-4 py-3, not taller px-5 py-4.
		self.assertRegex(
			rec_slice,
			r"kt-dem-ui06-recommend-head[^>]*(?:px-4|py-3)",
		)
		self.assertNotRegex(
			rec_slice,
			r'kt-dem-ui06-recommend-head[^"]*(?:px-5|py-4)',
		)

	def test_ui05_card_heads_opt_into_surface_low(self):
		html = FIXTURE.read_text(encoding="utf-8")
		heads = re.findall(r'class="([^"]*kt-dem-ui05-card-head[^"]*)"', html)
		self.assertGreaterEqual(len(heads), 4)
		for cls in heads:
			self.assertIn(
				"bg-surface-container-low",
				cls,
				f"UI-05 card head must include bg-surface-container-low for DS muted band: {cls}",
			)

	def test_no_legacy_primary_fixed_precedence_comments(self):
		css = CSS.read_text(encoding="utf-8")
		fixture = FIXTURE.read_text(encoding="utf-8")
		blob = css + "\n" + fixture
		bad = re.search(
			r"(?i)(app-wide primary-fixed|square cards are app-wide|primary-fixed wins)",
			blob,
		)
		self.assertIsNone(
			bad,
			"retire primary-fixed / square-card lock language from Demands review chrome",
		)


if __name__ == "__main__":
	unittest.main()
