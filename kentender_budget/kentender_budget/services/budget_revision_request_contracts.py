# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.11 §4.10, §8.5, §9.2 — the Budget receiving side of a
Procurement Planning budget revision request.

A request is not a revision (BUD-BR-028): it records that Planning's plan
update needs more on one line than the registered allocation, shows the
Budget Officer that pending work (BUD-DES-18), and reports how it ended —
Revised when a successor that changes the line is approved (BUD-BR-029),
Declined by the Budget Officer with a reason or by closing the Budget
(BUD-BR-030), or Withdrawn by Planning. Each outcome publishes one
`BudgetRevisionRequestOutcome.v1` through a transactional outbox, delivered
idempotently and in order; Budget draws no Planning conclusion.

Failures a caller can correct return `{"ok": False, "code", "errors"}`
(AGENTS.md §6.10), in the style of every other Budget command.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, flt, now_datetime

from kentender_budget.services.budget_idempotency import payload_digest
from kentender_budget.services.budget_money import parse_money, scale_for
from kentender_budget.services.budget_money import stored as money_stored
from kentender_budget.services.budget_write_family import budget_write

#: The one registered caller of receive/withdraw (§6 "Planning service
#: principal"). Planning's gateway sets this flag around the call; nothing
#: else in the product does.
PLANNING_PRINCIPAL = "procurement_planning"
PRINCIPAL_FLAG = "kt_budget_service_principal"

OUTCOME_EVENT = "BudgetRevisionRequestOutcome.v1"
CONSUMERS_HOOK = "kt_budget_revision_outcome_consumers"

STATUS_OPEN = "Open"
STATUS_REVISED = "Revised"
STATUS_DECLINED = "Declined"
STATUS_WITHDRAWN = "Withdrawn"

CLOSED_BUDGET_REASON = "The budget for this financial year is closed."

REASON_MIN, REASON_MAX = 10, 500


def _as_dict(payload) -> dict[str, Any]:
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return dict(payload or {})


def _error(code: str, field: str, message: str, **extra) -> dict[str, Any]:
	return {"ok": False, "code": code, "errors": {field: message}, **extra}


def _require_planning_principal() -> None:
	if frappe.flags.get(PRINCIPAL_FLAG) != PLANNING_PRINCIPAL:
		frappe.throw(_("Only Procurement Planning may send or withdraw a budget revision request."), frappe.PermissionError)


def _new_reference() -> str:
	return f"BRR-{frappe.generate_hash(length=10).upper()}"


def _summary(request) -> dict[str, Any]:
	return {
		"budget_revision_request_id": request.budget_revision_request_id,
		"planning_request_id": request.planning_request_id,
		"status": request.status,
		"budget_line": request.budget_line,
		"approved_amount_at_receipt": flt(request.approved_amount_at_receipt),
		"planned_amount": flt(request.planned_amount),
		"over_amount": flt(request.over_amount),
		"linked_budget_version": cstr(request.linked_budget_version),
	}


# --------------------------------------------------------------------------
# Receipt (§8.5 item 1; BUD-BR-027)
# --------------------------------------------------------------------------


