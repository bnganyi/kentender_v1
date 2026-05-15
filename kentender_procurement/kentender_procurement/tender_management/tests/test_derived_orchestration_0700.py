# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0700 — ``DerivedModelGenerationService``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_orchestration_0700
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.dom.generator import DomGenerator
from kentender_procurement.tender_management.derived_models.orchestration import (
	DerivedModelGenerationService,
)
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
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)


class TestDerivedOrchestration0700(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
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
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

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

	def test_derived_0700_generate_all_current_without_publish(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0700 All Current"
		doc.tender_reference = "DERIVED0700-CUR"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			out = DerivedModelGenerationService.generate_all(si.name, publish=False)
			self.assertTrue(out.get("ok"))
			self.assertFalse(out.get("published"))
			outputs = out.get("outputs") or {}
			self.assertEqual(set(outputs.keys()), set(OUTPUT_TYPES))

			inst = frappe.get_doc("Tender STD Instance", si.name)
			self.assertFalse((inst.current_bundle_output_code or "").strip())

			for label, name in outputs.items():
				row = frappe.get_doc("Tender STD Generated Output", name)
				self.assertEqual(row.output_type, label)
				self.assertEqual(row.output_status, "Current")
				DerivedModelGenerationService.validate_generated_output(name)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0700_partial_failure_marks_failed_and_preserves_prior_current(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0700 Partial"
		doc.tender_reference = "DERIVED0700-PART"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())

			def _boom(_instance_name: str):
				raise RuntimeError("simulated DOM failure")

			with patch.object(DomGenerator, "generateDOM", side_effect=_boom):
				with self.assertRaises(RuntimeError):
					DerivedModelGenerationService.generate_all(si.name, publish=False)

			bundle_rows = frappe.get_all(
				"Tender STD Generated Output",
				filters={"tender_std_instance": si.name, "output_type": "Bundle", "output_status": "Current"},
				pluck="name",
			)
			self.assertEqual(len(bundle_rows), 1)
			dsm_rows = frappe.get_all(
				"Tender STD Generated Output",
				filters={"tender_std_instance": si.name, "output_type": "DSM", "output_status": "Current"},
				pluck="name",
			)
			self.assertEqual(len(dsm_rows), 1)

			failed_dom = frappe.get_all(
				"Tender STD Generated Output",
				filters={"tender_std_instance": si.name, "output_type": "DOM", "output_status": "Failed"},
				pluck="name",
			)
			self.assertEqual(len(failed_dom), 1)

			self.assertEqual(
				frappe.db.count("Tender STD Generated Output", {"tender_std_instance": si.name, "output_type": "DEM"}),
				0,
			)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0700_validate_generated_output_rejects_empty_payload(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0700 Validate"
		doc.tender_reference = "DERIVED0700-VAL"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			row = StdInstanceGeneratedOutputService.insert_failed_output_row(si.name, "Bundle")
			with self.assertRaises(frappe.ValidationError):
				DerivedModelGenerationService.validate_generated_output(row.name)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0700_generated_by_job_from_actor_or_job(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0700 Job"
		doc.tender_reference = "DERIVED0700-JOB"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			job = "ORCH-JOB-0700-XYZ"
			self.assertFalse(frappe.db.exists("User", job))
			out = DerivedModelGenerationService.generate_output(
				si.name,
				"Bundle",
				actor_or_job=job,
				publish=False,
			)
			name = (out.get("outputs") or {}).get("Bundle")
			self.assertTrue(name)
			row = frappe.get_doc("Tender STD Generated Output", name)
			self.assertEqual((row.generated_by_job_code or "").strip(), job)
		finally:
			self._cleanup_tender(doc.name)
