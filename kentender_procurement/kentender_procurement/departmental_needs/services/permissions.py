"""Native Frappe authorization for Departmental Needs (NDS-CHG-001 v1.1 §6).

§6 and NDS-AC-044 require native Frappe Role, Workflow permission and User
Permission only. Capability Profiles and Operational Scope Assignments are not
consulted here, and a temporary acting HoD is expressed as the same
``Head of User Department`` role plus a time-bound User Permission — never a
delegate role (§1.1, NDS-AC-042).

Frappe's own User Permission semantics apply: when a user has no User
Permission rows for a doctype they are unrestricted on it; when they have any,
they are restricted to exactly those values.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.departmental_needs.constants import (
	ROLE_AUDITOR,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	STATE_ACCEPTED,
)
from kentender_procurement.departmental_needs.errors import fail

# Roles that see technical/neutral records without a business role (§6).
ADMINISTRATIVE_ROLES = ("System Manager", "Administrator")

SCOPE_FIELDS = (
	("Procuring Entity", "procuring_entity"),
	("Organisation Unit", "organisation_unit"),
	("Financial Year", "financial_year"),
)


def actor(user: str | None = None) -> str:
	value = cstr(user or frappe.session.user).strip()
	if not value or value == "Guest":
		# An unauthenticated caller holds neither the role nor the scope, so §9's
		# scope denial is the correct stable result; there is no separate
		# authentication code in the contract.
		fail("NDS_SCOPE_DENIED", "Sign in to access Departmental Needs.")
	return value


def roles_of(user: str) -> set[str]:
	return set(frappe.get_roles(user))


def has_role(user: str, role: str) -> bool:
	return role in roles_of(user)


def is_administrative(user: str) -> bool:
	return bool(roles_of(user).intersection(ADMINISTRATIVE_ROLES))


def permitted_values(user: str, doctype: str) -> set[str] | None:
	"""Allowed values for one doctype, or ``None`` when unrestricted.

	``None`` is Frappe's own meaning of "no User Permission rows for this
	doctype", which is materially different from an empty set (restricted to
	nothing) and must not be collapsed into it.
	"""
	rows = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": doctype},
		fields=["for_value"],
		limit_page_length=0,
	)
	if not rows:
		return None
	return {cstr(row.for_value) for row in rows}


# §6 — these two roles carry departmental authority, so their assignment must
# name the department. The Planner and Auditor are scoped by PE and FY only
# (§14.2), and requiring an Organisation Unit of them would deny the read access
# §6 grants.
DEPARTMENTAL_ROLES = (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT)


def required_dimensions(user: str) -> tuple[str, ...]:
	"""Scope dimensions this user's own role must name explicitly (NDS-BR-001)."""
	if roles_of(user).intersection(DEPARTMENTAL_ROLES):
		return ("Procuring Entity", "Organisation Unit", "Financial Year")
	return ("Procuring Entity", "Financial Year")


def in_scope(user: str, *, procuring_entity: str, organisation_unit: str, financial_year: str) -> bool:
	"""Every scope dimension must be explicitly authorised (NDS-BR-001).

	Frappe's own default is that a user with *no* User Permission rows for a
	doctype is unrestricted on it. This module deliberately inverts that for
	business roles, because NDS-BR-001 requires every Need to resolve to one
	explicit authorised PE, OU and FY and states that missing, ambiguous or
	expired scope fails closed.

	The inversion also removes a privilege-escalation trap. Ending a temporary
	acting assignment by deleting its only Organisation Unit row would, under
	Frappe's default, leave that user unrestricted across *every* department —
	silently widening their authority at the moment it was meant to end
	(NDS-AC-042). Administrative users are exempt because §6 grants them
	technical oversight rather than departmental authority.
	"""
	if is_administrative(user):
		return True
	values = {
		"procuring_entity": cstr(procuring_entity),
		"organisation_unit": cstr(organisation_unit),
		"financial_year": cstr(financial_year),
	}
	required = required_dimensions(user)
	for doctype, key in SCOPE_FIELDS:
		allowed = permitted_values(user, doctype)
		if allowed is None:
			# Unnamed dimension: fails closed when the user's own role is scoped
			# by it, and is simply not a restriction otherwise.
			if doctype in required:
				return False
			continue
		if values[key] not in allowed:
			return False
	return True


def _need_scope(need: Any) -> dict[str, str]:
	return {
		"procuring_entity": cstr(need.procuring_entity),
		"organisation_unit": cstr(need.organisation_unit),
		"financial_year": cstr(need.financial_year),
	}


def is_owner(need: Any, user: str) -> bool:
	"""§4.2 fixes the framework ``owner`` as the author; no duplicate field."""
	return cstr(need.owner) == cstr(user)


# §6 names the roles that read Needs. The Author and Head of User Department
# are departmental, so their contexts are the units their User Permissions name;
# the Planner and Auditor are PE/FY-scoped (§14.2), so every unit under a
# permitted Procuring Entity is in view for them.
READING_ROLES = (
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	ROLE_AUDITOR,
)


def creation_contexts(user: str | None = None) -> list[dict[str, str]]:
	"""PE/OU pairs in which this user may author a Need (§8.1 resolve contexts)."""
	principal = actor(user)
	if not (has_role(principal, ROLE_DEPARTMENTAL_AUTHOR) or is_administrative(principal)):
		return []
	return _contexts_in_scope(principal)


