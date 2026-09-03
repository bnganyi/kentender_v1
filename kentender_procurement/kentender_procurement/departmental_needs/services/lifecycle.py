"""Departmental Needs command layer (NDS-CHG-001 v1.1 §5, §8.2).

Every mutating command follows one shape: replay the idempotency key, resolve
the actor, lock the root row, check the optimistic record version, authorize
natively (§6), guard the state, validate, mutate, then record one immutable
decision (§4.5). Authorization uses Frappe roles and User Permissions only —
no capability or scope-assignment store (NDS-AC-044).

The §5.1 initial lifecycle, the §5.2 accepted-successor lifecycle and the §5.3
withdrawal decision set are all implemented here on the version model.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, flt, getdate, now_datetime

from kentender_procurement.departmental_needs.constants import (
	ACTION_ACCEPT,
	ACTION_ACCEPT_SUCCESSOR,
	ACTION_APPROVE_WITHDRAWAL,
	ACTION_CANCEL_SUCCESSOR,
	ACTION_CREATE,
	ACTION_CREATE_SUCCESSOR,
	ACTION_DECLINE,
	ACTION_DECLINE_SUCCESSOR,
	ACTION_DECLINE_WITHDRAWAL,
	ACTION_EVALUATE_WITHDRAWAL,
	ACTION_REEVALUATE_WITHDRAWAL,
	ACTION_REQUEST_WITHDRAWAL,
	ACTION_RESUBMIT,
	ACTION_RETURN,
	ACTION_RETURN_SUCCESSOR,
	ACTION_SAVE_DRAFT,
	ACTION_SAVE_SUCCESSOR,
	ACTION_SUBMIT,
	ACTION_SUBMIT_SUCCESSOR,
	ACTION_WITHDRAW,
	DESCRIPTION_MAX,
	DESCRIPTION_MIN,
	OPEN_SUCCESSOR_STATUSES,
	OPEN_WITHDRAWAL_STATUSES,
	REASON_MAX,
	REASON_MIN,
	REASON_REQUIRED_ACTIONS,
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_NOT_TAKEN_FORWARD,
	STATE_RETURNED,
	STATE_SUBMITTED,
	STATE_WITHDRAWN,
	USAGE_FULL,
	TASK_COMPLETED,
	TASK_INITIAL_ACCEPTANCE,
	TASK_OPEN,
	TASK_SUCCESSOR_ACCEPTANCE,
	TASK_WITHDRAWAL,
	VERSION_ACCEPTED,
	VERSION_CONTENT_FIELDS,
	VERSION_DRAFT,
	VERSION_NOT_TAKEN_FORWARD,
	VERSION_RETURNED,
	VERSION_SUBMITTED,
	VERSION_SUPERSEDED,
	VERSION_WITHDRAWN,
	WITHDRAWAL_APPROVED,
	WITHDRAWAL_AWAITING_CLEARANCE,
	WITHDRAWAL_AWAITING_REVIEW,
	WITHDRAWAL_DECLINED,
)
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.context import (
	require_open_intake,
	selectable_financial_year,
)
from kentender_procurement.departmental_needs.services.notifications import notify_need_transition
from kentender_procurement.departmental_needs.services.permissions import (
	actor,
	is_owner,
	require_author_command,
	require_create,
	require_review_command,
)
from kentender_procurement.departmental_needs.services.events import (
	publish_accepted,
	publish_superseded,
	publish_withdrawn,
)
from kentender_procurement.departmental_needs.services.usage import planning_usage_detail


def _token() -> str:
	return uuid4().hex


# --- Audit and idempotency -------------------------------------------------


def _request_context() -> dict[str, str]:
	"""§8.4's request identifier / source IP / session.

	Read from the active HTTP request when one exists; falls back to a generated
	identifier and blank IP/session for console, background and test contexts,
	where there genuinely is no HTTP request to attribute.
	"""
	try:
		request_id = cstr(frappe.get_request_header("X-Frappe-Request-Id") or "")
	except Exception:
		request_id = ""
	return {
		"request_id": request_id or uuid4().hex,
		"source_ip": cstr(getattr(frappe.local, "request_ip", "") or ""),
		"session_id": cstr(getattr(frappe.session, "sid", "") or ""),
	}


def _fingerprint(payload: dict[str, Any]) -> str:
	"""A stable digest of the caller's command payload (§8, §9).

	`user` and the key itself are excluded: the same request replayed by the
	same caller must match, and the key is the lookup, not part of the payload.
	"""
	material = {
		key: cstr(value)
		for key, value in sorted(payload.items())
		if key not in {"user", "idempotency_key"} and value is not None
	}
	return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


def _existing(idempotency_key: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
	"""Replay a completed command, or reject the key if the payload differs.

	§9 distinguishes a genuine retry from key reuse: the same key with a
	different payload is `NDS_IDEMPOTENCY_CONFLICT`, never a silent replay of
	the earlier command's result.
	"""
	key = cstr(idempotency_key).strip()
	if not key:
		fail("NDS_IDEMPOTENCY_CONFLICT", "An idempotency key is required.")
	row = frappe.db.get_value(
		"Departmental Need Decision",
		{"idempotency_key": key},
		["departmental_need", "action", "request_fingerprint"],
		as_dict=True,
	)
	if not row:
		return None
	if payload is not None:
		seen = cstr(row.request_fingerprint)
		if seen and seen != _fingerprint(payload):
			fail(
				"NDS_IDEMPOTENCY_CONFLICT",
				"This idempotency key was already used with a different request.",
			)
	need = frappe.get_doc("Departmental Need", row.departmental_need)
	return _result(need, idempotent=True, action=row.action)


def _state_hash(need, version=None) -> str:
	"""A stable digest of the fields that define the Need's meaningful state."""
	payload = {
		"current_state": cstr(need.current_state),
		"record_version": cstr(need.record_version),
		"current_version": cstr(need.current_version),
		"current_accepted_version": cstr(need.current_accepted_version),
	}
	if version is not None:
		payload["version"] = _content_payload(version)
	return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _content_payload(version) -> dict[str, str]:
	return {field: cstr(version.get(field)) for field in VERSION_CONTENT_FIELDS}


