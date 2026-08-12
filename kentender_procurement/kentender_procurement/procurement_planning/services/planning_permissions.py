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
# Finance confirmation (C05) — Budget Officer; scaffolded in C01 for task guards.
ROLE_BUDGET_OFFICER = "Budget Officer"

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
SUBMIT_FOR_REVIEW_ROLES = frozenset((ROLE_PLANNER, ROLE_AUTHORITY))
# Professional recommend — Reviewer (Authority may also recommend in small entities).
RECOMMEND_PLAN_ROLES = frozenset((ROLE_REVIEWER, ROLE_AUTHORITY))
# Return from review rail — Reviewer or final-approver roles.
RETURN_PLAN_ROLES = frozenset(
	(
		ROLE_REVIEWER,
		ROLE_DESIGNATED_APPROVER,
		ROLE_ACCOUNTING_OFFICER,
		ROLE_AUTHORITY,
	)
)
APPROVE_PLAN_ROLES = frozenset(
	(ROLE_DESIGNATED_APPROVER, ROLE_ACCOUNTING_OFFICER, ROLE_AUTHORITY)
)
READ_PLAN_ROLES = frozenset(ALL_PLANNING_ROLES)
# Professional review task (recommend / return / approve) — opens PLN-UI-08 task surface.
REVIEW_TASK_ROLES = frozenset(
	RECOMMEND_PLAN_ROLES | RETURN_PLAN_ROLES | APPROVE_PLAN_ROLES
)
CONFIRM_PLAN_FUNDING_ROLES = frozenset((ROLE_BUDGET_OFFICER,))

# USA roles that grant PE eligibility for plan create selection.
CREATE_SCOPE_ROLES = frozenset((ROLE_PLANNER, ROLE_AUTHORITY))

# Auth-pack shaped capability vocabulary (Planning-local).
CAP_PLAN_VIEW = "plan.view"
CAP_PLAN_CREATE = "plan.create"
CAP_PLAN_ITEM_EDIT = "plan_item.edit"
CAP_PLAN_SUBMIT = "plan.submit"
CAP_PLAN_REVIEW = "plan.review"
CAP_PLAN_APPROVE = "plan.approve"
CAP_PLAN_RECOMMEND = "plan.recommend"
CAP_PLAN_RETURN = "plan.return"
CAP_PLAN_FINANCE_CONFIRM = "plan.finance.confirm"
CAP_PLAN_FINANCE_TASK = "plan.finance.task"

CAPABILITY_ROLES: dict[str, frozenset[str]] = {
	CAP_PLAN_VIEW: READ_PLAN_ROLES,
	CAP_PLAN_CREATE: CREATE_PLAN_ROLES,
	CAP_PLAN_ITEM_EDIT: ADD_DEMAND_ROLES,
	CAP_PLAN_SUBMIT: SUBMIT_FOR_REVIEW_ROLES,
	CAP_PLAN_REVIEW: REVIEW_TASK_ROLES,
	CAP_PLAN_APPROVE: APPROVE_PLAN_ROLES,
	CAP_PLAN_RECOMMEND: RECOMMEND_PLAN_ROLES,
	CAP_PLAN_RETURN: RETURN_PLAN_ROLES,
	CAP_PLAN_FINANCE_CONFIRM: CONFIRM_PLAN_FUNDING_ROLES,
	CAP_PLAN_FINANCE_TASK: CONFIRM_PLAN_FUNDING_ROLES,
}

ERR_PERMISSION = "PLN_PERMISSION_DENIED"
ERR_SCOPE = "PLN_SCOPE_DENIED"
ERR_OPERATIONAL_ROLE = "PLN_OPERATIONAL_ROLE_REQUIRED"
ERR_PE_SELECTION = "PLN_PE_SELECTION_REQUIRED"
ERR_PE_BLOCKED = "PLN_PE_SCOPE_BLOCKED"
ERR_TASK = "PLN_TASK_DENIED"

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


def actor_planning_roles(user: str | None = None) -> set[str]:
	"""Roles used for Planning capability checks (C01).

	Administrator / System Manager never inherit Planning authority from Desk
	``get_roles`` inflation — only User Scope Assignment counts for them.
	Other users: USA when present, else Desk Planning roles.
	"""
	user = user or frappe.session.user
	usa = planning_usa_roles(user)
	desk = operational_roles(user)
	adminish = user == "Administrator" or "System Manager" in desk
	if adminish:
		return usa
	if usa:
		return usa
	return desk.intersection(ALL_PLANNING_ROLES)


def funding_usa_roles(user: str | None = None) -> set[str]:
	"""Budget Officer (and related) from USA — used for Finance task scaffolding."""
	from kentender_core.services.org_scope_access import user_scope_rows

	user = user or frappe.session.user
	return {
		(row.get("role") or "").strip()
		for row in user_scope_rows(user)
		if (row.get("role") or "").strip() == ROLE_BUDGET_OFFICER
	}


def actor_funding_roles(user: str | None = None) -> set[str]:
	user = user or frappe.session.user
	usa = funding_usa_roles(user)
	desk = operational_roles(user)
	adminish = user == "Administrator" or "System Manager" in desk
	if adminish:
		return usa
	if usa:
		return usa
	return desk.intersection(CONFIRM_PLAN_FUNDING_ROLES)


