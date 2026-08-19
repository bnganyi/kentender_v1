"""Deterministic Gate 05 Budget capability assignments and workflow routing."""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.utils import add_days, now_datetime

from kentender_budget.seeds.budget_role_users import BUDGET_ROLE_USERS, _ensure_pe, _upsert_user


PROFILE_CAPABILITIES = {
	"viewer": ["budget.list", "budget.view"],
	"officer": ["budget.list", "budget.view", "budget.create", "budget.edit", "budget.submit"],
	"reviewer": ["budget.list", "budget.view", "budget.review", "budget.return"],
	"authority": ["budget.list", "budget.view", "budget.approve", "budget.return", "budget.export"],
	"officer_authority": ["budget.list", "budget.view", "budget.create", "budget.edit", "budget.submit", "budget.approve", "budget.return", "budget.export"],
	"test_admin": ["budget.list", "budget.view", "budget.create", "budget.edit", "budget.submit", "budget.review", "budget.return", "budget.approve", "budget.export"],
}

USER_PROFILE = {
	"moh.viewer@example.test": "viewer",
	"moh.medicalservices.officer@example.test": "officer",
	"moh.budget.reviewer@example.test": "reviewer",
	"moh.budget.authority@example.test": "authority",
	"moh.budget.officer.authority@example.test": "officer_authority",
	"other.entity.officer@example.test": "officer",
}


def _profile(key: str):
	name = f"CAP-BUD-{key.upper()}"
	values = {
		"profile_name": f"Budget {key.replace('_', ' ').title()}",
		"capabilities": json.dumps(PROFILE_CAPABILITIES[key]),
		"allows_entity_wide": 1,
		"status": "Active",
		"effective_from": add_days(now_datetime(), -1),
		"concurrency_token": uuid4().hex,
	}
	if frappe.db.exists("Capability Profile", name):
		frappe.db.set_value("Capability Profile", name, values, update_modified=False)
		return frappe.get_doc("Capability Profile", name)
	return frappe.get_doc({"doctype": "Capability Profile", "profile_id": name, **values}).insert(ignore_permissions=True)


def _assignment(user: str, profile, pe: str):
	name = f"OSA-BUD-{user.split('@')[0].upper()}"
	for superseded in frappe.get_all(
		"Operational Scope Assignment",
		filters=[["name", "like", f"{name}-CAP-BUD-%"], ["status", "=", "Active"]],
		pluck="name",
	):
		frappe.db.set_value(
			"Operational Scope Assignment",
			superseded,
			{"status": "Ended", "ended_by": "Administrator", "ended_at": now_datetime(), "end_reason": "Superseded test fixture identifier"},
			update_modified=False,
		)
	values = {
		"user_id": user,
		"capability_profile_id": profile.name,
		"procuring_entity_id": pe,
		"effective_from": add_days(now_datetime(), -1),
		"status": "Active",
		"assigned_by": "Administrator",
		"assigned_at": now_datetime(),
		"concurrency_token": uuid4().hex,
	}
	if frappe.db.exists("Operational Scope Assignment", name):
		frappe.db.set_value("Operational Scope Assignment", name, values, update_modified=False)
		return
	frappe.get_doc({"doctype": "Operational Scope Assignment", "assignment_id": name, **values}).insert(ignore_permissions=True)


def _route(pe: str, task_type: str, capability: str, user: str):
	name = f"RTV-BUD-{task_type.split('.')[-1].upper()}-{pe}"
	values = {
		"routing_rule_id": f"RTR-BUD-{task_type.split('.')[-1].upper()}-{pe}",
		"version": 1,
		"module_name": "Budget & Funding",
		"task_type": task_type,
		"procuring_entity_id": pe,
		"required_capability": capability,
		"assignee_strategy": "Named user",
		"assignee_user_id": user,
		"priority": 100,
		"effective_from": add_days(now_datetime(), -1),
		"status": "Active",
		"approved_by": "Administrator",
		"approved_at": now_datetime(),
	}
	if frappe.db.exists("Workflow Routing Rule", name):
		frappe.db.set_value("Workflow Routing Rule", name, values, update_modified=False)
		return
	frappe.get_doc({"doctype": "Workflow Routing Rule", "routing_version_id": name, **values}).insert(ignore_permissions=True)


def upsert_budget_authorization():
	profiles = {key: _profile(key) for key in PROFILE_CAPABILITIES}
	entities = {
		"PE-MOH": _ensure_pe("PE-MOH", "Ministry of Health"),
		"PE-MOE": _ensure_pe("PE-MOE", "Ministry of Education"),
	}
	for email, full_name, roles, entity_code in BUDGET_ROLE_USERS:
		user = _upsert_user(email, full_name, roles, entities[entity_code])
		_assignment(user, profiles[USER_PROFILE[email]], entities[entity_code])
	_route(entities["PE-MOH"], "budget.review", "budget.review", "moh.budget.reviewer@example.test")
	_route(entities["PE-MOH"], "budget.approve", "budget.approve", "moh.budget.authority@example.test")
	frappe.db.commit()
	return {"ok": True, "profiles": list(profiles), "assignments": len(USER_PROFILE), "routes": 2}


def upsert_budget_test_authorization():
	"""Give legacy integration tests explicit authority without a production fallback."""
	pe = _ensure_pe("PE-MOH", "Ministry of Health")
	profile = _profile("test_admin")
	_assignment("Administrator", profile, pe)
	for task_type, capability in (("budget.review", "budget.review"), ("budget.approve", "budget.approve")):
		_route(pe, task_type, capability, "Administrator")
	return {"ok": True, "assignment": "OSA-BUD-ADMINISTRATOR"}


def assign_budget_test_user(user: str, profile_key: str = "officer"):
	"""Explicit test fixture helper; never called by production hooks."""
	pe = _ensure_pe("PE-MOH", "Ministry of Health")
	_assignment(user, _profile(profile_key), pe)
	return user


def configure_budget_test_workflow(*, reviewer: str, authority: str):
	"""Route test-created Budget work to explicitly assigned test actors."""
	pe = _ensure_pe("PE-MOH", "Ministry of Health")
	if reviewer == authority:
		_assignment(reviewer, _profile("test_admin"), pe)
	else:
		_assignment(reviewer, _profile("reviewer"), pe)
		_assignment(authority, _profile("authority"), pe)
	_route(pe, "budget.review", "budget.review", reviewer)
	_route(pe, "budget.approve", "budget.approve", authority)
	return {"reviewer": reviewer, "authority": authority}
