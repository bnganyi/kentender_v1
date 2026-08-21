from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, flt, getdate, now_datetime

from kentender_core.services.authorization_policy import evaluate_capability
from kentender_core.services.workflow_routing import RoutingContext
from kentender_core.services.workflow_tasks import TaskSpec, execute_routed_transition, transition_task
from kentender_procurement.departmental_needs.constants import (
	CAP_CREATE,
	CAP_REVIEW,
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_NOT_TAKEN_FORWARD,
	STATE_RETURNED,
	STATE_SUBMITTED,
	STATE_WITHDRAWN,
	TASK_DEPARTMENT_REVIEW,
	TASK_WITHDRAWAL_REVIEW,
	UNIT_CODES,
)
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.context import selectable_financial_year
from kentender_procurement.departmental_needs.services.notifications import notify_need_transition
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
	"""Parse and lightly normalize item rows for a Draft save (NDS-FR-023).

	A row may be entirely incomplete — missing description, zero quantity, no
	unit — that is a valid Draft state, not an error. This function only
	rejects structurally malformed input (not a list, or an invalid
	`unit_code` value that isn't even in the closed enum, or a nonsensical
	Other/other_unit combination); it never enforces completeness. Submission
	completeness is enforced separately by `_validate_submission`.
	"""
	rows = json.loads(value) if isinstance(value, str) else value
	if not isinstance(rows, list):
		fail("NDS_ITEMS_INVALID", "Items must be a list of rows.")
	clean = []
	for row in rows:
		description = cstr(row.get("description")).strip()
		quantity = flt(row.get("indicative_quantity"))
		unit_code = cstr(row.get("unit_code")).strip()
		other_unit = cstr(row.get("other_unit")).strip()
		if quantity < 0:
			fail("NDS_ITEM_INVALID", "Indicative quantity cannot be negative.")
		if unit_code and unit_code not in UNIT_CODES:
			fail("NDS_ITEM_INVALID", "Unit must be one of the controlled Departmental Need units.")
		if other_unit and unit_code != "Other":
			fail("NDS_ITEM_OTHER_UNIT_INVALID", "Other Unit may only be set when Unit is Other.")
		clean.append({
			"description": description, "indicative_quantity": quantity, "unit_code": unit_code,
			"other_unit": other_unit if unit_code == "Other" else "",
		})
	return clean


def _item_complete(row) -> bool:
	description = cstr(row.description).strip()
	quantity = flt(row.indicative_quantity)
	unit_code = cstr(row.unit_code).strip()
	if not description or quantity <= 0 or unit_code not in UNIT_CODES:
		return False
	if unit_code == "Other" and not (2 <= len(cstr(row.other_unit).strip()) <= 50):
		return False
	return True


def _validate_submission(doc) -> None:
	"""Full §5 submit/resubmit validation contract. Must run before any state
	change, revision_no increment, work dispatch or notification — a failure
	here is a pure no-op with a stable error code (NDS-FR-026)."""
	justification = cstr(doc.business_justification).strip()
	if not (50 <= len(justification) <= 2000):
		fail("NDS_JUSTIFICATION_INVALID", "Business justification must be 50-2,000 characters.")
	if not doc.required_by_date:
		fail("NDS_REQUIRED_BY_DATE_MISSING", "Required-by date is required.")
	fy_row = selectable_financial_year(doc.target_financial_year)
	required_by = getdate(doc.required_by_date)
	if not (getdate(fy_row["start_date"]) <= required_by <= getdate(fy_row["end_date"])):
		fail("NDS_REQUIRED_BY_DATE_OUT_OF_YEAR", "Required-by date must fall within the target financial year.")
	if not cstr(doc.delivery_or_use_location).strip():
		fail("NDS_LOCATION_MISSING", "Delivery or use location is required.")
	if doc.indicative_cost:
		cost = flt(doc.indicative_cost)
		cents = cost * 100
		if cost <= 0 or abs(cents - round(cents)) > 1e-6:
			fail("NDS_INDICATIVE_COST_INVALID", "Estimated total cost must be positive with at most two decimal places.")
	rows = frappe.get_all(
		"Departmental Need Item", filters={"departmental_need": doc.name},
		fields=["description", "indicative_quantity", "unit_code", "other_unit"], order_by="line_number asc",
	)
	if not rows:
		fail("NDS_ITEMS_REQUIRED", "Add at least one Departmental Need item.")
	if any(not _item_complete(row) for row in rows):
		fail("NDS_ITEM_INCOMPLETE", "Every item line must have a description, a positive quantity and a unit before submission.")
	unclean = frappe.get_all(
		"Departmental Need Attachment",
		filters={"departmental_need": doc.name, "is_active": 1, "scan_status": ["!=", "Clean"]},
		limit=1,
	)
	if unclean:
		fail("NDS_ATTACHMENT_NOT_CLEAN", "All supporting documents must finish malware scanning before submission.")


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


