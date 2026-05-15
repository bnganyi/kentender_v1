# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-15 — TM2 Bid Submission (BID-* codes, DSM + publication snapshot, TM2-BID-001/002, LOCK-008).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_bid_submission_p1_15
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class _TM2BidSubmissionP115FixtureMixin:
	"""Shared TM2 bid + supplier fixtures for P1-15 / P1-16 tests (not a TestCase)."""

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
			frappe.throw("No Supplier Group for P1-15 Supplier fixture")
		return sg

	def _ensure_supplier(self, label: str) -> str:
		supplier_name = f"P115 {label} Supplier"
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
				"tender_title": "P115 TM2",
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

	def _fixture_published_with_timeline(self, *, tender_code: str = "TND-P115-2028-0001"):
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

	def _bid_payload(self, tm2_name: str, sup_name: str, **kwargs) -> dict:
		base = {
			"doctype": "TM2 Bid Submission",
			"tm2_tender": tm2_name,
			"supplier": sup_name,
			"dsm_output_code": "DSM-P115-FIXTURE-01",
			"tender_std_instance_code": "TSI-P115-001",
			"publication_snapshot_code": "PUBSNAP-P115-001",
			"addendum_acknowledgement_snapshot": {"ADD-01": "ACKNOWLEDGED"},
		}
		base.update(kwargs)
		return base


class TestTM2BidSubmissionP115(_TM2BidSubmissionP115FixtureMixin, _ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Bid Submission",
			filters={"tender_code": ["like", "TND-P115%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Submission", row):
				frappe.delete_doc("TM2 Bid Submission", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Bid Draft Metadata",
			filters={"tender_code": ["like", "TND-P115%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Draft Metadata", row):
				frappe.delete_doc("TM2 Bid Draft Metadata", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P115%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P115%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P115%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		for sn in self._supplier_names:
			if frappe.db.exists("Supplier", sn):
				frappe.delete_doc("Supplier", sn, force=True, ignore_permissions=True)
		super().tearDown()

	def test_p115_insert_sequence_and_code(self) -> None:
		tm2, sup = self._fixture_published_with_timeline()
		prefix = f"BID-{tm2.tender_code}-{sup}-"
		b1 = frappe.get_doc(self._bid_payload(tm2.name, sup)).insert(ignore_permissions=True)
		self.assertEqual(b1.bid_code, f"{prefix}01")
		self.assertEqual(b1.name, b1.bid_code)
		b2 = frappe.get_doc(self._bid_payload(tm2.name, sup)).insert(ignore_permissions=True)
		self.assertEqual(b2.bid_code, f"{prefix}02")

	def test_p115_bid_001_past_deadline(self) -> None:
		tm2, sup = self._fixture_published_with_timeline(tender_code="TND-P115-2028-0002")
		tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2.name}, "name")
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl_name,
			"submission_deadline_at",
			add_to_date(now_datetime(), days=-1),
		)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._bid_payload(tm2.name, sup)).insert(ignore_permissions=True)

	def test_p115_lock_008_core_immutable(self) -> None:
		tm2, sup = self._fixture_published_with_timeline(tender_code="TND-P115-2028-0003")
		b = frappe.get_doc(self._bid_payload(tm2.name, sup)).insert(ignore_permissions=True)
		b.reload()
		b.dsm_output_code = "TAMPERED"
		with self.assertRaises(frappe.ValidationError):
			b.save(ignore_permissions=True)

	def test_p115_updates_participation_last_bid(self) -> None:
		tm2, sup = self._fixture_published_with_timeline(tender_code="TND-P115-2028-0004")
		b = frappe.get_doc(self._bid_payload(tm2.name, sup)).insert(ignore_permissions=True)
		part = frappe.db.get_value(
			"TM2 Supplier Participation",
			{"tm2_tender": tm2.name, "supplier": sup},
			["last_bid_submission_code", "current_status"],
			as_dict=True,
		)
		self.assertEqual(part.last_bid_submission_code, b.bid_code)
		self.assertEqual(part.current_status, "Bid Submitted")

	def test_p115_links_bid_draft_metadata_final(self) -> None:
		tm2, sup = self._fixture_published_with_timeline(tender_code="TND-P115-2028-0005")
		bdm = frappe.get_doc(
			{
				"doctype": "TM2 Bid Draft Metadata",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"dsm_output_code": "DSM-P115-DRAFT",
			}
		).insert(ignore_permissions=True)
		b = frappe.get_doc(self._bid_payload(tm2.name, sup, dsm_output_code="DSM-P115-SUBMIT")).insert(
			ignore_permissions=True
		)
		bdm.reload()
		self.assertEqual(bdm.tm2_final_bid_submission, b.name)

	def test_p115_previous_submission_lineage(self) -> None:
		tm2, sup = self._fixture_published_with_timeline(tender_code="TND-P115-2028-0006")
		b1 = frappe.get_doc(self._bid_payload(tm2.name, sup)).insert(ignore_permissions=True)
		b2 = frappe.get_doc(
			self._bid_payload(tm2.name, sup, previous_tm2_bid_submission=b1.name)
		).insert(ignore_permissions=True)
		self.assertEqual(b2.previous_tm2_bid_submission, b1.name)

	def test_p115_bid_002_empty_dsm(self) -> None:
		tm2, sup = self._fixture_published_with_timeline(tender_code="TND-P115-2028-0007")
		pl = self._bid_payload(tm2.name, sup)
		pl["dsm_output_code"] = " "
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(pl).insert(ignore_permissions=True)

	def test_p115_mutable_bid_status_after_insert(self) -> None:
		tm2, sup = self._fixture_published_with_timeline(tender_code="TND-P115-2028-0008")
		b = frappe.get_doc(self._bid_payload(tm2.name, sup)).insert(ignore_permissions=True)
		b.reload()
		b.bid_status = "Sealed"
		b.save(ignore_permissions=True)
		self.assertEqual(b.bid_status, "Sealed")

	def test_p115_meta_doc_fields(self) -> None:
		meta = frappe.get_meta("TM2 Bid Submission")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"bid_code",
			"tm2_tender",
			"tender_code",
			"supplier",
			"supplier_code",
			"submission_sequence",
			"dsm_output_code",
			"tender_std_instance_code",
			"publication_snapshot_code",
			"addendum_acknowledgement_snapshot",
			"bid_status",
			"submitted_by",
			"submitted_at",
			"sealed_at",
			"submission_hash",
			"total_submitted_price",
			"currency",
			"previous_tm2_bid_submission",
			"superseded_by_tm2_bid_submission",
			"withdrawn_by",
			"withdrawn_at",
			"withdrawal_reason",
			"opened_at",
			"evaluation_locked_at",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
