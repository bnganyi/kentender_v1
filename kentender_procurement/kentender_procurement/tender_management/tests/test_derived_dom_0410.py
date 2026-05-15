# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0410 — ``DomGenerator.generateDOM``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_dom_0410
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.dom.generator import DomGenerator
from kentender_procurement.tender_management.derived_models.dom.schema import DOM_GENERATION_FAILED
from kentender_procurement.tender_management.derived_models.dom.validator import validate_dom_source_traces
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


def _append_parameter(instance_name: str, *, parameter_code: str, value: str, **extra: str) -> None:
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	row: dict = {
		"value_code": f"V-DOM41-{parameter_code.replace('.', '-')}",
		"parameter_code": parameter_code,
		"value": value,
		"value_status": "Provided",
		"source": "Officer Entry",
	}
	row.update(extra)
	doc.append("parameter_values", row)
	doc.save(ignore_permissions=True)


class TestDerivedDom0410(IntegrationTestCase):
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

	def test_derived_0410_generate_dom_validates(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0410 DOM"
		doc.tender_reference = "DERIVED0410-DOM"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			payload = DomGenerator.generateDOM(si.name)
			validate_dom_source_traces(payload)
			codes = {r["field_code"] for r in payload["register_fields"]}
			self.assertGreaterEqual(len(codes), 10)
			self.assertIn("bidder_name", codes)
			self.assertIn("opening_timestamp", codes)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0410_submitted_total_uses_boq_trace_when_boq_present(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0410 BOQ"
		doc.tender_reference = "DERIVED0410-BOQ"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, _minimal_boq_payload())
			payload = DomGenerator.generateDOM(si.name)
			row = next(r for r in payload["register_fields"] if r["field_code"] == "submitted_total_bid_price")
			self.assertEqual(row["source_trace"].get("source_type"), "BOQ")
			self.assertEqual(row["source_trace"].get("source_section_code"), "V")
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0410_addendum_marks_ack_field_mandatory(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0410 ADD"
		doc.tender_reference = "DERIVED0410-ADD"
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
				value="2026-06-01T12:00:00",
				source_addendum_code="ADD-DOM-0410",
			)
			payload = DomGenerator.generateDOM(si.name)
			row = next(
				r for r in payload["register_fields"] if r["field_code"] == "addendum_acknowledgement_present"
			)
			self.assertTrue(row["mandatory"])
			self.assertEqual(row["source_trace"].get("source_type"), "Addendum")
			self.assertEqual(row["source_trace"].get("source_addendum_code"), "ADD-DOM-0410")
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0410_opening_datetime_from_parameter(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0410 OPEN"
		doc.tender_reference = "DERIVED0410-OPEN"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			_append_parameter(si.name, parameter_code="DATES.OPENING_DATETIME", value="2026-06-02T14:00:00")
			payload = DomGenerator.generateDOM(si.name)
			self.assertEqual(payload.get("opening_datetime"), "2026-06-02T14:00:00")
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0410_invalid_instance(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			DomGenerator.generateDOM("STDINST-NONEXISTENT-DOM0410")
		self.assertEqual(_last_msg_title(), DOM_GENERATION_FAILED)
