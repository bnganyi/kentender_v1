# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B9 — at most one active (non-cancelled) tender per planning package (doc 2 sec. 16.3).

Run:
	bench --site <site> run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_planning_tender_handoff_duplicate_b9
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.release_procurement_package_to_tender import (
	release_procurement_package_to_tender,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestPlanningTenderHandoffDuplicateB9(_ReleaseProcurementPackageHandoffFixtures):
	def test_b9_copy_doc_second_tender_same_package_raises(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")

		out = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out.get("ok"), out)
		tn = out["tender"]
		self._created.append(("Procurement Tender", tn))

		t1 = frappe.get_doc("Procurement Tender", tn)
		dup = frappe.copy_doc(t1)
		dup.tender_reference = f"DUP-{dup.tender_reference}-b9"
		with self.assertRaises(frappe.ValidationError) as ctx:
			dup.insert(ignore_permissions=True)
		self.assertIn("already linked", str(ctx.exception).lower())

	def test_b9_after_cancel_release_creates_new_tender(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")

		out1 = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out1.get("ok"), out1)
		t1 = out1["tender"]
		self._created.append(("Procurement Tender", t1))

		frappe.db.set_value("Procurement Tender", t1, "tender_status", "Cancelled")

		out2 = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out2.get("ok"), out2)
		self.assertFalse(out2.get("existing"), out2)
		t2 = out2["tender"]
		self.assertNotEqual(t1, t2)
		self._created.append(("Procurement Tender", t2))

		self.assertEqual(
			frappe.db.get_value("Procurement Tender", t2, "procurement_package"),
			pkg.name,
		)
		self.assertEqual(frappe.db.get_value("Procurement Tender", t2, "std_template"), TEMPLATE_CODE)
