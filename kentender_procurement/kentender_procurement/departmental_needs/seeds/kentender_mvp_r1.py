"""Exact NDS-UI-01 seed plus governed authorization assignments."""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.utils import add_days, now_datetime
from frappe.utils.password import update_password

from kentender_procurement.departmental_needs.constants import (
	CAP_ALLOCATE, CAP_CREATE, CAP_EDIT_OWN, CAP_OVERSIGHT_READ, CAP_PLANNING_READ,
	CAP_REVIEW, CAP_SUBMIT_OWN, CAP_VIEW_DEPARTMENT, CAP_VIEW_OWN,
	STATE_ACCEPTED, STATE_RETURNED, STATE_SUBMITTED, TASK_DEPARTMENT_REVIEW, TASK_WITHDRAWAL_REVIEW,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"
FY = "2027/28"
NS = "KENTENDER_MVP_1_R1_NDS"
REQUESTER = "grace.wanjiku@moh.example.test"
REVIEWER = "peter.kimani@moh.example.test"
PLANNER = "mercy.kilonzo@moh.example.test"
BUDGET_VIEWER = "moh.budget.officer@moh.example.test"


def _ensure_role(name: str) -> None:
	if not frappe.db.exists("Role", name):
		frappe.get_doc({"doctype": "Role", "role_name": name, "desk_access": 1}).insert(ignore_permissions=True)


def _user(email: str, full_name: str, roles: tuple[str, ...]) -> str:
	for role in roles:
		_ensure_role(role)
	if not frappe.db.exists("User", email):
		parts = full_name.split()
		frappe.get_doc({"doctype": "User", "email": email, "first_name": parts[0], "last_name": " ".join(parts[1:]), "full_name": full_name,
			"enabled": 1, "user_type": "System User", "send_welcome_email": 0}).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("User", email, {"enabled": 1, "full_name": full_name}, update_modified=False)
	doc = frappe.get_doc("User", email)
	doc.add_roles("Desk User", *roles)
	update_password(email, "admin")
	return email


def _profile(profile_id: str, name: str, capabilities: list[str], *, entity_wide: bool = False):
	values = {"profile_name": name, "capabilities": json.dumps(capabilities), "allows_entity_wide": int(entity_wide), "status": "Active",
		"effective_from": add_days(now_datetime(), -1), "concurrency_token": uuid4().hex}
	if frappe.db.exists("Capability Profile", profile_id):
		frappe.db.set_value("Capability Profile", profile_id, values, update_modified=False)
		return frappe.get_doc("Capability Profile", profile_id)
	return frappe.get_doc({"doctype": "Capability Profile", "profile_id": profile_id, **values}).insert(ignore_permissions=True)


def _assignment(assignment_id: str, user: str, profile: str, *, ou: str | None = OU):
	values = {"user_id": user, "capability_profile_id": profile, "procuring_entity_id": PE, "organisation_unit_id": ou,
		"effective_from": add_days(now_datetime(), -1), "status": "Active", "assigned_by": "Administrator", "assigned_at": now_datetime(), "concurrency_token": uuid4().hex}
	if frappe.db.exists("Operational Scope Assignment", assignment_id):
		frappe.db.set_value("Operational Scope Assignment", assignment_id, values, update_modified=False)
	else:
		frappe.get_doc({"doctype": "Operational Scope Assignment", "assignment_id": assignment_id, **values}).insert(ignore_permissions=True)


def _route(task_type: str):
	key = task_type.rsplit(".", 1)[-1].replace("_", "-").upper()
	name = f"RTV-NDS-{key}-MOH-DHP-V1"
	values = {"routing_rule_id": f"RTR-NDS-{key}-MOH-DHP", "version": 1, "module_name": "Departmental Needs", "task_type": task_type,
		"procuring_entity_id": PE, "organisation_unit_id": OU, "required_capability": CAP_REVIEW, "assignee_strategy": "Named user",
		"assignee_user_id": REVIEWER, "priority": 100, "effective_from": add_days(now_datetime(), -1), "status": "Active", "approved_by": "Administrator", "approved_at": now_datetime()}
	if frappe.db.exists("Workflow Routing Rule", name):
		frappe.db.set_value("Workflow Routing Rule", name, values, update_modified=False)
	else:
		frappe.get_doc({"doctype": "Workflow Routing Rule", "routing_version_id": name, **values}).insert(ignore_permissions=True)


def _uom(name: str) -> None:
	if not frappe.db.exists("UOM", name):
		frappe.get_doc({"doctype": "UOM", "uom_name": name, "enabled": 1}).insert(ignore_permissions=True)


NEEDS = (
	("NDS-MOH-2027-001", "National digital health infrastructure upgrade", "2027-08-31", STATE_ACCEPTED, 1, "programme"),
	("NDS-MOH-2027-002", "Digital health technical staff certification programme", "2027-10-31", STATE_SUBMITTED, 120, "staff"),
	("NDS-MOH-2027-003", "Regional health-facility connectivity equipment", "2028-01-15", STATE_RETURNED, 120, "sets"),
)


def _need(reference: str, title: str, required_by: str, status: str, quantity: float, unit: str):
	values = {"title": title, "procuring_entity": PE, "organisation_unit": OU, "target_financial_year": FY, "submitted_by": REQUESTER,
		"business_justification": f"Departmental requirement for {title.lower()}.", "required_by_date": required_by,
		"delivery_or_use_location": "Directorate of Digital Health and Policy", "status": status, "concurrency_token": uuid4().hex, "fixture_namespace": NS}
	is_new = not frappe.db.exists("Departmental Need", reference)
	if not is_new:
		frappe.db.set_value("Departmental Need", reference, values, update_modified=False)
	else:
		frappe.get_doc({"doctype": "Departmental Need", "need_reference": reference, **{**values, "status": "Draft"}}).insert(ignore_permissions=True)
	item_ref = f"{reference}-001"
	item_values = {"departmental_need": reference, "line_number": 1, "description": title, "indicative_quantity": quantity, "unit": unit, "fixture_namespace": NS}
	if frappe.db.exists("Departmental Need Item", item_ref):
		frappe.db.set_value("Departmental Need Item", item_ref, item_values, update_modified=False)
	else:
		frappe.get_doc({"doctype": "Departmental Need Item", "item_reference": item_ref, **item_values}).insert(ignore_permissions=True)
	if is_new and status != "Draft":
		frappe.db.set_value("Departmental Need", reference, "status", status, update_modified=False)
	return reference, item_ref


def upsert_departmental_needs(*, commit: bool = True) -> dict:
	for name in ("Departmental Need Requester", "Head of User Department", "Departmental Review Delegate", "Procurement Planner", "Budget Officer", "Accounting Officer"):
		_ensure_role(name)
	_user(REQUESTER, "Grace Wanjiku", ("Departmental Need Requester",))
	_user(REVIEWER, "Dr Peter Kimani", ("Head of User Department",))
	_user(PLANNER, "Mercy Kilonzo", ("Procurement Planner",))
	_user(BUDGET_VIEWER, "MOH Budget Officer", ("Budget Officer",))
	profiles = {
		"CAP-NDS-REQUESTER": _profile("CAP-NDS-REQUESTER", "Departmental Need Requester", [CAP_CREATE, CAP_EDIT_OWN, CAP_SUBMIT_OWN, CAP_VIEW_OWN]),
		"CAP-NDS-REVIEWER": _profile("CAP-NDS-REVIEWER", "Departmental Need Departmental Reviewer", [CAP_VIEW_DEPARTMENT, CAP_REVIEW]),
		"CAP-NDS-PLANNER": _profile("CAP-NDS-PLANNER", "Departmental Need Planning Reader", [CAP_PLANNING_READ, CAP_ALLOCATE], entity_wide=True),
		"CAP-NDS-OVERSIGHT": _profile("CAP-NDS-OVERSIGHT", "Departmental Need Oversight Reader", [CAP_OVERSIGHT_READ], entity_wide=True),
		"CAP-NDS-SUPPORT": _profile("CAP-NDS-SUPPORT", "Departmental Need Support Reader", ["support.record.view"], entity_wide=True),
	}
	_assignment("OSA-NDS-GRACE-MOH-DHP", REQUESTER, profiles["CAP-NDS-REQUESTER"].name)
	_assignment("OSA-NDS-PETER-MOH-DHP", REVIEWER, profiles["CAP-NDS-REVIEWER"].name)
	_assignment("OSA-NDS-MERCY-MOH", PLANNER, profiles["CAP-NDS-PLANNER"].name, ou=None)
	_assignment("OSA-NDS-BUDGET-MOH", BUDGET_VIEWER, profiles["CAP-NDS-OVERSIGHT"].name, ou=None)
	_assignment("OSA-NDS-ADMIN-SUPPORT-MOH", "Administrator", profiles["CAP-NDS-SUPPORT"].name, ou=None)
	_route(TASK_DEPARTMENT_REVIEW)
	_route(TASK_WITHDRAWAL_REVIEW)
	for uom in ("programme", "staff", "sets"):
		_uom(uom)
	created = [_need(*row) for row in NEEDS]
	plan = frappe.db.get_value("Procurement Plan", {"plan_code": "PLN-MOH-2027-001"}, "name")
	version = frappe.db.get_value("Procurement Plan Version", {"version_code": "PLN-MOH-2027-001-V1"}, "name")
	item = frappe.db.get_value("Procurement Plan Item", {"plan_item_code": "PPI-MOH-2027-021"}, "name")
	allocation = ""
	if plan and version and item:
		key = "NDS-SEED-ALLOC-001"
		allocation = frappe.db.get_value("Plan Need Allocation", {"idempotency_key": key}, "name") or ""
		if not allocation:
			allocation = frappe.get_doc({"doctype": "Plan Need Allocation", "plan_item": item, "departmental_need": created[0][0], "departmental_need_item": created[0][1],
				"source_organisation_unit": OU, "allocated_quantity": 1, "status": "Effective", "proposed_in_version": version,
				"effective_from_version": version, "effective_at": now_datetime(), "reason": "Exact NDS-UI-01 approved allocation", "idempotency_key": key, "fixture_namespace": NS}).insert(ignore_permissions=True).name
	if commit:
		frappe.db.commit()
	return {"ok": True, "needs": [row[0] for row in created], "allocation": allocation, "allocation_seeded": bool(allocation)}