def _content_hash(version) -> str:
	return hashlib.sha256(
		json.dumps(_content_payload(version), sort_keys=True).encode()
	).hexdigest()


def _record_decision(
	need,
	*,
	action: str,
	prior: str,
	result: str,
	principal: str,
	idempotency_key: str,
	version: str = "",
	withdrawal_request: str = "",
	reason: str = "",
	task: str = "",
	before_hash: str = "",
	content_hash: str = "",
	fingerprint: str = "",
):
	ctx = _request_context()
	return frappe.get_doc(
		{
			"doctype": "Departmental Need Decision",
			"decision_id": f"NDD-{uuid4().hex.upper()}",
			"departmental_need": need.name,
			"need_version": version or None,
			"withdrawal_request": withdrawal_request or None,
			"action": action,
			"actor": principal,
			"effective_assignment": _effective_assignment(principal, need),
			"scope": f"{need.procuring_entity}/{need.organisation_unit}/{need.financial_year}",
			"review_task": task or None,
			"occurred_at": now_datetime(),
			"reason": cstr(reason).strip(),
			"prior_state": prior,
			"result_state": result,
			"content_hash": content_hash,
			"correlation_id": ctx["request_id"],
			"request_id": ctx["request_id"],
			"source_ip": ctx["source_ip"],
			"session_id": ctx["session_id"],
			"before_state_hash": before_hash,
			"after_state_hash": _state_hash(need),
			"idempotency_key": cstr(idempotency_key).strip(),
			"request_fingerprint": fingerprint,
		}
	).insert(ignore_permissions=True)


def _effective_assignment(principal: str, need) -> str:
	"""§8.4 — the native User Permission scope that authorized this command."""
	rows = frappe.get_all(
		"User Permission",
		filters={
			"user": principal,
			"allow": ("in", ["Procuring Entity", "Organisation Unit", "Financial Year"]),
		},
		fields=["allow", "for_value"],
		limit_page_length=0,
	)
	relevant = {
		f"{row.allow}:{row.for_value}"
		for row in rows
		if row.for_value
		in {need.procuring_entity, need.organisation_unit, need.financial_year}
	}
	return ",".join(sorted(relevant))


# --- Root and version helpers ---------------------------------------------


def _locked_need(name: str):
	rows = frappe.db.sql(
		"select name from `tabDepartmental Need` where name=%s for update",
		cstr(name).strip(),
		as_dict=True,
	)
	if not rows:
		fail("NDS_SCOPE_DENIED", "Departmental Need not found.")
	return frappe.get_doc("Departmental Need", rows[0].name)


def _check_version(need, expected_version) -> None:
	if cstr(expected_version) == "" or cstr(need.record_version) != cstr(expected_version):
		fail(
			"NDS_STALE_WRITE",
			"This Departmental Need changed after it was opened. Reload and try again.",
		)


def _bump(need, target_state: str | None = None) -> None:
	if target_state:
		need.current_state = target_state
	need.record_version = int(need.record_version or 0) + 1
	need.save(ignore_permissions=True)


def _current_version(need):
	if not need.current_version:
		fail("NDS_STATE_CONFLICT", "This Departmental Need has no current version.")
	return frappe.get_doc("Departmental Need Version", need.current_version)


def _next_version_number(need: str) -> int:
	rows = frappe.get_all(
		"Departmental Need Version",
		filters={"departmental_need": need},
		pluck="version_number",
	)
	return max([int(n or 0) for n in rows] or [0]) + 1


def _create_version(need, *, values: dict[str, Any], based_on: str = "") -> Any:
	number = _next_version_number(need.name)
	return frappe.get_doc(
		{
			"doctype": "Departmental Need Version",
			"need_version_id": f"{need.need_reference}-V{number:03d}",
			"departmental_need": need.name,
			"version_number": number,
			"based_on_version": based_on or None,
			"version_status": VERSION_DRAFT,
			"fixture_namespace": need.fixture_namespace,
			**values,
		}
	).insert(ignore_permissions=True)


def _set_version_status(version, status: str) -> None:
	frappe.db.set_value(
		"Departmental Need Version", version.name, "version_status", status, update_modified=False
	)


def _open_successor(need) -> str:
	"""The Need's open accepted-successor version, or "" when there is none (§5.2).

	A successor exists exactly while the root points at a version other than its
	current accepted one. Accept, decline and cancel all repoint `current_version`
	so the pointer alone answers "is a successor open?"; the status check below is
	a second, independent guard against a stale pointer.
	"""
	if not need.current_accepted_version or not need.current_version:
		return ""
	if cstr(need.current_version) == cstr(need.current_accepted_version):
		return ""
	status = frappe.db.get_value(
		"Departmental Need Version", need.current_version, "version_status"
	)
	return cstr(need.current_version) if status in OPEN_SUCCESSOR_STATUSES else ""


