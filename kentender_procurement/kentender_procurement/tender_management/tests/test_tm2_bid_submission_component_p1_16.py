# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-16 — TM2 Bid Submission Component (BSC-* codes, TM2-BSC-001/002/004).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_bid_submission_component_p1_16
"""

from __future__ import annotations

import frappe
from frappe.utils import cint

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)
from kentender_procurement.tender_management.tests.test_tm2_bid_submission_p1_15 import (
	_TM2BidSubmissionP115FixtureMixin,
)


class TestTM2BidSubmissionComponentP116(
	_TM2BidSubmissionP115FixtureMixin, _ReleaseProcurementPackageHandoffFixtures
):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []
	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Bid Submission Component",
			filters={"tender_code": ["like", "TND-P116%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Submission Component", row):
				frappe.delete_doc("TM2 Bid Submission Component", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Bid Submission",
			filters={"tender_code": ["like", "TND-P116%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Submission", row):
				frappe.delete_doc("TM2 Bid Submission", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P116%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P116%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P116%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _fixture_p116_bid(self, *, tender_code: str = "TND-P116-2028-0001"):
		tm2, sup = self._fixture_published_with_timeline(tender_code=tender_code)
		b = frappe.get_doc(self._bid_payload(tm2.name, sup, dsm_output_code="DSM-P116-01")).insert(
			ignore_permissions=True
		)
		return tm2, sup, b

	def _bsc_payload(self, bid_name: str, **kwargs) -> dict:
		base = {
			"doctype": "TM2 Bid Submission Component",
			"tm2_bid_submission": bid_name,
			"std_submission_requirement_code": "REQ-P116-ALPHA",
			"component_type": "STRUCTURED_TEXT",
			"component_label": "Technical offer",
			"required": 0,
			"submitted": 0,
		}
		base.update(kwargs)
		return base

	def test_p116_insert_bsc_sequence(self) -> None:
		_, _, b = self._fixture_p116_bid()
		prefix = f"BSC-{b.bid_code}-"
		c1 = frappe.get_doc(self._bsc_payload(b.name)).insert(ignore_permissions=True)
		self.assertEqual(c1.bsc_code, f"{prefix}01")
		self.assertEqual(c1.name, c1.bsc_code)
		c2 = frappe.get_doc(
			self._bsc_payload(b.name, std_submission_requirement_code="REQ-P116-BETA")
		).insert(ignore_permissions=True)
		self.assertEqual(c2.bsc_code, f"{prefix}02")

	def test_p116_bsc_004_immutable(self) -> None:
		_, _, b = self._fixture_p116_bid(tender_code="TND-P116-2028-0002")
		c = frappe.get_doc(self._bsc_payload(b.name)).insert(ignore_permissions=True)
		c.reload()
		c.component_label = "Tampered"
		with self.assertRaises(frappe.ValidationError):
			c.save(ignore_permissions=True)

	def test_p116_bsc_002_required_flag_immutable(self) -> None:
		_, _, b = self._fixture_p116_bid(tender_code="TND-P116-2028-0009")
		c = frappe.get_doc(self._bsc_payload(b.name, required=0)).insert(ignore_permissions=True)
		c.reload()
		c.required = 1
		c.flags.tm2_bsc_allowed_requirement_codes = {"REQ-P116-ALPHA"}
		with self.assertRaises(frappe.ValidationError):
			c.save(ignore_permissions=True)

	def test_p116_duplicate_requirement_rejected(self) -> None:
		_, _, b = self._fixture_p116_bid(tender_code="TND-P116-2028-0003")
		frappe.get_doc(self._bsc_payload(b.name)).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._bsc_payload(b.name)).insert(ignore_permissions=True)

	def test_p116_bsc_001_unknown_requirement_when_allowlist_set(self) -> None:
		_, _, b = self._fixture_p116_bid(tender_code="TND-P116-2028-0004")
		doc = frappe.get_doc(self._bsc_payload(b.name, std_submission_requirement_code="REQ-WRONG"))
		doc.flags.tm2_bsc_allowed_requirement_codes = {"REQ-P116-ALPHA"}
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_p116_bsc_002_required_without_dsm_context(self) -> None:
		_, _, b = self._fixture_p116_bid(tender_code="TND-P116-2028-0005")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._bsc_payload(b.name, required=1)).insert(ignore_permissions=True)

	def test_p116_bsc_002_required_with_allowlist(self) -> None:
		_, _, b = self._fixture_p116_bid(tender_code="TND-P116-2028-0006")
		doc = frappe.get_doc(
			self._bsc_payload(
				b.name,
				required=1,
				std_submission_requirement_code="REQ-P116-REQD",
			)
		)
		doc.flags.tm2_bsc_allowed_requirement_codes = {"REQ-P116-REQD"}
		doc.insert(ignore_permissions=True)
		self.assertEqual(cint(doc.required), 1)

	def test_p116_submitted_file_like_needs_ref(self) -> None:
		_, _, b = self._fixture_p116_bid(tender_code="TND-P116-2028-0007")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._bsc_payload(
					b.name,
					std_submission_requirement_code="REQ-P116-FILE",
					component_type="FILE_SET",
					submitted=1,
				)
			).insert(ignore_permissions=True)

	def test_p116_submitted_file_like_with_ref_ok(self) -> None:
		_, _, b = self._fixture_p116_bid(tender_code="TND-P116-2028-0008")
		c = frappe.get_doc(
			self._bsc_payload(
				b.name,
				std_submission_requirement_code="REQ-P116-FILE",
				component_type="FILE_SET",
				submitted=1,
				file_ref="FILE-P116-001",
			)
		).insert(ignore_permissions=True)
		self.assertEqual(c.file_ref, "FILE-P116-001")

	def test_p116_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Bid Submission Component")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"tm2_bid_submission",
			"bid_code",
			"tm2_tender",
			"tender_code",
			"supplier",
			"supplier_code",
			"bsc_code",
			"std_submission_requirement_code",
			"component_type",
			"component_label",
			"required",
			"submitted",
			"file_ref",
			"structured_payload_ref",
			"validation_status",
			"validation_payload",
		):
			self.assertIn(req, names, msg=f"missing field {req}")