# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract funding requests (BUD-CHG-001 v1.16 sections 8.6, 8.7, 8.8; follow-ups BUD23-XD-004, BUD24-XD-004/005).

An independently registered contract (one that was signed before KenTender and has no Tender, Award or reservation here) is funded by Budget in one way only: Contract Management raises **one request**
for the contract and a target Budget year (Initial or Annual), for an exact increment event (Additional) or for an exact correction subject (Correction); a Budget Officer prepares an entry for it, and a
different Budget Approver decides it (`budget_existing_contract_entry`). This module is the request: its creation and reuse, its basis, its closing and the ordered outcomes Budget gives back.

* A request creates no reservation, commitment or appropriation by itself, and Budget stores no Finance task. Finance confirmation is owned and completed in Contract Management, which sends validated funding
  facts (`ContractFundingBasis.v1`) and opaque evidence references. Budget reads no accounting record.
* One request per contract and target year, shared by Initial and Annual; one per exact increment event and year; one per correction subject. An identical replay returns the original request. A Declined or
  Withdrawn request that Contract Management raises again is the same lineage reopened, not a second request. A Completed request is never raised again.
* A missing or unusable basis does not stop receipt: the request shows **Year allocation required** and waits. Currency or product outside the supported scope shows **Scope review required** and invents nothing.
* When the confirmed charge for the year is already covered exactly by Budget's own commitments, or is zero, the request completes with **Already covered** or **No charge to this year**: no entry, no zero
  commitment, no ledger movement, and no authority to spend.
* Every decision attempt publishes one ordered outcome (`Contract Funding Outcome`) that Contract Management acknowledges; what is not acknowledged is retried, and a receiver that is down never changes
  what Budget decided."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from kentender_budget.services import budget_funding_authority as authority
from kentender_budget.services.budget_audit_contracts import (
	EVENT_FUNDING_REQUEST_DECLINED,
	EVENT_FUNDING_REQUEST_RECEIVED,
	EVENT_FUNDING_REQUEST_WITHDRAWN,
	safe_record_event,
)
from kentender_budget.services.budget_idempotency import payload_digest, run_idempotent
from kentender_budget.services.budget_locking import locked_doc
from kentender_budget.services.budget_money import MoneyInputError, parse_money, scale_for, stored, text
from kentender_budget.services.budget_reference import allocate_funding_request_reference
from kentender_budget.services.budget_service_principal import ACTION_FUNDING_REQUEST, PRINCIPAL_CONTRACT, PRINCIPAL_LABEL, refuse, require_principal
from kentender_budget.services.budget_write_family import budget_write
from kentender_core.services import contract_funding_request_contract as seam

REQUEST = "Contract Funding Request"
ENTRY = "Existing Contract Commitment Entry"
OUTCOME = "Contract Funding Outcome"
SUPPORTED_CURRENCY = "KES"
REASON_MIN, REASON_MAX = 10, 500
OPEN, COMPLETED, DECLINED, WITHDRAWN = "Open", "Completed", "Declined", "Withdrawn"


# ---- small helpers --------------------------------------------------------------------------------------------------------------


def money(value: Any, currency: str, field: str, *, allow_zero: bool = False) -> Decimal:
	try:
		return parse_money(value, scale=scale_for(currency), field=field, allow_zero=allow_zero)
	except MoneyInputError as exc:
		frappe.throw(str(exc), frappe.ValidationError, title="BUDGET_MONEY_PRECISION_INVALID")
		raise


def refusal(code: str, field: str, message: str, **extra) -> dict[str, Any]:
	return {"ok": False, "code": code, "errors": {field: message}, **extra}


def resolve_request(reference: str, *, lock: bool = False):
	key = cstr(reference).strip()
	if not key:
		frappe.throw(_("Request is required"))
	name = key if frappe.db.exists(REQUEST, key) else frappe.db.get_value(REQUEST, {"generated_reference": key}, "name") or frappe.db.get_value(REQUEST, {"scope_key": key}, "name")
	if not name:
		frappe.throw(_("Request {0} not found").format(key), frappe.DoesNotExistError)
	return locked_doc(REQUEST, name) if lock else frappe.get_doc(REQUEST, name)


