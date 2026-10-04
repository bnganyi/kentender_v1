# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 — schema contract tests (v0.8 tracker TND-207; v0.12 TND12-102..104).

Guards: (1) every doctype exists with exactly its allow-listed fields (§4 —
an undocumented field is a defect, not an option); (2) no spec-prohibited
concept token survives in the module's server code (§16 prohibited
shortcuts, tracker rule 3); (3) `bench migrate` produced real tables; (4)
DocPerms are exactly the §6 readers and no role can write the installed STD
release registry; (5) the error contract is exactly the thirty-five v0.12 §8
codes.
"""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tenders.services import errors

MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AUDIT = {"record_version", "fixture_namespace"}
EXPECTED_FIELDS: dict[str, set[str]] = {
	"Tender": {
		"tender_reference", "requirement_title", "requisition_handoff", "requisition", "requisition_reference", "requisition_version",
		"plan_item_id", "plan_item_version_id", "fiscal_year", "lead_org_unit", "contributing_org_unit_ids", "product_key",
		"template_release_id", "template_key", "template_release", "product_profile_id", "renderer_profile_id", "supported_renderer_version",
		"official_source_digest", "bundle_digest", "response_rules_digest", "downstream_rules_digest", "addendum_identity_rules_digest",
		"current_version", "approved_version", "overall_status",
		"publication", "published_at", "submission_deadline", "clarification_deadline", "cancellation", "submission_handoff", *AUDIT,
	},
	"Tender Version": {
		"tender", "version_number", "status", "predecessor_version", "requisition_handoff", "requisition_version", "template_release_id",
		"template_key", "template_release", "product_profile_id", "renderer_profile_id", "supported_renderer_version", "official_source_digest", "bundle_digest",
		"response_rules_digest", "downstream_rules_digest", "addendum_identity_rules_digest", "requisition_snapshot_digest", "requisition_snapshot_json", "officer_payload_json",
		"evidence_requirements", "review_findings", "review_result_digest", "invitation_digest", "issued_tender_digest",
		"response_schema_digest", "evaluation_contract_digest", "contract_projection_digest", "package_digest", "prepared_by",
		"prepared_at", "submitted_by", "submitted_at", "approved_by", "approved_at", "returned_by", "returned_at", "return_reason",
		"return_affected_task", "reopen_reason", "stopped_by", "stopped_at", "stop_reason", *AUDIT,
	},
	"Tender Evidence Requirement": {"evidence_requirement_id", "label", "evidence_type", "linked_requirement_type", "linked_requirement_id", "mandatory", "row_order"},
	"Tender Review Finding": {"finding_code", "severity", "message", "task", "field", "route"},
	"Tender Decision": {
		"tender", "tender_version", "decision", "subject_type", "subject_id", "actor", "business_role", "reason", "affected_task",
		"authority_snapshot", "decided_at", "command_idempotency_key", "fixture_namespace",
	},
	"Tender Task": {"tender", "tender_version", "task_type", "business_role", "holder", "sender", "comment", "subject_type", "subject_id", "status", "decision", "task_token", *AUDIT},
	"Tender Publication": {
		"tender", "tender_version", "package_digest", "bid_definition", "bid_definition_id", "definition_version", "definition_digest",
		"response_schema_digest", "evaluation_contract_digest", "contract_projection_digest", "authorised_by", "authorised_at", "rule_snapshot_id", "rule_snapshot_json",
		"threshold_snapshot_json", "required_channels_json", "minimum_preparation_days", "publication_status", "published_at",
		"publication_digest", "withdrawn_by", "withdrawn_at", "withdrawal_reason", "withdrawal_evidence", *AUDIT,
	},
	"Tender Channel Confirmation": {
		"tender", "publication", "subject_type", "subject_id", "subject_digest", "channel", "channel_label", "confirmation_mode", "status",
		"available_at", "evidence_reference", "public_url", "url_not_applicable_reason", "evidence_file", "evidence_digest",
		"evidence_check_result", "evidence_notes", "attestation_text", "attested_by", "attested_at", *AUDIT,
	},
	"Tender Addendum": {
		"tender", "publication", "addendum_number", "addendum_reference", "status", "change_class", "affected_area", "affected_reference",
		"affected_reference_key", "previous_value", "revised_value", "reason", "materiality_statement", "deadline_extension_required",
		"revised_submission_deadline", "baseline_digest", "addendum_digest", "drafted_by", "drafted_at", "submitted_by", "submitted_at",
		"returned_by", "returned_at", "return_reason", "issue_decided_by", "issue_decided_at", "issued_at", "successor_bid_definition",
		"successor_bid_definition_id", "successor_definition_version", "successor_definition_digest", "predecessor_addendum",
		"cancellation_review_status", "cancellation_review_reason", "cancellation_review_closed_reason", "discarded_by", "discarded_at", *AUDIT,
	},
	"Tender Clarification": {
		"tender", "publication", "bid_definition_id", "related_addendum", "candidate_registration_id", "producer", "inbound_event_id",
		"question", "received_at", "status", "response", "response_audience", "affects_published_tender", "required_addendum",
		"responded_by", "responded_at", "closed_reason", "response_digest", *AUDIT,
	},
	"Tender Candidate Notice": {
		"tender", "notice_type", "subject_type", "subject_id", "subject_digest", "audience_frozen_at", "candidate_registration_id",
		"destination_snapshot", "destination_version", "content_digest", "status", "attempt_count", "last_attempt_at",
		"provider_reference", "failure_reason", "delivered_at", "attempts", *AUDIT,
	},
	"Tender Candidate Notice Attempt": {"attempt_number", "attempted_at", "transport", "result", "provider_reference", "failure_reason", "actor"},
	"Tender Bid Definition": {
		"tender", "tender_version", "publication", "addendum", "bid_definition_id", "definition_version", "definition_digest", "status",
		"definition_json", "response_schema_digest", "evaluation_contract_digest", "contract_projection_digest",
		"predecessor_bid_definition", "identity_map_json", "identity_map_digest", "frozen_at", "effective_at", *AUDIT,
	},
	"Tender Cancellation": {
		"tender", "publication", "ground", "ground_label", "reason", "recommendation", "decided_by", "decided_at", "ppra_report_due_by",
		"candidate_notice_due_by", "ppra_report_status", "ppra_report_evidence_id", "candidate_notice_status", "notice_publication_status",
		"cancellation_digest", "notice_document_digest", "obligations", *AUDIT,
	},
	"Tender Cancellation Obligation": {
		"obligation_id", "obligation_type", "channel", "label", "due_by", "status", "evidence_reference", "evidence_file", "evidence_digest",
		"recorded_by", "recorded_at",
	},
	"Tender Document": {"tender", "tender_version", "addendum", "cancellation", "kind", "audience", "digest", "file", "html_file", "generated_by", "generated_at", "fixture_namespace"},
	"Tender Command Journal": {"idempotency_key", "command", "document_type", "document_name", "request_fingerprint", "actor", "result", "occurred_at", "fixture_namespace"},
	"Tender Event": {"event_id", "event_type", "tender", "sequence", "subject_type", "subject_id", "occurred_at", "payload", "status", "consumer", "delivered_at", "fixture_namespace"},
	"Tender Submission Handoff": {"tender", "tender_version", "publication", "handoff_version", "payload_json", "handoff_digest", "effective_submission_deadline", "closed_at", "fixture_namespace"},
}
CHILD_TABLES = ("Tender Evidence Requirement", "Tender Review Finding", "Tender Cancellation Obligation", "Tender Candidate Notice Attempt")
SITE_READERS = {"Procurement Officer", "Head of Procurement Function", "Accounting Officer", "Auditor"}

# §16 / tracker rule 3: concepts this module must never reference. Proven by
# planted violation (the test's own sub-test).
PROHIBITED_TOKENS: tuple[str, ...] = (
	"tender_preparation", "Prepared Tender", "TenderPublicationHandoff", "TPR_TEMPLATE", "Procurement Tender", "Mark as published",
	"pe_fy_context", "Frappe User Permission", "manifest_editor", "schema_editor", "showPeSwitcher: true", "kt_cl_surface_registry",
	# TPR-CHG-001 v0.12 tracker rule 3 — the retired v0.8 inquiry model.
	"Tender Addendum Inquiry", "TND_INQUIRY_LATE", "receive_addendum_inquiry", "respond_to_addendum_inquiry",
)
_ALLOWED_MENTIONS = {("tests/test_tender_schema.py", token) for token in PROHIBITED_TOKENS}


def _module_sources() -> list[tuple[str, str]]:
	out = []
	for root, _dirs, files in os.walk(MODULE_DIR):
		if "__pycache__" in root:
			continue
		for name in files:
			if name.endswith((".py", ".json", ".html", ".js")):
				path = os.path.join(root, name)
				with open(path, encoding="utf-8") as handle:
					out.append((os.path.relpath(path, MODULE_DIR), handle.read()))
	return out


class TestTendersSchema(IntegrationTestCase):
	def test_every_doctype_has_exactly_its_allow_listed_fields(self):
		for doctype, expected in EXPECTED_FIELDS.items():
			self.assertTrue(frappe.db.exists("DocType", doctype), f"{doctype} is missing")
			meta = frappe.get_meta(doctype)
			actual = {f.fieldname for f in meta.fields if f.fieldtype not in ("Section Break", "Column Break", "Tab Break")}
			self.assertEqual(actual, expected, f"{doctype}: unexpected={sorted(actual - expected)} missing={sorted(expected - actual)}")

	def test_every_doctype_belongs_to_the_tenders_module_and_has_a_table(self):
		for doctype in EXPECTED_FIELDS:
			self.assertEqual(frappe.db.get_value("DocType", doctype, "module"), "Tenders", doctype)
			self.assertTrue(frappe.db.table_exists(doctype), f"{doctype} has no table")

	def test_child_tables_are_not_independently_permissioned(self):
		for doctype in CHILD_TABLES:
			meta = frappe.get_meta(doctype)
			self.assertTrue(meta.istable, f"{doctype} should be a child table")
			self.assertEqual([p.role for p in meta.permissions], [], f"{doctype} carries DocPerms")

	def test_docperms_are_exactly_the_section_6_readers(self):
		"""§6: the four Site-wide responsibilities read; Tender and Tender
		Version additionally admit the two departmental neutral readers; no
		business role writes, creates or deletes anything."""
		for doctype in EXPECTED_FIELDS:
			if doctype in CHILD_TABLES:
				continue
			meta = frappe.get_meta(doctype)
			business = {p.role for p in meta.permissions if p.role != "System Manager"}
			expected = SITE_READERS | ({"Departmental Author", "Head of User Department"} if doctype in ("Tender", "Tender Version", "Tender Document") else set())
			if doctype == "Tender Command Journal":
				expected = {"Auditor"}
			self.assertEqual(business, expected, doctype)
			for perm in meta.permissions:
				if perm.role == "System Manager":
					continue
				self.assertFalse(perm.write or perm.create or perm.delete, f"{doctype}: {perm.role} may write")
		template_perms = frappe.get_meta("Installed STD Release").permissions
		self.assertFalse(any(p.write or p.create for p in template_perms), "no role writes the installed STD release registry")

	def test_the_error_contract_is_exactly_the_section_8_set(self):
		self.assertEqual(len(errors.ERROR_CODES), 35)
		self.assertEqual(set(errors.MESSAGES), errors.ERROR_CODES)
		with self.assertRaises(ValueError):
			errors.fail("TND_SOMETHING_ELSE")
		with self.assertRaises(errors.TendersError) as ctx:
			errors.fail("TND_MUST_FIX")
		self.assertEqual(ctx.exception.code, "TND_MUST_FIX")

	def test_no_prohibited_concept_token_in_module_sources(self):
		hits = []
		for relpath, text in _module_sources():
			for token in PROHIBITED_TOKENS:
				if token in text and (relpath, token) not in _ALLOWED_MENTIONS:
					hits.append((relpath, token))
		self.assertEqual(hits, [])
		# Planted violation: the scan must be able to fail.
		planted = [(rel, tok) for rel, text in [("planted.py", "x = 'Mark as published'")] for tok in PROHIBITED_TOKENS if tok in text]
		self.assertEqual(planted, [("planted.py", "Mark as published")])
