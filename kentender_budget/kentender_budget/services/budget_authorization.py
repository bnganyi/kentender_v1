# Copyright (c) 2026, KenTender and contributors
"""BUD-CHG-001 v1.2 §7/§17.1 capability wiring, on AUTH-ADR-001's native
Frappe Role + User Permission engine (kentender_core.services.authorization_native)
— not kentender_core's older Operational Scope Assignment/Workflow Task +
Workflow Routing Rule task-queue engine, and not a "My Work" queue entry.

v1.2 collapses the 3-role/3-capability model (Officer/Reviewer/Activation
Authority) onto 2 roles/capabilities (Officer/Approver), mirroring Strategy's
STR-CHG-001 v1.5 collapse exactly (kentender_strategy.services.strategy_authorization).
Segregation of duties is a single same-version self-check, not a pairwise
rule table: "the submitting Officer cannot approve the same version, even if
that user also holds Budget Approver" (§6.2/§12.5). Enforced directly here
via the version's own audit trail (Budget Audit Event — the FundingLedgerEvent
object), not kentender_core's general capability-pair SoD machinery.
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_core.services.authorization_native import evaluate_role_capability, require_role_capability
from kentender_core.services.authorization_policy import ResourceContext

CAP_LIST = "budget.list"
CAP_VIEW = "budget.view"
CAP_CREATE = "budget.create"
CAP_EDIT = "budget.edit"
CAP_SUBMIT = "budget.submit"
CAP_RETURN = "budget.return"
CAP_APPROVE = "budget.approve"
CAP_EXPORT = "budget.export"

# BUD-CHG-001 v1.2 §7: only 2 Budget Version workflow roles remain. Budget
# Reviewer is removed outright (not renamed, not aliased). Budget Activation
# Authority is renamed to Budget Approver — same responsibility, new name.
# Budget Viewer is intentionally not part of this governance-role tuple —
# read access stays a plain Frappe Role driving ordinary DocType permissions,
# outside the capability engine entirely (same as Strategy Viewer).
ROLE_BUDGET_OFFICER = "Budget Officer"
ROLE_BUDGET_APPROVER = "Budget Approver"

BUDGET_GOVERNANCE_ROLES = (
	ROLE_BUDGET_OFFICER,
	ROLE_BUDGET_APPROVER,
)


def ensure_budget_governance_roles() -> dict:
	"""Idempotent: create the 2 BUD-CHG-001 v1.2 §7 Frappe Roles. No
	Separation of Duties Rule is seeded any more — with only 2 capabilities
	the only remaining rule is the direct same-version self-check in
	`_blocked_by_self_approval` below, not a capability-pair rule.

	Does not grant any Role to a specific user — provisioning real named
	actors is a separate seed-contract concern (§15.2)."""
	created = {"roles": []}

	for role in BUDGET_GOVERNANCE_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)
			created["roles"].append(role)

	return created


def resource_context_for_version(version) -> ResourceContext:
	"""Build a ResourceContext for one Budget Version, resolving its owning
	Budget for Procuring Entity scope."""
	if isinstance(version, str):
		version = frappe.get_doc("Budget Version", version)
	procuring_entity = frappe.db.get_value("Budget", version.budget, "procuring_entity")
	return ResourceContext(
		resource_type="Budget Version",
		resource_id=version.name,
		procuring_entity_id=procuring_entity or "",
		state=version.status or "",
	)


def _submitted_by(version_name: str) -> str | None:
	"""The user who performed this version's own "Submit for review" — read
	from its ledger trail (§17.1: "the version's own submission audit
	event"), not a stored field."""
	event = frappe.db.get_value(
		"Budget Audit Event",
		{"budget_version": version_name, "event_type": "Budget version submitted"},
		["actor"],
		order_by="event_at asc",
	)
	return event or None


def _blocked_by_self_approval(user: str, capability: str, version_name: str) -> bool:
	"""§6.2/§12.5: "the submitting Officer cannot approve the same version" —
	a same-version self-check, not a general capability-pair rule. Return is
	not restricted by self-submission (only Approve is)."""
	if capability != CAP_APPROVE:
		return False
	return _submitted_by(version_name) == user


def require_budget_version_capability(
	user: str, capability: str, version, *, correlation_id: str = ""
) -> None:
	if isinstance(version, str):
		version_name = version
	else:
		version_name = version.name
	resource = resource_context_for_version(version)
	require_role_capability(
		user,
		capability,
		resource,
		sod_blocked=_blocked_by_self_approval(user, capability, version_name),
	)


def has_budget_version_capability(user: str, capability: str, version) -> bool:
	if isinstance(version, str):
		version_name = version
	else:
		version_name = version.name
	if _blocked_by_self_approval(user, capability, version_name):
		return False
	return evaluate_role_capability(user, capability, resource_context_for_version(version))[0]


def require_budget_create_capability(user: str, procuring_entity_id: str) -> None:
	"""Creating a brand-new Budget: the PE already exists at creation time, so
	a normal Role+PE-scope check applies directly (no bootstrap workaround
	needed, same as Strategy's `require_plan_create_capability`)."""
	require_role_capability(
		user,
		CAP_CREATE,
		ResourceContext(resource_type="Budget", resource_id="", procuring_entity_id=procuring_entity_id),
	)


# AUTH-ADR-001 maps each capability string to exactly one Role (§5.2) — there
# is no single "view" capability shared across Officer/Approver/Viewer/Auditor.
# Read access to a Budget/Version in progress is not itself a workflow action
# (§7: "Read access is not a third Strategy workflow role", mirrored here) —
# it only needs "does this user hold any Budget-related Role with PE scope",
# not a same-version segregation check. `CAP_VIEW` stays reserved for the
# neutral Budget Viewer read surface (§9.1's Active-only reads); this is the
# check every other read contract in this module uses instead.
_READ_ROLES = (ROLE_BUDGET_OFFICER, ROLE_BUDGET_APPROVER, "Budget Viewer", "Auditor")


def require_budget_read_scope(procuring_entity_id: str) -> None:
	user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return
	if not any(role in frappe.get_roles(user) for role in _READ_ROLES):
		frappe.throw(_("Not permitted to view Budget & Funding"), frappe.PermissionError, title="BUDGET_PERMISSION_DENIED")
	pe_scope = set(frappe.get_all("User Permission", filters={"user": user, "allow": "Procuring Entity"}, pluck="for_value"))
	if pe_scope and procuring_entity_id not in pe_scope:
		frappe.throw(_("Not permitted for this procuring entity"), frappe.PermissionError, title="BUDGET_PERMISSION_DENIED")


def require_budget_version_read_scope(version) -> None:
	if isinstance(version, str):
		version = frappe.get_doc("Budget Version", version)
	procuring_entity = frappe.db.get_value("Budget", version.budget, "procuring_entity")
	require_budget_read_scope(procuring_entity or "")