def target_budget(fiscal_year: str) -> str | None:
	return frappe.db.get_value("Procurement Budget", {"fiscal_year": fiscal_year}, "name") if fiscal_year else None


def _basis(doc) -> dict[str, Any]:
	return frappe.parse_json(doc.basis_json) if doc.basis_json else {}


def confirmed_charge(doc) -> Decimal | None:
	"""The confirmed gross funding charge for the request's year and scope, or None while the year is not confirmed."""
	if doc.year_allocation_status != seam.YEAR_CONFIRMED:
		return None
	return stored(_basis(doc).get("confirmed_charge"), scale=scale_for(doc.currency))


def coverage_of(doc) -> dict[str, Any]:
	"""Budget's own verified coverage of the charge (BUD v1.16 8.7): the Active and Closed commitments of this contract in this year's Budget and this currency, counted once each. Native invoices and
	payments are not coverage. An Additional request is covered only by what was funded for that exact increment (nothing, until it is approved), never by the original commitment."""
	scale = scale_for(doc.currency)
	rows: list[dict[str, Any]] = []
	if doc.kind != "Additional" and doc.fiscal_year:
		rows = frappe.db.sql(
			"""select c.name as id, c.generated_reference as code, c.current_amount as amount, c.status as status, c.budget_line as budget_line, c.modified as modified
			from `tabProcurement Commitment` c join `tabProcurement Budget` b on b.name = c.budget
			where c.contract = %s and b.fiscal_year = %s and c.currency = %s and c.status in ('Active', 'Closed') order by c.name""",
			(doc.contract, doc.fiscal_year, doc.currency), as_dict=True,
		)
	items = [{"commitment": r.id, "code": r.code, "amount": text(stored(r.amount, scale=scale), scale=scale), "status": r.status, "budget_line": r.budget_line, "revision": str(r.modified)} for r in rows]
	total = sum((stored(r.amount, scale=scale) for r in rows), Decimal("0"))
	digest = payload_digest({"coverage": [(i["commitment"], i["amount"], i["status"], i["revision"]) for i in items]})
	return {"items": items, "total": total, "digest": digest}


def award_funded(contract: str) -> bool:
	"""A contract an Award reached has reservation-origin commitments: it is funded by its reservations and cannot use an Initial or Annual entry as a bypass (CM-AC-79)."""
	return bool(frappe.db.exists("Procurement Commitment", {"contract": contract, "origin": "Reservation conversion"}))


# ---- the ordered outcome outbox -------------------------------------------------------------------------------------------------


def publish_outcome(doc, outcome: str, *, attempt: str, detail: dict[str, Any] | None = None) -> Any:
	"""Record one outcome for a decision attempt and offer it, in order, to Contract Management. A request's outcomes are numbered; an earlier one that is not acknowledged is offered first."""
	latest = frappe.db.sql("select coalesce(max(sequence), 0) from `tabContract Funding Outcome` where request = %s for update", (doc.name,))[0][0]
	row = frappe.get_doc({"doctype": OUTCOME, "request": doc.name, "sequence": int(latest) + 1, "attempt_identity": cstr(attempt) or doc.name, "outcome": outcome,
		"payload_json": json.dumps(detail or {}, default=str, sort_keys=True), "created_at": now_datetime(), "fixture_namespace": doc.fixture_namespace or ""})
	with budget_write():
		row.insert(ignore_permissions=True)
	deliver_pending(doc.name)
	return row


def _wire(doc, row) -> dict[str, Any]:
	return {"request": doc.name, "reference": doc.generated_reference, "scope_key": doc.scope_key, "contract": doc.contract, "sequence": int(row.sequence), "attempt": row.attempt_identity, "outcome": row.outcome,
		"detail": frappe.parse_json(row.payload_json) if row.payload_json else {}}


