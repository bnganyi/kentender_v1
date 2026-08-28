# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Commitment conversion, adjustment and expenditure ingestion —
BUD-CHG-001 §12 logical integration contracts `convert_reservation`,
`adjust_commitment`, `ingest_expenditure_snapshot`.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, today

from kentender_budget.services.budget_authorization import (
	CAP_BUDGET_RESERVE,
	require_budget_capability,
)
from kentender_budget.services.budget_check_reserve_contracts import _resolve_line, _resolve_reservation
from kentender_budget.services.budget_line_contracts import ACTUAL_STALE_DAYS, format_kes_full
from kentender_budget.services.budget_permissions import (
	ROLE_APPROVER,
	ROLE_OFFICER,
	ROLE_APPROVER,
	require_any_role,
)
from kentender_budget.services.budget_reference import (
	allocate_commitment_reference,
	allocate_expenditure_snapshot_reference,
)


def _resolve_commitment(commitment: str) -> Any:
	key = (commitment or "").strip()
	if not key:
		frappe.throw(_("Commitment is required"))
	name = key if frappe.db.exists("Procurement Commitment", key) else ""
	if not name:
		name = frappe.db.get_value("Procurement Commitment", {"generated_reference": key}, "name") or ""
	if not name:
		frappe.throw(_("Commitment {0} not found").format(key), frappe.DoesNotExistError)
	return frappe.get_doc("Procurement Commitment", name)


def _commitment_result(doc, *, reused: bool) -> dict[str, Any]:
	currency = doc.currency or "KES"
	return {
		"ok": True,
		"reused": reused,
		"commitment_id": doc.name,
		"commitment_code": doc.generated_reference,
		"status": doc.status,
		"budget_line": doc.budget_line,
		"reservation": doc.reservation,
		"contract_code": doc.contract_code,
		"original_amount": flt(doc.original_amount),
		"current_amount": flt(doc.current_amount),
		"outstanding_amount": flt(doc.outstanding_amount),
		"current_amount_display": format_kes_full(doc.current_amount, currency=currency),
		"outstanding_amount_display": format_kes_full(doc.outstanding_amount, currency=currency),
		"idempotency_key": doc.idempotency_key or "",
	}


def convert_reservation(
	reservation: str | None = None,
	contract_code: str | None = None,
	contract_title: str | None = None,
	commitment_amount: float | None = None,
	idempotency_key: str | None = None,
	actor: str | None = None,
	generated_reference: str | None = None,
) -> dict[str, Any]:
	"""BUD-CHG-001 §12 `convert_reservation` — convert all or part of a
	Reserved/Partially converted reservation's remaining balance into a
	Procurement Commitment against an Award/Contract. Excess beyond the
	remaining reservation is rejected; any unconverted remainder stays
	Reserved (status becomes Partially converted) — it is not silently
	released. One reservation may be converted more than once (partial
	conversions), never beyond its original amount.
	"""
	key = (idempotency_key or "").strip()
	if key:
		existing = frappe.db.get_value("Procurement Commitment", {"idempotency_key": key}, "name")
		if existing:
			return _commitment_result(frappe.get_doc("Procurement Commitment", existing), reused=True)

	doc = _resolve_reservation(reservation or "")
	bud = frappe.get_doc("Budget", doc.budget)
	require_budget_capability(CAP_BUDGET_RESERVE, bud)

	if doc.status not in ("Reserved", "Partially converted"):
		frappe.throw(_("Only a Reserved or Partially converted reservation can be converted"))

	amount = flt(commitment_amount)
	if amount <= 0:
		frappe.throw(_("Commitment amount must be positive"))

	contract = (contract_code or "").strip()
	if not contract:
		frappe.throw(_("Contract reference is required to convert a reservation"))

	# Row lock against parallel conversion of the same reservation.
	frappe.db.sql(
		"SELECT name FROM `tabFunding Reservation` WHERE name=%s FOR UPDATE",
		(doc.name,),
	)
	doc.reload()

	remaining = flt(doc.remaining_reserved)
	if amount > remaining + 0.0001:
		frappe.throw(
			_("Commitment amount ({0}) exceeds the remaining reservation ({1})").format(
				format_kes_full(amount, currency=doc.currency or "KES"),
				format_kes_full(remaining, currency=doc.currency or "KES"),
			)
		)

	preferred = (generated_reference or "").strip()
	if preferred and not frappe.db.exists("Procurement Commitment", {"generated_reference": preferred}):
		ref = preferred
	else:
		ref = allocate_commitment_reference(bud.procuring_entity)
	idem = key or f"{doc.name}:{contract}:{flt(amount):.2f}"

	# Re-check idempotency after lock (race).
	existing2 = frappe.db.get_value("Procurement Commitment", {"idempotency_key": idem}, "name")
	if existing2:
		return _commitment_result(frappe.get_doc("Procurement Commitment", existing2), reused=True)

	com = frappe.get_doc(
		{
			"doctype": "Procurement Commitment",
			"budget": bud.name,
			"budget_line": doc.budget_line,
			"reservation": doc.name,
			"generated_reference": ref,
			"status": "Active",
			"event_date": getdate(today()),
			"contract_code": contract,
			"contract_title": (contract_title or "").strip() or contract,
			"original_amount": amount,
			"current_amount": amount,
			"actual_expenditure": 0,
			"currency": bud.currency or "KES",
			"idempotency_key": idem,
		}
	)
	com.insert(ignore_permissions=True)

	# Reclassify held funds: reservation -> commitment. Total held (reserved +
	# committed) on the line is unchanged (BUD-CHG-001 §6.1 canonical formula).
	doc.remaining_reserved = remaining - amount
	doc.status = "Converted" if doc.remaining_reserved <= 0.0001 else "Partially converted"
	doc.save(ignore_permissions=True)

	line = frappe.get_doc("Budget Line", doc.budget_line)
	frappe.db.set_value(
		"Budget Line",
		line.name,
		{
			"amount_reserved": max(0.0, flt(line.amount_reserved) - amount),
			"amount_committed": flt(line.amount_committed) + amount,
		},
		update_modified=True,
	)

	from kentender_budget.services.budget_audit_contracts import EVENT_COMMITMENT, safe_record_event

	safe_record_event(
		budget=bud.name,
		event_type=EVENT_COMMITMENT,
		record_doctype="Procurement Commitment",
		record_code=ref,
		budget_line=doc.budget_line,
		after_summary=format_kes_full(amount, currency=bud.currency or "KES"),
		source_reference=doc.generated_reference,
		actor=(actor or frappe.session.user or "System").strip(),
		actor_kind="user",
	)

	com.reload()
	return _commitment_result(com, reused=False)


