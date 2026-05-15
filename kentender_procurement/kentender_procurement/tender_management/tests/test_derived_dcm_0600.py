# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0600 — DCM pack §12 schema + Works BOQ price-source validation.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_dcm_0600
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.common.source_trace import (
	DERIVED_SOURCE_TRACE_MISSING,
	validate_derived_output_source_traces,
)
from kentender_procurement.tender_management.derived_models.dcm.schema import (
	DCM_MANUAL_PRICE_OVERRIDE_DENIED,
	DCM_SCHEMA_INVALID,
	build_dcm_stub_payload,
)
from kentender_procurement.tender_management.derived_models.dcm.validator import validate_dcm_source_traces
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


def _tr(sec: str) -> dict[str, str]:
	return {"source_type": "Section", "source_section_code": sec}


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


def _shell(**overrides) -> dict:
	base: dict = {
		"has_boq": False,
		"contract_documents": [
			{
				"document_code": "D1",
				"label": "GCC",
				"source_trace": _tr("VIII"),
			},
		],
		"contract_terms": [
			{
				"term_code": "T1",
				"label": "Term",
				"value": {"x": 1},
				"editable_in_contract": False,
				"source_trace": _tr("IX"),
			},
		],
		"price_source": {
			"source_type": "LumpSum",
			"manual_override_allowed": True,
		},
		"works_scope_references": {
			"specifications": ["VI"],
			"drawings": ["VII"],
			"boq": {},
		},
	}
	base.update(overrides)
	return base


class TestDerivedDcm0600(IntegrationTestCase):
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

	def test_derived_0600_valid_payload_passes(self) -> None:
		p = _shell()
		validate_dcm_source_traces(p)
		validate_derived_output_source_traces("DCM", p)

	def test_derived_0600_rejects_unknown_top_level_key(self) -> None:
		frappe.clear_messages()
		p = _shell()
		p["extra"] = 1
		with self.assertRaises(frappe.ValidationError):
			validate_dcm_source_traces(p)
		self.assertEqual(_last_msg_title(), DCM_SCHEMA_INVALID)

	def test_derived_0600_rejects_missing_term_trace(self) -> None:
		frappe.clear_messages()
		row = {
			"term_code": "T1",
			"label": "L",
			"value": {},
			"editable_in_contract": False,
		}
		p = _shell(contract_terms=[row])
		with self.assertRaises(frappe.ValidationError):
			validate_dcm_source_traces(p)
		self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)

	def test_derived_0600_rejects_prohibited_key(self) -> None:
		frappe.clear_messages()
		p = _shell()
		p["use_opening_price_as_contract"] = True
		with self.assertRaises(frappe.ValidationError):
			validate_dcm_source_traces(p)
		self.assertEqual(_last_msg_title(), DCM_SCHEMA_INVALID)

	def test_derived_0600_works_boq_rejects_manual_override(self) -> None:
		frappe.clear_messages()
		p = _shell(
			has_boq=True,
			price_source={
				"source_type": "CorrectedEvaluatedBOQTotal",
				"manual_override_allowed": True,
			},
		)
		with self.assertRaises(frappe.ValidationError):
			validate_dcm_source_traces(p)
		self.assertEqual(_last_msg_title(), DCM_MANUAL_PRICE_OVERRIDE_DENIED)

	def test_derived_0600_works_boq_requires_corrected_evaluated_total(self) -> None:
		frappe.clear_messages()
		p = _shell(
			has_boq=True,
			price_source={
				"source_type": "LumpSum",
				"manual_override_allowed": False,
			},
		)
		with self.assertRaises(frappe.ValidationError):
			validate_dcm_source_traces(p)
		self.assertEqual(_last_msg_title(), DCM_MANUAL_PRICE_OVERRIDE_DENIED)

	def test_derived_0600_dispatcher_empty_dict(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_derived_output_source_traces("DCM", {})
		self.assertEqual(_last_msg_title(), DCM_SCHEMA_INVALID)

	def test_derived_0600_generate_dcm_without_boq(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0600 DCM"
		doc.tender_reference = "DERIVED0600-DCM"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			row = StdInstanceGeneratedOutputService.generate_dcm(si.name)
			payload = row.content_json if isinstance(row.content_json, dict) else frappe.parse_json(row.content_json)
			validate_dcm_source_traces(payload)
			self.assertFalse(payload["has_boq"])
			self.assertEqual(payload["price_source"]["source_type"], "LumpSum")
			self.assertGreaterEqual(len(payload["contract_documents"]), 1)
			self.assertGreaterEqual(len(payload["contract_terms"]), 10)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0600_generate_dcm_with_boq(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0600 DCM BOQ"
		doc.tender_reference = "DERIVED0600-BOQ"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, _minimal_boq_payload())
			inst = frappe.get_doc("Tender STD Instance", si.name)
			payload = build_dcm_stub_payload(inst)
			validate_dcm_source_traces(payload)
			self.assertTrue(payload["has_boq"])
			self.assertEqual(payload["price_source"]["source_type"], "CorrectedEvaluatedBOQTotal")
			self.assertFalse(payload["price_source"]["manual_override_allowed"])
			# Pack §19 — Works+BOQ commercial summary (defaults when TDS omits explicit values).
			self.assertEqual(payload.get("completion_period_days"), 180)
			self.assertEqual(payload.get("defects_liability_period_days"), 365)
			self.assertEqual(payload.get("performance_security_percent"), 10)
			self.assertEqual(payload.get("retention_percent"), 5)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0600_rejects_invalid_completion_period_days_type(self) -> None:
		frappe.clear_messages()
		p = _shell(has_boq=True, completion_period_days=True)
		p["price_source"] = {
			"source_type": "CorrectedEvaluatedBOQTotal",
			"manual_override_allowed": False,
		}
		with self.assertRaises(frappe.ValidationError):
			validate_dcm_source_traces(p)
		self.assertEqual(_last_msg_title(), DCM_SCHEMA_INVALID)