def receive_budget_revision_request(payload: dict | str | None = None) -> dict[str, Any]:
	"""Record one Open request from Planning's `RequestBudgetRevision`.

	Called inside Planning's transaction: it commits with that transaction or
	not at all. Idempotent on the Planning request id and the idempotency key.
	"""
	from kentender_budget.services.budget_audit_contracts import EVENT_REVISION_REQUEST_RECEIVED, safe_record_event
	from kentender_budget.services.budget_contracts import _active_version
	from kentender_core.services.authorization import resolve_assignments

	_require_planning_principal()
	payload = _as_dict(payload)
	planning_request_id = cstr(payload.get("planning_request_id")).strip()
	key = cstr(payload.get("idempotency_key")).strip()
	digest = payload_digest(payload)
	existing = frappe.db.get_value("Budget Revision Request", {"planning_request_id": planning_request_id}, "name")
	if existing:
		request = frappe.get_doc("Budget Revision Request", existing)
		if request.payload_digest and request.payload_digest != digest:
			return _error("BUDGET_IDEMPOTENCY_CONFLICT", "idempotency_key", _("This request differs from the original attempt. No new effect was created."))
		return {"ok": True, "replayed": True, **_summary(request)}

	requester = cstr(payload.get("requested_by"))
	assignments = resolve_assignments(requester, "Procurement Planner") if requester else []
	if not assignments:
		frappe.throw(_("The requesting Procurement Planner has no current assignment."), frappe.PermissionError)

	budget = frappe.db.get_value("Procurement Budget", {"fiscal_year": cstr(payload.get("fiscal_year"))}, "name")
	active = _active_version(budget) if budget else None
	if not active:
		return _error("BUDGET_INVALID_STATE", "budget", _("There is no current budget for this financial year."))
	line_version = frappe.db.get_value(
		"Procurement Budget Line Version",
		{"budget_version": active.name, "budget_line": cstr(payload.get("budget_line"))},
		["name", "approved_amount", "currency"], as_dict=True,
	)
	if not line_version:
		return _error("BUDGET_INVALID_STATE", "budget_line", _("This budget line is not in the current budget."))
	expected = cstr(payload.get("expected_line_revision"))
	if expected and expected != line_version.name:
		return _error("BUDGET_DECISION_BASIS_STALE", "budget_line", _("The budget line has changed. Refresh and check the plan again."))
	# AUD-XC-117 — exact amounts at the Budget currency's scale; a malformed,
	# non-finite or excess-scale planned amount fails typed, before any effect.
	scale = scale_for(line_version.currency)
	planned = parse_money(payload.get("planned_amount"), scale=scale, field="planned_amount", allow_zero=True)
	approved = money_stored(line_version.approved_amount, scale=scale)
	if planned <= approved:
		# BUD-BR-027 — Budget's own approved amount at receipt decides.
		return _error("BUDGET_REVISION_NOT_REQUIRED", "budget_line", _("This budget line already covers the planned amount. No budget revision is needed."))

	with budget_write():
		request = frappe.get_doc({
			"doctype": "Budget Revision Request",
			"budget_revision_request_id": _new_reference(),
			"planning_request_id": planning_request_id,
			"status": STATUS_OPEN,
			"budget": budget,
			"budget_line": cstr(payload.get("budget_line")),
			"budget_line_version_at_receipt": line_version.name,
			"approved_amount_at_receipt": approved,
			"planned_amount": planned,
			"over_amount": parse_money(payload.get("over_amount"), scale=scale, field="over_amount") if payload.get("over_amount") else (planned - approved),
			"plan_version_reference": cstr(payload.get("plan_version_reference")),
			# Planning supplies the display label: Budget never reads Planning's
			# records (Budget is upstream of Procurement).
			"plan_label": cstr(payload.get("plan_label")),
			"requested_by": requester,
			"requested_by_assignment": assignments[0].name,
			"requested_at": now_datetime(),
			"idempotency_key": key,
			"payload_digest": digest,
			"fixture_namespace": cstr(payload.get("fixture_namespace")),
		}).insert(ignore_permissions=True)
	safe_record_event(
		budget=budget, budget_version=active.name, event_type=EVENT_REVISION_REQUEST_RECEIVED,
		actor=requester, correlation_id=key or request.name, calling_module="Procurement Planning",
		downstream_reference=planning_request_id,
	)
	return {"ok": True, **_summary(request)}


# --------------------------------------------------------------------------
# Decline and withdrawal (BUD-BR-030)
# --------------------------------------------------------------------------


def decline_budget_revision_request(payload: dict | str | None = None) -> dict[str, Any]:
	"""The Budget Officer's decline with a 10–500 character reason."""
	from kentender_budget.services.budget_audit_contracts import EVENT_REVISION_REQUEST_DECLINED, safe_record_event
	from kentender_budget.services.budget_authorization import CAP_EDIT, require_budget_version_capability
	from kentender_budget.services.budget_contracts import _active_version

	payload = _as_dict(payload)
	request = _locked(cstr(payload.get("budget_revision_request")))
	active = _active_version(request.budget)
	require_budget_version_capability(frappe.session.user, CAP_EDIT, active)
	if request.status != STATUS_OPEN:
		return _closed(request)
	reason = cstr(payload.get("reason")).strip()
	if not (REASON_MIN <= len(reason) <= REASON_MAX):
		return _error("BUDGET_REASON_REQUIRED", "reason", _("Enter a reason of 10 to 500 characters."))
	_close(request, STATUS_DECLINED, by=frappe.session.user, reason=reason)
	safe_record_event(
		budget=request.budget, budget_version=active.name if active else None, event_type=EVENT_REVISION_REQUEST_DECLINED,
		actor=frappe.session.user, correlation_id=cstr(payload.get("idempotency_key")) or request.name,
		calling_module="Budget & Funding", reason=reason, downstream_reference=request.planning_request_id,
	)
	return {"ok": True, **_summary(request)}


