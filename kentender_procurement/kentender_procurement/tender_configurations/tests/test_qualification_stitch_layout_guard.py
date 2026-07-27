# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Static Stitch fidelity gate for Qualification and Capability UI.

Fails if shipped templates regress to form-stack approximations (missing tables /
drawers / section headings required by 08_Qualifications/*_code.html).
"""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

_APP = Path(frappe.get_app_path("kentender_procurement"))
_WWW = _APP / "www" / "tenders"
_INCL = _APP / "templates" / "includes" / "qualification"


def _read(path: Path) -> str:
	return path.read_text(encoding="utf-8")


class TestQualificationStitchLayoutGuard(IntegrationTestCase):
	def test_overview_has_category_table_columns(self) -> None:
		html = _read(_WWW / "qualification_and_capability.html")
		self.assertIn('data-testid="kt-s600-root"', html)
		self.assertIn("kt-s600-table", html)
		for col in (
			"Category",
			"Requirement summary",
			"Progress",
			"Status",
			"Action",
		):
			self.assertIn(col, html)
		# Anti-approximation: must not be a bare card list without a table.
		self.assertIn("<table", html)
		self.assertNotIn("cdn.tailwindcss.com", html)
		# Status column is badge-only — no remaining/issue prose under the chip.
		self.assertNotIn("kt-s600-row-issue", html)

	def test_category_shell_includes_per_screen_partials(self) -> None:
		html = _read(_WWW / "qualification_category.html")
		self.assertIn('data-testid="kt-s600-category-root"', html)
		self.assertIn("kt_s600_contract.html", html)
		self.assertIn("kt_s600_financial.html", html)
		self.assertIn("kt_s600_experience.html", html)
		self.assertIn("kt_s600_personnel.html", html)
		self.assertIn("kt_s600_partners.html", html)
		self.assertIn('data-testid="kt-s600-drawer"', html)
		self.assertNotIn("cdn.tailwindcss.com", html)

	def test_contract_screen_has_disclosure_tables(self) -> None:
		html = _read(_INCL / "kt_s600_contract.html")
		self.assertIn("1. Reporting Entity", html)
		self.assertIn("2. Non-performing Contracts", html)
		self.assertIn("3. Pending Litigation", html)
		self.assertIn("4. Litigation History", html)
		self.assertIn("Add non-performing contract", html)
		self.assertIn("Add pending litigation", html)
		self.assertIn("Add Litigation Record", html)
		for header in ("Contract", "Client", "Currency", "Amount", "Current Status"):
			self.assertIn(header, html)
		# One table template rendered thrice via Jinja loop for the three disclosures.
		self.assertIn('data-records-table="{{ key }}"', html)
		self.assertIn("non_performing", html)
		self.assertIn("pending_litigation", html)
		self.assertIn("litigation_history", html)

	def test_financial_screen_has_three_data_tables(self) -> None:
		html = _read(_INCL / "kt_s600_financial.html")
		self.assertIn("Configured Requirements", html)
		self.assertIn("Historical Financial Performance", html)
		self.assertIn("Average Annual Turnover", html)
		self.assertIn("Financial Resources", html)
		self.assertIn("Add resource", html)
		for header in (
			"Financial Year",
			"Total Assets",
			"Total Liabilities",
			"Net Worth",
			"Resource Type",
			"Provider",
		):
			self.assertIn(header, html)
		self.assertGreaterEqual(html.count("<table"), 3)

	def test_experience_screen_has_general_and_specific_tables(self) -> None:
		html = _read(_INCL / "kt_s600_experience.html")
		self.assertIn("General Experience", html)
		self.assertIn("Specific Experience", html)
		self.assertIn("Qualifying years", html)
		self.assertIn("Similarity details", html)
		self.assertIn("Add project", html)
		self.assertGreaterEqual(html.count("<table"), 2)
		# Requirements must be explicit before the bidder records projects.
		self.assertIn('data-testid="kt-s600-exp-config"', html)
		self.assertIn('data-testid="kt-s600-req-min-years"', html)
		self.assertIn('data-testid="kt-s600-req-min-specific"', html)
		self.assertIn("General experience required", html)
		self.assertIn("Specific experience required", html)

	def test_categories_with_in_body_progress_hide_duplicate_header_kpi(self) -> None:
		html = _read(_WWW / "qualification_category.html")
		self.assertIn("hide_header_kpi", html)
		self.assertIn('"experience"', html)
		self.assertIn('"key_personnel"', html)
		self.assertIn('"delivery_partners"', html)
		self.assertIn("kt-s600-exp-config", _read(_INCL / "kt_s600_experience.html"))
		self.assertIn('data-testid="kt-s600-personnel-progress"', _read(_INCL / "kt_s600_personnel.html"))
		self.assertIn('data-testid="kt-s600-partners-progress"', _read(_INCL / "kt_s600_partners.html"))

	def test_personnel_screen_has_matrix_and_assign_drawer_hooks(self) -> None:
		html = _read(_INCL / "kt_s600_personnel.html")
		self.assertIn("Personnel Matrix", html)
		self.assertIn("Required Position", html)
		self.assertIn("Assigned Person", html)
		self.assertIn("Assign person", html)
		self.assertIn("<table", html)
		# Row Complete must require a complete profile, not merely an assignment id.
		self.assertIn("years_experience", html)
		self.assertIn('data-testid="kt-s600-personnel-progress-text"', html)

	def test_partners_screen_has_matrix_and_drawer_hooks(self) -> None:
		html = _read(_INCL / "kt_s600_partners.html")
		self.assertIn("Item or service", html)
		self.assertIn("Proposed organization", html)
		self.assertIn("Who manufactures", html)
		self.assertIn("Who will perform", html)
		self.assertIn("Another organization", html)
		self.assertIn("<table", html)
		self.assertIn("kt-s600-radio-col", html)
		self.assertIn('data-testid="kt-s600-partners-progress-text"', html)
		# Avoid Jinja dict.items method collision (causes HTTP 500).
		self.assertIn('cfg.get("items"', html)
		self.assertIn('bucket.get("items"', html)

	def test_data_table_input_styles_exclude_radio_and_checkbox(self) -> None:
		css = _read(_APP / "public" / "css" / "qualification_and_capability_web.css")
		self.assertIn(
			'.kt-s600-data-table input:not([type="radio"]):not([type="checkbox"])',
			css,
		)
		self.assertIn('.kt-s600-radio-col input[type="radio"]', css)
		# Guard against reintroducing the full-width text-field chrome on radios.
		self.assertNotRegex(
			css,
			r"\.kt-s600-data-table input,\s*\n\s*\.kt-s600-data-table select",
		)
