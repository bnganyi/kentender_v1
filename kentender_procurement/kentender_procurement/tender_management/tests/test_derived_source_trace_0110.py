# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0110 — source trace schema and validation.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_source_trace_0110
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.common.source_trace import (
	DERIVED_SOURCE_TRACE_MISSING,
	SOURCE_TRACE_TYPES,
	validate_derived_output_source_traces,
	validate_source_trace,
)
from kentender_procurement.tender_management.derived_models.dsm.schema import (
	DSM_SCHEMA_INVALID,
	dsm_default_boq_rate_entry,
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
from kentender_procurement.tender_management.works_completion.services.output_generation import (
	WorksOutputGenerationService,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


def _content_json_as_dict(content_json: Any) -> dict[str, Any]:
	if isinstance(content_json, dict):
		return content_json
	if isinstance(content_json, str):
		return json.loads(content_json)
	raise AssertionError(f"unexpected content_json type: {type(content_json)}")


class TestDerivedSourceTrace0110(IntegrationTestCase):
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

	def test_derived_0110_source_trace_types_match_pack(self) -> None:
		expected = {
			"Section",
			"Clause",
			"Parameter",
			"Form",
			"BOQ",
			"WorksRequirement",
			"Drawing",
			"Attachment",
			"EvaluationResult",
			"Addendum",
			"SystemRule",
		}
		self.assertEqual(set(SOURCE_TRACE_TYPES), expected)

	def test_derived_0110_validate_source_trace_system_rule_ok(self) -> None:
		out = validate_source_trace({"source_type": "SystemRule"})
		self.assertEqual(out["source_type"], "SystemRule")

	def test_derived_0110_validate_source_trace_optional_string_fields(self) -> None:
		out = validate_source_trace(
			{
				"source_type": "Parameter",
				"source_parameter_code": "P-X",
				"source_section_code": "",
			},
		)
		self.assertEqual(out["source_parameter_code"], "P-X")

	def test_derived_0110_validate_source_trace_rejects_not_mapping(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_source_trace([])
		self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)

	def test_derived_0110_validate_source_trace_rejects_missing_source_type(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_source_trace({})
		self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)

	def test_derived_0110_validate_source_trace_rejects_unknown_source_type(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_source_trace({"source_type": "NotInPack"})
		self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)

	def test_derived_0110_validate_source_trace_rejects_unknown_key(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_source_trace({"source_type": "SystemRule", "extra": "x"})
		self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)

	def test_derived_0110_validate_source_trace_rejects_non_string_optional(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_source_trace({"source_type": "Clause", "source_clause_code": 1})
		self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)

	def test_derived_0110_dispatcher_bundle_requires_dict(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_derived_output_source_traces("Bundle", "not-a-dict")
		self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)

	def test_derived_0110_dispatcher_dsm_requires_requirements(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_derived_output_source_traces("DSM", {})
		self.assertEqual(_last_msg_title(), DSM_SCHEMA_INVALID)

	def test_derived_0110_dispatcher_dsm_row_missing_trace(self) -> None:
		frappe.clear_messages()
		payload = {
			"requirements": [
				{
					"requirement_code": "x",
					"requirement_type": "Form",
					"label": "L",
					"mandatory": True,
					"supplier_action": "CompleteForm",
				},
			],
			"boq_rate_entry": dsm_default_boq_rate_entry(enabled=False),
			"addendum_acknowledgements": [],
		}
		with self.assertRaises(frappe.ValidationError):
			validate_derived_output_source_traces("DSM", payload)
		self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)

	def test_derived_0110_dispatcher_rejects_non_object_content(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_derived_output_source_traces("DOM", [])
		self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)

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

	def test_derived_0110_generate_dsm_and_full_chain_succeeds(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0110 Test Tender"
		doc.tender_reference = "DERIVED0110-TRACE"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			dsm = StdInstanceGeneratedOutputService.generate_dsm(si.name)
			dsm_payload = _content_json_as_dict(dsm.content_json)
			self.assertIn("requirements", dsm_payload)
			self.assertIn("source_trace", dsm_payload["requirements"][0])

			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			out = WorksOutputGenerationService.generate_all_works_outputs(si.name)
			self.assertTrue(out.get("ok"))
			self.assertEqual(set((out.get("outputs") or {}).keys()), set(OUTPUT_TYPES))
			for label in ("DSM", "DOM", "DEM", "DCM"):
				row = frappe.get_doc("Tender STD Generated Output", out["outputs"][label])
				payload = _content_json_as_dict(row.content_json)
				validate_derived_output_source_traces(label, payload)
		finally:
			for name in frappe.get_all(
				"Tender STD Instance",
				filters={"tm2_tender": doc.name},
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
			frappe.delete_doc("Procurement Tender", doc.name, force=True, ignore_permissions=True)