def withdraw_budget_revision_request(payload: dict | str | None = None) -> dict[str, Any]:
	"""Planning withdraws its own request. A successor already started from
	it is not changed: it remains ordinary Budget Officer work (§8.5 item 4)."""
	from kentender_budget.services.budget_audit_contracts import EVENT_REVISION_REQUEST_WITHDRAWN, safe_record_event

	_require_planning_principal()
	payload = _as_dict(payload)
	name = frappe.db.get_value("Budget Revision Request", {"planning_request_id": cstr(payload.get("planning_request_id"))}, "name")
	if not name:
		return _error("BUDGET_REVISION_REQUEST_CLOSED", "budget_revision_request", _("This budget revision request has already been resolved. Refresh to see its outcome."))
	request = _locked(name)
	if request.status != STATUS_OPEN:
		return _closed(request)
	_close(request, STATUS_WITHDRAWN, by=PLANNING_PRINCIPAL)
	safe_record_event(
		budget=request.budget, event_type=EVENT_REVISION_REQUEST_WITHDRAWN, actor=cstr(payload.get("requested_by")) or "Administrator",
		correlation_id=cstr(payload.get("idempotency_key")) or request.name, calling_module="Procurement Planning",
		downstream_reference=request.planning_request_id,
	)
	return {"ok": True, **_summary(request)}


def _locked(name: str):
	if not name or not frappe.db.exists("Budget Revision Request", name):
		frappe.throw(_("Budget revision request not found"), frappe.DoesNotExistError)
	frappe.db.sql("select name from `tabBudget Revision Request` where name=%s for update", (name,))
	return frappe.get_doc("Budget Revision Request", name)


def _closed(request) -> dict[str, Any]:
	return _error(
		"BUDGET_REVISION_REQUEST_CLOSED", "budget_revision_request",
		_("This budget revision request has already been resolved. Refresh to see its outcome."),
		**_summary(request),
	)


def _close(request, status: str, *, by: str, reason: str = "", line_version: str = "", approved: float | None = None) -> None:
	request.status = status
	request.outcome_by = by
	request.outcome_at = now_datetime()
	if reason:
		request.decline_reason = reason
	request.outcome_sequence = int(request.outcome_sequence or 0) + 1
	with budget_write():
		request.save(ignore_permissions=True)
	publish_outcome(request, line_version=line_version, approved=approved)


# --------------------------------------------------------------------------
# Successor link and activation (BUD-BR-029), closure (BUD-BR-030)
# --------------------------------------------------------------------------


def link_successor(budget_revision_request: str, budget_version: str) -> None:
	"""`create_budget_successor_version(budget_revision_request_id=…)` records
	the created or reused successor on the request (§9.2)."""
	name = frappe.db.get_value("Budget Revision Request", {"budget_revision_request_id": budget_revision_request}, "name")
	if name:
		frappe.db.set_value("Budget Revision Request", name, "linked_budget_version", budget_version, update_modified=False)