def deliver_pending(request: str) -> int:
	"""Offer a request's unacknowledged outcomes in sequence; stop at the first one nobody acknowledges. Never raises: a receiver that is down leaves the outcome pending for the next sweep."""
	doc = frappe.get_doc(REQUEST, request)
	sent = 0
	for name in frappe.get_all(OUTCOME, filters={"request": request, "delivered_at": ("is", "not set")}, pluck="name", order_by="sequence asc"):
		row = frappe.get_doc(OUTCOME, name)
		savepoint = f"fo_{frappe.generate_hash(length=8)}"
		frappe.db.savepoint(savepoint)
		try:
			receipt = seam.deliver_outcome(_wire(doc, row))
		except Exception:
			frappe.db.rollback(save_point=savepoint)
			frappe.log_error(title=f"Contract funding outcome delivery failed for {doc.name}")
			break
		if not receipt:
			frappe.db.release_savepoint(savepoint)
			break
		frappe.db.release_savepoint(savepoint)
		with budget_write():
			row.delivered_at, row.delivery_receipt = now_datetime(), cstr(receipt.get("receipt") if isinstance(receipt, dict) else receipt)
			row.save(ignore_permissions=True)
		sent += 1
	return sent


def retry_pending_outcomes() -> int:
	"""Scheduled sweep: offer every request's unacknowledged outcomes again."""
	count = 0
	for request in frappe.get_all(OUTCOME, filters={"delivered_at": ("is", "not set")}, pluck="request", distinct=True):
		try:
			count += deliver_pending(request)
			frappe.db.commit()
		except Exception:
			frappe.log_error(title=f"Contract funding outcome retry failed for {request}")
	return count


# ---- what a request looks like ---------------------------------------------------------------------------------------------------


def waiting_item(doc) -> dict[str, Any]:
	"""Contract Management's own waiting item for this request, when its receiver offers one (Budget stores no Finance task; the holder belongs to CM's live assignments)."""
	for receiver in seam.receivers():
		reader = getattr(receiver, "waiting_item", None)
		if callable(reader):
			item = reader(scope_key=doc.scope_key)
			if item:
				return dict(item)
	return {}


def display_status(doc, entry=None) -> str:
	if doc.status == DECLINED:
		return "Declined"
	if doc.status == WITHDRAWN:
		return "Withdrawn"
	if doc.status == COMPLETED:
		return {seam.OUTCOME_ALREADY_COVERED: "Already covered — no new entry required", seam.OUTCOME_NO_CHARGE: "No charge to this year"}.get(doc.outcome, "Funding entry approved")
	if doc.year_allocation_status == seam.SCOPE_REVIEW:
		return "This funding is outside the supported scope"
	if doc.year_allocation_status != seam.YEAR_CONFIRMED:
		return "Year allocation required"
	if entry is None:
		return "Ready to prepare"
	if entry.status == "Awaiting approval":
		return "Awaiting approval" if entry.basis_revision == doc.basis_revision else "The opening review has changed. Return this entry for an updated allocation."
	if entry.status == "Returned":
		last = frappe.db.get_value(OUTCOME, {"request": doc.name}, "outcome", order_by="sequence desc")
		return "Funding shortfall" if last == seam.OUTCOME_SHORTFALL else "Returned"
	return "Draft" if entry.status == "Draft" else "Ready to prepare"


def holder_of(doc, entry=None) -> str:
	"""Who has the turn: the Budget Officer, the Budget Approver, or Contract Management's Finance (for the missing year basis)."""
	if doc.status != OPEN:
		return ""
	if doc.year_allocation_status != seam.YEAR_CONFIRMED:
		return "Contract Management Finance" if doc.year_allocation_status == seam.YEAR_REQUIRED else "Contract Management"
	if entry is not None and entry.status == "Awaiting approval":
		return "Budget Approver" if entry.basis_revision == doc.basis_revision else "Budget Approver"
	return "Budget Officer"


def current_entry(doc):
	return frappe.get_doc(ENTRY, doc.current_entry) if doc.current_entry else None


