# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The existing-contract commitment entry (BUD-CHG-001 v1.16 sections 4.12, 8.7, 8.8, 9.2; BUD-BR-037 to BUD-BR-040).

One coordinated entry recognises the funding charge of an independently registered contract for **one** eligible Active Budget year and its currency. A Budget Officer prepares it from the request Contract
Management raised; a different Budget Approver decides it. It is the only way such a contract reaches the Budget, and it is never a general commitment editor.

* **The amount is calculated, never typed.** Amount requiring funding = the confirmed gross funding charge for the year (from Finance's `ContractFundingBasis.v1`, which Contract Management owns) minus the
  verified, non-overlapping commitment coverage Budget already holds for this contract and year. Neither figure is editable. Coverage above the charge is an error (`BUDGET_ENTRY_DUPLICATE`), never clamped to
  zero; a native invoice or payment is not coverage.
* **Save is not submit.** Draft and Returned preparation save with incomplete rows, reconciliation and year confirmation and move no money. Submission validates the complete payload (rows add up to the calculated
  amount, every line eligible and in the target year and currency, the reconciliation text given) and freezes it; Approved is immutable.
* **The Approver is independent.** Different from the entry's preparer and from every Finance confirmer of the basis the entry relied on; checked on actual participation (`budget_funding_authority`).
* **Approval is all or nothing.** Under the Budget's locks: the request is still open and the basis and the coverage are exactly those submitted (otherwise the Approver returns it for refreshed preparation;
  nothing is silently recalculated), the lines are still eligible, the grouped requirement per line fits the line's available balance, and then one Active commitment is created per positive row, each with its ledger
  event. A shortfall creates nothing: the entry is returned to the Officer with the grouped shortfall.
* No reservation is created, and no earlier year's commitment is moved, released or reopened."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from kentender_budget.services import budget_contract_funding as funding
from kentender_budget.services import budget_funding_authority as authority
from kentender_budget.services.budget_audit_contracts import (
	EVENT_ENTRY_APPROVED,
	EVENT_ENTRY_COMMITMENT,
	EVENT_ENTRY_RETURNED,
	EVENT_ENTRY_SUBMITTED,
	record_event,
)
from kentender_budget.services.budget_commitment_corrections import _position
from kentender_budget.services.budget_idempotency import payload_digest, run_idempotent
from kentender_budget.services.budget_line_contracts import format_kes_full
from kentender_budget.services.budget_locking import locked_doc, lock_budgets_of_lines
from kentender_budget.services.budget_money import scale_for, stored, text
from kentender_budget.services.budget_reference import allocate_commitment_reference, allocate_entry_reference
from kentender_budget.services.budget_write_family import budget_write
from kentender_core.services import contract_funding_request_contract as seam
from kentender_core.services.responsibility_errors import fail

ENTRY, ROW = funding.ENTRY, "Existing Contract Entry Row"
DRAFT, AWAITING, RETURNED, APPROVED, SUPERSEDED = "Draft", "Awaiting approval", "Returned", "Approved", "Superseded"
APPROVE, RETURN = "Approve", "Return"
REASON_MIN, REASON_MAX = funding.REASON_MIN, funding.REASON_MAX
CALLING_MODULE = "Budget & Funding"
_ZERO = Decimal("0")


def _as_dict(payload) -> dict[str, Any]:
	return dict(frappe.parse_json(payload) if isinstance(payload, str) else (payload or {}))


# ---- reading ---------------------------------------------------------------------------------------------------------------------


def resolve_entry(reference: str, *, lock: bool = False):
	key = cstr(reference).strip()
	if not key:
		frappe.throw(_("Entry is required"))
	name = key if frappe.db.exists(ENTRY, key) else frappe.db.get_value(ENTRY, {"generated_reference": key}, "name")
	if not name:
		frappe.throw(_("Entry {0} not found").format(key), frappe.DoesNotExistError)
	return locked_doc(ENTRY, name) if lock else frappe.get_doc(ENTRY, name)


