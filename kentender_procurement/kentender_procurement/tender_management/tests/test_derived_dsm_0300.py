# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0300 — DSM pack §9 schema validation.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_dsm_0300
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.common.source_trace import (
	validate_derived_output_source_traces,
)
from kentender_procurement.tender_management.derived_models.dsm.schema import (
	DSM_SCHEMA_INVALID,
	dsm_default_boq_rate_entry,
)
from kentender_procurement.tender_management.derived_models.dsm.validator import validate_dsm_source_traces
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


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


def _valid_req(*, code: str = "R1") -> dict:
	tr = {"source_type": "SystemRule"}
	return {
		"requirement_code": code,
		"requirement_type": "Form",
		"label": "Label",
		"mandatory": True,
		"supplier_action": "CompleteForm",
		"source_trace": tr,
	}


def _shell(**overrides) -> dict:
	base = {
		"requirements": [_valid_req()],
		"boq_rate_entry": dsm_default_boq_rate_entry(enabled=False),
		"addendum_acknowledgements": [],
	}
	base.update(overrides)
	return base


class TestDerivedDsm0300(IntegrationTestCase):
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
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def test_derived_0300_valid_payload_passes(self) -> None:
		validate_dsm_source_traces(_shell())
		validate_derived_output_source_traces("DSM", _shell())

	def test_derived_0300_rejects_unknown_top_level_key(self) -> None:
		frappe.clear_messages()
		p = _shell()
		p["not_allowed"] = True
		with self.assertRaises(frappe.ValidationError):
			validate_dsm_source_traces(p)
		self.assertEqual(_last_msg_title(), DSM_SCHEMA_INVALID)

	def test_derived_0300_rejects_missing_boq_rate_entry(self) -> None:
		frappe.clear_messages()
		p = {"requirements": [_valid_req()], "addendum_acknowledgements": []}
		with self.assertRaises(frappe.ValidationError):
			validate_dsm_source_traces(p)
		self.assertEqual(_last_msg_title(), DSM_SCHEMA_INVALID)

	def test_derived_0300_rejects_prohibited_ranking_key(self) -> None:
		frappe.clear_messages()
		p = _shell()
		p["ranking"] = {"method": "x"}
		with self.assertRaises(frappe.ValidationError):
			validate_dsm_source_traces(p)
		self.assertEqual(_last_msg_title(), DSM_SCHEMA_INVALID)

	def test_derived_0300_rejects_prohibited_nested_in_condition(self) -> None:
		frappe.clear_messages()
		req = _valid_req()
		req["condition"] = {"ranking": True}
		p = _shell(requirements=[req])
		with self.assertRaises(frappe.ValidationError):
			validate_dsm_source_traces(p)
		self.assertEqual(_last_msg_title(), DSM_SCHEMA_INVALID)

	def test_derived_0300_rejects_bad_boq_editable_fields(self) -> None:
		frappe.clear_messages()
		bqe = dsm_default_boq_rate_entry(enabled=True)
		bqe["editable_fields"] = ["rate", "quantity"]
		p = _shell(boq_rate_entry=bqe)
		with self.assertRaises(frappe.ValidationError):
			validate_dsm_source_traces(p)
		self.assertEqual(_last_msg_title(), DSM_SCHEMA_INVALID)

	def test_derived_0300_generate_dsm_stub_matches_schema(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0300 DSM"
		doc.tender_reference = "DERIVED0300-DSM"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			row = StdInstanceGeneratedOutputService.generate_dsm(si.name)
			raw = row.content_json
			payload = raw if isinstance(raw, dict) else frappe.parse_json(raw)
			validate_dsm_source_traces(payload)
		finally:
			self._cleanup_tender(doc.name)
