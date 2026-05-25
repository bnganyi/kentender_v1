# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-015 — Entity and department scope checks for Procurement Planning."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PlanningPermission,
)

# Roles with full PP entity-scoped access (department not required for writes/reads).
_PP_ENTITY_SCOPED_ROLES = frozenset(
	(
		"Procurement Planner",
		"Planning Reviewer",
		"Planning Authority",
		"Procurement Officer",
		"Tender Manager",
		"Budget Officer",
		"Finance Reviewer",
		"Auditor",
	)
)

# Roles limited to explicit department membership for sensitive reads.
_DEPARTMENT_LIMITED_ROLES = frozenset(("Department Approver", "Requisitioner"))

_MOE_ENTITY_ALIASES = frozenset(("MOH", "PE-MOH"))


def _norm(value: str | None) -> str:
	return (value or "").strip()


def _session_user(user: str | None) -> str:
	return _norm(user) or _norm(frappe.session.user)


def _is_break_glass(user: str) -> bool:
	return user == "Administrator"


def _is_unrestricted_read(user: str) -> bool:
	if _is_break_glass(user):
		return True
	return "System Manager" in frappe.get_roles(user)


def _expand_entity_aliases(entities: set[str]) -> set[str]:
	expanded = set(entities)
	if expanded & _MOE_ENTITY_ALIASES:
		expanded |= _MOE_ENTITY_ALIASES
	return expanded


def _user_permission_values(user: str, allow: str) -> set[str]:
	rows = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": allow},
		pluck="for_value",
	)
	return {_norm(r) for r in rows if _norm(r)}


def get_user_allowed_entities(user: str | None = None) -> set[str] | None:
	"""Return explicit entity allow-list, or None when no scope is configured."""
	user = _session_user(user)
	if _is_break_glass(user):
		return None

	allowed: set[str] = set()
	if frappe.db.has_column("User", "kt_procuring_entity"):
		pe = _norm(frappe.db.get_value("User", user, "kt_procuring_entity"))
		if pe:
			allowed.add(pe)
	allowed |= _user_permission_values(user, "Procuring Entity")
	if not allowed:
		return None
	return _expand_entity_aliases(allowed)


def get_user_allowed_departments(user: str | None = None) -> set[str] | None:
	"""Return explicit department allow-list, or None when no scope is configured."""
	user = _session_user(user)
	if _is_break_glass(user):
		return None

	allowed: set[str] = set()
	if frappe.db.has_column("User", "kt_primary_department"):
		dept = _norm(frappe.db.get_value("User", user, "kt_primary_department"))
		if dept:
			allowed.add(dept)
	allowed |= _user_permission_values(user, "Procuring Department")
	if not allowed:
		return None
	return allowed


def entity_in_user_scope(entity: str | None, user: str | None = None) -> bool:
	allowed = get_user_allowed_entities(user)
	if allowed is None:
		return True
	record_entity = _norm(entity)
	if not record_entity:
		return False
	return bool(_expand_entity_aliases({record_entity}) & allowed)


def department_in_user_scope(department: str | None, user: str | None = None) -> bool:
	allowed = get_user_allowed_departments(user)
	if allowed is None:
		return True
	record_dept = _norm(department)
	if not record_dept:
		return False
	return record_dept in allowed


def _deny_out_of_scope() -> None:
	frappe.throw(
		_("{0}: Out of scope.").format(PlanningPermission.OUT_OF_SCOPE),
		frappe.PermissionError,
	)


def assert_entity_in_scope(entity: str | None, *, user: str | None = None) -> None:
	if entity_in_user_scope(entity, user):
		return
	_deny_out_of_scope()


def _resolve_plan_entity(plan_doc_or_code) -> str | None:
	if isinstance(plan_doc_or_code, str):
		code = _norm(plan_doc_or_code)
		if not code:
			return None
		if frappe.db.exists("Procurement Plan", code):
			return frappe.db.get_value("Procurement Plan", code, "procuring_entity")
		return frappe.db.get_value(
			"Procurement Plan", {"plan_code": code}, "procuring_entity"
		)
	ent = getattr(plan_doc_or_code, "procuring_entity", None) or plan_doc_or_code.get(
		"procuring_entity"
	)
	return _norm(ent) or None


def _resolve_demand_entity(demand_doc_or_code) -> str | None:
	if isinstance(demand_doc_or_code, str):
		code = _norm(demand_doc_or_code)
		if not code:
			return None
		if frappe.db.exists("Demand", code):
			return frappe.db.get_value("Demand", code, "procuring_entity")
		return frappe.db.get_value("Demand", {"demand_id": code}, "procuring_entity")
	return _norm(
		getattr(demand_doc_or_code, "procuring_entity", None)
		or demand_doc_or_code.get("procuring_entity")
	) or None


def _resolve_package_entity(package_doc_or_code) -> str | None:
	if isinstance(package_doc_or_code, str):
		code = _norm(package_doc_or_code)
		if not code:
			return None
		plan_id = frappe.db.get_value("Procurement Package", code, "plan_id")
		if plan_id:
			return _resolve_plan_entity(plan_id)
		return None
	plan_id = getattr(package_doc_or_code, "plan_id", None) or package_doc_or_code.get("plan_id")
	if plan_id:
		return _resolve_plan_entity(plan_id)
	return None


