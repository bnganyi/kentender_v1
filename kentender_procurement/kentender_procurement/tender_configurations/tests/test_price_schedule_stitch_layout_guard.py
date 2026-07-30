# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static layout guard — Price Schedule Stitch 01–04 fidelity."""

from __future__ import annotations

import unittest
from pathlib import Path

_APP = Path(__file__).resolve().parents[2]
_WWW = _APP / "www" / "tenders"
_JS = _APP / "public" / "js"
_CSS = _APP / "public" / "css"


def _read(path: Path) -> str:
	return path.read_text(encoding="utf-8")


class TestPriceScheduleStitchLayoutGuard(unittest.TestCase):
	def test_overview_has_progress_bento_status_pills_and_footer(self) -> None:
		html = _read(_WWW / "price_schedule.html")
		self.assertIn('data-testid="kt-ps-root"', html)
		self.assertIn('data-testid="kt-ps-progress"', html)
		self.assertIn("kt-ps-progress-card", html)
		self.assertIn('data-testid="kt-ps-progress-label"', html)
		self.assertIn('data-testid="kt-ps-schedules-table"', html)
		self.assertIn("kt-ps-bento", html)
		self.assertIn("kt-ps-status-pill", html)
		self.assertIn("Schedule", html)
		self.assertIn("Progress", html)
		self.assertIn("Status", html)
		self.assertIn("Action", html)
		self.assertIn('data-testid="kt-ps-offer-tabs"', html)
		self.assertIn('data-testid="kt-ps-lot-selector"', html)
		self.assertIn("Back to Checklist", html)
		self.assertIn('data-testid="kt-ps-continue"', html)
		self.assertNotIn("cdn.tailwindcss.com", html)
		# Must not lean on FoT/qualification generic chrome for the canvas
		self.assertNotIn("kt-fot-main-inner", html)
		self.assertNotIn("kt-s600-table", html)

	def test_editor_has_supply_columns_and_save(self) -> None:
		html = _read(_WWW / "price_schedule_schedule.html")
		self.assertIn('data-testid="kt-ps-editor-root"', html)
		self.assertIn("Item", html)
		self.assertIn("Description", html)
		self.assertIn("Qty", html)
		self.assertIn("Unit", html)
		self.assertIn("Country of Origin", html)
		self.assertIn("Currency", html)
		self.assertIn("Unit Price", html)
		self.assertIn("Total", html)
		self.assertIn("kt-ps-bento", html)
		self.assertIn('data-testid="kt-ps-save-draft"', html)
		self.assertIn('data-testid="kt-ps-editor-progress-label"', html)
		self.assertIn('data-testid="kt-ps-editor-progress-fill"', html)
		self.assertIn("unit_price_display", html)
		self.assertIn("line_total_display", html)
		self.assertIn("Back to Price Schedule", html)
		self.assertIn('href="{{ e.section_url }}"', html)
		self.assertNotIn("cdn.tailwindcss.com", html)
		self.assertNotIn("Secure Bid Environment", html)
		js = _read(_JS / "price_schedule_web.js")
		self.assertIn("refreshEditorProgress", js)
		self.assertIn("formatMoney", js)
		self.assertIn("parseMoney", js)

	def test_review_has_attention_summary_and_complete_to_checklist(self) -> None:
		html = _read(_WWW / "price_schedule_review.html")
		self.assertIn('data-testid="kt-ps-review-root"', html)
		self.assertIn("Needs Attention", html)
		self.assertIn("kt-ps-attention", html)
		self.assertIn('data-testid="kt-ps-summary-table"', html)
		self.assertIn("kt-ps-status-pill", html)
		self.assertIn("Lot", html)
		self.assertIn("Schedule", html)
		self.assertIn("Currency", html)
		self.assertIn("Subtotal", html)
		self.assertIn("Complete Price Schedule", html)
		self.assertIn("Back to Price Schedule", html)
		self.assertIn('href="{{ r.section_url }}"', html)
		self.assertNotIn("Secure Bid Environment", html)
		self.assertNotIn("cdn.tailwindcss.com", html)
		js = _read(_JS / "price_schedule_web.js")
		self.assertIn("complete_price_schedule", js)
		self.assertIn('getAttribute("data-workspace-url")', js)
		self.assertIn("returning to checklist", js)
		self.assertIn("save_price_schedule_lines", js)

	def test_hooks_register_dedicated_routes(self) -> None:
		hooks = _read(_APP / "hooks.py")
		self.assertIn("price_schedule/review", hooks)
		self.assertIn("price_schedule/schedules/<schedule_key>", hooks)
		self.assertIn('to_route": "tenders/price_schedule"', hooks)

	def test_css_fixed_action_footer_and_stitch_tokens(self) -> None:
		css = _read(_CSS / "price_schedule_web.css")
		foot = css.split(".kt-ps-foot {", 1)[1].split("}", 1)[0]
		self.assertIn("position: fixed", foot)
		self.assertNotIn("position: sticky", foot)
		self.assertIn("bottom: 0", foot)
		self.assertIn("left: var(--kt-a2-sidebar", css)
		self.assertIn(".kt-ps-status-pill", css)
		self.assertIn(".kt-ps-bento", css)
		self.assertIn(".kt-ps-progress-card", css)
