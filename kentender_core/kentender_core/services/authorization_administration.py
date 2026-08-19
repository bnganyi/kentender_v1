"""Protected AUTH-G04 administration commands and read projections."""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe import _
from frappe.utils import format_datetime, get_datetime, now_datetime

from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.authorization_records import new_concurrency_token
from kentender_core.services.authorization_policy import ResourceContext, evaluate_capability, resolve_effective_access

ADMIN_ROLES = {"System Manager", "System Access Administrator"}


def require_access_administrator(user: str | None = None) -> str:
	actor = user or frappe.session.user
	if actor != "Administrator" and not ADMIN_ROLES.intersection(frappe.get_roles(actor)):
		frappe.throw(_("You are not permitted to manage operational access."), frappe.PermissionError, title="AUTH_ADMIN_PERMISSION_DENIED")
	return actor


def _audit(doc, event_type: str, action: str, actor: str, metadata=None):
	log_audit_event(event_type=event_type, entity=doc.get("procuring_entity_id") or "", document_type=doc.doctype, document_name=doc.name, action=action, performed_by=actor, metadata=metadata or {})


def _lock(doctype: str, name: str, expected_token: str):
	rows = frappe.db.sql(f"select name, concurrency_token from `tab{doctype}` where name=%s for update", name, as_dict=True)
	if not rows:
		frappe.throw(_("The authorization record was not found."), title="AUTH_RECORD_NOT_FOUND")
	if rows[0].concurrency_token != expected_token:
		frappe.throw(_("This authorization record changed after you opened it. Reload and try again."), frappe.ValidationError, title="AUTH_CONCURRENCY_CONFLICT")
	return frappe.get_doc(doctype, name)


def get_user_operational_access(target_user: str, *, user: str | None = None) -> dict:
	require_access_administrator(user)
	account = frappe.db.get_value("User", target_user, ["full_name", "enabled"], as_dict=True)
	if not account:
		frappe.throw(_("User not found."), title="AUTH_USER_NOT_FOUND")
	assignments = []
	for row in frappe.get_all("Operational Scope Assignment", filters={"user_id": target_user}, fields=["name", "assignment_id", "capability_profile_id", "procuring_entity_id", "organisation_unit_id", "include_descendants", "resource_scope_type", "resource_scope_id", "effective_from", "effective_to", "status", "concurrency_token"], order_by="effective_from desc"):
		assignments.append({
			**row,
			"role": frappe.db.get_value("Capability Profile", row.capability_profile_id, "profile_name") or row.capability_profile_id,
			"procuring_entity": frappe.db.get_value("Procuring Entity", row.procuring_entity_id, "entity_name") or row.procuring_entity_id,
			"organisation_scope": ("All assigned units and descendants" if row.organisation_unit_id and row.include_descendants else row.organisation_unit_id or "Entity-wide"),
			"resource_scope": f"{row.resource_scope_type}: {row.resource_scope_id}" if row.resource_scope_type else "All admitted resources",
			"effective_period": f"{format_datetime(row.effective_from, 'dd MMMM yyyy')} — {format_datetime(row.effective_to, 'dd MMMM yyyy') if row.effective_to else 'No end date'}",
		})
	return {
		"user": target_user, "full_name": account.full_name or target_user, "account_status": "Active" if account.enabled else "Disabled",
		"as_at": format_datetime(now_datetime(), "dd MMMM yyyy"), "assignments": assignments,
		"active_assignments": sum(row["status"] == "Active" for row in assignments),
		"open_tasks": frappe.db.count("Workflow Task", {"assigned_user_id": target_user, "state": "Open"}),
		"sod_issues": 0,
	}


