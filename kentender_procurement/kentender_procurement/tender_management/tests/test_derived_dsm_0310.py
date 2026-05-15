# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0310 — ``DsmGenerator.generateDSM``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_dsm_0310
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.dsm.generator import DsmGenerator
from kentender_procurement.tender_management.derived_models.dsm.schema import DSM_GENERATION_FAILED
from kentender_procurement.tender_management.derived_models.dsm.validator import validate_dsm_source_traces
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.works_requirements_completion import (
	WorksRequirementsCompletionService,
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


def _append_parameter(
	instance_name: str,
	*,
	parameter_code: str,
	value: str,
	source_addendum_code: str | None = None,
) -> None:
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	row: dict = {
		"value_code": f"V-TEST-{parameter_code.replace('.', '-')}",
		"parameter_code": parameter_code,
		"value": value,
		"value_status": "Provided",
		"source": "Officer Entry",
	}
	if source_addendum_code:
		row["source_addendum_code"] = source_addendum_code
	doc.append("parameter_values", row)
	doc.save(ignore_permissions=True)


class TestDerivedDsm0310(IntegrationTestCase):
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

	def test_derived_0310_generate_dsm_validates_and_includes_core_requirements(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0310 DSM"
		doc.tender_reference = "DERIVED0310-DSM"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			payload = DsmGenerator.generateDSM(si.name)
			validate_dsm_source_traces(payload)
			codes = {r["requirement_code"] for r in payload["requirements"]}
			self.assertIn("DSM-FORE-001", codes)
			self.assertTrue({"DSM-QUAL-NCA", "DSM-QUAL-TAX", "DSM-QUAL-BO"}.issubset(codes))
			self.assertFalse(payload["boq_rate_entry"]["enabled"])
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0310_boq_enables_rate_entry_and_requirement(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0310 BOQ"
		doc.tender_reference = "DERIVED0310-BOQ"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, _minimal_boq_payload())
			payload = DsmGenerator.generateDSM(si.name)
			validate_dsm_source_traces(payload)
			self.assertTrue(payload["boq_rate_entry"]["enabled"])
			codes = {r["requirement_code"] for r in payload["requirements"]}
			self.assertIn("DSM-BOQ-RATES", codes)
			boq_req = next(r for r in payload["requirements"] if r["requirement_code"] == "DSM-BOQ-RATES")
			self.assertEqual(boq_req["requirement_type"], "BOQRateEntry")
			self.assertEqual(boq_req["supplier_action"], "EnterRates")
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0310_tender_security_parameter_adds_requirement(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0310 SEC"
		doc.tender_reference = "DERIVED0310-SEC"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			_append_parameter(si.name, parameter_code="SECURITY.TENDER_SECURITY_MODE", value="TENDER_SECURITY")
			payload = DsmGenerator.generateDSM(si.name)
			codes = {r["requirement_code"] for r in payload["requirements"]}
			self.assertIn("DSM-SEC-001", codes)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0310_method_statement_flag_adds_requirement(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0310 METH"
		doc.tender_reference = "DERIVED0310-METH"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksRequirementsCompletionService.save_works_requirements(
				si.name,
				{
					"specifications": {"structured_summary": "Outpatient block renovation scope."},
					"method_statement_required": True,
				},
			)
			payload = DsmGenerator.generateDSM(si.name)
			codes = {r["requirement_code"] for r in payload["requirements"]}
			self.assertIn("DSM-WR-METHOD_STATEMENT", codes)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0310_addendum_codes_surface_in_acknowledgements(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0310 ADD"
		doc.tender_reference = "DERIVED0310-ADD"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			_append_parameter(
				si.name,
				parameter_code="DATES.SUBMISSION_DEADLINE",
				value="2026-12-31T17:00:00",
				source_addendum_code="ADD-0310-A",
			)
			payload = DsmGenerator.generateDSM(si.name)
			acks = payload.get("addendum_acknowledgements") or []
			self.assertEqual(acks, [{"addendum_code": "ADD-0310-A", "mandatory": True}])
			self.assertIn("submission_deadline", payload)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0310_invalid_instance_code(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			DsmGenerator.generateDSM("STDINST-NONEXISTENT-0310")
		self.assertEqual(_last_msg_title(), DSM_GENERATION_FAILED)