def _state_hash(need) -> str:
	"""§8.4's before/after state hash — a stable digest of the fields that
	actually define the Need's meaningful state, not a full row dump."""
	payload = {
		"status": cstr(need.status), "revision_no": need.revision_no, "title": cstr(need.title),
		"business_justification": cstr(need.business_justification), "required_by_date": cstr(need.required_by_date),
		"delivery_or_use_location": cstr(need.delivery_or_use_location), "indicative_cost": cstr(need.indicative_cost),
		"concurrency_token": cstr(need.concurrency_token),
	}
	return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _request_context() -> dict[str, str]:
	"""§8.4's request identifier / source IP / session — read from the active
	HTTP request when one exists (a real command call); falls back to a
	generated identifier and blank IP/session for console/background/test
	contexts, where there genuinely is no HTTP request to attribute."""
	request_id = ""
	try:
		request_id = cstr(frappe.get_request_header("X-Frappe-Request-Id") or "")
	except Exception:
		request_id = ""
	if not request_id:
		request_id = uuid4().hex
	return {
		"request_id": request_id,
		"source_ip": cstr(getattr(frappe.local, "request_ip", "") or ""),
		"session_id": cstr(getattr(frappe.session, "sid", "") or ""),
	}


def _effective_assignment(principal: str, capability: str, need) -> str:
	"""§8.4's "effective assignment" — the governed assignment(s) that actually
	authorized this command. Command enforcement already ran (require_capability/
	transition_task) before this is called; re-evaluating here is read-only and
	side-effect-free, purely to capture the assignment identifiers for the audit
	record without changing the enforcement call sites' return contracts."""
	decision = evaluate_capability(principal, capability, resource(need))
	return ",".join(decision.assignment_ids)


