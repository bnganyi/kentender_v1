# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Administration Console POC — Admin step 2 information architecture baseline.

Anchors the IA markdown (navigation, primary views, journeys, data mapping, server/UI
capabilities, §24 `ADMIN-IA-AC-*`, §25 boundary prompt). Implementation of Desk UI
is Admin steps 3–8; smoke Admin step 9.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_admin_console_step2_information_architecture_baseline
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _admin_ia_document_path() -> Path:
	repo_v1 = Path(__file__).resolve().parents[4]
	return (
		repo_v1
		/ "docs"
		/ "prompts"
		/ "std poc"
		/ "admin console"
		/ "2. std_admin_console_information_architecture.md"
	)


REQUIRED_ANCHORS: tuple[str, ...] = (
	"## 5. Navigation Model",
	"## 7. Primary Screens and Views",
	"## 19. Required User Journeys",
	"## 20. Data Object Mapping",
	"## 21. Minimal Server Capabilities Required by the IA",
	"## 22. Minimal Client/UI Capabilities Required by the IA",
	"## 24. Acceptance Criteria",
	"ADMIN-IA-AC-001",
	"ADMIN-IA-AC-013",
	"## 25. Cursor Boundary Prompt for Later Implementation",
	"Implement only the STD Administration Console POC information architecture outputs.",
)


class TestStdAdminConsoleStep2InformationArchitectureBaseline(UnitTestCase):
	def test_admin_ia_document_exists_with_stable_anchors(self) -> None:
		path = _admin_ia_document_path()
		self.assertTrue(path.is_file(), f"Expected IA doc at {path}")
		text = path.read_text(encoding="utf-8")
		for anchor in REQUIRED_ANCHORS:
			with self.subTest(anchor=anchor):
				self.assertIn(anchor, text)
