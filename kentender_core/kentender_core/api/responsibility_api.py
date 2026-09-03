"""AUTH-ADR-001 v1.6 §9.2/§14.2–§14.4 — whitelisted responsibility endpoints.

Thin wrappers over :mod:`kentender_core.services.responsibility_administration`
and the shared authorization service. Explicit signatures (no ``**kwargs``) so
Frappe filters the transport fields (``cmd``/``csrf_token``) out of the call
itself — a ``**kwargs`` endpoint forwards them into the service and fails with
a 500 that no direct-service test can see.

Every endpoint re-derives the actor from the session and re-checks the grant
authority inside the service; nothing here trusts a client-supplied actor,
assignment id, scope or permitted-action list (§5.5). There is no Procuring
Entity parameter anywhere: one site is one PE.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services import responsibility_administration as administration
from kentender_core.services.authorization import diagnose_user


@frappe.whitelist()
def registry_options() -> list[dict[str, Any]]:
	"""The registered responsibilities, each with the scope the registry requires."""
	administration.require_assignment_administrator_any()
	return administration.registry_options()


@frappe.whitelist()
def user_responsibilities(target_user: str) -> dict[str, Any]:
	"""§9.1 — active, scheduled, expired and revoked assignments, plus
	projections, conflicts and the rows still awaiting migration."""
	administration.require_assignment_administrator_any()
	return diagnose_user(target_user)


@frappe.whitelist()
def grant_responsibility(
	user: str,
	business_role: str,
	organisation_unit: str | None = None,
	appointment_type: str = "Permanent",
	authority_reference: str | None = None,
	effective_from: str | None = None,
	effective_to: str | None = None,
) -> dict[str, Any]:
	"""§9.2 `AssignResponsibility` — validated and audited in one transaction."""
	return administration.grant(
		user=user,
		business_role=business_role,
		organisation_unit=organisation_unit or "",
		appointment_type=appointment_type,
		authority_reference=authority_reference or "",
		effective_from=effective_from,
		effective_to=effective_to,
	)


@frappe.whitelist()
def revoke_responsibility(
	assignment: str, reason: str, expected_version: str | None = None
) -> dict[str, Any]:
	"""§9.2 `RevokeResponsibility` — one explicit action with a 10–500 char reason."""
	return administration.revoke(
		assignment, reason=reason, expected_version=expected_version or ""
	)


@frappe.whitelist()
def list_user_responsibilities(
	search: str | None = None,
	organisation_unit: str | None = None,
	business_role: str | None = None,
	status: str | None = None,
	start: int = 0,
	page_length: int = 50,
) -> dict[str, Any]:
	"""§9.2 `ListUserResponsibilities` — rows and counts from one predicate."""
	return administration.list_user_responsibilities(
		search=search or "",
		organisation_unit=organisation_unit or "",
		business_role=business_role or "",
		status=status or "",
		start=int(start or 0),
		page_length=int(page_length or 50),
	)


@frappe.whitelist()
def preview_responsibility_assignment(
	user: str | None = None,
	business_role: str | None = None,
	organisation_unit: str | None = None,
	appointment_type: str = "Permanent",
	effective_from: str | None = None,
	effective_to: str | None = None,
	authority_reference: str | None = None,
) -> dict[str, Any]:
	"""§9.2 `PreviewResponsibilityAssignment` — validate and describe; create nothing."""
	return administration.preview_assignment(
		user=user or "",
		business_role=business_role or "",
		organisation_unit=organisation_unit or "",
		appointment_type=appointment_type,
		effective_from=effective_from,
		effective_to=effective_to,
		authority_reference=authority_reference or "",
	)


@frappe.whitelist()
def get_responsibility_assignment(assignment: str) -> dict[str, Any]:
	"""§9.2 `GetResponsibilityAssignment` — full detail, audit and diagnostics."""
	return administration.get_assignment_detail(assignment)


@frappe.whitelist()
def assignment_form_options() -> dict[str, Any]:
	"""Everything the assign dialog and the register filters offer.

	Served from the server so the offer can never drift from the code-owned
	registry or show an inactive Organisation Unit (§14.3).
	"""
	administration.require_assignment_administrator_any()
	from kentender_core.services.organisation_structure import _path_of

	units = [
		{
			"id": row["name"],
			"label": row["unit_name"],
			# AUTH-DES-04 shows the selected unit as its full path.
			"path_label": " › ".join(_path_of(row["name"])),
			"parent": row.get("parent_organisation_unit") or "",
		}
		for row in frappe.get_all(
			"Organisation Unit",
			filters={"status": "Active"},
			fields=["name", "unit_name", "parent_organisation_unit"],
			order_by="lft asc, unit_name asc",
			limit_page_length=0,
		)
	]
	return {
		"responsibilities": administration.registry_options(),
		"organisation_units": units,
		"statuses": list(administration.DERIVED_STATUSES),
	}


@frappe.whitelist()
def search_users(query: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
	"""§14.3 control 1 — enabled System Users, by full name or login."""
	administration.require_assignment_administrator_any()
	filters: dict[str, Any] = {"enabled": 1, "user_type": "System User"}
	needle = (query or "").strip()
	rows = frappe.get_all(
		"User",
		filters=filters,
		or_filters=(
			[["full_name", "like", f"%{needle}%"], ["name", "like", f"%{needle}%"]]
			if needle
			else None
		),
		fields=["name", "full_name"],
		order_by="full_name asc",
		limit_page_length=int(limit or 20),
	)
	return [{"id": row["name"], "label": row["full_name"] or row["name"]} for row in rows]
