# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.3 §8.3/§9.1 — later reservation/commitment lifecycle events:
`revalidate_reservations`, `release_reservation`, `convert_reservation`,
`adjust_commitment`. They are in-process calls authenticated by a service
principal (`budget_service_principal`), never web endpoints (AUD-XC-002).
No expenditure contract exists in MVP-1 — the previous
`ingest_expenditure_snapshot` function and Expenditure Snapshot integration
are removed outright, not stubbed.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt

from kentender_budget.services.budget_write_family import budget_write
from kentender_budget.services.budget_check_reserve_contracts import _resolve_reservation
from kentender_budget.services.budget_line_contracts import format_kes_full
from kentender_budget.services.budget_locking import locked_doc, lock_budgets_of_lines
from kentender_budget.services.budget_money import parse_money, scale_for, stored, text
from kentender_budget.services.budget_reference import allocate_commitment_reference
from kentender_budget.services.budget_service_principal import (
	ACTION_ADJUST,
	ACTION_CONVERT,
	ACTION_RELEASE,
	ACTION_REVALIDATE,
	PRINCIPAL_CONTRACT,
	PRINCIPAL_LABEL,
	PRINCIPAL_REQUISITIONS,
	refuse,
	require_principal,
)


def _require_event(event_id: str, event_type: str) -> None:
	"""BUD-BR-015 — every release, conversion and adjustment names the
	authenticated downstream event it carries out."""
	if not (event_id or "").strip() or not (event_type or "").strip():
		refuse(_("An authenticated downstream event is required."))


def _require_key(idempotency_key: str) -> str:
	key = (idempotency_key or "").strip()
	if not key:
		refuse(_("An idempotency key is required."))
	return key


def _idempotent(*, action: str, caller, key: str, params: dict[str, Any], fn, budget_for) -> dict[str, Any]:
	"""BUD-BR-015 — one execution per (key, payload): a replay returns the
	first result flagged `replayed`; the same key with a different payload is
	`BUDGET_IDEMPOTENCY_CONFLICT`. Journaled on the funding ledger by the
	same mechanism the governance commands use."""
	from kentender_budget.services.budget_idempotency import conflict, run_idempotent

	payload = {"action": action, "principal": caller.principal, "reference": caller.reference, **params, "idempotency_key": key}
	# the caller was authorised by `require_principal` and the scope checks before this point; the key is bound to the principal and the action
	result = run_idempotent(payload=payload, fn=fn, budget_for=budget_for, command=action, actor=caller.principal)
	if result.get("ok") is False and result.get("code") == "BUDGET_IDEMPOTENCY_CONFLICT":
		frappe.throw(conflict(key)["errors"]["idempotency_key"], frappe.ValidationError, title="BUDGET_IDEMPOTENCY_CONFLICT")
	return result


def _budget_of_reservation(name_key: str):
	def budget_for(result):
		reservation = (result.get("reservation") or {}).get(name_key)
		return frappe.db.get_value("Funding Reservation", reservation, "budget") if reservation else None

	return budget_for


def _resolve_commitment(commitment: str) -> Any:
	key = (commitment or "").strip()
	if not key:
		frappe.throw(_("Commitment is required"))
	name = key if frappe.db.exists("Procurement Commitment", key) else frappe.db.get_value("Procurement Commitment", {"generated_reference": key}, "name")
	if not name:
		frappe.throw(_("Commitment {0} not found").format(key), frappe.DoesNotExistError)
	return frappe.get_doc("Procurement Commitment", name)


def _commitment_result(doc) -> dict[str, Any]:
	return {
		"commitment_id": doc.name,
		"commitment_code": doc.generated_reference,
		"status": doc.status,
		"reservation": doc.reservation,
		"contract": doc.contract,
		"current_amount": flt(doc.current_amount),
		"currency": doc.currency,
	}


def _reservation_result(doc) -> dict[str, Any]:
	return {
		"reservation_id": doc.name,
		"reservation_code": doc.generated_reference,
		"status": doc.status,
		"budget_line": doc.budget_line,
		"remaining_amount": flt(doc.remaining_amount),
		"currency": doc.currency,
	}


