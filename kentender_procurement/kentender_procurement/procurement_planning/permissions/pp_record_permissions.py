# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase E1 — Row-level visibility + ``has_permission`` for Procurement Plan / Package.

Entity scope uses **User Permission** on **Procuring Entity** (same pattern as Demand).
Hooks only *deny* where the matrix requires it; DocPerm supplies baseline grants.

Auditors without entity User Permissions see **no** plans/packages (strict).
"""

from __future__ import annotations

import frappe

_PP_ROLES = frozenset(
	(
		"Procurement Planner",
		"Procurement Officer",
		"Planning Authority",
		"Auditor",
		"Administrator",
		"System Manager",
	)
)


def _user_permission_entities(user: str) -> set[str] | None:
	rows = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Procuring Entity"},
		pluck="for_value",
	)
	if not rows:
		return None
	return set(rows)


def _entity_in_clause(values: set[str], *, table_alias: str, column: str) -> str:
	col = f"`{table_alias}`.`{column}`" if table_alias else f"`tabProcurement Plan`.`{column}`"
	inlist = ", ".join(frappe.db.escape(e) for e in sorted(values))
	return f"ifnull({col}, '') IN ({inlist})"


def get_permission_query_conditions_for_procurement_plan(user: str | None = None) -> str:
	"""Restrict list views / link queries to allowed procuring entities."""
	if not user:
		user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""
	roles = set(frappe.get_roles(user))
	if not roles & _PP_ROLES:
		return ""

	ents = _user_permission_entities(user)
	if "Auditor" in roles:
		if not ents:
			return "1=0"
		return _entity_in_clause(ents, table_alias="tabProcurement Plan", column="procuring_entity")

	if ents:
		return _entity_in_clause(ents, table_alias="tabProcurement Plan", column="procuring_entity")
	return ""


def get_permission_query_conditions_for_procurement_package(user: str | None = None) -> str:
	"""Restrict packages by their plan's procuring entity."""
	if not user:
		user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""
	roles = set(frappe.get_roles(user))
	if not roles & _PP_ROLES:
		return ""

	ents = _user_permission_entities(user)
	join = (
		"exists (select 1 from `tabProcurement Plan` `_pp_plan` where "
		"`_pp_plan`.name = `tabProcurement Package`.plan_id and {ent_clause})"
	)

	if "Auditor" in roles:
		if not ents:
			return "1=0"
		inlist = ", ".join(frappe.db.escape(e) for e in sorted(ents))
		ent_clause = f"ifnull(`_pp_plan`.procuring_entity, '') IN ({inlist})"
		return join.format(ent_clause=ent_clause)

	if ents:
		inlist = ", ".join(frappe.db.escape(e) for e in sorted(ents))
		ent_clause = f"ifnull(`_pp_plan`.procuring_entity, '') IN ({inlist})"
		return join.format(ent_clause=ent_clause)
	return ""


def _plan_entity_for_package_doc(doc) -> str | None:
	pid = doc.get("plan_id") if not hasattr(doc, "plan_id") else doc.plan_id
	if not pid:
		return None
	return frappe.db.get_value("Procurement Plan", pid, "procuring_entity")


def _entity_read_allowed(user: str, roles: set[str], entity_value: str | None) -> bool:
	"""Return True if read is allowed (hook must return explicit bool for Frappe)."""
	if user == "Administrator" or "System Manager" in roles:
		return True
	ents = _user_permission_entities(user)
	if ents is not None:
		return bool(entity_value and entity_value in ents)
	if "Auditor" in roles:
		return False
	return True


def procurement_plan_has_permission(doc, ptype="read", user=None, **kwargs):
	"""Controller hook: return False to deny; True lets DocPerm decide (cannot grant extra rights)."""
	if not doc or getattr(doc, "doctype", None) != "Procurement Plan":
		return True
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if user == "Administrator":
		return True
	if "System Manager" in roles:
		return True

	if ptype == "create":
		return bool(roles & {"Procurement Planner", "Administrator", "System Manager"})

	ent = doc.get("procuring_entity")
	if ptype == "read":
		return _entity_read_allowed(user, roles, ent)

	if ptype == "write":
		if "Auditor" in roles:
			return False
		if "Procurement Officer" in roles:
			return False
		st = (doc.get("status") or "").strip()
		if "Planning Authority" in roles:
			return st in ("Submitted", "Approved")
		if "Procurement Planner" in roles:
			return st == "Draft"
		return False

	return True


def procurement_package_has_permission(doc, ptype="read", user=None, **kwargs):
	if not doc or getattr(doc, "doctype", None) != "Procurement Package":
		return True
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if user == "Administrator":
		return True
	if "System Manager" in roles:
		return True

	if ptype == "create":
		return bool(roles & {"Procurement Planner", "Administrator", "System Manager"})

	ent = _plan_entity_for_package_doc(doc)
	if ptype == "read":
		return _entity_read_allowed(user, roles, ent)

	if ptype == "write":
		if "Auditor" in roles:
			return False
		st = (doc.get("status") or "").strip()
		if "Procurement Planner" in roles:
			return st in ("Draft", "Completed", "Returned")
		if "Planning Authority" in roles:
			return st == "Submitted"
		if "Procurement Officer" in roles:
			return st == "Approved"
		return False

	return True
