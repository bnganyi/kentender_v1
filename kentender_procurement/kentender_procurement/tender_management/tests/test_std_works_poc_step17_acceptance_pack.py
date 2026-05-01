# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 17 — acceptance evidence pack structure (regression).

Ensures the formal acceptance artefact under the template package exists and
retains the section headings required by Step 17 §7.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_works_poc_step17_acceptance_pack
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _acceptance_pack_path() -> Path:
	pkg = Path(__file__).resolve().parent.parent / "std_templates"
	return pkg / "ke_ppra_works_building_2022_04_poc" / "evidence" / "acceptance_pack.md"


REQUIRED_STEP17_HEADINGS: tuple[str, ...] = (
	"# STD-WORKS-POC Acceptance Evidence Pack",
	"## 1. Acceptance Summary",
	"## 2. POC Identity",
	"## 3. Package Artefacts Reviewed",
	"## 4. Environment and Execution Context",
	"## 5. End-to-End Smoke Result",
	"## 6. Template Import Evidence",
	"## 7. Tender Creation and Sample Load Evidence",
	"## 8. Validation Evidence",
	"## 9. Required Forms Evidence",
	"## 10. Sample BoQ Evidence",
	"## 11. Tender-Pack Preview Evidence",
	"## 12. Audit and Reproducibility Evidence",
	"## 13. Negative Scenario Evidence",
	"## 14. Positive Variant Evidence",
	"## 15. Known Issues and Dispositions",
	"## 16. Explicit POC Limitations",
	"## 17. Acceptance Checklist",
	"## 18. Reviewer Sign-Off",
	"## 19. Acceptance Decision",
)


class TestStdWorksPocStep17AcceptancePack(UnitTestCase):
	def test_step17_acceptance_pack_exists_and_has_required_sections(self) -> None:
		path = _acceptance_pack_path()
		self.assertTrue(path.is_file(), f"Expected acceptance pack at {path}")
		text = path.read_text(encoding="utf-8")
		for heading in REQUIRED_STEP17_HEADINGS:
			with self.subTest(heading=heading):
				self.assertIn(heading, text, "Step 17 §7 structure must be preserved")

	def test_step17_issue_log_exists(self) -> None:
		pack = _acceptance_pack_path()
		issue_log = pack.parent / "issue_log.md"
		self.assertTrue(issue_log.is_file(), "issue_log.md required beside acceptance_pack.md")
