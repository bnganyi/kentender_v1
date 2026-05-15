# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-14 — TM2 Bid Draft Metadata (BDM-* codes, TM2-BDM-002/004, no draft body columns).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_bid_draft_metadata_p1_14
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2BidDraftMetadataP114(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Bid Draft Metadata",
			filters={"tender_code": ["like", "TND-P114%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Draft Metadata", row):
				frappe.delete_doc("TM2 Bid Draft Metadata", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P114%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P114%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P114%"]}, pluck="name"):
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
			frappe.throw("No Supplier Group for P1-14 Supplier fixture")
		return sg

	def _ensure_supplier(self, label: str) -> str:
		supplier_name = f"P114 {label} Supplier"
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
				"tender_title": "P114 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
			}
		).insert(ignore_permissions=True)

	def _mk_timeline(self, tm2_name: str, *, submission_deadline_at) -> frappe.model.document.Document:
		base = now_datetime()
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender Timeline",
				"tm2_tender": tm2_name,
				"planned_publication_at": add_to_date(base, hours=1),
				"clarification_deadline_at": add_to_date(base, days=2),
				"addendum_cutoff_at": add_to_date(base, days=3),
				"submission_deadline_at": submission_deadline_at,
				"opening_scheduled_at": add_to_date(base, days=7),
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

	def _fixture_open_deadline(self, *, tender_code: str = "TND-P114-2028-0001"):
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tender_code)
		tm2.status = "Published"
		tm2.flags.ignore_tm2_tender_governed_status_mutation = True
		tm2.save(ignore_permissions=True)
		sup = self._ensure_supplier("A")
		self._mk_timeline(tm2.name, submission_deadline_at=add_to_date(now_datetime(), days=5))
		self._mk_participation(tm2.name, sup)
		return tm2, sup

	def test_p114_insert_code_and_identity(self) -> None:
		tm2, sup = self._fixture_open_deadline()
		dm = frappe.get_doc(
			{
				"doctype": "TM2 Bid Draft Metadata",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"dsm_output_code": "DSM-P114-FIXTURE-01",
				"validation_summary": {"errors": 0, "warnings": 1},
			}
		).insert(ignore_permissions=True)
		self.assertEqual(dm.draft_metadata_code, f"BDM-{tm2.tender_code}-{sup}")
		self.assertEqual(dm.name, dm.draft_metadata_code)
		dm.reload()
		dm.draft_status = "Saved"
		dm.save(ignore_permissions=True)
		self.assertEqual(dm.draft_status, "Saved")
		self.assertTrue(dm.last_saved_at)

	def test_p114_bdm_002_requires_dsm_output_code(self) -> None:
		tm2, sup = self._fixture_open_deadline(tender_code="TND-P114-2028-0002")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Bid Draft Metadata",
					"tm2_tender": tm2.name,
					"supplier": sup,
					"dsm_output_code": "  ",
				}
			).insert(ignore_permissions=True)

	def test_p114_bdm_004_past_submission_deadline(self) -> None:
		tm2, sup = self._fixture_open_deadline(tender_code="TND-P114-2028-0003")
		tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2.name}, "name")
		# Timeline is locked after tender publication (TM2-TTL-004); bypass DocType validate for fixture.
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl_name,
			"submission_deadline_at",
			add_to_date(now_datetime(), days=-1),
		)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Bid Draft Metadata",
					"tm2_tender": tm2.name,
					"supplier": sup,
					"dsm_output_code": "DSM-P114-LATE",
				}
			).insert(ignore_permissions=True)

	def test_p114_rejects_draft_tender(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P114-2028-0004")
		sup = self._ensure_supplier("B")
		self._mk_timeline(tm2.name, submission_deadline_at=add_to_date(now_datetime(), days=5))
		self._mk_participation(tm2.name, sup)
		self.assertEqual(tm2.status, "Draft")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Bid Draft Metadata",
					"tm2_tender": tm2.name,
					"supplier": sup,
					"dsm_output_code": "DSM-P114-DRAFT-TND",
				}
			).insert(ignore_permissions=True)

	def test_p114_unique_per_tender_supplier(self) -> None:
		tm2, sup = self._fixture_open_deadline(tender_code="TND-P114-2028-0005")
		frappe.get_doc(
			{
				"doctype": "TM2 Bid Draft Metadata",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"dsm_output_code": "DSM-1",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Bid Draft Metadata",
					"tm2_tender": tm2.name,
					"supplier": sup,
					"dsm_output_code": "DSM-2",
				}
			).insert(ignore_permissions=True)

	def test_p114_requires_participation(self) -> None:
		tm2, _sup = self._fixture_open_deadline(tender_code="TND-P114-2028-0006")
		other = self._ensure_supplier("NoPart")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "TM2 Bid Draft Metadata",
					"tm2_tender": tm2.name,
					"supplier": other,
					"dsm_output_code": "DSM-NOP",
				}
			).insert(ignore_permissions=True)

	def test_p114_identity_immutable(self) -> None:
		tm2, sup = self._fixture_open_deadline(tender_code="TND-P114-2028-0007")
		dm = frappe.get_doc(
			{
				"doctype": "TM2 Bid Draft Metadata",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"dsm_output_code": "DSM-X",
			}
		).insert(ignore_permissions=True)
		other = self._ensure_supplier("Other")
		self._mk_participation(tm2.name, other)
		dm.reload()
		dm.supplier = other
		with self.assertRaises(frappe.ValidationError):
			dm.save(ignore_permissions=True)

	def test_p114_no_body_column_fieldtypes(self) -> None:
		meta = frappe.get_meta("TM2 Bid Draft Metadata")
		forbidden_types = ("Long Text", "HTML Editor", "Markdown Editor", "Text Editor", "Attach", "Attach Image")
		for df in meta.fields:
			self.assertNotIn(
				df.fieldtype,
				forbidden_types,
				msg=f"field {df.fieldname} uses disallowed type {df.fieldtype} for draft-body exclusion",
			)

	def test_p114_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Bid Draft Metadata")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"draft_metadata_code",
			"tm2_tender",
			"tender_code",
			"supplier",
			"supplier_code",
			"dsm_output_code",
			"draft_status",
			"draft_started_at",
			"last_saved_at",
			"completeness_status",
			"validation_summary",
			"tm2_final_bid_submission",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
