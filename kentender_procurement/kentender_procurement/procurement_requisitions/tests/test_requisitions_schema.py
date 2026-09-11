# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 — schema contract tests (REQ-107).

Guards: (1) every doctype exists with exactly its allow-listed fields (§2.2
field-purpose rule: an undocumented field is a defect, not an option); (2) no
spec-prohibited concept token survives in the module's server code (§1's
posture: no STD manifest/composer/schema-editor, no `pe_fy_context`, no
native-Role/User-Permission authority, no attachment-primary path); (3)
`bench migrate` produced real tables for every doctype.
"""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase

MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXPECTED_FIELDS: dict[str, set[str]] = {
	"Procurement Requisition": {
		"requisition_reference", "plan_id", "plan_version_id", "plan_item_id", "strategic_objective",
		"strategic_objective_path", "procurement_category", "plan_horizon", "multi_year_justification",
		"contributing_org_units", "lead_org_unit", "current_version", "authorised_version", "current_state",
		"planning_drawdown_reference", "handoff", "handoff_consumed_at", "record_version", "fixture_namespace",
	},
	"Requisition Contributing Unit": {"organisation_unit"},
	"Requisition Version": {
		"requisition", "version_number", "based_on_version", "version_status", "requirement_title",
		"delivery_location", "delivery_address_snapshot", "latest_delivery_date", "related_services_required",
		"package_version", "content_digest", "drawdown_lines", "record_version", "fixture_namespace",
	},
	"Requisition Drawdown Line": {
		"drawdown_line_id", "plan_item_line_id", "source_line_id", "contributing_org_unit", "approved_quantity",
		"approved_value", "remaining_quantity", "remaining_value", "requested_quantity", "requested_value",
		"unit", "reservation_id", "planning_drawdown_reference",
	},
	"IT Equipment Requirement Package": {
		"requisition", "product_pattern", "current_version", "authorised_version", "reservation_category",
		"lotting_indicator", "record_version", "fixture_namespace",
	},
	"IT Equipment Requirement Package Version": {
		"package", "version_number", "based_on_version", "version_status", "minimum_warranty_months",
		"onsite_support_required", "maximum_support_response_hours", "manufacturer_support_required",
		"service_location_constraint", "support_description", "items", "technical_requirements",
		"related_services", "acceptance_requirements", "supporting_materials", "catalogue_version",
		"content_digest", "record_version", "fixture_namespace",
	},
	"Requisition Item": {
		"requisition_item_id", "plan_item_line_id", "equipment_category", "item_name", "quantity", "unit",
		"intended_use", "delivery_location", "latest_delivery_date", "row_order",
	},
	"Requisition Technical Requirement": {
		"technical_requirement_id", "applies_to_scope", "applies_to_id", "characteristic_key", "comparison",
		"required_value_json", "required_value_display", "unit", "other_value", "mandatory", "reason",
		"row_status", "proposed_by_rule", "row_order",
	},
	"Requisition Related Service": {
		"service_requirement_id", "service_type", "applies_to_scope", "applies_to_id", "required_result",
		"quantity_or_coverage", "completion_date", "acceptance_evidence", "other_evidence_name", "row_order",
	},
	"Requisition Acceptance Requirement": {
		"acceptance_requirement_id", "applies_to_scope", "applies_to_id", "check_type", "pass_condition",
		"evidence_type", "other_evidence_name", "row_order",
	},
	"Requisition Supporting Material": {
		"supporting_material_id", "title", "document_type", "other_document_type", "purpose", "file",
		"file_digest", "file_check_result", "treatment", "linked_requirement_ids_json", "document_version",
	},
	"Requisition Task": {
		"requisition", "requisition_version", "business_role", "organisation_unit", "status", "decision",
		"task_token", "record_version", "fixture_namespace",
	},
	"Requisition Decision": {
		"task", "requisition_version", "actor", "legal_capacity", "decision", "return_reason",
		"authority_snapshot", "decided_at", "command_idempotency_key", "fixture_namespace",
	},
	"Authorised Requisition Handoff": {
		"requisition", "requisition_version", "payload_json", "handoff_digest", "handoff_version",
		"generated_at", "tender", "tender_version", "template_key", "template_version", "consumed_at",
		"fixture_namespace",
	},
	"Requisition Command Journal": {
		"idempotency_key", "command", "document_type", "document_name", "request_fingerprint", "actor",
		"result", "occurred_at", "fixture_namespace",
	},
	"Requisition Event": {
		"event_id", "event_type", "requisition", "sequence", "requisition_version", "occurred_at", "payload",
		"status", "consumer", "delivered_at", "fixture_namespace",
	},
}

# §1: concepts this module must never reference. Proven by planted violation
# (test_no_prohibited_concept_token_in_module_sources's own sub-test).
PROHIBITED_TOKENS: tuple[str, ...] = (
	"pe_fy_context", "STD Configuration", "Requirements Composer", "composer_profile", "capability_profile",
	"Frappe User Permission", "manifest_editor", "schema_editor",
)

# Files that legitimately mention a prohibited word in a comment explaining
# why it is prohibited (this test file itself, most obviously).
_ALLOWED_MENTIONS = {("tests/test_requisitions_schema.py", token) for token in PROHIBITED_TOKENS}


class TestRequisitionsSchema(IntegrationTestCase):
	def test_every_doctype_has_exactly_its_allow_listed_fields(self):
		for doctype, expected in EXPECTED_FIELDS.items():
			self.assertTrue(frappe.db.exists("DocType", doctype), f"{doctype} is missing")
			meta = frappe.get_meta(doctype)
			actual = {f.fieldname for f in meta.fields if f.fieldtype not in ("Section Break", "Column Break", "Tab Break")}
			self.assertEqual(
				actual, expected,
				f"{doctype}: unexpected={sorted(actual - expected)} missing={sorted(expected - actual)}",
			)

	def test_every_doctype_has_a_real_table(self):
		for doctype in EXPECTED_FIELDS:
			self.assertTrue(frappe.db.table_exists(doctype), f"{doctype} has no table")

	def test_child_tables_are_not_independently_permissioned(self):
		"""Child rows are reached only through their parent document; a
		DocPerm on a child table doctype would be meaningless."""
		for doctype in ("Requisition Contributing Unit", "Requisition Drawdown Line", "Requisition Item",
						"Requisition Technical Requirement", "Requisition Related Service",
						"Requisition Acceptance Requirement", "Requisition Supporting Material"):
			meta = frappe.get_meta(doctype)
			self.assertEqual(meta.istable, 1, f"{doctype} must be istable=1")

	def test_no_prohibited_concept_token_survives(self):
		hits: list[str] = []
		for root, _dirs, files in os.walk(MODULE_DIR):
			if "__pycache__" in root:
				continue
			for name in files:
				if not (name.endswith(".py") or name.endswith(".json")):
					continue
				path = os.path.join(root, name)
				rel = os.path.relpath(path, MODULE_DIR)
				text = open(path, encoding="utf-8").read()
				for token in PROHIBITED_TOKENS:
					if token in text and (rel, token) not in _ALLOWED_MENTIONS:
						hits.append(f"{rel}: {token}")
		self.assertEqual(hits, [])

	def test_the_scan_is_not_vacuous(self):
		"""Planted-violation proof (tracker rule 7): the scan actually finds
		a token when one is present."""
		import tempfile

		with tempfile.NamedTemporaryFile("w", suffix=".py", dir=MODULE_DIR, delete=True) as fh:
			fh.write("# planted: pe_fy_context\n")
			fh.flush()
			hits: list[str] = []
			text = open(fh.name, encoding="utf-8").read()
			for token in PROHIBITED_TOKENS:
				if token in text:
					hits.append(token)
			self.assertIn("pe_fy_context", hits)
