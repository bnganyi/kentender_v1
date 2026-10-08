"""CFG-CHG-002 v0.19 §7.1–7.2 — whitelisted endpoints for the Staff home units
tab of System setup (AUTH-ADR-001 v1.12 AUTH-DES-10 and AUTH-DES-11).

Thin wrappers over :mod:`kentender_core.services.staff_home_unit` with
explicit signatures (no ``**kwargs``): every authority check, validation and
audit write happens in the service. A denial on the read is returned as data
(KT-STD-001 §3A.2); the command raises its CFG error."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services import staff_home_unit as home


def _is_setup_actor() -> bool:
	user = frappe.session.user
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)


@frappe.whitelist()
def staff_home_units(search: str | None = None, not_recorded: int | str | None = None, page: int | str | None = None, page_length: int | str | None = None) -> dict[str, Any]:
	if not _is_setup_actor():
		return {"outcome": "FORBIDDEN"}
	return {"outcome": "OK", **home.list_staff_home_units(search=search or "", not_recorded=bool(int(not_recorded or 0)), page=int(page or 1), page_length=int(page_length or 50)),
		"units": _active_units()}


def _active_units() -> list[dict[str, str]]:
	"""The Active units a home unit may be set to, each labelled with its path from the root (AUTH-DES-11)."""
	rows = frappe.get_all("Organisation Unit", fields=["name", "unit_name", "parent_organisation_unit", "status"], order_by="lft asc", limit_page_length=0)
	by_name = {r.name: r for r in rows}

	def path(name: str) -> str:
		parts, seen = [], set()
		while name and name in by_name and name not in seen:
			seen.add(name)
			parts.append(by_name[name].unit_name)
			name = by_name[name].parent_organisation_unit
		return " › ".join(reversed(parts))

	return [{"value": r.name, "label": path(r.name)} for r in rows if r.status == "Active"]


@frappe.whitelist(methods=["POST"])
def set_staff_home_unit(user: str, organisation_unit: str | None = None, expected_token: str | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
	return home.set_staff_home_organisation_unit(user=user, organisation_unit=organisation_unit or "", expected_token=expected_token,
		idempotency_key=idempotency_key or "")
