# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 Phase 1 — schema contract tests.

Guards three things: (1) every §4 doctype exists with exactly its allow-listed
fields (§2.2 data-purpose gate: an undocumented field is a defect, not an
option); (2) no removed-concept token survives in the module's server code
(§1.1); (3) the Demand-era doctypes are gone and the composite uniqueness
constraints for invariants 2/7/17/24 exist and actually reject duplicates.

Scan scope note: the static scan covers the whole module — doctype/,
services/, seeds/, tests/, page/ and api.py (page/ joined in Phase 3 when
the Stitch pages were demolished, D10).
"""

from __future__ import annotations

import os

import frappe
from frappe.tests import IntegrationTestCase

MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STANDARD_FIELDS = {
	"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx",
	"_user_tags", "_comments", "_assign", "_liked_by",
}

EXPECTED_FIELDS: dict[str, set[str]] = {
	"Departmental Plan Submission Window": {
		"pe_fy_context", "opens_at", "closes_at", "fixture_namespace",
	},
	"Departmental Plan": {
		"dpp_reference", "pe_fy_context", "procuring_entity", "organisation_unit",
		"financial_year", "current_state", "current_version", "current_accepted_version",
		"record_version", "fixture_namespace",
	},
	"Departmental Plan Version": {
		"version_reference", "departmental_plan", "version_number", "based_on_version",
		"returned_from_submission", "version_status", "submission", "record_version",
		"fixture_namespace",
	},
	"Departmental Plan Entry": {
		"entry_id", "dpp_version", "source_origin", "need", "need_version", "title",
		"description", "expected_operational_result", "quantity", "unit",
		"required_by_date", "budget_line", "indicative_amount", "fixture_namespace",
	},
	"Departmental Plan Submission": {
		"submission_reference", "dpp_version", "submission_number", "entry_snapshots",
		"content_hash", "attestation_text", "submitted_by_user", "authority_snapshot",
		"submitted_at", "fixture_namespace",
	},
	"Departmental Plan Validation Task": {
		"task_reference", "submission", "dpp_version", "procuring_entity",
		"organisation_unit", "financial_year", "status", "decision", "task_token",
		"record_version", "fixture_namespace",
	},
	"Departmental Plan Validation Decision": {
		"decision_reference", "task", "submission", "decision", "classifications",
		"issues", "actor", "authority_snapshot", "decided_at",
		"command_idempotency_key", "fixture_namespace",
	},
	"Annual Plan": {
		"plan_reference", "title", "pe_fy_context", "procuring_entity",
		"financial_year", "active_version", "open_successor_version", "record_version",
		"fixture_namespace",
	},
	"Annual Plan Version": {
		"version_reference", "annual_plan", "version_number", "based_on_version",
		"correction_of_plan_version", "version_status", "change_reason",
		"submitted_snapshot", "snapshot_hash", "submitted_by_user", "submitted_at",
		"activated_at", "record_version", "fixture_namespace",
	},
	"Annual Plan Item": {
		"plan_item_id", "plan_version", "title", "description", "strategic_objective",
		"strategy_plan", "strategy_plan_version", "objective_path", "requirement_type",
		"procurement_method", "aggregation_reason", "invitation_date",
		"bid_opening_date", "evaluation_completion_date", "award_approval_date",
		"award_notification_date", "contract_signing_date", "delivery_completion_date",
		"item_state", "finance_state", "record_version", "fixture_namespace",
	},
	"Plan Source Allocation": {
		"allocation_id", "plan_item", "plan_item_id", "plan_version", "dpp_entry",
		"source_origin", "need", "need_version", "organisation_unit", "quantity",
		"unit", "required_by_date", "budget_line", "indicative_amount",
		"allocation_state", "fixture_namespace",
	},
	"Plan Finance Task": {
		"task_reference", "plan_item", "plan_item_id", "plan_version",
		"procuring_entity", "source_set_hash", "required_amount", "status", "decision",
		"task_token", "record_version", "fixture_namespace",
	},
	"Plan Finance Decision": {
		"decision_reference", "task", "decision", "return_reason", "actor",
		"authority_snapshot", "decided_at", "command_idempotency_key",
		"fixture_namespace",
	},
	"Plan Reservation Reference": {
		"finance_decision", "plan_item", "plan_item_id", "allocation", "reservation",
		"budget_line", "amount", "release_reference", "release_correlation",
		"fixture_namespace",
	},
	"Plan Governance Task": {
		"task_reference", "annual_plan", "plan_version", "stage", "capacity",
		"procuring_entity", "status", "decision", "task_token", "record_version",
		"fixture_namespace",
	},
	"Plan Governance Decision": {
		"decision_reference", "task", "plan_version", "stage", "decision", "capacity",
		"resolution_reference", "return_reason", "actor", "authority_snapshot",
		"decided_at", "command_idempotency_key", "fixture_namespace",
	},
	"Annual Plan Publication": {
		"publication_reference", "plan_version", "destination", "attempt_number",
		"result", "payload_hash", "external_reference", "attempted_at",
		"acknowledged_at", "fixture_namespace",
	},
	"Annual Plan Publication Destination": {
		"destination_id", "title", "adapter", "active", "fixture_namespace",
	},
}

CORE_CATALOGUES = {
	"Requirement Type": {"title", "status", "fixture_namespace"},
	"Procurement Method": {"title", "status", "fixture_namespace"},
}

# Added in Phase 2: the §8.2 idempotency store (decision log D-journal note).
EXPECTED_FIELDS["Planning Command Journal"] = {
	"idempotency_key", "command", "document_type", "document_name",
	"request_fingerprint", "actor", "result", "occurred_at", "fixture_namespace",
}

# Added in Phase 10 (Slice H): the §7.4 drawdown ledger — authoritative
# Requisition drawdown references consumed from the owning module.
EXPECTED_FIELDS["Plan Drawdown Reference"] = {
	"plan_item", "plan_item_id", "allocation", "requisition_reference",
	"requesting_org_unit", "quantity", "amount", "drawdown_state",
	"reversal_reference", "record_version", "fixture_namespace",
}

LEGACY_DOCTYPES = (
	"Procurement Plan", "Procurement Plan Version", "Procurement Plan Item",
	"Procurement Plan Item Version", "Plan Need Allocation", "Plan Decision",
	"Plan Validation Result", "Planning Handoff Snapshot", "Publication Event",
)

# §1.1 removed-concept tokens. Each is specific enough not to collide with a
# permitted identifier; this test file itself is excluded from the scan.
PROHIBITED_TOKENS = (
	"pvc_snapshot",
	"lotting_decision",
	"expected_lot_count",
	"recommended_method",
	"method_basis",
	"multi_year_justification",
	"annual_funding_schedule",
	"preference_reservation_scheme",
	"schedule_change_reason",
	"ms_invitation_published",
	"Plan Need Allocation",
	"Demand Funding Allocation",
	"add_demand_to_plan",
	"list_eligible_demands",
	"planning_permissions",
	"Operational Scope Assignment",
	"require_capability",
)

SCAN_DIRS = ("doctype", "services", "seeds", "tests", "page")  # page/ added in Phase 3 (D10)

UNIQUE_INDEXES = {
	("tabDepartmental Plan", "pln_uniq_dpp_root"),
	("tabDepartmental Plan Version", "pln_uniq_dpp_version"),
	("tabDepartmental Plan Entry", "pln_uniq_entry_id_per_version"),
	("tabAnnual Plan Version", "pln_uniq_plan_version"),
	("tabAnnual Plan Item", "pln_uniq_item_per_version"),
	("tabPlan Source Allocation", "pln_uniq_alloc_per_version"),
	# invariant 7 (one accepted DPP entry allocated at most once per Plan
	# Version) is deliberately NOT a DB unique — see
	# pln_chg_001_v12_drop_reformable_allocation_unique: §4.10 requires a
	# Released allocation to stop blocking re-formation, which a plain
	# composite unique cannot express on MariaDB. `FormPlanItems` row-locks
	# the Annual Plan Version before creating any allocation instead.
}


class TestPlanningV12Schema(IntegrationTestCase):
	def test_every_v12_doctype_has_exactly_its_allow_listed_fields(self):
		for doctype, expected in {**EXPECTED_FIELDS, **CORE_CATALOGUES}.items():
			self.assertTrue(
				frappe.db.exists("DocType", doctype), f"{doctype} is missing"
			)
			meta = frappe.get_meta(doctype)
			actual = {
				f.fieldname
				for f in meta.fields
				if f.fieldtype not in ("Section Break", "Column Break", "Tab Break")
			}
			self.assertEqual(
				actual, expected,
				f"{doctype}: unexpected={sorted(actual - expected)} "
				f"missing={sorted(expected - actual)}",
			)

	def test_legacy_planning_doctypes_are_gone(self):
		for doctype in LEGACY_DOCTYPES:
			self.assertFalse(
				frappe.db.exists("DocType", doctype),
				f"legacy doctype {doctype} still exists",
			)
			self.assertFalse(
				frappe.db.sql(
					"""select 1 from information_schema.tables
					where table_schema = database() and table_name = %s""",
					(f"tab{doctype}",),
				),
				f"legacy table tab{doctype} still exists",
			)

	def test_no_removed_concept_token_in_module_sources(self):
		this_file = os.path.abspath(__file__)
		hits: list[str] = []
		scan_files = [os.path.join(MODULE_DIR, "api.py")]
		for sub in SCAN_DIRS:
			for root, _dirs, files in os.walk(os.path.join(MODULE_DIR, sub)):
				if "__pycache__" in root:
					continue
				scan_files.extend(
					os.path.join(root, f)
					for f in files
					if f.endswith((".py", ".json"))
				)
		for path in scan_files:
			if os.path.abspath(path) == this_file:
				continue
			text = open(path, encoding="utf-8").read()
			for token in PROHIBITED_TOKENS:
				if token in text:
					hits.append(f"{os.path.relpath(path, MODULE_DIR)}: {token}")
		self.assertEqual(hits, [], "removed-concept tokens found: " + "; ".join(hits))

	def test_composite_unique_indexes_exist(self):
		rows = frappe.db.sql(
			"""select table_name, index_name from information_schema.statistics
			where table_schema = database() and index_name like 'pln_uniq%%'
			group by table_name, index_name"""
		)
		self.assertEqual(UNIQUE_INDEXES - {tuple(r) for r in rows}, set())

	def test_dpp_root_uniqueness_rejects_a_duplicate(self):
		# "the first row on the site" rather than a dedicated fixture: fragile
		# by design (any PE Fiscal Year Context/Organisation Unit will do to
		# prove the DB constraint), but by Phase 6 other slices' fixtures
		# populate real Departmental Plan rows against exactly this kind of
		# row — clear this scope's own residue first so only *this* pair's
		# uniqueness is under test, not leftover fixture state.
		ctx = frappe.get_all("PE Fiscal Year Context", limit=1, pluck="name")
		ou = frappe.get_all("Organisation Unit", limit=1, pluck="name")
		if not ctx or not ou:
			self.skipTest("no PE Fiscal Year Context / Organisation Unit on this site")
		ctx_doc = frappe.get_doc("PE Fiscal Year Context", ctx[0])
		pe = ctx_doc.get("procuring_entity")
		fy = ctx_doc.get("financial_year") or ctx_doc.get("fiscal_year")
		frappe.db.delete("Departmental Plan", {"pe_fy_context": ctx[0], "organisation_unit": ou[0]})
		fields = {
			"doctype": "Departmental Plan",
			"pe_fy_context": ctx[0],
			"procuring_entity": pe,
			"organisation_unit": ou[0],
			"financial_year": fy,
			"current_state": "Draft",
			"record_version": 0,
			"fixture_namespace": "KENTENDER_TEST",
		}
		first = frappe.get_doc(dict(fields, dpp_reference="DPP-SCHEMA-TEST-001"))
		first.insert(ignore_permissions=True)
		self.addCleanup(frappe.db.delete, "Departmental Plan", {"name": first.name})
		second = frappe.get_doc(dict(fields, dpp_reference="DPP-SCHEMA-TEST-002"))
		with self.assertRaises(Exception) as caught:
			second.insert(ignore_permissions=True)
		self.assertIn("Duplicate", str(caught.exception))

	def test_controllers_are_thin(self):
		"""No doctype controller may exceed shape validation — a crude but
		effective ceiling: none may import another module's services or exceed
		80 lines."""
		doctype_dir = os.path.join(MODULE_DIR, "doctype")
		for root, _dirs, files in os.walk(doctype_dir):
			if "__pycache__" in root:
				continue
			for f in files:
				if not f.endswith(".py") or f == "__init__.py":
					continue
				path = os.path.join(root, f)
				lines = open(path, encoding="utf-8").read().splitlines()
				self.assertLessEqual(
					len(lines), 80, f"{f} exceeds the thin-controller ceiling"
				)
				service_imports = [
					line for line in lines
					if line.strip().startswith(("import ", "from "))
					and ".services" in line
				]
				self.assertEqual(
					service_imports, [],
					f"{f} imports a services module — business rules belong in "
					"services, called by commands, not controllers",
				)