def summary(doc) -> dict[str, Any]:
	entry = current_entry(doc)
	scale = scale_for(doc.currency or SUPPORTED_CURRENCY)
	charge = confirmed_charge(doc)
	cover = coverage_of(doc) if charge is not None else None
	required = (charge - cover["total"]) if (charge is not None and cover is not None) else None
	waiting = waiting_item(doc) if doc.status == OPEN and doc.year_allocation_status != seam.YEAR_CONFIRMED else {}
	return {
		"id": doc.name, "code": doc.generated_reference, "kind": doc.kind, "status": doc.status, "outcome": doc.outcome or "", "display_status": display_status(doc, entry),
		"holder": holder_of(doc, entry), "scope_key": doc.scope_key, "contract": doc.contract, "contract_reference": doc.contract_reference or "", "agreement_version": doc.agreement_version or "",
		"supplier_name": doc.supplier_name or "", "fiscal_year": doc.fiscal_year or "", "currency": doc.currency or "", "source_organisation_unit": doc.source_organisation_unit or "",
		"year_allocation_status": doc.year_allocation_status, "basis_revision": int(doc.basis_revision or 0), "confirmed_charge": text(charge, scale=scale) if charge is not None else None,
		"coverage_total": text(cover["total"], scale=scale) if cover else None, "coverage": cover["items"] if cover else [],
		"amount_requiring_funding": text(required, scale=scale) if required is not None else None, "evidence": frappe.parse_json(doc.evidence_json) if doc.evidence_json else [],
		"basis_issues": frappe.parse_json(doc.get("basis_issues_json")) if doc.get("basis_issues_json") else [], "entry": entry.name if entry else "", "entry_status": entry.status if entry else "",
		"waiting_for": waiting, "revision": str(doc.modified), "closed_reason": doc.closed_reason or "",
	}


# ---- Contract Management: receive, update the basis, withdraw -----------------------------------------------------------------------


def _apply_basis(doc, basis: Any, evidence: list[str]) -> list[str]:
	"""Store a funding basis if it can be relied on. Returns the problems found (empty when relied on); the previous basis is kept when the new one is unusable."""
	problems: list[str] = []
	if doc.kind == "Correction":  # a correction names a Closed commitment and its evidence; there is no funding year to confirm
		doc.year_allocation_status = seam.YEAR_CONFIRMED
		if evidence:
			doc.evidence_json = json.dumps(sorted({cstr(e).strip() for e in evidence if cstr(e).strip()}))
		return []
	if basis:
		problems = seam.validate_basis(basis, contract=doc.contract, target_year=doc.fiscal_year or "", currency=doc.currency or "")
	if doc.currency and doc.currency != SUPPORTED_CURRENCY:
		doc.year_allocation_status = seam.SCOPE_REVIEW
		return problems or [_("Only {0} is supported for funding in Budget.").format(SUPPORTED_CURRENCY)]
	if basis and not problems:
		if (basis.get("unsupported_residual") or []):
			doc.year_allocation_status = seam.SCOPE_REVIEW
			problems = [_("Part of the contract is outside the supported scope.")]
		else:
			digest = cstr(basis.get("digest"))
			if digest != cstr(doc.basis_digest):
				doc.basis_revision = int(doc.basis_revision or 0) + 1
			doc.basis_json, doc.basis_digest = json.dumps(basis, sort_keys=True, default=str), digest
			doc.year_allocation_status = seam.YEAR_CONFIRMED
	elif not basis and not doc.basis_json:
		doc.year_allocation_status = seam.YEAR_REQUIRED
	if evidence:
		doc.evidence_json = json.dumps(sorted({cstr(e).strip() for e in evidence if cstr(e).strip()}))
	doc.basis_issues_json = json.dumps(problems) if doc.meta.has_field("basis_issues_json") else None
	return problems