def create_draft_assignment(values: dict, *, user: str | None = None):
	actor = require_access_administrator(user)
	proposed = set(json.loads(frappe.db.get_value("Capability Profile", values["capability_profile_id"], "capabilities") or "[]"))
	existing = {capability for row in resolve_effective_access(values["user_id"]) for capability in row["capabilities"]}
	for rule in frappe.get_all("Separation of Duties Rule", filters={"status": "Active"}, fields=["first_capability", "second_capability", "enforcement_level"]):
		if rule.enforcement_level == "Assignment" and ((rule.first_capability in proposed and rule.second_capability in existing) or (rule.second_capability in proposed and rule.first_capability in existing)):
			frappe.throw(_("This assignment would create a prohibited separation-of-duties combination."), frappe.PermissionError, title="SEPARATION_OF_DUTIES_BLOCKED")
	doc = frappe.get_doc({"doctype": "Operational Scope Assignment", "assignment_id": values.get("assignment_id") or f"OSA-{uuid4().hex.upper()}", "user_id": values["user_id"], "capability_profile_id": values["capability_profile_id"], "procuring_entity_id": values["procuring_entity_id"], "organisation_unit_id": values.get("organisation_unit_id"), "include_descendants": int(values.get("include_descendants") or 0), "resource_scope_type": values.get("resource_scope_type"), "resource_scope_id": values.get("resource_scope_id"), "effective_from": values["effective_from"], "effective_to": values.get("effective_to"), "status": "Draft", "concurrency_token": new_concurrency_token()}).insert(ignore_permissions=True)
	_audit(doc, "authorization.assignment.created", "create_draft", actor)
	return doc.as_dict()


def change_assignment_state(name: str, expected_token: str, target_state: str, *, reason: str = "", user: str | None = None):
	actor = require_access_administrator(user)
	if target_state not in {"Active", "Suspended", "Ended"}:
		frappe.throw(_("Unsupported assignment state."), frappe.ValidationError)
	doc = _lock("Operational Scope Assignment", name, expected_token)
	if doc.status == "Ended" or (target_state == "Active" and doc.status not in {"Draft", "Suspended"}):
		frappe.throw(_("This assignment cannot make the requested transition."), frappe.ValidationError, title="AUTH_ASSIGNMENT_TRANSITION_INVALID")
	if target_state == "Active" and not doc.assigned_at:
		doc.assigned_by, doc.assigned_at = actor, now_datetime()
	if target_state == "Ended":
		if not reason:
			frappe.throw(_("A reason is required to end an assignment."), frappe.ValidationError)
		doc.ended_by, doc.ended_at, doc.end_reason = actor, now_datetime(), reason
	doc.status = target_state
	doc.concurrency_token = new_concurrency_token()
	doc.save(ignore_permissions=True)
	_audit(doc, f"authorization.assignment.{target_state.lower()}", target_state.lower(), actor, {"reason": reason})
	return doc.as_dict()


def get_routing_rule_detail(name: str, *, user: str | None = None) -> dict:
	require_access_administrator(user)
	if not frappe.db.exists("Workflow Routing Rule", name):
		name = frappe.db.get_value("Workflow Routing Rule", {"routing_rule_id": name, "status": "Active"}, "name") or name
	doc = frappe.get_doc("Workflow Routing Rule", name)
	assignee = doc.assignee_user_id or doc.queue_id
	return {**doc.as_dict(), "assignee": assignee, "procuring_entity": frappe.db.get_value("Procuring Entity", doc.procuring_entity_id, "entity_name") or doc.procuring_entity_id, "eligible": bool(assignee), "eligibility_copy": f"{assignee} has an active assignment covering the required capability and governed scope." if assignee else "No eligible assignee is configured."}


def create_revised_routing_rule(name: str, *, user: str | None = None):
	actor = require_access_administrator(user)
	current = frappe.get_doc("Workflow Routing Rule", name)
	fields = ("routing_rule_id", "module_name", "task_type", "procuring_entity_id", "organisation_unit_id", "include_descendants", "resource_scope_type", "resource_scope_id", "required_capability", "assignee_strategy", "assignee_user_id", "queue_id", "priority", "fallback_rule_id")
	doc = frappe.get_doc({"doctype": "Workflow Routing Rule", "routing_version_id": f"{current.routing_rule_id}-V{int(current.version) + 1}", "version": int(current.version) + 1, **{field: current.get(field) for field in fields}, "effective_from": now_datetime(), "status": "Draft"}).insert(ignore_permissions=True)
	_audit(doc, "authorization.routing.revised", "create_revision", actor, {"predecessor": current.name})
	return doc.as_dict()


