# Copyright (c) 2026, KenTender and contributors
"""REQ §12 role helpers for Strategy MVP-1."""

from __future__ import annotations

import frappe
from frappe import _

ROLE_VIEWER = "Strategy Viewer"
ROLE_PLANNING = "Planning Authority"
ROLE_AUDITOR = "Auditor"

# STR-CHG-001 v1.5/v1.6 — the pre-rebuild role set (Strategy Officer, Strategy
# Manager, Strategy Reviewer) is retired. Only Strategy Viewer (plain native
# permission role, current model) plus the cross-domain Planning Authority /
# Auditor roles this module references for scope checks remain here.


def user_roles(user: str | None = None) -> set[str]:
	"""STR-CHG-001 §5 — Administrator has neutral read access only unless
	explicitly assigned. Every consumer below explicitly checks for
	"System Manager" itself, so no special-casing is needed here."""
	user = user or frappe.session.user
	return set(frappe.get_roles(user))


def require_any_role(*roles: str) -> None:
	have = user_roles()
	if "System Manager" in have:
		return
	if not have.intersection(roles):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def can_edit_draft_plan() -> bool:
	"""REQ §12 — Create/edit Draft plans: STR-CHG-001 v1.5's Strategy Author."""
	return bool(user_roles().intersection({"Strategy Author", "System Manager"}))


def can_create_successor_plan() -> bool:
	"""STR-UI-02 — Create successor Draft from Active/Approved: Strategy Author."""
	return can_edit_draft_plan()


def has_cross_entity_authority(user: str | None = None) -> bool:
	"""STR-FR-002 — cross-entity context switch (Planning Authority / System Manager)."""
	roles = user_roles(user)
	return bool(roles.intersection({ROLE_PLANNING, ROLE_AUDITOR, "System Manager"}))


def entity_for_user(user: str | None = None) -> str | None:
	"""Best-effort procuring entity from user defaults / Employee; may be None for Admin."""
	user = user or frappe.session.user
	pe = frappe.defaults.get_user_default("Procuring Entity", user)
	if pe:
		return pe if isinstance(pe, str) else (pe[0] if pe else None)
	# Frappe treats "Procuring Entity" as a user-permission key; a plain DefaultValue
	# string is then ignored by get_user_default — fall back to raw defaults.
	defaults = frappe.defaults.get_defaults(user) or {}
	raw = defaults.get("Procuring Entity") or defaults.get("procuring_entity")
	if isinstance(raw, (list, tuple)):
		return raw[0] if len(raw) == 1 else None
	return raw or None


def assert_entity_in_scope(procuring_entity: str | None, user: str | None = None) -> None:
	"""Raise PermissionError when PE is outside the user's authorised entity scope."""
	user = user or frappe.session.user
	if has_cross_entity_authority(user):
		return
	from kentender_core.services.org_scope_access import permitted_procuring_entities

	pes = permitted_procuring_entities(user)
	if pes is None:
		return
	if pes and procuring_entity in pes:
		return
	# Legacy fallback when User Scope Assignment is absent.
	own = entity_for_user(user)
	if not procuring_entity or not own or procuring_entity != own:
		frappe.throw(_("Not permitted for this procuring entity"), frappe.PermissionError)


def assert_org_unit_in_scope(
	procuring_entity: str | None,
	owner_org_unit: str | None,
	user: str | None = None,
	*,
	require_write: bool = False,
) -> None:
	"""PE + Organisation Unit ownership gate (User Scope Assignment)."""
	from kentender_core.services.org_scope_access import assert_can_access_owned_record

	assert_can_access_owned_record(
		procuring_entity=procuring_entity,
		owner_org_unit=owner_org_unit,
		user=user,
		require_write=require_write,
	)


def ownership_path_for_unit(owner_org_unit: str | None) -> str:
	from kentender_core.services.org_scope_access import ownership_path_label

	return ownership_path_label(owner_org_unit)
