# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-PERM — Planning MVP-1 roles, PE/OU scope, and action authority."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

ROLE_CONTRIBUTOR = "Planning Contributor"
ROLE_HOD = "Head of User Department"
ROLE_PLANNER = "Procurement Planner"
ROLE_REVIEWER = "Planning Reviewer"
ROLE_AUTHORITY = "Planning Authority"
ROLE_ACCOUNTING_OFFICER = "Accounting Officer"
ROLE_DESIGNATED_APPROVER = "Designated Approver"
ROLE_TENDER_INITIATOR = "Tender Initiator"
ROLE_VIEWER = "Planning Viewer"

ALL_PLANNING_ROLES = (
	ROLE_CONTRIBUTOR,
	ROLE_HOD,
	ROLE_PLANNER,
	ROLE_REVIEWER,
	ROLE_AUTHORITY,
	ROLE_ACCOUNTING_OFFICER,
	ROLE_DESIGNATED_APPROVER,
	ROLE_TENDER_INITIATOR,
	ROLE_VIEWER,
)

# May prepare / mutate draft plan content (not final approve alone).
PLANNING_MUTATE_ROLES = frozenset(
	(
		ROLE_CONTRIBUTOR,
		ROLE_HOD,
		ROLE_PLANNER,
		ROLE_REVIEWER,
		ROLE_AUTHORITY,
		ROLE_ACCOUNTING_OFFICER,
		ROLE_DESIGNATED_APPROVER,
	)
)

CREATE_PLAN_ROLES = frozenset((ROLE_PLANNER, ROLE_AUTHORITY))
ADD_DEMAND_ROLES = frozenset(
	(ROLE_CONTRIBUTOR, ROLE_HOD, ROLE_PLANNER, ROLE_AUTHORITY)
)
APPROVE_PLAN_ROLES = frozenset(
	(ROLE_DESIGNATED_APPROVER, ROLE_ACCOUNTING_OFFICER, ROLE_AUTHORITY)
)
READ_PLAN_ROLES = frozenset(ALL_PLANNING_ROLES)

# USA roles that grant PE eligibility for plan create selection.
CREATE_SCOPE_ROLES = frozenset((ROLE_PLANNER, ROLE_AUTHORITY))

ERR_PERMISSION = "PLN_PERMISSION_DENIED"
ERR_SCOPE = "PLN_SCOPE_DENIED"
ERR_OPERATIONAL_ROLE = "PLN_OPERATIONAL_ROLE_REQUIRED"
ERR_PE_SELECTION = "PLN_PE_SELECTION_REQUIRED"
ERR_PE_BLOCKED = "PLN_PE_SCOPE_BLOCKED"

MODE_SINGLE = "single_readonly"
MODE_MULTI = "multi_required"
MODE_BLOCKED = "blocked"

# Workspace PE filter sentinel — never a silent default owner; explicit "all" view.
PE_FILTER_ALL = "__all__"


def ensure_planning_roles() -> None:
	for role in ALL_PLANNING_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{"doctype": "Role", "role_name": role, "desk_access": 1}
			).insert(ignore_permissions=True)


def throw_planning_error(
	code: str,
	message: str,
	*,
	exc: type[Exception] | None = None,
) -> None:
	frappe.throw(f"{code}: {_(message)}", exc or frappe.ValidationError, title=code)


def operational_roles(user: str | None = None) -> set[str]:
	user = user or frappe.session.user
	return set(frappe.get_roles(user))


def has_any_operational_role(*roles: str, user: str | None = None) -> bool:
	return bool(operational_roles(user).intersection(roles))


def _is_admin_only(user: str | None = None) -> bool:
	"""True when the actor is adminish and has no Planning role at all (incl. Viewer).

	Administrator + Planning Viewer is support read access — not "admin only".
	"""
	user = user or frappe.session.user
	roles = operational_roles(user)
	adminish = user == "Administrator" or "System Manager" in roles
	if not adminish:
		return False
	return not roles.intersection(ALL_PLANNING_ROLES)