def revalidate_reservations(
	reservations: list[str],
	downstream_event_id: str,
	downstream_event_type: str,
	idempotency_key: str,
	*,
	caller=None,
) -> dict[str, Any]:
	"""§9.1 `revalidate_reservations` — Current or Needs Attention results and
	ledger events; no new reservation is created. Budget-internal only."""
	require_principal(caller, ACTION_REVALIDATE)
	_require_event(downstream_event_id, downstream_event_type)
	_require_key(idempotency_key)
	from kentender_budget.services.budget_contracts import _line_position_exact
	from kentender_budget.services.budget_audit_contracts import EVENT_REVALIDATED, safe_record_event

	results = []
	for name in reservations or []:
		doc = _resolve_reservation(name)
		if doc.status in ("Converted", "Released"):
			results.append(_reservation_result(doc))
			continue

		# AUD-XC-116 — exact decimals: a line whose approved amount equals its
		# reserved plus committed amount has an available balance of exactly
		# zero and is not in breach.
		pos = _line_position_exact(doc.budget_line, _current_line_version(doc.budget_line))
		scale = scale_for(doc.currency)
		# The reservation's own remaining_amount is already inside pos["reserved"];
		# a floor breach shows up as negative available once approved_amount fell.
		prior_status = doc.status
		new_status = "Needs Attention" if pos["available"] < 0 else ("Active" if stored(doc.remaining_amount, scale=scale) >= stored(doc.original_amount, scale=scale) else "Partially Converted")

		if new_status != prior_status:
			doc.status = new_status
			with budget_write():
				doc.save(ignore_permissions=True)
			safe_record_event(
				budget=doc.budget,
				budget_line=doc.budget_line,
				reservation=doc.name,
				event_type=EVENT_REVALIDATED,
				actor=frappe.session.user,
				correlation_id=idempotency_key,
				calling_module=downstream_event_type,
				downstream_reference=downstream_event_id,
				revalidation_failure_code="BUDGET_LINE_FLOOR_BREACH" if new_status == "Needs Attention" else "",
			)
			doc.reload()
		results.append(_reservation_result(doc))
	return {"ok": True, "reservations": results}


def _current_line_version(budget_line: str, *, for_update: bool = False):
	from kentender_budget.services.budget_contracts import _active_version, _line_version_for

	budget = frappe.db.get_value("Procurement Budget Line", budget_line, "budget")
	version = _active_version(budget, for_update=for_update) if budget else None
	return _line_version_for(version.name, budget_line, for_update=for_update) if version else None


def release_reservation(
	reservation: str,
	amount: Decimal | str | int | None,
	downstream_event_id: str,
	downstream_event_type: str,
	idempotency_key: str,
	*,
	caller=None,
) -> dict[str, Any]:
	"""§9.1 `release_reservation` — reduce the remaining amount or set
	Released, and return the new line position. "Release" frees a reserved
	budget amount, not cash.

	Requisitions may release only the whole, unconverted reservation its own
	requisition created (governed revocation; the caller releases the Planning
	drawdown in the same transaction). Contract Management may release an
	explicit unused amount of a reservation it has converted for its own
	contract."""
	caller = require_principal(caller, ACTION_RELEASE)
	_require_event(downstream_event_id, downstream_event_type)
	key = _require_key(idempotency_key)
	doc = _resolve_reservation(reservation)
	# AUD-XC-117 — a malformed, non-finite or excess-scale amount fails typed,
	# before the scope check and before any effect.
	amount = None if amount is None else parse_money(amount, scale=scale_for(doc.currency), field="amount")
	_require_release_scope(caller, doc, amount)
	params = {"reservation": doc.name, "amount": None if amount is None else text(amount, scale=scale_for(doc.currency)), "event_id": downstream_event_id, "event_type": downstream_event_type}
	return _idempotent(
		action=ACTION_RELEASE, caller=caller, key=key, params=params,
		fn=lambda: _release(doc.name, amount, downstream_event_id, downstream_event_type, key, caller),
		budget_for=_budget_of_reservation("reservation_id"),
	)


