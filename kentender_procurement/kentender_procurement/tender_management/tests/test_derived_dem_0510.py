# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0510 — ``DemGenerator.generateDEM``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_dem_0510
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.dem.generator import DemGenerator
from kentender_procurement.tender_management.derived_models.dem.schema import (
	DEM_GENERATION_FAILED,
	MANUAL_EVALUATION_CRITERIA_DENIED,
)
from kentender_procurement.tender_management.derived_models.dem.validator import validate_dem_source_traces
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


def _minimal_boq_payload() -> dict:
	return {
		"header": {"currency": "USD"},
		"bills": [
			{
				"bill_number": "B1",
				"bill_title": "Preliminaries",
				"bill_type": "Standard",
				"order_index": 0,
				"items": [
					{
						"item_number": "1.1",
						"description": "Site clearance",
						"unit": "m2",
						"quantity": 100,
						"item_type": "Normal",
						"supplier_input_mode": "Rate Only",
					},
				],
			},
		],
	}


class TestDerivedDem0510(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		frappe.clear_messages()
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		frappe.clear_messages()
		super().tearDown()

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			for out_name in frappe.get_all(
				"Tender STD Generated Output",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Generated Output",
					out_name,
					force=True,
					ignore_permissions=True,
				)
			for boq_name in frappe.get_all(
				"Tender STD Instance BOQ",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Instance BOQ",
					boq_name,
					force=True,
					ignore_permissions=True,
				)
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def test_derived_0510_generate_dem_seven_stages_and_validates(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0510 DEM"
		doc.tender_reference = "DERIVED0510-DEM"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, _minimal_boq_payload())
			payload = DemGenerator.generateDEM(si.name)
			validate_dem_source_traces(payload)
			self.assertEqual(len(payload["stages"]), 7)
			types = [s["stage_type"] for s in payload["stages"]]
			self.assertEqual(
				types,
				[
					"Responsiveness",
					"Eligibility",
					"Qualification",
					"Technical",
					"Financial",
					"BOQArithmetic",
					"Ranking",
				],
			)
			self.assertEqual(payload["ranking"]["method"], "LowestEvaluatedCost")
			self.assertTrue(payload["boq_arithmetic_correction"]["enabled"])
			self.assertEqual(len(payload["boq_arithmetic_correction"]["correction_rules"]), 5)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0510_qualification_includes_threshold_when_turnover_set(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0510 QUAL"
		doc.tender_reference = "DERIVED0510-QUAL"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			for pc, val in (
				("minimum_average_annual_turnover_amount", "5000000"),
				("minimum_average_annual_turnover_currency", "KES"),
				("minimum_average_annual_turnover_years", "3"),
			):
				StdInstanceParameterService.set_parameter_value(
					si.name,
					pc,
					val,
					ignore_publication_lock=True,
				)
			payload = DemGenerator.generateDEM(si.name)
			qual = next(s for s in payload["stages"] if s["stage_code"] == "DEM-STG-3")
			codes = [r["rule_code"] for r in qual["rules"]]
			self.assertIn("DEM-QUAL-TURNOVER", codes)
			t_rule = next(r for r in qual["rules"] if r["rule_code"] == "DEM-QUAL-TURNOVER")
			self.assertEqual(t_rule["rule_type"], "Threshold")
			self.assertIn("threshold_value", t_rule)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0510_rejects_manual_criteria_in_parameter_json(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0510 MANUAL"
		doc.tender_reference = "DERIVED0510-MAN"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			inst = frappe.get_doc("Tender STD Instance", si.name)
			inst.append(
				"parameter_values",
				{
					"value_code": "DEM0510-BAD",
					"parameter_code": "key_personnel_required",
					"value": '{"manual_criteria": true}',
					"value_status": "Provided",
					"source": "Officer Entry",
				},
			)
			inst.save(ignore_permissions=True)
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				DemGenerator.generateDEM(si.name)
			self.assertEqual(_last_msg_title(), MANUAL_EVALUATION_CRITERIA_DENIED)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0510_invalid_instance(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			DemGenerator.generateDEM("STDINST-NONEXISTENT-DEM0510")
		self.assertEqual(_last_msg_title(), DEM_GENERATION_FAILED)