def _line_facts(lines: list[str]) -> dict[str, dict[str, Any]]:
	"""Each line's current Active-version identity and position, for eligibility and display."""
	out: dict[str, dict[str, Any]] = {}
	for line in sorted({l for l in lines if l}):
		budget = frappe.db.get_value("Procurement Budget Line", line, "budget")
		if not budget:
			continue
		version = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name")
		facts = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "budget_line": line}, ["title", "owner_org_unit", "funding_source", "approved_amount", "currency"], as_dict=True) if version else None
		out[line] = {"budget": budget, "active": bool(version), "title": facts.title if facts else "", "owner_org_unit": facts.owner_org_unit if facts else "", "funding_source": facts.funding_source if facts else "",
			"reference": frappe.db.get_value("Procurement Budget Line", line, "generated_reference") or ""}
	return out


def _problem_for_line(request, line: str, facts: dict[str, Any]) -> str:
	"""Why a line cannot take this request's funding, or an empty string. BUD-BR-007/008: Entity-wide or the source unit's own line, an available funding source, the target year and currency only."""
	budget = funding.target_budget(request.fiscal_year)
	if not facts:
		return _("Budget line not found.")
	if facts["budget"] != budget:
		return _("This line is not in the Budget for {0}.").format(request.fiscal_year)
	if not facts["active"]:
		return _("The Budget for {0} has no Active version.").format(request.fiscal_year)
	if facts["owner_org_unit"] and request.source_organisation_unit and facts["owner_org_unit"] != request.source_organisation_unit:
		return _("This line belongs to another department.")
	if facts["funding_source"] and frappe.db.get_value("Funding Source", facts["funding_source"], "record_status") != "Available":
		return _("This funding source is not available.")
	return ""


def amounts_of(request) -> dict[str, Any]:
	"""The calculated figures for a request: confirmed charge, verified coverage and the amount requiring funding, or Nones while the year is unconfirmed. Coverage above the charge is returned as `excess`."""
	scale = scale_for(request.currency)
	charge = funding.confirmed_charge(request)
	cover = funding.coverage_of(request)
	required = (charge - cover["total"]) if charge is not None else None
	return {"charge": charge, "coverage": cover, "required": required, "excess": cover["total"] > charge if charge is not None else False, "scale": scale}


def _rows(entry) -> list[dict[str, Any]]:
	scale = scale_for(entry.currency)
	return [{"row_id": r.row_id, "budget_line": r.budget_line or "", "amount": text(stored(r.amount, scale=scale), scale=scale) if r.amount else "",
		"funding_source": r.funding_source or "", "commitment": r.commitment or ""} for r in entry.rows]


def _doc_rows(entry) -> list[dict[str, Any]]:
	"""The saved rows as input for the same cleaning a new save goes through."""
	return [{"row_id": r["row_id"], "budget_line": r["budget_line"], "amount": r["amount"]} for r in _rows(entry)]


def entry_summary(entry, request=None) -> dict[str, Any]:
	request = request or frappe.get_doc(funding.REQUEST, entry.request)
	scale = scale_for(entry.currency)
	rows = _rows(entry)
	facts = _line_facts([r["budget_line"] for r in rows])
	for row in rows:
		line = facts.get(row["budget_line"]) or {}
		row.update(title=line.get("title", ""), reference=line.get("reference", ""), source_organisation_unit=request.source_organisation_unit or "")
		if row["budget_line"] and line:
			position = _position_safe(row["budget_line"])
			row["available"] = text(Decimal(str(position["available"])), scale=scale) if position else None
	money = lambda value: text(stored(value, scale=scale), scale=scale) if value is not None else None  # noqa: E731
	return {
		"id": entry.name, "code": entry.generated_reference, "request": request.name, "request_code": request.generated_reference, "kind": entry.kind, "status": entry.status, "version": int(entry.version_no or 1),
		"contract": entry.contract, "contract_reference": entry.contract_reference or "", "fiscal_year": entry.fiscal_year or "", "currency": entry.currency, "source_organisation_unit": entry.source_organisation_unit or "",
		"confirmed_charge": money(entry.confirmed_charge), "coverage_total": money(entry.coverage_total), "amount_requiring_funding": money(entry.amount_requiring_funding), "rows_total": money(entry.rows_total),
		"coverage": frappe.parse_json(entry.coverage_json) if entry.coverage_json else [], "reconciliation": entry.reconciliation or "", "rows": rows,
		"basis_stale": bool(entry.status == AWAITING and (int(entry.basis_revision or 0) != int(request.basis_revision or 0) or cstr(entry.basis_digest) != cstr(request.basis_digest))),
		"prepared_by": entry.prepared_by or "", "submitted_by": entry.submitted_by or "", "submitted_at": cstr(entry.submitted_at or ""), "decided_by": entry.decided_by or "", "decided_at": cstr(entry.decided_at or ""),
		"decision_reason": entry.decision_reason or "", "original_commitment": entry.original_commitment or "", "revision": str(entry.modified),
	}


