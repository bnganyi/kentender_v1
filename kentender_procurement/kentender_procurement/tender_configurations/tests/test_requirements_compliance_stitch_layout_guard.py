# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static layout guard — Requirements Compliance Stitch 01/02/03 fidelity."""

from __future__ import annotations

import unittest
from pathlib import Path

_APP = Path(__file__).resolve().parents[2]
_WWW = _APP / "www" / "tenders"
_JS = _APP / "public" / "js"
_CSS = _APP / "public" / "css"


def _read(path: Path) -> str:
	return path.read_text(encoding="utf-8")


class TestRequirementsComplianceStitchLayoutGuard(unittest.TestCase):
	def test_workspace_has_domains_and_mode_columns(self) -> None:
		html = _read(_WWW / "requirements_compliance.html")
		self.assertIn('data-testid="kt-rc-workspace-root"', html)
		self.assertIn("Requirement Domains", html)
		self.assertIn('data-testid="kt-rc-requirements-table"', html)
		self.assertIn('data-testid="kt-rc-progress-label"', html)
		self.assertIn('data-testid="kt-rc-progress-bar"', html)
		self.assertIn("Reference", html)
		self.assertIn("Mode", html)
		self.assertIn('data-testid="kt-rc-goto-review"', html)
		self.assertIn("kt-a4-drawer", html)
		self.assertIn("Save draft", html)
		self.assertIn("Save & Next", html)
		self.assertNotIn("cdn.tailwindcss.com", html)

	def test_matrix_js_updates_rc_progress_testids(self) -> None:
		"""Regression: applyMatrix must refresh kt-rc-progress-* (not only kt-a4-*)."""
		js = _read(_JS / "requirement_matrix_web.js")
		self.assertIn("kt-rc-progress-label", js)
		self.assertIn("kt-rc-progress-bar", js)
		self.assertIn("function applyMatrix", js)

	def test_review_has_kpis_and_complete(self) -> None:
		html = _read(_WWW / "requirements_compliance_review.html")
		self.assertIn('data-testid="kt-rc-review-root"', html)
		self.assertIn('data-testid="kt-rc-kpi-grid"', html)
		self.assertIn('data-testid="kt-rc-unresolved"', html)
		self.assertIn("Responses requiring action", html)
		self.assertIn('data-testid="kt-rc-complete-btn"', html)
		self.assertIn("Complete Section", html)
		# FoT / RC-workspace footer contract: Back | last-saved | Complete — no copyright strip,
		# no fake Save Section, Back returns to the matrix (not the same target as Complete).
		self.assertIn("Back to Requirements", html)
		self.assertIn('href="{{ r.section_url }}"', html)
		self.assertIn('data-testid="kt-rc-review-last-saved"', html)
		self.assertNotIn("Save Section", html)
		self.assertNotIn("kt-rc-review-save-draft", html)
		self.assertNotIn("Secure Bid Environment", html)
		# Footer must be a sibling of the shell (viewport-fixed), not nested in scroll content.
		foot_at = html.find('data-testid="kt-rc-review-footer"')
		self.assertGreater(foot_at, 0)
		self.assertIn("kt-a4-foot", html)
		js = _read(_JS / "requirements_compliance_review.js")
		self.assertIn("complete_requirements_compliance_section", js)
		self.assertIn('getAttribute("data-workspace-url")', js)
		self.assertIn("returning to checklist", js)
		self.assertNotIn("kt-rc-review-save-draft", js)
		self.assertNotIn(
			'getAttribute("data-section-url") || r.getAttribute("data-workspace-url")',
			js,
		)

	def test_hooks_register_dedicated_routes(self) -> None:
		hooks = _read(_APP / "hooks.py")
		self.assertIn("requirements_compliance/review", hooks)
		self.assertIn('to_route": "tenders/requirements_compliance"', hooks)

	def test_css_fixed_action_footer(self) -> None:
		css = _read(_CSS / "requirement_matrix_web.css")
		self.assertIn(".kt-rc-kpi-grid", css)
		# Stitch / FoT contract: viewport-fixed footer, not sticky-in-flow.
		foot = css.split(".kt-a4-foot {", 1)[1].split("}", 1)[0]
		self.assertIn("position: fixed", foot)
		self.assertNotIn("position: sticky", foot)
		self.assertIn("bottom: 0", foot)