def planning_usa_roles(user: str | None = None) -> set[str]:
	"""Planning roles granted via User Scope Assignment (not Desk role inflation).

	Frappe returns every Role for user ``Administrator`` from ``get_roles`` — USA is
	the authority for operational vs support visibility.
	"""
	from kentender_core.services.org_scope_access import user_scope_rows

	user = user or frappe.session.user
	return {
		(row.get("role") or "").strip()
		for row in user_scope_rows(user)
		if (row.get("role") or "").strip() in ALL_PLANNING_ROLES
	}


def is_planning_read_only(user: str | None = None) -> bool:
	"""True when the actor may inspect Planning but has no mutate/approve/create USA."""
	user = user or frappe.session.user
	usa_roles = planning_usa_roles(user)
	if usa_roles:
		return not usa_roles.intersection(
			PLANNING_MUTATE_ROLES | APPROVE_PLAN_ROLES | CREATE_PLAN_ROLES
		)
	# No Planning USA: Administrator never gains operational authority from get_roles.
	if user == "Administrator":
		return True
	roles = operational_roles(user)
	return not roles.intersection(
		PLANNING_MUTATE_ROLES | APPROVE_PLAN_ROLES | CREATE_PLAN_ROLES
	)


def require_operational_roles(*roles: str, user: str | None = None) -> None:
	"""Require a real Planning operational role; System Manager / Administrator alone fails."""
	if has_any_operational_role(*roles, user=user):
		return
	throw_planning_error(
		ERR_OPERATIONAL_ROLE if _is_admin_only(user) else ERR_PERMISSION,
		"Not permitted for this Planning action",
		exc=frappe.PermissionError,
	)


def assert_planning_actor(user: str | None = None) -> str:
	"""Login + any mutate-capable Planning role (Admin alone denied)."""
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		frappe.throw(_("Login required."), frappe.PermissionError, title="PLN_LOGIN_REQUIRED")
	require_operational_roles(*PLANNING_MUTATE_ROLES, user=actor)
	return actor


def assert_can_create_plan(user: str | None = None) -> str:
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		frappe.throw(_("Login required."), frappe.PermissionError, title="PLN_LOGIN_REQUIRED")
	require_operational_roles(*CREATE_PLAN_ROLES, user=actor)
	return actor


def assert_can_add_demand(user: str | None = None) -> str:
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		frappe.throw(_("Login required."), frappe.PermissionError, title="PLN_LOGIN_REQUIRED")
	require_operational_roles(*ADD_DEMAND_ROLES, user=actor)
	return actor


def assert_can_approve_plan(user: str | None = None) -> str:
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		frappe.throw(_("Login required."), frappe.PermissionError, title="PLN_LOGIN_REQUIRED")
	require_operational_roles(*APPROVE_PLAN_ROLES, user=actor)
	return actor


def assert_planning_scope(
	*,
	procuring_entity: str | None,
	org_unit: str | None = None,
	user: str | None = None,
	require_write: bool = False,
) -> None:
	"""Server-side PE + organisation-unit gate (REQ §11 / PLN-NFR-001)."""
	from kentender_core.services.org_scope_access import can_access_owned_record

	user = user or frappe.session.user
	# Admin alone (no Planning role, including Viewer) must not bypass via org_scope_access.
	if _is_admin_only(user):
		throw_planning_error(
			ERR_OPERATIONAL_ROLE,
			"Not permitted for this organisational scope",
			exc=frappe.PermissionError,
		)
	# Administrator / System Manager with a Planning role (e.g. Viewer) still honour USA —
	# never treat them as unrestricted PE owners.
	roles = operational_roles(user)
	is_pure_admin = (
		user == "Administrator" or "System Manager" in roles
	) and not roles.intersection(ALL_PLANNING_ROLES)
	if is_pure_admin:
		throw_planning_error(
			ERR_SCOPE,
			"Not permitted for this organisational scope",
			exc=frappe.PermissionError,
		)

	from kentender_core.services.org_scope_access import (
		permitted_org_units,
		permitted_procuring_entities,
	)

	pes = permitted_procuring_entities(user)
	# None means unrestricted admin — treat as no PE when also lacking planning USA.
	if pes is None:
		# System Manager + Planning role without USA rows: fall through to USA empty.
		from kentender_core.services.org_scope_access import user_scope_rows

		rows = user_scope_rows(user)
		pes = {r.procuring_entity for r in rows if r.procuring_entity} if rows else set()

	if not procuring_entity or procuring_entity not in pes:
		throw_planning_error(
			ERR_SCOPE,
			"Not permitted for this organisational scope",
			exc=frappe.PermissionError,
		)

	units = permitted_org_units(user, procuring_entity=procuring_entity)
	if units is None:
		return
	if not org_unit:
		if require_write:
			throw_planning_error(
				ERR_SCOPE,
				"Not permitted for this organisational scope",
				exc=frappe.PermissionError,
			)
		return
	if org_unit not in units:
		throw_planning_error(
			ERR_SCOPE,
			"Not permitted for this organisational scope",
			exc=frappe.PermissionError,
		)
	# Keep Demands-compatible helper available for callers that prefer it.
	_ = can_access_owned_record