def has_any_operational_role(*roles: str, user: str | None = None) -> bool:
	wanted = set(roles)
	if wanted.intersection(CONFIRM_PLAN_FUNDING_ROLES) and not wanted.intersection(
		ALL_PLANNING_ROLES
	):
		return bool(actor_funding_roles(user).intersection(wanted))
	return bool(actor_planning_roles(user).intersection(wanted))


def _is_admin_only(user: str | None = None) -> bool:
	"""True when the actor is adminish and has no Planning USA role at all."""
	user = user or frappe.session.user
	desk = operational_roles(user)
	adminish = user == "Administrator" or "System Manager" in desk
	if not adminish:
		return False
	return not planning_usa_roles(user)


def is_planning_read_only(user: str | None = None) -> bool:
	"""True when the actor may inspect Planning but has no mutate/approve/create USA."""
	user = user or frappe.session.user
	usa_roles = actor_planning_roles(user)
	if not usa_roles:
		return True
	return not usa_roles.intersection(
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


def require_capability(
	capability: str,
	*,
	procuring_entity: str | None = None,
	org_unit: str | None = None,
	user: str | None = None,
	require_write: bool = False,
) -> str:
	"""Record / task / mutation gate — capability + optional PE/OU scope."""
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		frappe.throw(_("Login required."), frappe.PermissionError, title="PLN_LOGIN_REQUIRED")
	role_set = CAPABILITY_ROLES.get(capability)
	if not role_set:
		throw_planning_error(
			ERR_PERMISSION,
			"Unknown Planning capability",
			exc=frappe.PermissionError,
		)
	require_operational_roles(*role_set, user=actor)
	if procuring_entity:
		assert_planning_scope(
			procuring_entity=procuring_entity,
			org_unit=org_unit,
			user=actor,
			require_write=require_write,
		)
	return actor


def has_review_task_capability(user: str | None = None) -> bool:
	return bool(actor_planning_roles(user).intersection(REVIEW_TASK_ROLES))


def assert_planning_actor(user: str | None = None) -> str:
	"""Login + any mutate-capable Planning role (Admin alone denied)."""
	return require_capability(CAP_PLAN_ITEM_EDIT, user=user)


def assert_can_create_plan(user: str | None = None) -> str:
	return require_capability(CAP_PLAN_CREATE, user=user)


def assert_can_add_demand(user: str | None = None) -> str:
	return require_capability(CAP_PLAN_ITEM_EDIT, user=user)


def assert_can_approve_plan(user: str | None = None) -> str:
	return require_capability(CAP_PLAN_APPROVE, user=user)


def assert_can_submit_for_review(user: str | None = None) -> str:
	return require_capability(CAP_PLAN_SUBMIT, user=user)


def assert_can_recommend_plan(user: str | None = None) -> str:
	return require_capability(CAP_PLAN_RECOMMEND, user=user)


def assert_can_return_plan(user: str | None = None) -> str:
	return require_capability(CAP_PLAN_RETURN, user=user)


def assert_can_open_finance_task(user: str | None = None) -> str:
	"""C01 scaffold — Budget Officer may open PLN-UI-07 Finance task (wired in C05)."""
	return require_capability(CAP_PLAN_FINANCE_TASK, user=user)


def assert_can_confirm_plan_funding(user: str | None = None) -> str:
	"""C01 scaffold — Confirm funding mutation authority (wired in C05)."""
	return require_capability(CAP_PLAN_FINANCE_CONFIRM, user=user)


def assert_can_open_review_task(user: str | None = None) -> str:
	"""Open PLN-UI-08 professional task surface (not neutral detail)."""
	return require_capability(CAP_PLAN_REVIEW, user=user)


def has_planning_scope(
	*,
	procuring_entity: str | None,
	org_unit: str | None = None,
	user: str | None = None,
	require_write: bool = False,
) -> bool:
	"""Silent PE + OU gate for list/filter paths (never msgprint / throw)."""
	user = user or frappe.session.user
	if _is_admin_only(user):
		return False

	from kentender_core.services.org_scope_access import (
		permitted_org_units,
		permitted_procuring_entities,
		user_scope_rows,
	)

	pes = permitted_procuring_entities(user)
	# None means unrestricted Desk admin — Planning still requires USA rows.
	if pes is None:
		rows = user_scope_rows(user)
		pes = {r.procuring_entity for r in rows if r.procuring_entity} if rows else set()

	if not procuring_entity or procuring_entity not in pes:
		return False

	units = permitted_org_units(user, procuring_entity=procuring_entity)
	if units is None:
		return True
	if not org_unit:
		return not require_write
	return org_unit in units


def assert_planning_scope(
	*,
	procuring_entity: str | None,
	org_unit: str | None = None,
	user: str | None = None,
	require_write: bool = False,
) -> None:
	"""Server-side PE + organisation-unit gate (REQ §11 / PLN-NFR-001)."""
	user = user or frappe.session.user
	if has_planning_scope(
		procuring_entity=procuring_entity,
		org_unit=org_unit,
		user=user,
		require_write=require_write,
	):
		return
	code = ERR_OPERATIONAL_ROLE if _is_admin_only(user) else ERR_SCOPE
	throw_planning_error(
		code,
		"Not permitted for this organisational scope",
		exc=frappe.PermissionError,
	)


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
