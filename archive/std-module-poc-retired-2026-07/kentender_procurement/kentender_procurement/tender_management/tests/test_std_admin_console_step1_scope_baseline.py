# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Administration Console POC — Admin step 1 scope document baseline.

Anchors the controlling scope markdown in-repo (§20 acceptance table, §24
boundary prompt, §25 exit). Admin step 1 is governance; full `ADMIN-SCOPE-AC-*`
evidence is delivered in later admin steps per STD-ADMIN-003.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_admin_console_step1_scope_baseline
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase


def _admin_scope_document_path() -> Path:
	# .../kentender_v1/kentender_procurement/kentender_procurement/tender_management/tests/this_file
	repo_v1 = Path(__file__).resolve().parents[4]
	return (
		repo_v1
		/ "docs"
		/ "prompts"
		/ "std poc"
		/ "admin console"
		/ "1. std_admin_console_scope_document.md"
	)


REQUIRED_ANCHORS: tuple[str, ...] = (
	"## 20. Acceptance Criteria",
	"ADMIN-SCOPE-AC-001",
	"## 24. Cursor Implementation Boundary Prompt",
	"This workstream is the STD Administration Console POC only.",
	"## 25. Exit Condition",
)


class TestStdAdminConsoleStep1ScopeBaseline(UnitTestCase):
	def test_admin_scope_document_exists_with_stable_anchors(self) -> None:
		path = _admin_scope_document_path()
		self.assertTrue(path.is_file(), f"Expected scope doc at {path}")
		text = path.read_text(encoding="utf-8")
		for anchor in REQUIRED_ANCHORS:
			with self.subTest(anchor=anchor):
				self.assertIn(anchor, text)
