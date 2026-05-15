# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-22 — TM2 Contract Handoff Reference (CHR-{tender_code}, TM2-CHR-001/002/003/005).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_contract_handoff_reference_p1_22
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, flt, now_datetime

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)
from kentender_procurement.tender_management.tests.test_tm2_bid_submission_p1_15 import (
	_TM2BidSubmissionP115FixtureMixin,
)


class TestTM2ContractHandoffReferenceP122(
	_TM2BidSubmissionP115FixtureMixin, _ReleaseProcurementPackageHandoffFixtures
):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Contract Handoff Reference",
			filters={"tender_code": ["like", "TND-P122%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Contract Handoff Reference", row):
				frappe.delete_doc("TM2 Contract Handoff Reference", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Closing Record",
			filters={"tender_code": ["like", "TND-P122%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Closing Record", row):
				frappe.delete_doc("TM2 Tender Closing Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P122%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P122%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _fixture_closed_tender(
		self, *, tender_code: str = "TND-P122-2028-0001", procurement_category: str = "Goods"
	):
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code=tender_code)
		if procurement_category != "Goods":
			tm2.procurement_category = procurement_category
			tm2.save(ignore_permissions=True)
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

	def _chr_doc(self, tm2_name: str, supplier_name: str, **kwargs) -> dict:
		base = {
			"doctype": "TM2 Contract Handoff Reference",
			"tm2_tender": tm2_name,
			"award_decision_code": "AWD-P122-FIXTURE-001",
			"awarded_supplier": supplier_name,
			"dcm_output_code": "DCM-P122-001",
			"tender_std_instance_code": "TSI-P122-001",
			"contract_handoff_payload": {"fixture": True},
			"handoff_status": "Not Ready",
			"currency": "KES",
		}
		base.update(kwargs)
		return base

	def test_p122_insert_chr_code(self) -> None:
		tm2 = self._fixture_closed_tender()
		sup = self._ensure_supplier("CHR-A")
		c = frappe.get_doc(self._chr_doc(tm2.name, sup)).insert(ignore_permissions=True)
		self.assertEqual(c.contract_handoff_code, f"CHR-{tm2.tender_code}")
		self.assertEqual(c.name, c.contract_handoff_code)

	def test_p122_duplicate_per_tender_rejected(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P122-2028-0002")
		sup = self._ensure_supplier("CHR-B")
		frappe.get_doc(self._chr_doc(tm2.name, sup)).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._chr_doc(tm2.name, sup, dcm_output_code="DCM-OTHER")).insert(ignore_permissions=True)

	def test_p122_chr_001_requires_award_code(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P122-2028-0003")
		sup = self._ensure_supplier("CHR-C")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._chr_doc(tm2.name, sup, award_decision_code=" ")).insert(ignore_permissions=True)

	def test_p122_chr_002_requires_dcm(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P122-2028-0004")
		sup = self._ensure_supplier("CHR-D")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._chr_doc(tm2.name, sup, dcm_output_code=" ")).insert(ignore_permissions=True)

	def test_p122_chr_003_works_requires_price_and_boq(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P122-2028-0005", procurement_category="Works")
		sup = self._ensure_supplier("CHR-E")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._chr_doc(tm2.name, sup)).insert(ignore_permissions=True)
		c = frappe.get_doc(
			self._chr_doc(
				tm2.name,
				sup,
				final_evaluated_price=96754000,
				final_boq_reference="BOQ-P122-CORRECTED-01",
			)
		).insert(ignore_permissions=True)
		self.assertEqual(flt(c.final_evaluated_price), 96754000)

	def test_p122_goods_allows_missing_evaluated_price(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P122-2028-0006")
		sup = self._ensure_supplier("CHR-F")
		c = frappe.get_doc(self._chr_doc(tm2.name, sup)).insert(ignore_permissions=True)
		self.assertFalse(c.final_evaluated_price)

	def test_p122_addendum_refs_must_be_strings(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P122-2028-0007")
		sup = self._ensure_supplier("CHR-G")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._chr_doc(tm2.name, sup, addendum_history_refs={"refs": [1]})
			).insert(ignore_permissions=True)

	def test_p122_pre_accept_can_change_handoff_status(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P122-2028-0008")
		sup = self._ensure_supplier("CHR-H")
		c = frappe.get_doc(self._chr_doc(tm2.name, sup)).insert(ignore_permissions=True)
		c.reload()
		c.handoff_status = "Ready"
		c.save(ignore_permissions=True)
		self.assertEqual(c.handoff_status, "Ready")

	def test_p122_chr_005_locked_after_contract_acceptance(self) -> None:
		tm2 = self._fixture_closed_tender(tender_code="TND-P122-2028-0009")
		sup = self._ensure_supplier("CHR-I")
		c = frappe.get_doc(self._chr_doc(tm2.name, sup)).insert(ignore_permissions=True)
		c.reload()
		c.accepted_by_contract_module_at = now_datetime()
		c.save(ignore_permissions=True)
		c.reload()
		c.dcm_output_code = "DCM-TAMPER"
		with self.assertRaises(frappe.ValidationError):
			c.save(ignore_permissions=True)

	def test_p122_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Contract Handoff Reference")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"contract_handoff_code",
			"tm2_tender",
			"tender_code",
			"award_decision_code",
			"awarded_supplier",
			"dcm_output_code",
			"tender_std_instance_code",
			"final_evaluated_price",
			"currency",
			"final_boq_reference",
			"addendum_history_refs",
			"contract_handoff_payload",
			"handoff_status",
			"created_by",
			"created_at",
			"accepted_by_contract_module_at",
			"rejection_reason",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
