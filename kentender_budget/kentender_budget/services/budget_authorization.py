# Copyright (c) 2026, KenTender and contributors
"""BUD-CHG-001 v1.3 §7/§17.1 capability wiring on AUTH-ADR-001 v1.6 (Phase 4):
one site is one Procuring Entity, and the three Budget governance
responsibilities are Site-wide business responsibilities resolved through
`kentender_core.services.authorization` — no capability strings, no
ResourceContext, no User-Permission scope checks. Mirrors
`kentender_strategy.services.strategy_authorization`'s v1.6 rewrite.

Segregation of duties stays a single same-version self-check, not a pairwise
rule table: "the submitting Budget Officer cannot approve the same version,
even if that user also holds Budget Approver" (§6/§17.1), enforced here from
the version's own submission audit event (Budget Audit Event), never a
stored field or a general capability-pair engine.

Reads are a separate concern from writes (§5.3 vs §5.5 of the ADR): a write
requires an Active site-wide `User Responsibility Assignment`
(`authorise_record`, below); a read is governed by the registered
`permission_query_conditions`/`has_permission` hooks acting on DocPerm plus
the caller's assignments (`kentender_scope_map`, registered in this app's
`hooks.py` — BUD-CHG-001 v1.3 §17.1, AUTH-ADR-001 v1.6 §5.3). Budget's own
`require_budget_read_scope` below exists only to make backend service code
actually invoke those hooks — a raw `frappe.get_doc()` call does not.
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_core.services.authorization import (
	PURPOSE_COMMAND,
	PURPOSE_READ,
	authorise_record,
	is_technical,
)
from kentender_core.services.responsibility_errors import fail

CAP_CREATE = "budget.create"
CAP_EDIT = "budget.edit"
CAP_SUBMIT = "budget.submit"
CAP_RETURN = "budget.return"
CAP_APPROVE = "budget.approve"

# §7 — exactly three Budget business responsibilities, all Site-wide. There
# is no Budget Viewer role in this vocabulary; read access is a DocPerm/
# scope-map concern, never a capability.
ROLE_BUDGET_OFFICER = "Budget Officer"
ROLE_BUDGET_APPROVER = "Budget Approver"
ROLE_FINANCE_CONFIRMATION_OFFICER = "Finance Confirmation Officer"

ROLE_AUDITOR = "Auditor"

BUDGET_GOVERNANCE_ROLES = (
	ROLE_BUDGET_OFFICER,
	ROLE_BUDGET_APPROVER,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
)

# KT-STD-001 v1.2 §3A — the page-load read gate. Distinct from the DocPerm/
# scope-map read enforcement in `require_budget_read_scope` below (kept as
# defence-in-depth for a direct record route): this one never raises, so a
# page mount can resolve its Forbidden verdict as data instead of a framework
# permission error.
BUDGET_READ_ROLES = BUDGET_GOVERNANCE_ROLES + (ROLE_AUDITOR,)

_BUSINESS_ROLE_FOR_CAPABILITY = {
	CAP_CREATE: ROLE_BUDGET_OFFICER,
	CAP_EDIT: ROLE_BUDGET_OFFICER,
	CAP_SUBMIT: ROLE_BUDGET_OFFICER,
	CAP_RETURN: ROLE_BUDGET_APPROVER,
	CAP_APPROVE: ROLE_BUDGET_APPROVER,
}


def ensure_budget_governance_roles() -> dict:
	"""Idempotent: create the 3 BUD-CHG-001 v1.3 §7 Frappe Roles (the
	registry's projections for the three business responsibilities).

	Does not grant any Role to a specific user — under v1.6 a grant flows
	only through the User Responsibility Assignment administration command,
	which projects the Frappe Role itself."""
	created = {"roles": []}

	for role in BUDGET_GOVERNANCE_ROLES:
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


def _version_name(version) -> str:
	return version if isinstance(version, str) else version.name


def _submitted_by(version_name: str) -> str | None:
	"""The user who performed this version's own "Submit for review" — read
	from its ledger trail (§17.1: "the version's submission audit event"),
	not a stored field."""
	event = frappe.db.get_value(
		"Budget Audit Event",
		{"budget_version": version_name, "event_type": "Budget version submitted"},
		["actor"],
		order_by="event_at asc",
	)
	return event or None


def _blocked_by_self_approval(user: str, capability: str, version_name: str) -> bool:
	"""§6/§17.1: "the submitting Officer cannot approve the same version" — a
	same-version self-check, not a general capability-pair rule. Return is
	not restricted by self-submission (only Approve is)."""
	if capability != CAP_APPROVE:
		return False
	return _submitted_by(version_name) == user


def require_budget_version_capability(
	user: str, capability: str, version, *, correlation_id: str = ""
) -> None:
	"""Raise unless `user` holds the Enabled Site-wide assignment for this
	capability's business role — and, for Approve, is not the version's own
	submitter."""
	version_name = _version_name(version)
	if _blocked_by_self_approval(user, capability, version_name):
		fail("AUTH_SEGREGATION_BLOCKED")
	decision = authorise_record(
		user=user,
		business_role=_business_role(capability),
		organisation_unit="",
		purpose=PURPOSE_COMMAND,
	)
	if not decision.allowed:
		fail(decision.reason_code or "AUTH_RESPONSIBILITY_REQUIRED")


def has_budget_version_capability(user: str, capability: str, version) -> bool:
	version_name = _version_name(version)
	if _blocked_by_self_approval(user, capability, version_name):
		return False
	return authorise_record(
		user=user,
		business_role=_business_role(capability),
		organisation_unit="",
		purpose=PURPOSE_COMMAND,
	).allowed


def require_budget_create_capability(user: str) -> None:
	"""Creating a brand-new Budget: one site is one Procuring Entity, so a
	plain Site-wide responsibility check applies directly — no PE parameter,
	no bootstrap workaround needed (mirrors Strategy's
	`require_plan_create_capability`)."""
	decision = authorise_record(
		user=user,
		business_role=ROLE_BUDGET_OFFICER,
		organisation_unit="",
		purpose=PURPOSE_COMMAND,
	)
	if not decision.allowed:
		fail(decision.reason_code or "AUTH_RESPONSIBILITY_REQUIRED")


def require_budget_read_scope(doctype: str, name: str) -> None:
	"""§5.3 — explicitly triggers the registered `has_permission` hook (which
	`frappe.get_doc()` alone does not do) so backend service code gets the
	same DocPerm + `kentender_scope_map` scoping a Desk list view would."""
	frappe.has_permission(doctype, doc=name, user=frappe.session.user, throw=True)


def require_budget_version_read_scope(version) -> None:
	require_budget_read_scope("Procurement Budget Version", _version_name(version))


def holds_any_budget_responsibility(user: str | None = None) -> bool:
	"""KT-STD-001 v1.2 §3A.1 — the page-level verdict resolved before anything
	renders. Never raises: a page load with no matching responsibility is a
	typed Forbidden result, not a permission error."""
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return False
	if is_technical(principal):
		return True
	return any(
		authorise_record(user=principal, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed
		for role in BUDGET_READ_ROLES
	)
