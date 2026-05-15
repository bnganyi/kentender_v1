# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-21 — TM2 Evaluation Handoff Record (EHR-{tender_code}, TM2-EHR-001/002/004).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_evaluation_handoff_record_p1_21
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


class TestTM2EvaluationHandoffRecordP121(
	_TM2BidSubmissionP115FixtureMixin, _ReleaseProcurementPackageHandoffFixtures
):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Evaluation Handoff Record",
			filters={"tender_code": ["like", "TND-P121%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Evaluation Handoff Record", row):
				frappe.delete_doc("TM2 Evaluation Handoff Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Closing Record",
			filters={"tender_code": ["like", "TND-P121%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Closing Record", row):
				frappe.delete_doc("TM2 Tender Closing Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P121%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P121%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _fixture_closed_tender(self, *, tender_code: str = "TND-P121-2028-0001"):
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
		frappe.get_doc(
			{
				"doctype": "TM2 Tender Closing Record",
				"tm2_tender": tm2.name,
				"closing_status": "Closed On Time",
				"valid_submission_count": 1,
				"withdrawn_submission_count": 0,
				"late_attempt_count": 0,
				"closing_payload": {},
			}
		).insert(ignore_permissions=True)
		return tm2

	def _ehr_doc(self, tm2_name: str, **kwargs) -> dict:
		base = {
			"doctype": "TM2 Evaluation Handoff Record",
			"tm2_tender": tm2_name,
			"opening_record_code": "OPEN-P121-FIXTURE-001",
			"dem_output_code": "DEM-P121-001",
			"dsm_output_code": "DSM-P121-001",
			"tender_std_instance_code": "TSI-P121-001",
			"opened_submission_refs": {"refs": ["BID-P121-FAKE-01"]},
			"handoff_payload": {"fixture": True},
			"handoff_status": "Not Ready",
		}
		base.update(kwargs)
		return base

	def test_p121_insert_ehr_code(self) -> None:
		tm2 = self._fixture_closed_tender()
		e = frappe.get_doc(self._ehr_doc(tm2.name)).insert(ignore_permissions=True)
		self.assertEqual(e.evaluation_handoff_code, f"EHR-{tm2.tender_code}")
		self.assertEqual(e.name, e.evaluation_handoff_code)

	def test_p121_duplicate_per_tender_rejected(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P121-2028-0002")
		frappe.get_doc(self._ehr_doc(tm2.name)).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._ehr_doc(tm2.name, dem_output_code="DEM-OTHER")).insert(ignore_permissions=True)

	def test_p121_ehr_001_requires_opening_code(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P121-2028-0003")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._ehr_doc(tm2.name, opening_record_code=" ")).insert(ignore_permissions=True)

	def test_p121_ehr_002_requires_dem(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P121-2028-0004")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._ehr_doc(tm2.name, dem_output_code=" ")).insert(ignore_permissions=True)

	def test_p121_opened_refs_must_be_strings(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P121-2028-0005")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._ehr_doc(tm2.name, opened_submission_refs={"refs": [1, 2]})
			).insert(ignore_permissions=True)

	def test_p121_pre_accept_can_change_handoff_status(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P121-2028-0006")
		e = frappe.get_doc(self._ehr_doc(tm2.name)).insert(ignore_permissions=True)
		e.reload()
		e.handoff_status = "Ready"
		e.save(ignore_permissions=True)
		self.assertEqual(e.handoff_status, "Ready")

	def test_p121_ehr_004_locked_after_evaluation_acceptance(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P121-2028-0007")
		e = frappe.get_doc(self._ehr_doc(tm2.name)).insert(ignore_permissions=True)
		e.reload()
		e.accepted_by_evaluation_at = now_datetime()
		e.save(ignore_permissions=True)
		e.reload()
		e.dsm_output_code = "DSM-TAMPER"
		with self.assertRaises(frappe.ValidationError):
			e.save(ignore_permissions=True)

	def test_p121_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Evaluation Handoff Record")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"evaluation_handoff_code",
			"tm2_tender",
			"tender_code",
			"opening_record_code",
			"dem_output_code",
			"dsm_output_code",
			"tender_std_instance_code",
			"opened_submission_refs",
			"addendum_history_refs",
			"handoff_payload",
			"handoff_status",
			"sent_by",
			"sent_at",
			"accepted_by_evaluation_at",
			"rejection_reason",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
