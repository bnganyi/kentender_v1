# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0210 — WorksEvaluationOptionsService.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_evaluation_options_0210
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
from kentender_procurement.tender_management.std_instance.parameter import (
	parse_outputs_stale_flags,
	StdInstanceParameterService,
)
from kentender_procurement.tender_management.works_completion.services.completion_status import (
	get_completion_status,
)
from kentender_procurement.tender_management.works_completion.services.evaluation_options_completion import (
	DENY_CODE,
	WorksEvaluationOptionsService,
	assert_no_manual_criteria,
)


class TestWorksCompEvaluationOptions0210(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_procurement_tender(self) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WORKS-COMP-0210 Test Tender"
		doc.tender_reference = "WORKSCOMP0210-REF"
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
		if frappe.db.exists("Procurement Tender", name):
			self._delete_std_instances_for_tender(name)
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def _codes(self, out: dict) -> list[str]:
		return [b["code"] for b in out.get("blockers") or []]

	def test_works_comp_0210_assert_no_manual_criteria_denies_nested(self) -> None:
		with self.assertRaises(frappe.ValidationError) as ctx:
			assert_no_manual_criteria({"minimum_average_annual_turnover": {"manual_criteria": "x"}})
		self.assertIn(DENY_CODE, str(ctx.exception))

	def test_works_comp_0210_validate_empty_ok(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = WorksEvaluationOptionsService.validate_evaluation_options(si.name)
			self.assertTrue(out["valid"], out)
			self.assertEqual(out.get("blockers"), [])
		finally:
			self._delete_tender(tender)

	def test_works_comp_0210_turnover_amount_requires_currency(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = WorksEvaluationOptionsService.validate_evaluation_options(
				si.name,
				prospective_values={
					"minimum_average_annual_turnover_amount": "5000000",
					"minimum_average_annual_turnover_currency": "",
					"minimum_average_annual_turnover_years": "",
				},
			)
			self.assertFalse(out["valid"])
			self.assertIn("EVAL_TURNOVER_CURRENCY_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0210_save_flat_persists(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksEvaluationOptionsService.save_evaluation_options(
				si.name,
				{
					"key_personnel_required": "1",
					"equipment_schedule_required": "0",
					"similar_works_experience_minimum_contracts": "3",
				},
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			found = {(r.parameter_code or "").strip(): (r.value or "").strip() for r in doc.parameter_values}
			self.assertEqual(found.get("key_personnel_required"), "1")
			self.assertEqual(found.get("equipment_schedule_required"), "0")
			self.assertEqual(found.get("similar_works_experience_minimum_contracts"), "3")
			for row in doc.parameter_values:
				if (row.parameter_code or "").strip() == "key_personnel_required":
					self.assertEqual(row.source, "Works Evaluation Options")
		finally:
			self._delete_tender(tender)

	def test_works_comp_0210_save_nested_flatten(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksEvaluationOptionsService.save_evaluation_options(
				si.name,
				{
					"minimum_average_annual_turnover": {
						"amount": "100000",
						"currency": "KES",
						"years": "3",
					},
				},
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			found = {(r.parameter_code or "").strip(): (r.value or "").strip() for r in doc.parameter_values}
			self.assertEqual(found.get("minimum_average_annual_turnover_amount"), "100000")
			self.assertEqual(found.get("minimum_average_annual_turnover_currency"), "KES")
			self.assertEqual(found.get("minimum_average_annual_turnover_years"), "3")
		finally:
			self._delete_tender(tender)

	def test_works_comp_0210_save_rejects_manual_payload(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			with self.assertRaises(frappe.ValidationError) as ctx:
				WorksEvaluationOptionsService.save_evaluation_options(
					si.name,
					{"custom_scoring_rules": {"weight": 99}},
				)
			self.assertIn(DENY_CODE, str(ctx.exception))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0210_key_personnel_change_marks_stale(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksEvaluationOptionsService.save_evaluation_options(
				si.name,
				{"key_personnel_required": "0"},
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.current_bundle_output_code = "B-0210"
			doc.current_dsm_output_code = "DSM-0210"
			doc.current_dem_output_code = "DEM-0210"
			doc.save(ignore_permissions=True)

			WorksEvaluationOptionsService.save_evaluation_options(
				si.name,
				{"key_personnel_required": "1"},
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			flags = parse_outputs_stale_flags(doc)
			self.assertIn("Bundle", flags)
			self.assertIn("DSM", flags)
			self.assertIn("DEM", flags)
			raw = (doc.outputs_stale_flags or "").strip()
			self.assertIsInstance(json.loads(raw), list)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0210_completion_status_blocked_when_invalid_persisted(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceParameterService.set_parameter_value(
				si.name,
				"minimum_average_annual_turnover_amount",
				"999",
				source="Officer Entry",
				ignore_publication_lock=False,
			)
			out = get_completion_status(si.name)
			eval_stage = next(s for s in out["stages"] if s["stage_code"] == "EVALUATION_OPTIONS")
			self.assertEqual(eval_stage["status"], "Blocked")
			self.assertEqual(out["overall_status"], "Blocked")
		finally:
			self._delete_tender(tender)
