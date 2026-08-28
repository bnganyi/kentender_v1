# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.2 §8.3/§9.1 — later reservation/commitment lifecycle events:
`revalidate_reservations`, `release_reservation`, `convert_reservation`,
`adjust_commitment`. No expenditure contract exists in MVP-1 — the previous
`ingest_expenditure_snapshot` function and Expenditure Snapshot integration
are removed outright, not stubbed.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt

from kentender_budget.services.budget_check_reserve_contracts import _resolve_reservation
from kentender_budget.services.budget_line_contracts import format_kes_full
from kentender_budget.services.budget_reference import allocate_commitment_reference


def _require_service_capability(procuring_entity: str) -> None:
	"""§17.1: downstream service principals authenticate their event, not a
	Budget Version workflow role. A System Manager / Administrator technical
	session, or any authenticated user acting for a downstream module, may
	call these — the real authority boundary is the caller's own module
	(Contract Management, Procurement Planning), asserted by their own event."""
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("Authentication is required"), frappe.PermissionError, title="BUDGET_DOWNSTREAM_FORBIDDEN")


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
) -> dict[str, Any]:
	"""§9.1 `revalidate_reservations` — Current or Needs Attention results and
	ledger events; no new reservation is created."""
	_require_service_capability("")
	from kentender_budget.services.budget_contracts import _line_position
	from kentender_budget.services.budget_audit_contracts import EVENT_REVALIDATED, safe_record_event

	results = []
	for name in reservations or []:
		doc = _resolve_reservation(name)
		if doc.status in ("Converted", "Released"):
			results.append(_reservation_result(doc))
			continue

		pos = _line_position(doc.budget_line, _current_line_version(doc.budget_line))
		# The reservation's own remaining_amount is already inside pos["reserved"];
		# a floor breach shows up as negative available once approved_amount fell.
		prior_status = doc.status
		new_status = "Needs Attention" if pos["available"] < 0 else ("Active" if flt(doc.remaining_amount) >= flt(doc.original_amount) else "Partially Converted")

		if new_status != prior_status:
			doc.status = new_status
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


def _current_line_version(budget_line: str):
	from kentender_budget.services.budget_contracts import _active_version, _line_version_for

	budget = frappe.db.get_value("Budget Line", budget_line, "budget")
	version = _active_version(budget) if budget else None
	return _line_version_for(version.name, budget_line) if version else None


def release_reservation(
	reservation: str,
	amount: float | None,
	downstream_event_id: str,
	downstream_event_type: str,
	idempotency_key: str,
) -> dict[str, Any]:
	"""§9.1 `release_reservation` — reduce the remaining amount or set
	Released, and return the new line position."""
	_require_service_capability("")
	doc = _resolve_reservation(reservation)
	if doc.status in ("Converted", "Released"):
		return {"ok": True, "reused": True, "reservation": _reservation_result(doc)}

	frappe.db.sql("select name from `tabFunding Reservation` where name=%s for update", (doc.name,))
	doc.reload()

	release_amount = flt(amount) if amount is not None else flt(doc.remaining_amount)
	release_amount = min(release_amount, flt(doc.remaining_amount))
	if release_amount <= 0:
		return {"ok": True, "reused": True, "reservation": _reservation_result(doc)}

	prior_remaining = flt(doc.remaining_amount)
	doc.remaining_amount = prior_remaining - release_amount
	doc.status = "Released" if doc.remaining_amount <= 0.0001 else doc.status
	doc.save(ignore_permissions=True)

	from kentender_budget.services.budget_audit_contracts import EVENT_RELEASED, safe_record_event

	safe_record_event(
		budget=doc.budget,
		budget_line=doc.budget_line,
		reservation=doc.name,
		event_type=EVENT_RELEASED,
		actor=frappe.session.user,
		correlation_id=idempotency_key,
		calling_module=downstream_event_type,
		downstream_reference=downstream_event_id,
		amount=release_amount,
		currency=doc.currency,
	)
	doc.reload()
	return {"ok": True, "reused": False, "reservation": _reservation_result(doc)}


