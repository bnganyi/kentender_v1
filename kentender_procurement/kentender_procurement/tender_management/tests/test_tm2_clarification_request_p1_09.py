# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-09 — TM2 Clarification Request (CLR-* codes, TM2-CLR-001/002/004).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_clarification_request_p1_09
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2ClarificationRequestP109(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Clarification Request",
			filters={"tender_code": ["like", "TND-P109%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Clarification Request", row):
				frappe.delete_doc("TM2 Clarification Request", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P109%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P109%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P109%"]}, pluck="name"):
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
			frappe.throw("No Supplier Group for P1-09 Supplier fixture")
		return sg

	def _ensure_supplier(self, label: str) -> str:
		supplier_name = f"P109 {label} Supplier"
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
				"tender_title": "P109 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
			}
		).insert(ignore_permissions=True)

	def _mk_timeline(self, tm2_name: str, *, clarification_deadline_at) -> frappe.model.document.Document:
		base = now_datetime()
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender Timeline",
				"tm2_tender": tm2_name,
				"planned_publication_at": add_to_date(base, hours=1),
				"clarification_deadline_at": clarification_deadline_at,
				"addendum_cutoff_at": add_to_date(base, days=3),
				"submission_deadline_at": add_to_date(base, days=5),
				"opening_scheduled_at": add_to_date(base, days=5),
				"tender_validity_days": 90,
				"timezone": "Africa/Nairobi",
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

	def _fixture_open_deadline(self) -> tuple[frappe.model.document.Document, str, frappe.model.document.Document]:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P109-2028-0001")
		sup = self._ensure_supplier("A")
		self._mk_timeline(tm2.name, clarification_deadline_at=add_to_date(now_datetime(), days=3))
		self._mk_participation(tm2.name, sup)
		return tm2, sup, pkg

	def test_p109_insert_sequence_and_code(self) -> None:
		tm2, sup, _pkg = self._fixture_open_deadline()
		c1 = frappe.get_doc(
			{
				"doctype": "TM2 Clarification Request",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"question_text": "Is alternate material acceptable?",
				"attachment_refs": {"files": []},
			}
		).insert(ignore_permissions=True)
		self.assertEqual(c1.clarification_code, f"CLR-{tm2.tender_code}-0001")
		self.assertEqual(c1.name, c1.clarification_code)
		c2 = frappe.get_doc(
			{
				"doctype": "TM2 Clarification Request",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"question_text": "Second question.",
				"attachment_refs": {},
			}
		).insert(ignore_permissions=True)
		self.assertEqual(c2.clarification_code, f"CLR-{tm2.tender_code}-0002")

	def test_p109_clr_002_requires_participation(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P109-2028-0002")
		sup = self._ensure_supplier("B")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Clarification Request",
					"tm2_tender": tm2.name,
					"supplier": sup,
					"question_text": "No participation row.",
				}
			).insert(ignore_permissions=True)

	def test_p109_clr_001_past_deadline(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P109-2028-0003")
		sup = self._ensure_supplier("C")
		self._mk_timeline(tm2.name, clarification_deadline_at=add_to_date(now_datetime(), days=-1))
		self._mk_participation(tm2.name, sup)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Clarification Request",
					"tm2_tender": tm2.name,
					"supplier": sup,
					"question_text": "Too late.",
				}
			).insert(ignore_permissions=True)

	def test_p109_clr_004_content_locked(self) -> None:
		tm2, sup, _pkg = self._fixture_open_deadline()
		c = frappe.get_doc(
			{
				"doctype": "TM2 Clarification Request",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"question_text": "Original",
			}
		).insert(ignore_permissions=True)
		c.reload()
		c.question_text = "Tampered"
		with self.assertRaises(frappe.ValidationError):
			c.save(ignore_permissions=True)
		c.reload()
		c.status = "Under Review"
		c.save(ignore_permissions=True)
		self.assertEqual(c.status, "Under Review")

	def test_p109_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Clarification Request")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"clarification_code",
			"tender_code",
			"supplier",
			"supplier_code",
			"related_std_section_code",
			"related_std_clause_ref",
			"related_boq_item_code",
			"question_text",
			"attachment_refs",
			"submitted_at",
			"status",
			"requires_addendum",
			"tm2_converted_addendum",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
