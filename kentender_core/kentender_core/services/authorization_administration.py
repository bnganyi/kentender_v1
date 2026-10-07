"""Read-only AUTH-G04 administration projections (retired authority store).

AUD-XC-026 / AUTH-ADR-001 §11.3 step 9, §11.5: the Operational Scope
Assignment / Capability Profile engine no longer authorises anything and no
longer takes writes. Its commands (create or change an assignment, revise or
activate a routing rule, queue memberships, delegations) were removed; the
records that exist are kept for the migration evidence and can be inspected
here until the §11.3 step 11 clean-up. Responsibilities are assigned only
through `responsibility_administration`.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import format_datetime, now_datetime

ADMIN_ROLES = {"System Manager", "System Access Administrator"}


def require_access_administrator(user: str | None = None) -> str:
	actor = user or frappe.session.user
	if actor != "Administrator" and not ADMIN_ROLES.intersection(frappe.get_roles(actor)):
		frappe.throw(_("You are not permitted to manage operational access."), frappe.PermissionError, title="AUTH_ADMIN_PERMISSION_DENIED")
	return actor


def get_user_operational_access(target_user: str, *, user: str | None = None) -> dict:
	require_access_administrator(user)
	account = frappe.db.get_value("User", target_user, ["full_name", "enabled"], as_dict=True)
	if not account:
		frappe.throw(_("User not found."), title="AUTH_USER_NOT_FOUND")
	assignments = []
	for row in frappe.get_all("Operational Scope Assignment", filters={"user_id": target_user}, fields=["name", "assignment_id", "capability_profile_id", "procuring_entity_id", "organisation_unit_id", "include_descendants", "resource_scope_type", "resource_scope_id", "effective_from", "effective_to", "status", "concurrency_token"], order_by="effective_from desc"):
		assignments.append({
			**row,
			"role": frappe.db.get_value("Capability Profile", row.capability_profile_id, "profile_name") or row.capability_profile_id,
			"procuring_entity": frappe.db.get_value("Procuring Entity", row.procuring_entity_id, "entity_name") or row.procuring_entity_id,
			"organisation_scope": ("All assigned units and descendants" if row.organisation_unit_id and row.include_descendants else row.organisation_unit_id or "Entity-wide"),
			"resource_scope": f"{row.resource_scope_type}: {row.resource_scope_id}" if row.resource_scope_type else "All admitted resources",
			"effective_period": f"{format_datetime(row.effective_from, 'dd MMMM yyyy')} — {format_datetime(row.effective_to, 'dd MMMM yyyy') if row.effective_to else 'No end date'}",
		})
	return {
		"user": target_user, "full_name": account.full_name or target_user, "account_status": "Active" if account.enabled else "Disabled",
		"as_at": format_datetime(now_datetime(), "dd MMMM yyyy"), "assignments": assignments,
		"active_assignments": sum(row["status"] == "Active" for row in assignments),
		"open_tasks": frappe.db.count("Workflow Task", {"assigned_user_id": target_user, "state": "Open"}),
		"sod_issues": 0,
	}


def get_routing_rule_detail(name: str, *, user: str | None = None) -> dict:
	require_access_administrator(user)
	if not frappe.db.exists("Workflow Routing Rule", name):
		name = frappe.db.get_value("Workflow Routing Rule", {"routing_rule_id": name, "status": "Active"}, "name") or name
	doc = frappe.get_doc("Workflow Routing Rule", name)
	assignee = doc.assignee_user_id or doc.queue_id
	return {**doc.as_dict(), "assignee": assignee, "procuring_entity": frappe.db.get_value("Procuring Entity", doc.procuring_entity_id, "entity_name") or doc.procuring_entity_id, "eligible": bool(assignee), "eligibility_copy": f"{assignee} has an active assignment covering the required capability and governed scope." if assignee else "No eligible assignee is configured."}