def convert_reservation(
	reservation: str,
	contract: str,
	amount: float,
	idempotency_key: str,
) -> dict[str, Any]:
	"""§9.1 `convert_reservation` — convert all or part of a reservation's
	remaining balance into one Procurement Commitment. Excess beyond the
	remaining reservation is rejected; the unconverted remainder stays
	reserved (BUD-BR-014)."""
	_require_service_capability("")
	doc = _resolve_reservation(reservation)
	contract = (contract or "").strip()
	if not contract:
		frappe.throw(_("Contract reference is required"))

	# §4.6 — contract is unique within the reservation lineage, so (reservation,
	# contract) is the natural idempotency key: a repeat call for the same pair
	# returns the existing commitment rather than creating a second one.
	existing = frappe.db.get_value("Procurement Commitment", {"contract": contract, "reservation": doc.name}, "name")
	if existing:
		existing_doc = frappe.get_doc("Procurement Commitment", existing)
		return {"ok": True, "reused": True, "commitment": _commitment_result(existing_doc), "reservation": _reservation_result(doc)}

	if doc.status not in ("Active", "Partially Converted"):
		frappe.throw(_("Only an Active or Partially Converted reservation can be converted"), frappe.ValidationError, title="BUDGET_INVALID_STATE")

	amount = flt(amount)
	if amount <= 0:
		frappe.throw(_("Commitment amount must be positive"))

	frappe.db.sql("select name from `tabFunding Reservation` where name=%s for update", (doc.name,))
	doc.reload()

	remaining = flt(doc.remaining_amount)
	if amount > remaining + 0.0001:
		frappe.throw(
			_("Commitment amount ({0}) exceeds the remaining reservation ({1})").format(
				format_kes_full(amount, currency=doc.currency), format_kes_full(remaining, currency=doc.currency)
			),
			frappe.ValidationError,
			title="BUDGET_CONVERSION_EXCEEDS_REMAINDER",
		)

	budget = frappe.get_doc("Budget", doc.budget)
	ref = allocate_commitment_reference(budget.procuring_entity)
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
	com.insert(ignore_permissions=True)

	doc.remaining_amount = remaining - amount
	doc.status = "Converted" if doc.remaining_amount <= 0.0001 else "Partially Converted"
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
		calling_module="Contract Management",
		downstream_reference=contract,
		amount=amount,
		currency=doc.currency,
	)
	com.reload()
	doc.reload()
	return {"ok": True, "commitment": _commitment_result(com), "reservation": _reservation_result(doc)}


def adjust_commitment(
	commitment: str,
	new_total: float,
	variation_event_id: str,
	variation_event_type: str,
	idempotency_key: str,
) -> dict[str, Any]:
	"""§9.1 `adjust_commitment` — apply a contract variation/cancellation to
	an Active commitment's current amount after locked revalidation. An
	increase must be covered by the line's current available balance."""
	_require_service_capability("")
	doc = _resolve_commitment(commitment)
	if doc.status != "Active":
		frappe.throw(_("Only an Active commitment can be adjusted"), frappe.ValidationError, title="BUDGET_INVALID_STATE")

	new_amt = flt(new_total)
	if new_amt < 0:
		frappe.throw(_("Adjusted commitment amount cannot be negative"))

	frappe.db.sql("select name from `tabProcurement Commitment` where name=%s for update", (doc.name,))
	doc.reload()

	reservation = frappe.get_doc("Funding Reservation", doc.reservation)
	prior_amount = flt(doc.current_amount)
	delta = new_amt - prior_amount
	if delta > 0:
		from kentender_budget.services.budget_contracts import _line_position

		pos = _line_position(reservation.budget_line, _current_line_version(reservation.budget_line))
		if delta > pos["available"] + 0.0001:
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
		calling_module=variation_event_type,
		downstream_reference=variation_event_id,
		amount=new_amt,
		currency=doc.currency,
	)
	doc.reload()
	return {"ok": True, "commitment": _commitment_result(doc)}
