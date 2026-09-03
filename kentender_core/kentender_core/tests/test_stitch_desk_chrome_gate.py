# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Hard gate — Stitch Desk chrome baseline (shared CSS + fixture opt-in).

Region/title layout guards are not enough. This gate fails when a registered
Stitch Desk surface omits `kt-stitch-canvas` or when the shared Desk-bleed
defeat sheet is weakened.
"""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_core.stitch_desk_chrome_registry import (
	REQUIRED_SHARED_CSS_MARKERS,
	SHARED_CHROME_CSS_REL,
	STITCH_CANVAS_CLASS,
	STITCH_DESK_SURFACES,
)


def _app_public(app: str) -> Path:
	return Path(frappe.get_app_path(app)) / "public"


def _kentender_v1_root() -> Path:
	"""Resolve monorepo `apps/kentender_v1` whether apps are symlinked or nested."""
	here = Path(__file__).resolve()
	for parent in here.parents:
		if parent.name == "kentender_v1" and (parent / "tests" / "ui").is_dir():
			return parent
		candidate = parent / "kentender_v1"
		if candidate.is_dir() and (candidate / "tests" / "ui").is_dir():
			return candidate
	raise AssertionError("Could not locate apps/kentender_v1 from test path")


def _read(path: Path) -> str:
	return path.read_text(encoding="utf-8")


class TestStitchDeskChromeGate(FrappeTestCase):
	def test_shared_chrome_css_loaded_and_complete(self):
		css_path = Path(frappe.get_app_path("kentender_core")) / SHARED_CHROME_CSS_REL
		self.assertTrue(css_path.is_file(), css_path)
		css = _read(css_path)
		for marker in REQUIRED_SHARED_CSS_MARKERS:
			self.assertIn(marker, css, f"shared chrome CSS missing marker: {marker}")

		# Filled primary hover must keep white — never on-primary-container ink / Desk black.
		hover_idx = css.find("button.bg-primary:hover")
		self.assertGreaterEqual(hover_idx, 0)
		hover_slice = css[hover_idx : hover_idx + 500]
		self.assertIn("#ffffff", hover_slice)
		self.assertIn("#0052cc", hover_slice)
		self.assertNotIn("var(--kt-stitch-on-primary-container)", hover_slice)
		self.assertNotIn("color: #7b9ee0", hover_slice)

		# Editable inputs must default to white — never surface tint.
		input_idx = css.find("Editable inputs: white fill")
		self.assertGreaterEqual(input_idx, 0)
		# Block ends at Tailwind Forms select chevron (next major section).
		input_end = css.find("Tailwind Forms select chevron", input_idx)
		self.assertGreater(input_end, input_idx)
		input_slice = css[input_idx:input_end]
		self.assertIn("background-color: #ffffff !important", input_slice)
		self.assertIn("background-color: #e2e2e8 !important", input_slice)
		self.assertIn("cursor: not-allowed", input_slice)
		self.assertNotIn("var(--kt-stitch-surface)", input_slice)

		# Section/table headers: DS muted heads + rounded cards (not primary-fixed / square).
		section_idx = css.find("DS section/table chrome")
		self.assertGreaterEqual(section_idx, 0)
		# Block ends at Win98 button reset (next major section after tokens).
		section_end = css.find("Desk/Bootstrap must not paint Win98", section_idx)
		self.assertGreater(section_end, section_idx)
		section_slice = css[section_idx:section_end]
		self.assertIn("--kt-stitch-table-head", section_slice)
		self.assertIn("thead tr.bg-surface-container-low", section_slice)
		self.assertIn(".rounded-xl", section_slice)
		self.assertIn("border-radius: 0.75rem !important", section_slice)
		self.assertIn("kt-ds-section-title", section_slice)
		self.assertIn("kt-ds-table-head", section_slice)
		self.assertNotIn("border-radius: 0 !important", section_slice)
		self.assertNotIn("inset 3px 0 0", section_slice)
		self.assertNotIn("#d7e2ff", section_slice)

		from kentender_core import hooks as core_hooks

		includes = "\n".join(core_hooks.app_include_css or [])
		self.assertIn("kt_stitch_desk_chrome.css", includes)

	def test_registered_fixtures_opt_into_canvas_class(self):
		self.assertGreaterEqual(len(STITCH_DESK_SURFACES), 2)
		for surface in STITCH_DESK_SURFACES:
			rel = Path(surface["fixture_rel"])
			# fixture_rel is like public/js/... — strip public/ for app public root
			fixture = _app_public(surface["app"]) / rel.relative_to("public")
			self.assertTrue(fixture.is_file(), f"{surface['id']}: missing {fixture}")
			text = _read(fixture)
			self.assertIn(
				STITCH_CANVAS_CLASS,
				text,
				f"{surface['id']}: fixture must include class `{STITCH_CANVAS_CLASS}` on Stitch root",
			)
			self.assertNotIn("cdn.tailwindcss.com", text)

	def test_playwright_helper_and_cross_module_spec_cover_chrome(self):
		"""Runtime chrome asserts must exist — visibility-only smoke is insufficient."""
		v1 = _kentender_v1_root()
		helper = v1 / "tests" / "ui" / "helpers" / "stitchDeskChrome.ts"
		self.assertTrue(helper.is_file(), helper)
		helper_src = _read(helper)
		self.assertIn("assertStitchDeskChrome", helper_src)
		self.assertIn("assertFilledPrimaryCtaHover", helper_src)
		self.assertIn("assertEditableInputs", helper_src)
		self.assertIn("assertStitchSectionTableChrome", helper_src)
		# DS primary #003d9b / hover #0052cc; muted table head (not primary-fixed #d7e2ff).
		self.assertIn("rgb(0, 61, 155)", helper_src)
		self.assertIn("rgb(0, 82, 204)", helper_src)
		self.assertIn("rgb(255, 255, 255)", helper_src)
		self.assertIn("outset", helper_src)
		self.assertNotIn("rgb(215, 226, 255)", helper_src)
		self.assertNotIn("rgb(0, 31, 72)", helper_src)

		cross = v1 / "tests" / "ui" / "smoke" / "stitch-desk" / "stitch-desk-chrome.spec.ts"
		self.assertTrue(cross.is_file(), cross)
		spec = _read(cross)
		self.assertIn("assertStitchDeskChrome", spec)
		self.assertIn("strategy-portfolio", spec)
		self.assertIn("strategy-plan-create", spec)
		self.assertIn("assertEditableInputs", spec)
		for surface in STITCH_DESK_SURFACES:
			self.assertIn(surface["desk_route"], spec, surface["id"])
			self.assertIn(surface["primary_cta_testid"], spec, surface["id"])