def _require_open_successor(need):
	successor = _open_successor(need)
	if need.current_state != STATE_ACCEPTED or not successor:
		fail("NDS_STATE_CONFLICT", "This Departmental Need has no open update.")
	return frappe.get_doc("Departmental Need Version", successor)


def _next_reference(pe: str, financial_year: str) -> tuple[str, str]:
	entity_code = cstr(
		frappe.db.get_value("Procuring Entity", pe, "entity_code") or pe
	).removeprefix("PE-")
	year = cstr(frappe.db.get_value("Financial Year", financial_year, "start_year") or "")
	prefix = f"NDS-{entity_code}-{year}-"
	lock_name = f"nds:create:{entity_code}:{year}"[:64]
	if not frappe.db.sql("select get_lock(%s, 10)", lock_name)[0][0]:
		fail("NDS_STATE_CONFLICT", "Departmental Need creation is busy. Try again.")
	refs = frappe.get_all(
		"Departmental Need",
		filters={"need_reference": ["like", f"{prefix}%"]},
		pluck="need_reference",
	)
	seq = max(
		[int(ref.rsplit("-", 1)[-1]) for ref in refs if ref.rsplit("-", 1)[-1].isdigit()] or [0]
	) + 1
	return f"{prefix}{seq:04d}", lock_name


def _result(need, *, idempotent: bool = False, action: str = "", task: str = "") -> dict[str, Any]:
	return {
		"ok": True,
		"idempotent": idempotent,
		"action": action,
		"need": need.name,
		"need_reference": need.need_reference,
		"current_state": need.current_state,
		"current_version": need.current_version or "",
		"current_accepted_version": need.current_accepted_version or "",
		"record_version": need.record_version,
		"task": task or "",
	}


# --- Review tasks (§4.4) ---------------------------------------------------


def _open_task(need, *, task_type: str, version: str = "", withdrawal_request: str = ""):
	return frappe.get_doc(
		{
			"doctype": "Departmental Need Review Task",
			"review_task_id": f"NDT-{uuid4().hex.upper()}",
			"departmental_need": need.name,
			"need_version": version or None,
			"withdrawal_request": withdrawal_request or None,
			"task_type": task_type,
			"procuring_entity": need.procuring_entity,
			"organisation_unit": need.organisation_unit,
			"financial_year": need.financial_year,
			"status": TASK_OPEN,
			"decision_token": _token(),
			"opened_at": now_datetime(),
			"fixture_namespace": need.fixture_namespace,
		}
	).insert(ignore_permissions=True)


def _claim_task(task_id: str, need: str, task_type: str, decision_token: str):
	"""Lock one Open task and verify its decision token (NDS-AC-028)."""
	row = frappe.db.sql(
		"select name from `tabDepartmental Need Review Task` where name=%s for update",
		cstr(task_id).strip(),
		as_dict=True,
	)
	if not row:
		fail("NDS_STATE_CONFLICT", "This review task does not exist.")
	task = frappe.get_doc("Departmental Need Review Task", row[0].name)
	if task.departmental_need != need or task.task_type != task_type or task.status != TASK_OPEN:
		fail("NDS_STATE_CONFLICT", "This task does not belong to the current Departmental Need action.")
	if cstr(task.decision_token) != cstr(decision_token):
		fail("NDS_STALE_WRITE", "This task was already decided. Reload and try again.")
	return task


def _consume_task(task_id: str, need: str, task_type: str, decision_token: str):
	"""Close the task: the decision it carried has been taken."""
	task = _claim_task(task_id, need, task_type, decision_token)
	task.status = TASK_COMPLETED
	task.closed_at = now_datetime()
	task.decision_token = _token()
	task.save(ignore_permissions=True)
	return task


def _touch_task(task_id: str, need: str, task_type: str, decision_token: str):
	"""Rotate the token but leave the task Open.

	§5.3's `Evaluate` and `Re-evaluate` record a decision without resolving the
	withdrawal request, so the task must survive; rotating the token still makes
	the acted-on submission unrepeatable.
	"""
	task = _claim_task(task_id, need, task_type, decision_token)
	task.decision_token = _token()
	task.save(ignore_permissions=True)
	return task


# --- Validation (§4.3, §5) -------------------------------------------------


def _require_text(value: str, label: str) -> str:
	text = cstr(value).strip()
	if not (DESCRIPTION_MIN <= len(text) <= DESCRIPTION_MAX):
		fail("NDS_FIELD_REQUIRED", f"{label} must be {DESCRIPTION_MIN}-{DESCRIPTION_MAX} characters.")
	return text


