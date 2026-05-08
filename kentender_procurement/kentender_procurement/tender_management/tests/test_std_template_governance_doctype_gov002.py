# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-002 — ``STD Template`` governance field schema (doc 7 §7.1–§7.11).

Omits pack duplicates ``package_payload_json`` / ``package_manifest_json`` (see
``STD-GOV-102``); child tables are STD-GOV-003.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_doctype_gov002
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

# Fieldnames required on STD Template per implementation pack §7 (minus §7.3 duplicates).
STD_GOV_002_EXPECTED_FIELDS: frozenset[str] = frozenset(
	{
		"template_code",
		"template_title",
		"template_family",
		"procurement_category",
		"procurement_method_profile",
		"template_version",
		"package_version",
		"version_label",
		"is_governed_version",
		"source_authority",
		"source_document_code",
		"source_document_title",
		"source_effective_date",
		"source_url",
		"source_notes",
		"import_source_type",
		"import_batch_id",
		"package_hash",
		"package_hash_algorithm",
		"package_size_bytes",
		"package_file_reference",
		"canonicalization_version",
		"payload_locked",
		"lifecycle_status",
		"previous_lifecycle_status",
		"status_changed_at",
		"status_changed_by",
		"status_reason",
		"allowed_for_tender_creation",
		"is_suspended",
		"is_historical",
		"latest_validation_status",
		"latest_validation_run_id",
		"latest_validation_at",
		"latest_validation_by",
		"latest_validation_package_hash",
		"latest_validation_result_json",
		"critical_finding_count",
		"warning_finding_count",
		"info_finding_count",
		"validation_is_current",
		"submitted_for_approval_by",
		"submitted_for_approval_at",
		"submission_comment",
		"reviewed_by",
		"reviewed_at",
		"review_comment",
		"approved_by",
		"approved_at",
		"approval_decision",
		"approval_comments",
		"approval_validation_run_id",
		"approval_package_hash",
		"approval_override_used",
		"approval_override_reason",
		"activated_by",
		"activated_at",
		"activation_reason",
		"activation_approval_reference",
		"activation_package_hash",
		"active_from",
		"active_until",
		"suspended_by",
		"suspended_at",
		"suspension_reason",
		"reinstated_by",
		"reinstated_at",
		"reinstatement_reason",
		"retired_by",
		"retired_at",
		"retirement_reason",
		"supersedes_template",
		"superseded_by_template",
		"superseded_by",
		"superseded_at",
		"supersession_reason",
		"supersession_effective_date",
		"is_default_active_version",
		"active_profile_key",
		"tender_usage_count",
		"first_used_at",
		"last_used_at",
		"locked_due_to_usage",
		"mutation_blocked",
		"delete_blocked",
		"usage_summary_json",
		"governance_notes",
		"correction_notes",
		"internal_admin_notes",
		"legal_review_notes",
		"latest_governance_snapshot_json",
		"latest_governance_snapshot_hash",
		"latest_governance_snapshot_at",
		"latest_governance_snapshot_by",
		# STD-GOV-003 child table fields on parent.
		"lifecycle_events",
		"validation_findings",
		"template_usage",
		# POC / governed combined payload (pack semantic for payload + manifest).
		"package_json",
		"manifest_json",
	}
)


class TestStdTemplateGovernanceDocTypeGov002(IntegrationTestCase):
	def test_std_gov_002_expected_fields_exist(self) -> None:
		meta = frappe.get_meta("STD Template")
		names = {df.fieldname for df in meta.fields}
		missing = sorted(STD_GOV_002_EXPECTED_FIELDS - names)
		self.assertEqual(
			missing,
			[],
			f"STD-GOV-002 missing fields: {missing}",
		)

	def test_std_gov_002_lifecycle_and_validation_select_options(self) -> None:
		meta = frappe.get_meta("STD Template")
		lc = meta.get_field("lifecycle_status")
		self.assertIsNotNone(lc)
		opts = (lc.options or "").split("\n")
		self.assertIn("Validated", opts)
		self.assertIn("Archived", opts)

		vs = meta.get_field("latest_validation_status")
		self.assertIsNotNone(vs)
		vopts = (vs.options or "").split("\n")
		self.assertIn("Not Run", vopts)
		self.assertIn("Pass with Warnings", vopts)

	def test_std_gov_002_template_family_is_select(self) -> None:
		meta = frappe.get_meta("STD Template")
		tf = meta.get_field("template_family")
		self.assertEqual(tf.fieldtype, "Select")
		self.assertIn("Works", (tf.options or "").split("\n"))

	def test_std_gov_002_no_package_payload_duplicate_field(self) -> None:
		meta = frappe.get_meta("STD Template")
		self.assertIsNone(meta.get_field("package_payload_json"))
		self.assertIsNone(meta.get_field("package_manifest_json"))
