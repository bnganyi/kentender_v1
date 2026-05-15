# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-17 — TM2 Bid Receipt (RCT-{bid_code}, TM2-RCT-001/002/003).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_bid_receipt_p1_17
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)
from kentender_procurement.tender_management.tests.test_tm2_bid_submission_p1_15 import (
	_TM2BidSubmissionP115FixtureMixin,
)


class TestTM2BidReceiptP117(_TM2BidSubmissionP115FixtureMixin, _ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Bid Receipt",
			filters={"tender_code": ["like", "TND-P117%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Receipt", row):
				frappe.delete_doc("TM2 Bid Receipt", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Bid Submission",
			filters={"tender_code": ["like", "TND-P117%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Submission", row):
				frappe.delete_doc("TM2 Bid Submission", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P117%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P117%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P117%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _fixture_p117_bid(self, *, tender_code: str = "TND-P117-2028-0001"):
		tm2, sup = self._fixture_published_with_timeline(tender_code=tender_code)
		b = frappe.get_doc(self._bid_payload(tm2.name, sup, dsm_output_code="DSM-P117-01")).insert(
			ignore_permissions=True
		)
		return tm2, sup, b

	def _receipt_payload(self, bid_name: str, **kwargs) -> dict:
		base = {
			"doctype": "TM2 Bid Receipt",
			"tm2_bid_submission": bid_name,
			"receipt_payload": {"event": "bid_submitted", "bid_code_ref": True},
		}
		base.update(kwargs)
		return base

	def test_p117_receipt_code_rct_prefix(self) -> None:
		_, _, b = self._fixture_p117_bid()
		r = frappe.get_doc(self._receipt_payload(b.name)).insert(ignore_permissions=True)
		self.assertEqual(r.receipt_code, f"RCT-{b.bid_code}")
		self.assertEqual(r.name, r.receipt_code)

	def test_p117_rct_001_one_receipt_per_bid(self) -> None:
		_, _, b = self._fixture_p117_bid(tender_code="TND-P117-2028-0002")
		frappe.get_doc(self._receipt_payload(b.name)).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._receipt_payload(b.name, receipt_payload={"event": "duplicate"})
			).insert(ignore_permissions=True)

	def test_p117_rct_003_immutable(self) -> None:
		_, _, b = self._fixture_p117_bid(tender_code="TND-P117-2028-0003")
		r = frappe.get_doc(self._receipt_payload(b.name)).insert(ignore_permissions=True)
		r.reload()
		r.receipt_hash = "TAMPER"
		with self.assertRaises(frappe.ValidationError):
			r.save(ignore_permissions=True)

	def test_p117_rct_002_forbidden_payload_key(self) -> None:
		_, _, b = self._fixture_p117_bid(tender_code="TND-P117-2028-0004")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._receipt_payload(
					b.name,
					receipt_payload={"sealed_bid_content": "x"},
				)
			).insert(ignore_permissions=True)

	def test_p117_receipt_types(self) -> None:
		_, _, b = self._fixture_p117_bid(tender_code="TND-P117-2028-0005")
		r = frappe.get_doc(
			self._receipt_payload(b.name, receipt_type="Withdrawal", receipt_payload={"event": "withdrawn"})
		).insert(ignore_permissions=True)
		self.assertEqual(r.receipt_type, "Withdrawal")

	def test_p117_issued_at_stamped(self) -> None:
		_, _, b = self._fixture_p117_bid(tender_code="TND-P117-2028-0006")
		r = frappe.get_doc(self._receipt_payload(b.name)).insert(ignore_permissions=True)
		self.assertTrue(r.issued_at)

	def test_p117_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Bid Receipt")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"tm2_bid_submission",
			"bid_code",
			"tm2_tender",
			"tender_code",
			"supplier",
			"supplier_code",
			"receipt_code",
			"receipt_type",
			"issued_at",
			"issued_by_system",
			"receipt_payload",
			"receipt_hash",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
