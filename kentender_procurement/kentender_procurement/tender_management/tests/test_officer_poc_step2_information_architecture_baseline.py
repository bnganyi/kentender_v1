# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Officer Tender Configuration POC — Officer step 2 IA baseline.

Anchors the IA markdown (navigation, screen inventory, journeys, data mapping,
server/UI capabilities, §29 ``OFFICER-IA-AC-*``, §30 boundary prompt). Desk
implementation is Officer steps **3–8**; smoke Officer step **9**.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_officer_poc_step2_information_architecture_baseline
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _officer_ia_document_path() -> Path:
	repo_v1 = Path(__file__).resolve().parents[4]
	return (
		repo_v1
		/ "docs"
		/ "prompts"
		/ "std poc"
		/ "tender configuration"
		/ "2. procurement_officer_tender_configuration_poc_user_journey_information_architecture.md"
	)


REQUIRED_ANCHORS: tuple[str, ...] = (
	"## 6. Navigation Model",
	"## 8. Screen / View Inventory",
	"## 20. Required User Journeys",
	"## 21. Data Object Mapping",
	"## 22. Server Capability Requirements",
	"## 23. UI Capability Requirements",
	"## 29. Acceptance Criteria",
	"OFFICER-IA-AC-001",
	"OFFICER-IA-AC-015",
	"## 30. Cursor Boundary Prompt for Later Implementation",
	"Implement only the Procurement Officer Tender Configuration POC information architecture outputs.",
)


class TestOfficerPocStep2InformationArchitectureBaseline(UnitTestCase):
	def test_officer_ia_document_exists_with_stable_anchors(self) -> None:
		path = _officer_ia_document_path()
		self.assertTrue(path.is_file(), f"Expected IA doc at {path}")
		text = path.read_text(encoding="utf-8")
		for anchor in REQUIRED_ANCHORS:
			with self.subTest(anchor=anchor):
				self.assertIn(anchor, text)

	def test_first_pass_uses_procurement_tender_list_and_form(self) -> None:
		"""Planning correction §8 — no new Workspace in first pass."""
		path = _officer_ia_document_path()
		text = path.read_text(encoding="utf-8")
		self.assertIn("| `Procurement Tender` List View |", text)
		self.assertIn("| `Procurement Tender` Form |", text)
