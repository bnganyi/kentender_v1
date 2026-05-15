# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-13 — TM2 Addendum Acknowledgement (ACK-* codes, TM2-ACK-002/003).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_addendum_acknowledgement_p1_13
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2AddendumAcknowledgementP113(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Addendum Acknowledgement",
			filters={"tender_code": ["like", "TND-P113%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Addendum Acknowledgement", row):
				frappe.delete_doc("TM2 Addendum Acknowledgement", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Addendum",
			filters={"tender_code": ["like", "TND-P113%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Addendum", row):
				frappe.delete_doc("TM2 Addendum", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P113%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P113%"]}, pluck="name"):
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
			frappe.throw("No Supplier Group for P1-13 Supplier fixture")
		return sg

	def _ensure_supplier(self, label: str) -> str:
		supplier_name = f"P113 {label} Supplier"
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
				"tender_title": "P113 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
			}
		).insert(ignore_permissions=True)

	def _mk_participation(self, tm2_name: str, supplier_name: str) -> frappe.model.document.Document:
		return frappe.get_doc(
			{
				"doctype": "TM2 Supplier Participation",
				"tm2_tender": tm2_name,
				"supplier": supplier_name,
			}
		).insert(ignore_permissions=True)

	def _issued_addendum_with_supplier(self, *, tender_code: str = "TND-P113-2028-0001"):
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tender_code)
		tm2.status = "Published"
		tm2.flags.ignore_tm2_tender_governed_status_mutation = True
		tm2.save(ignore_permissions=True)
		sup = self._ensure_supplier("A")
		self._mk_participation(tm2.name, sup)
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2.name,
				"title": "Fixture addendum",
				"reason": "Fixture for acknowledgement tests.",
			}
		).insert(ignore_permissions=True)
		ad.reload()
		ad.status = "Issued"
		ad.save(ignore_permissions=True)
		return tm2, ad, sup

	def test_p113_ack_code_shape(self) -> None:
		tm2, ad, sup = self._issued_addendum_with_supplier()
		ack = frappe.get_doc(
			{
				"doctype": "TM2 Addendum Acknowledgement",
				"tm2_addendum": ad.name,
				"supplier": sup,
				"acknowledged": 1,
				"acknowledgement_payload": {"source": "test"},
			}
		).insert(ignore_permissions=True)
		expected = f"ACK-{ad.addendum_code}-{sup}"
		self.assertEqual(ack.acknowledgement_code, expected)
		self.assertEqual(ack.name, ack.acknowledgement_code)

	def test_p113_ack_002_duplicate_supplier_same_addendum(self) -> None:
		tm2, ad, sup = self._issued_addendum_with_supplier(tender_code="TND-P113-2028-0002")
		frappe.get_doc(
			{
				"doctype": "TM2 Addendum Acknowledgement",
				"tm2_addendum": ad.name,
				"supplier": sup,
				"acknowledged": 1,
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Addendum Acknowledgement",
					"tm2_addendum": ad.name,
					"supplier": sup,
					"acknowledged": 1,
				}
			).insert(ignore_permissions=True)

	def test_p113_requires_participation(self) -> None:
		tm2, ad, _sup = self._issued_addendum_with_supplier(tender_code="TND-P113-2028-0003")
		other = self._ensure_supplier("NoPart")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Addendum Acknowledgement",
					"tm2_addendum": ad.name,
					"supplier": other,
					"acknowledged": 1,
				}
			).insert(ignore_permissions=True)

	def test_p113_ack_003_immutable_after_acknowledged(self) -> None:
		tm2, ad, sup = self._issued_addendum_with_supplier(tender_code="TND-P113-2028-0004")
		ack = frappe.get_doc(
			{
				"doctype": "TM2 Addendum Acknowledgement",
				"tm2_addendum": ad.name,
				"supplier": sup,
				"acknowledged": 1,
			}
		).insert(ignore_permissions=True)
		ack.reload()
		ack.required = 0
		with self.assertRaises(frappe.ValidationError):
			ack.save(ignore_permissions=True)

	def test_p113_cannot_clear_acknowledged(self) -> None:
		tm2, ad, sup = self._issued_addendum_with_supplier(tender_code="TND-P113-2028-0005")
		ack = frappe.get_doc(
			{
				"doctype": "TM2 Addendum Acknowledgement",
				"tm2_addendum": ad.name,
				"supplier": sup,
				"acknowledged": 1,
			}
		).insert(ignore_permissions=True)
		ack.reload()
		ack.acknowledged = 0
		with self.assertRaises(frappe.ValidationError):
			ack.save(ignore_permissions=True)

	def test_p113_acknowledged_requires_issued_addendum(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P113-2028-0006")
		tm2.status = "Published"
		tm2.flags.ignore_tm2_tender_governed_status_mutation = True
		tm2.save(ignore_permissions=True)
		sup = self._ensure_supplier("B")
		self._mk_participation(tm2.name, sup)
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2.name,
				"title": "Draft addendum",
				"reason": "Not issued yet.",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Addendum Acknowledgement",
					"tm2_addendum": ad.name,
					"supplier": sup,
					"acknowledged": 1,
				}
			).insert(ignore_permissions=True)

	def test_p113_transition_acknowledged_stamps_metadata(self) -> None:
		tm2, ad, sup = self._issued_addendum_with_supplier(tender_code="TND-P113-2028-0007")
		ack = frappe.get_doc(
			{
				"doctype": "TM2 Addendum Acknowledgement",
				"tm2_addendum": ad.name,
				"supplier": sup,
				"acknowledged": 0,
			}
		).insert(ignore_permissions=True)
		self.assertFalse(ack.acknowledged_by)
		ack.reload()
		ack.acknowledged = 1
		ack.save(ignore_permissions=True)
		self.assertTrue(ack.acknowledged_by)
		self.assertTrue(ack.acknowledged_at)

	def test_p113_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Addendum Acknowledgement")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"acknowledgement_code",
			"tm2_addendum",
			"addendum_code",
			"tm2_tender",
			"tender_code",
			"supplier",
			"supplier_code",
			"required",
			"acknowledged",
			"acknowledged_by",
			"acknowledged_at",
			"acknowledgement_payload",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