def _require_release_scope(caller, doc, amount) -> None:
	if not caller.reference:
		refuse(_("The calling service must name what it acts for."))
	if caller.principal == PRINCIPAL_REQUISITIONS:
		created_by_requisition = doc.calling_module == PRINCIPAL_LABEL[PRINCIPAL_REQUISITIONS] and (doc.caller_reference or "") == caller.reference
		converted = doc.status in ("Converted", "Partially Converted") or frappe.db.exists("Procurement Commitment", {"reservation": doc.name})
		if not created_by_requisition or converted or amount is not None:
			refuse(_("Requisitions may release only the whole, unconverted reservation its own requisition created."))
	elif caller.principal == PRINCIPAL_CONTRACT:
		linked = frappe.db.exists("Procurement Commitment", {"reservation": doc.name, "contract": caller.reference})
		if not linked or amount is None:
			refuse(_("Contract Management may release only an explicit unused amount of a reservation it converted for its own contract."))


def _release(reservation: str, amount, downstream_event_id: str, downstream_event_type: str, idempotency_key: str, caller) -> dict[str, Any]:
	# AUD-XC-101..103 — the Budget's shared lock order first (Version rows, the
	# line row), then the reservation row; the state is decided only from the
	# locked, latest-committed reservation, never the snapshot read above it.
	lock_budgets_of_lines([frappe.db.get_value("Funding Reservation", reservation, "budget_line")])
	doc = locked_doc("Funding Reservation", reservation)
	if doc.status in ("Converted", "Released"):
		return {"ok": True, "reused": True, "reservation": _reservation_result(doc)}

	scale = scale_for(doc.currency)
	prior_remaining = stored(doc.remaining_amount, scale=scale)
	release_amount = amount if amount is not None else prior_remaining
	if release_amount > prior_remaining:
		frappe.throw(
			_("Release amount ({0}) exceeds the remaining reservation ({1})").format(
				format_kes_full(release_amount, currency=doc.currency), format_kes_full(prior_remaining, currency=doc.currency)
			),
			frappe.ValidationError,
			title="BUDGET_RELEASE_EXCEEDS_REMAINDER",
		)
	if release_amount <= 0:
		return {"ok": True, "reused": True, "reservation": _reservation_result(doc)}

	new_remaining = prior_remaining - release_amount
	doc.remaining_amount = new_remaining
	doc.status = "Released" if new_remaining == 0 else doc.status
	with budget_write():
		doc.save(ignore_permissions=True)

	from kentender_budget.services.budget_audit_contracts import EVENT_RELEASED, safe_record_event

	safe_record_event(
		budget=doc.budget,
		budget_line=doc.budget_line,
		reservation=doc.name,
		event_type=EVENT_RELEASED,
		actor=frappe.session.user,
		correlation_id=idempotency_key,
		calling_module=PRINCIPAL_LABEL[caller.principal],
		downstream_reference=downstream_event_id,
		amount=release_amount,
		currency=doc.currency,
	)
	doc.reload()
	return {"ok": True, "reused": False, "reservation": _reservation_result(doc)}


def convert_reservation(
	reservation: str,
	contract: str,
	amount: Decimal | str | int,
	idempotency_key: str,
	*,
	contract_event_id: str = "",
	contract_event_type: str = "",
	caller=None,
) -> dict[str, Any]:
	"""§9.1 `convert_reservation` — convert all or part of a reservation's
	remaining balance into one Procurement Commitment. Excess beyond the
	remaining reservation is rejected; the unconverted remainder stays
	reserved (BUD-BR-014). Contract Management only, for its own contract,
	on a contract event."""
	caller = require_principal(caller, ACTION_CONVERT)
	_require_event(contract_event_id, contract_event_type)
	key = _require_key(idempotency_key)
	contract = (contract or "").strip()
	if not contract:
		frappe.throw(_("Contract reference is required"))
	if caller.reference != contract:
		refuse(_("Contract Management may convert a reservation only for its own contract."))
	doc = _resolve_reservation(reservation)
	amount = parse_money(amount, scale=scale_for(doc.currency), field="amount")
	params = {"reservation": doc.name, "contract": contract, "amount": text(amount, scale=scale_for(doc.currency)), "event_id": contract_event_id, "event_type": contract_event_type}
	return _idempotent(
		action=ACTION_CONVERT, caller=caller, key=key, params=params,
		fn=lambda: _convert(doc.name, contract, amount, key, contract_event_id, contract_event_type),
		budget_for=_budget_of_reservation("reservation_id"),
	)


