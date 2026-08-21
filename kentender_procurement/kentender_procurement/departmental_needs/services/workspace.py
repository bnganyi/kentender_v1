from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, formatdate

from kentender_core.services.authorization_diagnostics import authorize_support_record_view
from kentender_core.services.authorization_policy import ResourceContext, evaluate_capability, resolve_effective_access
from kentender_core.services.financial_context import enabled_fiscal_years
from kentender_procurement.departmental_needs.constants import (
	CAP_CREATE,
	CAP_EDIT_OWN,
	CAP_OVERSIGHT_READ,
	CAP_READ_ACCEPTED_FOR_PLANNING,
	CAP_REVIEW,
	CAP_VIEW_DEPARTMENT,
	CAP_VIEW_OWN,
	STATE_ACCEPTED,
	STATE_RETURNED,
	STATE_SUBMITTED,
	STATE_WITHDRAWN,
	USAGE_FULL,
)
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.permissions import actor, can_view, resource
from kentender_procurement.departmental_needs.services.usage import planning_usage


READ_CAPABILITIES = {CAP_CREATE, CAP_VIEW_OWN, CAP_VIEW_DEPARTMENT, CAP_REVIEW, CAP_READ_ACCEPTED_FOR_PLANNING, CAP_OVERSIGHT_READ}


def _contexts(principal: str) -> list[dict[str, str]]:
	contexts: dict[tuple[str, str], dict[str, str]] = {}
	for assignment in resolve_effective_access(principal):
		if not READ_CAPABILITIES.intersection(assignment.get("capabilities") or []):
			continue
		pe, assigned_ou = cstr(assignment.get("procuring_entity_id")), cstr(assignment.get("organisation_unit_id"))
		if not pe:
			continue
		units = [assigned_ou] if assigned_ou else frappe.get_all("Organisation Unit", filters={"procuring_entity": pe, "status": "Active"}, pluck="name")
		for ou in units:
			contexts[(pe, ou)] = {
				"procuring_entity": pe,
				"procuring_entity_label": cstr(frappe.db.get_value("Procuring Entity", pe, "legal_name") or pe),
				"organisation_unit": ou,
				"organisation_unit_label": cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou),
			}
	return sorted(contexts.values(), key=lambda row: (row["procuring_entity_label"], row["organisation_unit_label"]))


def _selected_context(principal: str, pe: str, ou: str) -> tuple[dict[str, str] | None, list[dict[str, str]]]:
	contexts = _contexts(principal)
	if not contexts:
		return None, contexts
	if pe or ou:
		selected = next((row for row in contexts if row["procuring_entity"] == pe and row["organisation_unit"] == ou), None)
		if not selected:
			fail("NDS_CONTEXT_OUTSIDE_ASSIGNMENT", "The selected Departmental Needs context is outside your active assignment.")
		return selected, contexts
	if len(contexts) > 1:
		return None, contexts
	return contexts[0], contexts


def _indicative_requirement(need: str) -> str:
	rows = frappe.get_all("Departmental Need Item", filters={"departmental_need": need}, fields=["indicative_quantity", "unit_code", "other_unit"], order_by="line_number asc")
	if len(rows) == 1:
		quantity = flt(rows[0].indicative_quantity)
		value = int(quantity) if quantity.is_integer() else quantity
		unit_label = rows[0].other_unit if rows[0].unit_code == "Other" else rows[0].unit_code
		return f"{value} {unit_label}"
	return f"{len(rows)} need lines"


def _open_review_task(need: str) -> dict[str, str] | None:
	row = frappe.db.get_value(
		"Workflow Task", {"subject_type": "Departmental Need", "subject_id": need, "task_type": "departmental_needs.department_review", "state": "Open"},
		["name", "concurrency_token"], order_by="created_at desc", as_dict=True,
	)
	return {"name": row.name, "concurrency_token": row.concurrency_token} if row else None


def _actions(doc, principal: str, profile: str) -> list[dict[str, str]]:
	ctx = resource(doc)
	if doc.status == STATE_SUBMITTED and evaluate_capability(principal, CAP_REVIEW, ctx).allowed:
		task = _open_review_task(doc.name)
		return [{"code": "review", "label": "Review", "task": (task or {}).get("name", ""), "task_token": (task or {}).get("concurrency_token", "")}]
	if doc.submitted_by == principal and doc.status in {"Draft", STATE_RETURNED} and evaluate_capability(principal, CAP_EDIT_OWN, ctx).allowed:
		# "edit" first: the workspace row button always wires to actions[0]
		# (see departmental_needs_page.js's rowAction()) — a Draft/Returned
		# need is by definition incomplete, so its own owner opening it from
		# the workspace should land straight in the editable form, not a
		# read-only preview requiring a second "Edit" click to get anywhere.
		return [{"code": "edit", "label": "Edit"}, {"code": "view", "label": "View"}]
	return [{"code": "view", "label": "View"}] if profile != "none" else []


