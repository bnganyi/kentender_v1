# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Resolve User Scope Assignment → Organisation Unit / PE access."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def _is_admin(user: str) -> bool:
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)


def descendant_org_units(root: str) -> set[str]:
	"""Return root + all descendants, from the nested-set range (AUTH-ADR-001 v1.2 §6.2).

	One indexed `lft`/`rgt` comparison replaces the breadth-first walk this used
	to do, which issued a query per level on every scope check. A node whose
	range has not been stamped yet (`rgt` still 0, before the nested-set patch
	runs) would otherwise match nothing at all, so fall back to the node itself
	rather than silently reporting an empty subtree.
	"""
	if not root:
		return set()
	bounds = frappe.db.get_value("Organisation Unit", root, ["lft", "rgt"], as_dict=True)
	if not bounds or not bounds.rgt:
		return {root}
	return set(
		frappe.get_all(
			"Organisation Unit",
			filters={"lft": (">=", bounds.lft), "rgt": ("<=", bounds.rgt)},
			pluck="name",
			limit_page_length=0,
		)
	) | {root}


def ownership_path_label(org_unit: str | None) -> str:
	"""Display path using configured unit-type labels (Name · Type · …)."""
	if not org_unit or not frappe.db.exists("Organisation Unit", org_unit):
		return ""
	parts: list[str] = []
	cur = org_unit
	guard = 0
	while cur and guard < 12:
		row = frappe.db.get_value(
			"Organisation Unit",
			cur,
			["unit_name", "unit_type", "parent_organisation_unit"],
			as_dict=True,
		)
		if not row:
			break
		type_label = (
			frappe.db.get_value("Organisation Unit Type", row.unit_type, "display_label")
			or row.unit_type
			or ""
		)
		parts.append(f"{row.unit_name} ({type_label})" if type_label else row.unit_name)
		cur = row.parent_organisation_unit
		guard += 1
	return " › ".join(reversed(parts))


def user_scope_rows(user: str | None = None) -> list[dict[str, Any]]:
	user = user or frappe.session.user
	if not frappe.db.exists("DocType", "User Scope Assignment"):
		return []
	return frappe.get_all(
		"User Scope Assignment",
		filters={"user": user},
		fields=[
			"role",
			"procuring_entity",
			"organisation_unit",
			"include_descendants",
			"effective_from",
			"effective_to",
		],
	)


def permitted_procuring_entities(user: str | None = None) -> set[str] | None:
	"""None = unrestricted (admin). Empty set = no PE assignments."""
	user = user or frappe.session.user
	if _is_admin(user):
		return None
	rows = user_scope_rows(user)
	if not rows:
		# Fall back to User Permission PEs if no scope rows yet. ALL rows: the
		# earlier single-row get_value silently narrowed a user permitted
		# several entities to one arbitrary one (CTX-CHG-001 rule 1 — the
		# permissions, not an accident of row order, determine access).
		pes = frappe.get_all(
			"User Permission",
			filters={"user": user, "allow": "Procuring Entity"},
			pluck="for_value",
		)
		return {pe for pe in pes if pe}
	return {r.procuring_entity for r in rows if r.procuring_entity}


def permitted_org_units(
	user: str | None = None,
	*,
	procuring_entity: str | None = None,
) -> set[str] | None:
	"""
	Org units the user may maintain (unit-scoped).

	None = entity-wide within permitted PEs (reviewer/viewer/authority with blank OU).
	Empty set = no unit access (and not entity-wide).
	"""
	user = user or frappe.session.user
	if _is_admin(user):
		return None
	rows = user_scope_rows(user)
	if procuring_entity:
		rows = [r for r in rows if r.procuring_entity == procuring_entity]
	if not rows:
		return set()
	# Any blank organisation_unit assignment ⇒ entity-wide for that PE.
	if any(not r.organisation_unit for r in rows):
		return None
	units: set[str] = set()
	for r in rows:
		ou = r.organisation_unit
		if not ou:
			continue
		if int(r.include_descendants or 0):
			units |= descendant_org_units(ou)
		else:
			units.add(ou)
	return units


def can_access_owned_record(
	*,
	procuring_entity: str | None,
	owner_org_unit: str | None,
	user: str | None = None,
	require_write: bool = False,
) -> bool:
	"""PE + optional owner_org_unit gate for Strategy/Budget owned records."""
	user = user or frappe.session.user
	if _is_admin(user):
		return True
	pes = permitted_procuring_entities(user)
	if pes is not None and (not procuring_entity or procuring_entity not in pes):
		return False
	units = permitted_org_units(user, procuring_entity=procuring_entity)
	if units is None:
		# Entity-wide — may access any unit (or entity-owned blank) in PE.
		return True
	if not owner_org_unit:
		# Entity-owned header: unit officers do not get write; read allowed for
		# entity-wide only (already handled). Officers with unit scope: deny write.
		return not require_write
	return owner_org_unit in units


def assert_can_access_owned_record(
	*,
	procuring_entity: str | None,
	owner_org_unit: str | None,
	user: str | None = None,
	require_write: bool = False,
) -> None:
	if not can_access_owned_record(
		procuring_entity=procuring_entity,
		owner_org_unit=owner_org_unit,
		user=user,
		require_write=require_write,
	):
		frappe.throw(_("Not permitted for this organisational scope"), frappe.PermissionError)


def strategy_items_for_unit(
	organisation_unit: str,
	*,
	include_descendants: bool = True,
) -> list[dict[str, Any]]:
	"""Resolve Strategy Scope Assignment rows applicable to a unit."""
	if not frappe.db.exists("DocType", "Strategy Scope Assignment"):
		return []
	units = (
		descendant_org_units(organisation_unit)
		if include_descendants
		else {organisation_unit}
	)
	# Assignments whose organisation_unit is an ancestor (with include_descendants)
	# or exact match.
	rows = frappe.get_all(
		"Strategy Scope Assignment",
		fields=[
			"name",
			"strategy_doctype",
			"strategy_item",
			"strategy_item_code",
			"organisation_unit",
			"include_descendants",
			"applicability",
			"procuring_entity",
			"plan_version",
		],
	)
	out: list[dict[str, Any]] = []
	for r in rows:
		assigned = r.organisation_unit
		if not assigned:
			continue
		if assigned in units:
			out.append(r)
			continue
		if int(r.include_descendants or 0):
			if organisation_unit in descendant_org_units(assigned):
				out.append(r)
	return out
