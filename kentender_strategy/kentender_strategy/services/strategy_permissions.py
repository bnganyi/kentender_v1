# Copyright (c) 2026, KenTender and contributors
"""REQ §12 role helpers for Strategy MVP-1, on AUTH-ADR-001 v1.6 (CU-303).

One site is one Procuring Entity, so every PE-scope helper this module used
to export (`entity_for_user`, `assert_entity_in_scope`,
`has_cross_entity_authority`, `assert_org_unit_in_scope`) is gone with the
concepts behind it: there is no working context, no per-user PE set, and no
cross-entity authority. What remains are plain role checks used only to
decide what to OFFER — every command re-authorises through
`strategy_authorization`'s `require_*` helpers, which resolve real
User Responsibility Assignments.
"""

from __future__ import annotations

import frappe
from frappe import _

ROLE_VIEWER = "Strategy Viewer"
ROLE_PLANNING = "Planning Authority"
ROLE_AUDITOR = "Auditor"


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
	"""REQ §12 — offer create/edit of Draft plans to Strategy Author holders.

	Offer-only: the Frappe Role exists purely as the projection of an Enabled
	Site-wide assignment (v1.6 §5.2); the command itself re-authorises via
	`require_plan_create_capability`/`require_plan_version_capability`, so a
	System Manager sees no authoring offer and holds no authoring power."""
	return "Strategy Author" in user_roles()


def can_create_successor_plan() -> bool:
	"""STR-UI-02 — Create successor Draft from Active/Approved: Strategy Author."""
	return can_edit_draft_plan()


def ownership_path_for_unit(owner_org_unit: str | None) -> str:
	"""Display path for a plan's owning Organisation Unit (site-local tree)."""
	if not owner_org_unit:
		return ""
	from kentender_core.services.organisation_structure import _path_of

	return " › ".join(_path_of(owner_org_unit))
