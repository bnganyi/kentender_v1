"""Departmental Needs authorization on the shared resolver (NDS-CHG-001 v1.6 §6, §16.4).

§6: "User Responsibility Assignment is the sole source of the role-to-
site-wide/OU relationship. Frappe Roles are synchronized framework
projections and Frappe User Permission, User Scope Assignment, Capability
Profile and Operational Scope Assignment grant no Departmental Needs
authority." Every scope decision in this module goes through
`kentender_core.services.authorization` — this file never queries
`User Permission`, and never invents a parallel scope store.

AUTH-ADR-001 v1.6 §10 describes its own error codes as "the shared
vocabulary of the resolver, not a replacement for a module's published
error contract." This module keeps its own closed §9 code set
(`NDS_SCOPE_DENIED`, `NDS_CONTEXT_REQUIRED`, ...) and maps the resolver's
`AUTH_*` codes onto it at this boundary — see `_AUTH_TO_NDS`.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services.authorization import (
	PURPOSE_COMMAND,
	PURPOSE_READ,
	authorise_record,
	is_technical,
	permitted_ou_scopes,
)
from kentender_procurement.departmental_needs.constants import (
	ROLE_AUDITOR,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	STATE_ACCEPTED,
)
from kentender_procurement.departmental_needs.errors import fail

# AUTH-ADR-001 v1.6 §10 → NDS-CHG-001 v1.6 §9. A code not listed here (there
# is currently no case that reaches one) falls back to NDS_SCOPE_DENIED,
# never an unmapped code leaking past this boundary.
_AUTH_TO_NDS: dict[str, str] = {
	"AUTH_RESPONSIBILITY_REQUIRED": "NDS_SCOPE_DENIED",
	"AUTH_SCOPE_REQUIRED": "NDS_SCOPE_DENIED",
	"AUTH_ASSIGNMENT_INACTIVE": "NDS_SCOPE_DENIED",
	"AUTH_CONFIGURATION_INVALID": "NDS_CONTEXT_REQUIRED",
}

# The two Organisation-Unit-scoped responsibilities this module names (§6).
DEPARTMENTAL_ROLES = (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT)
# The two Site-wide responsibilities this module names (§6).
SITE_WIDE_ROLES = (ROLE_PROCUREMENT_PLANNER, ROLE_AUDITOR)


def actor(user: str | None = None) -> str:
	value = cstr(user or frappe.session.user).strip()
	if not value or value == "Guest":
		# An unauthenticated caller holds neither the responsibility nor the
		# scope, so §9's scope denial is the correct stable result; there is
		# no separate authentication code in the contract.
		fail("NDS_SCOPE_DENIED", "Sign in to access Departmental Needs.")
	return value


def is_administrative(user: str) -> bool:
	"""§6/§8 — Administrator and System Manager read all without an assignment."""
	return is_technical(user)


def is_owner(need: Any, user: str) -> bool:
	"""§4.2 fixes the framework ``owner`` as the author; no duplicate field."""
	return cstr(need.owner) == cstr(user)


def _fail_from_decision(reason_code: str, message: str) -> None:
	fail(_AUTH_TO_NDS.get(reason_code, "NDS_SCOPE_DENIED"), message)


def in_scope(user: str, *, business_role: str, organisation_unit: str) -> bool:
	"""Whether `user` holds `business_role` with authority over `organisation_unit`.

	Technical readers pass unconditionally (§8); everyone else is resolved
	through the shared predicate. Used by callers that already know which
	single responsibility they are checking (My Work, notifications).
	"""
	if is_technical(user):
		return True
	return authorise_record(
		user=user,
		business_role=business_role,
		organisation_unit=cstr(organisation_unit),
		purpose=PURPOSE_READ,
	).allowed


def require_create(user: str, organisation_unit: str) -> str:
	"""§5.1 — only an active Departmental Author assignment for this OU may
	create. Returns the exact matching assignment ID (§15)."""
	decision = authorise_record(
		user=user,
		business_role=ROLE_DEPARTMENTAL_AUTHOR,
		organisation_unit=cstr(organisation_unit).strip(),
		purpose=PURPOSE_COMMAND,
	)
	if not decision.allowed:
		_fail_from_decision(
			decision.reason_code,
			"You have no Departmental Author responsibility for that department.",
		)
	return decision.assignment_id


def can_view(need: Any, user: str) -> tuple[bool, str]:
	"""One scope predicate for every read path (NDS-BR-019, NDS-AC-021)."""
	if is_technical(user):
		return True, "oversight"
	ou = cstr(need.organisation_unit)
	if is_owner(need, user) and authorise_record(
		user=user, business_role=ROLE_DEPARTMENTAL_AUTHOR, organisation_unit=ou, purpose=PURPOSE_READ
	).allowed:
		return True, "owner"
	if authorise_record(
		user=user, business_role=ROLE_HEAD_OF_USER_DEPARTMENT, organisation_unit=ou, purpose=PURPOSE_READ
	).allowed:
		return True, "department"
	# §6/§7 — the Planner reads only the current accepted source, Site-wide.
	if cstr(need.current_state) == STATE_ACCEPTED and authorise_record(
		user=user, business_role=ROLE_PROCUREMENT_PLANNER, organisation_unit="", purpose=PURPOSE_READ
	).allowed:
		return True, "planning"
	if authorise_record(
		user=user, business_role=ROLE_AUDITOR, organisation_unit="", purpose=PURPOSE_READ
	).allowed:
		return True, "oversight"
	return False, "none"


def require_view(need: Any, user: str) -> str:
	allowed, profile = can_view(need, user)
	if not allowed:
		# §9 — disclose no protected record data, including its existence.
		fail("NDS_SCOPE_DENIED", "Departmental Need not found.")
	return profile


def require_author_command(need: Any, user: str) -> str:
	"""§5.1 — the Departmental Author who owns the Need performs these commands.

	Returns the exact matching assignment ID, retained on the decision
	record's snapshot (AUTH-ADR-001 v1.6 §15).
	"""
	if not is_owner(need, user):
		fail("NDS_SCOPE_DENIED", "Only the authoring user may perform this action.")
	decision = authorise_record(
		user=user,
		business_role=ROLE_DEPARTMENTAL_AUTHOR,
		organisation_unit=cstr(need.organisation_unit),
		purpose=PURPOSE_COMMAND,
	)
	if not decision.allowed:
		_fail_from_decision(
			decision.reason_code, "You have no Departmental Needs permission for that context."
		)
	return decision.assignment_id


def require_review_command(need: Any, user: str) -> str:
	"""§5.1/§6 — the Head of User Department decides a submitted version.

	Returns the exact matching assignment ID, retained on the decision
	record's snapshot (AUTH-ADR-001 v1.6 §15).
	"""
	decision = authorise_record(
		user=user,
		business_role=ROLE_HEAD_OF_USER_DEPARTMENT,
		organisation_unit=cstr(need.organisation_unit),
		purpose=PURPOSE_COMMAND,
	)
	if not decision.allowed:
		_fail_from_decision(
			decision.reason_code, "You have no departmental review permission for that context."
		)
	return decision.assignment_id


# --- Organisation Unit offers (§8.1 resolve_needs_scope / list_need_create_targets) ---


def _unit_rows(units: set[str] | None) -> list[dict[str, str]]:
	if not units:
		return []
	rows = frappe.get_all(
		"Organisation Unit",
		filters={"name": ("in", sorted(units)), "status": "Active"},
		fields=["name", "unit_name"],
		order_by="unit_name asc",
	)
	return [
		{"organisation_unit": row.name, "organisation_unit_label": cstr(row.unit_name or row.name)}
		for row in rows
	]


def _all_active_units() -> list[dict[str, str]]:
	rows = frappe.get_all(
		"Organisation Unit", filters={"status": "Active"}, fields=["name", "unit_name"], order_by="unit_name asc"
	)
	return [
		{"organisation_unit": row.name, "organisation_unit_label": cstr(row.unit_name or row.name)}
		for row in rows
	]


def creation_contexts(user: str | None = None) -> list[dict[str, str]]:
	"""Organisation Units in which this user may author a Need (§8.1, §16.4.4)."""
	principal = actor(user)
	if is_technical(principal):
		return _all_active_units()
	return _unit_rows(permitted_ou_scopes(principal, ROLE_DEPARTMENTAL_AUTHOR))


def viewing_contexts(user: str | None = None) -> list[dict[str, str]]:
	"""Organisation Units whose Needs this user may list (§8.1).

	Distinct from :func:`creation_contexts`, which answers "where may this
	user *author*". `get_workspace` backs the review screen as well as the
	author workspace, so resolving through the authoring question alone
	would turn the Head of User Department away from NDS-UI-02 entirely.
	Resolving a context grants nothing: `can_view` still filters every row,
	and every command re-checks its own authority.
	"""
	principal = actor(user)
	if is_technical(principal):
		return _all_active_units()
	# `permitted_ou_scopes` returns None for a held Site-wide assignment
	# (unrestricted) and an empty set for no assignment at all — only the
	# former should widen the offer to every unit.
	if any(permitted_ou_scopes(principal, role) is None for role in SITE_WIDE_ROLES):
		return _all_active_units()
	units: set[str] = set()
	for role in DEPARTMENTAL_ROLES:
		scope = permitted_ou_scopes(principal, role)
		if scope:
			units |= scope
	return _unit_rows(units)