def _validate_submission(need, version) -> None:
	"""§5/NDS-BR-007 — all six values, a governed unit and an in-year date.

	Runs before any state change, task creation or notification, so a failure is
	a pure no-op with a stable §9 code.
	"""
	_require_text(version.description, "Description")
	_require_text(version.expected_operational_result, "Expected operational result")
	if flt(version.indicative_quantity) <= 0:
		fail("NDS_FIELD_REQUIRED", "Indicative quantity must be greater than zero.")
	if not version.unit:
		fail("NDS_FIELD_REQUIRED", "Unit is required.")
	if frappe.db.get_value("Unit Of Measure", version.unit, "status") != "Active":
		fail("NDS_UNIT_INELIGIBLE", "The selected unit is not an active governed unit.")
	if not version.required_by_date:
		fail("NDS_FIELD_REQUIRED", "Required-by date is required.")
	fy = selectable_financial_year(need.financial_year)
	required_by = getdate(version.required_by_date)
	if not (getdate(fy["start_date"]) <= required_by <= getdate(fy["end_date"])):
		fail(
			"NDS_REQUIRED_BY_OUTSIDE_FY",
			"Required-by date must fall within the target financial year.",
		)


def _require_reason(reason: str) -> str:
	text = cstr(reason).strip()
	if not (REASON_MIN <= len(text) <= REASON_MAX):
		fail("NDS_FIELD_REQUIRED", f"A reason of {REASON_MIN}-{REASON_MAX} characters is required.")
	return text


def _content_values(
	*,
	title: str,
	description: str = "",
	expected_operational_result: str = "",
	indicative_quantity: float | None = None,
	unit: str = "",
	required_by_date: str | None = None,
) -> dict[str, Any]:
	"""A partial Draft is valid once the title is (§12.3, NDS-AC-004)."""
	return {
		"title": cstr(title).strip(),
		"description": cstr(description).strip(),
		"expected_operational_result": cstr(expected_operational_result).strip(),
		"indicative_quantity": flt(indicative_quantity) if indicative_quantity not in (None, "") else None,
		"unit": cstr(unit).strip() or None,
		"required_by_date": required_by_date or None,
	}


# --- §5.1 initial lifecycle ------------------------------------------------


