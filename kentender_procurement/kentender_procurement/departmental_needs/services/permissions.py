from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services.authorization_policy import (
	ResourceContext,
	evaluate_capability,
	require_capability,
	resolve_effective_access,
)
from kentender_procurement.departmental_needs.constants import (
	CAP_CREATE,
	CAP_EDIT_OWN,
	CAP_OVERSIGHT_READ,
	CAP_READ_ACCEPTED_FOR_PLANNING,
	CAP_REVIEW,
	CAP_SUBMIT,
	CAP_VIEW_DEPARTMENT,
	CAP_VIEW_OWN,
	STATE_ACCEPTED,
)
from kentender_procurement.departmental_needs.errors import fail


def actor(user: str | None = None) -> str:
	value = cstr(user or frappe.session.user).strip()
	if not value or value == "Guest":
		fail("NDS_AUTHENTICATION_REQUIRED", "Sign in to access Departmental Needs.")
	return value


def resource(need: Any) -> ResourceContext:
	return ResourceContext(
		"Departmental Need",
		cstr(need.name),
		cstr(need.procuring_entity),
		cstr(need.target_financial_year),
		cstr(need.organisation_unit),
		state=cstr(need.status),
		relationships={"submitted_by": cstr(need.submitted_by)},
	)


def creation_contexts(user: str | None = None) -> list[dict[str, str]]:
	principal = actor(user)
	rows = resolve_effective_access(principal, CAP_CREATE)
	contexts: list[dict[str, str]] = []
	seen: set[tuple[str, str]] = set()
	for row in rows:
		pe, ou = cstr(row.get("procuring_entity_id")), cstr(row.get("organisation_unit_id"))
		if not pe or not ou or (pe, ou) in seen:
			continue
		if frappe.db.get_value("Organisation Unit", ou, "procuring_entity") != pe:
			continue
		seen.add((pe, ou))
		contexts.append({
			"procuring_entity": pe,
			"procuring_entity_label": cstr(frappe.db.get_value("Procuring Entity", pe, "legal_name") or pe),
			"organisation_unit": ou,
			"organisation_unit_label": cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou),
		})
	return sorted(contexts, key=lambda row: (row["procuring_entity_label"], row["organisation_unit_label"]))


def require_create(user: str, pe: str, ou: str, financial_year: str) -> None:
	if frappe.db.get_value("Organisation Unit", ou, "procuring_entity") != pe:
		fail("NDS_ORGANISATION_UNIT_PE_MISMATCH", "The selected department does not belong to the selected Procuring Entity.")
	require_capability(user, CAP_CREATE, ResourceContext("Departmental Need", "new", pe, financial_year, ou))


def can_view(need: Any, user: str) -> tuple[bool, str]:
	"""§6 — a Planner sees only Accepted Needs in their assigned PE; every
	other profile's scope is fully expressed by its capability grant alone.
	This rule lives here, not in each caller, so every view/list/download
	path is scoped identically by construction."""
	ctx = resource(need)
	if cstr(need.submitted_by) == user and evaluate_capability(user, CAP_VIEW_OWN, ctx).allowed:
		return True, "owner"
	for capability, profile in (
		(CAP_VIEW_DEPARTMENT, "department"),
		(CAP_REVIEW, "department"),
		(CAP_READ_ACCEPTED_FOR_PLANNING, "planning"),
		(CAP_OVERSIGHT_READ, "oversight"),
	):
		if profile == "planning" and cstr(need.status) != STATE_ACCEPTED:
			continue
		if evaluate_capability(user, capability, ctx).allowed:
			return True, profile
	return False, "none"


def require_owner_command(need: Any, user: str, capability: str) -> None:
	if cstr(need.submitted_by) != user:
		fail("NDS_NOT_RECORD_OWNER", "Only the submitting user may perform this action.")
	require_capability(user, capability, resource(need))


def owner_capability(action: str) -> str:
	return CAP_EDIT_OWN if action == "edit" else CAP_SUBMIT
