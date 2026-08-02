# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-03…09 — Add/Edit drawers must not dismiss on backdrop click (data-loss guard)."""

from __future__ import annotations

import unittest
from pathlib import Path

_JS_DIR = Path(__file__).resolve().parents[2] / "public" / "js"

# (screen, js filename, overlay testid)
_CFG_DRAWERS = (
	("CFG-03", "it_tender_configuration_it_requirements_page.js", "kt-cl-cfg03-drawer-overlay"),
	("CFG-04", "it_tender_configuration_implementation_schedule_page.js", "kt-cl-cfg04-drawer-overlay"),
	("CFG-05", "it_tender_configuration_system_inventory_page.js", "kt-cl-cfg05-drawer-overlay"),
	("CFG-06", "it_tender_configuration_price_schedule_page.js", "kt-cl-cfg06-drawer-overlay"),
	("CFG-07", "it_tender_configuration_evaluation_setup_page.js", "kt-cl-cfg07-drawer-overlay"),
	("CFG-08", "it_tender_configuration_forms_and_evidence_page.js", "kt-cl-cfg08-drawer-overlay"),
	("CFG-09", "it_tender_configuration_scc_page.js", "kt-cl-cfg09-drawer-overlay"),
)


class TestCfgDrawerDismissGuard(unittest.TestCase):
	def test_cfg_overlays_are_explicit_dismiss_only(self) -> None:
		for screen, filename, overlay_tid in _CFG_DRAWERS:
			with self.subTest(screen=screen):
				js = (_JS_DIR / filename).read_text(encoding="utf-8")
				self.assertIn(f'data-testid="{overlay_tid}"', js, screen)
				self.assertIn('data-dismiss="explicit-only"', js, screen)
				# Regression: overlay click handler previously called closeDrawer()
				self.assertNotIn(
					f"[data-testid='{overlay_tid}']\", function (e) {{\n"
					"\t\t\tif (e.target === this) {\n"
					"\t\t\t\tcloseDrawer();",
					js,
					screen,
				)
				self.assertIn("[data-action='close-drawer']", js, screen)


class TestCfgRelatedFormOverlayDismissGuard(unittest.TestCase):
	"""Create / WF form overlays that capture typed state must not dismiss on backdrop."""

	def test_create_modal_explicit_dismiss_only(self) -> None:
		modal_js = (_JS_DIR / "it_tender_configuration_create_modal.js").read_text(encoding="utf-8")
		comp_js = (
			Path(__file__).resolve().parents[4]
			/ "kentender_core"
			/ "kentender_core"
			/ "public"
			/ "js"
			/ "kt_cl_components.js"
		).read_text(encoding="utf-8")
		self.assertIn('data-testid="kt-cl-uim01-overlay"', comp_js)
		self.assertIn('data-dismiss="explicit-only"', comp_js)
		self.assertNotIn(
			'if ($(e.target).is(\'[data-testid="kt-cl-uim01-overlay"]\'))',
			modal_js,
		)
		self.assertIn('[data-action="close"]', modal_js)

	def test_wf02_form_overlays_explicit_dismiss_only(self) -> None:
		js = (_JS_DIR / "it_tender_configuration_review_and_approval_page.js").read_text(
			encoding="utf-8"
		)
		self.assertIn('data-testid="kt-cl-wf02-finding-drawer"', js)
		self.assertIn('data-dismiss="explicit-only"', js)
		# Finding backdrop must not wire data-action=close-modal
		self.assertNotIn(
			'kt-cl-wf02-drawer-backdrop" data-action="close-modal"',
			js,
		)
		self.assertNotIn(
			"[data-testid='kt-cl-wf02-approve-modal']\", function (e) {\n"
			"\t\t\tif (e.target === this) {\n"
			"\t\t\t\tcloseModal();",
			js,
		)

	def test_wf03_return_overlay_explicit_dismiss_only(self) -> None:
		js = (_JS_DIR / "it_tender_configuration_render_preview_page.js").read_text(encoding="utf-8")
		self.assertIn('data-testid="kt-cl-wf03-return-modal"', js)
		self.assertIn('data-dismiss="explicit-only"', js)
		self.assertNotIn(
			'kt-cl-wf03-drawer-backdrop" data-action="close-return"',
			js,
		)

	def test_bidder_form_drawers_explicit_dismiss_only(self) -> None:
		tp = (_JS_DIR / "technical_proposal_web.js").read_text(encoding="utf-8")
		s600 = (_JS_DIR / "qualification_and_capability_web.js").read_text(encoding="utf-8")
		self.assertNotIn("t.closest(\"[data-testid='kt-tp-drawer-backdrop']\")", tp)
		self.assertNotIn("t.closest(\"[data-testid='kt-s600-drawer-backdrop']\")", s600)
		self.assertIn("[data-tp-drawer-close]", tp)
		self.assertIn("[data-s600-drawer-close]", s600)