def revise_on_activation(version) -> list[str]:
	"""BUD-BR-029 — in `approve_budget_version`'s own transaction: every Open
	request on a line whose approved amount the activated successor changed
	or omitted becomes Revised. A successor that leaves the line unchanged
	leaves the request Open."""
	from kentender_budget.services.budget_audit_contracts import EVENT_REVISION_REQUEST_REVISED, safe_record_event

	revised = []
	for row in frappe.get_all(
		"Budget Revision Request", filters={"budget": version.budget, "status": STATUS_OPEN},
		fields=["name", "budget_line", "approved_amount_at_receipt"], limit_page_length=0,
	):
		line = frappe.db.get_value(
			"Procurement Budget Line Version", {"budget_version": version.name, "budget_line": row.budget_line},
			["name", "approved_amount"], as_dict=True,
		)
		if line and money_stored(line.approved_amount) == money_stored(row.approved_amount_at_receipt):
			continue
		request = _locked(row.name)
		_close(request, STATUS_REVISED, by=frappe.session.user, line_version=line.name if line else "", approved=flt(line.approved_amount) if line else 0.0)
		safe_record_event(
			budget=version.budget, budget_version=version.name, event_type=EVENT_REVISION_REQUEST_REVISED,
			actor=frappe.session.user, correlation_id=request.name, calling_module="Budget & Funding",
			downstream_reference=request.planning_request_id,
		)
		revised.append(request.budget_revision_request_id)
	return revised


def decline_on_close(budget: str) -> list[str]:
	"""BUD-BR-030 — closing the Budget declines every remaining Open request
	with the system reason."""
	from kentender_budget.services.budget_audit_contracts import EVENT_REVISION_REQUEST_DECLINED, safe_record_event

	declined = []
	for name in frappe.get_all("Budget Revision Request", filters={"budget": budget, "status": STATUS_OPEN}, pluck="name"):
		request = _locked(name)
		_close(request, STATUS_DECLINED, by="system", reason=CLOSED_BUDGET_REASON)
		safe_record_event(
			budget=budget, event_type=EVENT_REVISION_REQUEST_DECLINED, actor=frappe.session.user,
			correlation_id=request.name, calling_module="Budget & Funding", reason=CLOSED_BUDGET_REASON,
			downstream_reference=request.planning_request_id,
		)
		declined.append(request.budget_revision_request_id)
	return declined


# --------------------------------------------------------------------------
# Outcome outbox (§8.5 item 3)
# --------------------------------------------------------------------------


def _utc_iso(value) -> str:
	"""BUD v1.11 §6 — an instant crossing the contract is ISO-8601 UTC.
	Budget stores naive site-timezone datetimes (`now_datetime()`), so the
	value is read in that zone before conversion."""
	from kentender_core.utils.instants import to_utc_iso

	return to_utc_iso(value)


def publish_outcome(request, *, line_version: str = "", approved: float | None = None) -> str:
	"""Append the outcome to the outbox in the state change's transaction,
	then try to deliver it at once; an undelivered event stays Pending and
	is retried in order (`retry_pending_outcomes`)."""
	body = {
		"event": OUTCOME_EVENT,
		"planning_request_id": request.planning_request_id,
		"budget_revision_request_id": request.budget_revision_request_id,
		"outcome": request.status,
		"resulting_line_version": line_version,
		"resulting_approved_amount": approved,
		"reason": cstr(request.decline_reason),
		"decided_by": cstr(request.outcome_by),
		"decided_by_name": cstr(frappe.db.get_value("User", request.outcome_by, "full_name")) if request.outcome_by and frappe.db.exists("User", request.outcome_by) else "",
		"decided_at": _utc_iso(request.outcome_at),
		"sequence": int(request.outcome_sequence or 0),
	}
	with budget_write():
		event = frappe.get_doc({
			"doctype": "Budget Revision Request Event",
			"event_id": f"{request.budget_revision_request_id}-{body['sequence']}",
			"budget_revision_request": request.name,
			"planning_request_id": request.planning_request_id,
			"outcome": request.status,
			"sequence": body["sequence"],
			"payload": json.dumps(body, default=str),
			"status": "Pending",
			"fixture_namespace": cstr(request.fixture_namespace),
		}).insert(ignore_permissions=True)
	_deliver(event)
	return event.name


def _deliver(event) -> bool:
	"""Hand one event to every registered consumer, idempotently. A consumer
	failure rolls back only the consumer's own writes and leaves the event
	Pending; the Budget state change it reports stands."""
	body = json.loads(event.payload or "{}")
	savepoint = f"kt_brr_{frappe.generate_hash(length=8)}"
	frappe.db.savepoint(savepoint)
	try:
		for path in frappe.get_hooks(CONSUMERS_HOOK) or []:
			frappe.get_attr(path)(body)
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		frappe.db.set_value("Budget Revision Request Event", event.name, {
			"attempts": int(event.attempts or 0) + 1,
			"last_error": frappe.get_traceback()[-1000:],
		}, update_modified=False)
		frappe.log_error(title="Budget revision outcome delivery failed", message=frappe.get_traceback())
		return False
	frappe.db.set_value("Budget Revision Request Event", event.name, {
		"status": "Delivered", "delivered_at": now_datetime(), "attempts": int(event.attempts or 0) + 1,
	}, update_modified=False)
	return True