def activate_revised_routing_rule(name: str, expected_token: str = "", *, user: str | None = None):
	actor = require_access_administrator(user)
	doc = frappe.get_doc("Workflow Routing Rule", name)
	if doc.status != "Draft":
		frappe.throw(_("Only a Draft routing version can be activated."), frappe.ValidationError)
	active = frappe.get_all("Workflow Routing Rule", filters={"routing_rule_id": doc.routing_rule_id, "status": "Active"}, pluck="name")
	for prior_name in active:
		prior = frappe.get_doc("Workflow Routing Rule", prior_name)
		prior.status, prior.effective_to = "Superseded", now_datetime()
		prior.save(ignore_permissions=True)
	doc.status, doc.approved_by, doc.approved_at = "Active", actor, now_datetime()
	doc.save(ignore_permissions=True)
	_audit(doc, "authorization.routing.activated", "activate", actor, {"superseded": active})
	return doc.as_dict()


def create_queue_membership(values: dict, *, user: str | None = None):
	actor = require_access_administrator(user)
	queue = frappe.get_doc("Workflow Queue", values["queue_id"])
	resource = ResourceContext("Workflow Queue", queue.name, queue.procuring_entity_id)
	if not evaluate_capability(values["user_id"], queue.required_capability, resource).allowed:
		frappe.throw(_("The selected user is not eligible for this queue."), frappe.PermissionError, title="QUEUE_MEMBER_NOT_ELIGIBLE")
	doc = frappe.get_doc({"doctype": "Workflow Queue Membership", "membership_id": values.get("membership_id") or f"QMB-{uuid4().hex.upper()}", "queue_id": values["queue_id"], "user_id": values["user_id"], "effective_from": values["effective_from"], "effective_to": values.get("effective_to"), "status": values.get("status") or "Draft", "concurrency_token": new_concurrency_token()}).insert(ignore_permissions=True)
	_audit(doc, "authorization.queue_membership.created", "create", actor)
	return doc.as_dict()


def create_delegation(values: dict, *, user: str | None = None):
	actor = require_access_administrator(user)
	doc = frappe.get_doc({"doctype": "Authorization Delegation", "delegation_id": values.get("delegation_id") or f"DEL-{uuid4().hex.upper()}", "delegator_user_id": values["delegator_user_id"], "delegate_user_id": values["delegate_user_id"], "capability_profile_id": values["capability_profile_id"], "procuring_entity_id": values["procuring_entity_id"], "organisation_unit_id": values.get("organisation_unit_id"), "effective_from": values["effective_from"], "effective_to": values["effective_to"], "reason": values["reason"], "status": "Scheduled", "concurrency_token": new_concurrency_token()}).insert(ignore_permissions=True)
	_audit(doc, "authorization.delegation.created", "create", actor)
	return doc.as_dict()


def change_delegation_state(name: str, expected_token: str, target_state: str, *, user: str | None = None):
	actor = require_access_administrator(user)
	if target_state not in {"Active", "Revoked"}:
		frappe.throw(_("Unsupported delegation state."), frappe.ValidationError)
	doc = _lock("Authorization Delegation", name, expected_token)
	if target_state == "Active":
		doc.approved_by, doc.approved_at = actor, now_datetime()
	doc.status, doc.concurrency_token = target_state, new_concurrency_token()
	doc.save(ignore_permissions=True)
	_audit(doc, f"authorization.delegation.{target_state.lower()}", target_state.lower(), actor)
	return doc.as_dict()
