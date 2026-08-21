"""Validation and cache invalidation for governed authorization records."""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime


def new_concurrency_token() -> str:
	return uuid4().hex


def _date_order(doc) -> None:
	start = get_datetime(doc.get("effective_from")) if doc.get("effective_from") else None
	end = get_datetime(doc.get("effective_to")) if doc.get("effective_to") else None
	if start and end and end <= start:
		frappe.throw(_("Effective To must be later than Effective From."), frappe.ValidationError)


def _json_list(value, label: str) -> list[str]:
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except (TypeError, ValueError):
			frappe.throw(_("{0} must be a JSON list.").format(label), frappe.ValidationError)
	if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
		frappe.throw(_("{0} must contain qualified capability names.").format(label), frappe.ValidationError)
	return value


def _validate_assignment(doc) -> None:
	profile = frappe.get_cached_doc("Capability Profile", doc.capability_profile_id)
	if doc.organisation_unit_id:
		pe = frappe.db.get_value("Organisation Unit", doc.organisation_unit_id, "procuring_entity")
		if pe != doc.procuring_entity_id:
			frappe.throw(_("Organisation Unit must belong to the selected Procuring Entity."), frappe.ValidationError)
	elif not int(profile.allows_entity_wide or 0):
		frappe.throw(_("This capability profile does not permit entity-wide assignment."), frappe.ValidationError)
	if doc.resource_scope_type and not doc.resource_scope_id:
		frappe.throw(_("Resource Scope ID is required when Resource Scope Type is set."), frappe.ValidationError)
	if doc.resource_scope_id and not frappe.db.exists(doc.resource_scope_type, doc.resource_scope_id):
		frappe.throw(_("The governed resource scope does not exist."), frappe.ValidationError)
	if doc.status == "Active" and (not doc.assigned_by or not doc.assigned_at):
		frappe.throw(_("Active assignments require immutable assignment evidence."), frappe.ValidationError)
	if doc.status == "Ended" and (not doc.ended_by or not doc.ended_at or not doc.end_reason):
		frappe.throw(_("Ended assignments require actor, time and reason."), frappe.ValidationError)
	if doc.status == "Active":
		rows = frappe.get_all(
			"Operational Scope Assignment",
			filters={
				"user_id": doc.user_id,
				"capability_profile_id": doc.capability_profile_id,
				"procuring_entity_id": doc.procuring_entity_id,
				"status": "Active",
			},
			fields=["name", "organisation_unit_id", "resource_scope_type", "resource_scope_id", "effective_from", "effective_to"],
		)
		start = get_datetime(doc.effective_from)
		end = get_datetime(doc.effective_to) if doc.effective_to else None
		for row in rows:
			if row.name == doc.name:
				continue
			if (row.organisation_unit_id or "") != (doc.organisation_unit_id or "") or (row.resource_scope_type or "") != (doc.resource_scope_type or "") or (row.resource_scope_id or "") != (doc.resource_scope_id or ""):
				continue
			row_start = get_datetime(row.effective_from)
			row_end = get_datetime(row.effective_to) if row.effective_to else None
			if (not end or row_start < end) and (not row_end or start < row_end):
				frappe.throw(_("An overlapping active operational assignment already exists."), frappe.ValidationError)


def _validate_routing(doc) -> None:
	named = doc.assignee_strategy == "Named user"
	if named != bool(doc.assignee_user_id) or named == bool(doc.queue_id):
		frappe.throw(_("Routing must identify exactly one named user or named claimable queue."), frappe.ValidationError)
	if doc.status == "Active" and (not doc.approved_by or not doc.approved_at):
		frappe.throw(_("Active routing versions require approval evidence."), frappe.ValidationError)
	previous = doc.get_doc_before_save() if not doc.is_new() else None
	if previous and previous.status == "Active":
		immutable = (
			"routing_rule_id", "version", "module_name", "task_type", "procuring_entity_id",
			"organisation_unit_id", "include_descendants", "resource_scope_type", "resource_scope_id",
			"required_capability", "assignee_strategy", "assignee_user_id", "queue_id", "priority",
			"effective_from", "fallback_rule_id", "approved_by", "approved_at",
		)
		if any(previous.get(field) != doc.get(field) for field in immutable):
			frappe.throw(_("Active routing versions are immutable; create a revised version instead."), frappe.ValidationError)


def _validate_task(doc) -> None:
	user_task = doc.assignee_type == "User"
	if user_task != bool(doc.assigned_user_id) or user_task == bool(doc.queue_id):
		frappe.throw(_("A Workflow Task must identify exactly one assigned user or queue."), frappe.ValidationError)
	if doc.claimed_by and doc.assignee_type != "Queue":
		frappe.throw(_("Only queue tasks may be claimed."), frappe.ValidationError)


def validate_authorization_record(doc, _method=None) -> None:
	_date_order(doc)
	if hasattr(doc, "concurrency_token") and not doc.concurrency_token:
		doc.concurrency_token = new_concurrency_token()
	if doc.doctype == "Capability Profile":
		_json_list(doc.capabilities, "Capabilities")
	elif doc.doctype == "Operational Scope Assignment":
		_validate_assignment(doc)
	elif doc.doctype == "Workflow Routing Rule":
		_validate_routing(doc)
	elif doc.doctype == "Workflow Task":
		_validate_task(doc)
	elif doc.doctype == "Authorization Delegation":
		if doc.delegator_user_id == doc.delegate_user_id:
			frappe.throw(_("Delegator and delegate must be different users."), frappe.ValidationError)
		if doc.status == "Active" and (not doc.approved_by or not doc.approved_at):
			frappe.throw(_("Active delegations require approval evidence."), frappe.ValidationError)
	elif doc.doctype == "Separation of Duties Rule":
		if doc.first_capability == doc.second_capability:
			frappe.throw(_("Separation-of-duties capabilities must be different."), frappe.ValidationError)


def invalidate_authorization_cache(doc, _method=None) -> None:
	"""Invalidate all shared policy projections after governed record changes."""
	frappe.cache.delete_value("kentender:authorization:generation")
	frappe.cache.set_value("kentender:authorization:generation", now_datetime().isoformat())