def evaluate_no_entry(doc, *, attempt: str) -> str:
	"""Complete the request with no entry when the confirmed charge is zero or Budget already covers it exactly (BUD v1.16 8.7). Coverage above the charge is an error, never zero: it is refused where the entry
	is prepared. Returns the outcome label, or an empty string when an entry is needed."""
	if doc.status != OPEN or doc.kind == "Correction":
		return ""
	charge = confirmed_charge(doc)
	if charge is None:
		return ""
	cover = coverage_of(doc)
	if charge == 0 or cover["total"] == charge:
		outcome = seam.OUTCOME_NO_CHARGE if charge == 0 else seam.OUTCOME_ALREADY_COVERED
		doc.status, doc.outcome, doc.closed_at, doc.closed_by = COMPLETED, outcome, now_datetime(), PRINCIPAL_LABEL[PRINCIPAL_CONTRACT]
		with budget_write():
			doc.save(ignore_permissions=True)
		if doc.current_entry:
			entry = locked_doc(ENTRY, doc.current_entry)
			if entry.status != "Approved":
				entry.status = "Superseded"
				with budget_write():
					entry.save(ignore_permissions=True)
		publish_outcome(doc, outcome, attempt=attempt, detail={"confirmed_charge": text(charge, scale=scale_for(doc.currency)), "coverage_total": text(cover["total"], scale=scale_for(doc.currency)), "coverage": cover["items"]})
		return outcome
	return ""


def announce_ready(doc, was_ready: bool, attempt: str) -> None:
	"""The request has just become ready for Budget's Officer to prepare (Finance's basis arrived): Contract Management is told once, so it shows **Funding entry pending** with the Officer as holder."""
	if not was_ready and doc.status == OPEN and doc.kind != "Correction" and doc.year_allocation_status == seam.YEAR_CONFIRMED:
		publish_outcome(doc, seam.OUTCOME_ENTRY_SUBMITTED, attempt=attempt, detail={"stage": "Preparing", "holder": "Budget Officer"})


def receive_contract_funding_request(request: dict | str | None, identity: str, *, caller) -> dict[str, Any]:
	"""Contract Management raises the request for its own contract. Idempotent on `identity`; changes no amount."""
	caller = require_principal(caller, ACTION_FUNDING_REQUEST)
	request = frappe.parse_json(request) if isinstance(request, str) else dict(request or {})
	contract = cstr(request.get("contract")).strip()
	if not contract or caller.reference != contract:
		refuse(_("Contract Management may raise a funding request only for its own contract."))
	if not cstr(identity).strip():
		refuse(_("An idempotency key is required."))
	payload = {"action": ACTION_FUNDING_REQUEST, "principal": caller.principal, "reference": caller.reference, "request": request, "idempotency_key": identity}
	result = run_idempotent(payload=payload, fn=lambda: _receive(request, identity), budget_for=lambda r: (r.get("request") or {}).get("budget"), command="receive_contract_funding_request", actor=caller.principal)
	if result.get("ok") is False and result.get("code") == "BUDGET_IDEMPOTENCY_CONFLICT":
		frappe.throw(result["errors"]["idempotency_key"], frappe.ValidationError, title="BUDGET_IDEMPOTENCY_CONFLICT")
	return result


