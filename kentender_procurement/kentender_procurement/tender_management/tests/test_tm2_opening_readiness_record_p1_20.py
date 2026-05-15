# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-20 — TM2 Opening Readiness Record (ORR-{tender_code}, TM2-ORR-001/002/004/005).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_opening_readiness_record_p1_20
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


class TestTM2OpeningReadinessRecordP120(
	_TM2BidSubmissionP115FixtureMixin, _ReleaseProcurementPackageHandoffFixtures
):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Opening Readiness Record",
			filters={"tender_code": ["like", "TND-P120%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Opening Readiness Record", row):
				frappe.delete_doc("TM2 Opening Readiness Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Closing Record",
			filters={"tender_code": ["like", "TND-P120%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Closing Record", row):
				frappe.delete_doc("TM2 Tender Closing Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P120%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P120%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _fixture_closed_tender(self, *, tender_code: str = "TND-P120-2028-0001"):
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
		closing = frappe.get_doc(
			{
				"doctype": "TM2 Tender Closing Record",
				"tm2_tender": tm2.name,
				"closing_status": "Closed On Time",
				"valid_submission_count": 1,
				"withdrawn_submission_count": 0,
				"late_attempt_count": 0,
				"closing_payload": {"fixture": True},
			}
		).insert(ignore_permissions=True)
		return tm2, closing

	def _orr_doc(self, tm2_name: str, closing_name: str, **kwargs) -> dict:
		base = {
			"doctype": "TM2 Opening Readiness Record",
			"tm2_tender": tm2_name,
			"tm2_tender_closing_record": closing_name,
			"dom_output_code": "DOM-P120-001",
			"tender_std_instance_code": "TSI-P120-001",
			"sealed_submission_refs": {"refs": ["BID-P120-FAKE-01"]},
			"valid_submission_count": 1,
			"readiness_status": "Not Ready",
		}
		base.update(kwargs)
		return base

	def test_p120_insert_orr_code(self) -> None:
		tm2, closing = self._fixture_closed_tender()
		o = frappe.get_doc(self._orr_doc(tm2.name, closing.name)).insert(ignore_permissions=True)
		self.assertEqual(o.opening_readiness_code, f"ORR-{tm2.tender_code}")
		self.assertEqual(o.name, o.opening_readiness_code)

	def test_p120_duplicate_per_tender_rejected(self) -> None:
		tm2, closing = self._fixture_closed_tender(tender_code="TND-P120-2028-0002")
		frappe.get_doc(self._orr_doc(tm2.name, closing.name)).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._orr_doc(tm2.name, closing.name, sealed_submission_refs={"refs": ["BID-OTHER"]})
			).insert(ignore_permissions=True)

	def test_p120_orr_001_wrong_closing_tender(self) -> None:
		tm2_a, closing_a = self._fixture_closed_tender(tender_code="TND-P120-2028-0003")
		tm2_b, closing_b = self._fixture_closed_tender(tender_code="TND-P120-2028-0004")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._orr_doc(tm2_b.name, closing_a.name)).insert(ignore_permissions=True)

	def test_p120_orr_002_requires_dom(self) -> None:
		tm2, closing = self._fixture_closed_tender(tender_code="TND-P120-2028-0005")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._orr_doc(tm2.name, closing.name, dom_output_code=" ")).insert(
				ignore_permissions=True
			)

	def test_p120_orr_004_refs_must_be_string_list(self) -> None:
		tm2, closing = self._fixture_closed_tender(tender_code="TND-P120-2028-0006")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._orr_doc(tm2.name, closing.name, sealed_submission_refs={"refs": [1, 2]})
			).insert(ignore_permissions=True)

	def test_p120_pre_accept_can_change_readiness_status(self) -> None:
		tm2, closing = self._fixture_closed_tender(tender_code="TND-P120-2028-0007")
		o = frappe.get_doc(self._orr_doc(tm2.name, closing.name)).insert(ignore_permissions=True)
		o.reload()
		o.readiness_status = "Ready"
		o.save(ignore_permissions=True)
		self.assertEqual(o.readiness_status, "Ready")

	def test_p120_orr_005_locked_after_opening_acceptance(self) -> None:
		tm2, closing = self._fixture_closed_tender(tender_code="TND-P120-2028-0008")
		o = frappe.get_doc(self._orr_doc(tm2.name, closing.name)).insert(ignore_permissions=True)
		o.reload()
		o.accepted_by_opening_module_at = now_datetime()
		o.save(ignore_permissions=True)
		o.reload()
		o.dom_output_code = "DOM-TAMPER"
		with self.assertRaises(frappe.ValidationError):
			o.save(ignore_permissions=True)

	def test_p120_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Opening Readiness Record")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"opening_readiness_code",
			"tm2_tender",
			"tender_code",
			"tm2_tender_closing_record",
			"dom_output_code",
			"tender_std_instance_code",
			"sealed_submission_refs",
			"valid_submission_count",
			"readiness_status",
			"blocker_payload",
			"prepared_by",
			"prepared_at",
			"accepted_by_opening_module_at",
			"opening_record_code",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