def _position_safe(line: str) -> dict[str, float] | None:
	"""A line's position for display only: a plain read that locks nothing."""
	from kentender_budget.services.budget_contracts import _active_version, _line_position, _line_version_for

	try:
		budget = frappe.db.get_value("Procurement Budget Line", line, "budget")
		version = _active_version(budget) if budget else None
		return _line_position(line, _line_version_for(version.name, line)) if version else None
	except Exception:
		return None


def get_contract_funding(request: str) -> dict[str, Any]:
	"""Everything the funding screens need for one request, in one read: the request with its calculated figures, the current entry, the actions the caller may take and why not."""
	from kentender_budget.services.budget_authorization import approved_only_reader, holds_any_budget_responsibility

	user = frappe.session.user
	if not holds_any_budget_responsibility(user) or approved_only_reader(user):  # a funding request names a contract, a supplier and amounts: a Budget responsibility or a technical read is needed, and reading approved plans alone is not enough
		frappe.throw(_("You do not have access to this funding request."), frappe.PermissionError)
	doc = funding.resolve_request(request)
	entry = funding.current_entry(doc)
	out: dict[str, Any] = {"ok": True, "request": funding.summary(doc), "entry": entry_summary(entry, doc) if entry else None, "actions": {}}
	is_officer, is_approver = _holds(user, authority.ROLE_BUDGET_OFFICER), _holds(user, authority.ROLE_BUDGET_APPROVER)
	actions: dict[str, Any] = {}
	if doc.status == funding.OPEN and doc.kind != "Correction":
		confirmed = doc.year_allocation_status == seam.YEAR_CONFIRMED
		if is_officer and (entry is None or entry.status in (DRAFT, RETURNED)):
			actions.update(save=True, submit=confirmed, decline=True)
		if is_approver and entry is not None and entry.status == AWAITING:
			blocked = _blocked_reason(entry, user)
			actions.update(approve=not blocked and not out["entry"]["basis_stale"], **{"return": not blocked}, blocked=blocked)
	out["actions"] = actions
	if doc.fiscal_year and doc.status in (funding.OPEN,):
		from kentender_budget.services.budget_line_contracts import list_eligible_budget_lines

		out["eligible_lines"] = list_eligible_budget_lines(doc.fiscal_year, doc.source_organisation_unit or None)
	return out


def _holds(user: str, role: str) -> bool:
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	return bool(authorise_record(user=user, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND).allowed)


def _blocked_reason(entry, user: str) -> str:
	confirmers = frappe.parse_json(entry.confirmers_json) if entry.confirmers_json else []
	if not authority.participants(prepared_by=entry.prepared_by, submitted_by=entry.submitted_by, confirmers=confirmers) - {""}:
		return _("Another Budget Approver must decide this funding entry.")
	try:
		authority.require_independent(user, prepared_by=entry.prepared_by, submitted_by=entry.submitted_by, confirmers=confirmers)
	except Exception:
		frappe.clear_last_message()
		return _("Another Budget Approver must decide this funding entry.")
	return ""


# ---- record (save a Draft or Returned preparation) -----------------------------------------------------------------------------


def _next_row_id(existing: list[str]) -> str:
	numbers = [int(r[1:]) for r in existing if r.startswith("R") and r[1:].isdigit()]
	return f"R{(max(numbers) if numbers else 0) + 1}"