def _receive(request: dict[str, Any], identity: str) -> dict[str, Any]:
	kind, contract = cstr(request.get("kind")).strip(), cstr(request.get("contract")).strip()
	if kind not in seam.KINDS:
		frappe.throw(_("The request kind must be Initial, Annual, Additional or Correction"))
	year, currency = cstr(request.get("target_year")).strip(), cstr(request.get("currency")).strip() or SUPPORTED_CURRENCY
	if kind != "Correction" and (not year or not frappe.db.exists("Fiscal Year", year)):
		return refusal("BUDGET_CONFIG_MISSING", "target_year", _("The Budget year the funding is for is not set up on this site."))
	if kind in ("Initial", "Annual") and award_funded(contract):
		return refusal("BUDGET_INVALID_STATE", "contract", _("This contract was awarded through KenTender and is funded by its reservations. It cannot be funded as an existing contract."))
	subject = cstr(request.get("subject_event")).strip()
	if kind in ("Additional", "Correction") and not subject:
		return refusal("BUDGET_INVALID_STATE", "subject_event", _("An additional or correction request names the exact event or subject it is for."))
	original = cstr(request.get("original_commitment")).strip()
	if kind in ("Additional", "Correction") and not (original and frappe.db.get_value("Procurement Commitment", original, "status") == "Closed"):
		return refusal("BUDGET_INVALID_STATE", "original_commitment", _("An additional or correction request names the Closed commitment it follows."))
	key = seam.scope_key(kind=kind, contract=contract, target_year=year, subject_event=subject)
	existing = frappe.db.get_value(REQUEST, {"scope_key": key}, "name")
	basis, evidence = request.get("basis") or {}, [cstr(e) for e in (request.get("evidence") or [])]
	if existing:
		doc = locked_doc(REQUEST, existing)
		if doc.status == COMPLETED:
			return refusal("BUDGET_ENTRY_DUPLICATE", "request", _("Funding for this contract and year is already complete. Open the existing funding record."), request=summary(doc))
		reopened = doc.status in (DECLINED, WITHDRAWN)
		if reopened:
			doc.status, doc.outcome, doc.closed_at, doc.closed_by, doc.closed_reason = OPEN, "", None, "", ""
		created = False
	else:
		doc = frappe.get_doc({
			"doctype": REQUEST, "generated_reference": allocate_funding_request_reference(), "kind": kind, "status": OPEN, "scope_key": key, "contract": contract, "contract_reference": cstr(request.get("contract_reference")),
			"agreement_version": cstr(request.get("agreement_version")), "supplier_name": cstr(request.get("supplier_name")), "fiscal_year": year or None, "currency": currency,
			"source_organisation_unit": cstr(request.get("source_organisation_unit")) or None, "subject_event": subject, "original_commitment": original or None, "received_by": PRINCIPAL_LABEL[PRINCIPAL_CONTRACT],
			"received_at": now_datetime(), "idempotency_key": identity, "payload_digest": payload_digest(request),
		})
		reopened, created = False, True
	was_ready = doc.year_allocation_status == seam.YEAR_CONFIRMED and not created and not reopened
	problems = _apply_basis(doc, basis, evidence)
	with budget_write():
		if created:
			doc.insert(ignore_permissions=True)
		else:
			doc.save(ignore_permissions=True)
	budget = target_budget(doc.fiscal_year)
	if budget and (created or reopened):
		safe_record_event(budget=budget, event_type=EVENT_FUNDING_REQUEST_RECEIVED, actor=PRINCIPAL_LABEL[PRINCIPAL_CONTRACT], actor_kind="integration", correlation_id=identity,
			calling_module=PRINCIPAL_LABEL[PRINCIPAL_CONTRACT], downstream_reference=doc.contract_reference or doc.contract, amount=None, currency=doc.currency)
	closed = evaluate_no_entry(doc, attempt=identity)
	if not closed:
		announce_ready(doc, was_ready, identity)
	doc.reload()
	return {"ok": True, "created": created, "reopened": reopened, "problems": problems, "closed": closed, "request": {**summary(doc), "budget": budget}}


def update_contract_funding_basis(scope_key: str, basis: dict | str | None, evidence: list[str] | None, identity: str, *, caller) -> dict[str, Any]:
	"""Source evidence arrived later (or changed): the same request is refreshed. A changed basis on an entry already submitted is not recalculated silently: the Approver returns it for refreshed preparation."""
	caller = require_principal(caller, ACTION_FUNDING_REQUEST)
	basis = frappe.parse_json(basis) if isinstance(basis, str) else dict(basis or {})
	payload = {"action": "update_contract_funding_basis", "principal": caller.principal, "reference": caller.reference, "scope_key": scope_key, "basis": basis, "evidence": list(evidence or []), "idempotency_key": identity}
	return run_idempotent(payload=payload, fn=lambda: _update_basis(scope_key, basis, list(evidence or []), identity, caller), budget_for=lambda r: (r.get("request") or {}).get("budget"),
		command="update_contract_funding_basis", actor=caller.principal)


