# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.13 proposal (owner decision 1, 16 October 2026) — the only way to lower a Closed commitment.

A Closed commitment keeps its final amount in Committed (BUD-BR-031). It accepts no increase and no ordinary adjustment from the contract service: `adjust_commitment` refuses it. Its amount is
lowered only by an evidenced **correction** that two different people authorise inside Budget:

1. a **Budget Officer records** it: the new, lower amount, the reason, one or more evidence references and the Contract Management reference it relates to;
2. a **different person holding Budget Approver decides** it. Approving lowers the commitment's running amount, appends one *Commitment corrected* funding event with the amounts before and
   after, the reason, the evidence, the contract reference and both people, and returns exactly the decrease to Available. The reservation is never touched: money that left a reservation
   when it became a commitment does not go back to it. Returning it records the decision and changes nothing else.

The correction is its own record. The original conversion event, the closure event and every earlier event are never edited; the commitment's `current_amount` is the running figure the position
reads. A correction is allowed after the Budget is Closed (a decrease only, with the same two people); an increase is never possible. Reopening the contract in Contract Management calls none
of this and changes no balance. The two commands are whitelisted for the Budget screens that are still to be designed; they are not downstream service calls and carry no service principal."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_budget.services.budget_audit_contracts import (
	EVENT_COMMITMENT_CORRECTED,
	EVENT_CORRECTION_RECORDED,
	EVENT_CORRECTION_RETURNED,
	record_event,
)
from kentender_budget.services.budget_authorization import ROLE_BUDGET_APPROVER, ROLE_BUDGET_OFFICER
from kentender_budget.services.budget_idempotency import run_idempotent
from kentender_budget.services.budget_locking import locked_doc, lock_budgets_of_lines
from kentender_budget.services.budget_line_contracts import format_kes_full
from kentender_budget.services.budget_money import parse_money, scale_for, stored
from kentender_budget.services.budget_reference import allocate_correction_reference
from kentender_budget.services.budget_write_family import budget_write
from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record
from kentender_core.services.responsibility_errors import fail

CORRECTION = "Commitment Correction"
AWAITING, APPROVED, RETURNED = "Awaiting approval", "Approved", "Returned"
APPROVE, RETURN = "Approve", "Return"
REASON_MIN, REASON_MAX = 10, 500
CALLING_MODULE = "Budget & Funding"


def _as_dict(payload) -> dict[str, Any]:
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return dict(payload or {})


def _require_role(user: str, role: str) -> None:
	"""A correction is Budget's own business action: it needs the live Site-wide responsibility for the role, like every other Budget command (BUD-BR-001)."""
	decision = authorise_record(user=user, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND)
	if not decision.allowed:
		fail(decision.reason_code or "AUTH_RESPONSIBILITY_REQUIRED")


def _refusal(code: str, field: str, message: str, **extra) -> dict[str, Any]:
	return {"ok": False, "code": code, "errors": {field: message}, **extra}


def _resolve_commitment(commitment: str):
	key = (commitment or "").strip()
	if not key:
		frappe.throw(_("Commitment is required"))
	name = key if frappe.db.exists("Procurement Commitment", key) else frappe.db.get_value("Procurement Commitment", {"generated_reference": key}, "name")
	if not name:
		frappe.throw(_("Commitment {0} not found").format(key), frappe.DoesNotExistError)
	return frappe.get_doc("Procurement Commitment", name)


def _resolve_correction(correction: str):
	key = (correction or "").strip()
	if not key:
		frappe.throw(_("Correction is required"))
	name = key if frappe.db.exists(CORRECTION, key) else frappe.db.get_value(CORRECTION, {"generated_reference": key}, "name")
	if not name:
		frappe.throw(_("Correction {0} not found").format(key), frappe.DoesNotExistError)
	return frappe.get_doc(CORRECTION, name)


