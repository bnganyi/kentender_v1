# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-07 — TM2 Tender Invitation (INV-* codes, TM2-INV-002/003/004).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_tender_invitation_p1_07
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2TenderInvitationP107(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Tender Invitation", filters={"tender_code": ["like", "TND-P107%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Invitation", row):
				frappe.delete_doc("TM2 Tender Invitation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P107%"]}, pluck="name"):
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
			frappe.throw("No Supplier Group for P1-07 Supplier fixture")
		return sg

	def _ensure_supplier(self, label: str) -> str:
		supplier_name = f"P107 {label} Supplier"
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
				"tender_title": "P107 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
			}
		).insert(ignore_permissions=True)

	def test_p107_insert_invitation_code_and_snapshots(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P107-2028-0001")
		sup = self._ensure_supplier("A")
		inv = frappe.get_doc(
			{
				"doctype": "TM2 Tender Invitation",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(inv.invitation_code, f"INV-{tm2.tender_code}-0001")
		self.assertEqual(inv.name, inv.invitation_code)
		self.assertEqual(inv.supplier_code, sup)
		self.assertTrue(inv.supplier_name_snapshot)

	def test_p107_inv_004_blocks_second_active_same_supplier(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P107-2028-0002")
		sup = self._ensure_supplier("B")
		base = {"doctype": "TM2 Tender Invitation", "tm2_tender": tm2.name, "supplier": sup, "status": "Draft"}
		frappe.get_doc(dict(base)).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(dict(base)).insert(ignore_permissions=True)

	def test_p107_inv_004_allows_after_superseded(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P107-2028-0003")
		sup = self._ensure_supplier("C")
		first = frappe.get_doc(
			{
				"doctype": "TM2 Tender Invitation",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		first.status = "Superseded"
		first.save(ignore_permissions=True)
		second = frappe.get_doc(
			{
				"doctype": "TM2 Tender Invitation",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(second.invitation_code, f"INV-{tm2.tender_code}-0002")

	def test_p107_inv_002_sent_requires_published(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P107-2028-0004")
		sup = self._ensure_supplier("D")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Tender Invitation",
					"tm2_tender": tm2.name,
					"supplier": sup,
					"status": "Sent",
				}
			).insert(ignore_permissions=True)

	def test_p107_inv_003_revoke_requires_reason(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P107-2028-0005")
		sup = self._ensure_supplier("E")
		inv = frappe.get_doc(
			{
				"doctype": "TM2 Tender Invitation",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		inv.status = "Revoked"
		with self.assertRaises(frappe.ValidationError):
			inv.save(ignore_permissions=True)
		inv.reload()
		inv.status = "Revoked"
		inv.revocation_reason = "No longer participating in restricted lot."
		inv.save(ignore_permissions=True)
		self.assertEqual(inv.status, "Revoked")

	def test_p107_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Tender Invitation")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"invitation_code",
			"tender_code",
			"supplier",
			"supplier_code",
			"supplier_name_snapshot",
			"eligibility_result_ref",
			"status",
			"invited_by",
			"invited_at",
			"delivered_at",
			"accepted_at",
			"declined_at",
			"revoked_by",
			"revoked_at",
			"revocation_reason",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
