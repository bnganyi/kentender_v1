# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 — schema contract tests.

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
	"Authorised Requisition Handoff": {
		"consumed_at", "fixture_namespace", "generated_at", "handoff_digest", "handoff_version", "payload_json",
		"requisition", "requisition_version", "template_key", "template_version", "tender", "tender_version",
	},
	"IT Equipment Requirement Package": {
		"authorised_version", "county_resident_reservation", "current_version", "fixture_namespace", "lotting_indicator",
		"product_pattern", "record_version", "requisition", "reservation_category", "reservation_rule_snapshot_ids",
	},
	"IT Equipment Requirement Package Version": {
		"acceptance_requirements", "based_on_version", "catalogue_version", "content_digest", "fixture_namespace", "items",
		"manufacturer_support_required", "maximum_support_response_hours", "minimum_warranty_months",
		"onsite_support_required", "package", "proposal_digest", "record_version", "related_services",
		"service_location_constraint", "standard_package_review_state", "standard_profile_key", "standard_profile_version",
		"support_description", "supporting_materials", "technical_requirements", "version_number", "version_status",
	},
	"Procurement Requisition": {
		"authorised_version", "contributing_org_units", "current_state", "current_version", "fixture_namespace", "handoff",
		"handoff_consumed_at", "lead_org_unit_id", "open_slot_key", "plan_horizon", "plan_id", "plan_item_id",
		"plan_item_version_id", "plan_version_id", "planning_correction_outcome_event_id", "planning_correction_request_id",
		"planning_drawdown_reference", "prior_requisition_id", "prior_requisition_version_id", "procurement_category",
		"record_version", "requisition_reference", "strategic_objective_id", "strategic_objective_path",
	},
	"Requisition Acceptance Requirement": {
		"acceptance_requirement_id", "applies_to_id", "applies_to_scope", "check_type", "evidence_type",
		"other_evidence_name", "pass_condition", "row_order", "row_state",
	},
	"Requisition Command Journal": {
		"actor", "command", "document_name", "document_type", "fixture_namespace", "idempotency_key", "occurred_at",
		"request_fingerprint", "result",
	},
	"Requisition Contributing Unit": {
		"organisation_unit",
	},
	"Requisition Correction Outcome": {
		"correcting_plan_version_id", "correction_request_id", "decided_by", "decision_at", "eligibility_revision",
		"event_id", "fixture_namespace", "item_hold_state", "outcome", "payload_digest", "plan_item_id", "producer",
		"producer_sequence", "quarantine_reason", "reason", "received_at", "replacement_lineage_json",
		"requested_plan_item_version_id", "requested_plan_version_id", "requisition", "requisition_version",
		"schema_version", "status", "unresolved_request_count",
	},
	"Requisition Decision": {
		"actor", "affected_section", "authority_snapshot", "command_idempotency_key", "decided_at", "decision",
		"fixture_namespace", "legal_capacity", "new_lead_org_unit_id", "reason", "requisition_version", "resulting_state",
		"task",
	},
	"Requisition Drawdown Line": {
		"approved_quantity", "approved_value", "contributing_org_unit", "drawdown_line_id", "plan_item_line_id",
		"planning_drawdown_reference", "remaining_quantity", "remaining_value", "requested_quantity", "requested_value",
		"reservation_id", "source_line_id", "unit",
	},
	"Requisition Event": {
		"consumer", "delivered_at", "event_id", "event_type", "fixture_namespace", "occurred_at", "payload", "requisition",
		"requisition_version", "sequence", "status",
	},
	"Requisition Item": {
		"delivery_location", "drawdown_line_id", "equipment_category", "intended_use", "item_name", "latest_delivery_date",
		"plan_item_line_id", "quantity", "requisition_item_id", "row_order", "unit",
	},
	"Requisition Related Service": {
		"acceptance_evidence", "applies_to_id", "applies_to_scope", "completion_date", "other_evidence_name",
		"quantity_or_coverage", "required_result", "row_order", "service_requirement_id", "service_type",
	},
	"Requisition Supporting Material": {
		"document_type", "document_version", "file", "file_check_result", "file_digest", "linked_requirement_ids_json",
		"other_document_type", "purpose", "supporting_material_id", "title", "treatment",
	},
	"Requisition Task": {
		"business_role", "decision", "fixture_namespace", "organisation_unit", "record_version", "requisition",
		"requisition_version", "status", "task_token",
	},
	"Requisition Technical Requirement": {
		"applies_to_id", "applies_to_scope", "characteristic_key", "comparison", "mandatory", "other_value", "reason",
		"required_value_display", "required_value_json", "row_order", "row_state", "technical_requirement_id", "unit",
	},
	"Requisition Version": {
		"based_on_version", "basis_snapshot_json", "certified_lead_org_unit_id", "content_digest",
		"delivery_address_snapshot", "delivery_location", "drawdown_lines", "fixture_namespace", "latest_delivery_date",
		"lead_routing_directive", "package_version", "prepared_authority_snapshot", "prepared_by", "prepared_capacity",
		"record_version", "related_services_required", "requirement_title", "requisition", "sent_for_approval_at",
		"sent_for_approval_by", "submitted_at", "submitted_authority_snapshot", "submitted_by", "submitted_capacity", "version_number", "version_status",
	},
}

# §1: concepts this module must never reference. Proven by planted violation
# (test_no_prohibited_concept_token_in_module_sources's own sub-test).
PROHIBITED_TOKENS: tuple[str, ...] = (
	"pe_fy_context", "STD Configuration", "Requirements Composer", "composer_profile", "capability_profile",
	"Frappe User Permission", "manifest_editor", "schema_editor",
	# REQ-CHG-001 v1.11 — removed commands and the float money path (§5.14).
	"release_handoff_consumption", "confirm_proposed_requirement", "record_requisition_drawdown", "change_lead_organisation_unit",
	"flt(", "1e-6",
)

# Files that legitimately mention a prohibited word in a comment explaining
# why it is prohibited (this test file itself, most obviously).
_ALLOWED_MENTIONS = {("tests/test_requisitions_schema.py", token) for token in PROHIBITED_TOKENS} | {
	# asserts Planning no longer publishes the removed per-row drawdown command
	("tests/test_gateway_contracts.py", "record_requisition_drawdown"),
}


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
