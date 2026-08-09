# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-PERM — Demands MVP-1 roles, scope, segregation, and decision authority."""

from __future__ import annotations

import frappe
from frappe import _

ROLE_REQUESTER = "Requester"
ROLE_BUSINESS = "Business Approver"
ROLE_PAA = "Procurement Approval Authority"
ROLE_BUDGET = "Budget Officer"
ROLE_PLANNING = "Planning Officer"
ROLE_VIEWER = "Demand Viewer"
ROLE_AUDITOR = "Auditor"

ALL_DEMAND_ROLES = (
	ROLE_REQUESTER,
	ROLE_BUSINESS,
	ROLE_PAA,
	ROLE_BUDGET,
	ROLE_PLANNING,
	ROLE_VIEWER,
	ROLE_AUDITOR,
)

# Roles that may perform lifecycle decisions (DIA-AC-013: admin alone is not enough).
OPERATIONAL_DECISION_ROLES = (
	ROLE_REQUESTER,
	ROLE_BUSINESS,
	ROLE_PAA,
	ROLE_BUDGET,
)

ERR_PERMISSION = "DEMAND_PERMISSION_DENIED"
ERR_SCOPE = "DEMAND_SCOPE_DENIED"
ERR_SEGREGATION = "DEMAND_SEGREGATION_VIOLATION"
ERR_ADMIN_ROLE = "DEMAND_OPERATIONAL_ROLE_REQUIRED"
ERR_STALE = "DEMAND_STALE_VERSION"


def ensure_demand_roles() -> None:
	for role in ALL_DEMAND_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def throw_demand_error(
	code: str,
	message: str,
	*,
	exc: type[Exception] | None = None,
	issue: str | None = None,
	owner: str | None = None,
	action: str | None = None,
) -> None:
	"""Raise with stable code prefix (DIA-NFR-009) + optional business fields (DIA-NFR-008)."""
	issue_text = (issue or message or "").strip()
	owner_text = (owner or "").strip()
	action_text = (action or "").strip()
	frappe.flags.demand_error = {
		"code": code,
		"issue": issue_text,
		"owner": owner_text,
		"action": action_text,
		"message": message,
	}
	parts = [f"{code}: {_(message)}"]
	if owner_text:
		parts.append(f"Owner: {owner_text}")
	if action_text:
		parts.append(f"Action: {action_text}")
	frappe.throw(" | ".join(parts), exc or frappe.ValidationError, title=code)


def operational_roles(user: str | None = None) -> set[str]:
	"""Actual Has Role set — does not inflate System Manager (DIA-AC-013)."""
	user = user or frappe.session.user
	return set(frappe.get_roles(user))


def has_any_operational_role(*roles: str, user: str | None = None) -> bool:
	return bool(operational_roles(user).intersection(roles))


def require_operational_roles(*roles: str, user: str | None = None) -> None:
	"""Require a real operational role; System Manager / Administrator alone fails."""
	if has_any_operational_role(*roles, user=user):
		return
	throw_demand_error(
		ERR_ADMIN_ROLE if _is_admin_only(user) else ERR_PERMISSION,
		"Not permitted for this Demands action",
		exc=frappe.PermissionError,
	)


def _is_admin_only(user: str | None = None) -> bool:
	user = user or frappe.session.user
	roles = operational_roles(user)
	adminish = user == "Administrator" or "System Manager" in roles
	if not adminish:
		return False
	return not roles.intersection(OPERATIONAL_DECISION_ROLES)


def can_read_demand(user: str | None = None) -> bool:
	roles = operational_roles(user)
	if user == "Administrator" or "System Manager" in roles:
		return True
	return bool(roles.intersection(ALL_DEMAND_ROLES))


def can_edit_requester_fields(user: str | None = None) -> bool:
	return has_any_operational_role(ROLE_REQUESTER, user=user)


def can_business_decide(user: str | None = None) -> bool:
	return has_any_operational_role(ROLE_BUSINESS, user=user)


def can_procurement_enrich(user: str | None = None) -> bool:
	return has_any_operational_role(ROLE_PAA, user=user)


def can_confirm_funding(user: str | None = None) -> bool:
	return has_any_operational_role(ROLE_BUDGET, user=user)


def can_final_approve(user: str | None = None) -> bool:
	return has_any_operational_role(ROLE_PAA, user=user)


def can_consume_in_planning(user: str | None = None) -> bool:
	return has_any_operational_role(ROLE_PLANNING, user=user)


def assert_demand_scope(
	*,
	procuring_entity: str | None,
	owner_org_unit: str | None,
	user: str | None = None,
	require_write: bool = False,
) -> None:
	"""Server-side PE + organisation-unit gate (DEM-PERM-002)."""
	from kentender_core.services.org_scope_access import can_access_owned_record

	user = user or frappe.session.user
	if not can_access_owned_record(
		procuring_entity=procuring_entity,
		owner_org_unit=owner_org_unit,
		user=user,
		require_write=require_write,
	):
		throw_demand_error(
			ERR_SCOPE,
			"Not permitted for this organisational scope",
			exc=frappe.PermissionError,
		)


def assert_business_approver_segregation(
	*,
	requester: str | None,
	actor: str | None = None,
	small_entity_exception: bool = False,
) -> None:
	"""DIA-FR-040 / DEM-PERM-005 — Requester ≠ Business Approver on same Demand."""
	actor = actor or frappe.session.user
	if small_entity_exception:
		return
	if requester and actor and requester == actor:
		throw_demand_error(
			ERR_SEGREGATION,
			"Requester cannot act as Business Approver on the same Demand",
			exc=frappe.PermissionError,
		)


# Stage → action → required roles
_STAGE_ACTION_ROLES: dict[tuple[str, str], frozenset[str]] = {
	("Request Preparation", "Submit"): frozenset({ROLE_REQUESTER}),
	("Request Preparation", "Cancel"): frozenset({ROLE_REQUESTER, ROLE_PAA}),
	("Business Review", "Support"): frozenset({ROLE_BUSINESS}),
	("Business Review", "Return"): frozenset({ROLE_BUSINESS}),
	("Business Review", "Reject"): frozenset({ROLE_BUSINESS}),
	("Procurement Enrichment", "Send for budget confirmation"): frozenset({ROLE_PAA}),
	("Procurement Enrichment", "Return"): frozenset({ROLE_PAA}),
	("Procurement Enrichment", "Reject"): frozenset({ROLE_PAA}),
	("Budget Confirmation", "Confirm funding"): frozenset({ROLE_BUDGET}),
	("Budget Confirmation", "Return"): frozenset({ROLE_BUDGET}),
	("Final Approval", "Approve"): frozenset({ROLE_PAA}),
	("Final Approval", "Return"): frozenset({ROLE_PAA}),
	("Final Approval", "Reject"): frozenset({ROLE_PAA}),
	("Final Approval", "Cancel"): frozenset({ROLE_PAA}),
}


def roles_for_stage_action(stage: str, action: str) -> frozenset[str]:
	return _STAGE_ACTION_ROLES.get((stage, action), frozenset())


def assert_can_perform_stage_action(
	stage: str,
	action: str,
	*,
	user: str | None = None,
) -> None:
	allowed = roles_for_stage_action(stage, action)
	if not allowed:
		throw_demand_error(
			ERR_PERMISSION,
			f"No role mapping for action {action!r} at stage {stage!r}",
			exc=frappe.PermissionError,
		)
	require_operational_roles(*allowed, user=user)