def adjust_commitment(
	commitment: str | None = None,
	new_amount: float | None = None,
	reason: str | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""BUD-CHG-001 §12 `adjust_commitment` — apply a variation/correction to an
	Active Procurement Commitment's current amount, updating the Budget
	Line's committed balance accordingly. An increase must be covered by the
	line's current available balance (a revalidation-equivalent guard);
	`outstanding_amount` is recomputed automatically (already-existing
	`Procurement Commitment.validate()` behaviour).
	"""
	doc = _resolve_commitment(commitment or "")
	bud = frappe.get_doc("Budget", doc.budget)
	require_budget_capability(CAP_BUDGET_RESERVE, bud)

	if doc.status != "Active":
		frappe.throw(_("Only an Active commitment can be adjusted"))

	new_amt = flt(new_amount)
	if new_amt < 0:
		frappe.throw(_("Adjusted commitment amount cannot be negative"))

	reason_text = (reason or "").strip()
	if not reason_text:
		frappe.throw(_("A reason is required to adjust a commitment"))

	# Row lock against parallel adjustment.
	frappe.db.sql(
		"SELECT name FROM `tabProcurement Commitment` WHERE name=%s FOR UPDATE",
		(doc.name,),
	)
	doc.reload()

	prior_amount = flt(doc.current_amount)
	delta = new_amt - prior_amount
	line = frappe.get_doc("Budget Line", doc.budget_line)
	if delta > 0:
		available = flt(line.approved_amount) - flt(line.amount_reserved) - flt(line.amount_committed)
		if delta > available + 0.0001:
			frappe.throw(
				_("Increase of {0} exceeds the Budget Line's available balance ({1})").format(
					format_kes_full(delta, currency=doc.currency or "KES"),
					format_kes_full(available, currency=doc.currency or "KES"),
				)
			)

	doc.current_amount = new_amt
	doc.save(ignore_permissions=True)

	frappe.db.set_value(
		"Budget Line",
		line.name,
		"amount_committed",
		max(0.0, flt(line.amount_committed) + delta),
		update_modified=True,
	)

	from kentender_budget.services.budget_audit_contracts import (
		EVENT_COMMITMENT_ADJUSTED,
		safe_record_event,
	)

	safe_record_event(
		budget=bud.name,
		event_type=EVENT_COMMITMENT_ADJUSTED,
		record_doctype="Procurement Commitment",
		record_code=doc.generated_reference,
		budget_line=doc.budget_line,
		before_summary=format_kes_full(prior_amount, currency=doc.currency or "KES"),
		after_summary=format_kes_full(new_amt, currency=doc.currency or "KES"),
		reason=reason_text,
		actor=(actor or frappe.session.user or "System").strip(),
		actor_kind="user",
	)

	doc.reload()
	return _commitment_result(doc, reused=False)


def _snapshot_result(doc, *, reused: bool) -> dict[str, Any]:
	return {
		"ok": True,
		"reused": reused,
		"snapshot_id": doc.name,
		"snapshot_code": doc.generated_reference,
		"reconciliation_status": doc.reconciliation_status,
		"budget_line": doc.budget_line,
		"commitment": doc.commitment or "",
		"amount": flt(doc.amount),
		"amount_display": format_kes_full(doc.amount, currency=doc.currency or "KES"),
		"source_as_at": str(doc.source_as_at) if doc.source_as_at else "",
		"idempotency_key": doc.idempotency_key or "",
	}


def ingest_expenditure_snapshot(
	budget_line: str | None = None,
	commitment: str | None = None,
	amount: float | None = None,
	source_system: str | None = None,
	source_reference: str | None = None,
	source_as_at: str | None = None,
	idempotency_key: str | None = None,
	generated_reference: str | None = None,
) -> dict[str, Any]:
	"""BUD-CHG-001 §12 `ingest_expenditure_snapshot` — record a read-only
	Expenditure Snapshot from an authoritative finance-system payload. Never
	invents or derives an amount — actual expenditure is integration-only,
	never manual entry, and reconciliation status reflects payload freshness
	rather than a fabricated zero when no integration is configured.
	"""
	require_any_role(ROLE_OFFICER, ROLE_APPROVER, ROLE_APPROVER, "System Manager")

	key = (idempotency_key or "").strip()
	if key:
		existing = frappe.db.get_value("Expenditure Snapshot", {"idempotency_key": key}, "name")
		if existing:
			return _snapshot_result(frappe.get_doc("Expenditure Snapshot", existing), reused=True)

	line = _resolve_line(budget_line or "")
	bud = frappe.get_doc("Budget", line.budget)

	amt = flt(amount)
	if amt < 0:
		frappe.throw(_("Expenditure amount cannot be negative"))
	source = (source_system or "").strip()
	if not source:
		frappe.throw(_("Source system is required for an expenditure snapshot"))

	com_doc = None
	com_key = (commitment or "").strip()
	if com_key:
		com_doc = _resolve_commitment(com_key)
		if com_doc.budget_line != line.name:
			frappe.throw(_("Commitment does not belong to this Budget Line"))

	as_at = getdate(source_as_at) if source_as_at else getdate(today())
	preferred = (generated_reference or "").strip()
	if preferred and not frappe.db.exists("Expenditure Snapshot", {"generated_reference": preferred}):
		ref = preferred
	else:
		ref = allocate_expenditure_snapshot_reference(bud.procuring_entity)
	idem = key or f"{line.name}:{source}:{as_at}:{flt(amt):.2f}"

	existing2 = frappe.db.get_value("Expenditure Snapshot", {"idempotency_key": idem}, "name")
	if existing2:
		return _snapshot_result(frappe.get_doc("Expenditure Snapshot", existing2), reused=True)

	staleness_days = (getdate(today()) - as_at).days
	reconciliation = "Stale" if staleness_days > ACTUAL_STALE_DAYS else "Matched"

	snap = frappe.get_doc(
		{
			"doctype": "Expenditure Snapshot",
			"budget": bud.name,
			"budget_line": line.name,
			"commitment": com_doc.name if com_doc else None,
			"generated_reference": ref,
			"reconciliation_status": reconciliation,
			"amount": amt,
			"currency": bud.currency or "KES",
			"source_system": source,
			"source_reference": (source_reference or "").strip(),
			"contract_code": com_doc.contract_code if com_doc else "",
			"source_as_at": as_at,
			"received_at": now_datetime(),
			"idempotency_key": idem,
		}
	)
	snap.insert(ignore_permissions=True)

	# Read-only reconciliation reference onto the line / commitment display
	# fields — never the source of the reservation/commitment balances above.
	frappe.db.set_value(
		"Budget Line", line.name, {"amount_actual": amt, "actual_as_at": as_at}, update_modified=True
	)
	if com_doc:
		outstanding = max(0.0, flt(com_doc.current_amount) - amt)
		frappe.db.set_value(
			"Procurement Commitment",
			com_doc.name,
			{"actual_expenditure": amt, "outstanding_amount": outstanding},
			update_modified=True,
		)

	from kentender_budget.services.budget_audit_contracts import EVENT_EXPENDITURE, safe_record_event

	safe_record_event(
		budget=bud.name,
		event_type=EVENT_EXPENDITURE,
		record_doctype="Expenditure Snapshot",
		record_code=ref,
		budget_line=line.name,
		after_summary=format_kes_full(amt, currency=bud.currency or "KES"),
		source_reference=source,
		actor=frappe.session.user or "System",
		actor_kind="integration",
	)

	snap.reload()
	return _snapshot_result(snap, reused=False)
