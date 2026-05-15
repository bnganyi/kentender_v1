# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0200 — BundleGenerator and bundle trace validation.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_bundle_0200
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.bundle.generator import BundleGenerator
from kentender_procurement.tender_management.derived_models.bundle.schema import (
	BUNDLE_GENERATION_FAILED,
	BUNDLE_SECTION_CODES,
)
from kentender_procurement.tender_management.derived_models.bundle.validator import (
	validate_bundle_source_traces,
)
from kentender_procurement.tender_management.derived_models.common.source_trace import (
	DERIVED_SOURCE_TRACE_MISSING,
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
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.output_generation import (
	WorksOutputGenerationService,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


def _minimal_valid_boq_payload() -> dict:
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


class TestDerivedBundle0200(IntegrationTestCase):
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
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def test_derived_0200_generate_bundle_shape_and_traces(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0200 Bundle"
		doc.tender_reference = "DERIVED0200-BUNDLE"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			payload = BundleGenerator.generateBundle(si.name)
			self.assertEqual(payload.get("output_type"), "Bundle")
			self.assertEqual(payload.get("instance_code"), si.name)
			self.assertIn("document_outline", payload)
			self.assertIn("sections", payload)
			self.assertIn("attachments", payload)
			self.assertIn("placeholder_status", payload)
			self.assertEqual(len(payload["sections"]), len(BUNDLE_SECTION_CODES))
			for row in payload["sections"]:
				self.assertIn("source_trace", row)
				self.assertEqual(row["source_trace"].get("source_type"), "Section")
			validate_bundle_source_traces(payload)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0200_generate_bundle_invalid_instance(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			BundleGenerator.generateBundle("STDINST-NONEXISTENT-DERIVED0200")
		self.assertEqual(_last_msg_title(), BUNDLE_GENERATION_FAILED)

	def test_derived_0200_validator_rejects_missing_section_trace(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0200 Neg"
		doc.tender_reference = "DERIVED0200-NEG"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			payload = BundleGenerator.generateBundle(si.name)
			del payload["sections"][0]["source_trace"]
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				validate_bundle_source_traces(payload)
			self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0200_integration_generate_and_works_chain(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0200 Int"
		doc.tender_reference = "DERIVED0200-INT"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, _minimal_valid_boq_payload())
			b = StdInstanceGeneratedOutputService.generate_bundle(si.name)
			self.assertEqual(b.output_type, "Bundle")
			raw = b.content_json
			payload = raw if isinstance(raw, dict) else frappe.parse_json(raw)
			self.assertEqual(len(payload.get("sections") or []), len(BUNDLE_SECTION_CODES))

			out = WorksOutputGenerationService.generate_all_works_outputs(si.name)
			self.assertTrue(out.get("ok"))
			self.assertIn("Bundle", out.get("outputs") or {})
		finally:
			self._cleanup_tender(doc.name)
