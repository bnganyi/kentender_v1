"""Generate Departmental Needs records through Frappe's DocType lifecycle.

Schemas follow NDS-CHG-001 v1.6 §4. Coarse DocType permissions are declared
on each DocType's checked-in JSON; business authority is enforced per
command through the AUTH-ADR-001 v1.6 resolver in
`departmental_needs/services/permissions.py` — no Frappe User Permission,
capability or scope-assignment store (§6, §16.4). This generator only
bootstraps a fresh environment (NDS-AC-032).

Retired by v1.1 §1.1 and removed here: `Departmental Need Item` (one Need is
one requirement), `Departmental Need Attachment` (no decision requires a
document) and `Departmental Need Review` (superseded by
`Departmental Need Decision`). See patch
`nds_chg_001_v11_drop_retired_need_doctypes`.

Retired by v1.6 and removed here: `Needs Intake Window` (replaced by two
namespaced fields on ERPNext's `Fiscal Year`, owned by Configuration &
Governance) and the `procuring_entity` field on every doctype below (the
site is implicitly one Procuring Entity). See patch
`nds_chg_001_v16_drop_needs_intake_window`.
"""

from __future__ import annotations

import frappe


def _f(label: str, fieldname: str, fieldtype: str = "Data", **extra):
	return {"label": label, "fieldname": fieldname, "fieldtype": fieldtype, **extra}


# §6 native roles. Business authority is enforced per command in
# `departmental_needs/services/permissions.py` using these roles plus User
# Permission scope; no capability or scope-assignment store is consulted.
#
# Permissions are declared per doctype rather than as one blanket set, because
# §6 grants materially different work to each role and NDS-AC-022 requires the
# match to be exact. Budget Officer and Accounting Officer appear nowhere
# (NDS-AC-023, §17). No role receives `delete` on a business record: §13 keeps
# Needs, versions and decisions permanently, and the controllers block deletion.
ADMIN_PERMISSIONS: list[dict] = [
	{"role": "System Manager", "read": 1, "write": 1, "create": 1},
	{"role": "Administrator", "read": 1, "write": 1, "create": 1},
]

# Read-only oversight: §6 gives the Auditor no business mutation, and the
# Planner reads current accepted versions through the typed source contract.
OVERSIGHT_READ: list[dict] = [
	{"role": "Procurement Planner", "read": 1},
	{"role": "Auditor", "read": 1},
]

# The Need, its versions and its withdrawal requests: the Author creates and
# edits their own; the HoD decides. Row-level ownership and PE/OU/FY scope are
# applied by `services/permissions.py` and User Permission, not here.
NEED_PERMISSIONS: list[dict] = [
	*ADMIN_PERMISSIONS,
	{"role": "Departmental Author", "read": 1, "write": 1, "create": 1},
	{"role": "Head of User Department", "read": 1, "write": 1},
	*OVERSIGHT_READ,
]

# §4.4 — the departmental decision queue. The Planner has no Need decision
# (§6, NDS-AC-043), so the task is not readable by that role at all.
REVIEW_TASK_PERMISSIONS: list[dict] = [
	*ADMIN_PERMISSIONS,
	{"role": "Departmental Author", "read": 1},
	{"role": "Head of User Department", "read": 1, "write": 1},
	{"role": "Auditor", "read": 1},
]

# §4.5 — an immutable record created only by a successful command. Nothing
# outside the command layer writes it, so no business role gets write.
DECISION_PERMISSIONS: list[dict] = [
	{"role": "System Manager", "read": 1},
	{"role": "Administrator", "read": 1},
	{"role": "Departmental Author", "read": 1},
	{"role": "Head of User Department", "read": 1},
	*OVERSIGHT_READ,
]

# One explicit mapping so a new doctype cannot silently inherit the wrong set.
PERMISSIONS_BY_DOCTYPE: dict[str, list[dict]] = {
	"Departmental Need": NEED_PERMISSIONS,
	"Departmental Need Version": NEED_PERMISSIONS,
	"Need Withdrawal Request": NEED_PERMISSIONS,
	"Departmental Need Review Task": REVIEW_TASK_PERMISSIONS,
	"Departmental Need Decision": DECISION_PERMISSIONS,
}

STATES = "Draft\nSubmitted\nReturned\nAccepted for planning\nNot taken forward\nWithdrawn"
VERSION_STATES = "Draft\nSubmitted\nReturned\nAccepted\nNot taken forward\nWithdrawn\nSuperseded"