def _convert(reservation: str, contract: str, amount: Decimal, idempotency_key: str, contract_event_id: str, contract_event_type: str) -> dict[str, Any]:
	# AUD-XC-101..103/BUD-004 — shared lock order, then every read below is a
	# locking read of the latest committed state.
	lock_budgets_of_lines([frappe.db.get_value("Funding Reservation", reservation, "budget_line")])
	doc = locked_doc("Funding Reservation", reservation)
	scale = scale_for(doc.currency)

	# §4.6 — contract is unique within the reservation lineage, so (reservation,
	# contract) is also a natural key: the same pair and amount returns the
	# existing commitment; the same pair with a different amount is a changed
	# request, not a replay. One contract may hold a commitment on each of
	# several reservations (AUD-BUD-004).
	existing = frappe.db.get_value("Procurement Commitment", {"contract": contract, "reservation": doc.name}, "name", for_update=True)
	if existing:
		existing_doc = locked_doc("Procurement Commitment", existing)
		if stored(existing_doc.current_amount, scale=scale) != amount:
			frappe.throw(
				_("This contract already holds a commitment on this reservation for a different amount. Adjust the commitment instead."),
				frappe.ValidationError,
				title="BUDGET_IDEMPOTENCY_CONFLICT",
			)
		return {"ok": True, "reused": True, "commitment": _commitment_result(existing_doc), "reservation": _reservation_result(doc)}

	if doc.status not in ("Active", "Partially Converted"):
		frappe.throw(_("Only an Active or Partially Converted reservation can be converted"), frappe.ValidationError, title="BUDGET_INVALID_STATE")

	remaining = stored(doc.remaining_amount, scale=scale)
	if amount > remaining:
		frappe.throw(
			_("Commitment amount ({0}) exceeds the remaining reservation ({1})").format(
				format_kes_full(amount, currency=doc.currency), format_kes_full(remaining, currency=doc.currency)
			),
			frappe.ValidationError,
			title="BUDGET_CONVERSION_EXCEEDS_REMAINDER",
		)

	ref = allocate_commitment_reference()
	com = frappe.get_doc(
		{
			"doctype": "Procurement Commitment",
			"generated_reference": ref,
			"reservation": doc.name,
			"contract": contract,
			"status": "Active",
			"current_amount": amount,
			"currency": doc.currency,
		}
	)
	with budget_write():
		com.insert(ignore_permissions=True)

	new_remaining = remaining - amount
	doc.remaining_amount = new_remaining
	doc.status = "Converted" if new_remaining == 0 else "Partially Converted"
	with budget_write():
		doc.save(ignore_permissions=True)

	from kentender_budget.services.budget_audit_contracts import EVENT_COMMITMENT, safe_record_event

	safe_record_event(
		budget=doc.budget,
		budget_line=doc.budget_line,
		reservation=doc.name,
		commitment=com.name,
		event_type=EVENT_COMMITMENT,
		actor=frappe.session.user,
		correlation_id=idempotency_key,
		calling_module=PRINCIPAL_LABEL[PRINCIPAL_CONTRACT],
		downstream_reference=contract,
		amount=amount,
		currency=doc.currency,
	)
	com.reload()
	doc.reload()
	return {"ok": True, "commitment": _commitment_result(com), "reservation": _reservation_result(doc)}