def _record_event(need, *, action: str, prior: str, result: str, principal: str, idempotency_key: str, reason: str = "", task: str = "",
	before_hash: str = "", effective_assignment: str = ""):
	ctx = _request_context()
	return frappe.get_doc({
		"doctype": "Departmental Need Review",
		"review_reference": _review_reference(),
		"departmental_need": need.name,
		"action": action,
		"prior_state": prior,
		"result_state": result,
		"reason": cstr(reason).strip(),
		"actor": principal,
		"effective_assignment": effective_assignment,
		"scope": f"{need.procuring_entity}/{need.organisation_unit}/{need.target_financial_year}",
		"workflow_task": task or None,
		"occurred_at": now_datetime(),
		"request_id": ctx["request_id"],
		"source_ip": ctx["source_ip"],
		"session_id": ctx["session_id"],
		"before_state_hash": before_hash,
		"after_state_hash": _state_hash(need),
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
		"revision_no": need.revision_no,
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
	return f"{prefix}{seq:04d}", lock_name


def create_need(*, procuring_entity: str, organisation_unit: str, target_financial_year: str, title: str,
	business_justification: str = "", required_by_date: str | None = None, delivery_or_use_location: str = "",
	items=None, idempotency_key: str, indicative_cost: float | None = None,
	user: str | None = None) -> dict[str, Any]:
	"""Save a Draft (NDS-FR-023): only context (PE/OU/target FY) and title need
	be valid. Every submission-only field — justification, required-by date,
	location, items, indicative cost — may be absent or incomplete; the full
	§5 contract is enforced later, once only, at `submit_need`."""
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	fy = selectable_financial_year(target_financial_year)
	pe, ou = cstr(procuring_entity).strip(), cstr(organisation_unit).strip()
	require_create(principal, pe, ou, fy["id"])
	clean_items = _items(items or [])
	if not cstr(title).strip():
		fail("NDS_REQUIRED_FIELDS_MISSING", "Title is required.")
	reference, lock_name = _next_reference(pe, fy["id"])
	try:
		need = frappe.get_doc({
			"doctype": "Departmental Need", "need_reference": reference, "title": cstr(title).strip(),
			"procuring_entity": pe, "organisation_unit": ou, "target_financial_year": fy["id"],
			"submitted_by": principal, "business_justification": cstr(business_justification).strip(),
			"required_by_date": required_by_date or None, "delivery_or_use_location": cstr(delivery_or_use_location).strip(),
			"indicative_cost": indicative_cost, "currency": "KES", "status": STATE_DRAFT,
			"concurrency_token": _token(),
		}).insert(ignore_permissions=True)
		for number, row in enumerate(clean_items, 1):
			frappe.get_doc({"doctype": "Departmental Need Item", "item_reference": f"{reference}-{number:03d}",
				"departmental_need": need.name, "line_number": number, **row}).insert(ignore_permissions=True)
		_record_event(need, action="Create", prior=STATE_DRAFT, result=STATE_DRAFT, principal=principal, idempotency_key=idempotency_key,
			effective_assignment=_effective_assignment(principal, CAP_CREATE, need))
		return _result(need, action="Create")
	finally:
		frappe.db.sql("select release_lock(%s)", lock_name)


def update_need(*, need: str, title: str, business_justification: str = "", required_by_date: str | None = None,
	delivery_or_use_location: str = "", items=None, expected_token: str, idempotency_key: str,
	indicative_cost: float | None = None, user: str | None = None) -> dict[str, Any]:
	"""Save a partial Draft/Returned edit (NDS-FR-023) — only the title is
	required; every submission-only field may be left blank/incomplete here,
	same as `create_need`."""
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_token(doc, expected_token)
	require_owner_command(doc, principal, owner_capability("edit"))
	if doc.status not in {STATE_DRAFT, STATE_RETURNED}:
		fail("NDS_CONTENT_LOCKED", "Only Draft or Returned Departmental Needs may be edited.")
	clean_items = _items(items or [])
	if not cstr(title).strip():
		fail("NDS_REQUIRED_FIELDS_MISSING", "Title is required.")
	doc.title = cstr(title).strip()
	doc.business_justification = cstr(business_justification).strip()
	doc.required_by_date = required_by_date or None
	doc.delivery_or_use_location = cstr(delivery_or_use_location).strip()
	doc.indicative_cost, doc.currency, doc.concurrency_token = indicative_cost, "KES", _token()
	doc.save(ignore_permissions=True)
	frappe.db.delete("Departmental Need Item", {"departmental_need": doc.name})
	for number, row in enumerate(clean_items, 1):
		frappe.get_doc({"doctype": "Departmental Need Item", "item_reference": f"{doc.need_reference}-{number:03d}", "departmental_need": doc.name, "line_number": number, **row}).insert(ignore_permissions=True)
	_record_event(doc, action="Update", prior=doc.status, result=doc.status, principal=principal, idempotency_key=idempotency_key,
		before_hash=before_hash, effective_assignment=_effective_assignment(principal, owner_capability("edit"), doc))
	return _result(doc, action="Update")


def _route(need, task_type: str) -> RoutingContext:
	return RoutingContext("Departmental Needs", task_type, need.procuring_entity, need.target_financial_year, need.organisation_unit)


def submit_need(*, need: str, expected_token: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_token(doc, expected_token)
	require_owner_command(doc, principal, owner_capability("submit"))
	if doc.status not in {STATE_DRAFT, STATE_RETURNED}:
		fail("NDS_TRANSITION_NOT_ALLOWED", "Only Draft or Returned Departmental Needs may be submitted.")
	_validate_submission(doc)
	prior = doc.status
	action = "Submit" if prior == STATE_DRAFT else "Resubmit"
	iteration = frappe.db.count("Departmental Need Review", {"departmental_need": doc.name, "action": ["in", ["Submit", "Resubmit"]]}) + 1
	def transition():
		doc.revision_no = iteration
		doc.submitted_at = now_datetime()
		_set_state(doc, STATE_SUBMITTED)
		return _record_event(doc, action=action, prior=prior, result=STATE_SUBMITTED, principal=principal, idempotency_key=idempotency_key,
			before_hash=before_hash, effective_assignment=_effective_assignment(principal, owner_capability("submit"), doc))
	_, task = execute_routed_transition(TaskSpec(
		routing=_route(doc, TASK_DEPARTMENT_REVIEW), subject_type="Departmental Need", subject_id=doc.name,
		idempotency_key=f"nds:{doc.name}:department-review:{iteration}", task_iteration=iteration,
	), transition, actor=principal)
	event = frappe.db.get_value("Departmental Need Review", {"idempotency_key": idempotency_key}, "name")
	if event:
		frappe.db.set_value("Departmental Need Review", event, "workflow_task", task.name, update_modified=False)
	notify_need_transition(doc, action=action)
	return _result(doc, action=action, task=task.name)


def review_need(*, need: str, decision: str, task: str, expected_token: str, task_token: str,
	idempotency_key: str, reason: str = "", user: str | None = None) -> dict[str, Any]:
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_token(doc, expected_token)
	if doc.status != STATE_SUBMITTED:
		fail("NDS_TRANSITION_NOT_ALLOWED", "Only a Submitted Departmental Need may be reviewed.")
	# NDS-FR-031/AC-028 — maker-checker: the submitter may never decide their own
	# Need. This is an unconditional business rule, not delegated to the generic
	# (admin-configured) Separation of Duties Rule mechanism, which has no rows
	# for departmental_needs.submit/review and so would silently allow this if
	# relied on alone.
	if cstr(doc.submitted_by) == principal:
		fail("NDS_SELF_REVIEW_NOT_ALLOWED", "You cannot make the departmental decision on your own submitted Need.")
	choices = {
		"return": ("Return for correction", STATE_RETURNED, "Returned"),
		"accept": ("Accept for planning", STATE_ACCEPTED, "Completed"),
		"decline": ("Do not take forward", STATE_NOT_TAKEN_FORWARD, "Completed"),
	}
	if decision not in choices:
		fail("NDS_REVIEW_DECISION_INVALID", "Select return, accept or decline.")
	action, target, task_state = choices[decision]
	if decision in {"return", "decline"}:
		# NDS-FR-032/035 — a mandatory 20-1,000 character reason. The reason
		# dialog enforces this client-side (minlength/maxlength), but that is
		# not itself authorization: a direct API call must be rejected the
		# same way, not merely rely on the UI never sending a short one.
		reason_length = len(cstr(reason).strip())
		if not (20 <= reason_length <= 1000):
			fail("NDS_REASON_INVALID", "A reason of 20-1,000 characters is required for this decision.")
	_require_task_subject(task, doc.name, TASK_DEPARTMENT_REVIEW)
	transition_task(task, actor=principal, capability=CAP_REVIEW, target_state=task_state, expected_token=task_token)
	_set_state(doc, target)
	_record_event(doc, action=action, prior=STATE_SUBMITTED, result=target, principal=principal, reason=reason, task=task, idempotency_key=idempotency_key,
		before_hash=before_hash, effective_assignment=_effective_assignment(principal, CAP_REVIEW, doc))
	notify_need_transition(doc, action=action)
	return _result(doc, action=action, task=task)


def withdraw_need(*, need: str, expected_token: str, idempotency_key: str, reason: str = "", user: str | None = None) -> dict[str, Any]:
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_token(doc, expected_token)
	require_owner_command(doc, principal, owner_capability("submit"))
	if doc.status not in {STATE_DRAFT, STATE_RETURNED}:
		fail("NDS_WITHDRAWAL_REQUEST_REQUIRED", "An accepted Departmental Need requires a governed withdrawal request.")
	prior = doc.status
	_set_state(doc, STATE_WITHDRAWN)
	_record_event(doc, action="Withdraw", prior=prior, result=STATE_WITHDRAWN, principal=principal, reason=reason, idempotency_key=idempotency_key,
		before_hash=before_hash, effective_assignment=_effective_assignment(principal, owner_capability("submit"), doc))
	return _result(doc, action="Withdraw")


def request_withdrawal(*, need: str, expected_token: str, idempotency_key: str, reason: str, user: str | None = None) -> dict[str, Any]:
	if replay := _existing(idempotency_key):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
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
		return _record_event(doc, action="Request withdrawal", prior=STATE_ACCEPTED, result=STATE_ACCEPTED, principal=principal, reason=reason, idempotency_key=idempotency_key,
			before_hash=before_hash, effective_assignment=_effective_assignment(principal, owner_capability("submit"), doc))
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
	before_hash = _state_hash(doc)
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
	_record_event(doc, action="Approve withdrawal", prior=STATE_ACCEPTED, result=STATE_WITHDRAWN, principal=principal, task=task, idempotency_key=idempotency_key,
		before_hash=before_hash, effective_assignment=_effective_assignment(principal, CAP_REVIEW, doc))
	return _result(doc, action="Approve withdrawal", task=task)