def _resolve_package_department(package_doc_or_code) -> str | None:
	package_code = None
	if isinstance(package_doc_or_code, str):
		package_code = _norm(package_doc_or_code)
	elif package_doc_or_code:
		package_code = _norm(
			getattr(package_doc_or_code, "package_code", None)
			or package_doc_or_code.get("package_code")
			or package_doc_or_code.get("name")
		)
	if not package_code:
		return None

	dept = frappe.db.get_value(
		"Procurement Package Line",
		{"package_id": package_code, "is_active": 1},
		"department",
		order_by="creation asc",
	)
	if dept:
		return _norm(dept)

	demand_name = frappe.db.get_value(
		"Procurement Package Line",
		{"package_id": package_code, "is_active": 1},
		"demand_id",
		order_by="creation asc",
	)
	if demand_name:
		return _norm(frappe.db.get_value("Demand", demand_name, "requesting_department"))
	return None


def assert_may_act_on_procurement_plan(plan_doc_or_code, *, user: str | None = None) -> None:
	assert_entity_in_scope(_resolve_plan_entity(plan_doc_or_code), user=user)


def assert_may_act_on_procurement_package(package_doc_or_code, *, user: str | None = None) -> None:
	assert_entity_in_scope(_resolve_package_entity(package_doc_or_code), user=user)


def assert_may_act_on_demand(demand_doc_or_code, *, user: str | None = None) -> None:
	assert_entity_in_scope(_resolve_demand_entity(demand_doc_or_code), user=user)


def assert_may_act_on_planning_inclusion(
	demand_code: str,
	plan_code: str,
	*,
	user: str | None = None,
) -> None:
	assert_may_act_on_demand(demand_code, user=user)
	assert_may_act_on_procurement_plan(plan_code, user=user)


def _department_limited_read_allowed(
	*,
	user: str,
	entity: str | None,
	department: str | None,
) -> bool:
	if not entity_in_user_scope(entity, user):
		return False
	return department_in_user_scope(department, user)


def assert_may_read_package_review_decision(review_doc_or_code, *, user: str | None = None) -> None:
	user = _session_user(user)
	if _is_break_glass(user) or _is_unrestricted_read(user):
		return

	if isinstance(review_doc_or_code, str):
		code = _norm(review_doc_or_code)
		if not code or not frappe.db.exists("Package Review Decision", code):
			_deny_out_of_scope()
		review = frappe.get_doc("Package Review Decision", code)
	else:
		review = review_doc_or_code

	package_code = _norm(review.get("package_code"))
	if not package_code:
		_deny_out_of_scope()

	entity = _resolve_package_entity(package_code)
	department = _resolve_package_department(package_code)
	roles = set(frappe.get_roles(user))

	if roles & _DEPARTMENT_LIMITED_ROLES:
		if _department_limited_read_allowed(user=user, entity=entity, department=department):
			return
		_deny_out_of_scope()

	if roles & _PP_ENTITY_SCOPED_ROLES:
		assert_entity_in_scope(entity, user=user)
		return

	_deny_out_of_scope()


def _entity_in_clause_sql(values: set[str], *, table_alias: str, column: str) -> str:
	col = f"`{table_alias}`.`{column}`"
	inlist = ", ".join(frappe.db.escape(e) for e in sorted(values))
	return f"ifnull({col}, '') IN ({inlist})"


def get_permission_query_conditions_for_package_review_decision(user: str | None = None) -> str:
	"""Restrict review-decision list reads by package entity (and department for limited roles)."""
	user = _session_user(user)
	if _is_unrestricted_read(user):
		return ""

	roles = set(frappe.get_roles(user))
	if not (roles & (_PP_ENTITY_SCOPED_ROLES | _DEPARTMENT_LIMITED_ROLES)):
		return ""

	allowed_entities = get_user_allowed_entities(user)
	if allowed_entities is not None and not allowed_entities:
		return "1=0"

	entity_list = sorted(allowed_entities) if allowed_entities else []
	if entity_list:
		inlist = ", ".join(frappe.db.escape(e) for e in entity_list)
		entity_clause = (
			f"exists (select 1 from `tabProcurement Package` `_pp_pkg` "
			f"inner join `tabProcurement Plan` `_pp_plan` on `_pp_plan`.name = `_pp_pkg`.plan_id "
			f"where `_pp_pkg`.package_code = `tabPackage Review Decision`.package_code "
			f"and ifnull(`_pp_plan`.procuring_entity, '') IN ({inlist}))"
		)
	else:
		entity_clause = "1=1"

	if roles & _DEPARTMENT_LIMITED_ROLES:
		allowed_depts = get_user_allowed_departments(user)
		if allowed_depts is not None and not allowed_depts:
			return "1=0"
		if allowed_depts:
			dept_inlist = ", ".join(frappe.db.escape(d) for d in sorted(allowed_depts))
			dept_clause = (
				f"exists (select 1 from `tabProcurement Package Line` `_pp_line` "
				f"where `_pp_line`.package_id = `tabPackage Review Decision`.package_code "
				f"and ifnull(`_pp_line`.is_active, 1) = 1 "
				f"and ifnull(`_pp_line`.department, '') IN ({dept_inlist}))"
			)
			return f"({entity_clause}) AND ({dept_clause})"

	return entity_clause


def package_review_decision_has_permission(doc, ptype="read", user=None, **kwargs):
	"""Deny read when review decision is outside entity/department scope."""
	if not doc or getattr(doc, "doctype", None) != "Package Review Decision":
		return True
	user = user or frappe.session.user
	if ptype != "read":
		return True
	try:
		assert_may_read_package_review_decision(doc, user=user)
	except frappe.PermissionError:
		return False
	return True
