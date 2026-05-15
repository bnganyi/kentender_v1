# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0500 — DEM pack §11 schema + traceability validation.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_dem_0500
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.common.source_trace import (
	DERIVED_SOURCE_TRACE_MISSING,
	validate_derived_output_source_traces,
)
from kentender_procurement.tender_management.derived_models.dem.schema import (
	DEM_SCHEMA_INVALID,
	build_dem_stub_payload,
)
from kentender_procurement.tender_management.derived_models.dem.validator import (
	validate_dem_source_traces,
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


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


def _tr_section(code: str = "III") -> dict[str, str]:
	return {"source_type": "Section", "source_section_code": code}


def _rule(*, trace: dict[str, str], code: str = "R1") -> dict:
	return {
		"rule_code": code,
		"rule_type": "PresenceCheck",
		"label": "Rule label",
		"data_source": "DSM submission package",
		"failure_effect": "Reject",
		"source_trace": trace,
	}


def _stage(*, rules: list[dict], code: str = "S1", seq: int = 1, st: str = "Responsiveness") -> dict:
	return {
		"stage_code": code,
		"stage_name": "Stage name",
		"sequence": seq,
		"stage_type": st,
		"mandatory": True,
		"rules": rules,
	}


def _shell(**overrides) -> dict:
	tr = _tr_section()
	base: dict = {
		"evaluation_method": "LowestEvaluatedResponsiveBid",
		"stages": [_stage(rules=[_rule(trace=tr)])],
		"boq_arithmetic_correction": {
			"enabled": False,
			"stage_code": "DEM-STUB-FIN",
			"correction_rules": [],
		},
		"ranking": {"method": "LowestEvaluatedCost", "source_trace": tr},
	}
	base.update(overrides)
	return base


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


class TestDerivedDem0500(IntegrationTestCase):
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

	def test_derived_0500_valid_payload_passes(self) -> None:
		p = _shell()
		validate_dem_source_traces(p)
		validate_derived_output_source_traces("DEM", p)

	def test_derived_0500_system_rule_trace_requires_mapping_code(self) -> None:
		frappe.clear_messages()
		p = _shell(
			stages=[
				_stage(
					rules=[
						_rule(
							trace={"source_type": "SystemRule"},
							code="R-SYS",
						),
					],
				),
			],
		)
		with self.assertRaises(frappe.ValidationError):
			validate_dem_source_traces(p)
		self.assertEqual(_last_msg_title(), DEM_SCHEMA_INVALID)

	def test_derived_0500_system_rule_with_mapping_ok(self) -> None:
		p = _shell(
			stages=[
				_stage(
					rules=[
						_rule(
							trace={"source_type": "SystemRule", "mapping_code": "DEM_PACK_DEFAULT"},
							code="R-SYS",
						),
					],
				),
			],
		)
		validate_dem_source_traces(p)

	def test_derived_0500_rejects_unknown_top_level_key(self) -> None:
		frappe.clear_messages()
		p = _shell()
		p["extra_field"] = True
		with self.assertRaises(frappe.ValidationError):
			validate_dem_source_traces(p)
		self.assertEqual(_last_msg_title(), DEM_SCHEMA_INVALID)

	def test_derived_0500_rejects_missing_rule_trace(self) -> None:
		frappe.clear_messages()
		stage = _stage(rules=[_rule(trace=_tr_section())])
		stage["rules"][0].pop("source_trace")
		p = _shell(stages=[stage])
		with self.assertRaises(frappe.ValidationError):
			validate_dem_source_traces(p)
		self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)

	def test_derived_0500_rejects_prohibited_manual_criteria_key(self) -> None:
		frappe.clear_messages()
		p = _shell()
		p["manual_evaluation_criteria"] = [{"code": "X"}]
		with self.assertRaises(frappe.ValidationError):
			validate_dem_source_traces(p)
		self.assertEqual(_last_msg_title(), DEM_SCHEMA_INVALID)

	def test_derived_0500_rejects_boq_correction_enabled_without_rules(self) -> None:
		frappe.clear_messages()
		p = _shell(
			boq_arithmetic_correction={
				"enabled": True,
				"stage_code": "ARITH",
				"correction_rules": [],
			},
		)
		with self.assertRaises(frappe.ValidationError):
			validate_dem_source_traces(p)
		self.assertEqual(_last_msg_title(), DEM_SCHEMA_INVALID)

	def test_derived_0500_rejects_duplicate_stage_code(self) -> None:
		frappe.clear_messages()
		tr = _tr_section()
		p = _shell(
			stages=[
				_stage(rules=[_rule(trace=tr, code="A")], code="SAME", seq=1),
				_stage(rules=[_rule(trace=tr, code="B")], code="SAME", seq=2, st="Eligibility"),
			],
		)
		with self.assertRaises(frappe.ValidationError):
			validate_dem_source_traces(p)
		self.assertEqual(_last_msg_title(), DEM_SCHEMA_INVALID)

	def test_derived_0500_dispatcher_empty_dict(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_derived_output_source_traces("DEM", {})
		self.assertEqual(_last_msg_title(), DEM_SCHEMA_INVALID)

	def test_derived_0500_generate_dem_stub_without_boq(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0500 DEM"
		doc.tender_reference = "DERIVED0500-DEM"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			row = StdInstanceGeneratedOutputService.generate_dem(si.name)
			payload = row.content_json if isinstance(row.content_json, dict) else frappe.parse_json(row.content_json)
			validate_dem_source_traces(payload)
			self.assertFalse(payload["boq_arithmetic_correction"]["enabled"])
			self.assertEqual(payload["boq_arithmetic_correction"]["correction_rules"], [])
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0500_generate_dem_stub_with_boq(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0500 DEM BOQ"
		doc.tender_reference = "DERIVED0500-DEM-BOQ"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, _minimal_boq_payload())
			inst = frappe.get_doc("Tender STD Instance", si.name)
			payload = build_dem_stub_payload(inst)
			validate_dem_source_traces(payload)
			self.assertTrue(payload["boq_arithmetic_correction"]["enabled"])
			self.assertEqual(len(payload["boq_arithmetic_correction"]["correction_rules"]), 5)
		finally:
			self._cleanup_tender(doc.name)
