# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 — schema contract tests (plan Phase 2a, tracker PLN18-201..204).

Guards: (1) every §4 doctype exists with exactly its allow-listed fields (an
undocumented field is a defect, not an option); (2) the composite uniqueness
of §4.10 exists in storage; (3) no doctype slug collides with a Desk Page
route (D21, [[frappe-page-doctype-slug-collision]]); (4) no removed-concept
token survives in the module's server sources (tracker rule 3) — and the scan
itself is proven live by a planted violation; (5) `errors.py` equals spec §8;
(6) the retired doctypes are gone; (7) controllers stay thin.

`DEFERRED_MENTIONS` names the rule-3 tokens still present in a file until the
Phase 2 sub-phase that removes them lands (row id given); the Phase 2 exit row
PLN18-213 requires it empty.
"""

from __future__ import annotations

import os
import re

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning import errors

MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(
	os.path.dirname(frappe.get_app_path("kentender_procurement")), "..", "docs", "mvp-1-r1", "04_planning",
	"KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_18.md",
)

MILESTONES = ("invitation", "bid_opening", "evaluation_completion", "award_approval", "award_notification", "contract_signing", "delivery_completion")

EXPECTED_FIELDS: dict[str, set[str]] = {
	# --- departmental (§4.2–4.4) -------------------------------------------
	"Departmental Plan": {"dpp_reference", "fiscal_year", "organisation_unit", "current_state", "current_version", "current_accepted_version", "record_version", "fixture_namespace"},
	"Departmental Plan Version": {"version_reference", "departmental_plan", "version_number", "based_on_version", "returned_from_submission", "version_status", "submission", "record_version", "fixture_namespace"},
	"Departmental Plan Entry": {"entry_id", "dpp_version", "source_origin", "direct_source_id", "need", "need_revision", "title", "description", "expected_operational_result", "quantity", "unit", "required_by_date", "budget_line", "indicative_amount", "not_proceeding_reason", "fixture_namespace"},
	"Departmental Plan Submission": {"submission_reference", "dpp_version", "submission_number", "entry_snapshots", "content_hash", "attestation_text", "submitted_by_user", "authority_snapshot", "submitted_at", "fixture_namespace"},
	"Departmental Plan Validation Task": {"task_reference", "submission", "dpp_version", "organisation_unit", "fiscal_year", "status", "decision", "task_token", "record_version", "fixture_namespace"},
	"Departmental Plan Validation Decision": {"decision_reference", "task", "submission", "decision", "classifications", "issues", "actor", "authority_snapshot", "decided_at", "command_idempotency_key", "fixture_namespace"},
	# --- annual roots, versions, items (§4.5–4.6) -----------------------------
	"Annual Plan": {"plan_reference", "title", "fiscal_year", "active_version", "open_successor_version", "record_version", "fixture_namespace"},
	"Annual Plan Version": {
		"version_reference", "annual_plan", "version_number", "based_on_version", "correction_of_plan_version", "source_cohort",
		"version_status", "change_reason", "project_name", "funding_state", "funding_line_totals_hash", "splitting_confirmation",
		"late_activation_reason", "submitted_snapshot", "snapshot_hash", "submitted_by_user", "preparation_signature",
		"submitted_snapshot_id", "submitted_at", "activated_at", "record_version", "fixture_namespace",
	},
	"Plan Item": {"plan_item_id", "plan_item_reference", "annual_plan", "scope_locked_since", "first_authorised_requisition", "authorisation_hold", "open_correction_requests", "record_version", "fixture_namespace"},
	"Annual Plan Item": {
		"plan_item_id", "plan_version", "plan_item", "title", "description", "strategic_objective", "strategy_plan", "strategy_plan_version",
		"objective_path", "requirement_type", "procurement_method", "method_profile_version", "schedule_profile_version",
		"method_condition_evidence", "mandatory_restriction_results", "estimate_basis", "estimate_basis_reference", "aggregation_reason",
		"procurement_category", "plan_horizon", "aggregation_indicator", "lotting_indicator", "lot_count", "reservation_category",
		"reservation_category_reason", "county_resident_reservation", "exclusive_preference", "threshold_band_at_readiness",
		"baseline_invitation_date", "tendering_period_days", "evaluation_period_days", "award_approval_buffer_days",
		"notification_buffer_days", "standstill_period_days", "estimated_delivery_period_days", "period_inputs", "baseline_milestones",
		"estimated_completion_date",
		*(f"baseline_{m}_date" for m in MILESTONES if m != "invitation"), *(f"forecast_{m}_date" for m in MILESTONES), *(f"actual_{m}_date" for m in MILESTONES),
		"item_status", "item_state", "record_version", "fixture_namespace",
	},
	"Plan Source Allocation": {"allocation_id", "plan_item", "plan_item_id", "plan_version", "dpp_entry", "source_origin", "source_key", "need", "need_revision", "organisation_unit", "quantity", "unit", "required_by_date", "budget_line", "indicative_amount", "allocation_state", "fixture_namespace"},
	"Plan Item Forecast Revision": {"plan_item", "plan_item_id", "milestone", "previous_forecast_date", "new_forecast_date", "reason", "cascade_id", "revised_by", "revised_at", "fixture_namespace"},
	# --- financial and governance evidence (§4.7) -----------------------------
	"Plan Financial Basis": {"plan_version", "fiscal_year", "currency", "precision", "lines", "planned_total", "approved_total", "basis_digest", "budget_basis_digest", "captured_at", "fixture_namespace"},
	"Plan Finance Task": {"task_reference", "plan_version", "financial_basis", "plan_value", "line_totals_hash", "affordability_statement", "status", "decision", "task_token", "record_version", "fixture_namespace"},
	"Plan Finance Decision": {"decision_reference", "task", "decision", "return_reason", "affordability_statement", "actor", "authority_snapshot", "decided_at", "command_idempotency_key", "fixture_namespace"},
	"Plan Finance Basis Reuse": {"plan_version", "earlier_decision", "financial_basis", "validated_at", "fixture_namespace"},
	"Plan Preparation Signature": {"plan_version", "submitted_snapshot_id", "snapshot_hash", "actor", "capacity", "authority_snapshot", "signed_at", "command_idempotency_key", "fixture_namespace"},
	"Plan Governance Task": {"task_reference", "annual_plan", "plan_version", "stage", "capacity", "status", "decision", "task_token", "record_version", "fixture_namespace"},
	"Plan Governance Decision": {"decision_reference", "task", "plan_version", "stage", "decision", "capacity", "collective_resolution_reference", "return_reason", "actor", "authority_snapshot", "decided_at", "command_idempotency_key", "fixture_namespace"},
	"Late Activation Explanation": {"plan_version", "reason", "actor", "authority_snapshot", "recorded_at", "supersedes", "fixture_namespace"},
	# --- downstream use, correction, operational evidence (§4.8) --------------
	"Plan Drawdown Reference": {"plan_item", "plan_item_id", "allocation", "requisition_reference", "requesting_org_unit", "quantity", "amount", "drawdown_state", "reversal_reference", "record_version", "fixture_namespace"},
	"Plan Item Correction Request": {"plan_item", "plan_item_id", "plan_version", "requisition_reference", "requisition_version", "reason", "requested_by", "requested_role", "requested_at", "producer_event_id", "status", "resolved_by", "resolved_at", "resolution_note", "idempotency_key", "record_version", "fixture_namespace"},
	"Plan Item Correction Disposition": {"correction_request", "action", "actor", "authority_snapshot", "disposed_at", "reason", "correcting_plan_version", "replacement_lineage", "producer_event_id", "command_idempotency_key", "fixture_namespace"},
	"Milestone Actual Event": {"producer", "event_id", "schema_version", "proceeding_type", "proceeding_id", "requisition_reference", "plan_version", "plan_item", "plan_item_id", "allocation", "milestone", "actual_date", "recorded_at", "producer_sequence", "supersedes_event_id", "source_evidence_reference", "fixture_namespace"},
	"Proceeding Coverage": {"proceeding_type", "proceeding_id", "requisition_reference", "requisition_version", "plan_version", "plan_item", "plan_item_id", "allocation", "covered_quantity", "covered_value", "authorisation_state", "publication_state", "reversal_state", "last_event", "fixture_namespace"},
	"Milestone Notice": {"recipient", "plan_item", "plan_item_id", "proceeding_id", "milestone", "due_date", "notice_status", "notification_key", "last_evaluated_at", "history", "fixture_namespace"},
	# --- publication and external evidence (§4.9) -----------------------------
	"Approved Plan Snapshot": {"plan_version", "annual_plan", "content", "evidence_index", "content_digest", "approval_decision", "strategy_approval_snapshot", "approved_at", "fixture_namespace"},
	"Plan Publication": {"publication_id", "snapshot", "plan_version", "destination", "schema_version", "manifest", "package_hash", "publication_state", "public_location", "external_reference", "acknowledged_at", "record_version", "fixture_namespace"},
	"Publication Intent": {"publication", "dispatch_state", "created_at", "dispatched_at", "correlation_id", "hold", "record_version", "fixture_namespace"},
	"Publication Attempt": {"publication", "attempt_number", "result", "attempted_at", "completed_at", "external_reference", "response_evidence", "failure_reason", "fixture_namespace"},
	"Publication Acknowledgement": {"event_id", "publication", "snapshot", "destination", "package_hash", "public_location", "external_reference", "acknowledged_at", "received_at", "matched", "mismatch_reason", "fixture_namespace"},
	"Treasury Submission Evidence": {"plan_version", "document_hash", "submitted_at", "channel", "destination", "dispatch_reference", "supporting_attachment", "exact_document_confirmed", "actor", "authority_snapshot", "recorded_at", "evidence_state", "superseded_by", "correction_reason", "fixture_namespace"},
	"Plan Publication Hold": {"plan_version", "publication", "hold_kind", "reason", "raised_by", "raised_by_service", "raised_at", "reconciliation_outcome", "withdrawal_decision", "hold_state", "released_at", "record_version", "fixture_namespace"},
	"Annual Plan Publication Destination": {"destination_id", "title", "adapter", "active", "sandbox_outcome", "fixture_namespace"},
	# --- v1.12 rows carried until the Phase 2 exit patch retires them (PLN18-213)
	"Annual Plan Publication": {"publication_reference", "plan_version", "destination", "attempt_number", "result", "payload_hash", "payload", "legal_character", "external_reference", "attempted_at", "acknowledged_at", "fixture_namespace"},
	# --- infrastructure
	"Planning Command Journal": {"idempotency_key", "command", "document_type", "document_name", "request_fingerprint", "actor", "result", "occurred_at", "fixture_namespace"},
}

# v1.18 §4.6/§4.7 columns whose replacement lands in a later Phase 2 sub-phase;
# dropped by `pln_chg_001_v118_drop_retired_fields` at the Phase 2 exit (D15).
RETIRED_COLUMNS_PENDING_DROP = {
	"Annual Plan Item": {"exclusive_preference", "threshold_band_at_readiness", "reservation_category_reason", "tendering_period_days", "evaluation_period_days", "award_approval_buffer_days", "notification_buffer_days", "standstill_period_days"},
	"Annual Plan Version": {"funding_line_totals_hash", "splitting_confirmation", "late_activation_reason"},
	"Plan Finance Task": {"plan_value", "line_totals_hash", "affordability_statement"},
}

CORE_CATALOGUES = {"Requirement Type": {"title", "status", "fixture_namespace"}, "Procurement Method": {"title", "status", "fixture_namespace"}}

LEGACY_DOCTYPES = (
	"Procurement Plan", "Procurement Plan Version", "Procurement Plan Item", "Procurement Plan Item Version", "Plan Need Allocation",
	"Plan Decision", "Plan Validation Result", "Planning Handoff Snapshot", "Publication Event",
	"Departmental Plan Submission Window", "Plan Reservation Reference",
)

# Tracker rule 3 (v1.18 §16 / §17.4) + the v1.12 §1.1 list. Each token is
# specific enough not to collide with a permitted identifier.
PROHIBITED_TOKENS = (
	# v1.12 removed concepts
	"pvc_snapshot", "lotting_decision", "expected_lot_count", "recommended_method", "method_basis", "annual_funding_schedule",
	"preference_reservation_scheme", "schedule_change_reason", "ms_invitation_published", "Plan Need Allocation",
	"Demand Funding Allocation", "add_demand_to_plan", "list_eligible_demands", "planning_permissions",
	"Operational Scope Assignment", "require_capability", "pe_fy_context", "procuring_entity", "PEFiscalYearContext",
	"User Permission", "Funding Reservation", "reserve_funding", "release_reservation", "revalidate_reservations",
	"Unit Of Measure", "Planning Auditor", "finance_state", "Pending addition\"",
	# v1.18 rule 3
	"PLN_RESERVATION_RELEASE_FAILED", "PLN_TENDERING_PERIOD_BELOW_MINIMUM", "PLN_EVALUATION_PERIOD_ABOVE_MAXIMUM", "PLN_STANDSTILL_BELOW_MINIMUM",
	"TENDERING_FLOOR", "EVALUATION_CEILING", "STANDSTILL_FLOOR", "DEFAULT_AWARD_APPROVAL_BUFFER", "DEFAULT_NOTIFICATION_BUFFER",
	"highest_advantage", "multi_year_justification", "Multi-year", "\"ocds", "ocid", "Awaiting Finance\"",
	"record_requisition_drawdown", "RecordRequisitionDrawdown", "_stamp_design_clock", "showPeSwitcher: true",
	"kt_cl_surface_registry", "is_board_capacity",
)

# Tests proving a retired concept is ABSENT from the live site, and the one
# §5.2.2-permitted UI work-status label, may name a token once.
ALLOWED_MENTIONS = {
	("tests/test_plan_finance.py", "Funding Reservation"),
	("tests/test_plan_publication.py", "Funding Reservation"),
	("seeds/kentender_mvp_v1.py", "Funding Reservation"),
	("services/plan_read.py", "Awaiting Finance\""),  # §5.2.2: a Finance-task badge label, never a Plan status
	("tests/test_plan_workbench.py", "Multi-year"),  # proves the fixed literal rejects an unsupported payload
	("errors.py", "Multi-year"),  # the §8 message of PLN_MULTI_YEAR_UNSUPPORTED names what is rejected
}

# Rule-3 tokens still present until the named Phase 2 row lands (PLN18-213 requires this empty).
DEFERRED_MENTIONS: dict[tuple[str, str], str] = {
	("services/publication_payload.py", "ocid"): "PLN18-209",
	("services/publication_payload.py", "\"ocds"): "PLN18-209",
	("tests/test_plan_publication.py", "ocid"): "PLN18-209",
	("tests/test_plan_publication.py", "\"ocds"): "PLN18-209",
	("seeds/kentender_mvp_v1.py", "_stamp_design_clock"): "PLN18-401",
}

SCAN_DIRS = ("doctype", "services", "tests", "page", "seeds")
SCAN_SUFFIXES = (".py", ".json")

UNIQUE_INDEXES = {
	("tabDepartmental Plan", "pln_uniq_dpp_root"),
	("tabDepartmental Plan Version", "pln_uniq_dpp_version"),
	("tabDepartmental Plan Entry", "pln_uniq_entry_id_per_version"),
	("tabAnnual Plan Version", "pln_uniq_plan_version"),
	("tabAnnual Plan Item", "pln_uniq_item_per_version"),
	("tabAnnual Plan Item", "pln_uniq_item_root_per_version"),
	("tabPlan Source Allocation", "pln_uniq_alloc_per_version"),
	("tabMilestone Actual Event", "pln_uniq_actual_event"),
	("tabPlan Publication", "pln_uniq_publication"),
	("tabPublication Attempt", "pln_uniq_attempt"),
	("tabProceeding Coverage", "pln_uniq_coverage"),
}


def scan_for_tokens(module_dir: str = MODULE_DIR, *, tokens=PROHIBITED_TOKENS, allowed=None, deferred=None) -> list[str]:
	"""The rule-3 scan: every server source under the module, minus this file."""
	this_file = os.path.abspath(__file__)
	allowed = ALLOWED_MENTIONS if allowed is None else allowed
	deferred = DEFERRED_MENTIONS if deferred is None else deferred
	files = [os.path.join(module_dir, "api.py"), os.path.join(module_dir, "errors.py")]
	for sub in SCAN_DIRS:
		for root, _dirs, names in os.walk(os.path.join(module_dir, sub)):
			if "__pycache__" in root:
				continue
			files.extend(os.path.join(root, f) for f in names if f.endswith(SCAN_SUFFIXES))
	hits: list[str] = []
	for path in files:
		if os.path.abspath(path) == this_file or not os.path.exists(path):
			continue
		rel = os.path.relpath(path, module_dir)
		text = open(path, encoding="utf-8").read()
		for token in tokens:
			if token in text and (rel, token) not in allowed and (rel, token) not in deferred:
				hits.append(f"{rel}: {token}")
	return hits


def spec_error_table() -> dict[str, str]:
	text = open(os.path.normpath(SPEC), encoding="utf-8").read()
	section = text.split("## 8. Error contract")[1].split("\n## 9.")[0]
	return dict(re.findall(r"^\| (PLN_[A-Z_]+) \| (.+?) \|$", section, re.M))


class TestPlanningV118Schema(IntegrationTestCase):
	def test_every_v118_doctype_has_exactly_its_allow_listed_fields(self):
		for doctype, expected in {**EXPECTED_FIELDS, **CORE_CATALOGUES}.items():
			self.assertTrue(frappe.db.exists("DocType", doctype), f"{doctype} is missing")
			meta = frappe.get_meta(doctype)
			actual = {f.fieldname for f in meta.fields if f.fieldtype not in ("Section Break", "Column Break", "Tab Break")}
			self.assertEqual(actual, expected, f"{doctype}: unexpected={sorted(actual - expected)} missing={sorted(expected - actual)}")
			pending = RETIRED_COLUMNS_PENDING_DROP.get(doctype, set())
			self.assertEqual(pending - actual, set(), f"{doctype}: a pending-drop column is already gone; update RETIRED_COLUMNS_PENDING_DROP")

	def test_fixed_literals_and_status_vocabularies(self):
		"""§4.6 horizon is a fixed literal; §5.2 statuses; §4.8 correction states."""
		item = frappe.get_meta("Annual Plan Item")
		self.assertEqual(item.get_field("plan_horizon").options.split("\n"), ["Single year"])
		version = frappe.get_meta("Annual Plan Version")
		statuses = version.get_field("version_status").options.split("\n")
		for status in ("Withdrawn for correction", "Published — activation held", "Active", "Superseded", "Cancelled"):
			self.assertIn(status, statuses)
		self.assertNotIn("Confirmed", statuses)
		self.assertEqual(version.get_field("funding_state").options.split("\n"), ["Not requested", "Awaiting confirmation", "Confirmed", "Returned", "Stale"])
		self.assertEqual(frappe.get_meta("Plan Item Correction Request").get_field("status").options.split("\n"), ["Open", "In progress", "Resolved", "Closed without change"])
		self.assertEqual(frappe.get_meta("Milestone Actual Event").get_field("milestone").options.split("\n"), list(MILESTONES))
		self.assertEqual(frappe.get_meta("Plan Publication").get_field("schema_version").default, "KenTenderAnnualPlan.v1")

	def test_head_of_procurement_function_reads_the_annual_plan_family(self):
		"""§6.2 (D6): the exact read the preparation signature needs, never an implicit Planner assignment."""
		for doctype in ("Annual Plan", "Annual Plan Version", "Annual Plan Item", "Plan Source Allocation", "Plan Finance Task", "Plan Governance Task", "Plan Preparation Signature", "Approved Plan Snapshot"):
			roles = {p.role for p in frappe.get_meta(doctype).permissions if p.read}
			self.assertIn("Head of Procurement Function", roles, doctype)
			self.assertNotIn("Head of User Department", roles, doctype)

	def test_legacy_planning_doctypes_are_gone(self):
		for doctype in LEGACY_DOCTYPES:
			self.assertFalse(frappe.db.exists("DocType", doctype), f"legacy doctype {doctype} still exists")
			self.assertFalse(
				frappe.db.sql("select 1 from information_schema.tables where table_schema = database() and table_name = %s", (f"tab{doctype}",)),
				f"legacy table tab{doctype} still exists",
			)

	def test_no_removed_concept_token_in_module_sources(self):
		hits = scan_for_tokens()
		self.assertEqual(hits, [], "removed-concept tokens found: " + "; ".join(hits))
		for (rel, token), row in DEFERRED_MENTIONS.items():
			path = os.path.join(MODULE_DIR, rel)
			self.assertTrue(os.path.exists(path) and token in open(path, encoding="utf-8").read(), f"{rel}: {token} is gone — remove its deferral ({row})")

	def test_the_scan_catches_a_planted_violation(self):
		planted = os.path.join(MODULE_DIR, "seeds", "_planted_violation_test.py")
		with open(planted, "w", encoding="utf-8") as handle:
			handle.write("# planted by test_planning_v118_schema\nVALUE = 'record_requisition_drawdown'\n")
		try:
			hits = scan_for_tokens()
		finally:
			os.remove(planted)
		self.assertEqual(hits, ["seeds/_planted_violation_test.py: record_requisition_drawdown"])
		self.assertEqual(scan_for_tokens(), [])

	def test_error_contract_equals_spec_section_8(self):
		table = spec_error_table()
		self.assertEqual(len(table), 51)
		self.assertEqual(set(table), set(errors.ERROR_CODES))
		self.assertEqual(table, errors.MESSAGES)
		for removed in ("PLN_RESERVATION_RELEASE_FAILED", "PLN_TENDERING_PERIOD_BELOW_MINIMUM", "PLN_EVALUATION_PERIOD_ABOVE_MAXIMUM", "PLN_STANDSTILL_BELOW_MINIMUM"):
			self.assertNotIn(removed, errors.ERROR_CODES)
			with self.assertRaises(ValueError):
				errors.fail(removed)

	def test_composite_unique_indexes_exist(self):
		rows = frappe.db.sql(
			"""select table_name, index_name from information_schema.statistics
			where table_schema = database() and index_name like 'pln_uniq%%' group by table_name, index_name"""
		)
		self.assertEqual(UNIQUE_INDEXES - {tuple(r) for r in rows}, set())

	def test_event_uniqueness_rejects_a_duplicate_producer_event(self):
		"""§4.10 — event uniqueness by producer + event id, in storage."""
		plan_item = frappe.get_all("Plan Item", limit=1, pluck="name")
		if not plan_item:
			self.skipTest("no Plan Item on this site")
		base = {
			"doctype": "Milestone Actual Event", "producer": "schema-test", "event_id": "EVT-SCHEMA-1", "plan_item": plan_item[0],
			"plan_item_id": plan_item[0], "milestone": "invitation", "actual_date": "2101-01-01", "recorded_at": frappe.utils.now_datetime(),
			"fixture_namespace": "KENTENDER_TEST",
		}
		first = frappe.get_doc(base)
		first.insert(ignore_permissions=True)
		self.addCleanup(frappe.db.delete, "Milestone Actual Event", {"producer": "schema-test"})
		with self.assertRaises(Exception) as caught:
			frappe.get_doc(base).insert(ignore_permissions=True)
		self.assertIn("Duplicate", str(caught.exception))

	def test_no_doctype_slug_collides_with_a_desk_page(self):
		"""D21 — a Page route always loses to a same-named doctype List View."""
		pages = set(frappe.get_all("Page", pluck="name"))
		for doctype in EXPECTED_FIELDS:
			self.assertNotIn(frappe.scrub(doctype).replace("_", "-"), pages, doctype)

	def test_no_retired_planning_permission_hook_paths_survive(self):
		import kentender_procurement.hooks as hooks

		self.assertIn("Departmental Plan", hooks.kentender_scope_map)
		self.assertIn("Departmental Plan Validation Task", hooks.kentender_scope_map)
		for doctype in ("Annual Plan", "Plan Item", "Plan Publication", "Milestone Notice"):
			self.assertNotIn(doctype, hooks.kentender_scope_map)
		self.assertFalse(os.path.exists(os.path.join(MODULE_DIR, "services", "authority.py")))

	def test_controllers_are_thin(self):
		doctype_dir = os.path.join(MODULE_DIR, "doctype")
		for root, _dirs, files in os.walk(doctype_dir):
			if "__pycache__" in root:
				continue
			for f in files:
				if not f.endswith(".py") or f == "__init__.py":
					continue
				lines = open(os.path.join(root, f), encoding="utf-8").read().splitlines()
				self.assertLessEqual(len(lines), 80, f"{f} exceeds the thin-controller ceiling")
				self.assertEqual([l for l in lines if l.strip().startswith(("import ", "from ")) and ".services" in l], [], f"{f} imports a services module")