def _entity_ref(pe: str) -> dict[str, str]:
	name = pe
	code = pe
	if pe and frappe.db.exists("Procuring Entity", pe):
		name = str(
			frappe.db.get_value("Procuring Entity", pe, "entity_name")
			or frappe.db.get_value("Procuring Entity", pe, "procuring_entity_name")
			or pe
		)
		code = str(frappe.db.get_value("Procuring Entity", pe, "entity_code") or pe)
	return {"id": pe, "code": code, "name": name}


def list_eligible_procuring_entities(user: str | None = None) -> list[dict[str, Any]]:
	"""Distinct PEs from Planning create-scope User Scope Assignments."""
	from kentender_core.services.org_scope_access import user_scope_rows

	user = user or frappe.session.user
	seen: set[str] = set()
	out: list[dict[str, Any]] = []
	for row in user_scope_rows(user):
		if (row.get("role") or "") not in CREATE_SCOPE_ROLES:
			continue
		pe = (row.get("procuring_entity") or "").strip()
		if not pe or pe in seen:
			continue
		seen.add(pe)
		out.append(_entity_ref(pe))
	out.sort(key=lambda p: p["id"])
	return out


def resolve_pe_for_create(
	user: str | None = None,
	selected_pe: str | None = None,
) -> dict[str, Any]:
	"""Zero → block; one → force that PE; multi → require explicit selection."""
	user = user or frappe.session.user
	entities = list_eligible_procuring_entities(user)
	if not entities:
		return {
			"selection_mode": MODE_BLOCKED,
			"procuring_entities": [],
			"procuring_entity": None,
			"blocked_reason": "No operational Planning assignment exists for plan creation.",
		}
	if len(entities) == 1:
		pe = entities[0]["id"]
		return {
			"selection_mode": MODE_SINGLE,
			"procuring_entities": entities,
			"procuring_entity": pe,
			"blocked_reason": None,
		}
	chosen = (selected_pe or "").strip()
	if not chosen:
		return {
			"selection_mode": MODE_MULTI,
			"procuring_entities": entities,
			"procuring_entity": None,
			"blocked_reason": None,
		}
	ids = {e["id"] for e in entities}
	if chosen not in ids:
		throw_planning_error(
			ERR_PE_SELECTION,
			"Selected Procuring Entity is not an eligible Planning assignment",
		)
	return {
		"selection_mode": MODE_MULTI,
		"procuring_entities": entities,
		"procuring_entity": chosen,
		"blocked_reason": None,
	}


def assert_pe_resolved_for_create(
	*,
	user: str | None = None,
	selected_pe: str | None = None,
) -> str:
	scope = resolve_pe_for_create(user, selected_pe)
	if scope["selection_mode"] == MODE_BLOCKED:
		throw_planning_error(
			ERR_PE_BLOCKED,
			scope.get("blocked_reason")
			or "No operational Planning assignment exists for plan creation.",
			exc=frappe.PermissionError,
		)
	if scope["selection_mode"] == MODE_MULTI and not scope.get("procuring_entity"):
		throw_planning_error(
			ERR_PE_SELECTION,
			"Procuring Entity selection is required when multiple entities are assigned",
		)
	pe = (scope.get("procuring_entity") or "").strip()
	if not pe:
		throw_planning_error(
			ERR_PE_BLOCKED,
			"No Procuring Entity resolved for plan creation",
			exc=frappe.PermissionError,
		)
	return pe