def get_workspace(*, procuring_entity: str = "", organisation_unit: str = "", financial_year: str = "", user: str | None = None) -> dict[str, Any]:
	principal = actor(user)
	selected, contexts = _selected_context(principal, cstr(procuring_entity), cstr(organisation_unit))
	if not selected:
		return {
			"ok": False,
			"outcome": "NO_ACTIVE_OPERATIONAL_ASSIGNMENT" if not contexts else "CONTEXT_SELECTION_REQUIRED",
			"contexts": contexts,
			"financial_years": [row for row in enabled_fiscal_years() if not row.get("is_future") and not row.get("is_past")],
			"needs": [], "work_requiring_action": [], "summary": {}, "actions": [],
		}
	fy = cstr(financial_year).strip()
	filters = {"procuring_entity": selected["procuring_entity"], "organisation_unit": selected["organisation_unit"]}
	if fy:
		filters["target_financial_year"] = fy
	rows = frappe.get_all("Departmental Need", filters=filters,
		fields=["name", "need_reference", "title", "procuring_entity", "organisation_unit", "target_financial_year", "submitted_by", "required_by_date", "status", "concurrency_token"],
		order_by="required_by_date asc, need_reference asc")
	needs = []
	for row in rows:
		doc = frappe._dict(row)
		allowed, profile = can_view(doc, principal)
		if not allowed:
			continue
		usage = planning_usage(doc.name)
		needs.append({
			"name": doc.name, "reference": doc.need_reference, "title": doc.title,
			"submitted_by": frappe.db.get_value("User", doc.submitted_by, "full_name") or doc.submitted_by,
			"required_by": str(doc.required_by_date or ""),
			"required_by_label": formatdate(doc.required_by_date, "d MMMM yyyy") if doc.required_by_date else "",
			"status": doc.status, "planning_usage": usage,
			"indicative_requirement": _indicative_requirement(doc.name),
			"actions": _actions(doc, principal, profile),
		})
	work = [row for row in needs if row["status"] == STATE_SUBMITTED and any(a["code"] == "review" for a in row["actions"])]
	visible = [row for row in needs if row["status"] != STATE_WITHDRAWN]
	can_create = evaluate_capability(principal, CAP_CREATE, ResourceContext("Departmental Need", "new", selected["procuring_entity"], fy, selected["organisation_unit"])).allowed
	fy_options = [row for row in enabled_fiscal_years() if not row.get("is_future") and not row.get("is_past")]
	return {
		"ok": True, "outcome": "READY", "contexts": contexts, "financial_years": fy_options,
		"context": {**selected, "financial_year": fy},
		"summary": {
			"total_needs": len(visible),
			"awaiting_departmental_review": sum(row["status"] == STATE_SUBMITTED for row in visible),
			"accepted_for_planning": sum(row["status"] == STATE_ACCEPTED for row in visible),
			"included_in_approved_plan": sum(row["planning_usage"] == USAGE_FULL for row in visible),
		},
		"work_requiring_action": work, "needs": visible,
		"actions": [{"code": "create", "label": "Create need"}] if can_create else [],
		"route": "/desk/departmental-needs",
	}


def get_need(*, need: str, user: str | None = None) -> dict[str, Any]:
	principal = actor(user)
	if not frappe.db.exists("Departmental Need", need):
		fail("NDS_NOT_FOUND", "Departmental Need not found.")
	doc = frappe.get_doc("Departmental Need", need)
	allowed, profile = can_view(doc, principal)
	if not allowed:
		fail("NDS_NOT_FOUND", "Departmental Need not found.")
	latest_return = None
	if doc.status == "Returned":
		row = frappe.db.get_value(
			"Departmental Need Review", {"departmental_need": doc.name, "action": "Return for correction"},
			["reason", "actor", "occurred_at"], order_by="occurred_at desc", as_dict=True,
		)
		if row:
			latest_return = {
				"reason": row.reason, "actor": row.actor,
				"actor_label": frappe.db.get_value("User", row.actor, "full_name") or row.actor,
				"occurred_at": str(row.occurred_at), "occurred_label": formatdate(row.occurred_at, "d MMMM y") + " at " + frappe.utils.format_time(row.occurred_at, "HH:mm"),
			}
	return {
		"ok": True, "need": doc.as_dict(no_nulls=True),
		"items": frappe.get_all("Departmental Need Item", filters={"departmental_need": doc.name}, fields=["name", "item_reference", "line_number", "description", "indicative_quantity", "unit_code", "other_unit"], order_by="line_number asc"),
		"attachments": frappe.get_all(
			"Departmental Need Attachment", filters={"departmental_need": doc.name, "is_active": 1},
			fields=["name", "attachment_reference", "original_filename", "file_size", "mime_type", "scan_status"],
			order_by="uploaded_at asc",
		),
		"latest_return": latest_return,
		"submitted_by_label": frappe.db.get_value("User", doc.submitted_by, "full_name") or doc.submitted_by,
		"submitted_label": (formatdate(doc.submitted_at, "d MMMM y") + " at " + frappe.utils.format_time(doc.submitted_at, "HH:mm")) if doc.submitted_at else frappe._("Not yet submitted"),
		"planning_usage": planning_usage(doc.name), "actions": _actions(doc, principal, profile), "access_profile": profile,
	}


def get_support_need(*, need: str, purpose: str, user: str | None = None) -> dict[str, Any]:
	principal = actor(user)
	if not frappe.db.exists("Departmental Need", need):
		fail("NDS_NOT_FOUND", "Departmental Need not found.")
	doc = frappe.get_doc("Departmental Need", need)
	authorize_support_record_view(user=principal, resource=resource(doc), purpose=purpose)
	return {
		"ok": True, "access_label": "Support read-only",
		"need_reference": doc.need_reference, "title": doc.title, "status": doc.status,
		"procuring_entity": doc.procuring_entity, "organisation_unit": doc.organisation_unit,
		"target_financial_year": doc.target_financial_year, "planning_usage": planning_usage(doc.name),
		"actions": [],
	}
