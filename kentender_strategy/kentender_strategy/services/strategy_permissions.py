# Copyright (c) 2026, KenTender and contributors
"""REQ §12 role helpers for Strategy MVP-1."""

from __future__ import annotations

import frappe
from frappe import _

ROLE_VIEWER = "Strategy Viewer"
ROLE_OFFICER = "Strategy Officer"
ROLE_MANAGER = "Strategy Manager"
ROLE_REVIEWER = "Strategy Reviewer"
ROLE_PLANNING = "Planning Authority"
ROLE_PERF_OFFICER = "Performance Officer"
ROLE_PERF_VERIFIER = "Performance Verifier"
ROLE_AUDITOR = "Auditor"

ALL_STRATEGY_ROLES = (
	ROLE_VIEWER,
	ROLE_OFFICER,
	ROLE_MANAGER,
	ROLE_REVIEWER,
	ROLE_PLANNING,
	ROLE_PERF_OFFICER,
	ROLE_PERF_VERIFIER,
	ROLE_AUDITOR,
)


def ensure_strategy_roles() -> None:
	for role in ALL_STRATEGY_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def user_roles(user: str | None = None) -> set[str]:
	user = user or frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return set(ALL_STRATEGY_ROLES) | {"System Manager"}
	return set(frappe.get_roles(user))


def require_any_role(*roles: str) -> None:
	have = user_roles()
	if "System Manager" in have or "Administrator" == frappe.session.user:
		return
	if not have.intersection(roles):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def can_edit_draft_plan() -> bool:
	"""REQ §12 — Create/edit Draft plans: Strategy Officer and Strategy Manager."""
	return bool(user_roles().intersection({ROLE_OFFICER, ROLE_MANAGER, "System Manager"}))


def can_create_successor_plan() -> bool:
	"""STR-UI-02 — Create successor Draft from Active/Approved: Officer / Manager."""
	return can_edit_draft_plan()


def can_submit_plan() -> bool:
	return ROLE_MANAGER in user_roles() or "System Manager" in user_roles()


def can_review_plan() -> bool:
	return bool(user_roles().intersection({ROLE_REVIEWER, ROLE_PLANNING, "System Manager"}))


def can_approve_plan() -> bool:
	return ROLE_PLANNING in user_roles() or "System Manager" in user_roles()


def can_submit_measurement() -> bool:
	return ROLE_PERF_OFFICER in user_roles() or "System Manager" in user_roles()


def can_verify_measurement() -> bool:
	return ROLE_PERF_VERIFIER in user_roles() or "System Manager" in user_roles()


def has_cross_entity_authority(user: str | None = None) -> bool:
	"""STR-FR-002 — cross-entity context switch (Planning Authority / System Manager)."""
	roles = user_roles(user)
	return bool(roles.intersection({ROLE_PLANNING, ROLE_AUDITOR, "System Manager"})) or (
		(user or frappe.session.user) == "Administrator"
	)


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
	own = entity_for_user(user)
	if not procuring_entity or not own or procuring_entity != own:
		frappe.throw(_("Not permitted for this procuring entity"), frappe.PermissionError)
