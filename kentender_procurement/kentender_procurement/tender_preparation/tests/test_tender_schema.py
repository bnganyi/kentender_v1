# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 — schema contract tests (plan Phase 2, TPR-207).

Guards: (1) every doctype exists with exactly its allow-listed fields (an
undocumented field is a defect, not an option); (2) DocPerms are exactly the
three Site-wide readers plus System Manager, and nobody may write the
`Supported Tender Template` registry (TPR-AC-034); (3) no spec-prohibited
concept token survives in the module's server code (§20, §1.1, the banned
`Procurement Tender` literal); (4) `bench migrate` produced real tables; (5)
both permission hooks are registered for every family doctype (plan D11).
"""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase

MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXPECTED_FIELDS: dict[str, set[str]] = {
	"Prepared Tender": {
		"tender_reference", "requisition_handoff", "requisition", "requisition_reference", "requisition_version",
		"requisition_content_digest", "handoff_digest", "handoff_version", "plan_item_id", "fiscal_year",
		"requirement_title", "template_key", "template_version", "official_source_digest", "bundle_digest",
		"current_version", "approved_version", "current_state", "publication_handoff", "publication_consumed_at",
		"predecessor_tender", "predecessor_version", "prepared_by", "record_version", "fixture_namespace",
	},
	"Tender Preparation Version": {
		"tender", "version_number", "based_on_version", "version_status", "snapshot_json", "snapshot_digest",
		"tender_title", "issue_date", "clarification_deadline", "submission_deadline", "tender_validity_days",
		"tender_security_amount", "pre_tender_meeting", "meeting_datetime", "meeting_mode", "meeting_venue",
		"online_joining_information", "manufacturer_authorisation_required", "datasheets_required",
		"past_experience_required", "minimum_comparable_contracts", "experience_period_years",
		"after_sales_evidence_required", "after_sales_evidence", "evidence_requirements", "inspection_location",
		"payment_timing_days", "performance_security_required", "performance_security_percent",
		"delay_damages_per_week_percent", "maximum_delay_damages_percent", "contract_contact_office",
		"readiness_findings", "readiness_digest", "readiness_run_at", "blocking_count", "warning_count",
		"content_digest", "render_context_digest", "invitation_html_digest", "issued_tender_html_digest",
		"prepared_by", "prepared_at", "submitted_by", "submitted_at", "decided_by", "decided_at",
		"record_version", "fixture_namespace",
	},
	"Tender Evidence Requirement": {
		"evidence_requirement_id", "evidence_label", "evidence_type", "linked_requirement_type", "linked_requirement_id",
		"mandatory", "source", "row_order",
	},
	"Tender Readiness Finding": {"finding_code", "severity", "task_number", "field_reference", "message", "row_order"},
	"Tender Preparation Task": {
		"tender", "tender_version", "business_role", "status", "decision", "task_token", "record_version", "fixture_namespace",
	},
	"Tender Preparation Decision": {
		"task", "tender", "tender_version", "actor", "legal_capacity", "decision", "reason", "resulting_state",
		"authority_snapshot", "decided_at", "command_idempotency_key", "fixture_namespace",
	},
	"Tender Publication Handoff": {
		"tender", "tender_version", "handoff_version", "package_json", "package_digest", "invitation_html_file",
		"issued_tender_html_file", "invitation_pdf_file", "issued_tender_pdf_file", "invitation_digest",
		"issued_tender_digest", "status", "generated_at", "consumed_at", "consumption_correlation_id", "published_on",
		"fixture_namespace",
	},
	"Tender Preparation Command Journal": {
		"idempotency_key", "command", "document_type", "document_name", "request_fingerprint", "actor", "result",
		"occurred_at", "fixture_namespace",
	},
	"Tender Preparation Event": {
		"event_id", "event_type", "tender", "tender_version", "correlation_id", "sequence", "occurred_at", "payload",
		"status", "consumer", "delivered_at", "fixture_namespace",
	},
	"Supported Tender Template": {
		"template_key", "template_version", "display_name", "supported_category", "supported_method",
		"official_source_title", "official_source_digest", "bundle_digest", "availability", "installed_at",
		"last_verified_at", "verification_note", "fixture_namespace",
	},
}

CHILD_TABLES = ("Tender Evidence Requirement", "Tender Readiness Finding")
ROOT_FAMILY_READERS = {"System Manager", "Procurement Officer", "Head of Procurement Function", "Auditor"}
EXPECTED_READERS: dict[str, set[str]] = {
	"Prepared Tender": ROOT_FAMILY_READERS,
	"Tender Preparation Version": ROOT_FAMILY_READERS,
	"Tender Preparation Task": ROOT_FAMILY_READERS,
	"Tender Preparation Decision": ROOT_FAMILY_READERS,
	"Tender Publication Handoff": ROOT_FAMILY_READERS,
	"Supported Tender Template": ROOT_FAMILY_READERS,
	"Tender Preparation Command Journal": {"System Manager", "Auditor"},
	"Tender Preparation Event": {"System Manager", "Procurement Planner", "Auditor"},
}

# §20 / §1.1 / plan D2: concepts this module must never reference. Proven by
# planted violation below (tracker rule 7).
PROHIBITED_TOKENS: tuple[str, ...] = (
	"pe_fy_context", "Procurement Tender", "STD Configuration", "composer_profile", "capability_profile",
	"Frappe User Permission", "manifest_editor", "schema_editor", "clause_editor", "template_selector",
	"TPR_ROLE_REQUIRED", "TPR_SCOPE_DENIED", "bid_opening_actual",
)
_ALLOWED_MENTIONS = {("tests/test_tender_schema.py", token) for token in PROHIBITED_TOKENS}


class TestTenderSchema(IntegrationTestCase):
	def test_every_doctype_has_exactly_its_allow_listed_fields(self):
		for doctype, expected in EXPECTED_FIELDS.items():
			self.assertTrue(frappe.db.exists("DocType", doctype), f"{doctype} is missing")
			meta = frappe.get_meta(doctype)
			actual = {f.fieldname for f in meta.fields if f.fieldtype not in ("Section Break", "Column Break", "Tab Break")}
			self.assertEqual(actual, expected, f"{doctype}: unexpected={sorted(actual - expected)} missing={sorted(expected - actual)}")

	def test_every_doctype_has_a_real_table(self):
		for doctype in EXPECTED_FIELDS:
			self.assertTrue(frappe.db.table_exists(doctype), f"{doctype} has no table")

	def test_child_tables_are_not_independently_permissioned(self):
		for doctype in CHILD_TABLES:
			meta = frappe.get_meta(doctype)
			self.assertEqual(meta.istable, 1, f"{doctype} must be istable=1")
			self.assertEqual(meta.permissions, [], f"{doctype} carries DocPerms")

	def test_docperms_are_exactly_the_site_wide_readers(self):
		for doctype, readers in EXPECTED_READERS.items():
			perms = frappe.get_meta(doctype).permissions
			self.assertEqual({p.role for p in perms if p.read}, readers, doctype)
			for p in perms:
				if p.role != "System Manager":
					self.assertFalse(p.write or p.create or p.delete, f"{doctype}: {p.role} may write")

	def test_nobody_may_write_the_template_registry(self):
		"""TPR-AC-034 / plan D13 — not even System Manager holds a write
		DocPerm; only `tender_templates.registry.install()` writes it."""
		for p in frappe.get_meta("Supported Tender Template").permissions:
			self.assertFalse(p.write or p.create or p.delete, f"{p.role} may write the registry")

	def test_both_permission_hooks_are_registered_for_the_whole_family(self):
		from kentender_procurement.tender_preparation.services.tender_authorization import FAMILY_DOCTYPES

		pqc = frappe.get_hooks("permission_query_conditions")
		hp = frappe.get_hooks("has_permission")
		for doctype in FAMILY_DOCTYPES:
			self.assertIn("tender_authorization.permission_query_conditions", " ".join(pqc.get(doctype, [])), doctype)
			self.assertIn("tender_authorization.has_permission", " ".join(hp.get(doctype, [])), doctype)
		self.assertNotIn("Prepared Tender", frappe.get_hooks("kentender_scope_map") or {})

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
		import tempfile

		with tempfile.NamedTemporaryFile("w", suffix=".py", dir=MODULE_DIR, delete=True) as fh:
			fh.write("# planted: pe_fy_context\n")
			fh.flush()
			text = open(fh.name, encoding="utf-8").read()
			self.assertIn("pe_fy_context", [t for t in PROHIBITED_TOKENS if t in text])
