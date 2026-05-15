# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0400 — WorksSccCompletionService.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_scc_0400
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.parameter import parse_outputs_stale_flags
from kentender_procurement.tender_management.works_completion.services.scc_completion import (
	WorksSccCompletionService,
)


class TestWorksCompScc0400(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tm2_tender(self) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WORKS-COMP-0400 Test Tender"
		doc.tender_reference = "WORKSCOMP0400-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _delete_std_instances_for_tender(self, tender: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)

	def _delete_tender(self, name: str) -> None:
		if frappe.db.exists("TM2 Tender", name):
			self._delete_std_instances_for_tender(name)
			frappe.delete_doc("TM2 Tender", name, force=True, ignore_permissions=True)

	def _codes(self, out: dict) -> list[str]:
		return [b["code"] for b in out.get("blockers") or []]

	def _full_scc_payload(self) -> dict:
		return {
			"scc.completion_period_months": "12",
			"scc.defects_liability_period_months": "12",
			"scc.performance_security_required": "1",
			"scc.performance_security_percentage": "10",
			"scc.retention_percentage": "10",
			"scc.liquidated_damages_rate": "0.05% per day of delay",
			"scc.advance_payment_allowed": "1",
			"scc.insurance_requirements": "Contractors all risks minimum cover per GCC.",
			"bid_currency": "USD",
			"scc.engineer_or_project_manager": "Employer's Representative",
			"scc.payment_terms": "Interim payments against certified works.",
			"scc.dispute_resolution_forum": "ARBITRATION",
		}

	def test_works_comp_0400_validate_empty_instance(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = WorksSccCompletionService.validate_scc_values(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("SCC_COMPLETION_PERIOD_MISSING", self._codes(out))
			self.assertIn("SCC_PAYMENT_CURRENCY_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0400_insurance_optional_via_configuration_json(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			td = frappe.get_doc("TM2 Tender", tender)
			td.configuration_json = json.dumps({"WORKS.SCC_INSURANCE_OPTIONAL": True})
			td.save(ignore_permissions=True)
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			patch = dict(self._full_scc_payload())
			patch["scc.insurance_requirements"] = ""
			out = WorksSccCompletionService.validate_scc_values(si.name, prospective_patch=patch)
			self.assertNotIn("SCC_INSURANCE_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0400_save_validate_happy_path(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksSccCompletionService.save_scc_values(si.name, self._full_scc_payload())
			out = WorksSccCompletionService.validate_scc_values(si.name)
			self.assertTrue(out["valid"], out)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			vals = {(r.parameter_code or "").strip(): (r.value or "").strip() for r in doc.parameter_values or []}
			self.assertEqual(vals.get("scc.completion_period_months"), "12")
			self.assertEqual(vals.get("bid_currency"), "USD")
		finally:
			self._delete_tender(tender)

	def test_works_comp_0400_alias_payload(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			p = self._full_scc_payload()
			p.pop("scc.completion_period_months")
			p["completion_period_days"] = "18"
			WorksSccCompletionService.save_scc_values(si.name, p)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			vals = {(r.parameter_code or "").strip(): (r.value or "").strip() for r in doc.parameter_values or []}
			self.assertEqual(vals.get("scc.completion_period_months"), "18")
		finally:
			self._delete_tender(tender)

	def test_works_comp_0400_parameter_change_marks_bundle_dcm_stale(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksSccCompletionService.save_scc_values(si.name, self._full_scc_payload())
			inst = frappe.get_doc("Tender STD Instance", si.name)
			first = parse_outputs_stale_flags(inst)
			self.assertIn("Bundle", first)
			self.assertIn("DCM", first)

			WorksSccCompletionService.save_scc_values(
				si.name,
				{"scc.retention_percentage": "8"},
			)
			inst2 = frappe.get_doc("Tender STD Instance", si.name)
			raw = (inst2.outputs_stale_flags or "").strip()
			self.assertTrue(raw)
			parsed = json.loads(raw)
			self.assertIn("Bundle", parsed)
			self.assertIn("DCM", parsed)
		finally:
			self._delete_tender(tender)
