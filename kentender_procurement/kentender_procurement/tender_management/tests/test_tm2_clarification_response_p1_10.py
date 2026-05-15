# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-10 — TM2 Clarification Response (CLRR-* codes, TM2-CLRR-001/002/003).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_clarification_response_p1_10
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2ClarificationResponseP110(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Clarification Response",
			filters={"tender_code": ["like", "TND-P110%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Clarification Response", row):
				frappe.delete_doc("TM2 Clarification Response", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Clarification Request",
			filters={"tender_code": ["like", "TND-P110%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Clarification Request", row):
				frappe.delete_doc("TM2 Clarification Request", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P110%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P110%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P110%"]}, pluck="name"):
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
			frappe.throw("No Supplier Group for P1-10 Supplier fixture")
		return sg

	def _ensure_supplier(self, label: str) -> str:
		supplier_name = f"P110 {label} Supplier"
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
				"tender_title": "P110 TM2",
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

	def _fixture_tm2_and_clarification(self) -> tuple[frappe.model.document.Document, frappe.model.document.Document]:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P110-2028-0001")
		sup = self._ensure_supplier("R")
		self._mk_timeline(tm2.name, clarification_deadline_at=add_to_date(now_datetime(), days=3))
		self._mk_participation(tm2.name, sup)
		clr = frappe.get_doc(
			{
				"doctype": "TM2 Clarification Request",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"question_text": "Clarification for response tests.",
				"attachment_refs": {"files": []},
			}
		).insert(ignore_permissions=True)
		return tm2, clr

	def test_p110_insert_sequence_and_code(self) -> None:
		_tm2, clr = self._fixture_tm2_and_clarification()
		prefix = f"CLRR-{clr.clarification_code}-"
		r1 = frappe.get_doc(
			{
				"doctype": "TM2 Clarification Response",
				"tm2_clarification_request": clr.name,
				"response_text": "First answer.",
				"visibility": "All Participants",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(r1.response_code, f"{prefix}01")
		self.assertEqual(r1.name, r1.response_code)
		r2 = frappe.get_doc(
			{
				"doctype": "TM2 Clarification Response",
				"tm2_clarification_request": clr.name,
				"response_text": "Second answer.",
				"visibility": "Requesting Supplier Only",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(r2.response_code, f"{prefix}02")

	def test_p110_clrr_001_requires_approval_for_publish(self) -> None:
		_tm2, clr = self._fixture_tm2_and_clarification()
		r = frappe.get_doc(
			{
				"doctype": "TM2 Clarification Response",
				"tm2_clarification_request": clr.name,
				"response_text": "Draft body.",
				"visibility": "Internal Only",
			}
		).insert(ignore_permissions=True)
		r.reload()
		r.status = "Published"
		with self.assertRaises(frappe.ValidationError):
			r.save(ignore_permissions=True)

	def test_p110_clrr_002_addendum_blocks_ordinary_publish(self) -> None:
		_tm2, clr = self._fixture_tm2_and_clarification()
		r = frappe.get_doc(
			{
				"doctype": "TM2 Clarification Response",
				"tm2_clarification_request": clr.name,
				"response_text": "Needs addendum path.",
				"visibility": "Public",
				"addendum_required": 1,
			}
		).insert(ignore_permissions=True)
		r.reload()
		r.status = "Published"
		r.approved_by = "Administrator"
		r.approved_at = now_datetime()
		with self.assertRaises(frappe.ValidationError):
			r.save(ignore_permissions=True)

	def test_p110_clrr_003_immutable_after_publish(self) -> None:
		_tm2, clr = self._fixture_tm2_and_clarification()
		r = frappe.get_doc(
			{
				"doctype": "TM2 Clarification Response",
				"tm2_clarification_request": clr.name,
				"response_text": "Final text.",
				"visibility": "All Participants",
			}
		).insert(ignore_permissions=True)
		r.reload()
		r.status = "Published"
		r.approved_by = "Administrator"
		r.approved_at = now_datetime()
		r.save(ignore_permissions=True)
		r.reload()
		r.response_text = "Tampered"
		with self.assertRaises(frappe.ValidationError):
			r.save(ignore_permissions=True)

	def test_p110_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Clarification Response")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"response_code",
			"tm2_clarification_request",
			"clarification_request_code",
			"tm2_tender",
			"tender_code",
			"response_text",
			"visibility",
			"drafted_by",
			"drafted_at",
			"approved_by",
			"approved_at",
			"published_by",
			"published_at",
			"status",
			"addendum_required",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