def _evidence(doc) -> list[str]:
	return [str(ref) for ref in (frappe.parse_json(doc.evidence_json) if doc.evidence_json else [])]


def correction_summary(doc) -> dict[str, Any]:
	scale = scale_for(doc.currency)
	before, after = stored(doc.before_amount, scale=scale), stored(doc.after_amount, scale=scale)
	return {
		"id": doc.name, "code": doc.generated_reference, "status": doc.status, "commitment": doc.commitment, "budget": doc.budget, "budget_line": doc.budget_line,
		"before_amount": float(before), "after_amount": float(after), "decrease": float(before - after), "currency": doc.currency,
		"reason": doc.reason, "evidence": _evidence(doc), "contract_reference": doc.contract_reference,
		"recorded_by": doc.recorded_by, "recorded_at": str(doc.recorded_at or ""), "decided_by": doc.decided_by or "", "decided_at": str(doc.decided_at or ""),
		"decision_reason": doc.decision_reason or "", "revision": str(doc.modified),
	}


def _position(budget_line: str) -> dict[str, float]:
	"""The line's position, read under lock. A Closed Budget has no Active Version: its approved amounts are those of the Version that closed, so a correction made after closure reports the real
	approved amount and not zero."""
	from kentender_budget.services.budget_contracts import _active_version, _line_position_exact, _line_version_for

	budget = frappe.db.get_value("Procurement Budget Line", budget_line, "budget")
	version = _active_version(budget, for_update=True)
	version_name = version.name if version else frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Closed"}, "name", order_by="version_number desc", for_update=True)
	line_version = _line_version_for(version_name, budget_line, for_update=True) if version_name else None
	exact = _line_position_exact(budget_line, line_version, for_update=True)
	return {key: float(value) for key, value in exact.items()}


# ---- record ---------------------------------------------------------------------------------------------------------------------


def record_commitment_correction(payload: dict | str | None = None) -> dict[str, Any]:
	"""Budget Officer. Record a correction that lowers a Closed commitment. Payload: `commitment`, `new_amount`, `reason` (10–500 characters), `evidence` (a list of reference strings, at least one),
	`contract_reference` (the Contract Management reference the correction relates to), optional `expected_revision` (the commitment revision read), `idempotency_key`."""
	payload = _as_dict(payload)
	return run_idempotent(
		payload=payload, fn=lambda: _record(payload), budget_for=lambda r: (r.get("correction") or {}).get("budget"),
		command="RecordCommitmentCorrection", authorise=lambda: _require_role(frappe.session.user, ROLE_BUDGET_OFFICER),
	)