def _clean_rows(request, rows: Any, current_ids: list[str], *, complete: bool) -> tuple[list[dict[str, Any]], dict[str, str]]:
	rows = rows or []
	clean, problems, used = [], {}, list(current_ids)
	facts = _line_facts([cstr(r.get("budget_line")).strip() for r in rows if isinstance(r, dict)])
	for index, raw in enumerate(rows, start=1):
		raw = raw if isinstance(raw, dict) else {}
		row_id = cstr(raw.get("row_id")).strip() or _next_row_id(used)
		used.append(row_id)
		line, amount_text = cstr(raw.get("budget_line")).strip(), raw.get("amount")
		entry_row = {"row_id": row_id, "budget_line": line, "amount": None, "funding_source": ""}
		if line:
			why = _problem_for_line(request, line, facts.get(line, {}))
			if why:
				problems[f"rows.{row_id}.budget_line"] = why
			else:
				entry_row["funding_source"] = facts[line]["funding_source"] or ""
		elif complete:
			problems[f"rows.{row_id}.budget_line"] = _("Choose a budget line.")
		if amount_text not in (None, ""):
			try:
				entry_row["amount"] = funding.money(amount_text, request.currency, f"rows.{row_id}.amount")
			except frappe.ValidationError as exc:
				problems[f"rows.{row_id}.amount"] = frappe.safe_decode(str(exc))
			else:
				if entry_row["amount"] <= 0:
					problems[f"rows.{row_id}.amount"] = _("Enter an amount above zero.")
		elif complete:
			problems[f"rows.{row_id}.amount"] = _("Enter an amount.")
		clean.append(entry_row)
	if complete and not clean:
		problems["rows"] = _("Add at least one budget line.")
	return clean, problems


def _write_rows(entry, rows: list[dict[str, Any]]) -> None:
	entry.set("rows", [])
	for row in rows:
		entry.append("rows", {"row_id": row["row_id"], "budget_line": row["budget_line"] or None, "amount": row["amount"], "funding_source": row["funding_source"], "currency": entry.currency})


def record_existing_contract_commitment_entry(payload: dict | str | None = None) -> dict[str, Any]:
	"""Budget Officer. Save a Draft, or update a Returned preparation, from an exact open request. No money moves. Incomplete rows, reconciliation and year confirmation may be saved; only submission requires
	them. Payload: `request`, optional `entry` and `expected_revision` (the entry revision read), `rows` (`[{row_id?, budget_line, amount}]`), `reconciliation`, `idempotency_key`."""
	payload = _as_dict(payload)
	return run_idempotent(payload=payload, fn=lambda: _record(payload), budget_for=lambda r: (r.get("entry") or {}).get("budget"), command="RecordExistingContractCommitmentEntry",
		authorise=lambda: authority.require_officer(frappe.session.user))


def _record(payload: dict[str, Any]) -> dict[str, Any]:
	request = funding.resolve_request(payload.get("request") or "", lock=True)
	if request.kind == "Correction":
		return funding.refusal("BUDGET_INVALID_STATE", "request", _("A correction is recorded as a commitment correction, not as an entry."))
	if request.status != funding.OPEN:
		return funding.refusal("BUDGET_INVALID_STATE", "request", _("This funding request is no longer open."), request=funding.summary(request))
	entry = funding.current_entry(request)
	entry = locked_doc(ENTRY, entry.name) if entry else None
	if entry is not None and entry.status == SUPERSEDED:  # an abandoned attempt is retained; deliberate resubmission is the next version of the same lineage
		entry = None
	if entry is not None and entry.status not in (DRAFT, RETURNED):
		return funding.refusal("BUDGET_INVALID_STATE", "entry", _("This entry is {0} and cannot be edited.").format(entry.status.lower()), entry=entry_summary(entry, request))
	expected = cstr(payload.get("expected_revision")).strip()
	if entry is not None and expected and expected != str(entry.modified):
		return funding.refusal("BUDGET_STALE_REVISION", "entry", _("This entry changed since you opened it. Review the latest version."), entry=entry_summary(entry, request))
	user = frappe.session.user
	reconciliation = cstr(payload.get("reconciliation")).strip()
	rows, problems = _clean_rows(request, payload.get("rows"), [r.row_id for r in entry.rows] if entry else [], complete=False)
	if problems:
		return {"ok": False, "code": "BUDGET_LINE_NOT_ELIGIBLE", "errors": problems}
	now = amounts_of(request)
	scale = now["scale"]
	key = cstr(payload.get("idempotency_key")).strip()
	if entry is None:
		entry = frappe.get_doc({"doctype": ENTRY, "generated_reference": allocate_entry_reference(), "request": request.name, "version_no": 1 + frappe.db.count(ENTRY, {"request": request.name}), "kind": request.kind,
			"status": DRAFT, "contract": request.contract, "contract_reference": request.contract_reference, "fiscal_year": request.fiscal_year, "budget": funding.target_budget(request.fiscal_year),
			"currency": request.currency, "source_organisation_unit": request.source_organisation_unit, "original_commitment": request.original_commitment, "increment_event": request.subject_event,
			"prepared_by": user, "prepared_at": now_datetime(), "idempotency_key": key})
	entry.reconciliation = reconciliation
	entry.prepared_by, entry.prepared_at = user, now_datetime()
	_refresh_basis(entry, request, now)
	_write_rows(entry, rows)
	entry.rows_total = sum((r["amount"] for r in rows if r["amount"] is not None), _ZERO)
	with budget_write():
		entry.save(ignore_permissions=True) if not entry.is_new() else entry.insert(ignore_permissions=True)
	if request.current_entry != entry.name:
		request.current_entry = entry.name
		with budget_write():
			request.save(ignore_permissions=True)
	entry.reload()
	return {"ok": True, "entry": {**entry_summary(entry, request), "budget": entry.budget}, "request": funding.summary(request)}


