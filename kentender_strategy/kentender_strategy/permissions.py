# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Entity-scoped permission_query_conditions and has_permission for Strategy DocTypes."""

from __future__ import annotations

import frappe


def _is_unrestricted(user: str) -> bool:
	if user == "Administrator":
		return True
	return "System Manager" in frappe.get_roles(user)


def _user_allowed_procuring_entities(user: str) -> list[str]:
	"""Primary entity from User custom field plus User Permission rows."""
	out: set[str] = set()
	if frappe.db.has_column("User", "kt_procuring_entity"):
		pe = frappe.db.get_value("User", user, "kt_procuring_entity")
		if pe:
			out.add(pe)
	for row in frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Procuring Entity"},
		pluck="for_value",
	):
		if row:
			out.add(row)
	return list(out)


def _plan_entity(plan_name: str | None) -> str | None:
	if not plan_name:
		return None
	return frappe.db.get_value("Strategic Plan", plan_name, "procuring_entity")


def _sql_in_strings(values: list[str]) -> str:
	# frappe.db.escape already returns a single-quoted SQL literal (MariaDB/MySQLdb and PyMySQL).
	# Do not wrap again — double quotes break IN (...) and cause ProgrammingError near e.g. 'MOH'')).
	return ", ".join(frappe.db.escape(a, percent=False) for a in values)


def get_strategic_plan_permission_query_conditions(user: str) -> str:
	if _is_unrestricted(user):
		return ""
	allowed = _user_allowed_procuring_entities(user)
	if not allowed:
		return "1=0"
	return f"`tabStrategic Plan`.procuring_entity in ({_sql_in_strings(allowed)})"


def get_strategy_program_permission_query_conditions(user: str) -> str:
	if _is_unrestricted(user):
		return ""
	allowed = _user_allowed_procuring_entities(user)
	if not allowed:
		return "1=0"
	inn = _sql_in_strings(allowed)
	return f"""`tabStrategy Program`.strategic_plan in (
		select name from `tabStrategic Plan` where procuring_entity in ({inn})
	)"""


def get_strategy_objective_permission_query_conditions(user: str) -> str:
	if _is_unrestricted(user):
		return ""
	allowed = _user_allowed_procuring_entities(user)
	if not allowed:
		return "1=0"
	inn = _sql_in_strings(allowed)
	return f"""`tabStrategy Objective`.strategic_plan in (
		select name from `tabStrategic Plan` where procuring_entity in ({inn})
	)"""


def get_strategy_target_permission_query_conditions(user: str) -> str:
	if _is_unrestricted(user):
		return ""
	allowed = _user_allowed_procuring_entities(user)
	if not allowed:
		return "1=0"
	inn = _sql_in_strings(allowed)
	return f"""`tabStrategy Target`.strategic_plan in (
		select name from `tabStrategic Plan` where procuring_entity in ({inn})
	)"""


def has_strategic_plan_permission(doc, user: str | None = None, ptype: str | None = None, **kwargs) -> bool:
	"""Return False to deny entity-scoped access; True to defer to role permissions."""
	user = user or frappe.session.user
	if not doc:
		return True
	if _is_unrestricted(user):
		return True
	ent = getattr(doc, "procuring_entity", None) or doc.get("procuring_entity")
	allowed = _user_allowed_procuring_entities(user)
	if not allowed:
		return False
	return ent in allowed


def has_strategy_program_permission(doc, user: str | None = None, ptype: str | None = None, **kwargs) -> bool:
	user = user or frappe.session.user
	if not doc:
		return True
	if _is_unrestricted(user):
		return True
	plan = getattr(doc, "strategic_plan", None) or doc.get("strategic_plan")
	ent = _plan_entity(plan)
	allowed = _user_allowed_procuring_entities(user)
	if not allowed or not ent:
		return False
	return ent in allowed


def has_strategy_objective_permission(doc, user: str | None = None, ptype: str | None = None, **kwargs) -> bool:
	user = user or frappe.session.user
	if not doc:
		return True
	if _is_unrestricted(user):
		return True
	plan = getattr(doc, "strategic_plan", None) or doc.get("strategic_plan")
	ent = _plan_entity(plan)
	allowed = _user_allowed_procuring_entities(user)
	if not allowed or not ent:
		return False
	return ent in allowed


def has_strategy_target_permission(doc, user: str | None = None, ptype: str | None = None, **kwargs) -> bool:
	user = user or frappe.session.user
	if not doc:
		return True
	if _is_unrestricted(user):
		return True
	plan = getattr(doc, "strategic_plan", None) or doc.get("strategic_plan")
	ent = _plan_entity(plan)
	allowed = _user_allowed_procuring_entities(user)
	if not allowed or not ent:
		return False
	return ent in allowed