def _record(payload: dict[str, Any]) -> dict[str, Any]:
	from kentender_budget.services.budget_commitment_contracts import _commitment_result

	commitment = _resolve_commitment(payload.get("commitment") or "")
	scale = scale_for(commitment.currency)
	reason = (payload.get("reason") or "").strip()
	evidence = [str(ref).strip() for ref in (payload.get("evidence") or []) if str(ref).strip()]
	contract_reference = (payload.get("contract_reference") or "").strip()
	problems = {}
	if not evidence:
		problems["evidence"] = _("Add at least one evidence reference that supports the correction.")
	if not contract_reference:
		problems["contract_reference"] = _("Enter the Contract Management reference this correction relates to.")
	if not (REASON_MIN <= len(reason) <= REASON_MAX):
		problems["reason"] = _("Give the reason in {0} to {1} characters.").format(REASON_MIN, REASON_MAX)
	if problems:
		return {"ok": False, "code": "BUDGET_EVIDENCE_REQUIRED", "errors": problems}
	if payload.get("new_amount") is None:
		frappe.throw(_("The corrected amount is required"))
	after = parse_money(payload["new_amount"], scale=scale, field="new_amount", allow_zero=True)

	# the same lock order as every other commitment change (AUD-XC-101..103); everything below is a locking read of the latest committed state
	lock_budgets_of_lines([commitment.budget_line])
	commitment = locked_doc("Procurement Commitment", commitment.name)
	before = stored(commitment.current_amount, scale=scale)
	if commitment.status != "Closed":
		return _refusal("BUDGET_INVALID_STATE", "commitment", _("Only a Closed commitment is corrected here. An Active commitment is adjusted by its own contract."), commitment=_commitment_result(commitment))
	expected = (payload.get("expected_revision") or "").strip()
	if expected and expected != str(commitment.modified):
		return _refusal("BUDGET_STALE_REVISION", "commitment", _("The commitment changed after it was read. Review the latest amount before recording a correction."), commitment=_commitment_result(commitment))
	if after >= before:
		return _refusal("BUDGET_INVALID_STATE", "new_amount", _("A correction can only lower the amount ({0} now). It cannot raise it.").format(format_kes_full(before, currency=commitment.currency)))
	if frappe.db.exists(CORRECTION, {"commitment": commitment.name, "status": AWAITING}):
		return _refusal("BUDGET_INVALID_STATE", "commitment", _("A correction is already awaiting approval for this commitment."))

	key = (payload.get("idempotency_key") or "").strip()
	doc = frappe.get_doc(
		{
			"doctype": CORRECTION, "generated_reference": allocate_correction_reference(), "commitment": commitment.name, "budget": commitment.budget, "budget_line": commitment.budget_line,
			"status": AWAITING, "before_amount": before, "after_amount": after, "currency": commitment.currency, "reason": reason, "evidence_json": json.dumps(evidence),
			"contract_reference": contract_reference, "recorded_by": frappe.session.user, "recorded_at": now_datetime(), "idempotency_key": key,
		}
	)
	with budget_write():
		doc.insert(ignore_permissions=True)
	# the record is also on the ledger, so who recorded it is attributable independently of the row (a non-best-effort write: a correction with no attribution must not stand)
	event = record_event(
		budget=commitment.budget, budget_line=commitment.budget_line, reservation=commitment.reservation or None, commitment=commitment.name, event_type=EVENT_CORRECTION_RECORDED,
		actor=frappe.session.user, correlation_id=key or doc.name, calling_module=CALLING_MODULE, downstream_reference=contract_reference, amount=after,
		currency=commitment.currency, reason="; ".join(evidence)[:1000],
	)
	doc.recorded_event = event
	with budget_write():
		doc.save(ignore_permissions=True)
	doc.reload()
	return {"ok": True, "correction": correction_summary(doc)}


# ---- decide ---------------------------------------------------------------------------------------------------------------------


def decide_commitment_correction(payload: dict | str | None = None) -> dict[str, Any]:
	"""Budget Approver, and never the person who recorded the correction. Payload: `correction`, `decision` (`Approve` or `Return`), `reason` (required to return, 10–500 characters), `idempotency_key`."""
	payload = _as_dict(payload)
	return run_idempotent(
		payload=payload, fn=lambda: _decide(payload), budget_for=lambda r: (r.get("correction") or {}).get("budget"),
		command="DecideCommitmentCorrection", authorise=lambda: _require_role(frappe.session.user, ROLE_BUDGET_APPROVER),
	)


def _recorded_by_event(doc) -> str | None:
	return frappe.db.get_value("Budget Audit Event", doc.recorded_event, "actor") if doc.recorded_event else None