def _refresh_basis(entry, request, now: dict[str, Any]) -> None:
	"""Copy what the entry relies on from the request, at preparation: the basis (digest and revision), its confirmers, the calculated figures and the coverage the amount was calculated against."""
	basis = frappe.parse_json(request.basis_json) if request.basis_json else {}
	entry.basis_json, entry.basis_digest, entry.basis_revision = request.basis_json, request.basis_digest, int(request.basis_revision or 0)
	entry.confirmers_json = json.dumps(basis.get("confirmers") or [])
	entry.confirmed_charge = now["charge"]
	entry.coverage_total = now["coverage"]["total"] if now["charge"] is not None else None
	entry.amount_requiring_funding = now["required"]
	entry.coverage_json = json.dumps(now["coverage"]["items"])
	entry.coverage_digest = now["coverage"]["digest"]


# ---- submit ----------------------------------------------------------------------------------------------------------------------


def submit_existing_contract_commitment_entry(payload: dict | str | None = None) -> dict[str, Any]:
	"""Budget Officer. Validate the complete payload and freeze it Awaiting approval. Payload: `entry`, `expected_revision`, `idempotency_key`."""
	payload = _as_dict(payload)
	return run_idempotent(payload=payload, fn=lambda: _submit(payload), budget_for=lambda r: (r.get("entry") or {}).get("budget"), command="SubmitExistingContractCommitmentEntry",
		authorise=lambda: authority.require_officer(frappe.session.user))


