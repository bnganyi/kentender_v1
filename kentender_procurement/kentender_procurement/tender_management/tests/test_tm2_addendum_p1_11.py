# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-11 — TM2 Addendum (ADD-* codes, TM2-ADD-001/002/004).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_addendum_p1_11
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2AddendumP111(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Addendum",
			filters={"tender_code": ["like", "TND-P111%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Addendum", row):
				frappe.delete_doc("TM2 Addendum", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Clarification Request",
			filters={"tender_code": ["like", "TND-P111%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Clarification Request", row):
				frappe.delete_doc("TM2 Clarification Request", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P111%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P111%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P111%"]}, pluck="name"):
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
			frappe.throw("No Supplier Group for P1-11 Supplier fixture")
		return sg

	def _ensure_supplier(self, label: str) -> str:
		supplier_name = f"P111 {label} Supplier"
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
				"tender_title": "P111 TM2",
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

	def _published_tm2_with_optional_clr(
		self, *, tender_code: str = "TND-P111-2028-0001", with_clarification: bool = False
	):
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tender_code)
		tm2.status = "Published"
		tm2.flags.ignore_tm2_tender_governed_status_mutation = True
		tm2.save(ignore_permissions=True)
		clr = None
		if with_clarification:
			sup = self._ensure_supplier("CLR")
			self._mk_timeline(tm2.name, clarification_deadline_at=add_to_date(now_datetime(), days=3))
			self._mk_participation(tm2.name, sup)
			clr = frappe.get_doc(
				{
					"doctype": "TM2 Clarification Request",
					"tm2_tender": tm2.name,
					"supplier": sup,
					"question_text": "Question for lineage.",
					"attachment_refs": {},
				}
			).insert(ignore_permissions=True)
		return tm2, clr

	def test_p111_insert_sequence_and_code(self) -> None:
		tm2, _clr = self._published_tm2_with_optional_clr()
		prefix = f"ADD-{tm2.tender_code}-"
		a1 = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2.name,
				"title": "First addendum",
				"reason": "Correct scope ambiguity.",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(a1.addendum_code, f"{prefix}01")
		self.assertEqual(a1.addendum_number, 1)
		self.assertEqual(a1.name, a1.addendum_code)
		a2 = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2.name,
				"title": "Second addendum",
				"reason": "Deadline extension.",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(a2.addendum_code, f"{prefix}02")
		self.assertEqual(a2.addendum_number, 2)

	def test_p111_add_001_rejects_draft_tender(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P111-2028-0002")
		self.assertEqual(tm2.status, "Draft")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Addendum",
					"tm2_tender": tm2.name,
					"title": "Not allowed",
					"reason": "Tender not published.",
				}
			).insert(ignore_permissions=True)

	def test_p111_add_002_reason_required(self) -> None:
		tm2, _clr = self._published_tm2_with_optional_clr(tender_code="TND-P111-2028-0003")
		doc = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2.name,
				"title": "Bad reason",
				"reason": "temporary",
			}
		).insert(ignore_permissions=True)
		doc.reload()
		doc.reason = "   \n\t  "
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_p111_add_004_issued_immutable(self) -> None:
		tm2, _clr = self._published_tm2_with_optional_clr(tender_code="TND-P111-2028-0004")
		a = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2.name,
				"title": "Issued addendum",
				"reason": "Material change.",
			}
		).insert(ignore_permissions=True)
		a.reload()
		a.status = "Issued"
		a.save(ignore_permissions=True)
		a.reload()
		a.title = "Tampered"
		with self.assertRaises(frappe.ValidationError):
			a.save(ignore_permissions=True)

	def test_p111_cancelled_requires_cancellation_reason(self) -> None:
		tm2, _clr = self._published_tm2_with_optional_clr(tender_code="TND-P111-2028-0005")
		a = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2.name,
				"title": "Will cancel",
				"reason": "Planned then withdrawn.",
			}
		).insert(ignore_permissions=True)
		a.reload()
		a.status = "Cancelled"
		with self.assertRaises(frappe.ValidationError):
			a.save(ignore_permissions=True)
		a.reload()
		a.cancellation_reason = "Duplicate draft."
		a.status = "Cancelled"
		a.save(ignore_permissions=True)

	def test_p111_source_clarification_lineage(self) -> None:
		tm2_a, clr = self._published_tm2_with_optional_clr(
			tender_code="TND-P111-2028-0006", with_clarification=True
		)
		assert clr is not None
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2_b = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P111-2028-0007")
		tm2_b.status = "Published"
		tm2_b.flags.ignore_tm2_tender_governed_status_mutation = True
		tm2_b.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Addendum",
					"tm2_tender": tm2_b.name,
					"title": "Wrong tender",
					"reason": "Cross-link test.",
					"tm2_source_clarification_request": clr.name,
				}
			).insert(ignore_permissions=True)

	def test_p111_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Addendum")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"addendum_code",
			"tm2_tender",
			"tm2_source_clarification_request",
			"tender_code",
			"addendum_number",
			"title",
			"reason",
			"status",
			"primary_impact_type",
			"affects_deadline",
			"affects_submission_model",
			"affects_opening_model",
			"affects_evaluation_model",
			"affects_contract_model",
			"requires_supplier_acknowledgement",
			"created_by",
			"created_at",
			"submitted_for_approval_by",
			"submitted_for_approval_at",
			"approved_by",
			"approved_at",
			"issued_by",
			"issued_at",
			"cancelled_by",
			"cancelled_at",
			"cancellation_reason",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
