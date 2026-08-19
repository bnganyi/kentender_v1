from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_core.services.workflow_routing import RoutingContext
from kentender_core.services.workflow_tasks import TaskSpec, execute_routed_transition, transition_task
from kentender_procurement.departmental_needs.constants import (
	CAP_REVIEW,
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_NOT_TAKEN_FORWARD,
	STATE_RETURNED,
	STATE_SUBMITTED,
	STATE_WITHDRAWN,
	TASK_DEPARTMENT_REVIEW,
	TASK_WITHDRAWAL_REVIEW,
)
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.context import selectable_financial_year
from kentender_procurement.departmental_needs.services.permissions import (
	actor,
	owner_capability,
	require_create,
	require_owner_command,
	resource,
)
from kentender_procurement.departmental_needs.services.usage import draft_allocation_count, effective_allocation_count


def _token() -> str:
	return uuid4().hex


def _items(value: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
	rows = json.loads(value) if isinstance(value, str) else value
	if not isinstance(rows, list) or not rows:
		fail("NDS_ITEMS_REQUIRED", "Add at least one Departmental Need item.")
	clean = []
	for row in rows:
		description = cstr(row.get("description")).strip()
		quantity = flt(row.get("indicative_quantity"))
		unit = cstr(row.get("unit")).strip()
		if not description or quantity <= 0 or not unit:
			fail("NDS_ITEM_INVALID", "Each item requires a description, positive indicative quantity and unit.")
		clean.append({"description": description, "indicative_quantity": quantity, "unit": unit})
	return clean


def _existing(idempotency_key: str) -> dict[str, Any] | None:
	key = cstr(idempotency_key).strip()
	if not key:
		fail("NDS_IDEMPOTENCY_KEY_REQUIRED", "An idempotency key is required.")
	row = frappe.db.get_value(
		"Departmental Need Review", {"idempotency_key": key}, ["departmental_need", "action", "result_state", "workflow_task"], as_dict=True
	)
	if not row:
		return None
	need = frappe.get_doc("Departmental Need", row.departmental_need)
	return _result(need, idempotent=True, action=row.action, task=row.workflow_task)


def _review_reference() -> str:
	return f"NDR-{uuid4().hex.upper()}"


def _record_event(need, *, action: str, prior: str, result: str, principal: str, idempotency_key: str, reason: str = "", task: str = ""):
	return frappe.get_doc({
		"doctype": "Departmental Need Review",
		"review_reference": _review_reference(),
		"departmental_need": need.name,
		"action": action,
		"prior_state": prior,
		"result_state": result,
		"reason": cstr(reason).strip(),
		"actor": principal,
		"workflow_task": task or None,
		"occurred_at": now_datetime(),
		"idempotency_key": cstr(idempotency_key).strip(),
	}).insert(ignore_permissions=True)


def _result(need, *, idempotent: bool = False, action: str = "", task: str = "") -> dict[str, Any]:
	return {
		"ok": True,
		"idempotent": idempotent,
		"action": action,
		"need": need.name,
		"need_reference": need.need_reference,
		"status": need.status,
		"concurrency_token": need.concurrency_token,
		"task": task or "",
	}


def _locked_need(name: str):
	rows = frappe.db.sql("select name from `tabDepartmental Need` where name=%s for update", cstr(name).strip(), as_dict=True)
	if not rows:
		fail("NDS_NOT_FOUND", "Departmental Need not found.")
	return frappe.get_doc("Departmental Need", rows[0].name)


def _check_token(need, expected_token: str) -> None:
	if not expected_token or cstr(need.concurrency_token) != cstr(expected_token):
		fail("NDS_CONCURRENCY_CONFLICT", "This Departmental Need changed after it was opened. Reload and try again.")


def _require_task_subject(task: str, need: str, task_type: str) -> None:
	row = frappe.db.get_value("Workflow Task", cstr(task).strip(), ["subject_type", "subject_id", "task_type", "state"], as_dict=True)
	if not row or row.subject_type != "Departmental Need" or row.subject_id != need or row.task_type != task_type or row.state != "Open":
		fail("NDS_TASK_NOT_CURRENT", "This task does not belong to the current Departmental Need action.")


def _set_state(need, target: str) -> None:
	need.status = target
	need.last_decision_at = now_datetime()
	need.concurrency_token = _token()
	need.save(ignore_permissions=True)


def _next_reference(pe: str, financial_year: str) -> tuple[str, str]:
	entity_code = cstr(frappe.db.get_value("Procuring Entity", pe, "entity_code") or pe).removeprefix("PE-")
	year = cstr(financial_year).split("/", 1)[0]
	prefix = f"NDS-{entity_code}-{year}-"
	lock_name = f"nds:create:{entity_code}:{year}"[:64]
	if not frappe.db.sql("select get_lock(%s, 10)", lock_name)[0][0]:
		fail("NDS_CREATE_BUSY", "Departmental Need creation is busy. Try again.")
	refs = frappe.get_all("Departmental Need", filters={"need_reference": ["like", f"{prefix}%"]}, pluck="need_reference")
	seq = max([int(ref.rsplit("-", 1)[-1]) for ref in refs if ref.rsplit("-", 1)[-1].isdigit()] or [0]) + 1
	return f"{prefix}{seq:03d}", lock_name


def create_need(*, procuring_entity: str, organisation_unit: str, target_financial_year: str, title: str,
	business_justification: str, required_by_date: str, delivery_or_use_location: str, items,
	idempotency_key: str, indicative_cost: float | None = None, currency: str | None = None,
	user: str | None = None) -> dict[str, Any]:
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	fy = selectable_financial_year(target_financial_year)
	pe, ou = cstr(procuring_entity).strip(), cstr(organisation_unit).strip()
	require_create(principal, pe, ou, fy["id"])
	clean_items = _items(items)
	if not cstr(title).strip() or not cstr(business_justification).strip() or not cstr(required_by_date).strip() or not cstr(delivery_or_use_location).strip():
		fail("NDS_REQUIRED_FIELDS_MISSING", "Title, business justification, required-by date and location are required.")
	reference, lock_name = _next_reference(pe, fy["id"])
	try:
		need = frappe.get_doc({
			"doctype": "Departmental Need", "need_reference": reference, "title": cstr(title).strip(),
			"procuring_entity": pe, "organisation_unit": ou, "target_financial_year": fy["id"],
			"submitted_by": principal, "business_justification": cstr(business_justification).strip(),
			"required_by_date": required_by_date, "delivery_or_use_location": cstr(delivery_or_use_location).strip(),
			"indicative_cost": indicative_cost, "currency": currency, "status": STATE_DRAFT,
			"concurrency_token": _token(),
		}).insert(ignore_permissions=True)
		for number, row in enumerate(clean_items, 1):
			frappe.get_doc({"doctype": "Departmental Need Item", "item_reference": f"{reference}-{number:03d}",
				"departmental_need": need.name, "line_number": number, **row}).insert(ignore_permissions=True)
		_record_event(need, action="Create", prior=STATE_DRAFT, result=STATE_DRAFT, principal=principal, idempotency_key=idempotency_key)
		return _result(need, action="Create")
	finally:
		frappe.db.sql("select release_lock(%s)", lock_name)


def update_need(*, need: str, title: str, business_justification: str, required_by_date: str,
	delivery_or_use_location: str, items, expected_token: str, idempotency_key: str,
	indicative_cost: float | None = None, currency: str | None = None, user: str | None = None) -> dict[str, Any]:
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	_check_token(doc, expected_token)
	require_owner_command(doc, principal, owner_capability("edit"))
	if doc.status not in {STATE_DRAFT, STATE_RETURNED}:
		fail("NDS_CONTENT_LOCKED", "Only Draft or Returned Departmental Needs may be edited.")
	clean_items = _items(items)
	for field, value in (("title", title), ("business_justification", business_justification), ("required_by_date", required_by_date), ("delivery_or_use_location", delivery_or_use_location)):
		if not cstr(value).strip():
			fail("NDS_REQUIRED_FIELDS_MISSING", "Title, business justification, required-by date and location are required.")
		doc.set(field, cstr(value).strip())
	doc.indicative_cost, doc.currency, doc.concurrency_token = indicative_cost, currency, _token()
	doc.save(ignore_permissions=True)
	frappe.db.delete("Departmental Need Item", {"departmental_need": doc.name})
	for number, row in enumerate(clean_items, 1):
		frappe.get_doc({"doctype": "Departmental Need Item", "item_reference": f"{doc.need_reference}-{number:03d}", "departmental_need": doc.name, "line_number": number, **row}).insert(ignore_permissions=True)
	_record_event(doc, action="Update", prior=doc.status, result=doc.status, principal=principal, idempotency_key=idempotency_key)
	return _result(doc, action="Update")


def _route(need, task_type: str) -> RoutingContext:
	return RoutingContext("Departmental Needs", task_type, need.procuring_entity, need.target_financial_year, need.organisation_unit)


def submit_need(*, need: str, expected_token: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	_check_token(doc, expected_token)
	require_owner_command(doc, principal, owner_capability("submit"))
	if doc.status not in {STATE_DRAFT, STATE_RETURNED}:
		fail("NDS_TRANSITION_NOT_ALLOWED", "Only Draft or Returned Departmental Needs may be submitted.")
	prior = doc.status
	action = "Submit" if prior == STATE_DRAFT else "Resubmit"
	iteration = frappe.db.count("Departmental Need Review", {"departmental_need": doc.name, "action": ["in", ["Submit", "Resubmit"]]}) + 1
	def transition():
		_set_state(doc, STATE_SUBMITTED)
		return _record_event(doc, action=action, prior=prior, result=STATE_SUBMITTED, principal=principal, idempotency_key=idempotency_key)
	_, task = execute_routed_transition(TaskSpec(
		routing=_route(doc, TASK_DEPARTMENT_REVIEW), subject_type="Departmental Need", subject_id=doc.name,
		idempotency_key=f"nds:{doc.name}:department-review:{iteration}", task_iteration=iteration,
	), transition, actor=principal)
	event = frappe.db.get_value("Departmental Need Review", {"idempotency_key": idempotency_key}, "name")
	if event:
		frappe.db.set_value("Departmental Need Review", event, "workflow_task", task.name, update_modified=False)
	return _result(doc, action=action, task=task.name)


def review_need(*, need: str, decision: str, task: str, expected_token: str, task_token: str,
	idempotency_key: str, reason: str = "", user: str | None = None) -> dict[str, Any]:
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	_check_token(doc, expected_token)
	if doc.status != STATE_SUBMITTED:
		fail("NDS_TRANSITION_NOT_ALLOWED", "Only a Submitted Departmental Need may be reviewed.")
	choices = {
		"return": ("Return for correction", STATE_RETURNED, "Returned"),
		"accept": ("Accept for planning", STATE_ACCEPTED, "Completed"),
		"decline": ("Do not take forward", STATE_NOT_TAKEN_FORWARD, "Completed"),
	}
	if decision not in choices:
		fail("NDS_REVIEW_DECISION_INVALID", "Select return, accept or decline.")
	action, target, task_state = choices[decision]
	if decision in {"return", "decline"} and not cstr(reason).strip():
		fail("NDS_REASON_REQUIRED", "A reason is required for this decision.")
	_require_task_subject(task, doc.name, TASK_DEPARTMENT_REVIEW)
	transition_task(task, actor=principal, capability=CAP_REVIEW, target_state=task_state, expected_token=task_token)
	_set_state(doc, target)
	_record_event(doc, action=action, prior=STATE_SUBMITTED, result=target, principal=principal, reason=reason, task=task, idempotency_key=idempotency_key)
	return _result(doc, action=action, task=task)


def withdraw_need(*, need: str, expected_token: str, idempotency_key: str, reason: str = "", user: str | None = None) -> dict[str, Any]:
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	_check_token(doc, expected_token)
	require_owner_command(doc, principal, owner_capability("submit"))
	if doc.status not in {STATE_DRAFT, STATE_RETURNED}:
		fail("NDS_WITHDRAWAL_REQUEST_REQUIRED", "An accepted Departmental Need requires a governed withdrawal request.")
	prior = doc.status
	_set_state(doc, STATE_WITHDRAWN)
	_record_event(doc, action="Withdraw", prior=prior, result=STATE_WITHDRAWN, principal=principal, reason=reason, idempotency_key=idempotency_key)
	return _result(doc, action="Withdraw")


def request_withdrawal(*, need: str, expected_token: str, idempotency_key: str, reason: str, user: str | None = None) -> dict[str, Any]:
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	_check_token(doc, expected_token)
	require_owner_command(doc, principal, owner_capability("submit"))
	if doc.status != STATE_ACCEPTED:
		fail("NDS_TRANSITION_NOT_ALLOWED", "Only an Accepted for planning Need uses the withdrawal-request process.")
	if not cstr(reason).strip():
		fail("NDS_REASON_REQUIRED", "A withdrawal reason is required.")
	iteration = frappe.db.count("Departmental Need Review", {"departmental_need": doc.name, "action": "Request withdrawal"}) + 1
	def transition():
		doc.concurrency_token = _token()
		doc.save(ignore_permissions=True)
		return _record_event(doc, action="Request withdrawal", prior=STATE_ACCEPTED, result=STATE_ACCEPTED, principal=principal, reason=reason, idempotency_key=idempotency_key)
	_, task = execute_routed_transition(TaskSpec(
		routing=_route(doc, TASK_WITHDRAWAL_REVIEW), subject_type="Departmental Need", subject_id=doc.name,
		idempotency_key=f"nds:{doc.name}:withdrawal-review:{iteration}", task_iteration=iteration,
	), transition, actor=principal)
	event = frappe.db.get_value("Departmental Need Review", {"idempotency_key": idempotency_key}, "name")
	frappe.db.set_value("Departmental Need Review", event, "workflow_task", task.name, update_modified=False)
	return _result(doc, action="Request withdrawal", task=task.name)


def approve_withdrawal(*, need: str, task: str, expected_token: str, task_token: str,
	idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	_check_token(doc, expected_token)
	if doc.status != STATE_ACCEPTED:
		fail("NDS_TRANSITION_NOT_ALLOWED", "Only an Accepted for planning Need may complete governed withdrawal.")
	if draft_allocation_count(doc.name):
		fail("NDS_DRAFT_ALLOCATION_EXISTS", "Planning must remove every Draft Plan allocation before withdrawal can be approved.")
	if effective_allocation_count(doc.name):
		fail("NDS_APPROVED_PLAN_ALLOCATION_EXISTS", "The Approved Plan must be amended before withdrawal can be approved.")
	_require_task_subject(task, doc.name, TASK_WITHDRAWAL_REVIEW)
	transition_task(task, actor=principal, capability=CAP_REVIEW, target_state="Completed", expected_token=task_token)
	_set_state(doc, STATE_WITHDRAWN)
	_record_event(doc, action="Approve withdrawal", prior=STATE_ACCEPTED, result=STATE_WITHDRAWN, principal=principal, task=task, idempotency_key=idempotency_key)
	return _result(doc, action="Approve withdrawal", task=task)
