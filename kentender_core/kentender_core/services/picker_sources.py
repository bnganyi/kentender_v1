# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""kentender_core's sources for the shared record picker (see `record_picker`).

System setup's administrators choose a person to assign a responsibility to, and an Organisation Unit
for a unit-scoped responsibility, a home unit and a register filter. None of these is a rule about who
may be *named* in a business process: the gate is the administration surface's own
(`require_assignment_administrator_any`, or `require_configuration_administrator` for a home unit), and
anyone who fails it gets the masked not-found. The saving commands check again.

`core.responsible_user` filters in the database (a site can hold thousands of staff accounts), applying
`record_picker.matches` to what it fetched; the units are a bounded tree, listed whole with their path
from the root so a reader finds a unit by any of its ancestors' names."""

from __future__ import annotations

from typing import Any, Callable

import frappe
from frappe.utils import cstr

from kentender_core.services import record_picker

USER = "core.responsible_user"
UNIT = "core.organisation_unit"
HOME_UNIT = "core.home_unit"
REFERENCE_UNIT = "core.reference_unit"
FETCH = 300
PATH_SEPARATOR = " › "


def sources() -> list[dict[str, Any]]:
	base = "kentender_core.services.picker_sources."
	return [
		{"key": USER, "noun": "user", "plural": "users", "match": "provider", "provider": base + "responsible_users", "resolver": base + "responsible_users_by_id"},
		{"key": UNIT, "noun": "unit", "plural": "units", "rest_title": "Organisation units", "match": "core", "provider": base + "organisation_units"},
		{"key": HOME_UNIT, "noun": "unit", "plural": "units", "rest_title": "Organisation units", "match": "core", "provider": base + "home_units"},
		{"key": REFERENCE_UNIT, "noun": "unit", "plural": "units", "rest_title": "Organisation units", "match": "core", "provider": base + "reference_units"},
	]


def _gate(check: Callable[..., Any], actor: str) -> None:
	"""The administration surface's own gate; a refusal is a masked not-found, so the picker does not confirm that the surface exists."""
	try:
		check(actor)
	except Exception:
		raise frappe.DoesNotExistError("Not found") from None


def _assignment_administrator(actor: str) -> None:
	from kentender_core.services import responsibility_administration

	_gate(responsibility_administration.require_assignment_administrator_any, actor)


def _configuration_administrator(actor: str) -> None:
	from kentender_core.services.site_configuration import require_configuration_administrator

	_gate(require_configuration_administrator, actor)


def _unit_reader(actor: str) -> None:
	"""Organisation Unit's own read rule (a Desk User, never a portal account), asserted as `list_organisation_units` asserts it."""
	if not frappe.has_permission("Organisation Unit", "read", user=actor):
		raise frappe.PermissionError("Organisation Unit")


# -- people -----------------------------------------------------------------------------------


def _user_row(row: Any) -> dict[str, Any]:
	return {"id": row.name, "label": cstr(row.full_name) or row.name, "detail": row.name, "keywords": row.name}


def responsible_users(*, query: str, context: dict, actor: str, limit: int) -> tuple[list[dict[str, Any]], int]:
	"""Enabled staff accounts by name or login: the people a responsibility can be assigned to."""
	_assignment_administrator(actor)
	filters: dict[str, Any] = {"enabled": 1, "user_type": "System User"}
	tokens = record_picker.words(query)
	if not tokens:
		rows = frappe.get_all("User", filters=filters, fields=["name", "full_name"], order_by="full_name asc, name asc", limit_page_length=limit)
		return [_user_row(r) for r in rows], frappe.db.count("User", filters)
	like = f"%{tokens[0]}%"
	fetched = frappe.get_all("User", filters=filters, or_filters=[["full_name", "like", like], ["name", "like", like]], fields=["name", "full_name"],
		order_by="full_name asc, name asc", limit_page_length=FETCH)
	kept = [row for row in map(_user_row, fetched) if record_picker.matches(row, query)]
	return kept[:limit], len(kept)


def responsible_users_by_id(*, ids: list[str], context: dict, actor: str) -> list[dict[str, Any]]:
	_assignment_administrator(actor)
	rows = frappe.get_all("User", filters={"name": ("in", ids), "enabled": 1, "user_type": "System User"}, fields=["name", "full_name"])
	return [_user_row(r) for r in rows]


# -- organisation units -----------------------------------------------------------------------


def _active_units() -> list[dict[str, Any]]:
	"""Active units, each labelled with its path from the root (AUTH-DES-04, AUTH-DES-11)."""
	rows = frappe.get_all("Organisation Unit", fields=["name", "unit_name", "parent_organisation_unit", "status"], order_by="lft asc, unit_name asc", limit_page_length=0)
	by_name = {r.name: r for r in rows}

	def path(name: str) -> str:
		parts: list[str] = []
		seen: set[str] = set()
		while name and name in by_name and name not in seen:
			seen.add(name)
			parts.append(by_name[name].unit_name)
			name = by_name[name].parent_organisation_unit
		return PATH_SEPARATOR.join(reversed(parts))

	return [{"id": r.name, "label": path(r.name), "detail": r.name, "keywords": r.unit_name} for r in rows if r.status == "Active"]


def organisation_units(*, query: str, context: dict, actor: str, limit: int) -> list[dict[str, Any]]:
	_assignment_administrator(actor)
	return _active_units()


def home_units(*, query: str, context: dict, actor: str, limit: int) -> list[dict[str, Any]]:
	_configuration_administrator(actor)
	return _active_units()


def reference_units(*, query: str, context: dict, actor: str, limit: int) -> list[dict[str, Any]]:
	"""Every active unit, for a screen that only needs one named (a budget line's owner): the reference-data endpoint's own rule."""
	_gate(_unit_reader, actor)
	return _active_units()