def retry_pending_outcomes() -> int:
	"""Scheduler entry: deliver every Pending outcome, oldest first per
	request so each request's outcomes arrive in order."""
	delivered = 0
	for name in frappe.get_all("Budget Revision Request Event", filters={"status": "Pending"}, order_by="creation asc, sequence asc", pluck="name"):
		if _deliver(frappe.get_doc("Budget Revision Request Event", name)):
			delivered += 1
	if delivered:
		frappe.db.commit()
	return delivered


# --------------------------------------------------------------------------
# Reads (§11.1B BUD-DES-18, the line-detail quiet line, My Work)
# --------------------------------------------------------------------------


def open_requests_for_workspace(budget: str, user: str) -> list[dict[str, Any]]:
	"""The Budget Officer's pending request rows (BUD-DES-18). Approver,
	Auditor and technical readers get none: the request is not their work."""
	from kentender_budget.services.budget_authorization import CAP_EDIT, has_budget_version_capability
	from kentender_budget.services.budget_contracts import _active_version, _draft_version
	from kentender_budget.services.budget_contracts import format_kes_full

	active = _active_version(budget)
	if not active or not has_budget_version_capability(user, CAP_EDIT, active):
		return []
	draft = _draft_version(budget)
	rows = []
	for request in frappe.get_all(
		"Budget Revision Request", filters={"budget": budget, "status": STATUS_OPEN},
		fields=["name", "budget_revision_request_id", "budget_line", "approved_amount_at_receipt", "planned_amount", "over_amount", "plan_version_reference", "plan_label", "requested_by", "requested_at"],
		order_by="requested_at asc", limit_page_length=0,
	):
		title = cstr(frappe.db.get_value("Procurement Budget Line Version", {"budget_version": active.name, "budget_line": request.budget_line}, "title")) or request.budget_line
		plan = request.plan_label or request.plan_version_reference
		rows.append({
			"budget_revision_request_id": request.budget_revision_request_id,
			"budget_line": request.budget_line,
			"line_title": title,
			"title": _("Budget revision requested for {0}").format(title),
			"narrative": _(
				"Procurement Planning's plan update needs {0} on this line. The registered allocation is {1}, so it is over by {2}. "
				"An increase needs external approval before you record it as an allocation update."
			).format(format_kes_full(request.planned_amount), format_kes_full(request.approved_amount_at_receipt), format_kes_full(request.over_amount)),
			"requested_by": _requester_label(request.requested_by),
			"requested_by_name": cstr(frappe.db.get_value("User", request.requested_by, "full_name") or request.requested_by),
			"requested_at_display": _display(request.requested_at),
			"plan_label": plan,
			"over_display": format_kes_full(request.over_amount),
			# §11.1B — Update registered allocation, or Continue update when a
			# successor is already open; Decline request.
			"primary_action": "continue_update" if draft else "update_allocation",
			"primary_label": _("Continue update") if draft else _("Update registered allocation"),
			"can_decline": True,
		})
	return rows


def open_request_line_note(budget_line: str) -> str:
	"""§11 line detail — one quiet line when the line has an Open request."""
	requested_at = frappe.db.get_value("Budget Revision Request", {"budget_line": budget_line, "status": STATUS_OPEN}, "requested_at", order_by="requested_at asc")
	if not requested_at:
		return ""
	return _("Budget revision requested by Procurement Planning on {0}.").format(_display(requested_at, date_only=True))


def _display(value, *, date_only: bool = False) -> str:
	from kentender_budget.services.budget_contracts import _display_datetime

	if not value:
		return ""
	text = _display_datetime(frappe.utils.get_datetime(value))
	return text.split(",")[0] if date_only else text


def _requester_label(user: str) -> str:
	name = cstr(frappe.db.get_value("User", user, "full_name") or user)
	return _("{0}, Procurement Planner").format(name)