SCHEMAS = (
	{
		"name": "Departmental Need",
		"module": "Departmental Needs",
		"autoname": "field:need_reference",
		"search_fields": "need_reference",
		"fields": [
			_f("Need Reference", "need_reference", reqd=1, unique=1, read_only=1, in_list_view=1),
			_f("Organisation Unit", "organisation_unit", "Link", options="Organisation Unit", reqd=1, read_only=1, search_index=1),
			_f("Financial Year", "financial_year", "Link", options="Fiscal Year", reqd=1, read_only=1, search_index=1),
			_f("Current State", "current_state", "Select", options=STATES, default="Draft", reqd=1, read_only=1, in_list_view=1, search_index=1),
			_f("Current Version", "current_version", "Link", options="Departmental Need Version", read_only=1, search_index=1),
			_f("Current Accepted Version", "current_accepted_version", "Link", options="Departmental Need Version", read_only=1, search_index=1),
			_f("Record Version", "record_version", "Int", default="0", reqd=1, read_only=1),
			_f("Fixture Namespace", "fixture_namespace", hidden=1, read_only=1, search_index=1),
		],
	},
	{
		"name": "Departmental Need Version",
		"module": "Departmental Needs",
		"autoname": "field:need_version_id",
		"title_field": "title",
		"search_fields": "need_version_id,title",
		"fields": [
			_f("Need Version ID", "need_version_id", reqd=1, unique=1, read_only=1, in_list_view=1),
			_f("Departmental Need", "departmental_need", "Link", options="Departmental Need", reqd=1, read_only=1, search_index=1),
			_f("Version Number", "version_number", "Int", reqd=1, read_only=1, in_list_view=1),
			_f("Based On Version", "based_on_version", "Link", options="Departmental Need Version", read_only=1),
			_f("Version Status", "version_status", "Select", options=VERSION_STATES, default="Draft", reqd=1, read_only=1, in_list_view=1, search_index=1),
			_f("Title", "title", reqd=1, in_list_view=1),
			_f("Description", "description", "Text"),
			_f("Expected Operational Result", "expected_operational_result", "Text"),
			_f("Indicative Quantity", "indicative_quantity", "Float", precision="3"),
			_f("Unit", "unit", "Link", options="UOM"),
			_f("Required By", "required_by_date", "Date"),
			_f("Content Hash", "content_hash", read_only=1, search_index=1),
			_f("Fixture Namespace", "fixture_namespace", hidden=1, read_only=1, search_index=1),
		],
	},
	{
		"name": "Departmental Need Review Task",
		"module": "Departmental Needs",
		"autoname": "field:review_task_id",
		"search_fields": "review_task_id,departmental_need",
		"fields": [
			_f("Review Task ID", "review_task_id", reqd=1, unique=1, read_only=1, in_list_view=1),
			_f("Departmental Need", "departmental_need", "Link", options="Departmental Need", reqd=1, read_only=1, search_index=1, in_list_view=1),
			_f("Need Version", "need_version", "Link", options="Departmental Need Version", read_only=1, search_index=1),
			_f("Withdrawal Request", "withdrawal_request", "Link", options="Need Withdrawal Request", read_only=1, search_index=1),
			_f("Task Type", "task_type", "Select", options="Initial acceptance\nSuccessor acceptance\nWithdrawal", reqd=1, read_only=1, in_list_view=1, search_index=1),
			_f("Organisation Unit", "organisation_unit", "Link", options="Organisation Unit", reqd=1, read_only=1, search_index=1),
			_f("Financial Year", "financial_year", "Link", options="Fiscal Year", reqd=1, read_only=1, search_index=1),
			_f("Status", "status", "Select", options="Open\nCompleted\nCancelled", default="Open", reqd=1, read_only=1, in_list_view=1, search_index=1),
			_f("Decision Token", "decision_token", reqd=1, read_only=1),
			_f("Opened At", "opened_at", "Datetime", reqd=1, read_only=1),
			_f("Closed At", "closed_at", "Datetime", read_only=1),
			_f("Fixture Namespace", "fixture_namespace", hidden=1, read_only=1, search_index=1),
		],
	},
	{
		"name": "Need Withdrawal Request",
		"module": "Departmental Needs",
		"autoname": "field:withdrawal_request_id",
		"search_fields": "withdrawal_request_id,departmental_need",
		"fields": [
			_f("Withdrawal Request ID", "withdrawal_request_id", reqd=1, unique=1, read_only=1, in_list_view=1),
			_f("Departmental Need", "departmental_need", "Link", options="Departmental Need", reqd=1, read_only=1, search_index=1, in_list_view=1),
			_f("Accepted Version", "accepted_version", "Link", options="Departmental Need Version", reqd=1, read_only=1, search_index=1),
			_f("Requested By", "requested_by", "Link", options="User", reqd=1, read_only=1, search_index=1),
			_f("Reason", "reason", "Small Text", reqd=1, read_only=1),
			_f("Status", "status", "Select", options="Awaiting review\nAwaiting planning clearance\nApproved\nDeclined", default="Awaiting review", reqd=1, read_only=1, in_list_view=1, search_index=1),
			_f("Planning Dependency Version", "planning_dependency_version", read_only=1),
			_f("Record Version", "record_version", "Int", default="0", reqd=1, read_only=1),
			_f("Fixture Namespace", "fixture_namespace", hidden=1, read_only=1, search_index=1),
		],
	},
	{
		"name": "Departmental Need Decision",
		"module": "Departmental Needs",
		"autoname": "field:decision_id",
		"search_fields": "decision_id,departmental_need",
		"fields": [
			_f("Decision ID", "decision_id", reqd=1, unique=1, read_only=1, in_list_view=1),
			_f("Departmental Need", "departmental_need", "Link", options="Departmental Need", reqd=1, read_only=1, search_index=1),
			_f("Need Version", "need_version", "Link", options="Departmental Need Version", read_only=1, search_index=1),
			_f("Withdrawal Request", "withdrawal_request", "Link", options="Need Withdrawal Request", read_only=1, search_index=1),
			_f("Action", "action", "Select", options="Create\nSave draft\nSubmit\nResubmit\nReturn for correction\nAccept for planning\nDo not take forward\nWithdraw\nCreate successor\nSave successor\nCancel successor\nSubmit successor\nReturn successor\nAccept successor\nDecline successor\nRequest withdrawal\nEvaluate withdrawal\nRe-evaluate withdrawal\nApprove withdrawal\nDecline withdrawal", reqd=1, read_only=1, in_list_view=1, search_index=1),
			_f("Actor", "actor", "Link", options="User", reqd=1, read_only=1, search_index=1),
			_f("Effective Assignment", "effective_assignment", read_only=1),
			_f("Scope", "scope", read_only=1),
			_f("Review Task", "review_task", "Link", options="Departmental Need Review Task", read_only=1),
			_f("Occurred At", "occurred_at", "Datetime", reqd=1, read_only=1),
			_f("Reason", "reason", "Small Text", read_only=1),
			_f("Prior State", "prior_state", reqd=1, read_only=1),
			_f("Result State", "result_state", reqd=1, read_only=1),
			_f("Content Hash", "content_hash", read_only=1),
			_f("Correlation ID", "correlation_id", read_only=1, search_index=1),
			_f("Request ID", "request_id", read_only=1),
			_f("Source IP", "source_ip", read_only=1),
			_f("Session ID", "session_id", read_only=1),
			_f("Before State Hash", "before_state_hash", read_only=1),
			_f("After State Hash", "after_state_hash", read_only=1),
			_f("Idempotency Key", "idempotency_key", reqd=1, unique=1, read_only=1, search_index=1),
			_f("Request Fingerprint", "request_fingerprint", read_only=1),
			_f("Fixture Namespace", "fixture_namespace", hidden=1, read_only=1, search_index=1),
		],
	},
	# "Plan Need Allocation" was declared here until PLN-CHG-001 v1.2 Phase 1:
	# the v1.2 Planning model replaced it with Plan Source Allocation, and the
	# legacy doctype was dropped by pln_chg_001_v12_drop_legacy_planning_doctypes.
)


def generate() -> list[str]:
	"""Create and export all greenfield DocTypes idempotently."""
	frappe.flags.allow_doctype_export = True
	if not frappe.db.exists("Module Def", "Departmental Needs"):
		frappe.get_doc(
			{
				"doctype": "Module Def",
				"module_name": "Departmental Needs",
				"app_name": "kentender_procurement",
			}
		).insert(ignore_permissions=True)
	created: list[str] = []
	for schema in SCHEMAS:
		if frappe.db.exists("DocType", schema["name"]):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "DocType",
				"custom": 0,
				"engine": "InnoDB",
				"track_changes": 1,
				"allow_rename": 0,
				"permissions": PERMISSIONS_BY_DOCTYPE[schema["name"]],
				**schema,
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc.name)
	frappe.db.commit()
	return created