def viewing_contexts(user: str | None = None) -> list[dict[str, str]]:
	"""PE/OU pairs whose Needs this user may list (§8.1 resolve contexts).

	Distinct from :func:`creation_contexts`, which answers "where may this user
	*author*". `get_workspace` backs the review screen as well as the author
	workspace, so resolving through the authoring question turned the Head of
	User Department away from NDS-UI-02 entirely — no queue, no register — even
	though §6 gives them departmental review authority.

	Resolving a context grants nothing. It names the PE/OU pair whose rows are
	queried; `can_view` still filters every row, and every command re-checks
	its own authority. Widening this to the four §6 reading roles therefore
	changes what a reviewer can *open*, not what anyone can see or do.
	"""
	principal = actor(user)
	if not (roles_of(principal).intersection(READING_ROLES) or is_administrative(principal)):
		return []
	return _contexts_in_scope(principal)


def _contexts_in_scope(principal: str) -> list[dict[str, str]]:
	allowed_entities = permitted_values(principal, "Procuring Entity")
	allowed_units = permitted_values(principal, "Organisation Unit")
	filters: dict[str, Any] = {"status": "Active"}
	if allowed_units is not None:
		filters["name"] = ("in", sorted(allowed_units) or [""])
	if allowed_entities is not None:
		filters["procuring_entity"] = ("in", sorted(allowed_entities) or [""])
	contexts = [
		{
			"procuring_entity": cstr(row.procuring_entity),
			"procuring_entity_label": cstr(
				frappe.db.get_value("Procuring Entity", row.procuring_entity, "legal_name")
				or row.procuring_entity
			),
			"organisation_unit": cstr(row.name),
			"organisation_unit_label": cstr(row.unit_name or row.name),
		}
		for row in frappe.get_all(
			"Organisation Unit",
			filters=filters,
			fields=["name", "unit_name", "procuring_entity"],
			limit_page_length=0,
		)
		if row.procuring_entity
	]
	return sorted(contexts, key=lambda row: (row["procuring_entity_label"], row["organisation_unit_label"]))


def require_create(user: str, pe: str, ou: str, financial_year: str) -> None:
	if frappe.db.get_value("Organisation Unit", ou, "procuring_entity") != pe:
		# §9 — no single authorised PE/OU/FY context can be resolved.
		fail(
			"NDS_CONTEXT_REQUIRED",
			"The selected department does not belong to the selected Procuring Entity.",
		)
	if not (has_role(user, ROLE_DEPARTMENTAL_AUTHOR) or is_administrative(user)):
		fail("NDS_SCOPE_DENIED", "You do not hold the Departmental Author role.")
	if not in_scope(user, procuring_entity=pe, organisation_unit=ou, financial_year=financial_year):
		fail("NDS_SCOPE_DENIED", "You have no Departmental Needs permission for that context.")


def can_view(need: Any, user: str) -> tuple[bool, str]:
	"""One scope predicate for every read path (NDS-BR-019, NDS-AC-021)."""
	scope = _need_scope(need)
	if is_administrative(user):
		return True, "oversight"
	if not in_scope(user, **scope):
		return False, "none"
	held = roles_of(user)
	if ROLE_DEPARTMENTAL_AUTHOR in held and is_owner(need, user):
		return True, "owner"
	if ROLE_HEAD_OF_USER_DEPARTMENT in held:
		return True, "department"
	# A Planner reads only the current accepted source (§6, §7).
	if ROLE_PROCUREMENT_PLANNER in held and cstr(need.current_state) == STATE_ACCEPTED:
		return True, "planning"
	if ROLE_AUDITOR in held:
		return True, "oversight"
	return False, "none"


def require_view(need: Any, user: str) -> str:
	allowed, profile = can_view(need, user)
	if not allowed:
		# §9 — disclose no protected record data, including its existence.
		fail("NDS_SCOPE_DENIED", "Departmental Need not found.")
	return profile


def require_author_command(need: Any, user: str) -> None:
	"""§5.1 — the Departmental Author who owns the Need performs these commands."""
	if not is_owner(need, user):
		fail("NDS_SCOPE_DENIED", "Only the authoring user may perform this action.")
	if not (has_role(user, ROLE_DEPARTMENTAL_AUTHOR) or is_administrative(user)):
		fail("NDS_SCOPE_DENIED", "You do not hold the Departmental Author role.")
	if not in_scope(user, **_need_scope(need)):
		fail("NDS_SCOPE_DENIED", "You have no Departmental Needs permission for that context.")


def require_review_command(need: Any, user: str) -> None:
	"""§5.1/§6 — the Head of User Department decides a submitted version."""
	if not (has_role(user, ROLE_HEAD_OF_USER_DEPARTMENT) or is_administrative(user)):
		fail("NDS_SCOPE_DENIED", "You do not hold the Head of User Department role.")
	if not in_scope(user, **_need_scope(need)):
		fail("NDS_SCOPE_DENIED", "You have no departmental review permission for that context.")


def require_intake_window_command(user: str, *, procuring_entity: str, financial_year: str) -> None:
	"""§6 — the Procurement Planner maintains the PE/FY intake window."""
	if not (has_role(user, ROLE_PROCUREMENT_PLANNER) or is_administrative(user)):
		fail("NDS_SCOPE_DENIED", "You do not hold the Procurement Planner role.")
	allowed_entities = permitted_values(user, "Procuring Entity")
	allowed_years = permitted_values(user, "Financial Year")
	if allowed_entities is not None and cstr(procuring_entity) not in allowed_entities:
		fail("NDS_SCOPE_DENIED", "You have no permission for that Procuring Entity.")
	if allowed_years is not None and cstr(financial_year) not in allowed_years:
		fail("NDS_SCOPE_DENIED", "You have no permission for that Financial Year.")
