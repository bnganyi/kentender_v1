# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-08 — TM2 Supplier Participation (TPR-* codes, TM2-SPR-001).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_supplier_participation_p1_08
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2SupplierParticipationP108(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P108%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P108%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		for sn in self._supplier_names:
			if frappe.db.exists("Supplier", sn):
				frappe.delete_doc("Supplier", sn, force=True, ignore_permissions=True)
		super().tearDown()

	def _supplier_group(self) -> str:
		sg = frappe.db.get_value(
			"Supplier Group",
			{"is_group": 0},
			"name",
			order_by="lft asc",
		)
		if not sg:
			sg = frappe.db.get_value("Supplier Group", {}, "name")
		if not sg:
			frappe.throw("No Supplier Group for P1-08 Supplier fixture")
		return sg

	def _ensure_supplier(self, label: str) -> str:
		supplier_name = f"P108 {label} Supplier"
		existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
		if existing:
			self._supplier_names.append(existing)
			return existing
		doc = frappe.get_doc(
			{
				"doctype": "Supplier",
				"naming_series": "SUP-.YYYY.-",
				"supplier_name": supplier_name,
				"supplier_type": "Company",
				"supplier_group": self._supplier_group(),
			}
		).insert(ignore_permissions=True)
		self._supplier_names.append(doc.name)
		return doc.name

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str) -> frappe.model.document.Document:
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P108 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
			}
		).insert(ignore_permissions=True)

	def test_p108_insert_participation_code(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P108-2028-0001")
		sup = self._ensure_supplier("A")
		p = frappe.get_doc(
			{
				"doctype": "TM2 Supplier Participation",
				"tm2_tender": tm2.name,
				"supplier": sup,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(p.participation_code, f"TPR-{tm2.tender_code}-{sup}")
		self.assertEqual(p.name, p.participation_code)
		self.assertEqual(p.supplier_code, sup)

	def test_p108_spr_001_second_same_supplier_rejected(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P108-2028-0002")
		sup = self._ensure_supplier("B")
		base = {"doctype": "TM2 Supplier Participation", "tm2_tender": tm2.name, "supplier": sup}
		frappe.get_doc(dict(base)).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(dict(base)).insert(ignore_permissions=True)

	def test_p108_two_suppliers_distinct_codes(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P108-2028-0003")
		s1 = self._ensure_supplier("C1")
		s2 = self._ensure_supplier("C2")
		p1 = frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2.name, "supplier": s1}
		).insert(ignore_permissions=True)
		p2 = frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2.name, "supplier": s2}
		).insert(ignore_permissions=True)
		self.assertNotEqual(p1.participation_code, p2.participation_code)

	def test_p108_cannot_reassign_supplier(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P108-2028-0004")
		s1 = self._ensure_supplier("D1")
		s2 = self._ensure_supplier("D2")
		p = frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2.name, "supplier": s1}
		).insert(ignore_permissions=True)
		p.reload()
		p.supplier = s2
		with self.assertRaises(frappe.ValidationError):
			p.save(ignore_permissions=True)

	def test_p108_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Supplier Participation")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"participation_code",
			"tender_code",
			"supplier",
			"supplier_code",
			"current_status",
			"first_viewed_at",
			"documents_downloaded_at",
			"interest_expressed_at",
			"clarification_count",
			"bid_draft_started_at",
			"bid_submitted_at",
			"withdrawn_at",
			"eligibility_snapshot",
			"addendum_acknowledgement_status",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
		self.assertIn("last_bid_submission_code", names)
