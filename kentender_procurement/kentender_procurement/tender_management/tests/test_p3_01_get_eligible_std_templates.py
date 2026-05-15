# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-01 — doc 9 §8.2 ``get_eligible_std_templates`` (GATE-N isolated fixtures).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p3_01_get_eligible_std_templates
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	getEligibleStdTemplates,
	get_eligible_std_templates,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestP301GetEligibleStdTemplates(_ReleaseProcurementPackageHandoffFixtures):
	def test_p3_01_empty_package_code_returns_empty(self) -> None:
		self.assertEqual(get_eligible_std_templates(""), [])
		self.assertEqual(get_eligible_std_templates("   "), [])

	def test_p3_01_unknown_package_returns_empty(self) -> None:
		self.assertEqual(get_eligible_std_templates("PKG-NONEXISTENT-P301-XYZ"), [])

	def test_p3_01_fixture_package_returns_singleton_with_contract_keys(self) -> None:
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
		)
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name

		eligible = get_eligible_std_templates(pc)
		self.assertEqual(len(eligible), 1, eligible)
		row = eligible[0]
		for key in ("std_template", "template_code", "template_name", "lifecycle_status", "resolution_path"):
			self.assertIn(key, row, msg=f"missing {key} in {row!r}")
		self.assertEqual(row.get("resolution_path"), "default_std_template")
		self.assertEqual(row.get("std_template"), TEMPLATE_CODE)
		self.assertEqual(getEligibleStdTemplates(pc), eligible)

	def test_p3_01_ambiguous_handoff_returns_multiple_rows(self) -> None:
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{
				"allowed_for_tender_creation": 1,
				"status": "Imported",
				"procurement_category": "WORKS",
				"lifecycle_status": "Active",
			},
		)
		base = frappe.get_doc("STD Template", TEMPLATE_CODE)
		dup = frappe.copy_doc(base)
		dup.template_code = f"{TEMPLATE_CODE}-P301-DUP-{frappe.generate_hash()[:6]}"
		dup.template_usage = []
		dup.tender_usage_count = 0
		dup.lifecycle_events = []
		dup.validation_findings = []
		dup.insert(ignore_permissions=True)
		for child_dt in (
			"STD Template Usage",
			"STD Template Lifecycle Event",
			"STD Template Validation Finding",
		):
			frappe.db.delete(child_dt, {"parent": dup.name})
		frappe.db.set_value("STD Template", dup.name, "tender_usage_count", 0)

		def _cleanup_dup_std() -> None:
			n = dup.name
			if not frappe.db.exists("STD Template", n):
				return
			for child_dt in (
				"STD Template Usage",
				"STD Template Lifecycle Event",
				"STD Template Validation Finding",
			):
				frappe.db.delete(child_dt, {"parent": n})
			frappe.db.set_value("STD Template", n, "tender_usage_count", 0)
			frappe.delete_doc("STD Template", n, force=True, ignore_permissions=True, delete_permanently=True)

		self.addCleanup(_cleanup_dup_std)
		frappe.db.set_value(
			"STD Template",
			dup.name,
			{"allowed_for_tender_creation": 1, "status": "Imported", "procurement_category": "WORKS"},
		)

		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		frappe.db.set_value(
			"Procurement Template",
			tpl.name,
			{"category": "Works", "default_std_template": None},
		)
		pkg = self._mk_package(plan.name, tpl.name)
		frappe.db.set_value(
			"Procurement Package",
			pkg.name,
			{"procurement_method": "Open Tender", "contract_type": "Fixed Price"},
		)
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name

		eligible = get_eligible_std_templates(pc)
		self.assertGreaterEqual(len(eligible), 2, eligible)
		self.assertTrue(all(e.get("resolution_path") == "ambiguous" for e in eligible))
		names = {e.get("std_template") for e in eligible}
		self.assertIn(TEMPLATE_CODE, names)
		self.assertIn(dup.name, names)
