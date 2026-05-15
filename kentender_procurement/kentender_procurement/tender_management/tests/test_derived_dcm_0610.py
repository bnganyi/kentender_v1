# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0610 — ``DcmGenerator.generateDCM``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_dcm_0610
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.dcm.generator import DcmGenerator
from kentender_procurement.tender_management.derived_models.dcm.schema import DCM_GENERATION_FAILED
from kentender_procurement.tender_management.derived_models.dcm.validator import validate_dcm_source_traces
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService


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


class TestDerivedDcm0610(IntegrationTestCase):
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

	def test_derived_0610_generate_validates_and_boq_price_source(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0610 DCM"
		doc.tender_reference = "DERIVED0610-DCM"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			from kentender_procurement.tender_management.works_completion.services.boq_completion import (
				WorksBoqCompletionService,
			)

			WorksBoqCompletionService.save_boq(si.name, _minimal_boq_payload())
			payload = DcmGenerator.generateDCM(si.name)
			validate_dcm_source_traces(payload)
			codes = {d["document_code"] for d in payload["contract_documents"]}
			self.assertIn("DCM-GCC", codes)
			self.assertIn("DCM-SCC", codes)
			self.assertIn("DCM-CONTRACT-FORMS", codes)
			scc = next(d for d in payload["contract_documents"] if d["document_code"] == "DCM-SCC")
			self.assertIn("carry-forward", (scc.get("description") or "").lower())
			self.assertEqual(payload["price_source"]["source_type"], "CorrectedEvaluatedBOQTotal")
			self.assertFalse(payload["price_source"]["manual_override_allowed"])
			title_term = next(t for t in payload["contract_terms"] if t["term_code"] == "DCM-TERM-TITLE")
			self.assertEqual(title_term["value"].get("title"), "DERIVED-0610 DCM")
			self.assertEqual(payload.get("completion_period_days"), 180)
			self.assertEqual(payload.get("defects_liability_period_days"), 365)
			self.assertEqual(payload.get("performance_security_percent"), 10)
			self.assertEqual(payload.get("retention_percent"), 5)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0610_addendum_document_when_addendum_codes(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0610 ADD"
		doc.tender_reference = "DERIVED0610-ADD"
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
					"value_code": "DCM0610-AD",
					"parameter_code": "DATES.SUBMISSION_DEADLINE",
					"value": "2026-07-01T12:00:00",
					"value_status": "Provided",
					"source": "Officer Entry",
					"source_addendum_code": "ADD-DCM-0610",
				},
			)
			inst.save(ignore_permissions=True)
			payload = DcmGenerator.generateDCM(si.name)
			validate_dcm_source_traces(payload)
			codes = {d["document_code"] for d in payload["contract_documents"]}
			self.assertIn("DCM-ADDENDA", codes)
			add_doc = next(d for d in payload["contract_documents"] if d["document_code"] == "DCM-ADDENDA")
			self.assertEqual(add_doc["source_trace"].get("source_addendum_code"), "ADD-DCM-0610")
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0610_invalid_instance(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			DcmGenerator.generateDCM("STDINST-NONEXISTENT-DCM0610")
		self.assertEqual(_last_msg_title(), DCM_GENERATION_FAILED)