def _decide(payload: dict[str, Any]) -> dict[str, Any]:
	from kentender_budget.services.budget_commitment_contracts import _commitment_result

	decision = (payload.get("decision") or "").strip().capitalize()
	if decision not in (APPROVE, RETURN):
		frappe.throw(_("Decision must be Approve or Return"))
	reason = (payload.get("reason") or "").strip()
	if decision == RETURN and not (REASON_MIN <= len(reason) <= REASON_MAX):
		return _refusal("BUDGET_EVIDENCE_REQUIRED", "reason", _("Give the reason for returning the correction in {0} to {1} characters.").format(REASON_MIN, REASON_MAX))
	correction = _resolve_correction(payload.get("correction") or "")
	lock_budgets_of_lines([correction.budget_line])
	correction = locked_doc(CORRECTION, correction.name)
	if correction.status != AWAITING:
		return _refusal("BUDGET_INVALID_STATE", "correction", _("This correction has already been decided."), correction=correction_summary(correction))
	# AUD-XC-105 — decided on the locked row, and fail closed: when neither the row nor its ledger event shows who recorded it, nobody can be shown to be independent of it
	user = frappe.session.user
	recorders = {correction.recorded_by, _recorded_by_event(correction)}
	if not recorders - {None, ""} or user in recorders:
		fail("AUTH_SEGREGATION_BLOCKED")

	commitment = locked_doc("Procurement Commitment", correction.commitment)
	scale = scale_for(commitment.currency)
	key = (payload.get("idempotency_key") or "").strip()
	evidence = _evidence(correction)

	if decision == RETURN:
		correction.status, correction.decided_by, correction.decided_at, correction.decision_reason = RETURNED, user, now_datetime(), reason
		with budget_write():
			correction.save(ignore_permissions=True)
		record_event(
			budget=correction.budget, budget_line=correction.budget_line, reservation=commitment.reservation or None, commitment=commitment.name, event_type=EVENT_CORRECTION_RETURNED, actor=user,
			correlation_id=key or correction.name, calling_module=CALLING_MODULE, downstream_reference=correction.contract_reference, amount=correction.after_amount,
			currency=correction.currency, reason=reason,
		)
		correction.reload()
		_tell_contract_management(commitment.name, approved=False, correction=correction_summary(correction), attempt=key or correction.name)
		return {"ok": True, "correction": correction_summary(correction), "commitment": _commitment_result(commitment)}

	before, after = stored(correction.before_amount, scale=scale), stored(correction.after_amount, scale=scale)
	if commitment.status != "Closed" or stored(commitment.current_amount, scale=scale) != before:
		return _refusal("BUDGET_STALE_REVISION", "correction", _("The commitment changed after this correction was recorded. Record a new correction against its current amount."), correction=correction_summary(correction))
	position_before = _position(commitment.budget_line)
	commitment.current_amount = after
	with budget_write():
		commitment.save(ignore_permissions=True)
	position_after = _position(commitment.budget_line)
	if round(position_after["available"] - position_before["available"], scale) != float(before - after) or position_after["reserved"] != position_before["reserved"]:
		frappe.throw(_("A correction must return exactly the decrease to Available and change nothing else"), frappe.ValidationError, title="BUDGET_POSITION_CHANGED")
	record_event(
		budget=correction.budget, budget_line=correction.budget_line, reservation=commitment.reservation or None, commitment=commitment.name, event_type=EVENT_COMMITMENT_CORRECTED, actor=user,
		correlation_id=key or correction.name, calling_module=CALLING_MODULE, downstream_reference=correction.contract_reference, amount=after, currency=commitment.currency,
		before=position_before, after=position_after, reason="; ".join(evidence)[:1000],
	)
	correction.status, correction.decided_by, correction.decided_at, correction.decision_reason = APPROVED, user, now_datetime(), reason
	with budget_write():
		correction.save(ignore_permissions=True)
	correction.reload()
	commitment.reload()
	_tell_contract_management(commitment.name, approved=True, correction=correction_summary(correction), attempt=key or correction.name)
	return {"ok": True, "correction": correction_summary(correction), "commitment": _commitment_result(commitment), "positions": {"before": position_before, "after": position_after}}


def _tell_contract_management(commitment: str, *, approved: bool, correction: dict[str, Any], attempt: str) -> None:
	"""A request Contract Management raised for this correction hears the result, in order (BUD-CHG-001 v1.16 8.6). Nothing is sent when no request names the commitment."""
	from kentender_budget.services.budget_contract_funding import correction_decided

	correction_decided(commitment, approved=approved, correction=correction, attempt=attempt)


