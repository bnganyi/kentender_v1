# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-18 — TM2 Late Submission Attempt (LATE-* codes, TM2-LATE-002/003, late-time gate).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_late_submission_attempt_p1_18
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)
from kentender_procurement.tender_management.tests.test_tm2_bid_submission_p1_15 import (
	_TM2BidSubmissionP115FixtureMixin,
)


class TestTM2LateSubmissionAttemptP118(
	_TM2BidSubmissionP115FixtureMixin, _ReleaseProcurementPackageHandoffFixtures
):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Late Submission Attempt",
			filters={"tender_code": ["like", "TND-P118%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Late Submission Attempt", row):
				frappe.delete_doc("TM2 Late Submission Attempt", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P118%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P118%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P118%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _fixture_published_past_deadline(self, *, tender_code: str = "TND-P118-2028-0001"):
		tm2, sup = self._fixture_published_with_timeline(tender_code=tender_code)
		tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2.name}, "name")
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl_name,
			"submission_deadline_at",
			add_to_date(now_datetime(), days=-1),
		)
		return tm2, sup

	def _late_payload(self, tm2_name: str, sup_name: str, **kwargs) -> dict:
		base = {
			"doctype": "TM2 Late Submission Attempt",
			"tm2_tender": tm2_name,
			"supplier": sup_name,
			"attempted_payload_metadata": {"denial_code": "AUTH_DEADLINE_PASSED"},
		}
		base.update(kwargs)
		return base

	def test_p118_insert_code_sequence(self) -> None:
		tm2, sup = self._fixture_published_past_deadline()
		prefix = f"LATE-{tm2.tender_code}-{sup}-"
		a1 = frappe.get_doc(self._late_payload(tm2.name, sup)).insert(ignore_permissions=True)
		self.assertEqual(a1.late_attempt_code, f"{prefix}01")
		self.assertEqual(a1.name, a1.late_attempt_code)
		a2 = frappe.get_doc(self._late_payload(tm2.name, sup)).insert(ignore_permissions=True)
		self.assertEqual(a2.late_attempt_code, f"{prefix}02")

	def test_p118_rejects_not_late(self) -> None:
		tm2, sup = self._fixture_published_with_timeline(tender_code="TND-P118-2028-0002")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._late_payload(tm2.name, sup)).insert(ignore_permissions=True)

	def test_p118_late_002_immutable(self) -> None:
		tm2, sup = self._fixture_published_past_deadline(tender_code="TND-P118-2028-0003")
		a = frappe.get_doc(self._late_payload(tm2.name, sup)).insert(ignore_permissions=True)
		a.reload()
		a.rejection_reason = "Tampered"
		with self.assertRaises(frappe.ValidationError):
			a.save(ignore_permissions=True)

	def test_p118_late_003_forbidden_metadata(self) -> None:
		tm2, sup = self._fixture_published_past_deadline(tender_code="TND-P118-2028-0004")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._late_payload(
					tm2.name,
					sup,
					attempted_payload_metadata={"sealed_bid_content": "x"},
				)
			).insert(ignore_permissions=True)

	def test_p118_default_rejection_reason(self) -> None:
		tm2, sup = self._fixture_published_past_deadline(tender_code="TND-P118-2028-0005")
		a = frappe.get_doc(
			{
				"doctype": "TM2 Late Submission Attempt",
				"tm2_tender": tm2.name,
				"supplier": sup,
				"attempted_payload_metadata": {},
			}
		).insert(ignore_permissions=True)
		self.assertIn("AUTH_DEADLINE_PASSED", a.rejection_reason)

	def test_p118_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Late Submission Attempt")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"late_attempt_code",
			"tm2_tender",
			"tender_code",
			"supplier",
			"supplier_code",
			"attempted_by",
			"attempted_at",
			"submission_deadline_at",
			"rejection_reason",
			"attempted_payload_metadata",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