def _shortfalls(entry, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	scale = scale_for(entry.currency)
	needed: dict[str, Decimal] = {}
	for row in rows:
		needed[row["budget_line"]] = needed.get(row["budget_line"], _ZERO) + row["amount"]
	short = []
	for line in sorted(needed):
		position = _position(line)
		available = Decimal(str(position["available"]))
		if needed[line] > available:
			short.append({"budget_line": line, "needed": text(needed[line], scale=scale), "available": text(available, scale=scale), "shortfall": text(needed[line] - available, scale=scale)})
	return short


def _validated(entry, request) -> dict[str, Any] | None:
	"""The refusal that stops this entry being approved, or None: the year is confirmed, coverage is not above the charge, a new charge exists, and the calculation and coverage are exactly what was submitted."""
	now = amounts_of(request)
	problem = _calculation_problem(request, now)
	if problem:
		return problem
	if now["coverage"]["digest"] != entry.coverage_digest or now["charge"] != stored(entry.confirmed_charge, scale=now["scale"]):
		return funding.refusal("BUDGET_STALE_REVISION", "coverage", _("The funding position of this contract changed. Return this entry for an updated allocation."), entry=entry_summary(entry, request))
	return None


def _calculation_problem(request, now: dict[str, Any]) -> dict[str, Any] | None:
	if request.year_allocation_status != seam.YEAR_CONFIRMED:
		return funding.refusal("BUDGET_YEAR_ALLOCATION_REQUIRED", "request", _("Finance must confirm the funding year and amount."), request=funding.summary(request))
	if now["excess"]:
		return funding.refusal("BUDGET_ENTRY_DUPLICATE", "coverage", _("Budget already holds more for this contract and year ({0}) than the confirmed charge ({1}). Nothing is clamped to zero: the coverage must be reconciled first.").format(
			text(now["coverage"]["total"], scale=now["scale"]), text(now["charge"], scale=now["scale"])), request=funding.summary(request))
	if now["required"] is None or now["required"] <= 0:
		return funding.refusal("BUDGET_INVALID_STATE", "request", _("There is no new charge to fund for this year."), request=funding.summary(request))
	return None


def _submit(payload: dict[str, Any]) -> dict[str, Any]:
	entry = resolve_entry(payload.get("entry") or "", lock=True)
	request = funding.resolve_request(entry.request, lock=True)
	if entry.status not in (DRAFT, RETURNED) or request.status != funding.OPEN:
		return funding.refusal("BUDGET_INVALID_STATE", "entry", _("This entry cannot be submitted in its current state."), entry=entry_summary(entry, request))
	expected = cstr(payload.get("expected_revision")).strip()
	if expected and expected != str(entry.modified):
		return funding.refusal("BUDGET_STALE_REVISION", "entry", _("This entry changed since you opened it. Review the latest version."), entry=entry_summary(entry, request))
	user = frappe.session.user
	# the figures are recalculated from the request and Budget's own coverage now; a preparer who saved against an earlier basis submits against the current one, visibly
	now = amounts_of(request)
	if request.year_allocation_status == seam.YEAR_CONFIRMED:
		_refresh_basis(entry, request, now)
	problem = _validated_for_submit(entry, request, now)
	if problem:
		return problem
	scale = now["scale"]
	rows, problems = _clean_rows(request, _doc_rows(entry), [r.row_id for r in entry.rows], complete=True)
	reconciliation = cstr(entry.reconciliation).strip()
	if not (REASON_MIN <= len(reconciliation) <= REASON_MAX):
		problems["reconciliation"] = _("Explain how existing funding was checked against the confirmed charge, in {0} to {1} characters.").format(REASON_MIN, REASON_MAX)
	if problems:
		return {"ok": False, "code": "BUDGET_NOT_READY", "errors": problems, "entry": entry_summary(entry, request)}
	total = sum((r["amount"] for r in rows), _ZERO)
	if total != now["required"]:
		difference = total - now["required"]
		return {"ok": False, "code": "BUDGET_ENTRY_ROWS_MISMATCH", "errors": {"rows": _("The allocation rows must add up to the amount requiring funding. Required {0}, rows {1}, difference {2}.").format(
			text(now["required"], scale=scale), text(total, scale=scale), text(difference, scale=scale))}, "required": text(now["required"], scale=scale), "rows_total": text(total, scale=scale), "difference": text(difference, scale=scale)}
	lock_budgets_of_lines([r["budget_line"] for r in rows])
	short = _shortfalls(entry, rows)
	if short:
		return {"ok": False, "code": "BUDGET_INSUFFICIENT_FUNDS", "errors": {"rows": _("Not enough is available on one or more lines.")}, "shortfalls": short}
	entry.rows_total = total
	entry.status, entry.submitted_by, entry.submitted_at = AWAITING, user, now_datetime()
	entry.payload_digest = payload_digest({"rows": [(r["row_id"], r["budget_line"], text(r["amount"], scale=scale)) for r in rows], "reconciliation": reconciliation, "basis": entry.basis_digest, "coverage": entry.coverage_digest,
		"required": text(now["required"], scale=scale)})
	with budget_write():
		entry.save(ignore_permissions=True)
	if entry.budget:
		record_event(budget=entry.budget, event_type=EVENT_ENTRY_SUBMITTED, actor=user, correlation_id=cstr(payload.get("idempotency_key")) or entry.name, calling_module=CALLING_MODULE,
			downstream_reference=entry.contract_reference or entry.contract, amount=float(total), currency=entry.currency)
	funding.publish_outcome(request, seam.OUTCOME_ENTRY_SUBMITTED, attempt=cstr(payload.get("idempotency_key")) or entry.name, detail={"stage": "Awaiting approval", "entry": entry.generated_reference})
	entry.reload()
	return {"ok": True, "entry": {**entry_summary(entry, request), "budget": entry.budget}, "request": funding.summary(request)}


def _validated_for_submit(entry, request, now: dict[str, Any]) -> dict[str, Any] | None:
	problem = _calculation_problem(request, now)
	if problem:
		return problem
	budget = funding.target_budget(request.fiscal_year)
	if not budget or not frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name"):
		return funding.refusal("BUDGET_CONTEXT_NOT_FOUND", "fiscal_year", _("There is no Active Budget for {0} to fund this contract.").format(request.fiscal_year))
	return None


# ---- decide ----------------------------------------------------------------------------------------------------------------------


def decide_existing_contract_commitment_entry(payload: dict | str | None = None) -> dict[str, Any]:
	"""Budget Approver, independent of the entry's preparer and of every Finance confirmer the entry relied on. Approve creates every commitment or none; Return needs a reason (10–500 characters).
	Payload: `entry`, `decision` (`Approve` or `Return`), `reason`, `expected_revision`, `idempotency_key`."""
	payload = _as_dict(payload)
	return run_idempotent(payload=payload, fn=lambda: _decide(payload), budget_for=lambda r: (r.get("entry") or {}).get("budget"), command="DecideExistingContractCommitmentEntry",
		authorise=lambda: authority.require_approver(frappe.session.user))


def _decide(payload: dict[str, Any]) -> dict[str, Any]:
	decision = cstr(payload.get("decision")).strip().capitalize()
	if decision not in (APPROVE, RETURN):
		frappe.throw(_("Decision must be Approve or Return"))
	reason = cstr(payload.get("reason")).strip()
	if decision == RETURN and not (REASON_MIN <= len(reason) <= REASON_MAX):
		return funding.refusal("BUDGET_EVIDENCE_REQUIRED", "reason", _("Give the reason for returning the entry in {0} to {1} characters.").format(REASON_MIN, REASON_MAX))
	entry = resolve_entry(payload.get("entry") or "")
	lock_budgets_of_lines([r.budget_line for r in entry.rows if r.budget_line])
	entry = resolve_entry(entry.name, lock=True)
	request = funding.resolve_request(entry.request, lock=True)
	if entry.status != AWAITING or request.status != funding.OPEN:
		return funding.refusal("BUDGET_INVALID_STATE", "entry", _("This entry has already been decided or is no longer open."), entry=entry_summary(entry, request))
	expected = cstr(payload.get("expected_revision")).strip()
	if expected and expected != str(entry.modified):
		return funding.refusal("BUDGET_STALE_REVISION", "entry", _("This entry changed since you opened it. Review the latest version."), entry=entry_summary(entry, request))
	user = frappe.session.user
	confirmers = frappe.parse_json(entry.confirmers_json) if entry.confirmers_json else []
	authority.require_independent(user, prepared_by=entry.prepared_by, submitted_by=entry.submitted_by, confirmers=confirmers)  # fails closed on unclear attribution
	assignment = authority.require_approver(user)
	key = cstr(payload.get("idempotency_key")).strip() or entry.name
	if decision == RETURN:
		return _return_entry(entry, request, user, assignment, reason, key)
	return _approve(entry, request, user, assignment, key)


def _return_entry(entry, request, user: str, assignment: str, reason: str, key: str, *, outcome: str = seam.OUTCOME_RETURNED, detail: dict[str, Any] | None = None) -> dict[str, Any]:
	entry.status, entry.decided_by, entry.decided_at, entry.decision_reason, entry.decision_assignment = RETURNED, user, now_datetime(), reason, assignment
	with budget_write():
		entry.save(ignore_permissions=True)
	if entry.budget:
		record_event(budget=entry.budget, event_type=EVENT_ENTRY_RETURNED, actor=user, correlation_id=key, calling_module=CALLING_MODULE, downstream_reference=entry.contract_reference or entry.contract,
			amount=float(stored(entry.rows_total or 0, scale=scale_for(entry.currency))), currency=entry.currency, reason=reason)
	funding.publish_outcome(request, outcome, attempt=key, detail={"reason": reason, "entry": entry.generated_reference, **(detail or {})})
	entry.reload()
	return {"ok": True, "entry": {**entry_summary(entry, request), "budget": entry.budget}, "request": funding.summary(request)}


def _approve(entry, request, user: str, assignment: str, key: str) -> dict[str, Any]:
	scale = scale_for(entry.currency)
	# freshness: what the Approver is shown is exactly what was submitted; a changed basis or coverage is returned for refreshed preparation, never silently recalculated
	if int(entry.basis_revision or 0) != int(request.basis_revision or 0) or cstr(entry.basis_digest) != cstr(request.basis_digest):
		return funding.refusal("BUDGET_STALE_REVISION", "entry", _("The opening review has changed. Return this entry for an updated allocation."), entry=entry_summary(entry, request))
	problem = _validated(entry, request)
	if problem:
		return problem
	budget = funding.target_budget(request.fiscal_year)
	if budget != entry.budget or not frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name"):
		return funding.refusal("BUDGET_CLOSED", "fiscal_year", _("The Budget for {0} is not Active. Nothing was committed.").format(request.fiscal_year))
	rows, problems = _clean_rows(request, _doc_rows(entry), [r.row_id for r in entry.rows], complete=True)
	if problems:
		return {"ok": False, "code": "BUDGET_LINE_NOT_ELIGIBLE", "errors": problems, "entry": entry_summary(entry, request)}
	total = sum((r["amount"] for r in rows), _ZERO)
	required = amounts_of(request)["required"]
	if total != required:
		return {"ok": False, "code": "BUDGET_ENTRY_ROWS_MISMATCH", "errors": {"rows": _("The allocation rows must add up to the amount requiring funding.")}}
	short = _shortfalls(entry, rows)
	if short:  # nothing is created; the entry goes back to the Officer with the grouped shortfall and the outcome is published once for this attempt
		message = "; ".join(f"{s['budget_line']}: short by {s['shortfall']}" for s in short)
		result = _return_entry(entry, request, user, assignment, _("Funding shortfall: {0}").format(message)[:REASON_MAX], key, outcome=seam.OUTCOME_SHORTFALL, detail={"shortfalls": short})
		result.update(ok=False, code="BUDGET_INSUFFICIENT_FUNDS", shortfalls=short, errors={"rows": _("There is not enough available funding. Nothing was committed.")})
		return result
	created = []
	for row in entry.rows:
		position_before = _position(row.budget_line)
		amount = stored(row.amount, scale=scale)
		commitment = frappe.get_doc({
			"doctype": "Procurement Commitment", "generated_reference": allocate_commitment_reference(), "origin": "Existing-contract entry", "budget": budget, "budget_line": row.budget_line,
			"entry_row": f"{entry.name}/{row.row_id}", "contract": request.contract, "status": "Active", "current_amount": amount, "currency": entry.currency,
			"lineage_json": json.dumps({"entry": entry.name, "request": request.name, "kind": request.kind, "basis_digest": entry.basis_digest, "contract_reference": request.contract_reference,
				**({"original_commitment": request.original_commitment, "increment_event": request.subject_event} if request.kind == "Additional" else {})}, sort_keys=True),
		})
		with budget_write():
			commitment.insert(ignore_permissions=True)
		position_after = _position(row.budget_line)
		record_event(budget=budget, budget_line=row.budget_line, commitment=commitment.name, event_type=EVENT_ENTRY_COMMITMENT, actor=user, correlation_id=f"{key}:{row.row_id}", calling_module=CALLING_MODULE,
			downstream_reference=request.contract_reference or request.contract, amount=float(amount), currency=entry.currency, before=position_before, after=position_after)
		row.commitment = commitment.name
		created.append({"row": row.row_id, "commitment": commitment.name, "code": commitment.generated_reference, "budget_line": row.budget_line, "amount": text(amount, scale=scale)})
	entry.status, entry.decided_by, entry.decided_at, entry.decision_reason, entry.decision_assignment = APPROVED, user, now_datetime(), "", assignment
	with budget_write():
		entry.save(ignore_permissions=True)
	request.status, request.outcome, request.closed_at, request.closed_by = funding.COMPLETED, seam.OUTCOME_APPROVED, now_datetime(), user
	with budget_write():
		request.save(ignore_permissions=True)
	record_event(budget=budget, event_type=EVENT_ENTRY_APPROVED, actor=user, correlation_id=key, calling_module=CALLING_MODULE, downstream_reference=request.contract_reference or request.contract,
		amount=float(total), currency=entry.currency)
	funding.publish_outcome(request, seam.OUTCOME_APPROVED, attempt=key, detail={"entry": entry.generated_reference, "commitments": created, "total": text(total, scale=scale)})
	entry.reload()
	return {"ok": True, "entry": {**entry_summary(entry, request), "budget": budget}, "request": funding.summary(request), "commitments": created}