def _update_basis(scope_key: str, basis: dict[str, Any], evidence: list[str], identity: str, caller) -> dict[str, Any]:
	doc = resolve_request(scope_key, lock=True)
	if caller.reference != doc.contract:
		refuse(_("Contract Management may refresh the funding request only of its own contract."))
	if doc.status != OPEN:
		return refusal("BUDGET_INVALID_STATE", "request", _("This funding request is no longer open."), request=summary(doc))
	before, was_ready = doc.basis_revision, doc.year_allocation_status == seam.YEAR_CONFIRMED
	problems = _apply_basis(doc, basis, evidence)
	with budget_write():
		doc.save(ignore_permissions=True)
	if int(doc.basis_revision or 0) != int(before or 0):
		publish_outcome(doc, seam.OUTCOME_BASIS_CHANGED, attempt=identity, detail={"basis_revision": int(doc.basis_revision)})
	closed = evaluate_no_entry(doc, attempt=identity)
	if not closed:
		announce_ready(doc, was_ready, identity)
	doc.reload()
	return {"ok": True, "problems": problems, "closed": closed, "request": {**summary(doc), "budget": target_budget(doc.fiscal_year)}}


def withdraw_contract_funding_request(scope_key: str, reason: str, identity: str, *, caller) -> dict[str, Any]:
	"""Contract Management alone withdraws an Open request before funding. Unapproved preparation is abandoned; no commitment changes."""
	caller = require_principal(caller, ACTION_FUNDING_REQUEST)
	payload = {"action": "withdraw_contract_funding_request", "principal": caller.principal, "reference": caller.reference, "scope_key": scope_key, "reason": reason, "idempotency_key": identity}
	return run_idempotent(payload=payload, fn=lambda: _close_request(resolve_request(scope_key, lock=True), WITHDRAWN, cstr(reason), identity, caller=caller), budget_for=lambda r: (r.get("request") or {}).get("budget"),
		command="withdraw_contract_funding_request", actor=caller.principal)


def _close_request(doc, status: str, reason: str, identity: str, *, caller=None, user: str = "") -> dict[str, Any]:
	if caller is not None and caller.reference != doc.contract:
		refuse(_("Contract Management may withdraw the funding request only of its own contract."))
	if doc.status != OPEN:
		return refusal("BUDGET_INVALID_STATE", "request", _("This funding request is no longer open."), request=summary(doc))
	doc.status = status
	doc.outcome = seam.OUTCOME_WITHDRAWN if status == WITHDRAWN else seam.OUTCOME_DECLINED
	doc.closed_at, doc.closed_by, doc.closed_reason = now_datetime(), user or PRINCIPAL_LABEL[PRINCIPAL_CONTRACT], reason
	with budget_write():
		doc.save(ignore_permissions=True)
	if doc.current_entry:
		entry = locked_doc(ENTRY, doc.current_entry)
		if entry.status != "Approved":
			entry.status = "Superseded"
			with budget_write():
				entry.save(ignore_permissions=True)
	budget = target_budget(doc.fiscal_year)
	if budget:
		safe_record_event(budget=budget, event_type=EVENT_FUNDING_REQUEST_WITHDRAWN if status == WITHDRAWN else EVENT_FUNDING_REQUEST_DECLINED, actor=user or PRINCIPAL_LABEL[PRINCIPAL_CONTRACT],
			actor_kind="user" if user else "integration", correlation_id=identity, calling_module=PRINCIPAL_LABEL[PRINCIPAL_CONTRACT], downstream_reference=doc.contract_reference or doc.contract, amount=None, currency=doc.currency, reason=reason)
	publish_outcome(doc, doc.outcome, attempt=identity, detail={"reason": reason})
	doc.reload()
	return {"ok": True, "request": {**summary(doc), "budget": budget}}


# ---- Budget Officer: decline ---------------------------------------------------------------------------------------------------------


