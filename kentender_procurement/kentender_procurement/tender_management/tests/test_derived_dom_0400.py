# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0400 — DOM pack §10 / std engine §8 schema validation.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_dom_0400
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.common.source_trace import (
	DERIVED_SOURCE_TRACE_MISSING,
	validate_derived_output_source_traces,
)
from kentender_procurement.tender_management.derived_models.dom.schema import (
	DOM_SCHEMA_INVALID,
	dom_canonical_prohibited_actions,
	dom_default_register_fields,
)
from kentender_procurement.tender_management.derived_models.dom.validator import validate_dom_source_traces
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


def _minimal_dom_shell(**overrides) -> dict:
	base = {
		"register_fields": dom_default_register_fields(),
		"prohibited_actions": dom_canonical_prohibited_actions(),
	}
	base.update(overrides)
	return base


class TestDerivedDom0400(IntegrationTestCase):
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
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def test_derived_0400_valid_minimal_passes(self) -> None:
		p = _minimal_dom_shell()
		validate_dom_source_traces(p)
		validate_derived_output_source_traces("DOM", p)

	def test_derived_0400_rejects_missing_prohibited_actions(self) -> None:
		frappe.clear_messages()
		p = {"register_fields": dom_default_register_fields()}
		with self.assertRaises(frappe.ValidationError):
			validate_dom_source_traces(p)
		self.assertEqual(_last_msg_title(), DOM_SCHEMA_INVALID)

	def test_derived_0400_rejects_bad_prohibited_actions_manifest(self) -> None:
		frappe.clear_messages()
		p = _minimal_dom_shell(prohibited_actions=["arithmetic_correction"])
		with self.assertRaises(frappe.ValidationError):
			validate_dom_source_traces(p)
		self.assertEqual(_last_msg_title(), DOM_SCHEMA_INVALID)

	def test_derived_0400_rejects_empty_register_fields(self) -> None:
		frappe.clear_messages()
		p = _minimal_dom_shell(register_fields=[])
		with self.assertRaises(frappe.ValidationError):
			validate_dom_source_traces(p)
		self.assertEqual(_last_msg_title(), DOM_SCHEMA_INVALID)

	def test_derived_0400_rejects_unknown_register_row_key(self) -> None:
		frappe.clear_messages()
		rows = list(dom_default_register_fields())
		rows[0] = {**rows[0], "extra": "x"}
		p = _minimal_dom_shell(register_fields=rows)
		with self.assertRaises(frappe.ValidationError):
			validate_dom_source_traces(p)
		self.assertEqual(_last_msg_title(), DOM_SCHEMA_INVALID)

	def test_derived_0400_rejects_prohibited_ranking_key(self) -> None:
		frappe.clear_messages()
		p = _minimal_dom_shell()
		p["ranking"] = {"method": "x"}
		with self.assertRaises(frappe.ValidationError):
			validate_dom_source_traces(p)
		self.assertEqual(_last_msg_title(), DOM_SCHEMA_INVALID)

	def test_derived_0400_rejects_missing_row_trace(self) -> None:
		frappe.clear_messages()
		rows = list(dom_default_register_fields())
		del rows[0]["source_trace"]
		p = _minimal_dom_shell(register_fields=rows)
		with self.assertRaises(frappe.ValidationError):
			validate_dom_source_traces(p)
		self.assertEqual(_last_msg_title(), DERIVED_SOURCE_TRACE_MISSING)

	def test_derived_0400_generate_dom_stub_matches_schema(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0400 DOM"
		doc.tender_reference = "DERIVED0400-DOM"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			row = StdInstanceGeneratedOutputService.generate_dom(si.name)
			raw = row.content_json
			payload = raw if isinstance(raw, dict) else frappe.parse_json(raw)
			validate_dom_source_traces(payload)
			codes = {r["field_code"] for r in payload["register_fields"]}
			self.assertIn("bidder_name", codes)
			self.assertIn("opening_timestamp", codes)
		finally:
			self._cleanup_tender(doc.name)