def adjust_commitment(
	commitment: str,
	new_total: Decimal | str | int,
	variation_event_id: str,
	variation_event_type: str,
	idempotency_key: str,
	*,
	caller=None,
) -> dict[str, Any]:
	"""§9.1 `adjust_commitment` — apply a contract variation/cancellation to
	an Active commitment's current amount after locked revalidation. An
	increase must be covered by the line's current available balance.
	Contract Management only, for its own contract's commitment, on a
	variation or cancellation event."""
	caller = require_principal(caller, ACTION_ADJUST)
	_require_event(variation_event_id, variation_event_type)
	key = _require_key(idempotency_key)
	doc = _resolve_commitment(commitment)
	if not caller.reference or (doc.contract or "") != caller.reference:
		refuse(_("Contract Management may adjust only its own contract's commitment."))
	if new_total is None:
		frappe.throw(_("Adjusted commitment amount is required"))
	new_total = parse_money(new_total, scale=scale_for(doc.currency), field="new_total", allow_zero=True)
	params = {"commitment": doc.name, "new_total": text(new_total, scale=scale_for(doc.currency)), "event_id": variation_event_id, "event_type": variation_event_type}

	def budget_for(result):
		reservation = frappe.db.get_value("Procurement Commitment", (result.get("commitment") or {}).get("commitment_id"), "reservation")
		return frappe.db.get_value("Funding Reservation", reservation, "budget") if reservation else None

	return _idempotent(
		action=ACTION_ADJUST, caller=caller, key=key, params=params,
		fn=lambda: _adjust(doc.name, new_total, variation_event_id, variation_event_type, key),
		budget_for=budget_for,
	)


def _adjust(commitment: str, new_total: Decimal, variation_event_id: str, variation_event_type: str, idempotency_key: str) -> dict[str, Any]:
	new_amt = new_total

	# AUD-XC-102 — an increase must be serialised against the Budget Line and
	# every reservation on it, not only this commitment row: take the shared
	# lock order (Version rows, the line row), then the commitment, then decide
	# from locked, latest-committed reads.
	reservation_name = frappe.db.get_value("Procurement Commitment", commitment, "reservation")
	budget_line = frappe.db.get_value("Funding Reservation", reservation_name, "budget_line")
	lock_budgets_of_lines([budget_line])
	doc = locked_doc("Procurement Commitment", commitment)
	if doc.status != "Active":
		frappe.throw(_("Only an Active commitment can be adjusted"), frappe.ValidationError, title="BUDGET_INVALID_STATE")

	reservation = locked_doc("Funding Reservation", doc.reservation)
	prior_amount = stored(doc.current_amount, scale=scale_for(doc.currency))
	delta = new_amt - prior_amount
	if delta > 0:
		from kentender_budget.services.budget_contracts import _line_position_exact

		pos = _line_position_exact(reservation.budget_line, _current_line_version(reservation.budget_line, for_update=True), for_update=True)
		if delta > pos["available"]:
			frappe.throw(
				_("Increase of {0} exceeds the Budget Line's available balance ({1})").format(
					format_kes_full(delta, currency=doc.currency), format_kes_full(pos["available"], currency=doc.currency)
				),
				frappe.ValidationError,
				title="BUDGET_COMMITMENT_INCREASE_UNFUNDED",
			)

	doc.current_amount = new_amt
	if new_amt <= 0:
		doc.status = "Cancelled"
	with budget_write():
		doc.save(ignore_permissions=True)

	from kentender_budget.services.budget_audit_contracts import EVENT_COMMITMENT_ADJUSTED, safe_record_event

	safe_record_event(
		budget=reservation.budget,
		budget_line=reservation.budget_line,
		reservation=reservation.name,
		commitment=doc.name,
		event_type=EVENT_COMMITMENT_ADJUSTED,
		actor=frappe.session.user,
		correlation_id=idempotency_key,
		calling_module=PRINCIPAL_LABEL[PRINCIPAL_CONTRACT],
		downstream_reference=variation_event_id,
		amount=new_amt,
		currency=doc.currency,
	)
	doc.reload()
	return {"ok": True, "commitment": _commitment_result(doc)}