def decline_contract_funding_request(payload: dict | str | None = None) -> dict[str, Any]:
	"""Budget Officer. Decline an Open request with a reason (10–500 characters); the outcome is published and nothing is funded. Payload: `request`, `reason`, `idempotency_key`."""
	payload = frappe.parse_json(payload) if isinstance(payload, str) else dict(payload or {})
	return run_idempotent(payload=payload, fn=lambda: _decline(payload), budget_for=lambda r: (r.get("request") or {}).get("budget"), command="DeclineContractFundingRequest",
		authorise=lambda: authority.require_officer(frappe.session.user))


def _decline(payload: dict[str, Any]) -> dict[str, Any]:
	reason = cstr(payload.get("reason")).strip()
	if not (REASON_MIN <= len(reason) <= REASON_MAX):
		return refusal("BUDGET_EVIDENCE_REQUIRED", "reason", _("Give the reason for declining the request in {0} to {1} characters.").format(REASON_MIN, REASON_MAX))
	doc = resolve_request(payload.get("request") or "", lock=True)
	return _close_request(doc, DECLINED, reason, cstr(payload.get("idempotency_key")) or doc.name, user=frappe.session.user)


# ---- the work list --------------------------------------------------------------------------------------------------------------


def workspace_rows(fiscal_year: str, user: str) -> list[dict[str, Any]]:
	"""The funding work for the selected year, as rows of the Budget work list (BUD-DES-01B): the Officer's contracts to fund, the Approver's entries to review. Each row: task, contract reference, status, who has the
	turn, and the route to open it. A reader who is neither gets none; the request is not their work."""
	from kentender_budget.services.budget_funding_authority import ROLE_BUDGET_APPROVER, ROLE_BUDGET_OFFICER
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	def holds(role: str) -> bool:
		return bool(authorise_record(user=user, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND).allowed)

	officer, approver = holds(ROLE_BUDGET_OFFICER), holds(ROLE_BUDGET_APPROVER)
	if not (officer or approver):
		return []
	rows = []
	for name in frappe.get_all(REQUEST, filters={"fiscal_year": fiscal_year, "status": OPEN, "kind": ["!=", "Correction"]}, pluck="name", order_by="creation asc"):
		doc = frappe.get_doc(REQUEST, name)
		entry = current_entry(doc)
		awaiting = bool(entry and entry.status == "Awaiting approval")
		if awaiting and approver:
			task = "Review contract funding"
		elif officer and not awaiting:
			task = "Fund existing contract"
		else:
			continue
		rows.append({"request": doc.name, "code": doc.generated_reference, "task": task, "reference": doc.contract_reference or doc.contract, "status": display_status(doc, entry), "holder": holder_of(doc, entry),
			"kind": doc.kind, "route": ["budget-funding", "funding", doc.name]})
	return rows


# ---- a correction of a Closed commitment reaches the request that asked for it -------------------------------------------------------


def correction_decided(commitment: str, *, approved: bool, correction: dict[str, Any], attempt: str) -> None:
	"""Tell Contract Management what Budget decided about a Closed commitment's correction, if Contract Management asked for it (an Open Correction request naming the commitment). An approval closes the request;
	a return leaves it open for a corrected record. A correction a Budget Officer started alone has no request and nothing is sent: the Officer is not made to wait for, or to raise, a redundant HOP request."""
	for name in frappe.get_all(REQUEST, filters={"kind": "Correction", "status": OPEN, "original_commitment": commitment}, pluck="name"):
		doc = locked_doc(REQUEST, name)
		if approved:
			doc.status, doc.outcome, doc.closed_at, doc.closed_by = COMPLETED, seam.OUTCOME_CORRECTION_APPROVED, now_datetime(), correction.get("decided_by") or ""
			with budget_write():
				doc.save(ignore_permissions=True)
		publish_outcome(doc, seam.OUTCOME_CORRECTION_APPROVED if approved else seam.OUTCOME_CORRECTION_RETURNED, attempt=attempt,
			detail={"correction": correction.get("code"), "before_amount": correction.get("before_amount"), "after_amount": correction.get("after_amount"), "reason": correction.get("decision_reason") or ""})
