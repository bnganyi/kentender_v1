# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0500 — WorksOutputGenerationService.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_output_generation_0500
"""

from __future__ import annotations

from unittest.mock import patch

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
from kentender_procurement.tender_management.std_instance.generated_output import (
	OUTPUT_TYPES,
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import parse_outputs_stale_flags
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.evaluation_options_completion import (
	DENY_CODE,
)
from kentender_procurement.tender_management.works_completion.services.output_generation import (
	WorksOutputGenerationService,
)


class TestWorksCompOutputGeneration0500(IntegrationTestCase):
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
		doc.tender_title = "WORKS-COMP-0500 Test Tender"
		doc.tender_reference = "WORKSCOMP0500-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _delete_std_instances_for_tender(self, tender: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"procurement_tender": tender},
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

	def _delete_tender(self, name: str) -> None:
		if frappe.db.exists("Procurement Tender", name):
			self._delete_std_instances_for_tender(name)
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def _minimal_valid_boq_payload(self) -> dict:
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

	def test_works_comp_0500_precheck_boq_missing(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			with self.assertRaises(frappe.ValidationError) as ctx:
				WorksOutputGenerationService.assert_prechecks(si.name)
			self.assertIn("BOQ_MISSING", str(ctx.exception))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0500_precheck_manual_criteria_in_parameter_json(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			inst = frappe.get_doc("Tender STD Instance", si.name)
			inst.append(
				"parameter_values",
				{
					"value_code": "WORKS0500-MANUAL-BAD",
					"parameter_code": "key_personnel_required",
					"value": '{"manual_criteria": true}',
					"value_status": "Provided",
					"source": "Officer Entry",
				},
			)
			inst.save(ignore_permissions=True)
			with self.assertRaises(frappe.ValidationError) as ctx:
				WorksOutputGenerationService.assert_prechecks(si.name)
			self.assertIn(DENY_CODE, str(ctx.exception))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0500_generate_all_happy_path(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			out = WorksOutputGenerationService.generate_all_works_outputs(si.name)
			self.assertTrue(out.get("ok"))
			outputs = out.get("outputs") or {}
			self.assertEqual(set(outputs.keys()), set(OUTPUT_TYPES))

			inst = frappe.get_doc("Tender STD Instance", si.name)
			self.assertEqual(inst.current_bundle_output_code, outputs["Bundle"])
			self.assertEqual(inst.current_dsm_output_code, outputs["DSM"])
			self.assertEqual(inst.current_dom_output_code, outputs["DOM"])
			self.assertEqual(inst.current_dem_output_code, outputs["DEM"])
			self.assertEqual(inst.current_dcm_output_code, outputs["DCM"])

			for label, name in outputs.items():
				row = frappe.get_doc("Tender STD Generated Output", name)
				self.assertEqual(row.output_type, label)
				self.assertEqual(row.output_status, "Published")

			flags = parse_outputs_stale_flags(inst)
			for k in OUTPUT_TYPES:
				self.assertNotIn(k, flags)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0500_mid_chain_failure_deletes_partial_publishes(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			calls = {"n": 0}
			real_pub = StdInstanceGeneratedOutputService.publish_output

			def _pub(name: str, **kwargs):
				calls["n"] += 1
				if calls["n"] >= 2:
					raise RuntimeError("simulated publish failure")
				return real_pub(name, **kwargs)

			with patch.object(StdInstanceGeneratedOutputService, "publish_output", side_effect=_pub):
				with self.assertRaises(RuntimeError):
					WorksOutputGenerationService.generate_all_works_outputs(si.name)
			inst = frappe.get_doc("Tender STD Instance", si.name)
			self.assertFalse(inst.current_bundle_output_code)
			count = frappe.db.count(
				"Tender STD Generated Output",
				{"tender_std_instance": si.name, "output_status": "Published"},
			)
			self.assertEqual(count, 0)
		finally:
			self._delete_tender(tender)