def create_need(
	*,
	procuring_entity: str,
	organisation_unit: str,
	financial_year: str,
	title: str,
	description: str = "",
	expected_operational_result: str = "",
	indicative_quantity: float | None = None,
	unit: str = "",
	required_by_date: str | None = None,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""Save Draft Version 1 and generate the Need reference (§5.1)."""
	# Captured before any local is bound, so the digest is exactly the
	# caller's arguments (§9 NDS_IDEMPOTENCY_CONFLICT).
	payload = dict(locals())
	if replay := _existing(idempotency_key, payload):
		return replay
	principal = actor(user)
	fy = selectable_financial_year(financial_year)
	pe, ou = cstr(procuring_entity).strip(), cstr(organisation_unit).strip()
	require_create(principal, pe, ou, fy["id"])
	# NDS-BR-002 / NDS-AC-003 — initial creation requires an Open window.
	require_open_intake(pe, fy["id"])
	reference, lock_name = _next_reference(pe, fy["id"])
	try:
		need = frappe.get_doc(
			{
				"doctype": "Departmental Need",
				"need_reference": reference,
				"procuring_entity": pe,
				"organisation_unit": ou,
				"financial_year": fy["id"],
				"current_state": STATE_DRAFT,
				"record_version": 1,
			}
		).insert(ignore_permissions=True)
		version = _create_version(
			need,
			values=_content_values(
				title=title,
				description=description,
				expected_operational_result=expected_operational_result,
				indicative_quantity=indicative_quantity,
				unit=unit,
				required_by_date=required_by_date,
			),
		)
		need.current_version = version.name
		need.save(ignore_permissions=True)
		_record_decision(
			need,
			fingerprint=_fingerprint(payload),
			action=ACTION_CREATE,
			prior=STATE_DRAFT,
			result=STATE_DRAFT,
			principal=principal,
			idempotency_key=idempotency_key,
			version=version.name,
		)
		return _result(need, action=ACTION_CREATE)
	finally:
		frappe.db.sql("select release_lock(%s)", lock_name)


def update_need(
	*,
	need: str,
	title: str,
	description: str = "",
	expected_operational_result: str = "",
	indicative_quantity: float | None = None,
	unit: str = "",
	required_by_date: str | None = None,
	expected_version: int,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""Save the owner's Draft, returned correction or Draft successor (§5.1, §5.2)."""
	# Captured before any local is bound, so the digest is exactly the
	# caller's arguments (§9 NDS_IDEMPOTENCY_CONFLICT).
	payload = dict(locals())
	if replay := _existing(idempotency_key, payload):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_version(doc, expected_version)
	require_author_command(doc, principal)
	if doc.current_state == STATE_ACCEPTED:
		version, action = _require_open_successor(doc), ACTION_SAVE_SUCCESSOR
	elif doc.current_state in {STATE_DRAFT, STATE_RETURNED}:
		version, action = _current_version(doc), ACTION_SAVE_DRAFT
	else:
		fail("NDS_STATE_CONFLICT", "This Departmental Need is no longer editable.")
	if version.version_status != VERSION_DRAFT:
		fail("NDS_STATE_CONFLICT", "The current version is not editable.")
	version.update(
		_content_values(
			title=title,
			description=description,
			expected_operational_result=expected_operational_result,
			indicative_quantity=indicative_quantity,
			unit=unit,
			required_by_date=required_by_date,
		)
	)
	version.save(ignore_permissions=True)
	_bump(doc)
	_record_decision(
		doc,
		fingerprint=_fingerprint(payload),
		action=action,
		prior=doc.current_state,
		result=doc.current_state,
		principal=principal,
		idempotency_key=idempotency_key,
		version=version.name,
		before_hash=before_hash,
	)
	return _result(doc, action=action)


def submit_need(
	*, need: str, expected_version: int, idempotency_key: str, user: str | None = None
) -> dict[str, Any]:
	"""Lock the version, hash it and open one departmental review task (§5.1, §5.2)."""
	# Captured before any local is bound, so the digest is exactly the
	# caller's arguments (§9 NDS_IDEMPOTENCY_CONFLICT).
	payload = dict(locals())
	if replay := _existing(idempotency_key, payload):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_version(doc, expected_version)
	require_author_command(doc, principal)
	prior = doc.current_state
	if prior == STATE_ACCEPTED:
		# §5.2 — the accepted version stays effective, so the root state does not
		# move while its successor is under review.
		version = _require_open_successor(doc)
		action, target, task_type = ACTION_SUBMIT_SUCCESSOR, STATE_ACCEPTED, TASK_SUCCESSOR_ACCEPTANCE
	elif prior in {STATE_DRAFT, STATE_RETURNED}:
		version = _current_version(doc)
		# NDS-BR-002/003 — the initial submission needs an Open window; a
		# correction of a version submitted before close does not.
		if prior == STATE_DRAFT:
			require_open_intake(doc.procuring_entity, doc.financial_year)
		action = ACTION_SUBMIT if prior == STATE_DRAFT else ACTION_RESUBMIT
		target, task_type = STATE_SUBMITTED, TASK_INITIAL_ACCEPTANCE
	else:
		fail("NDS_STATE_CONFLICT", "This Departmental Need cannot be submitted.")
	if version.version_status != VERSION_DRAFT:
		fail("NDS_STATE_CONFLICT", "Only a Draft version may be submitted.")
	_validate_submission(doc, version)
	content_hash = _content_hash(version)
	frappe.db.set_value(
		"Departmental Need Version",
		version.name,
		{"version_status": VERSION_SUBMITTED, "content_hash": content_hash},
		update_modified=False,
	)
	_bump(doc, target)
	task = _open_task(doc, task_type=task_type, version=version.name)
	_record_decision(
		doc,
		fingerprint=_fingerprint(payload),
		action=action,
		prior=prior,
		result=target,
		principal=principal,
		idempotency_key=idempotency_key,
		version=version.name,
		task=task.name,
		before_hash=before_hash,
		content_hash=content_hash,
	)
	notify_need_transition(doc, action=action)
	return _result(doc, action=action, task=task.name)


def review_need(
	*,
	need: str,
	decision: str,
	task: str,
	expected_version: int,
	decision_token: str,
	idempotency_key: str,
	reason: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	"""Return, accept or decline the submitted initial version or successor (§5.1, §5.2).

	The task type decides which lifecycle applies. In the successor lifecycle the
	root stays `Accepted for planning` throughout, because the earlier accepted
	version remains effective until — and unless — the successor is accepted.
	"""
	# Captured before any local is bound, so the digest is exactly the
	# caller's arguments (§9 NDS_IDEMPOTENCY_CONFLICT).
	payload = dict(locals())
	if replay := _existing(idempotency_key, payload):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_version(doc, expected_version)
	require_review_command(doc, principal)
	# NDS-BR-006 / NDS-AC-010 — the maker of a version may never decide it. This
	# is unconditional and rechecked on the server, never inferred from the UI.
	if is_owner(doc, principal):
		fail("NDS_MAKER_CHECKER", "You cannot decide your own submitted Need.")
	task_type = cstr(
		frappe.db.get_value("Departmental Need Review Task", cstr(task).strip(), "task_type")
	)
	if task_type == TASK_SUCCESSOR_ACCEPTANCE:
		version = _require_open_successor(doc)
		choices = {
			"return": (ACTION_RETURN_SUCCESSOR, STATE_ACCEPTED, VERSION_RETURNED),
			"accept": (ACTION_ACCEPT_SUCCESSOR, STATE_ACCEPTED, VERSION_ACCEPTED),
			"decline": (ACTION_DECLINE_SUCCESSOR, STATE_ACCEPTED, VERSION_NOT_TAKEN_FORWARD),
		}
	elif task_type == TASK_INITIAL_ACCEPTANCE:
		if doc.current_state != STATE_SUBMITTED:
			fail("NDS_STATE_CONFLICT", "Only a Submitted Departmental Need may be reviewed.")
		version = _current_version(doc)
		choices = {
			"return": (ACTION_RETURN, STATE_RETURNED, VERSION_RETURNED),
			"accept": (ACTION_ACCEPT, STATE_ACCEPTED, VERSION_ACCEPTED),
			"decline": (ACTION_DECLINE, STATE_NOT_TAKEN_FORWARD, VERSION_NOT_TAKEN_FORWARD),
		}
	else:
		fail("NDS_STATE_CONFLICT", "This task is not a Departmental Need acceptance decision.")
	if version.version_status != VERSION_SUBMITTED:
		fail("NDS_STATE_CONFLICT", "Only a Submitted version may be decided.")
	if decision not in choices:
		fail("NDS_STATE_CONFLICT", "Select return, accept or decline.")
	action, target, version_status = choices[decision]
	prior = doc.current_state
	# NDS-BR-011 — return and decline require a reason; accept collects none.
	reason_text = _require_reason(reason) if action in REASON_REQUIRED_ACTIONS else ""
	_consume_task(task, doc.name, task_type, decision_token)
	_set_version_status(version, version_status)
	superseded, successor, earlier = "", "", None
	if decision == "return":
		# §5.1 / §5.2 / NDS-AC-011 — the submitted snapshot is preserved and a
		# copied correction Draft is created server-side; it is never unlocked
		# in place.
		copy = _create_version(
			doc, values=_content_payload_for_copy(version), based_on=version.name
		)
		doc.current_version = copy.name
		successor = copy.name
	elif decision == "accept":
		# NDS-AC-017 — supersession, repointing and the published lineage all
		# happen in this one transaction.
		if task_type == TASK_SUCCESSOR_ACCEPTANCE:
			superseded = cstr(doc.current_accepted_version)
			earlier = frappe.get_doc("Departmental Need Version", superseded)
			_set_version_status(earlier, VERSION_SUPERSEDED)
		doc.current_accepted_version = version.name
		doc.current_version = version.name
	elif task_type == TASK_SUCCESSOR_ACCEPTANCE:
		# NDS-AC-018 — a declined successor leaves the earlier accepted version
		# current, so the root pointer goes back to it.
		doc.current_version = doc.current_accepted_version
	_bump(doc, target)
	_record_decision(
		doc,
		fingerprint=_fingerprint(payload),
		action=action,
		prior=prior,
		result=target,
		principal=principal,
		idempotency_key=idempotency_key,
		version=version.name,
		reason=reason_text,
		task=task,
		before_hash=before_hash,
		content_hash=cstr(version.content_hash),
	)
	# §7.1 — the outbox row lands in this same transaction, so the event exists
	# if and only if the acceptance committed.
	event = ""
	if decision == "accept":
		if superseded:
			event = publish_superseded(doc, earlier=earlier, successor=version)
		else:
			event = publish_accepted(doc, version)
	notify_need_transition(doc, action=action)
	result = _result(doc, action=action, task=task)
	result["successor_version"] = successor
	result["superseded_version"] = superseded
	result["event_id"] = event
	return result


def _content_payload_for_copy(version) -> dict[str, Any]:
	return {field: version.get(field) for field in VERSION_CONTENT_FIELDS}


def withdraw_need(
	*,
	need: str,
	expected_version: int,
	idempotency_key: str,
	reason: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	"""Withdraw the owner's Draft or returned correction (§5.1)."""
	# Captured before any local is bound, so the digest is exactly the
	# caller's arguments (§9 NDS_IDEMPOTENCY_CONFLICT).
	payload = dict(locals())
	if replay := _existing(idempotency_key, payload):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_version(doc, expected_version)
	require_author_command(doc, principal)
	if doc.current_state not in {STATE_DRAFT, STATE_RETURNED}:
		fail(
			"NDS_STATE_CONFLICT",
			"An accepted Departmental Need requires a governed withdrawal request.",
		)
	prior = doc.current_state
	_set_version_status(_current_version(doc), VERSION_WITHDRAWN)
	_bump(doc, STATE_WITHDRAWN)
	_record_decision(
		doc,
		fingerprint=_fingerprint(payload),
		action=ACTION_WITHDRAW,
		prior=prior,
		result=STATE_WITHDRAWN,
		principal=principal,
		idempotency_key=idempotency_key,
		version=doc.current_version,
		before_hash=before_hash,
	)
	return _result(doc, action=ACTION_WITHDRAW)


# --- §5.2 accepted successor lifecycle -------------------------------------


def create_accepted_need_successor(
	*, need: str, expected_version: int, idempotency_key: str, user: str | None = None
) -> dict[str, Any]:
	"""Copy the current accepted version into the only permitted Draft successor.

	The accepted version is untouched and remains effective (NDS-AC-016); the
	root state does not move.
	"""
	# Captured before any local is bound, so the digest is exactly the
	# caller's arguments (§9 NDS_IDEMPOTENCY_CONFLICT).
	payload = dict(locals())
	if replay := _existing(idempotency_key, payload):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_version(doc, expected_version)
	require_author_command(doc, principal)
	if doc.current_state != STATE_ACCEPTED or not doc.current_accepted_version:
		fail("NDS_STATE_CONFLICT", "Only an Accepted for planning Need may be updated.")
	if _open_successor(doc):
		fail("NDS_OPEN_SUCCESSOR_EXISTS", "This Departmental Need already has an open update.")
	# NDS-BR-003 — a successor may be proposed while the PE/FY context is active;
	# it is not gated on the intake window.
	selectable_financial_year(doc.financial_year)
	accepted = frappe.get_doc("Departmental Need Version", doc.current_accepted_version)
	copy = _create_version(
		doc, values=_content_payload_for_copy(accepted), based_on=accepted.name
	)
	doc.current_version = copy.name
	_bump(doc)
	_record_decision(
		doc,
		fingerprint=_fingerprint(payload),
		action=ACTION_CREATE_SUCCESSOR,
		prior=STATE_ACCEPTED,
		result=STATE_ACCEPTED,
		principal=principal,
		idempotency_key=idempotency_key,
		version=copy.name,
		before_hash=before_hash,
	)
	result = _result(doc, action=ACTION_CREATE_SUCCESSOR)
	result["successor_version"] = copy.name
	return result


def cancel_accepted_need_successor(
	*,
	need: str,
	expected_version: int,
	idempotency_key: str,
	reason: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	"""Withdraw the Draft successor; the earlier accepted version stays current.

	NDS-AC-033 — cancelling withdraws only that successor.
	"""
	# Captured before any local is bound, so the digest is exactly the
	# caller's arguments (§9 NDS_IDEMPOTENCY_CONFLICT).
	payload = dict(locals())
	if replay := _existing(idempotency_key, payload):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_version(doc, expected_version)
	require_author_command(doc, principal)
	successor = _require_open_successor(doc)
	if successor.version_status != VERSION_DRAFT:
		fail("NDS_STATE_CONFLICT", "Only a Draft update may be cancelled.")
	_set_version_status(successor, VERSION_WITHDRAWN)
	doc.current_version = doc.current_accepted_version
	_bump(doc)
	_record_decision(
		doc,
		fingerprint=_fingerprint(payload),
		action=ACTION_CANCEL_SUCCESSOR,
		prior=STATE_ACCEPTED,
		result=STATE_ACCEPTED,
		principal=principal,
		idempotency_key=idempotency_key,
		version=successor.name,
		reason=cstr(reason).strip(),
		before_hash=before_hash,
	)
	result = _result(doc, action=ACTION_CANCEL_SUCCESSOR)
	result["cancelled_version"] = successor.name
	return result


# --- §5.3 accepted withdrawal lifecycle ------------------------------------


def check_withdrawal_dependency(need: str, accepted_version: str) -> dict[str, Any]:
	"""§8.1 `check_accepted_need_withdrawal_dependency` — no mutation.

	Reads the §4.7 projection Planning maintains, never Planning's own tables:
	the firm D1 boundary makes `NeedPlanningUsageChanged.v1` the only channel.
	NDS-BR-016 ties the block to the exact accepted version, and §5.3 is
	explicit that a Draft or Submitted DPP is not an Active Plan dependency —
	only an Active Plan inclusion is, which is precisely what the projection
	reports.
	"""
	detail = planning_usage_detail(cstr(need), cstr(accepted_version))
	included = detail["usage"] == USAGE_FULL
	# The token the reviewer's decision was taken against (§4.6).
	fingerprint = hashlib.sha256(
		json.dumps(
			{
				"usage": detail["usage"],
				"active_plan": detail["active_plan"],
				"active_plan_item": detail["active_plan_item"],
				"source_event_id": detail["source_event_id"],
			},
			sort_keys=True,
		).encode()
	).hexdigest()
	return {
		"need": cstr(need),
		"accepted_version": cstr(accepted_version),
		"included": included,
		"active_plan": detail["active_plan"],
		"active_plan_item": detail["active_plan_item"],
		"dependency_version": fingerprint,
	}


def request_withdrawal(
	*,
	need: str,
	expected_version: int,
	idempotency_key: str,
	reason: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""Create the only open withdrawal request and one review task (§5.3)."""
	# Captured before any local is bound, so the digest is exactly the
	# caller's arguments (§9 NDS_IDEMPOTENCY_CONFLICT).
	payload = dict(locals())
	if replay := _existing(idempotency_key, payload):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_version(doc, expected_version)
	require_author_command(doc, principal)
	if doc.current_state != STATE_ACCEPTED:
		fail(
			"NDS_STATE_CONFLICT",
			"Only an Accepted for planning Need uses the withdrawal-request process.",
		)
	reason_text = _require_reason(reason)
	if _open_withdrawal_request(doc.name):
		fail(
			"NDS_WITHDRAWAL_ALREADY_OPEN",
			"An open withdrawal request already exists for this Departmental Need.",
		)
	dependency = check_withdrawal_dependency(doc.name, doc.current_accepted_version)
	request = frappe.get_doc(
		{
			"doctype": "Need Withdrawal Request",
			"withdrawal_request_id": f"NDS-WDR-{uuid4().hex.upper()[:12]}",
			"departmental_need": doc.name,
			"accepted_version": doc.current_accepted_version,
			"requested_by": principal,
			"reason": reason_text,
			"status": WITHDRAWAL_AWAITING_REVIEW,
			"planning_dependency_version": dependency["dependency_version"],
			"record_version": 1,
			"fixture_namespace": doc.fixture_namespace,
		}
	).insert(ignore_permissions=True)
	task = _open_task(doc, task_type=TASK_WITHDRAWAL, withdrawal_request=request.name)
	# The Need stays Accepted for planning until approval succeeds (§4.6).
	_bump(doc)
	_record_decision(
		doc,
		fingerprint=_fingerprint(payload),
		action=ACTION_REQUEST_WITHDRAWAL,
		prior=STATE_ACCEPTED,
		result=STATE_ACCEPTED,
		principal=principal,
		idempotency_key=idempotency_key,
		withdrawal_request=request.name,
		reason=reason_text,
		task=task.name,
		before_hash=before_hash,
	)
	notify_need_transition(doc, action=ACTION_REQUEST_WITHDRAWAL)
	result = _result(doc, action=ACTION_REQUEST_WITHDRAWAL, task=task.name)
	result["withdrawal_request"] = request.name
	result["dependency"] = dependency
	return result


def decide_withdrawal(
	*,
	need: str,
	task: str,
	decision: str,
	expected_version: int,
	decision_token: str,
	idempotency_key: str,
	reason: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	"""Approve, block for clearance, or decline an accepted withdrawal (§5.3).

	The live Planning dependency is re-read inside the same transaction as the
	decision, so `Approve` can never complete against a stale "cleared" reading
	(NDS-AC-019). `Evaluate` and `Re-evaluate` leave the task Open because the
	request is not resolved; only `Approve` and `Decline` close it.
	"""
	# Captured before any local is bound, so the digest is exactly the
	# caller's arguments (§9 NDS_IDEMPOTENCY_CONFLICT).
	payload = dict(locals())
	if replay := _existing(idempotency_key, payload):
		return replay
	principal = actor(user)
	doc = _locked_need(need)
	before_hash = _state_hash(doc)
	_check_version(doc, expected_version)
	require_review_command(doc, principal)
	if doc.current_state != STATE_ACCEPTED:
		fail(
			"NDS_STATE_CONFLICT",
			"Only an Accepted for planning Need may complete governed withdrawal.",
		)
	if decision not in {"approve", "evaluate", "decline"}:
		fail("NDS_STATE_CONFLICT", "Select approve, evaluate or decline.")
	request = _locked_withdrawal_request(task, doc.name)
	if cstr(request.requested_by) == principal:
		fail("NDS_MAKER_CHECKER", "You cannot decide your own withdrawal request.")
	dependency = check_withdrawal_dependency(doc.name, request.accepted_version)
	prior_status = cstr(request.status)

	if decision == "approve":
		if dependency["included"]:
			fail(
				"NDS_ACTIVE_PLAN_DEPENDENCY",
				"Planning must clear the Active Plan dependency before withdrawal can be approved.",
			)
		_consume_task(task, doc.name, TASK_WITHDRAWAL, decision_token)
		_update_request(request, WITHDRAWAL_APPROVED, dependency)
		# The accepted version and any open successor go with the Need: a
		# Withdrawn Need cannot leave a live version behind it.
		for version in filter(None, {doc.current_accepted_version, _open_successor(doc)}):
			frappe.db.set_value(
				"Departmental Need Version",
				version,
				"version_status",
				VERSION_WITHDRAWN,
				update_modified=False,
			)
		action, target = ACTION_APPROVE_WITHDRAWAL, STATE_WITHDRAWN
		reason_text = ""
		withdrawn_event = publish_withdrawn(
			doc,
			version=frappe.get_doc("Departmental Need Version", doc.current_accepted_version)
			if doc.current_accepted_version
			else None,
			withdrawal_request=request.name,
			decided_by=principal,
		)
	elif decision == "evaluate":
		withdrawn_event = ""
		if not dependency["included"]:
			fail(
				"NDS_STATE_CONFLICT",
				"There is no live Plan dependency to clear; approve or decline this request.",
			)
		_touch_task(task, doc.name, TASK_WITHDRAWAL, decision_token)
		_update_request(request, WITHDRAWAL_AWAITING_CLEARANCE, dependency)
		action = (
			ACTION_REEVALUATE_WITHDRAWAL
			if prior_status == WITHDRAWAL_AWAITING_CLEARANCE
			else ACTION_EVALUATE_WITHDRAWAL
		)
		target, reason_text = STATE_ACCEPTED, ""
	else:
		withdrawn_event = ""
		reason_text = _require_reason(reason)
		_consume_task(task, doc.name, TASK_WITHDRAWAL, decision_token)
		_update_request(request, WITHDRAWAL_DECLINED, dependency)
		action, target = ACTION_DECLINE_WITHDRAWAL, STATE_ACCEPTED

	_bump(doc, target)
	_record_decision(
		doc,
		fingerprint=_fingerprint(payload),
		action=action,
		prior=STATE_ACCEPTED,
		result=target,
		principal=principal,
		idempotency_key=idempotency_key,
		withdrawal_request=request.name,
		reason=reason_text,
		task=task,
		before_hash=before_hash,
	)
	notify_need_transition(doc, action=action)
	result = _result(doc, action=action, task=task)
	result["withdrawal_request"] = request.name
	result["withdrawal_status"] = _request_status(request.name)
	result["dependency"] = dependency
	result["event_id"] = withdrawn_event
	return result


def _open_withdrawal_request(need: str) -> str:
	return cstr(
		frappe.db.get_value(
			"Need Withdrawal Request",
			{"departmental_need": need, "status": ("in", list(OPEN_WITHDRAWAL_STATUSES))},
			"name",
		)
		or ""
	)


def _locked_withdrawal_request(task: str, need: str):
	name = cstr(
		frappe.db.get_value(
			"Departmental Need Review Task", cstr(task).strip(), "withdrawal_request"
		)
		or ""
	)
	if not name:
		fail("NDS_STATE_CONFLICT", "This task carries no withdrawal request.")
	frappe.db.sql("select name from `tabNeed Withdrawal Request` where name=%s for update", name)
	request = frappe.get_doc("Need Withdrawal Request", name)
	if request.departmental_need != need or request.status not in OPEN_WITHDRAWAL_STATUSES:
		fail("NDS_STATE_CONFLICT", "This withdrawal request is not open for decision.")
	return request


def _update_request(request, status: str, dependency: dict[str, Any]) -> None:
	frappe.db.set_value(
		"Need Withdrawal Request",
		request.name,
		{
			"status": status,
			"planning_dependency_version": dependency["dependency_version"],
			"record_version": int(request.record_version or 0) + 1,
		},
		update_modified=False,
	)


def _request_status(name: str) -> str:
	return cstr(frappe.db.get_value("Need Withdrawal Request", name, "status"))
