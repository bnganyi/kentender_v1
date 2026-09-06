# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.5 §7/§18.1 capability wiring on AUTH-ADR-001 **v1.6**
(CU-301): one site is one Procuring Entity, and the two Strategy governance
roles are Site-wide business responsibilities resolved through
`kentender_core.services.authorization` — no capability strings, no
ResourceContext, no User-Permission scope checks.

v1.5 collapsed the 3-role model onto 2 (Author/Approver). Separation of
duties stays a version-specific, domain-owned rule — "the author of a
submitted version cannot approve or return it, even if that user also holds
Strategy Approver" (§13.4/§18.1) — enforced here via the version's own audit
trail, never via a general capability-pair engine.

v1.6 semantics callers should know:
- Technical users (Administrator/System Manager) may READ without an
  assignment but hold no business authority: authoring and approving require
  an Enabled `Strategy Author` / `Strategy Approver` assignment like anyone
  else (AUTH-AC-018). The old System-Manager-can-do-everything behaviour is
  gone by design.
- Both roles are Site-wide (registry §20 note): no Organisation Unit narrows
  them; any departmental narrowing stays a record-ownership check inside
  Strategy, not an authorization concern.
"""

from __future__ import annotations

import frappe

from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record
from kentender_core.services.responsibility_errors import fail
from kentender_strategy.services.strategy_audit import list_events

# Retained as the module's internal action vocabulary; each maps onto one
# registered Site-wide business role.
CAP_AUTHOR = "strategy.plan_version.author"
CAP_APPROVE = "strategy.plan_version.approve"

ROLE_STRATEGY_AUTHOR = "Strategy Author"
ROLE_STRATEGY_APPROVER = "Strategy Approver"

STRATEGY_GOVERNANCE_ROLES = (
	ROLE_STRATEGY_AUTHOR,
	ROLE_STRATEGY_APPROVER,
)

_BUSINESS_ROLE_FOR_CAPABILITY = {
	CAP_AUTHOR: ROLE_STRATEGY_AUTHOR,
	CAP_APPROVE: ROLE_STRATEGY_APPROVER,
}


def ensure_strategy_governance_roles() -> dict:
	"""Idempotent: create the 2 STR-CHG-001 v1.5 §7 Frappe Roles (the
	registry's projections for the two business responsibilities).

	Does not grant any Role to a specific user — under v1.6 a grant flows
	only through the User Responsibility Assignment administration command,
	which projects the Frappe Role itself."""
	created = {"roles": [], "sod_rules": []}

	for role in STRATEGY_GOVERNANCE_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)
			created["roles"].append(role)

	return created


def _business_role(capability: str) -> str:
	role = _BUSINESS_ROLE_FOR_CAPABILITY.get(capability)
	if not role:
		fail("AUTH_CONFIGURATION_INVALID")
	return role


def _submitted_by(version_name: str) -> str | None:
	"""The user who performed this version's own "Submit for approval" —
	read from its audit trail (§18.1: "the version's audit history for the
	no-self-approval check"), not a stored field."""
	for event in list_events("Strategic Plan Version", version_name):
		if event.get("action") == "Submit for approval":
			return event.get("performed_by")
	return None


def _blocked_by_self_approval(user: str, capability: str, version_name: str) -> bool:
	"""§6.2/§13.4/§18.1: "The author cannot approve the same version" / "even
	if that user also holds the Strategy Approver role" — a same-version
	self-check, not a general capability-pair rule."""
	if capability != CAP_APPROVE:
		return False
	return _submitted_by(version_name) == user


def _version_name(version) -> str:
	return version if isinstance(version, str) else version.name


def require_plan_version_capability(
	user: str, capability: str, version, *, correlation_id: str = ""
):
	"""Raise the applicable §10 error unless `user` holds the Enabled
	Site-wide assignment for this capability's business role — and, for
	Approve/Return, is not the version's own submitter."""
	if _blocked_by_self_approval(user, capability, _version_name(version)):
		fail("AUTH_SEGREGATION_BLOCKED")
	decision = authorise_record(
		user=user,
		business_role=_business_role(capability),
		organisation_unit="",
		purpose=PURPOSE_COMMAND,
	)
	if not decision.allowed:
		fail(decision.reason_code or "AUTH_RESPONSIBILITY_REQUIRED")
	return decision.assignment


def has_plan_version_capability(user: str, capability: str, version) -> bool:
	if _blocked_by_self_approval(user, capability, _version_name(version)):
		return False
	return authorise_record(
		user=user,
		business_role=_business_role(capability),
		organisation_unit="",
		purpose=PURPOSE_COMMAND,
	).allowed


def require_plan_create_capability(user: str):
	"""Creating a brand-new Strategic Plan requires the Site-wide Strategy
	Author responsibility (one site = one PE; no entity parameter exists).
	Returns the exercised assignment for the audit trail (§13)."""
	decision = authorise_record(
		user=user,
		business_role=ROLE_STRATEGY_AUTHOR,
		organisation_unit="",
		purpose=PURPOSE_COMMAND,
	)
	if not decision.allowed:
		fail(decision.reason_code or "AUTH_RESPONSIBILITY_REQUIRED")
	return decision.assignment


def business_role_for_capability(capability: str) -> str:
	"""Public name of the capability → business-role mapping, for audit."""
	return _business_role(capability)


def assignment_id(assignment) -> str | None:
	"""The `User Responsibility Assignment` name behind an authorization
	decision, or None for a technical read that exercised no assignment."""
	return getattr(assignment, "name", None) or None


def has_plan_create_capability(user: str) -> bool:
	return authorise_record(
		user=user,
		business_role=ROLE_STRATEGY_AUTHOR,
		organisation_unit="",
		purpose=PURPOSE_COMMAND,
	).allowed


def holds_approver_responsibility(user: str) -> bool:
	"""An Enabled Site-wide Strategy Approver assignment, irrespective of any
	per-version self-approval block — the §12.4 gate for opening an
	approval task at all."""
	return authorise_record(
		user=user,
		business_role=ROLE_STRATEGY_APPROVER,
		organisation_unit="",
		purpose=PURPOSE_COMMAND,
	).allowed
