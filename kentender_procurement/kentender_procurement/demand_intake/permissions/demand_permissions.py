# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""F1 — Demand row-level visibility (PRD §17.1–17.3) via hooks.

Hooks only *deny* access; DocPerm still grants baseline rights. When no matching
User Permission rows exist for Procuring Entity / Department, entity/department
filters are not applied (backward compatible for dev sites).
"""

from __future__ import annotations

import frappe


def _user_permission_values(user: str, allow: str) -> set[str] | None:
	rows = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": allow},
		pluck="for_value",
	)
	if not rows:
		return None
	return set(rows)


def _dia_business_roles(roles: set[str]) -> bool:
	return bool(
		roles
		& {
			"Requisitioner",
			"Department Approver",
			"Finance Reviewer",
			"Procurement Planner",
			"Auditor",
		}
	)


def _entity_gate_sql(user: str) -> str | None:
	ents = _user_permission_values(user, "Procuring Entity")
	if not ents:
		return None
	inlist = ", ".join(frappe.db.escape(e) for e in sorted(ents))
	return f"`tabDemand`.`procuring_entity` IN ({inlist})"


def get_permission_query_conditions_for_demand(user: str | None = None) -> str:
	"""Restrict list views / counts to rows the user may open (F1 / F3)."""
	if not user:
		user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""
	roles = set(frappe.get_roles(user))
	if not _dia_business_roles(roles):
		return ""

	ors: list[str] = []
	if "Requisitioner" in roles:
		ors.append(f"`tabDemand`.`requested_by` = {frappe.db.escape(user)}")
	if "Department Approver" in roles:
		depts = _user_permission_values(user, "Procuring Department")
		if depts:
			inlist = ", ".join(frappe.db.escape(d) for d in sorted(depts))
			ors.append(f"`tabDemand`.`requesting_department` IN ({inlist})")
		else:
			ors.append("1=1")
	if "Finance Reviewer" in roles or "Procurement Planner" in roles:
		ors.append("1=1")
	if "Auditor" in roles:
		ors.append("1=1")
	if not ors:
		return ""
	core = "(" + " OR ".join(ors) + ")"
	ent = _entity_gate_sql(user)
	if ent:
		return f"({core}) AND ({ent})"
	return core


def _doc_visible_to_dia_roles(doc, user: str, roles: set[str]) -> bool:
	ent = doc.get("procuring_entity")
	ents = _user_permission_values(user, "Procuring Entity")
	if ents is not None and ent and ent not in ents:
		return False

	visible = False
	if "Requisitioner" in roles and (doc.get("requested_by") or "") == user:
		visible = True
	if "Department Approver" in roles:
		depts = _user_permission_values(user, "Procuring Department")
		dept = doc.get("requesting_department")
		if depts is None or (dept and dept in depts):
			visible = True
	if "Finance Reviewer" in roles or "Procurement Planner" in roles:
		visible = True
	if "Auditor" in roles:
		visible = True
	return visible


def demand_has_permission(doc, ptype=None, user=None, debug=False, **kwargs):
	"""F1 — deny read/write when the row is outside the user's DIA scope."""
	if not doc or not getattr(doc, "doctype", None) or doc.doctype != "Demand":
		return True
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles:
		return True
	if not _dia_business_roles(roles):
		return True
	if not _doc_visible_to_dia_roles(doc, user, roles):
		return False
	return True