# ---- reads for the screens ---------------------------------------------------------------------------------------------------


def _holds_role(user: str, role: str) -> bool:
	return bool(authorise_record(user=user, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND).allowed)


def line_commitments(budget_line: str, user: str) -> list[dict[str, Any]]:
	"""The commitments charged to a line, of either origin, for the line detail. **Correct commitment** is offered to the Budget Officer for a Closed commitment with no correction already awaiting approval."""
	officer = _holds_role(user, ROLE_BUDGET_OFFICER)
	rows = []
	for c in frappe.get_all("Procurement Commitment", filters={"budget_line": budget_line}, fields=["name", "generated_reference", "contract", "status", "current_amount", "currency", "origin", "reservation"], order_by="creation asc"):
		awaiting = frappe.db.exists(CORRECTION, {"commitment": c.name, "status": AWAITING})
		rows.append({"id": c.name, "code": c.generated_reference, "contract": c.contract, "status": c.status, "origin": c.origin, "current_amount": float(c.current_amount or 0), "currency": c.currency,
			"correction_awaiting": bool(awaiting), "can_correct": bool(officer and c.status == "Closed" and not awaiting)})
	return rows


def get_commitment_correction(commitment: str = "", correction: str = "") -> dict[str, Any]:
	"""BUD-DES-20 — one Closed commitment with its correction, the caller's actions and why not. Read-only; the closed-year and stale variants are facts the server states, not something the screen works out."""
	from kentender_budget.services.budget_authorization import require_budget_read_scope
	from kentender_budget.services.budget_commitment_contracts import _commitment_result

	record = _resolve_correction(correction) if (correction or "").strip() else None
	commit = _resolve_commitment(commitment) if (commitment or "").strip() else (_resolve_commitment(record.commitment) if record else None)
	if commit is None:
		frappe.throw(_("Commitment is required"))
	require_budget_read_scope("Procurement Budget Line", commit.budget_line)
	if record is None:
		name = frappe.db.get_value(CORRECTION, {"commitment": commit.name, "status": AWAITING}, "name") or frappe.db.get_value(CORRECTION, {"commitment": commit.name}, "name", order_by="creation desc")
		record = frappe.get_doc(CORRECTION, name) if name else None
	user = frappe.session.user
	officer, approver = _holds_role(user, ROLE_BUDGET_OFFICER), _holds_role(user, ROLE_BUDGET_APPROVER)
	scale = scale_for(commit.currency)
	line_title = frappe.db.get_value("Procurement Budget Line Version", {"budget_line": commit.budget_line}, "title", order_by="creation desc") or commit.budget_line
	closed_year = bool(frappe.db.get_value("Procurement Budget Version", {"budget": commit.budget, "status": "Closed"}, "name")) and not frappe.db.get_value("Procurement Budget Version", {"budget": commit.budget, "status": "Active"}, "name")
	actions: dict[str, Any] = {}
	if record is None or record.status != AWAITING:
		actions["record"] = bool(officer and commit.status == "Closed")
	stale = bool(record and record.status == AWAITING and (commit.status != "Closed" or stored(commit.current_amount, scale=scale) != stored(record.before_amount, scale=scale)))
	if record is not None and record.status == AWAITING and approver:
		recorders = {record.recorded_by, _recorded_by_event(record)} - {None, ""}
		blocked = (not recorders) or user in recorders
		actions.update(decide=not blocked and not stale, blocked=_("Another Budget Approver must decide this correction.") if blocked else "")
	return {"ok": True, "commitment": {**_commitment_result(commit), "budget_line_title": line_title, "retained_amount": float(stored(commit.current_amount, scale=scale))},
		"correction": correction_summary(record) if record else None, "closed_year": closed_year, "stale": stale, "actions": actions}
