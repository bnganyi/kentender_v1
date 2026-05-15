# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-19 — TM2 Tender Closing Record (CLS-{tender_code}, TM2-CLS-001/003).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_tender_closing_record_p1_19
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


class TestTM2TenderClosingRecordP119(
	_TM2BidSubmissionP115FixtureMixin, _ReleaseProcurementPackageHandoffFixtures
):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Tender Closing Record",
			filters={"tender_code": ["like", "TND-P119%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Closing Record", row):
				frappe.delete_doc("TM2 Tender Closing Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P119%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P119%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _fixture_published_past_deadline(self, *, tender_code: str = "TND-P119-2028-0001"):
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tender_code)
		tm2.status = "Published"
		tm2.flags.ignore_tm2_tender_governed_status_mutation = True
		tm2.save(ignore_permissions=True)
		self._mk_timeline(tm2.name, submission_deadline_at=add_to_date(now_datetime(), days=5))
		tl_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2.name}, "name")
		frappe.db.set_value(
			"TM2 Tender Timeline",
			tl_name,
			"submission_deadline_at",
			add_to_date(now_datetime(), days=-1),
		)
		return tm2

	def _fixture_published_future_deadline(self, *, tender_code: str = "TND-P119-2028-0002"):
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tender_code)
		tm2.status = "Published"
		tm2.flags.ignore_tm2_tender_governed_status_mutation = True
		tm2.save(ignore_permissions=True)
		self._mk_timeline(tm2.name, submission_deadline_at=add_to_date(now_datetime(), days=5))
		return tm2

	def _closing_doc(self, tm2_name: str, **kwargs) -> dict:
		base = {
			"doctype": "TM2 Tender Closing Record",
			"tm2_tender": tm2_name,
			"closing_status": "Closed On Time",
			"valid_submission_count": 2,
			"withdrawn_submission_count": 0,
			"late_attempt_count": 0,
			"closing_payload": {"note": "fixture"},
		}
		base.update(kwargs)
		return base

	def test_p119_insert_closing_code(self) -> None:
		tm2 = self._fixture_published_past_deadline()
		c = frappe.get_doc(self._closing_doc(tm2.name)).insert(ignore_permissions=True)
		self.assertEqual(c.closing_code, f"CLS-{tm2.tender_code}")
		self.assertEqual(c.name, c.closing_code)
		self.assertEqual(c.no_valid_submissions, 0)

	def test_p119_derives_no_valid_when_zero(self) -> None:
		tm2 = self._fixture_published_past_deadline(tender_code="TND-P119-2028-0003")
		c = frappe.get_doc(
			self._closing_doc(tm2.name, valid_submission_count=0, closing_status="Closed With No Valid Submissions")
		).insert(ignore_permissions=True)
		self.assertEqual(c.valid_submission_count, 0)
		self.assertEqual(c.no_valid_submissions, 1)

	def test_p119_duplicate_per_tender_rejected(self) -> None:
		tm2 = self._fixture_published_past_deadline(tender_code="TND-P119-2028-0004")
		frappe.get_doc(self._closing_doc(tm2.name)).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._closing_doc(tm2.name, closing_payload={"second": True})).insert(
				ignore_permissions=True
			)

	def test_p119_cls_001_before_deadline_rejected(self) -> None:
		tm2 = self._fixture_published_future_deadline()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._closing_doc(tm2.name)).insert(ignore_permissions=True)

	def test_p119_cls_001_early_close_cancelled_allowed(self) -> None:
		tm2 = self._fixture_published_future_deadline(tender_code="TND-P119-2028-0005")
		tm2.status = "Cancelled"
		tm2.save(ignore_permissions=True)
		c = frappe.get_doc(self._closing_doc(tm2.name)).insert(ignore_permissions=True)
		self.assertTrue(c.name)

	def test_p119_cls_003_immutable(self) -> None:
		tm2 = self._fixture_published_past_deadline(tender_code="TND-P119-2028-0006")
		c = frappe.get_doc(self._closing_doc(tm2.name)).insert(ignore_permissions=True)
		c.reload()
		c.closing_status = "Closure Failed"
		with self.assertRaises(frappe.ValidationError):
			c.save(ignore_permissions=True)

	def test_p119_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Tender Closing Record")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"closing_code",
			"tm2_tender",
			"tender_code",
			"submission_deadline_at",
			"closed_at",
			"closed_by",
			"closing_status",
			"valid_submission_count",
			"withdrawn_submission_count",
			"late_attempt_count",
			"no_valid_submissions",
			"closing_payload",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
