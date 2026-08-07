# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static forbid-list: Demand review must not re-mute app-wide primary-fixed section chrome."""

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

	def test_ui05_section_heads_not_muted_to_surface_low(self):
		css = CSS.read_text(encoding="utf-8")
		# Forbidden: painting enrichment section heads drab #f4f3f9 (image-1 regression).
		mute_block = re.search(
			r"kt-dem-ui05-card-head[^{]*\{[^}]*#f4f3f9",
			css,
			flags=re.S,
		)
		self.assertIsNone(
			mute_block,
			"demands_review.css must not mute .kt-dem-ui05-card-head to #f4f3f9 "
			"(app-wide primary-fixed wins)",
		)
		enrich_mute = re.search(
			r"kt-dem-enrichment-active[^{]*\.rounded-xl\s*>\s*\.bg-surface-container-low[^{]*\{[^}]*#f4f3f9",
			css,
			flags=re.S,
		)
		self.assertIsNone(
			enrich_mute,
			"must not mute enrichment .rounded-xl > .bg-surface-container-low to #f4f3f9",
		)

	def test_ui06_cards_not_forced_rounded(self):
		css = CSS.read_text(encoding="utf-8")
		# Forbidden: border-radius 0.75rem on UI-06 section cards (defeats square lock).
		rounded_override = re.search(
			r"kt-dem-ui06-card\.rounded-xl[^{]*\{[^}]*border-radius:\s*0\.75rem",
			css,
			flags=re.S,
		)
		self.assertIsNone(
			rounded_override,
			"demands_review.css must not force 0.75rem radius on .kt-dem-ui06-card "
			"(square cards are app-wide)",
		)
		# Forbidden: mute recommendation section head to drab #f4f3f9 (same as Summary).
		rec_mute = re.search(
			r"kt-dem-ui06-recommend-head[^{]*\{[^}]*#f4f3f9",
			css,
			flags=re.S,
		)
		self.assertIsNone(
			rec_mute,
			"must not mute .kt-dem-ui06-recommend-head to #f4f3f9 "
			"(app-wide primary-fixed wins for all section heads)",
		)

	def test_ui06_summary_strategy_have_primary_fixed_bands(self):
		html = FIXTURE.read_text(encoding="utf-8")
		# Extract budget host region roughly.
		idx = html.find('data-testid="kt-dem-ui06-summary"')
		self.assertGreater(idx, 0)
		# Summary section must open with a direct-child surface-low band (not inline-only title).
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
				f"UI-05 card head must include bg-surface-container-low for primary-fixed: {cls}",
			)

	def test_no_wrong_precedence_comments_for_summary_strategy(self):
		css = CSS.read_text(encoding="utf-8")
		fixture = FIXTURE.read_text(encoding="utf-8")
		blob = css + "\n" + fixture
		# Do not document the wrong lock for Funding Summary / Strategy.
		bad = re.search(
			r"(?i)(funding summary|strategy alignment).{0,80}(no primary-fixed|inline navy titles)",
			blob,
		)
		self.assertIsNone(
			bad,
			"do not claim Summary/Strategy use inline titles / no primary-fixed",
		)


if __name__ == "__main__":
	unittest.main()
